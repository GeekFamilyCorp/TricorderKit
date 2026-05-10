---
description: Analyze the current vault structure and generate a concise structural report.
allowed-tools: Bash, Read, Glob, Grep
---

Analyze this vault without reading all files manually.

Steps:
1. Run `python scripts/vault_analyzer.py --vault . --out .tricorderkit/reports/initial_analysis.md`
2. Run `python scripts/vault_manifest.py --vault . --out .tricorderkit/index/manifest.jsonl`
3. Read only `.tricorderkit/reports/initial_analysis.md`.
4. Summarize detected vault type, folders, templates, risks and optimization path.

Never run `cat **/*.md`.
