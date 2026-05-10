---
name: vault-token-optimizer
description: Optimize any Markdown or Obsidian vault for Claude Code by analyzing structure first, generating manifests, routing work to CLI/MCP/cache/delta, and minimizing token use. Use when working on vault audits, vault migrations, Obsidian cleanup, TricorderKit, MangaTracker, or large Markdown repositories.
allowed-tools: Read, Grep, Glob, Bash, Write
---

# Vault Token Optimizer

## Core rule
Do not read the whole vault. Generate or read the manifest first.

## Protocol
1. Check `.tricorderkit/index/manifest.jsonl`.
2. If missing, run the analyzer and manifest scripts.
3. Read `initial_analysis.md`.
4. Generate or read `router.generated.json`.
5. Decide route: direct read, Grep, CLI, cache/delta, or MCP.
6. Create a dry-run before modifying.
7. Audit after modification.

## Supporting files
- TOKEN_BUDGET.md
- ROUTER_CLI_MCP.md
- VAULT_ADAPTATION_PROTOCOL.md
