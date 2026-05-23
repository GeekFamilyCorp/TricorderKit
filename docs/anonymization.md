# Anonymization Guide — TricorderKit v0.9

> Règle fondamentale : **aucun nom de projet lié, chemin personnel ou clé API ne doit apparaître dans le repo public TricorderKit.**

---

## Principe

TricorderKit est un moteur générique. Son repo GitHub est public. Tout ce qui est spécifique à un domaine, une organisation ou un utilisateur vit dans un linked_project séparé et privé.

Avant tout push vers le repo public, un audit d'anonymisation doit être effectué.

---

## Ce qui doit rester HORS du repo public

| Catégorie | Exemples | Risque |
|---|---|---|
| Clés API et secrets | `ANTHROPIC_API_KEY=sk-ant-...`, tokens GitHub | Compromission compte |
| Chemins personnels | `C:\Users\ton-nom\`, `/home/user/` | Fingerprinting |
| Noms de projets liés | `Japan-Alliance`, `MangaTracker` | Exposition stratégie |
| Données métier | listes de sources privées, schémas BDD propriétaires | Fuite propriété intellectuelle |
| Identifiants Supabase réels | `https://xxxx.supabase.co`, service role keys | Accès BDD |
| URLs de services internes | `http://internal-server/`, IPs locales non standard | Cartographie infra |

---

## Workflow d'anonymisation avant push

### 1. Scan automatique

```bash
# Vérification complète (secrets + anonymisation + patterns)
python cli/tk.py security check-anon

# Ou via make :
make security
```

### 2. Interprétation des résultats

```
[OK]   Aucun pattern à risque détecté
[WARN] Patterns suspects détectés — vérification manuelle requise
[FAIL] Secrets ou données sensibles détectés — ne pas pusher
```

En cas de `[FAIL]`, corriger avant tout commit.

### 3. Patterns détectés par `check-anon`

Le scanner analyse les fichiers versionnés (hors `.gitignore`) pour :

- Clés API connues : `sk-ant-`, `pk-lf-`, `sk-lf-`, `ghp_`, `ghs_`
- Chemins utilisateur Windows : `C:\Users\<nom>\`
- Chemins utilisateur Unix : `/home/<nom>/`, `/Users/<nom>/`
- Noms de projets liés configurés dans `configs/shared/defaults.yaml`
- Variables d'environnement avec valeurs réelles (pas de placeholders)

---

## Règles de whitelist

Certains fichiers peuvent légitimement contenir des patterns sans être des secrets réels :

| Fichier | Raison |
|---|---|
| `.env.example` | Template — contient des placeholders intentionnels |
| `docs/*.md` | Documentation — les patterns sont des exemples |
| `cli/tk.py` | Code source — les patterns sont des chaînes de détection, pas des secrets |
| `tests/` | Tests — les valeurs sont des fixtures, pas des secrets réels |

Ces fichiers sont automatiquement whitelistés par `check-anon`. Ne pas modifier la whitelist sans l'entrée `R17` dans `tasks/lessons.md`.

---

## Règle R17 — Whitelist git grep

Avant tout push public, valider manuellement ces 3 cas :

```bash
# 1. Aucun chemin personnel
git grep -r "Users\\sebas" -- . ':!.env' ':!*.example'

# 2. Aucun nom de projet lié
git grep -ri "japan.alliance\|mangatracker" -- . ':!docs/' ':!*.md'

# 3. Aucune clé API réelle
git grep -r "sk-ant-api" -- . ':!.env.example' ':!*.md'
```

Si l'un de ces grep retourne des résultats : **ne pas pusher**.

---

## Template linked_project anonymisé

Le répertoire `examples/linked-project-template/` fournit un point de départ anonymisé pour créer un nouveau linked_project :

```text
examples/linked-project-template/
├── project.config.example.yaml  ← configuration projet
├── sources.example.yaml         ← sources de données
├── workflows.example.yaml       ← workflows Temporal
├── skills.example.yaml          ← skills spécialisés
├── .env.example                 ← variables d'environnement
├── README.md                    ← guide démarrage rapide
└── README_PRIVACY.md            ← règles de séparation public/privé
```

Copier ce répertoire, renommer les fichiers (supprimer `.example`), et renseigner les valeurs réelles dans votre repo privé.

---

## Checklist pré-push

```
[ ] tk security check-anon → [OK] ou [WARN] validé manuellement
[ ] git grep Users\<nom> → 0 résultats
[ ] git grep <nom-projet-lié> → 0 résultats hors docs/
[ ] .env absent du diff (vérifié dans .gitignore)
[ ] Aucun fichier de config local (configs/local/) dans le diff
```

---

*TricorderKit v0.9 — GeekFamilyCorp — 2026*
