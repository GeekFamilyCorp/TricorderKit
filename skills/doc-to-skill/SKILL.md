---
name: doc-to-skill
description: Transforme une source documentaire (README, doc, PDF, page web, repo) en un SKILL.md prêt à relire OU en fiche de connaissance, avec détection de conflit/duplication. À utiliser quand l'utilisateur veut "faire un skill à partir de ce doc/PDF/repo", "ingérer cette documentation", "extraire un skill de ce README", "convertir cette page en compétence", "capitaliser ce contenu". Pipeline : ingestion → extraction d'intention/structure → brouillon (SKILL.md ou fiche) → détection de doublon vs l'existant → PROPOSITION (jamais d'installation auto). Inspiré de Skill_Seekers (inspiration de design, pas d'import de code). NE PAS utiliser pour un simple résumé (déléguer), ni pour polir/évaluer un skill déjà rédigé (déléguer à skill-creator).
version: "1.0"
author: claude
---

# doc-to-skill — Source documentaire → skill (ou fiche), proposé et dédupliqué

> Capitalise une doc/un PDF/un repo en **compétence réutilisable** sans réinventer la roue : on ingère,
> on extrait l'intention, on rédige un brouillon de `SKILL.md` (ou une fiche de connaissance), on
> **vérifie qu'il n'existe pas déjà**, et on **propose** — la création/installation reste un acte humain.
> Réutilise l'outillage en place ; ne le duplique pas.

## Quand l'utiliser / quand déléguer
- **Ici** : « j'ai cette doc/ce repo, fais-en un skill/une fiche ».
- **Déléguer** : polissage/éval d'un skill existant → `skill-creator` ; lookup factuel d'un domaine →
  le skill de recherche d'entités dédié au domaine ; recherche web profonde → `deep-research`/`autoresearch`.

## Pipeline
1. **Ingestion** (selon la source) :
   - PDF / docx / pptx / xlsx → plugin `document-ingestion` (MarkItDown) → Markdown.
   - Page web / repo → `web_fetch` (README brut `raw.githubusercontent.com` si volumineux) ; gros contenu → lire par tranches.
   - Contenu vault → `graphify` (RAG local) pour situer dans l'existant.
2. **Extraction d'intention** : de quoi parle la source ? quel besoin récurrent couvre-t-elle ? quels
   déclencheurs naturels ? quelles entrées/sorties ? quel garde-fou ?
3. **Brouillon** :
   - *Skill* → `SKILL.md` avec frontmatter `name` + `description` **orientée déclenchement** (mots-clés,
     « à utiliser quand… », « ne pas utiliser pour… ») + corps (workflow, format, garde-fous).
   - *Fiche de connaissance* (si c'est du contenu, pas une capacité) → format de fiche du domaine concerné.
4. **Détection de conflit/duplication** : confronter le `name` et l'intention aux skills existants
   (`skills/`, plugins) et au vault. Si un équivalent existe → **proposer une EXTENSION** plutôt qu'un
   doublon, ou signaler le recouvrement.
5. **Proposition** : présenter le brouillon + l'analyse de doublon + la source citée. L'humain valide,
   puis `skill-creator` finalise/évalue si besoin.

## Format de sortie
- Le brouillon `SKILL.md` (ou la fiche) **+** une note : source, intention détectée, doublons potentiels,
  recommandation (créer / étendre l'existant / abandonner), et où l'installer.

## Garde-fous
- **Proposition d'abord** : ne crée/n'installe jamais un skill tout seul (cf. note : on ne peut pas
  enregistrer un skill à chaud — l'utilisateur installe via Réglages > Capacités).
- **Anti-duplication** stricte (étape 4) : ne pas recréer god-mode/code-corrector/etc.
- **Source & licence** : citer la source ; pour un repo, vérifier la licence avant toute reprise de code
  (jamais d'import de code copyleft type AGPL dans le repo public ; l'inspiration de design reste OK).
- **R37** : le `SKILL.md` produit pour le repo public reste générique (aucun chemin/terme privé).
- **Frontière contenu vs capacité** : du contenu de domaine devient une **fiche** (vault), pas un skill.
