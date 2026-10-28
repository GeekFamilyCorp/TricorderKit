---
description: Show only changed vault files since the last manifest.
allowed-tools: Bash, Read
---

Run `python scripts/vault_delta.py --vault . --manifest .tricorderkit/index/manifest.jsonl --out .tricorderkit/reports/delta_report.md`, then read the report and return only changed files and recommended actions.
