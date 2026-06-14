# G1 — Patch de durcissement du Registre Central (prêt à appliquer)

> Statut : **proposé, non appliqué** · Risk Guard : **MEDIUM** (écriture vault live + règle agent)
> Pré-requis : validation explicite avant application ; toute écriture vault d'abord en `--dry-run`.
> Cible règle : `TricorderKit/AGENTS.md` · Cible en-tête : `projet lie/<rubrique>/index.md`

## Problème (vérifié 2026-06-01)
La règle « vérifier avant création » des `index.md` pointe vers un tableau **partiel**
(curé à la main, ~17 lignes côté manga), alors que l'exhaustif vit dans
`99_MASTER_INDEX.md` (1 232 entrées, nocturne). → risque de **faux négatif** (œuvre
absente du partiel mais présente dans le Master Index) → **doublon**. De plus l'ID
est attribué « dernier + 1 » manuel, fragile car les ID sont épars (MA001…MA996).

## Patch 1 — Règle dans `AGENTS.md` (additive)

Ajouter sous les règles métier (bloc à coller tel quel) :

```markdown
### Dédup & attribution d'ID (registre central)
1. Source de vérité dédup = `99_MASTER_INDEX.md` (exhaustif), JAMAIS l'`index.md` de rubrique seul.
2. Avant toute création : recherche stricte titre Romaji ET titre JP dans le Master Index.
   Si match → renvoyer l'ID existant, refuser le doublon, basculer en « mise à jour ».
3. Attribution d'ID via `goat next-id <PREFIXE>` (lit le max réel) — jamais « dernier + 1 » manuel.
4. Écriture synchrone : créer la fiche `<ID>.md` puis réinscrire la ligne dans l'index ET signaler
   au job de nuit (le Master Index se régénère, mais l'index de rubrique doit rester cohérent).
```

## Patch 2 — En-tête des `index.md` de rubrique (remplacement ciblé)

Remplacer la phrase de règle existante :

```text
> **Règles** : Ne jamais créer de doublon. Vérifier ici avant toute création. ID = work_id dans le frontmatter.
```

par :

```text
> **Règles** : Ne jamais créer de doublon. Vérification dédup = `99_MASTER_INDEX.md` (exhaustif),
> ce tableau n'est qu'un extrait « fiches clés ». ID via `goat next-id <PREFIXE>`. ID = work_id dans le frontmatter.
```

## Patch 3 — Job de nuit (passe fuzzy, optionnel mais recommandé)
Ajouter au générateur du Master Index une détection de quasi-doublons (romaji/JP normalisés,
distance de Levenshtein ou clé de translittération) → liste « collisions probables » dans le
rapport de nuit. Ferme l'écart des variantes de translittération (R29-R31).

## Procédure d'application (token-light, sécurisée)
1. Valider ce patch.
2. `AGENTS.md` : édition additive (repo TricorderKit) → commit `docs: G1 règle dédup Master Index`.
3. En-têtes `index.md` : via MCP `obsidian-vault-lie`, **un dry-run** (lister les fichiers
   `*/index.md` et la chaîne à remplacer) avant tout `patch_note`.
4. Patch 3 : modifier le générateur du Master Index (repo depot-exec-lie — routage DEC-016).
5. Si adopté → loguer **DEC-021** `Adoptée` dans `.planning/DECISIONS.md`.

*Patch préparé 2026-06-01 — application différée à validation.*
