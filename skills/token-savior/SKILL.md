# SKILL : token-savior
**Version** : 0.1.0 | **Alias** : token-hygiene (Cowork)
**Trigger** : "économise les tokens", "trop long", "budget tokens", "compresse ta réponse", "mode économe", "token-savior"

---

## Rôle

Applique le protocole token-hygiene TricorderKit en session Cowork : détecte les signaux de dépassement budgétaire, active le mode de communication compressé adapté à la tâche, et guide vers le model-router pour les tâches suivantes.

Ce skill est l'**alias Cowork** du protocole `token-hygiene` défini dans `AGENTS.md`. Il est conçu pour être déclenché sans Claude Code.

---

## Séquence d'activation

### 1. Évaluer la situation budgétaire

Détecter le signal déclencheur :
- **Signal explicite** : l'utilisateur demande de compresser / économiser
- **Signal implicite** : réponses > 800 tokens sur des tâches T1/T2, prose là où du JSON/tableau suffirait
- **Signal critique** : conversation > 80% du budget estimé

### 2. Sélectionner le niveau de compression

| Niveau | Quand | Format de sortie |
|--------|-------|-----------------|
| **lite** | Tâches T2, contexte professionnel | Phrases courtes, listes concises, pas de prose redondante |
| **full** | Tâches T1, réponses répétitives | Caveman classique : sujet + verbe + résultat |
| **ultra** | Budget critique (>85%) | Abréviations + flèches + JSON brut uniquement |

### 3. Activer le mode

Annoncer **une seule fois** :
```
[token-savior] Mode {lite|full|ultra} activé. Budget estimé : {X}%.
```

Puis appliquer immédiatement sans autre explication.

### 4. Router les tâches suivantes

Appliquer le routage task-tier :
- **T1** (simple, court) → réponse directe en mode ultra/full
- **T2** (standard) → mode lite, déléguer à haiku-executor si disponible
- **T3** (complexe, critique) → ne pas comprimer, noter l'exception

### 5. Surveiller et désactiver

- Rester en mode compressé jusqu'à signal explicite de désactivation (`token-savior off`, `reprends le mode normal`)
- En fin de session : loger `[token-savior] Session terminée — budget utilisé : {X}%`

---

## Règles non-négociables (R15)

- Les outputs inter-agents restent **JSON ou tabulaire**, jamais prose
- Les réponses utilisateur en mode lite/full évitent tout préambule ("Bien sûr", "Voici", "Je vais")
- Les explications ne dépassent pas 3 phrases en mode full, 1 phrase en mode ultra
- Ne jamais comprimer une réponse de niveau T3 critique (sécurité, architecture, décisions irréversibles)

---

## Format de sortie R15 caveman (full)

```
STATUS: ok
ACTION: {ce qui a été fait}
RESULT: {résultat clé}
NEXT: {prochaine étape si applicable}
```

---

## Exemples

**Déclencheur** : "tes réponses sont trop longues"
```
[token-savior] Mode lite activé. Budget : ~45%.
Compris — réponses compressées à partir de maintenant.
```

**Déclencheur** : "mode économe max"
```
[token-savior] Mode ultra activé.
STATUS: ok | ACTION: compression max | NEXT: attendre instructions
```

---

## Désactivation

Mots-clés : "token-savior off", "reprends le mode normal", "mode normal", "désactive la compression"
Action : confirmer en une ligne, reprendre le mode standard.

---

## Dépendances

- `AGENTS.md` — protocole token-hygiene source
- `plugins/token-optimizer/manifest.yml` — config budget_alert_threshold (défaut 0.80)
- Skill `token-optimizer:caveman` — référence pour les niveaux lite/full/ultra
