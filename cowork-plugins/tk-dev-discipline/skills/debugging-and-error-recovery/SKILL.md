---
name: debugging-and-error-recovery
description: >-
  Débogage discipliné par cause racine pour scripts Python, VPS (systemd/Docker/SFTP), pipelines de
  veille et automatisations maison. À utiliser quand un test échoue, un build casse, un timer ou une
  tâche planifiée ne produit rien, un script renvoie un résultat inattendu, ou face à toute erreur
  non comprise. Déclencheurs : "débogue", "ça marche pas", "pourquoi cette erreur", "trouve la
  cause", "root cause", "ça plantait avant", "le timer ne tourne plus", "sortie vide". Ne pas
  activer pour une coquille triviale corrigée en un coup d'œil, ni pour corriger/durcir une
  application web entière → code-corrector, ni pour ajouter du logging préventif → observability-
  and-instrumentation.
license: MIT
metadata:
  version: "1.1"
  author: GeekFamilyCorp
  langues: fr
---

# Débogage par cause racine

Objectif : trouver et corriger LA cause, pas un symptôme.

Règles citées, en une ligne chacune (détail dans `${CLAUDE_PLUGIN_ROOT}/references/regles.md`) :
- **R22** — au deuxième échec identique, s'arrêter, chercher la cause racine et changer de méthode.
- **R48** — toute erreur rencontrée est consignée en fin de session (symptôme, cause, correctif).
- **R51** — un cache ou une note n'est pas l'état réel : recouper sur la machine avant d'affirmer.

## Méthode (séquentielle)
1. **Reproduire** de façon fiable et minimale (commande et contexte exacts). Non reproductible →
   instrumenter d'abord (→ `observability-and-instrumentation`).
2. **Observer les faits avant toute hypothèse** : message complet, stacktrace, logs
   (`journalctl -u <unit>`, fichiers `*.log`), code de sortie, état réel (processus, fichiers,
   `systemctl list-timers`, `docker ps`).
3. **Une hypothèse falsifiable à la fois** : « si X, alors je verrais Y » → tester Y.
4. **Bissection** : réduire la surface (dry-run, `git bisect`, isoler le sous-script) jusqu'au point
   de bascule.
5. **Corriger la cause**, pas le symptôme ; vérifier qu'aucune autre branche n'en dépendait.
6. **Prouver** : rejouer le cas + un cas voisin (régression).
7. **Capitaliser (R48)** : une entrée dans le log d'erreurs du projet (par exemple `40_ERRORS/`) —
   symptôme, cause, correctif, pattern si récurrent.

## Exemple — timer systemd muet
Symptôme : « la veille n'a rien produit depuis deux jours ».
1. `systemctl list-timers --all | grep veille` → le timer existe, `LAST` date d'il y a deux jours,
   `NEXT` à `n/a` : il ne se réarme pas.
2. `systemctl status veille.service` → `inactive (dead)`, dernier résultat `exit-code`.
3. `journalctl -u veille.service --since "3 days ago"` → `ModuleNotFoundError: paramiko` à la première
   ligne de l'exécution ratée ; la veille précédente passait.
4. Hypothèse : le virtualenv a été recréé sans la dépendance → `ls <venv>/lib/*/site-packages | grep
   paramiko` → absent. Confirmé.
5. Cause : réinstallation du venv la veille sans `requirements.txt` à jour. Correctif : ajouter la
   dépendance au fichier, réinstaller, `systemctl start veille.service` → exit 0 ; `list-timers`
   affiche à nouveau un `NEXT`.
6. Entrée au log d'erreurs : « timer muet ≠ timer cassé : lire `status` puis `journalctl` avant de
   toucher à l'unité ».

## Pièges connus
- Cache ≠ source (R51). Quoting PowerShell → bash (le `$` disparaît) : passer par un fichier de commande.
- Encodage : un chemin ou une sortie en caractères non latins plante en cp1252 → forcer UTF-8 (`errors=replace`).
- Saturation du poste (outil lent, timeout) n'est pas un bug applicatif : basculer d'outil d'abord.
- Variable `PYTHONHOME` héritée : casse socket/paramiko de façon silencieuse.
- Un exit 0 sans effet est un bug (R71) : vérifier l'effet, pas le code.

## Anti-patterns
Changer plusieurs choses à la fois. Deviner sans observer. Réessayer la même approche trois fois (R22).
Corriger le symptôme et fermer.

## Changelog
- **2026-09-07 — 1.1** : R22/R48/R51 définies en une ligne ; chemins vault remplacés par
  « log d'erreurs du projet » ; noms de scripts privés retirés ; exemple timer
  systemd ajouté ; frontmatter normalisé.
- **2026-07 — 1.0** : version initiale.
