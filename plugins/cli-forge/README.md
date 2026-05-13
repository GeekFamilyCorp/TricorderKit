\# cli-forge — TricorderKit plugin



> Statut : prototype — 13/05/2026

> Standard : `docs/cli\_forge\_typer\_standard.md` (DEC-010)

> Schémas : `cli\_manifest.schema.json` + `core/contracts/skill\_output.schema.json` (DEC-005)



\## Rôle



Module central de TricorderKit pour créer, maintenir, tester et référencer

les CLIs déterministes utilisables par agents IA.



Objectifs :



\- Générer des CLIs déterministes et reproductibles

\- Standardiser les sorties JSON (schéma officiel `skill\_output.schema.json`)

\- Réduire la consommation de tokens (CLI > MCP quand suffisant)

\- Fournir une bibliothèque d'outils locaux réutilisables



\## Structure



```text

plugins/cli-forge/

├── README.md                       ← ce fichier

├── SKILL.md                        ← skill d'activation pour agents

├── manifest.yml                    ← métadonnées et standards imposés

├── cli\_manifest.schema.json        ← schéma de validation des manifests CLI

├── registry.yml                    ← inventaire des CLIs TricorderKit

├── scripts/

│   └── validate\_cli\_manifest.py    ← validateur de manifests

├── templates/

│   ├── typer\_cli.py.j2             ← squelette CLI Typer conforme

│   └── typer\_test.py.j2            ← squelette tests CliRunner conforme

└── generated/

&#x20;   ├── github-goat/                ← CLI GitHub argparse legacy

&#x20;   └── source-watch-goat/          ← CLI veille manga/anime argparse legacy

```



\## CLIs actuelles



| Nom | Framework | Statut | Tests |

|---|---|---|---|

| `github-goat` | argparse\_legacy | dry\_run\_validated | — |

| `source-watch-goat` | argparse\_legacy | in\_progress | — |

| `tk-installer` | typer | dry\_run\_validated | 27/27 ✅ |



Voir `registry.yml` pour les détails complets.



\## Standard imposé



Toute nouvelle CLI inscrite au registry doit respecter le contrat documenté

dans \[`docs/cli\_forge\_typer\_standard.md`](../../docs/cli\_forge\_typer\_standard.md) :



\- Framework : \*\*Typer\*\* (≥ 0.12)

\- Tolérance legacy : `argparse` pour CLIs préexistantes uniquement

\- Sorties JSON : conformes à `core/contracts/skill\_output.schema.json`

\- Options globales : `--version`, `--help`, `--output {pretty,json}`

\- Anti-écrasement : `--dry-run` et `--force` quand destructif

\- Tests CliRunner ≥ 5 dans `tests/cli\_contracts/`

\- Codes de sortie standardisés (0/1/2/3/4/5)



\## Procédure d'ajout d'une nouvelle CLI



1\. Lire `docs/cli\_forge\_typer\_standard.md`

2\. Copier le template `templates/typer\_cli.py.j2` vers `tools/<cli\_name>/`

3\. Implémenter la logique métier

4\. Copier `templates/typer\_test.py.j2` vers `tests/cli\_contracts/test\_<cli>.py`

5\. Lancer `pytest tests/cli\_contracts/test\_<cli>.py -v` jusqu'au vert

6\. Créer un manifest et valider via `scripts/validate\_cli\_manifest.py`

7\. Inscrire l'entrée dans `registry.yml` avec `framework: typer`

8\. Vérifier `scripts/validate\_repo.py` et `scripts/health\_check.py`



\## Migration argparse → Typer



Les CLIs legacy argparse sont tolérées en attendant migration. \*\*La

conversion automatique est interdite\*\* (DEC-010). Chaque migration passe

par une PR dédiée avec tests CliRunner.



\## Références



\- `docs/cli\_forge\_typer\_standard.md` — contrat d'implémentation Typer

\- `cli\_manifest.schema.json` — schéma de validation manifest

\- `core/contracts/skill\_output.schema.json` — schéma de validation output (DEC-005)

\- `DECISIONS.md` DEC-005, DEC-010, DEC-011, DEC-012 — décisions architecturales

\- Implémentation de référence : `tools/tk\_installer/tk\_installer.py`

