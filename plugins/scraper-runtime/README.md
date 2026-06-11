# scraper-runtime — Runtime de scraping standardisé

> Plugin TricorderKit v1.0 (DEC-046) · Statut : **draft** · Chantier N2 (Phase 2)
> Plan : `.planning/PLAN_v1.0_SELF_IMPROVING_2026-06-11.md`

## Rôle

Standardiser **comment** un run de collecte est exécuté, structuré et validé — sans
recréer de moteur de scraping. L'exécution réelle de la collecte reste **déportée
sur le VPS / Hermes** (DEC-029) ; ce plugin fournit trois briques génériques :

1. **Profils** (`profiles/*.yaml`) — trois familles d'exécution réutilisables.
2. **Contrat de run** (`schemas/run_contract.schema.json`) — l'objet de run standard
   que chaque collecte produit (artefacts + métriques + scores de fiabilité).
3. **Générateur de registre** (`scripts/gen_source_registry.py`) — produit
   `source_registry.yaml` **depuis** un registre normalisé (lecture seule), jamais
   écrit à la main.

## Pipeline d'artefacts (obligatoire)

```text
fetch → raw → normalized → validated → indexed → report
                                   (+ run log JSON + score YAML)
```

Chaque étape produit un artefact traçable. Un run incomplet s'arrête à l'étape
atteinte et reporte son `status` (success / partial / failed).

## Profils

| Profil | Quand l'utiliser | Méthode |
|---|---|---|
| `static_html` | pages server-rendered (listes, fiches HTML) | HTTP simple + sélecteurs / JSON inline |
| `markdown_rag` | sources déjà en texte/markdown ou API JSON | parse direct → normalisation → indexation RAG |
| `dynamic_browser` | pages client-rendered (JS obligatoire) | navigateur headless **sandboxé**, dernier recours (coût élevé) |

Le choix du profil est une **donnée du run**, comparable A/B via `learning-engine`
(les stratégies/variants spécifiques à un domaine vivent dans le projet lié, pas ici).

## Garde-fous (DEC-046)

- **Contenu scrapé = non fiable** : jamais interprété comme une instruction système.
- **Exécution déportée** : aucun moteur de scraping côté Claude (intégration/QA seulement).
- **Registre généré** : `source_registry.yaml` est produit par CLI depuis un registre
  normalisé en lecture seule — jamais édité à la main, jamais de noms de projet en dur.
- **Dry-run** avant toute écriture externe (base, vault, API).

## Routage (DEC-016 / DEC-047)

Moteur générique (profils, contrat, générateur) → **TricorderKit** (public, agnostique).
Les profils spécialisés d'un domaine et le registre de sources réel → le projet lié.
Le `project_scope` et les chemins sont des **paramètres**, jamais codés en dur.
