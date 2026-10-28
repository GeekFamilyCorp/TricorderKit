# Gabarit d'un jeu d'evals — `evals/<skill>/`

Deux fichiers par skill, tous deux au format **natif de skill-creator** (aucun champ inventé) :

| Fichier | Lu par | Format |
|---|---|---|
| `evals.json` | l'agent qui exécute les cas (skill-creator §« Running and evaluating ») et le grader (`agents/grader.md`) | `references/schemas.md` de skill-creator |
| `triggers.json` | `scripts/run_eval.py` / `scripts/run_loop.py` de skill-creator | tableau `[{query, should_trigger}]` |

Le no-trigger n'a pas de place dans `evals.json` (qui décrit des tâches à exécuter) : il vit dans
`triggers.json`, où il est mesuré par `run_eval.py`. On le **double** dans `evals.json` sous forme
d'un cas dont l'attente est « renvoie vers le skill X sans dérouler celui-ci », pour qu'un grader
puisse aussi le juger quand `claude -p` n'est pas disponible.

## 1. `evals.json` — format exact

```json
{
  "skill_name": "nom-du-skill",
  "evals": [
    {
      "id": 1,
      "prompt": "Phrase réaliste de l'utilisateur, en français, avec du contexte concret.",
      "expected_output": "[TRIGGER] Description humaine du résultat attendu.",
      "files": [],
      "expectations": [
        "[DET must_contain] texte attendu tel quel",
        "[DET must_not_contain] texte interdit",
        "[DET must_match] regex",
        "[DET must_not_match] regex",
        "[DET tool_used] NomDOutil",
        "[DET tool_not_used] NomDOutil",
        "[DET file_exists] chemin/relatif",
        "[LLM] énoncé vérifiable par un juge, avec la preuve à citer"
      ]
    }
  ]
}
```

Champs : `skill_name` = `name` du frontmatter ; `id` entier unique ; `prompt` ; `expected_output`
(texte libre — on y met le **type** du cas entre crochets) ; `files` (chemins relatifs à la racine
du skill, `[]` si aucun) ; `expectations` = liste de chaînes. Rien d'autre.

### Types de cas (préfixe de `expected_output`)

| Préfixe | Ce qu'on teste | Minimum par skill |
|---|---|---|
| `[TRIGGER]` | le skill se déclenche sur une phrase réaliste — dont au moins un **quasi-faux-positif** (phrase voisine d'un autre skill mais qui doit rester ici) | 2 |
| `[NO-TRIGGER → skill]` | requête voisine qui doit aller **ailleurs** ; on nomme le skill compétent | 1 |
| `[QUALITÉ]` | entrée → sortie conforme au gabarit du skill (sections, tableau, alias de modèle, « sur GO », vouvoiement, aucun chemin en dur) | 2 |
| `[RÉGRESSION]` | un défaut déjà corrigé dans le changelog ne doit pas revenir (renvoi fantôme, outil disparu, nom de modèle versionné, suppression au lieu d'archivage) | 0-1 |
| `[TOKEN-HYGIENE]` | le skill ne lit pas plus que nécessaire (une reference chargée, pas de batch, résumé ≤ N lignes, `deep` jamais pour une passe planifiée) | 0-1 |

### Préfixes d'expectations

- `[DET …]` — vérifiable par script, sans jugement : à écrire **en premier**. Un juge LLM n'intervient
  que sur ce qu'un `grep` ne peut pas trancher.
- `[LLM]` — jugement de qualité ; formuler l'énoncé de façon que le juge doive **citer une preuve**
  (schéma `grading.json` : `text`, `passed`, `evidence`).

Une expectation qui passerait aussi sur une sortie fausse est inutile (cf. `agents/grader.md`,
« Critique the Evals ») : préférer « le tableau contient une ligne A01 avec gravité » à « parle de
sécurité ».

## 2. `triggers.json` — format exact de `run_eval.py`

```json
[
  {"query": "phrase réaliste", "should_trigger": true,  "kind": "trigger"},
  {"query": "quasi-faux-positif",  "should_trigger": true,  "kind": "trigger-near-miss"},
  {"query": "requête voisine",  "should_trigger": false, "kind": "no-trigger", "expected_skill": "plugin:skill"}
]
```

`run_eval.py` ne lit que `query` et `should_trigger` ; `kind` et `expected_skill` sont des champs
documentaires, ignorés par le script. Viser 8-10 entrées par skill si l'on veut lancer
`run_loop.py` (split 60/40 train/test ; en dessous de 5, le split est dégénéré).

Les requêtes doivent être **substantielles** : une question d'une ligne que Claude traite seul ne
déclenche aucun skill, quelle que soit la description (skill-creator, « How skill triggering works »).

## 3. Règles de rédaction des prompts

- Français, ton de l'utilisateur (direct, tutoiement dans la demande ; la **réponse** attendue vouvoie).
- Contexte concret : chemin de projet, nom de conteneur, nom de fiche, nombre de fichiers.
- Aucun secret, aucun chemin personnel (`C:\Users\<nom>`), aucune IP, aucun nom de modèle versionné
  dans les prompts ni dans les expectations — `check_static.py` s'applique aussi aux evals.
- Le no-trigger doit être un **quasi-doublon** (mêmes mots-clés, autre intention), pas une question
  hors sujet.

## 4. Exemple complet (extrait de `evals/doubt-driven-development/`)

```json
{
  "id": 4,
  "prompt": "Tu m'affirmes que tricorder-temporal tourne. Tu l'as vérifié aujourd'hui ou tu le dis de mémoire ? Applique le doute.",
  "expected_output": "[QUALITÉ] Refuse d'affirmer de mémoire, recoupe sur la source réelle (commande exécutée), cite la sortie, puis seulement conclut.",
  "files": [],
  "expectations": [
    "[DET tool_used] Bash",
    "[DET must_contain] R51",
    "[DET must_not_contain] ça tourne",
    "[LLM] La conclusion sur l'état du conteneur est précédée d'une sortie de commande collée (docker ps ou équivalent) — citer la ligne."
  ]
}
```
