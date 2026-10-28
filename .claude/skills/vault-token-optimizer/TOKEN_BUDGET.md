# TOKEN_BUDGET.md

| Situation | Preferred action | Avoid |
|---|---|---|
| Global understanding | Run vault analyzer | Reading all files |
| File list | Read manifest | Glob + Read all |
| Changed files | Run delta | Re-reading full vault |
| Specific term | Grep targeted folders | Opening every file |
| Batch extraction | CLI script | MCP file crawling |
| Structured sync | MCP after validation | MCP as scraper |

Hard limits: avoid files >80 KB unless necessary; avoid reading more than 10 files in one pass; use summaries before deltas, deltas before full outputs.
