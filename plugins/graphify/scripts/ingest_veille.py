#!/usr/bin/env python3
"""ingest_veille.py - Veille d'actualite generique (flux RSS/Atom) -> fiches + RAG.

Lit une liste CONFIGURABLE de flux RSS 2.0 / Atom, normalise chaque entree en fiche,
classe sa fiabilite d'apres le tier de la source, deduplique, puis (en option) indexe
dans le RAG local. Aucun domaine metier n'est code ici : un domaine prive fournit ses
propres flux et listes de sources via son linked_project (variables d'environnement).

Etapes :
  1. Charge les flux : --feed (repetable), --feeds-file (une URL par ligne),
     variable d'env TK_VEILLE_FEEDS (URLs separees par des virgules), ou --input
     (fichier local RSS/Atom/JSON, utile hors ligne et pour les tests).
  2. Normalise chaque entree + classe la fiabilite (confirme / probable / a_verifier / incomplet).
  3. --dry-run (DEFAUT) : ecrit un rapport (MD + JSON) de ce qui SERAIT indexe. Aucune ecriture RAG.
  4. --index : embeddings nomic + upsert Qdrant 'vault' (fiches de veille).

Exemples de flux (theme : logiciel libre et recherche technique) :
  http://export.arxiv.org/api/query?search_query=all:%22vector+databases%22&max_results=20
  http://export.arxiv.org/api/query?search_query=all:%22local-first+software%22&max_results=20
  https://github.com/temporalio/temporal/releases.atom

Usage :
  python ingest_veille.py --feed http://export.arxiv.org/api/query?search_query=all:qdrant
  python ingest_veille.py --input ./sample_feed.xml --dry-run
  python ingest_veille.py --use-example-feeds --index      # apres validation
"""
from __future__ import annotations
import argparse, datetime, hashlib, json, os, re, unicodedata, urllib.parse, urllib.request, uuid
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))

EXAMPLE_FEEDS = (
    "http://export.arxiv.org/api/query?search_query=all:%22local-first+software%22&max_results=20",
    "http://export.arxiv.org/api/query?search_query=all:%22vector+databases%22&max_results=20",
    "http://export.arxiv.org/api/query?search_query=all:%22temporal+workflows%22&max_results=20",
)


def _split_env(name):
    return [s.strip() for s in os.environ.get(name, "").split(",") if s.strip()]


# --- Tiering des sources (primaire vs signal) -------------------------------------
# Une source "signal" ne FONDE JAMAIS seule un ✅ Confirme : elle sert de lead (🟠)
# ou de 2e source de cross-check. Listes surchargeables par linked_project (env).
PRIMARY_SOURCE_HINTS = tuple(_split_env("TK_VEILLE_PRIMARY")) or (
    "arxiv.org", "github.com", "wikipedia.org", "sqlite.org", "neo4j.com", "qdrant.tech",
    "temporal.io", "ollama.com", "apache.org", "mozilla.org", "official",
)
SIGNAL_SOURCE_HINTS = tuple(_split_env("TK_VEILLE_SIGNAL")) or (
    "news.ycombinator.com", "hn.algolia.com", "reddit.com", "twitter.com", "x.com",
    "medium.com", "dev.to",
)
# Sources BLOQUEES (contenu copie, fermes de contenu...) : seuil tolere = 0.
FORBIDDEN_SOURCE_HINTS = tuple(_split_env("TK_VEILLE_BLOCKLIST"))


def source_tier(s):
    """Classe une source/URL : 'primaire' ou 'signal'. Defaut prudent : inconnue = 'signal'."""
    low = (s or "").lower()
    if any(h in low for h in SIGNAL_SOURCE_HINTS):
        return "signal"
    if any(h in low for h in PRIMARY_SOURCE_HINTS):
        return "primaire"
    return "signal"


def forbidden_source(s):
    low = (s or "").lower()
    return any(h in low for h in FORBIDDEN_SOURCE_HINTS)


# --- Lecture des flux ---------------------------------------------------------------
_ATOM = "{http://www.w3.org/2005/Atom}"


def _txt(v):
    return re.sub(r"\s+", " ", (v or "")).strip()


def _strip_html(s):
    return _txt(re.sub(r"<[^>]+>", " ", s or ""))


def parse_feed(raw, feed_url=""):
    """Texte RSS 2.0 / Atom -> liste d'entrees brutes (dict)."""
    root = ET.fromstring(raw)
    items = []
    if root.tag.endswith("rss") or root.find("channel") is not None:
        for it in root.iter("item"):
            items.append({
                "title": _txt(it.findtext("title")),
                "link": _txt(it.findtext("link")),
                "summary": _strip_html(it.findtext("description")),
                "published": _txt(it.findtext("pubDate")),
                "authors": [_txt(a.text) for a in it.findall("author") if _txt(a.text)],
                "tags": [_txt(c.text) for c in it.findall("category") if _txt(c.text)],
                "id": _txt(it.findtext("guid")),
                "feed": feed_url,
            })
    else:  # Atom
        for e in root.iter(_ATOM + "entry"):
            link = ""
            for lk in e.findall(_ATOM + "link"):
                if lk.get("rel", "alternate") == "alternate":
                    link = lk.get("href", "")
                    break
            items.append({
                "title": _txt(e.findtext(_ATOM + "title")),
                "link": _txt(link),
                "summary": _strip_html(e.findtext(_ATOM + "summary") or e.findtext(_ATOM + "content")),
                "published": _txt(e.findtext(_ATOM + "published") or e.findtext(_ATOM + "updated")),
                "authors": [_txt(a.findtext(_ATOM + "name")) for a in e.findall(_ATOM + "author")
                            if _txt(a.findtext(_ATOM + "name"))],
                "tags": [c.get("term", "") for c in e.findall(_ATOM + "category") if c.get("term")],
                "id": _txt(e.findtext(_ATOM + "id")),
                "feed": feed_url,
            })
    return items


def load_input(path):
    """Fichier local : RSS/Atom (.xml/.atom/.rss) ou JSON ({"items": [...]} ou liste)."""
    with open(path, "r", encoding="utf-8") as fh:
        raw = fh.read()
    if path.lower().endswith(".json"):
        data = json.loads(raw)
        items = data.get("items", []) if isinstance(data, dict) else data
        return [dict(i, feed=i.get("feed", path)) for i in items if isinstance(i, dict)]
    return parse_feed(raw, feed_url=path)


def fetch_feed(url, timeout=20):
    req = urllib.request.Request(url, headers={"User-Agent": "TricorderKit-veille/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as r:  # noqa: S310 (URL fournie par l'operateur)
        return parse_feed(r.read().decode("utf-8", errors="replace"), feed_url=url)


# --- Normalisation + fiabilite ------------------------------------------------------
def classify_reliability(n):
    """confirme / probable / a_verifier / incomplet.
    Un ✅ EXIGE une source primaire ; une source signal seule plafonne a 🟠."""
    if not n["title"] or not n["link"]:
        return "incomplet"      # 🔴
    if n["has_primary"]:
        return "confirme" if n["summary"] and n["published"] else "probable"
    return "a_verifier"         # 🟠


RELIAB_BADGE = {"confirme": "✅ Confirmé", "probable": "🟡 Probable",
                "a_verifier": "🟠 À vérifier", "incomplet": "🔴 Incomplet"}


def normalize(raw):
    """Entree de flux brute -> fiche normalisee exploitable (vault/RAG)."""
    link = raw.get("link") or ""
    sources = [s for s in {urllib.parse.urlparse(link).netloc, raw.get("feed") or ""} if s]
    n = {
        "id_fiche": raw.get("id") or link or None,
        "type": raw.get("type") or "source",
        "title": _txt(raw.get("title")),
        "link": link,
        "summary": _txt(raw.get("summary"))[:2000],
        "published": raw.get("published") or "",
        "authors": raw.get("authors") or [],
        "tags": raw.get("tags") or [],
        "sources": sorted(sources),
    }
    n["has_primary"] = any(source_tier(s) == "primaire" for s in [link] + n["sources"])
    n["has_forbidden"] = any(forbidden_source(s) for s in [link] + n["sources"])
    n["fiabilite"] = classify_reliability(n)
    n["fiabilite_badge"] = RELIAB_BADGE[n["fiabilite"]]
    return n


# --- Dedup : contre le Master Index et intra-run ------------------------------------
def _norm_title(s):
    if not s:
        return ""
    s = unicodedata.normalize("NFKD", str(s))
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", " ", s.lower()).strip()


def load_master_index_titles(path):
    """Tableau Markdown du Master Index (| ID | Type | Titre | ...) -> set de titres normalises."""
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


def dedup(normalized, index_titles):
    """Retire les doublons intra-run (meme lien ou meme titre) et marque nouveau/existant."""
    seen, out = set(), []
    for n in normalized:
        key = n["link"] or _norm_title(n["title"])
        if key in seen:
            continue
        seen.add(key)
        if not index_titles:
            n["dedup"] = "inconnu"
        else:
            n["dedup"] = "existant" if _norm_title(n["title"]) in index_titles else "nouveau"
        out.append(n)
    return out


# --- Rapports -----------------------------------------------------------------------
def doc_text(n):
    parts = [n["title"], n["summary"], ", ".join(n["authors"]), " ".join(n["tags"]),
             " ".join(n["sources"])]
    return "search_document: " + " | ".join(p for p in parts if p)


def build_report(feeds, normalized):
    by_reliab, by_dedup = {}, {}
    for n in normalized:
        by_reliab[n["fiabilite"]] = by_reliab.get(n["fiabilite"], 0) + 1
        by_dedup[n.get("dedup", "inconnu")] = by_dedup.get(n.get("dedup", "inconnu"), 0) + 1
    return {
        "feeds": feeds,
        "generated_at": datetime.datetime.now().isoformat(timespec="seconds"),
        "n_fiches": len(normalized),
        "par_fiabilite": by_reliab,
        "par_dedup": by_dedup,
        "n_indexables": sum(1 for n in normalized
                            if n["fiabilite"] != "incomplet" and not n["has_forbidden"]),
        "fiches": normalized,
    }


def build_coverage(normalized):
    """Couverture par run : part des fiches avec source primaire + 0 source bloquee (bloquant)."""
    n = len(normalized) or 1
    forbidden = [{"id_fiche": x["id_fiche"], "sources": x["sources"]}
                 for x in normalized if x["has_forbidden"]]
    return {
        "n_fiches": len(normalized),
        "pct_primary": round(sum(1 for x in normalized if x["has_primary"]) / n, 3),
        "n_forbidden": len(forbidden),
        "forbidden": forbidden,
        "verdict": "PASS" if not forbidden else "FAIL",
    }


def build_leads(normalized):
    """Fiches 🟠 (source signal seule) -> leads a corroborer sur une source primaire."""
    return [{"id_fiche": n["id_fiche"], "titre": n["title"], "fiabilite": n["fiabilite"],
             "sources_actuelles": n["sources"],
             "action": "rechercher une source primaire (depot, article, documentation officielle)"}
            for n in normalized if n["fiabilite"] == "a_verifier"]


def write_report_md(path, rep):
    L = ["# Rapport d'ingestion veille", "",
         "> Flux : %s" % (", ".join("`%s`" % f for f in rep["feeds"]) or "—"),
         "> Généré : %s · %d fiches" % (rep["generated_at"], rep["n_fiches"]), "",
         "## Notes de fiabilité", ""]
    for k in ("confirme", "probable", "a_verifier", "incomplet"):
        if k in rep["par_fiabilite"]:
            L.append("- %s : %d" % (RELIAB_BADGE[k], rep["par_fiabilite"][k]))
    cov = rep.get("couverture", {})
    L += ["", "Dedup (vs Master Index) : " + ", ".join("%s=%d" % kv for kv in rep["par_dedup"].items()),
          "Indexables RAG (hors 🔴 et sources bloquées) : %d" % rep["n_indexables"],
          "Sources primaires : %.0f%% · sources bloquées : %d → **%s**" % (
              cov.get("pct_primary", 0) * 100, cov.get("n_forbidden", 0), cov.get("verdict", "?")),
          "", "## Fiches", ""]
    for n in rep["fiches"]:
        L.append("### %s [%s] — %s" % (n["fiabilite_badge"], n.get("dedup", "inconnu"),
                                       n["title"] or "(sans titre)"))
        L.append("- lien=%s | publié=%s" % (n["link"] or "—", n["published"] or "—"))
        L.append("- sources=%s" % (", ".join(n["sources"]) or "—"))
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(L))


def index_into_rag(normalized, qdrant, collection, ollama, model):
    """Upsert des fiches (hors 🔴 et sources bloquees) dans la collection RAG via index_vault."""
    import index_vault as iv
    pts = []
    for n in normalized:
        if n["fiabilite"] == "incomplet" or n["has_forbidden"]:
            continue
        key = n["id_fiche"] or hashlib.sha1(n["title"].encode("utf-8")).hexdigest()
        pts.append({"id": str(uuid.uuid5(uuid.NAMESPACE_URL, "veille:" + key)),
                    "vector": iv.embed(doc_text(n), ollama, model),
                    "payload": {"kind": "veille_fiche", "source_pipeline": "veille_rss",
                                "title": n["title"], "link": n["link"], "type": n["type"],
                                "authors": n["authors"], "published": n["published"],
                                "fiabilite": n["fiabilite"], "sources": n["sources"],
                                "text": doc_text(n)[len("search_document: "):]}})
    if not pts:
        return 0
    iv.ensure_collection(qdrant, collection, len(pts[0]["vector"]))
    iv._req("PUT", "%s/collections/%s/points?wait=true" % (qdrant, collection), {"points": pts})
    return len(pts)


def resolve_feeds(args):
    feeds = list(args.feed or [])
    if args.feeds_file and os.path.isfile(args.feeds_file):
        with open(args.feeds_file, "r", encoding="utf-8") as fh:
            feeds += [l.strip() for l in fh if l.strip() and not l.lstrip().startswith("#")]
    feeds += _split_env("TK_VEILLE_FEEDS")
    if args.use_example_feeds:
        feeds += list(EXAMPLE_FEEDS)
    return list(dict.fromkeys(feeds))


def main(argv=None):
    ap = argparse.ArgumentParser(description="Veille RSS/Atom generique -> fiches + RAG.")
    ap.add_argument("--feed", action="append", help="URL d'un flux RSS/Atom (repetable).")
    ap.add_argument("--feeds-file", default=os.environ.get("TK_VEILLE_FEEDS_FILE", ""),
                    help="Fichier texte : une URL de flux par ligne (# = commentaire).")
    ap.add_argument("--use-example-feeds", action="store_true",
                    help="Ajoute les flux d'exemple (arXiv : local-first, vector databases, temporal).")
    ap.add_argument("--input", action="append", default=None,
                    help="Fichier local RSS/Atom/JSON a ingerer (hors ligne).")
    ap.add_argument("--dry-run", action="store_true", default=True)
    ap.add_argument("--index", dest="dry_run", action="store_false",
                    help="Desactive le dry-run et indexe reellement dans le RAG.")
    ap.add_argument("--collection", default="vault")
    ap.add_argument("--qdrant", default="http://localhost:6333")
    ap.add_argument("--ollama", default="http://localhost:11434")
    ap.add_argument("--model", default="nomic-embed-text")
    ap.add_argument("--report", default=os.path.join(HERE, "veille_ingest_report.json"))
    ap.add_argument("--master-index", default=os.environ.get("TK_MASTER_INDEX", ""),
                    help="Master Index pour la dedup (defaut : env TK_MASTER_INDEX).")
    args = ap.parse_args(argv)

    feeds, raw, errors = resolve_feeds(args), [], []
    for path in args.input or []:
        raw += load_input(path)
    for url in feeds:
        try:
            raw += fetch_feed(url)
        except Exception as e:  # un flux en panne ne bloque pas les autres
            errors.append({"feed": url, "error": str(e)[:200]})
    sources = (args.input or []) + feeds
    if not sources:
        print(json.dumps({"error": "aucun flux configure (--feed, --feeds-file, TK_VEILLE_FEEDS, --input)"}))
        return 2

    normalized = dedup([normalize(r) for r in raw], load_master_index_titles(args.master_index))
    rep = build_report(sources, normalized)
    rep["master_index"] = args.master_index or None
    rep["feed_errors"] = errors
    rep["couverture"] = build_coverage(normalized)
    leads = build_leads(normalized)
    rep["n_leads"] = len(leads)
    leads_path = os.path.join(os.path.dirname(args.report) or HERE, "veille_leads.json")
    with open(leads_path, "w", encoding="utf-8") as fh:
        json.dump({"generated_at": rep["generated_at"], "leads": leads}, fh, ensure_ascii=False, indent=2)
    rep["leads_file"] = leads_path

    if not args.dry_run:
        rep["indexed"] = index_into_rag(normalized, args.qdrant, args.collection,
                                        args.ollama, args.model)
    with open(args.report, "w", encoding="utf-8") as fh:
        json.dump(rep, fh, ensure_ascii=False, indent=2)
    write_report_md(os.path.splitext(args.report)[0] + ".md", rep)
    print(json.dumps({k: v for k, v in rep.items() if k != "fiches"}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
