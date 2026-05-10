# cli/ — TricorderKit v0.7

Entrypoint principal `tk` et commandes `/tk:*`.

## Structure

```text
cli/
├── tk                    # Entrypoint principal (à créer en Phase 2)
└── commands/
    ├── boot.ts
    ├── status.ts
    ├── plan.ts
    ├── cli-forge.ts
    ├── deep-research.ts
    └── vault-audit.ts
```

## Usage

```bash
tk boot
tk status
tk cli-forge github
tk deep-research "One Piece"
```

*À implémenter en Phase 2 — CLI-first*
