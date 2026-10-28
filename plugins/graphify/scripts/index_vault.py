#!/usr/bin/env python3
"""index_vault.py - Indexeur de vault Obsidian -> Qdrant (G3 / DEC-023).

1 note .md = 1 point. Embeddings nomic-embed-text (768d) via Ollama REST (urllib pur).
Le payload porte le texte + metadonnees -> decouple search_vault de tout index positionnel.
Idempotent : point id = uuid5(rel_path). Re-run = upsert, pas de doublon.

Convention nomic : prefixe 'search_document: ' a l'indexation, 'search_query: ' a la requete.

Usage :
  python index_vault.py --dry-run            # valide chemin, compte, dim embeddings (aucune ecriture)
  python index_vault.py --limit 20           # test reel restreint (cree collection + upsert 20)
  python index_vault.py                       # run complet
"""
from __future__ import annotations
import argparse, json, os, time, uuid, urllib.request, urllib.error

DOC_PREFIX = "search_document: "
HERE = os.path.dirname(os.path.abspath(__file__))


def _req(method, url, body=None, timeout=120):
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(url, data=data, method=method,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        raw = r.read().decode("utf-8", "replace")
    return json.loads(raw) if raw else {}


def embed(text, ollama, model, keep_alive="30m"):
    # keep_alive maintient nomic resident -> evite le rechargement a froid (~6s) entre appels.
    res = _req("POST", ollama.rstrip("/") + "/api/embeddings",
               {"model": model, "prompt": text, "keep_alive": keep_alive}, timeout=120)
    return res["embedding"]


def ensure_collection(qdrant, name, dim):
    try:
        _req("GET", "%s/collections/%s" % (qdrant, name))
        return "exists"
    except urllib.error.HTTPError as e:
        if e.code != 404:
            raise
    _req("PUT", "%s/collections/%s" % (qdrant, name),
         {"vectors": {"size": dim, "distance": "Cosine"}})
    return "created"


def discover(root):
    out = []
    for dp, _dirs, files in os.walk(root):
        for fn in files:
            if fn.lower().endswith(".md"):
                out.append(os.path.join(dp, fn))
    return sorted(out)


def classify(rel, fn):
    low = fn.lower()
    rl = rel.lower()
    if low == "index.md" or low.startswith("index_") or low == "index":
        return "index"
    if "queue" in low or "rollout" in low:
        return "queue"
    if rel.startswith("00_") or "migration" in rl or "_system" in rl or "backup" in rl:
        return "system"
    return "fiche"


def _write_json(path, obj):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)


def main():
    ap = argparse.ArgumentParser(description="Indexeur vault -> Qdrant (G3).")
    ap.add_argument("--vault-root", default=os.environ.get("TK_VAULT_ROOT", ""),
                    help="Racine du vault a indexer (defaut : variable d'env TK_VAULT_ROOT).")
    ap.add_argument("--collection", default="vault")
    ap.add_argument("--qdrant", default="http://localhost:6333")
    ap.add_argument("--ollama", default="http://localhost:11434")
    ap.add_argument("--model", default="nomic-embed-text")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--batch", type=int, default=64)
    ap.add_argument("--embed-cap", type=int, default=6000)
    ap.add_argument("--text-cap", type=int, default=16000)
    ap.add_argument("--report", default=os.path.join(HERE, "index_report.json"))
    ap.add_argument("--incremental", action="store_true",
                    help="Ne (re)indexe que les notes nouvelles/modifiees (etat mtime). Pour run nocturne leger.")
    ap.add_argument("--state", default=os.path.join(HERE, "index_state.json"))
    args = ap.parse_args()

    root = args.vault_root
    if not os.path.isdir(root):
        _write_json(args.report, {"error": "vault-root introuvable", "path": root})
        print(json.dumps({"error": "vault-root introuvable", "path": root})); return 2

    files = discover(root)
    if args.limit:
        files = files[:args.limit]
    report = {"vault_root": root, "collection": args.collection,
              "n_files": len(files), "dry_run": bool(args.dry_run)}

    # mode incremental : ne garder que les notes nouvelles/modifiees (etat mtime)
    prev_state = {}
    if args.incremental and os.path.isfile(args.state):
        try:
            prev_state = json.load(open(args.state, encoding="utf-8"))
        except Exception:
            prev_state = {}
    if args.incremental:
        def _rel(fp):
            return os.path.relpath(fp, root).replace("\\", "/")
        changed = [fp for fp in files
                   if str(prev_state.get(_rel(fp))) != str(int(os.path.getmtime(fp)))]
        report["n_changed"] = len(changed)
        files = changed
        if not files:
            report.update({"n_ok": 0, "n_err": 0, "note": "incremental: rien a indexer"})
            _write_json(args.report, report)
            print(json.dumps(report, ensure_ascii=False)); return 0

    # validation dimension embeddings sur la 1re note lisible
    dim = None
    for fp in files:
        try:
            txt = open(fp, "r", encoding="utf-8", errors="replace").read()
        except Exception:
            continue
        dim = len(embed(DOC_PREFIX + txt[:args.embed_cap], args.ollama, args.model))
        break
    report["embed_dim"] = dim

    if args.dry_run:
        report["sample_titles"] = [os.path.basename(f) for f in files[:5]]
        _write_json(args.report, report)
        print(json.dumps(report, ensure_ascii=False)); return 0

    if dim != 768:
        report["error"] = "dim inattendue: %s" % dim
        _write_json(args.report, report); print(json.dumps(report)); return 3

    report["collection_status"] = ensure_collection(args.qdrant, args.collection, dim)

    t0 = time.time(); n_ok = 0; n_err = 0; batch = []; errors = []; new_state = {}
    prog_path = os.path.join(HERE, "index_progress.json")
    for i, fp in enumerate(files):
        try:
            text = open(fp, "r", encoding="utf-8", errors="replace").read()
            rel = os.path.relpath(fp, root).replace("\\", "/")
            title = os.path.splitext(os.path.basename(fp))[0]
            folder_top = rel.split("/", 1)[0] if "/" in rel else ""
            vec = embed(DOC_PREFIX + (title + "\n\n" + text)[:args.embed_cap],
                        args.ollama, args.model)
            batch.append({"id": str(uuid.uuid5(uuid.NAMESPACE_URL, rel)),
                          "vector": vec,
                          "payload": {"path": rel, "title": title,
                                      "folder_top": folder_top,
                                      "kind": classify(rel, os.path.basename(fp)),
                                      "n_chars": len(text),
                                      "text": text[:args.text_cap]}})
            new_state[rel] = int(os.path.getmtime(fp))
            n_ok += 1
        except Exception as e:
            n_err += 1; errors.append({"file": fp, "err": str(e)[:200]})
        if len(batch) >= args.batch:
            _req("PUT", "%s/collections/%s/points?wait=true" % (args.qdrant, args.collection),
                 {"points": batch}); batch = []
            _write_json(prog_path, {"done": i + 1, "n_ok": n_ok, "n_err": n_err,
                                    "elapsed_s": round(time.time() - t0, 1)})
    if batch:
        _req("PUT", "%s/collections/%s/points?wait=true" % (args.qdrant, args.collection),
             {"points": batch})

    if args.incremental:
        prev_state.update(new_state)
        _write_json(args.state, prev_state)

    info = _req("GET", "%s/collections/%s" % (args.qdrant, args.collection))
    report.update({"n_ok": n_ok, "n_err": n_err,
                   "points_count": info.get("result", {}).get("points_count"),
                   "elapsed_s": round(time.time() - t0, 1),
                   "errors_sample": errors[:10]})
    _write_json(args.report, report)
    print(json.dumps(report, ensure_ascii=False)); return 0


if __name__ == "__main__":
    import traceback
    try:
        rc = main()
    except SystemExit:
        raise
    except BaseException:
        tb = traceback.format_exc()
        with open(os.path.join(HERE, "index_crash.txt"), "w", encoding="utf-8") as _f:
            _f.write(tb)
        print(tb)
        rc = 99
    raise SystemExit(rc)
