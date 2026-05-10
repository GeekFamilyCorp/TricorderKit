# RISKS.md — TricorderKit v0.7

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
- **Statut** : Ouvert
- **Description** : TricorderKit risque de devenir trop complexe avant d'avoir un noyau stable. L'ajout de trop de plugins simultanément peut rendre le système ingérable.
- **Mitigation** : Règle stricte : Phase 1 complète avant Phase 2. Jamais plus de 2 plugins en construction simultanément.

---

### RISK-002 — Boucles infinies de tokens (workflows Temporal)
- **Date** : 10/05/2026
- **Niveau** : Haute
- **Statut** : Mitigé (DEC-006)
- **Description** : Un workflow mal configuré peut déclencher des appels LLM en boucle et consommer des budgets tokens significatifs.
- **Mitigation** : `token_budget` obligatoire dans chaque workflow manifest. Comportement `pause_and_notify` si dépassement.

---

### RISK-003 — Fragmentation des mémoires
- **Date** : 10/05/2026
- **Niveau** : Moyenne
- **Statut** : Ouvert
- **Description** : La coexistence de mémoire Claude Vault (Obsidian), mémoire auto (MEMORY.md), et mémoire projet (.planning/) peut créer des divergences ou des doublons.
- **Mitigation** : Règle claire : `.planning/` pour les décisions et tâches, Claude Vault pour le knowledge, MEMORY.md pour les préférences utilisateur. `/tk:vault-audit` pour détecter les divergences.

---

### RISK-004 — Dépendance aux APIs manga non officielles
- **Date** : 10/05/2026
- **Niveau** : Moyenne
- **Statut** : Ouvert
- **Description** : Jikan et MangaDex APIs peuvent être instables, rate-limitées ou changer sans préavis.
- **Mitigation** : Cache SQLite obligatoire dans cli-forge. Fallback vers sources alternatives dans `trusted_sources.yml`. Monitoring disponibilité dans usage-observer.

---

### RISK-005 — Prompt injection via skills externes
- **Date** : 10/05/2026
- **Niveau** : Haute
- **Statut** : Ouvert
- **Description** : Tout skill externe intégré peut contenir des instructions malveillantes cachées (prompt injection).
- **Mitigation** : Audit sécurité obligatoire avant tout skill externe (DEC-005). security-audit-cli à implémenter en Phase 5.

---

### RISK-006 — Perte de contexte entre sessions Claude
- **Date** : 10/05/2026
- **Niveau** : Moyenne
- **Statut** : Mitigé
- **Description** : Les sessions Claude Code ne persistent pas le contexte. Un agent peut reprendre un travail sans connaître les décisions passées.
- **Mitigation** : `/tk:boot` charge `.planning/STATE.md` + `DECISIONS.md` au démarrage. MainBrain v1.4 Memory Selector.

---

### RISK-007 — Infrastructure Docker non déployée bloque les tests
- **Date** : 10/05/2026
- **Niveau** : Basse
- **Statut** : Ouvert
- **Description** : Neo4j, Qdrant, Temporal et Langfuse ne sont pas encore déployés. Les tests qui en dépendent ne peuvent pas s'exécuter.
- **Mitigation** : Développer en mode dégradé (mock / fichiers Markdown locaux) pendant les Phases 1–2. Docker Compose à configurer en Phase 3.

---

*Dernière mise à jour : 10/05/2026*
