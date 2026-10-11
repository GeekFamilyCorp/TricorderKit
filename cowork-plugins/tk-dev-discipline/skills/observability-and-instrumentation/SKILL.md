---
name: observability-and-instrumentation
description: >-
  Rend le comportement des automatisations VISIBLE et diagnosticable — logs structurés JSON,
  compteurs de fin de run, heartbeats, alertes sur seuil — pour les timers systemd, tâches
  planifiées, pipelines de veille et scripts maison. À utiliser quand on ajoute du logging ou de
  l'alerting, quand on déploie une automatisation et qu'il faut prouver qu'elle tourne, ou quand un
  incident survient sans trace exploitable. Déclencheurs : "ajoute des logs", "comment savoir si ça
  tourne", "instrumente", "métriques", "alerte si", "observabilité", "le cron tourne-t-il". Fournit
  un logger JSON stdlib prêt à copier (scripts/structlog_snippet.py). Ne pas activer pour un simple
  print de debug ponctuel, ni pour trouver la cause d'une panne déjà visible → debugging-and-error-
  recovery.
license: Proprietary
metadata:
  version: "1.1"
  author: GeekFamilyCorp
  langues: fr
---

# Observabilité & instrumentation

Objectif : répondre à « ça a tourné, et qu'a-t-il fait ? » SANS relancer. Règles citées (R34 : tout
artefact opérationnel est inscrit au vault ; R48 : logging de session ; R71 : exit 0 seulement si
l'effet annoncé a eu lieu) — définitions dans `${CLAUDE_PLUGIN_ROOT}/references/regles.md`.

## Les 3 questions de toute automatisation
1. **A-t-elle tourné ?** — dernière exécution, succès/échec, durée.
2. **Qu'a-t-elle produit ?** — compteurs : N traités, N ignorés, N erreurs.
3. **Qu'est-ce qui a cloché ?** — erreurs avec contexte (fichier, entrée, exception), pas juste un code.

## Pratiques
- **Log structuré** : une ligne JSON par événement, horodatage ISO 8601 UTC, append-only, flush
  immédiat. Squelette prêt à copier : `scripts/structlog_snippet.py` (stdlib, ~60 lignes ;
  `python3 structlog_snippet.py --demo` pour voir la sortie).
- **Événements minimaux** : `run_start` (paramètres), `run_end` (compteurs + durée), `error`
  (contexte + exception), `skip` (raison). Nommer les événements en snake_case stable — c'est ce
  qu'on grep.
- **Heartbeat** pour les services longs : un événement `heartbeat` toutes les N minutes, ou un fichier
  touché ; l'absence de heartbeat est l'alerte.
- **Vérifier un timer** : `systemctl list-timers <unit>` + `journalctl -u <unit> --since today`.
  Sous Windows : historique de la tâche planifiée + fichier de log.
- **Seuils d'alerte** (peu, mais fermes) : run sans `run_end`, log non mis à jour depuis > 2 périodes,
  compteur `erreurs` > 0, exit 0 sans effet (R71).
- **Enregistrer l'artefact** (R34) : quoi, où, cadence, chemin du log, réversibilité — dans l'index
  des automatisations du vault.

## Exemple avant / après — un timer de veille

**Avant.** `veille.service` lance `veille.py` ; le script fait `print("ok")` et rend 0. Deux jours
sans nouveau digest : impossible de dire si le timer n'a pas tiré, si le script a tourné sans rien
trouver, ou s'il a planté en silence.

**Après.**
```python
from structlog_snippet import get_logger
log = get_logger("veille", logfile="veille.log")
log.info("run_start", sources=len(SOURCES))
for src in SOURCES:
    try:
        n = collecter(src)
        log.info("source_ok", source=src.name, items=n)
    except Exception as e:
        log.error("source_err", source=src.name, exc=repr(e))
log.info("run_end", items=total, erreurs=nb_err, duree_s=round(t, 1))
sys.exit(0 if total > 0 or nb_err == 0 else 1)   # R71 : 0 = effet réel
```
Lecture : `tail -1 veille.log` donne `{"ts":"…","event":"run_end","items":0,"erreurs":3,…}` → le
timer tire, le script tourne, trois sources échouent : la question 3 a sa réponse sans relancer.
Alerte : `erreurs > 0` ou pas de `run_end` depuis 2 périodes.

## Garde-fous
Pas de secret dans les logs (masquer tokens, mots de passe, en-têtes `Authorization`). Rotation ou
limite de taille. Local d'abord, zéro coût. Un log qui survit au crash (append immédiat, pas de
buffer).

## Anti-patterns
« Ça doit marcher » sans preuve. Logs non datés ou non parsables. Un seul log fourre-tout. Alerter
sur tout (bruit = silence).

## Changelog
- **2026-09-07 — 1.1** : noms de scripts privés retirés ; `scripts/structlog_snippet.py` ajouté
  (logger JSON stdlib, `--demo`) ; exemple avant/après sur un timer ; frontmatter normalisé.
- **2026-07 — 1.0** : version initiale.
