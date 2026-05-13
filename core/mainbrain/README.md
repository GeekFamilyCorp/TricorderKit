# MainBrain — TricorderKit Core

> Version : 1.4 | Stack : TypeScript strict

---

## Rôle

MainBrain est le routeur central de TricorderKit. Il reçoit toute intention (commande `/tk:*` ou requête agent), applique l'algorithme de décision en 10 étapes, et retourne une action structurée.

---

## Algorithme de décision (10 étapes)

```
1. intent_router     → classifier l'intention
2. skill_resolver    → existe-t-il un skill documenté ?
3. cli_resolver      → existe-t-il une CLI déterministe ?
4. workflow_resolver → existe-t-il un workflow Temporal ?
5. memory_resolver   → existe-t-il une mémoire projet / vault ?
6. risk_guard        → évaluer le niveau de risque
7. token_guard       → évaluer le budget tokens
8. executor          → exécuter l'action minimale
9. reporter          → produire un rapport Markdown court
10. memory_writer    → mémoriser les décisions utiles
```

---

## Structure

```
core/mainbrain/
├── README.md              → ce fichier
├── types.ts               → types partagés
├── router.ts              → point d'entrée — algorithme 10 étapes
├── guards/
│   ├── risk_guard.ts      → évaluation risque (LOW/MEDIUM/HIGH/CRITICAL)
│   └── token_guard.ts     → évaluation budget tokens
└── memory/
    └── context_manager.ts → lecture/écriture contexte session
```

---

## Usage

```typescript
import { MainBrain } from './router';

const brain = new MainBrain({ dryRun: false });
const result = await brain.process({
  command: '/tk:boot',
  args: {},
  context: {}
});
console.log(result);
```

---

*Version 1.4 — 13/05/2026*
