# [PROJECT_NAME] — linked_project TricorderKit

> Public-safe template. Replace all `[PLACEHOLDER]` values before use.
> Domain: [DOMAIN]
> Engine: TricorderKit

---

## What is this?

This repository is a **linked_project** connected to TricorderKit.

It contains the domain-specific data, sources, and workflows for `[DOMAIN]`.
TricorderKit provides the execution engine. This project provides the specialization.

```
TricorderKit (engine)  ←→  [PROJECT_NAME] (specialization)
```

---

## Setup

### 1. Clone and fill placeholders

```bash
cp -r templates/linked_project_anon /path/to/[PROJECT_ID]
cd /path/to/[PROJECT_ID]
# Replace all [PLACEHOLDER] values in project_config/
```

### 2. Register in TricorderKit

Edit `TricorderKit/configs/local/linked_projects.yaml`:

```yaml
linked_projects:
  - id: [PROJECT_ID]
    name: [PROJECT_NAME]
    root: /path/to/[PROJECT_ID]
    enabled: true
    # ... (see configs/local/linked_projects.example.yaml)
```

### 3. Validate

```bash
python cli/tk.py project status [PROJECT_ID]
python cli/tk.py project audit [PROJECT_ID]
```

---

## Structure

```text
[PROJECT_NAME]/
├── project_config/
│   ├── project.yaml      ← main project config (fill placeholders)
│   └── sources.yaml      ← domain-specific sources
├── vault/                ← Obsidian knowledge base
├── sources/              ← raw datasets and feeds
├── workflows/            ← specialized workflows
├── skills/               ← domain skills
├── reports/              ← TricorderKit-generated reports
├── exports/              ← exported data (anonymized only)
├── project_logs/         ← execution logs
└── project_decisions/    ← architecture decisions (YYYY-MM-DD_title.md)
```

---

## Ground rule

```
TricorderKit executes. This project specializes.
```

This repository never modifies TricorderKit core.
Communication goes through config, CLI, Markdown/JSON/YAML files, and declared workflows.

---

*Template TricorderKit v0.9 — anonymous variant*
