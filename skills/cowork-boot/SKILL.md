# Skill : cowork-boot — Japan-Alliance / MangaTracker
**Version** : 0.1.0
**Trigger** : début de session Cowork Japan-Alliance, "boot JA", "démarre la session", "reprends le contexte"
**Environnement** : Claude Cowork (pas Claude Code)
**Mis à jour** : 2026-05-22

---

## Rôle

Boot de session Cowork spécifique Japan-Alliance/MangaTracker.
Équivalent de `/tk:boot` mais sans Claude Code ni CLI.
Charge uniquement ce qui est nécessaire depuis le vault `claude-vault`.

> Pattern ARCH-001 actif : les hooks Cowork sont inertes.
> Tout le comportement intelligent doit être dans ce SKILL.md.

---

## Séquence de boot (lazy-load Cowork)

```text
TIER 1 — Lire en premier (~400 tokens)
  1. BOOT_SUMMARY_JA.md   → état session JA : phase active, tâche en cours, patterns

TIER 2 — Si TIER 1 insuffisant (~800 tokens supplémentaires)
  2. STATE_JA.md           → phase active, blockers, décisions récentes
  3. TASKS_JA.md           → items pending/in_progress uniquement

TIER 3 — À la demande uniquement
  - Templates de fiches    → uniquement si mot-clé déclencheur présent (voir ci-dessous)
  - DECISIONS.md           → uniquement si décision architecturale requise
```

**Règle d'or** : Si BOOT_SUMMARY_JA suffit → aller directement à l'action. Ne pas charger TIER 2/3.

---

## Template Routing — Chargement conditionnel

NE PAS charger un template si la requête ne contient pas de mot-clé déclencheur.
Charger uniquement le template demandé, jamais tous à la fois.

| Template | Mots-clés déclencheurs |
|---|---|
| Template_Fiche_Manga_Expert_v1.0.md | manga, tankōbon, sérialisation, chapitre, volume manga |
| Template_Fiche_LightNovel_Expert_v1.0.md | light novel, LN, roman léger, ラノベ, syosetu |
| Template_Fiche_Volume_Manga_Expert_v1.0.md | volume manga, tome manga, fiche volume |
| Template_Fiche_Volume_LN_Expert_v1.0.md | volume LN, tome LN, fiche volume light novel |
| Template_Fiche_Anime_Expert_v1.0.md | anime, adaptation animée, saison anime, cour |
| Template_Fiche_Saison_Cour_Anime_Expert_v1.0.md | saison, cour, simulcast, épisodes, diffusion |
| Template_Fiche_Seiyu_Expert_v1.0.md | seiyū, doubleur, VA, voice actor, 声優 |
| Template_Fiche_Singer_Expert_v1.0.md | chanteur, singer, artiste musical, OP, ED, opening, ending |
| Template_Fiche_Studio_Animation_Expert_v1.0.md | studio, studio d'animation, production |
| Template_Fiche_Staff_Anime_Expert_v1.0.md | staff, réalisateur, character design, série composition |
| Template_Fiche_Source_Expert_v1.0.md | source, œuvre source, adaptation originale |
| Template_Fiche_Magazine_Platform_Expert_v1.0.md | magazine, platform, Weekly Shonen, revue, sérialisation |
| Template_Fiche_Label_LN_Expert_v1.0.md | label LN, label light novel, collection LN |
| Template_Fiche_Label_Musical_Expert_v1.0.md | label musical, label musique, maison de disques |
| Template_Fiche_Lieu_Expert_v1.0.md | lieu, localisation, quartier, ville japonaise |
| Template_Fiche_Quartier_Otaku_Expert_v1.0.md | Akihabara, Nakano, Ikebukuro, quartier otaku, district |
| Template_Fiche_Musee_Exposition_Expert_v1.0.md | musée, exposition, galerie, exhibition |
| Template_Fiche_Prix_Classement_Expert_v1.0.md | prix, award, classement, palmarès, ranking |
| Template_Fiche_Produit_Goodie_Expert_v1.0.md | goodie, produit dérivé, figurine, merchandise, merch |
| Template_Fiche_Personnage_Expert_v1.0.md | personnage, character, protagoniste, antagoniste |
| Template_Fiche_Console_Platform_Expert_v1.0.md | console, plateforme, Switch, PS5, handheld, arcade |

**Règle** : Aucun mot-clé → pas de template. Un seul template à la fois sauf exception explicite.

---

## Extended Thinking — Désactivé par défaut

Ne jamais activer Extended Thinking pour :
- Remplissage de fiches (manga, anime, LN, seiyū, studio, goodie, personnage)
- Recherche web simple ou récupération de données factuelles
- Comparaisons de données, classements, listes
- Génération de fichiers depuis un template existant

Activer uniquement si le message contient `[THINK]` ou pour :
- Décision architecturale Japan-Alliance/MangaTracker
- Stratégie SaaS / structure BDD complexe

---

## Session Rotation

- Rotation toutes les **15–20 messages**
- Avant fermeture : générer capsule compacte (voir format ci-dessous)
- Coller la capsule en premier message du nouveau fil

---

## Format capsule de session (fin de session)

```json
{
  "project": "Japan-Alliance",
  "version": "v0.9",
  "status": "partial|complete",
  "domain": "manga|anime|ln|bdd|saas|workflow",
  "phase_active": "[nom phase]",
  "completed_this_session": [],
  "open_tasks": [],
  "decisions": [],
  "next_action": "[une seule action]",
  "resume_prompt": "[prompt court pour reprendre]"
}
```

---

## Rapport de boot

Afficher après chargement TIER 1 :

```
## Boot JA — [DATE]
Phase : [nom] | Budget : [X]% [SAFE|WATCH|ALERT]
Tâche prioritaire : [une ligne]
Patterns actifs : [codes]
```

---

## Règles non-négociables

- SEARCH BEFORE GENERATE — vérifier via web ou vault avant de répondre
- NO SPECULATION — donnée manquante → status `partial`, jamais d'invention
- OUTPUT JSON — tout output structuré en JSON ou Markdown tabulaire
- Écriture dans Japan-Alliance vault uniquement (jamais dans claude-vault)
- Une tâche = un fichier Obsidian atomique (100–500 tokens)

---

## Dépendances vault

- `claude-vault` → instructions, templates, skills (lecture)
- `japan-alliance` → fiches, données, résultats (écriture)
- `BOOT_SUMMARY_JA.md` → à créer dans `claude-vault` (voir Étape 1 QUEUE.md)

---

*Version 0.1.0 — 2026-05-22 — Boot Cowork Japan-Alliance · Template routing · Session rotation*
