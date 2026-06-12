# document-ingestion (MarkItDown)

Adaptateur **isolé** de conversion documentaire vers Markdown normalisé, pour
alimenter le vault Obsidian Japan-Alliance et le RAG local. Brique issue de
**DEC-047** (Headroom et Supermemory écartés à ce stade).

- **Provider** : [`microsoft/markitdown`](https://github.com/microsoft/markitdown) (MIT, v0.1.6)
- **Boucle** : `inbox -> convert -> frontmatter -> archive_original -> report` (quarantaine si échec)
- **Cœur TricorderKit non modifié** : ce plugin n'est qu'un adaptateur ; il se désactive par variable d'environnement.

## Installation

```bash
python -m pip install "markitdown[pdf,docx,xlsx,pptx]"
```

Installé le 2026-06-12 sur la machine (Python 3.14, markitdown 0.1.6 + onnxruntime,
magika, mammoth, pdfplumber, openpyxl).

## Usage

```bash
python plugins/document-ingestion/scripts/tk_ingest_document.py \
  INPUT.pdf vault/_ingested/INPUT.md \
  --archive-dir data/archive/originals \
  --quarantine-dir data/quarantine/ingestion_failed \
  --report reports/integrations/markitdown_ingestion_report.jsonl
```

Le Markdown produit reçoit un frontmatter (`source_file`, `source_hash`,
`source_extension`, `conversion_tool`, `conversion_date`, `ingestion_status`).

## Garde-fous

- L'original n'est **jamais** supprimé (copié en archive si `--archive-dir`).
- Pas d'écrasement d'un `.md` existant sans `--overwrite`.
- Liste blanche d'extensions ; URLs distantes interdites par défaut.
- **Rollback** : `set TK_MARKITDOWN_ENABLED=false` → le script devient un no-op.

## Limites connues

- PDF scanné sans OCR → conversion vide → mise en quarantaine + code retour 1.
- Tableaux très complexes parfois imparfaitement reconstruits (vérifier au cas par cas).

## Tests

```bash
python -m pytest plugins/document-ingestion/tests -q
```
