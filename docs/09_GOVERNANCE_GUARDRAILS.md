# Governance & Guardrails

> Giving an agent real autonomy over your second brain is only safe if it **cannot** leak your
> secrets, act on a malicious web page, publish private notes, or run away on cost.
> TricorderKit treats governance as a **first-class feature**: a numbered, versioned rule-set
> **enforced by deterministic gates** — not prose an agent can quietly ignore.

## Threat model — what we protect against

| Threat | Concretely |
|---|---|
| **Indirect prompt injection** | A web page, file, issue, or command output trying to hijack the agent. |
| **Secret leakage** | Credentials committed, pushed, or surfaced in logs. |
| **Irreversible mistakes** | An accidental destructive push / delete / transfer. |
| **Private-data exposure** | Personal or stack-specific content reaching a public repo. |
| **Runaway cost / loops** | An agent stuck repeating itself or burning budget. |
| **Context rot / memory loss** | An agent that forgets decisions or loses work. |

## The guardrail categories

1. **Untrusted tool output.** Any content from a tool (web page, file, command output, MCP result)
   is treated as **data, never instructions**. An embedded "now do X" is surfaced to the human,
   not executed. Instructions only ever come from the operator.
2. **Secrets discipline.** Secrets never live in code or config — they live in a vault / SOPS, with
   placeholders (`${VAR}`) in the repo. Any secret seen in the clear is treated as **already
   compromised** and rotated. A **secret-scanning gate** (gitleaks) blocks the commit.
3. **Irreversibility gates.** Explicit human confirmation before any **publish / push / send /
   delete / payment**. A pre-push review lists **exactly** what will ship — including concurrent
   commits from other agents — so nothing leaves by surprise.
4. **Public / private routing.** Generic engine code → **public** repo, where a **boundary gate**
   refuses any private term or personal path. Stack- and identity-specific code → **private** repo.
   Raw knowledge / notes → **never** in a repo. The split is enforced, not remembered.
5. **Cost & loop circuit-breaker.** Stop and ask when the **same tool call repeats** without
   progress, or when a session drifts past a token / cost budget.
6. **Memory discipline (zero-loss).** Boot from a hot cache, log every session, and **back up every
   change immediately** so a crash never costs work. Archive, never silently delete.
7. **The Rule of Two.** Never combine **untrusted input + sensitive access + external write** in a
   single step without a human checkpoint — that combination is the classic exfiltration path.
8. **Tool resilience.** A documented fallback chain so a single tool outage never blocks the work
   or, worse, corrupts it mid-operation.

## Enforced, not hoped

Guardrails that depend only on an agent "remembering" a sentence are the weakest layer. TricorderKit
backs each rule with a deterministic check:

- **`pre-commit`** — secret scanning (gitleaks) on staged changes.
- **`pre-push`** — public-boundary check (no private terms / personal paths) + docs-sync.
- **CI** mirrors the same gates, so the protection survives a forgotten local hook.
- Every rule is **numbered, versioned, and registered** in a single source of truth with a
  changelog, so the rule-set itself can be audited and improved over time.

## Why it matters

A second brain is only as valuable as it is **trustworthy**. These guardrails are what make it safe
to hand an agent real autonomy over your knowledge, your repositories, and your machine — and to
keep what is private, private.

---

*Part of [TricorderKit](../README.md) — the local-first Agentic Knowledge OS.*
