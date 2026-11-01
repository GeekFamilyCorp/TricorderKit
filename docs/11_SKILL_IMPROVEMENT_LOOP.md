# Skill improvement loop — task-observer + session-memory

> Added 01/11/2026. How TricorderKit turns the friction of real work sessions into better skills,
> without the agent ever rewriting its own skills unsupervised.

Two skills share the job. Each owns one kind of information; neither copies the other.

| Skill | What it records | Where | Who reads it |
|---|---|---|---|
| **task-observer** (third-party, CC BY 4.0) | what should **improve a skill**: a user correction, a broken rule, a task that keeps coming back, a new skill worth building | `<workspace>/skill-observations/observation-log/` — one Markdown file per observation, `NNNN-slug.md`, YAML header | the weekly review, which **stages** skill updates for a human to approve |
| **session-memory** (this repo, `skills/session-memory/`) | the **journal of facts and decisions**: what was done, what was decided, what changed, what is left to do | your vault's journal, recovery note and registries | the next session (boot), the human |

## The role-split rule (R130)

1. `task-observer` records what must **improve a skill**.
2. `session-memory` keeps the **journal of facts and decisions** and no longer writes skill-improvement lessons.
3. When one event concerns both, the journal line **cites the observation number** (`observation 0005`) and does not copy it.
4. Changing a skill's own text (including `session-memory`'s) is prepared by the weekly review and installed only on the human's go-ahead.

Why: two skills writing the same lesson in two places drift apart. Each type of information gets one owner; the other only points to it.

## How the loop runs

```
work session ──► task-observer writes observation files (same turn, never batched)
      │                         │
      └► session-memory writes  ▼
         the journal      weekly review (scheduled) ──► staged updates in skill-updates/
         (cites obs. N)                                         │
                                                  human approves ──► install
```

- **Nothing is installed automatically.** The review only stages copies; a human installs.
- **Second violation of the same rule → a barrier, not a rewording.** When a documented rule has been broken twice, the proposed fix is structural (a hook, a script that refuses the wrong path, a default), never a louder sentence.
- **First run:** the log starts empty. A one-off backfill pass can mine your existing error log, lessons file and decision records so the first review has material.

## Getting the skills

### task-observer — from its upstream repository

Source: <https://github.com/rebelytics/one-skill-to-rule-them-all> (author: Eoghan Henn and contributors, licence CC BY 4.0). It is **not** vendored here: install the upstream bundle so you get its fixes.

The bundle is `SKILL.md` + `references/` (7 files) + `scripts/` (5 files). Installing `SKILL.md` alone runs degraded.

**Claude apps (web, desktop, Cowork)**

1. Download the `.skill` bundle from the latest release, or the repository ZIP (Code → Download ZIP).
2. Put `SKILL.md`, `references/` and `scripts/` in one folder named `task-observer`, and zip that folder.
3. In Claude: **Customize → Skills → + → Create skill → Upload a skill**, choose the ZIP, then switch the skill on.

**Claude Code**

- `npx skills add rebelytics/one-skill-to-rule-them-all --skill task-observer` (add `-g` for all projects), or
- copy the folder to `.claude/skills/task-observer/` (project) or your user skills directory, keeping `references/` and `scripts/`.

**Set it up for your machine**

- **Pin the workspace.** Every snippet in the bundle uses the placeholder `[ABSOLUTE PATH]`: the folder that will hold `skill-observations/`. Replace it with one stable absolute path *outside* any skills directory (we use a folder inside our private vault). The skill creates `skill-observations/` there on its first run.
- **Windows:** the helper scripts are bash. Run them with Git Bash (`C:\Program Files\Git\bin\bash.exe`), not the WSL `bash.exe` in System32. Keep a copy of `scripts/` in `skill-observations/.bin/` (same SHA-256) so sessions bridged to the workstation can run them.
- **Activate it.** Description matching alone under-triggers: add the activation block from its `references/environments.md` to your `CLAUDE.md` (or your platform's project instructions), then check in a *new* session that `skill-observations/checkpoints.log` gets a fresh `session-start scan` line.
- **Schedule the review** weekly (we run it on Sunday evening, on the workstation, with a phone notification). The scheduled prompt loads the skill, runs its review, stages updates, and never installs.
- **Cost to expect:** about 11 000 tokens loaded at the start of every working session.

### session-memory — from this repository

Not part of the upstream bundle: it is TricorderKit's own skill, published here in a generic form.

**What it does.** It writes the session's facts *as they happen*, not at the end (a session that is cut off records nothing):

| Trigger | Immediate write |
|---|---|
| a decision is taken | journal entry + recovery note, with the measurement that settled it |
| a tool, scheduled task, path or running service is created or changed | the matching registry, with a dated "verified on" line |
| a task starts or ends (multi-agent setups) | the coordination board |
| a measurement contradicts a note | a **dated addition** to that note, never a rewrite |
| something is left to do | a checkbox in the recovery note |
| end of session | the closing checklist |

Errors and lessons that should change a skill are **not** written by session-memory any more: they go to task-observer, and the journal cites the observation number (R130).

**Install.**

1. Copy `skills/session-memory/` from this repository.
2. Claude apps: zip the `session-memory` folder and upload it (**Customize → Skills → + → Create skill → Upload a skill**). Claude Code: place it in `.claude/skills/session-memory/`.
3. Edit the paths table at the top of its `SKILL.md` to point at your own journal, recovery note and registries (defaults assume an Obsidian-style vault).

## Related

- Governance rules and gates: [docs/09_GOVERNANCE_GUARDRAILS.md](09_GOVERNANCE_GUARDRAILS.md)
- Skill inventory and health: `cowork-plugins/tk-knowledge/` (`skill-manager`, `skill-evals`)
- House rules (one-line definitions, R130 included): `cowork-plugins/tk-knowledge/references/regles.md`
