# tools/batch — Resilient adaptive batch runner

Process very large file trees (100k+ files) **without saturating** the host, and **resume**
exactly where you stopped after a crash, timeout, or reboot.

## Why

Scanning a huge knowledge base in a single synchronous pass causes timeouts and memory
pressure. This runner processes items in **adaptive batches** and **checkpoints** after each
one, so long jobs are safe to run detached and to interrupt.

## How — AIMD (Additive-Increase / Multiplicative-Decrease)

The batch size is controlled like TCP congestion:

- start at **100** items/batch;
- **+50** after each fast, successful batch (cap 2000);
- **×0.5** as soon as a batch exceeds the time budget **or** raises (floor 20).

Grow while it flows, shrink *before* it degrades. State (cursor, batch size) is written to
JSON after every batch → re-running the same command **resumes at the checkpoint**. The file
list is cached, so resume never re-walks the tree. A "poison pill" isolates a persistently
failing item instead of looping forever.

## Use

```python
from batch_runner import AdaptiveBatchRunner, walk_files
paths = walk_files(root, exts=(".md",), state_key="my_op")
AdaptiveBatchRunner("my_op").run(paths, process=lambda batch: do_work(batch))
```

Built-in CLI ops over a Markdown tree (resumable):

```bash
python batch_runner.py --root <dir> --op audit_ts        # coverage of created/updated
python batch_runner.py --root <dir> --op backfill_ts     # additively backfill timestamps
# resume: re-run the same command (continues at checkpoint); add --reset to start over
```

Recommended: run detached (`nohup` / `Start-Process`) and poll the state file
`<state_dir>/<name>.state.json`.

Inspiration: AIMD (TCP), `a-rahimi/python-checkpointing` (resume), `NVlabs/AdaBatch`
(adaptive batch). No third-party dependency.
