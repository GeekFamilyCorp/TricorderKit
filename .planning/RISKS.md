# RISKS.md — TricorderKit v0.9

> Registre des risques identifiés. Mettre à jour à chaque session.

---

## Format

```markdown
### RISK-XXX — Titre
- **Date** : JJ/MM/AAAA
- **Niveau** : Critique | Haute | Moyenne | Basse
- **Statut** : Ouvert | Mitigé | Clos
- **Description** : ...
- **Mitigation** : ...
```

---

### RISK-001 — Sur-architecture progressive
- **Date** : 10/05/2026
- **Niveau** : Haute
- **Statut** : Mitigé
- **Description** : TricorderKit risque de devenir trop complexe avant d'avoir un noyau stable.
- **Mitigation** : Règle stricte phases séquentielles + liste rouge permanente dans README_FIRST.md. Architecture linked_project (DEC-010) isole la complexité domaine.

---

### RISK-002 — Boucles infinies de tokens (workflows Temporal)
- **Date** : 10/05/2026
- **Niveau** : Haute
- **Statut** : Mitigé (DEC-006)
- **Description** : Un workflow mal configuré peut déclencher des appels LLM en boucle et consommer des budgets tokens significatifs.
- **Mitigation** : `token_budget` obligatoire dans chaque workflow manifest. budget_guard T1/T2/T3 opérationnel depuis v0.9 M1 (25 tests).

---

### RISK-003 — Fragmentation des mémoires
- **Date** : 10/05/2026
- **Niveau** : Moyenne
- **Statut** : Mitigé
- **Description** : Coexistence de mémoire Claude Vault (Obsidian), mémoire auto (MEMORY.md) et mémoire projet (.planning/) peut créer des divergences.
- **Mitigation** : Règle claire : `.planning/` pour décisions/tâches, Claude Vault pour knowledge, MEMORY.md pour préférences. BOOT_SUMMARY.md comme source de vérité boot (≤ 500 tokens). Pipeline observabilité M4 alimente Obsidian automatiquement.

---

### RISK-004 — Dépendance aux APIs manga non officielles
- **Date** : 10/05/2026
- **Niveau** : Moyenne
- **Statut** : Mitigé
- **Description** : Jikan et MangaDex APIs peuvent être instables, rate-limitées ou changer sans préavis.
- **Mitigation** : Cache SQLite obligatoire (cli-forge). Fallback multi-sources dans `trusted_sources.yml`. Tests live B3 (24/24 PASS 22/05/2026) confirment la résilience. Jikan 504 non bloquant grâce au fallback AniList. Self-host Jikan en option future.

---

### RISK-005 — Prompt injection via skills externes
- **Date** : 10/05/2026
- **Niveau** : Haute
- **Statut** : Mitigé
- **Description** : Tout skill externe intégré peut contenir des instructions malveillantes cachées.
- **Mitigation** : security-audit-cli opérationnel (Phase 5) — scan secrets, anonymisation, anti-patterns. 16 tests pytest couvrant secret_scanner, anonymization_checker, pattern_checker, security_runner (22/05/2026). Audit obligatoire avant tout import externe.

---

### RISK-006 — Perte de contexte entre sessions Claude
- **Date** : 10/05/2026
- **Niveau** : Moyenne
- **Statut** : Mitigé
- **Description** : Les sessions Claude Code ne persistent pas le contexte.
- **Mitigation** : `/tk:boot` v0.9 charge BOOT_SUMMARY.md (≤ 500 tokens) + lazy-load docs/. MainBrain v1.5 Memory Selector. Pipeline observabilité M4 → Obsidian auto-mis à jour.

---

### RISK-007 — Infrastructure Docker non déployée bloque les tests
- **Date** : 10/05/2026
- **Niveau** : Basse
- **Statut** : Clos (2026-05-15)
- **Description** : Neo4j, Qdrant, Temporal et Langfuse ne sont pas encore déployés.
- **Mitigation** : Docker Compose opérationnel depuis Phase 3 (vérifié 15/05/2026). Neo4j ✅ Qdrant ✅ Temporal ✅ Langfuse :3001 ✅. Traces live vérifiées M4.

---

### RISK-008 — Désynchronisation STATE.md / réalité repo
- **Date** : 22/05/2026
- **Niveau** : Moyenne
- **Statut** : Mitigé
- **Description** : STATE.md peut rester plusieurs sessions en retard sur la réalité (version, tests, phases). Constaté : STATE.md affichait v0.9 M2 / 247 tests alors que le repo était à M4 / 451 tests.
- **Mitigation** : Règle R18 — mettre à jour STATE.md en fin de chaque session avant commit. BOOT_SUMMARY.md comme double de vérification. Audit croisé TASKS.md / CHANGELOG / STATE.md si divergence suspectée.

---

### RISK-009 — Pattern db_connection_string trop restrictif
- **Date** : 22/05/2026
- **Niveau** : Basse
- **Statut** : Mitigé (2026-05-22)
- **Description** : Le pattern `db_connection_string` dans `secret_scanner.py` exigeait ≥ 10 chars sur le segment username. Des usernames courts comme `admin`, `root`, `dev` n'étaient pas détectés.
- **Mitigation** : Fix appliqué — `{10,}` → `{3,}` sur le segment username. Commit `bb96d11`.

---

*Dernière mise à jour : 22/05/2026 — v0.9 M4 — RISK-009 mitigé (fix db_connection_string)*
