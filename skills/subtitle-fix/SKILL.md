---
name: subtitle-fix
description: Corrige et convertit des fichiers de sous-titres (.srt, .vtt, .ass, .ssa) — resynchronise le timing (décalage global, étirement/compression de framerate), nettoie les artefacts OCR, réencode en UTF-8, fusionne ou découpe des pistes, et convertit entre formats. À utiliser quand l'utilisateur veut "décaler mes sous-titres de N secondes", "convertir srt en vtt", "mes sous-titres sont en avance/retard", "réparer l'encodage des sous-titres", "passer de 23.976 à 25 fps", "fusionner deux pistes de sous-titres". NE PAS utiliser pour TRADUIRE le contenu (déléguer au skill de langue/traduction) ni pour de l'extraction audio/vidéo.
version: "1.0"
author: claude
---

# subtitle-fix — Réparation, resynchronisation & conversion de sous-titres

> Promu depuis un brouillon généré par `doc-to-skill` (validé 2026-06-24). Couvre les pannes courantes
> de sous-titres — timing, encodage, format — sans toucher au **sens** (la traduction est déléguée).

## Quand l'utiliser / quand déléguer
- **Ici** : timing décalé/dérivant, mauvais encodage, mauvais format, artefacts OCR, fusion/découpe de pistes.
- **Déléguer** : traduire le texte → skill de langue/traduction (ex. `polyglotte`) ; extraire/muxer une
  piste depuis une vidéo → outil média dédié.

## Diagnostic du timing (clé)
- **Décalage constant (offset)** : tout est en avance/retard de N secondes → appliquer `+/- N s`.
- **Dérive (drift)** : l'écart grandit avec le temps → conversion de framerate (23.976 ↔ 25 ↔ 29.97) ou
  ré-échelonnage par deux points d'ancrage (timecode début connu + timecode fin connu → facteur + offset).
- **Mixte** : corriger d'abord le facteur (drift), puis l'offset résiduel.

## Workflow
1. **Détecter** format (srt/vtt/ass/ssa) et encodage ; réencoder en **UTF-8** si besoin (signaler si ambigu).
2. **Diagnostiquer** le type de problème de timing (offset vs drift, cf. ci-dessus).
3. **Corriger** : offset et/ou facteur d'étirement ; nettoyer balises parasites et artefacts OCR (l→I, 0→O…).
4. **Convertir** vers le format cible en préservant la mise en forme compatible (styles ass→vtt simplifiés).
5. **Vérifier** : montrer 3-5 timecodes d'échantillon **avant/après** + un résumé du diff.

## Garde-fous
- **Sauvegarde de l'original** avant toute écriture ; jamais d'écrasement sans confirmation.
- Ne **traduit pas** le contenu ; en cas d'encodage source ambigu, proposer les hypothèses plutôt que deviner.
- Préserver l'ordre et la numérotation des cues ; ne pas perdre de lignes lors d'une conversion.
- Outillage local (ffmpeg/sous-titres ou parsing maison) — pas de service en ligne requis.
