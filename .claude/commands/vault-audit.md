---
description: Audit vault integrity using manifest, hashes, links, and known optimization rules.
allowed-tools: Bash, Read, Grep
---

Run `python scripts/vault_delta.py --vault . --manifest .tricorderkit/index/manifest.jsonl --out .tricorderkit/reports/delta_report.md`.
Check empty folders, large files, duplicate filenames, broken-looking links, missing templates and secrets patterns. Read generated reports before target files.
