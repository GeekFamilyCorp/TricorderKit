# tasks/todo.md — TricorderKit
> Fichier initialisé le 2026-05-18 (Workflow Standard v1.0)
> Usage : plan d'exécution de la session ou tâche courante.
> Archiver en fin de session. Ne jamais supprimer l'historique.

---

## Plan de session — 2026-06-24 (T-2026-06-23-REPOINT-STAGING)

### Tâche active
Repointer les producteurs de brouillons du projet lié vers `_STAGING/<domaine>`, déplacer les anciens `_auto_staging` sans perte et livrer un rapport NO-DROP.

### Étapes
- [x] Étape 1 : Valider statut bus, heartbeat working et chemins sources/cibles
- [x] Étape 2 : Inventorier les producteurs et compteurs avant migration
- [x] Étape 3 : Exécuter les dry-runs, patcher les scripts producteurs et vérifier les diffs
- [x] Étape 4 : Déplacer les fichiers vers `_STAGING/<domaine>` avec backup et contrôles avant/après
- [x] Étape 5 : Déposer le rapport R40, poster `deliverable_ready`, repasser idle et archiver la tâche

### Preuve de fin attendue
- [x] Rapport de migration avec compteurs avant/après et table ancien→nouveau
- [x] `_INDEX.md` mis à jour si présent et concerné
- [x] Scripts producteurs repointés vers `_STAGING`
- [x] Aucun fichier perdu selon les compteurs NO-DROP
- [x] Event bus de livraison + tâche archivée

---

## Plan de session — 2026-06-14 (T-2026-06-14-CODEX-FICHES-QA-FUSION)

### Tâche active
Passe QA unifiée sur les fiches du projet lié : vérifier, compléter, corriger, contrôler la conformité template et produire le manifeste des gaps sans écriture directe dans le vault.

### Étapes
- [x] Étape 1 : Identifier le sas, le schéma de référence et les fiches cibles
- [x] Étape 2 : Exécuter un dry-run déterministe avec contrôles ISBN/template
- [x] Étape 3 : Générer le rapport unique et déposer le livrable R40
- [x] Étape 4 : Poster `deliverable_ready`, repasser idle et clôturer la tâche bus

### Preuve de fin attendue
- [x] Rapport présent dans `canal_agents/commands/claude_inbox/`
- [x] Copie du livrable déposée en zone R40
- [x] Dry-run et limites/gaps documentés
- [x] Event bus de livraison + tâche archivée

---

## Plan de session — 2026-06-13 (T-2026-06-13-CODEX-P2-IDS-875)

### Tâche active
Stamper les champs `*_id` du lot P2 `UNIQUE_SAFE` depuis le préfixe unique du nom de fichier.

### Étapes
- [x] Étape 1 : Vérifier le handoff, le CSV de travail et le script existant
- [x] Étape 2 : Exécuter un dry-run borné avec rapport
- [x] Étape 3 : Appliquer avec backup R31 si le dry-run est cohérent
- [x] Étape 4 : Relancer `audit_conformite_v2.py`, noter `PROGRESS.md` et livrer le rapport R40/bus

### Preuve de fin attendue
- [x] Rapport dry-run/apply présent dans `canal_agents/outbox/codex/`
- [x] Backup `_audit_p2_ids_*` créé
- [x] `summary.json` restauré sans régression (`id_manquant=1890`, `prefixe_id_incorrect=0`)
- [x] Event `deliverable_ready`, event `gap`, heartbeat idle et `done --archive`

---

## Plan de session — 2026-06-02 (Lot 5 Pilote SO)

### Tâche active
Vérification et enrichissement du Lot 5 (SO036 à SO057, 22 fiches) via APIs et recherche web.

### Étapes
- [x] Étape 1 : Analyser les 22 fiches pour extraire les titres et champs manquants
- [x] Étape 2 : Lancer la recherche automatisée/semi-automatisée pour chaque fiche sur AniList / Jikan / MangaDex
- [x] Étape 3 : Valider et croiser sur 2 sources autorisées (et noter les URLs de recoupement)
- [x] Étape 4 : Générer les 22 rapports dans `_sync_antigravity\rapports\`
- [x] Étape 5 : Mettre à jour `ETAT_PARTAGE.md` et `antigravity_vers_claude.md`, puis libérer le verrou

### Preuve de fin attendue
- [x] 22 rapports présents dans `_sync_antigravity\rapports\SO036.md` à `SO057.md`
- [x] Verrou de coopération libéré dans `ETAT_PARTAGE.md`
- [x] Indicateurs mis à jour dans `antigravity_vers_claude.md` avec métriques réelles

---

## Plan de session historique — 2026-05-18
- [x] P1 — Créer tasks/todo.md + tasks/lessons.md (ce fichier)
- [x] P2 — Mettre à jour HOT_CACHE Obsidian (15j stale → état v0.8 réel)
- [x] P3 — Vérifier/renommer MainBrain v1.4 → v1.5
- [x] P4 — Intégrer Workflow Standard v1.0 dans docs/06_workflow_standard.md

