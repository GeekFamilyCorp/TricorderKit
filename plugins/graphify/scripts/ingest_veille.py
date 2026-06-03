#!/usr/bin/env python3
"""ingest_veille.py - Pont d'ingestion d'une veille externe -> fiches + RAG (LECTURE SEULE).

Consommateur EN AVAL des sorties d'un agent de veille/scraping externe.
NE MODIFIE NI les scripts NI le schema producteur (separation des responsabilites).
Lit `veille_fiches_detaillees_*.json` (fiche structuree) et, en option, indexe dans le RAG.

Etapes :
  1. Localise la derniere `veille_fiches_detaillees_*.json` sous --runs-root.
  2. Normalise chaque fiche + classifie la fiabilite (taxonomie du linked_project).
  3. --dry-run (DEFAUT) : ecrit un rapport (MD + JSON) de ce qui SERAIT cree/indexe. Aucune ecriture vault/RAG.
  4. --index : embeddings nomic + upsert Qdrant 'vault' (fiches de veille). A valider (dedup G1 + contention Ollama).

Usage :
  python ingest_veille.py --dry-run
  python ingest_veille.py --index            # apres validation
"""
from __future__ import annotations
import argparse, glob, json, os, re, unicodedata, uuid, datetime

HERE = os.path.dirname(os.path.abspath(__file__))

# Racine des sorties de veille (variable d'env TK_VEILLE_RUNS dans le repo prive/linked_project).
DEFAULT_ROOTS = [r for r in [os.environ.get("TK_VEILLE_RUNS", "")] if r]


def find_latest_fiches(roots):
    """Retourne le chemin du veille_fiches_detaillees_*.json le plus recent parmi les racines."""
    candidates = []
    for root in roots:
        if root and os.path.isdir(root):
            candidates += glob.glob(os.path.join(root, "**", "veille_fiches_detaillees_*.json"),
                                    recursive=True)
    if not candidates:
        return None
    return max(candidates, key=os.path.getmtime)


def _txt(v):
    """Normalise une valeur texte : None / placeholders 'a verifier' -> ''."""
    if not v:
        return ""
    s = str(v).strip()
    low = s.lower()
    if low in ("a verifier", "à vérifier", "a verif", "null", "none", "n/a"):
        return ""
    return s


def detect_type(f):
    """Type dominant de la fiche d'apres les sous-objets renseignes."""
    if _txt((f.get("anime") or {}).get("statut")) or _txt((f.get("anime") or {}).get("studio")):
        return "anime"
    ln = f.get("light_novel") or {}
    if _txt(ln.get("statut")) or _txt(ln.get("syosetu")) or (ln.get("links") or []):
        return "light_novel"
    return "manga"


def classify_reliability(f):
    """Mappe vers la taxonomie de fiabilite : confirme / probable / a_verifier / incomplet.
    S'appuie sur le bloc tracabilite fourni par la veille amont (niveau_fiabilite, sources, champs)."""
    tr = f.get("tracabilite") or {}
    niveau = _txt(tr.get("niveau_fiabilite")).lower()
    sources = tr.get("sources") or []
    valides = tr.get("champs_valides") or []
    non_valides = tr.get("champs_non_valides") or []
    titre_jp_ok = bool(_txt(f.get("titre_japonais")))

    official = has_official_source(f)  # DEC-035 : ossature validante
    if not _txt(f.get("titre_international")) or (not valides and len(non_valides) >= 5):
        return "incomplet"      # 🔴
    # DEC-035 : un ✅ EXIGE au moins une source officielle/primaire.
    # Niveau "haute" reposant uniquement sur des sources signal -> plafond 🟡 Probable.
    if niveau in ("haute", "elevee", "élevée") and len(sources) >= 2 and valides:
        return "confirme" if official else "probable"   # ✅ si officielle, sinon 🟡
    if niveau in ("haute", "elevee", "élevée") and sources and titre_jp_ok:
        return "confirme" if official else "probable"   # ✅ si officielle, sinon 🟡
    if niveau in ("moyenne",) and sources:
        return "probable"       # 🟡
    if sources:
        return "a_verifier"     # 🟠
    return "incomplet"          # 🔴


RELIAB_BADGE = {"confirme": "✅ Confirmé", "probable": "🟡 Probable",
                "a_verifier": "🟠 À vérifier", "incomplet": "🔴 Incomplet"}


# --- DEC-035 : tiering des sources (officielle/primaire vs signal/cross-check) ---
# Une source non officielle ne FONDE JAMAIS seule un ✅ Confirmé : elle sert de lead (🟠)
# ou de 2e source de cross-check. L'ossature validante reste officielle/primaire.
OFFICIAL_SOURCE_HINTS = (
    "shueisha", "kodansha", "shogakukan", "kadokawa", "shonenjump", "shonen-jump",
    "viz.com", "yenpress", "squareenix", "square-enix", "hakusensha", "futabasha",
    "ichijinsha", "akitashoten", "comic-walker", "bookwalker", "cdjapan",
    "oricon.co.jp", "natalie.mu", ".co.jp", "official",
)
# Sources DEBLOQUEES mais NON fondatrices : signal/surveillance + cross-check uniquement.
SIGNAL_SOURCE_HINTS = (
    "wikipedia.org", "twitter.com", "x.com", "mangaupdates.com", "baka-updates",
    "mangadex.org", "myanimelist.net", "anilist.co", "jikan",
)


def source_tier(s):
    """Classe une source/URL : 'officielle' (primaire) ou 'signal' (cross-check/lead).
    Defaut prudent : une source inconnue est traitee comme 'signal' (non fondatrice)."""
    low = (s or "").lower()
    if any(h in low for h in SIGNAL_SOURCE_HINTS):
        return "signal"
    if any(h in low for h in OFFICIAL_SOURCE_HINTS):
        return "officielle"
    return "signal"


def has_official_source(f):
    """True si >=1 source/URL de la fiche est de tier officiel/primaire (DEC-035)."""
    tr = f.get("tracabilite") or {}
    for s in (tr.get("sources") or []) + (tr.get("urls") or []):
        if source_tier(s) == "officielle":
            return True
    return False


# DEC-035 : sources de CONTENU interdites (piratage / scantrad) — seuil tolere = 0.
# NB : MangaDex N'EST PAS ici (autorise en metadonnees/signal), mais l'est si scanle -> on
# bloque sur les agregateurs de scan connus.
FORBIDDEN_CONTENT_HINTS = (
    "scantrad", "scan-trad", "lelscan", "scan-manga", "japscan", "mangakawai",
    "reaperscans", "mangapark", "mangakakalot", "manganato", "mangafire",
    "mangabuddy", "bato.to", "aquamanga", "scanvf", "anime-sama",
)


def forbidden_content_source(s):
    """True si la source pointe un agregateur de contenu pirate/scanle (DEC-035)."""
    low = (s or "").lower()
    return any(h in low for h in FORBIDDEN_CONTENT_HINTS)


def has_forbidden_content(f):
    tr = f.get("tracabilite") or {}
    return any(forbidden_content_source(s)
               for s in (tr.get("sources") or []) + (tr.get("urls") or []))


# --- Dedup G1 : confronte les fiches au Master Index (source de verite opposable) ---
def _norm_title(s):
    """Normalise un titre pour comparaison : sans accents, minuscule, alphanum + espaces."""
    if not s:
        return ""
    s = unicodedata.normalize("NFKD", str(s))
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", " ", s.lower()).strip()


def load_master_index_titles(path):
    """Parse le tableau Markdown du Master Index -> set de titres normalises.
    Colonnes : | ID | Type | Titre | Status | Completude | Chemin |."""
    titles = set()
    if not path or not os.path.isfile(path):
        return titles
    for line in open(path, "r", encoding="utf-8", errors="replace"):
        if not line.startswith("|"):
            continue
        cols = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cols) >= 3 and cols[0] not in ("ID", "---", ""):
            t = _norm_title(cols[2])
            if t:
                titles.add(t)
    return titles


def dedup_status(n, index_titles):
    """nouveau / existant selon presence du titre (int. ou JP) dans le Master Index.
    NB : matching exact-normalise ; le fuzzy romaji<->JP reste un chantier (DEC-021)."""
    if not index_titles:
        return "inconnu"  # pas de Master Index fourni
    for key in (n.get("titre_international"), n.get("titre_japonais")):
        if key and _norm_title(key) in index_titles:
            return "existant"
    return "nouveau"


def normalize(f):
    """Fiche veille brute -> dict normalise exploitable (vault/RAG)."""
    tr = f.get("tracabilite") or {}
    ed = f.get("editeur") or {}
    au = f.get("auteur") or {}
    ar = f.get("artiste") or {}
    reliab = classify_reliability(f)
    return {
        "id_fiche": f.get("id_fiche"),
        "type": detect_type(f),
        "titre_international": _txt(f.get("titre_international")),
        "titre_japonais": _txt(f.get("titre_japonais")),
        "auteur": _txt(au.get("nom")),
        "artiste": _txt(ar.get("nom")),
        "editeur": _txt(ed.get("nom")),
        "magazine": _txt(ed.get("magazine_serialisation")),
        "isbn_13": _txt(ed.get("isbn_13")),
        "prix": _txt(ed.get("prix")),
        "tags": f.get("tags") or [],
        "sources": tr.get("sources") or [],
        "urls": tr.get("urls") or [],
        "fiabilite": reliab,
        "fiabilite_badge": RELIAB_BADGE[reliab],
        "has_official": has_official_source(f),                       # DEC-035
        "has_forbidden": has_forbidden_content(f),                    # DEC-035 (seuil 0)
        "champs_manquants": tr.get("champs_non_valides") or [],       # pour les leads
        "date_detection": f.get("date_detection"),
    }


def doc_text(n):
    """Texte a embarquer pour le RAG (concatenation des champs signifiants)."""
    parts = [n["titre_international"], n["titre_japonais"], n["auteur"], n["artiste"],
             n["editeur"], n["magazine"], " ".join(n["tags"]), " ".join(n["sources"])]
    return "search_document: " + " | ".join(p for p in parts if p)


def build_report(src_path, normalized):
    by_reliab, by_type, by_dedup = {}, {}, {}
    for n in normalized:
        by_reliab[n["fiabilite"]] = by_reliab.get(n["fiabilite"], 0) + 1
        by_type[n["type"]] = by_type.get(n["type"], 0) + 1
        by_dedup[n.get("dedup", "inconnu")] = by_dedup.get(n.get("dedup", "inconnu"), 0) + 1
    return {
        "source_file": src_path,
        "generated_at": datetime.datetime.now().isoformat(timespec="seconds"),
        "n_fiches": len(normalized),
        "par_fiabilite": by_reliab,
        "par_type": by_type,
        "par_dedup": by_dedup,
        # candidats indexables = tout sauf incomplet (🔴 exclu du RAG par defaut)
        "n_indexables": sum(1 for n in normalized if n["fiabilite"] != "incomplet"),
        # candidats a CREER dans le vault = nouveau ET non-incomplet (dedup G1)
        "n_a_creer": sum(1 for n in normalized
                         if n["fiabilite"] != "incomplet" and n.get("dedup") == "nouveau"),
        "fiches": normalized,
    }


def write_report_md(path, rep):
    L = ["# Rapport d'ingestion veille (dry-run)", "",
         "> Source : `%s`" % rep["source_file"],
         "> Généré : %s · %d fiches" % (rep["generated_at"], rep["n_fiches"]), "",
         "## 📊 Notes de fiabilité", ""]
    for k in ("confirme", "probable", "a_verifier", "incomplet"):
        if k in rep["par_fiabilite"]:
            L.append("- %s : %d" % (RELIAB_BADGE[k], rep["par_fiabilite"][k]))
    L += ["", "Par type : " + ", ".join("%s=%d" % (t, c) for t, c in rep["par_type"].items()),
          "Dedup G1 (vs Master Index) : " + ", ".join("%s=%d" % (d, c) for d, c in rep.get("par_dedup", {}).items()),
          "Indexables RAG (hors 🔴) : %d" % rep["n_indexables"],
          "À créer dans le vault (nouveau ET hors 🔴) : %d" % rep.get("n_a_creer", 0), ""]
    cov = rep.get("couverture", {})
    if cov:
        L += ["## 📈 Couverture (DEC-035)", "",
              "- Fiches sourcées : %.0f%%" % (cov.get("pct_sourced", 0) * 100),
              "- Avec source officielle/primaire : %.0f%%" % (cov.get("pct_official", 0) * 100),
              "- Règle 2 sources (proxy) : %.0f%%" % (cov.get("pct_two_sources", 0) * 100),
              "- Sources de contenu INTERDITES : %d → **%s** (seuil 0)" % (cov.get("n_forbidden", 0), cov.get("verdict", "?")),
              "> Couverture « sources visitées ≥ 95 % » mesurée côté gathering (rapport veille amont).", ""]
    L += ["## Fiches", ""]
    for n in rep["fiches"]:
        L.append("### %s [%s] — %s" % (n["fiabilite_badge"], n.get("dedup", "inconnu"),
                                       n["titre_international"] or "(sans titre)"))
        L.append("- type=%s | auteur=%s | éditeur=%s | ISBN=%s" %
                 (n["type"], n["auteur"] or "—", n["editeur"] or "—", n["isbn_13"] or "—"))
        L.append("- sources=%s" % (", ".join(n["sources"]) or "—"))
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(L))


def index_into_rag(normalized, qdrant, collection, ollama, model):
    """Upsert des fiches de veille (hors 🔴) dans la collection RAG. Reutilise index_vault."""
    import index_vault as iv
    payload_pts = []
    for n in normalized:
        if n["fiabilite"] == "incomplet" or n.get("has_forbidden"):  # DEC-035 : jamais indexer du contenu interdit
            continue
        vec = iv.embed(doc_text(n), ollama, model)
        pid = str(uuid.uuid5(uuid.NAMESPACE_URL, "veille:" + (n["id_fiche"] or n["titre_international"])))
        payload_pts.append({"id": pid, "vector": vec, "payload": {
            "kind": "veille_fiche", "source_pipeline": "veille_externe",
            "title": n["titre_international"], "title_jp": n["titre_japonais"],
            "type": n["type"], "auteur": n["auteur"], "editeur": n["editeur"],
            "isbn_13": n["isbn_13"], "fiabilite": n["fiabilite"],
            "sources": n["sources"], "urls": n["urls"],
            "text": doc_text(n)[len("search_document: "):]}})
    if not payload_pts:
        return 0
    dim = len(payload_pts[0]["vector"])
    iv.ensure_collection(qdrant, collection, dim)
    iv._req("PUT", "%s/collections/%s/points?wait=true" % (qdrant, collection),
            {"points": payload_pts})
    return len(payload_pts)


def build_coverage(normalized):
    """DEC-035 : metrique de couverture par run.
    Seuil valide (2026-06-03) : >=95% sources visitees (mesure gathering, reportee par
    l'agent de veille amont) + 0 source de CONTENU interdite (mesuree ici, bloquante)."""
    n = len(normalized) or 1
    n_sourced = sum(1 for x in normalized if x["sources"])
    n_official = sum(1 for x in normalized if x.get("has_official"))
    n_two = sum(1 for x in normalized if len(x["sources"]) >= 2)
    forbidden = [{"id_fiche": x.get("id_fiche"),
                  "sources": [s for s in x["sources"] if forbidden_content_source(s)]}
                 for x in normalized if x.get("has_forbidden")]
    return {
        "n_fiches": len(normalized),
        "pct_sourced": round(n_sourced / n, 3),
        "pct_official": round(n_official / n, 3),
        "pct_two_sources": round(n_two / n, 3),
        "n_forbidden": len(forbidden),
        "forbidden": forbidden,
        "verdict": "PASS" if len(forbidden) == 0 else "FAIL",
        "seuil": {"sources_visitees_min_pct": 95, "contenu_interdit_max": 0},
    }


def build_leads(normalized):
    """DEC-035 : file de surveillance -> recherche OFFICIELLE.
    Toute fiche 🟠 (a_verifier), ou 🟡/✅ sans source officielle, devient un *lead* :
    une demande de creuser plus profond sur source primaire (editeur, Oricon, BookWalker,
    Natalie, site studio). C'est le role 'signal' des sources non officielles."""
    leads = []
    for n in normalized:
        needs = (n["fiabilite"] == "a_verifier") or (
            n["fiabilite"] in ("probable", "confirme") and not n.get("has_official"))
        if not needs:
            continue
        leads.append({
            "id_fiche": n.get("id_fiche"),
            "titre": n["titre_international"] or n["titre_japonais"],
            "fiabilite": n["fiabilite"],
            "champs_manquants": n.get("champs_manquants", []),
            "sources_actuelles": n["sources"],
            "action": "rechercher source officielle/primaire (editeur, Oricon, BookWalker, Natalie, site studio) puis cross-check",
        })
    return leads


def write_leads(path, leads, src_path):
    """Ecrit la file de leads (JSON + MD) consommable en handoff par Antigravity/Hermes."""
    with open(path, "w", encoding="utf-8") as fh:
        json.dump({"source_file": src_path,
                   "generated_at": datetime.datetime.now().isoformat(timespec="seconds"),
                   "n_leads": len(leads), "leads": leads}, fh, ensure_ascii=False, indent=2)
    md = ["# Leads -> recherche officielle (DEC-035)", "",
          "> Source : `%s` · %d leads" % (src_path, len(leads)),
          "> Chaque entree = fiche a corroborer sur source primaire avant tout ✅.", ""]
    for d in leads:
        md.append("- **%s** [%s] — manque: %s — sources actuelles: %s" % (
            d["titre"] or "(sans titre)", d["fiabilite"],
            ", ".join(d["champs_manquants"]) or "—",
            ", ".join(d["sources_actuelles"]) or "—"))
    with open(os.path.splitext(path)[0] + ".md", "w", encoding="utf-8") as fh:
        fh.write("\n".join(md))


def main():
    ap = argparse.ArgumentParser(description="Pont d'ingestion veille -> fiches + RAG.")
    ap.add_argument("--runs-root", action="append", default=None,
                    help="Racine(s) des sorties veille. Defaut : variable d'env TK_VEILLE_RUNS.")
    ap.add_argument("--dry-run", action="store_true", default=True)
    ap.add_argument("--index", dest="dry_run", action="store_false",
                    help="Desactive le dry-run et indexe reellement dans le RAG.")
    ap.add_argument("--collection", default="vault")
    ap.add_argument("--qdrant", default="http://localhost:6333")
    ap.add_argument("--ollama", default="http://localhost:11434")
    ap.add_argument("--model", default="nomic-embed-text")
    ap.add_argument("--report", default=os.path.join(HERE, "veille_ingest_report.json"))
    ap.add_argument("--master-index", default=os.environ.get("TK_MASTER_INDEX", ""),
                    help="Master Index pour dedup G1 (defaut : env TK_MASTER_INDEX).")
    args = ap.parse_args()

    roots = args.runs_root or DEFAULT_ROOTS
    src = find_latest_fiches(roots)
    if not src:
        print(json.dumps({"error": "aucun veille_fiches_detaillees_*.json trouve", "roots": roots}))
        return 2
    with open(src, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    normalized = [normalize(f) for f in (data.get("fiches") or [])]
    index_titles = load_master_index_titles(args.master_index)
    for n in normalized:
        n["dedup"] = dedup_status(n, index_titles)
    rep = build_report(src, normalized)
    rep["master_index"] = args.master_index or None

    # DEC-035 : file de leads (surveillance -> recherche officielle), ecrite meme en dry-run.
    leads = build_leads(normalized)
    rep["n_leads"] = len(leads)
    leads_path = os.path.join(os.path.dirname(args.report) or HERE, "veille_leads_officiel.json")
    write_leads(leads_path, leads, src)
    rep["leads_file"] = leads_path
    rep["couverture"] = build_coverage(normalized)  # DEC-035

    with open(args.report, "w", encoding="utf-8") as fh:
        json.dump(rep, fh, ensure_ascii=False, indent=2)
    write_report_md(os.path.splitext(args.report)[0] + ".md", rep)

    if not args.dry_run:
        rep["indexed"] = index_into_rag(normalized, args.qdrant, args.collection,
                                        args.ollama, args.model)
    rep_out = {k: v for k, v in rep.items() if k != "fiches"}
    print(json.dumps(rep_out, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    import traceback
    try:
        rc = main()
    except SystemExit:
        raise
    except BaseException:
        tb = traceback.format_exc()
        with open(os.path.join(HERE, "veille_ingest_crash.txt"), "w", encoding="utf-8") as _f:
            _f.write(tb)
        print(tb); rc = 99
    raise SystemExit(rc)
