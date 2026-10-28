# deep-research-core — TricorderKit v0.7 Plugin

> Local-first autonomous research engine for TricorderKit.

---

## Why deep-research-core?

TricorderKit agents need structured, sourced, indexed research — not improvised answers.

This plugin transforms a query into a sourced Markdown report, indexed in Obsidian and the RAG vault (Qdrant).

---

## Cognitive pipeline

```text
User query
      ↓
Source Selector (trusted_sources.yml)
      ↓
Parallel multi-source collection
      ↓
Deduplication (hash + semantic similarity)
      ↓
Reliability score (0.0 → 1.0)
      ↓
Structured Markdown synthesis
      ↓
Obsidian + Qdrant indexing (RAG)
      ↓
Final sourced report
```

---

## Use cases

- Domain content watch (new releases, rankings, news)
- Entity enrichment (authors, publishers, producers)
- GitHub repo audits (scoring, TricorderKit integration)
- Infrastructure / vendor research
- Any structured, multi-source deep research task

---

## TricorderKit commands

```bash
/tk:deep-research "<query>"           # Full research
/tk:deep-research --pipeline content  # Use content pipeline
/tk:deep-research --dry-run "<q>"     # Simulate without real search
```

---

## Plugin structure

```text
plugins/deep-research-core/
├── README.md
├── manifest.yml
├── .claude-plugin/plugin.json
├── skills/tk-deep-research/SKILL.md
├── sources/
│   ├── trusted_sources.yml    ← allowed trusted sources
│   └── blocked_sources.yml    ← blocked sources
├── pipelines/
│   ├── content_sources_research.yml   ← content pipeline (adapt to your domain)
│   ├── entity_research.yml            ← entity pipeline (planned)
│   ├── github_research.yml            ← GitHub pipeline (planned)
│   └── vendor_research.yml            ← vendor pipeline (planned)
└── scripts/
    ├── collect_sources.py
    ├── score_reliability.py
    ├── deduplicate_findings.py
    └── export_report.py
```

---

*Version 0.1.0 — TricorderKit generic stub*
