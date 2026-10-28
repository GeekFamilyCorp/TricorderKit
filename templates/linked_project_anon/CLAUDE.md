# CLAUDE.md — [PROJECT_NAME]

> Claude Code config for this linked_project.
> Update: end of each session.

---

## Project identity

- **Name**: [PROJECT_NAME]
- **Engine**: TricorderKit v0.9
- **Domain**: [DOMAIN]
- **Architecture**: TricorderKit executes · [PROJECT_NAME] specializes

---

## Boot sequence (lazy-load)

```text
TIER 1 — Always load (~400 tokens)
  1. BOOT_SUMMARY.md          → version, tasks, patterns, status

TIER 2 — Only if TIER 1 insufficient (~2 000 tokens)
  2. .planning/STATE.md        → detailed state
  3. .planning/TASKS.md        → pending/in_progress only
  4. .planning/DECISIONS.md    → last 5 entries only

TIER 3 — On demand only
  - docs/
  - .planning/RISKS.md
```

---

## Extended Thinking Policy

Disabled by default. Enable only if message contains `[THINK]` or task involves:
- Multi-file architectural reasoning
- Complex regression debugging
- Irreversible decisions (DEC-NNN)

---

## Session Rotation Policy

- Open a new thread every 15–20 messages
- Before closing: generate compact `session_capsule.json`
- Paste capsule as first message of new thread
- Update `BOOT_SUMMARY.md` at session end

---

## Commit conventions

```text
feat: <description>
fix: <description>
docs: <description>
refactor: <description>
test: <description>
chore: <description>
```

---

## Ground rule

```
TricorderKit executes. This project specializes.
This repo never modifies TricorderKit core.
```

---

*[PROJECT_NAME] linked_project — TricorderKit v0.9 template*
