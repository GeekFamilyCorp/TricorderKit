---
name: session-memory
description: "Write what the session produces into your vault AS IT HAPPENS, not at the end: a decision taken, a tool, scheduled task, path or running service created or changed, a measurement that contradicts a note, something left to do, and the closing checklist. Not for lessons that should improve a skill (task-observer owns those, rule R130); not for reloading context at session start (boot skill)."
license: MIT
metadata:
  version: "1.3"
  author: GeekFamilyCorp
  alias: memoire-de-session
  updated: "2026-11-01"
---

# Session memory — never learn the same thing twice

A session that is cut off records nothing. Write each fact when it happens, into the channels the
next session and the human actually read — never into a new parallel file: **a lesson filed next
to the register is a lesson lost.**

## Configure once — your paths

Edit this table for your own vault. The defaults assume an Obsidian-style vault.

| Channel | Default path |
|---|---|
| Journal (one dated entry per notable action) | `00_SYSTEM/JOURNAL/entrees/<YYYY>/<MM>/<YYYY-MM-DD>_<project>_<slug>.md` |
| Recovery note (state, what runs, what is left) | `00_SYSTEM/05_Hot_Cache/HOT_CACHE.md` |
| Tools registry | `80_OUTILS/INDEX.md` |
| Automations registry (scheduled tasks, timers) | `00_SYSTEM/AUTOMATIONS_INDEX.md` |
| Paths and access routes | `00_SYSTEM/ARBORESCENCE_systeme.md` |
| Infrastructure (what actually runs) | `Infrastructure_Hub/INDEX.md` |
| Coordination board (multi-agent setups) | `00_coordination/ACTIVE_WORK.md` + `outbox/` of your hub repository |

## When to write — without being asked

| Trigger | Immediate write |
|---|---|
| A decision is taken (architecture, threshold, port, frequency) | journal entry + recovery note, with the measurement that settled it |
| A tool is created or changed | tools registry + its own page |
| A scheduled task is added, disabled or removed | automations registry, dated line |
| A folder, path or access route appears | paths registry |
| What runs changes (service, container, port) | infrastructure registry, dated line |
| A piece of work starts or ends (multi-agent) | coordination board: declare before acting, report when done |
| A measurement contradicts a note | **dated addition** to that note — never rewrite the old line |
| Something is left to do | checkbox in the recovery note |
| End of session | the checklist below |

**Not here — task-observer (rule R130).** An error, a user correction or a repeated task that
should change a *skill* is written as a task-observer observation. The journal line only cites it:
`see observation 0005`. Never copy the observation into the journal.

## Journal entry format

```markdown
---
date: "YYYY-MM-DD"
heure: "HH:MM"
projet: "<project>"
theme: "<theme>"
type: "<decision | livraison | reparation | installation>"
statut: "<fait | en-attente | en-observation>"
titre: "<one line>"
preuve: "<the measurement, commit or file that proves it>"
---

# <title>

- What was done, measured and verified (with dates).
- Rollback: <how to undo it>.
- Left to do: <if any>.
- Lesson for a skill: see observation NNNN (task-observer), if any.
```

## Ground rules

- **No-drop:** archive, never delete. An empty field beats a guessed one.
- **Nothing exists until it is written down and dated.**
- **A measurement beats a note**, even a recent one: correct by dated addition, so one can read
  what was believed and when it stopped being believed.
- **A page written by reading code describes an intention, not a state:** every tool or
  automation page carries a "state VERIFIED on <date>" line with the measurement behind it.
- A script returns 0 only if its announced effect happened.
- Never write a secret, not even described. Scan before copying anything to another host.

## Before closing a session

1. Are the session's decisions in the journal, each with its proof?
2. Does the recovery note say what runs now and what is left?
3. Are the registries touched today up to date (tools, automations, paths, infrastructure,
   coordination board)?
4. Did a measurement contradict the vault? Is the dated addition made?
5. Were the skill lessons logged as task-observer observations, and cited (not copied)?
6. Does the closing answer state the measured backup status?

What is not written down will be paid for again — in time, next session.

## Changelog

### v1.3 — 2026-11-01
- Public generic version. Role split with task-observer (R130): skill-improvement lessons move to
  task-observer observations; this skill keeps the journal of facts and decisions and cites
  observation numbers.
### v1.0–v1.2 — 2026-09-14 → 2026-10-21
- Private versions (French, `memoire-de-session`).
