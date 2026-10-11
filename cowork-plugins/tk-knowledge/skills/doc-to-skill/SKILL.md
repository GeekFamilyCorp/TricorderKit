---
name: doc-to-skill
description: >-
  Transforme une source documentaire (README, doc, PDF, DOCX, page web, dépôt) en un brouillon de
  SKILL.md prêt à relire OU en fiche de connaissance, avec checklist de frontmatter et détection de
  doublon vs les skills existants. À utiliser quand l'utilisateur veut "faire un skill à partir de
  ce doc/PDF/repo", "ingérer cette documentation", "extraire un skill de ce README", "convertir
  cette page en compétence", "capitaliser ce contenu". Pipeline : ingestion (pdf/docx via les skills
  pdf et docx) → extraction d'intention → brouillon → détection de doublon → PROPOSITION, jamais
  d'installation automatique. Ne pas utiliser pour un simple résumé, ni pour polir/évaluer un skill
  déjà rédigé → skill-creator, ni pour chercher un skill existant à installer (recherche à part, hors de ce skill).
license: MIT
metadata:
  version: "1.1"
  author: GeekFamilyCorp
  langues: fr
  inspiration: "Skill_Seekers (design seulement)"
---

# doc-to-skill — Source documentaire → skill (ou fiche), proposé et dédupliqué

Capitalise une doc, un PDF ou un dépôt en compétence réutilisable : ingérer, extraire l'intention,
rédiger un brouillon de `SKILL.md` (ou une fiche), vérifier qu'il n'existe pas déjà, **proposer**.
La création et l'installation restent un acte humain (R53 ; R26 : anti-doublon — définitions dans
`${CLAUDE_PLUGIN_ROOT}/references/regles.md`).

## Pipeline
1. **Ingestion** selon la source :
   - PDF → skill `pdf` (extraction texte) ; DOCX → skill `docx` ; XLSX → skill `xlsx`.
   - Page web / dépôt → WebFetch (README brut via `raw.githubusercontent.com` si volumineux) ; gros
     contenu lu par tranches.
   - Contenu déjà dans le vault → lecture directe des notes voisines pour situer l'existant.
2. **Extraction d'intention** : de quoi parle la source ? quel besoin récurrent couvre-t-elle ? quels
   déclencheurs naturels ? entrées/sorties ? garde-fous ? Si la réponse est « c'est du contenu, pas une
   capacité » → fiche, pas skill.
3. **Brouillon** :
   - *Skill* → `SKILL.md` conforme à la checklist ci-dessous ; corps = workflow, format de sortie,
     garde-fous, un exemple.
   - *Fiche de connaissance* → format de fiche du domaine concerné (frontmatter du vault).
4. **Détection de doublon** (R26) : confronter `name` et intention aux skills installés (plugins,
   `skills/`) et aux notes du vault. Équivalent trouvé → proposer une **extension** plutôt qu'un
   doublon ; recouvrement partiel → le signaler.
5. **Proposition** : brouillon + note (source, intention, doublons, recommandation : créer / étendre /
   abandonner, où installer). L'humain valide ; `skill-creator` finalise et évalue si besoin.

## Checklist frontmatter du brouillon produit
À vérifier avant de livrer — un brouillon qui échoue ici n'est pas livrable :
- [ ] `name` : kebab-case, ≤ 64 caractères, identique au nom du dossier.
- [ ] `description` : ≤ 1024 caractères, 3e personne, QUOI + QUAND (déclencheurs entre guillemets)
      + « Ne pas utiliser pour … → skill-existant » ; aucun chevron `<` `>`.
- [ ] Clés autorisées uniquement : `name`, `description`, `license`, `allowed-tools`, `metadata`,
      `compatibility` (+ `disable-model-invocation: true` si usage manuel). `version`, `author`,
      `status`, `langues` → sous `metadata:`.
- [ ] Ne citer que des skills qui existent réellement chez l'utilisateur.
- [ ] Corps < 500 lignes ; tableaux et référentiels → `references/` ; helpers → `scripts/`.
- [ ] Aucun chemin personnel, IP, ni nom de conteneur privé (R37) si destiné à un dépôt public.
- [ ] `## Changelog` daté en fin de fichier.
- [ ] Validation : `python3 …/skill-creator/scripts/quick_validate.py <dossier>` → « Skill is valid! ».

## Exemple entrée → sortie
**Entrée** : README d'un outil en ligne de commande `srtfix` (dépôt MIT) qui décale et convertit des
sous-titres.
**Étape 2** : intention = « réparer le timing/format de sous-titres » ; déclencheurs « décale mes
sous-titres », « convertir srt en vtt » ; entrée = fichier, sortie = fichier ; garde-fou = ne pas
écraser l'original.
**Étape 4** : `subtitle-fix` existe déjà dans ce plugin et couvre 90 % → **recommandation : étendre**
(ajouter la gestion `.ass` si le README l'apporte), pas de nouveau skill.
**Sortie** : note de proposition — source (URL + licence MIT, reprise de code possible), intention,
doublon détecté (`subtitle-fix`), recommandation « étendre », et le diff proposé pour `subtitle-fix`
en attente de GO. Aucun fichier installé.

## Garde-fous
- Proposition d'abord : ne crée ni n'installe jamais un skill seul (R53).
- Anti-duplication stricte (étape 4, R26).
- Source et licence citées ; jamais d'import de code copyleft (AGPL) dans un dépôt public —
  l'inspiration de design reste permise.
- Frontière contenu vs capacité : du contenu de domaine devient une fiche, pas un skill.

## Changelog
- **2026-09-07 — 1.1** : ingestion via les skills `pdf`/`docx`/`xlsx` (plus de `document-ingestion`),
  `graphify` supprimé ; checklist frontmatter du brouillon ; exemple entrée → sortie ; frontmatter
  normalisé.
- **2026-06 — 1.0** : version initiale.
