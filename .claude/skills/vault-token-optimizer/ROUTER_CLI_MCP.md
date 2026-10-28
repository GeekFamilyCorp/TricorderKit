# ROUTER_CLI_MCP.md

CLI performs batch work. MCP performs structured orchestration. Direct reads are last-mile inspection.

| Task | Route |
|---|---|
| First vault analysis | CLI |
| Manifest creation | CLI |
| Detect duplicates | CLI |
| Find files by category | Manifest + Grep |
| Edit a specific file | Direct Read + Edit |
| Sync validated record | MCP |
| Query back-office | MCP |
| Scrape external source | CLI |
| Generate report | CLI summary + Claude |
| Audit all links | CLI |
| Mass edit | dry-run CLI then apply |

MCP must not crawl the whole vault, scrape websites, replace manifest generation, or mass-write without dry-run.
