---
name: tk-deep-research
description: "Recherche autonome local-first : collecte multi-sources, deduplication, scoring et synthese Markdown. Declencheurs : /tk:deep-research, recherche approfondie, synthese de sources, pipeline de recherche, deep research."
---

# Skill: deep-research-core — TricorderKit v0.7

> Local-first autonomous research: collect, deduplicate, score and synthesize.

---

## Triggers

```text
/tk:deep-research "<query>"
/tk:deep-research --pipeline content "<query>"
/tk:deep-research --pipeline github "<query>"
/tk:deep-research --dry-run "<query>"
```

---

## Agent instructions

### Research algorithm

```text
1. Identify the pipeline based on the query (content / entity / github / vendor)
2. Read sources/trusted_sources.yml → select relevant sources
3. Block any source in blocked_sources.yml
4. Collect in parallel (max 3 simultaneous sources)
5. Deduplicate by title hash + semantic similarity (threshold 0.85)
6. Score each result (0.0 → 1.0) according to scoring_weights
7. Filter: keep score >= 0.70 only
8. Synthesize in structured Markdown
9. Index in Obsidian (target folder per pipeline)
10. Index in Qdrant if available
11. Return final report with cited sources
```

### Important rules

- Never use a source outside `trusted_sources.yml`
- Always cite sources in the final report
- Limit to 500 tokens per item in synthesis (atomic principle)
- If Qdrant down → continue without vector indexing (degraded mode)
- Log in `.planning/DECISIONS.md` if research leads to a decision

### Available pipelines (adapt to your domain)

| Pipeline | Usage |
|---|---|
| content | Domain content watch, entity profiles |
| entity | Authors, publishers, producers |
| github | Repo audits, integration scoring |
| vendor | VPS, services, comparisons |

---

## Output format

```json
{
  "status": "success",
  "skill_name": "tk-deep-research",
  "query": "<query>",
  "pipeline": "<pipeline>",
  "items_found": N,
  "items_after_dedup": N,
  "items_above_threshold": N,
  "report_path": "vault/reports/research_YYYY-MM-DD_<slug>.md",
  "output": {
    "summary": "...",
    "data": [],
    "sources_used": []
  }
}
```

---

## Degraded mode

- Qdrant down → skip vector indexing, continue
- Obsidian inaccessible → save to `vault/reports/` locally
- Source API down → use SQLite cache if available
