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

    if not _txt(f.get("titre_international")) or (not valides and len(non_valides) >= 5):
        return "incomplet"      # 🔴
    if niveau in ("haute", "elevee", "élevée") and len(sources) >= 2 and valides:
        return "confirme"       # ✅
    if niveau in ("haute", "elevee", "élevée") and sources and titre_jp_ok:
        return "confirme"       # ✅
    if niveau in ("moyenne",) and sources:
        return "probable"       # 🟡
    if sources:
        return "a_verifier"     # 🟠
    return "incomplet"          # 🔴


RELIAB_BADGE = {"confirme": "✅ Confirmé", "probable": "🟡 Probable",
                "a_verifier": "🟠 À vérifier", "incomplet": "🔴 Incomplet"}


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
          "À créer dans le vault (nouveau ET hors 🔴) : %d" % rep.get("n_a_creer", 0), "",
          "## Fiches", ""]
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
        if n["fiabilite"] == "incomplet":
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
