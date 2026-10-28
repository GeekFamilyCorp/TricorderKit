# -*- coding: utf-8 -*-
"""batch_runner.py — resilient adaptive batch processing for large file trees.

Solves saturation when processing huge Markdown/knowledge trees (100k+ files) in a
single pass (timeouts, RAM). Principle = AIMD (Additive-Increase / Multiplicative-Decrease,
TCP congestion control):
  - start at 100 items/batch;
  - +ADD after each fast, successful batch (additive increase, cap HI);
  - x MUL (0.5) as soon as a batch exceeds the time budget OR raises (multiplicative
    decrease, floor LO).
  -> grow while it flows, shrink *before* it degrades.

RESILIENCE:
  - CHECKPOINT after every batch (JSON) -> exact resume after crash/stop/reboot.
  - Path list CACHED (names scanned once, no re-scan on resume).
  - "poison pill": after too many failures at the floor, isolate 1 offending item and
    advance (never an infinite loop).
  - Designed to run DETACHED (nohup / Start-Process); the caller only launches + reads state.

Inspiration: AIMD (TCP), a-rahimi/python-checkpointing (resume), NVlabs/AdaBatch (adaptive batch).
No third-party dependency.

API:
  from batch_runner import AdaptiveBatchRunner, walk_files
  paths = walk_files(root, exts=(".md",), state_key="my_op")
  AdaptiveBatchRunner("my_op").run(paths, process=lambda batch: do_work(batch))

CLI (built-in resumable ops over a file tree):
  python batch_runner.py --root <dir> --op <audit_ts|backfill_ts|noop> [--reset] [--start 100] [--budget 20]
"""
import os, re, sys, json, time, datetime

DEFAULT_STATE = os.environ.get("BATCH_STATE_DIR",
                               os.path.join(os.path.expanduser("~"), ".batch_state"))
# directory-name fragments to skip while walking (archives, VCS, caches)
SKIP_DIRS = ("_ARCHIVE", "_Archive", ".git", ".trash", ".obsidian", "node_modules", "__pycache__")


def walk_files(root, exts=(".md",), state_key=None, state_dir=DEFAULT_STATE, refresh=False,
               skip_dirs=SKIP_DIRS):
    """Cached list of files under root with the given extensions, excluding skip_dirs.
    Only NAMES are scanned (lightweight); the list is cached so resume never re-walks."""
    os.makedirs(state_dir, exist_ok=True)
    cache = os.path.join(state_dir, "%s.paths.txt" % (state_key or "paths"))
    if os.path.exists(cache) and not refresh:
        with open(cache, encoding="utf-8") as f:
            return [ln.rstrip("\n") for ln in f if ln.strip()]
    paths = []
    for r, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if not any(s in d for s in skip_dirs)]
        if any(s in r for s in skip_dirs):
            continue
        for fn in files:
            if fn.endswith(tuple(exts)):
                paths.append(os.path.join(r, fn))
    with open(cache, "w", encoding="utf-8") as f:
        f.write("\n".join(paths))
    return paths


class AdaptiveBatchRunner:
    """AIMD-controlled, checkpointed batch processor. Resumable and detach-friendly."""

    def __init__(self, name, state_dir=DEFAULT_STATE, start=100, lo=20, hi=2000,
                 add=50, mul=0.5, budget=20.0, max_fail_at_lo=3):
        self.name = name
        os.makedirs(state_dir, exist_ok=True)
        self.state_file = os.path.join(state_dir, "%s.state.json" % name)
        self.start, self.lo, self.hi = start, lo, hi
        self.add, self.mul, self.budget = add, mul, budget
        self.max_fail_at_lo = max_fail_at_lo

    def _load(self):
        try:
            return json.load(open(self.state_file, encoding="utf-8"))
        except Exception:
            return {"cursor": 0, "batch": self.start, "done": 0, "errors": 0,
                    "started": datetime.datetime.now().isoformat(timespec="seconds")}

    def _save(self, st):
        st["updated"] = datetime.datetime.now().isoformat(timespec="seconds")
        tmp = self.state_file + ".tmp"
        json.dump(st, open(tmp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        os.replace(tmp, self.state_file)

    def reset(self):
        for p in (self.state_file, self.state_file + ".tmp"):
            if os.path.exists(p):
                os.remove(p)

    def run(self, items, process):
        """items = indexable list; process(sublist) handles one batch (may raise). Resumable."""
        st = self._load()
        total = len(items)
        st["total"] = total
        batch = int(st.get("batch", self.start))
        fails_at_lo = 0
        print("[%s] RESUME cursor=%d/%d batch=%d (AIMD %d..%d, +%d/x%.2f, budget %.0fs)"
              % (self.name, st["cursor"], total, batch, self.lo, self.hi, self.add, self.mul, self.budget),
              flush=True)
        while st["cursor"] < total:
            n = min(batch, total - st["cursor"])
            chunk = items[st["cursor"]:st["cursor"] + n]
            t0 = time.time()
            try:
                process(chunk)
                dt = time.time() - t0
                st["cursor"] += n
                st["done"] += n
                if dt > self.budget:
                    batch = max(self.lo, int(batch * self.mul)); flag = "SLOW-"
                elif dt < self.budget * 0.6:
                    batch = min(self.hi, batch + self.add); flag = "OK+"
                else:
                    flag = "OK="
                fails_at_lo = 0
                st["batch"] = batch
                self._save(st)
                print("[%s] %s cursor=%d/%d n=%d %.1fs -> batch=%d"
                      % (self.name, flag, st["cursor"], total, n, dt, batch), flush=True)
            except Exception as e:
                st["errors"] += 1
                new = max(self.lo, int(batch * self.mul))
                print("[%s] ERROR (%s) n=%d -> batch %d->%d"
                      % (self.name, type(e).__name__, n, batch, new), flush=True)
                if batch <= self.lo:
                    fails_at_lo += 1
                    if fails_at_lo >= self.max_fail_at_lo:
                        bad = items[st["cursor"]]
                        print("[%s] POISON PILL skipping: %s" % (self.name, bad), flush=True)
                        st["cursor"] += 1
                        st["errors"] += 1
                        fails_at_lo = 0
                        self._save(st)
                batch = new
                st["batch"] = batch
                self._save(st)
                time.sleep(1.0)
        print("[%s] DONE done=%d errors=%d" % (self.name, st["done"], st["errors"]), flush=True)
        return st


# ------------------------------------------------------------------ built-in example ops
_FMK = re.compile(r"^([A-Za-z0-9_]+)\s*:")
CRE = ("created_at", "created", "date_created", "collected_at", "collected")
UPD = ("updated_at", "updated", "date_updated", "modified")


def _head_keys(path, nbytes=1500):
    with open(path, encoding="utf-8", errors="replace") as f:
        if f.readline().strip() != "---":
            return None
        keys = {}
        for ln in f:
            if ln.strip() == "---":
                break
            m = _FMK.match(ln)
            if m:
                keys[m.group(1)] = ln.split(":", 1)[1].strip().strip('"').strip("'")
        return keys


def op_audit_ts(paths):
    """Coverage audit of created/updated frontmatter fields."""
    hc = hu = n = 0
    for p in paths:
        k = _head_keys(p)
        if k is None:
            continue
        n += 1
        hc += any(x in k for x in CRE)
        hu += any(x in k for x in UPD)
    op_audit_ts.acc[0] += n; op_audit_ts.acc[1] += hc; op_audit_ts.acc[2] += hu
op_audit_ts.acc = [0, 0, 0]


def op_backfill_ts(paths):
    """Additively backfill missing created_at/updated_at (NO overwrite)."""
    for p in paths:
        k = _head_keys(p)
        if k is None:
            continue
        has_c = any(x in k for x in CRE)
        has_u = any(x in k for x in UPD)
        if has_c and has_u:
            continue
        cre = next((k[x] for x in CRE if k.get(x)), None) or \
            datetime.date.fromtimestamp(os.path.getmtime(p)).isoformat()
        ins = []
        if not has_c:
            ins.append('created_at: "%s"' % cre)
        if not has_u:
            ins.append('updated_at: "%s"' % cre)
        txt = open(p, encoding="utf-8", errors="replace").read()
        lines = txt.split("\n")
        if lines and lines[0].strip() == "---":
            lines[1:1] = ins
            open(p, "w", encoding="utf-8", newline="\n").write("\n".join(lines))


def op_noop(paths):
    time.sleep(0.001 * len(paths))


OPS = {"audit_ts": op_audit_ts, "backfill_ts": op_backfill_ts, "noop": op_noop}


def main():
    import argparse
    ap = argparse.ArgumentParser(description="Resilient adaptive batch runner (AIMD + checkpoint).")
    ap.add_argument("--root", required=True)
    ap.add_argument("--op", choices=list(OPS), default="noop")
    ap.add_argument("--state", default=DEFAULT_STATE)
    ap.add_argument("--start", type=int, default=100)
    ap.add_argument("--budget", type=float, default=20.0)
    ap.add_argument("--reset", action="store_true")
    a = ap.parse_args()
    key = "%s_%s" % (a.op, re.sub(r"[^A-Za-z0-9]", "_", os.path.basename(a.root.rstrip("/\\"))))
    paths = walk_files(a.root, state_key=key, state_dir=a.state, refresh=a.reset)
    print("files listed:", len(paths))
    r = AdaptiveBatchRunner(key, state_dir=a.state, start=a.start, budget=a.budget)
    if a.reset:
        r.reset()
    r.run(paths, OPS[a.op])
    if a.op == "audit_ts":
        n, hc, hu = op_audit_ts.acc
        print("AUDIT: files=%d created=%d (%.1f%%) updated=%d (%.1f%%)"
              % (n, hc, 100 * hc / max(n, 1), hu, 100 * hu / max(n, 1)))


if __name__ == "__main__":
    main()
