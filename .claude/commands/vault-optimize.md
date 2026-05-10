---
description: Generate a vault-specific optimization plan using the manifest and router.
allowed-tools: Bash, Read, Write
---

Optimize the vault using a manifest-first workflow.

1. Ensure `.tricorderkit/index/manifest.jsonl` exists. If missing, run `/vault-analyze`.
2. Run `python scripts/vault_router.py --vault . --manifest .tricorderkit/index/manifest.jsonl --out .tricorderkit/config/router.generated.json`
3. Create `.tricorderkit/reports/optimization_plan.md`.
4. Do not modify vault content yet.
5. Recommend CLI/MCP/Skill/Agent routing by folder and task.
