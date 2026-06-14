# 📡 Canal de commandes — Claude ⇄ Antigravity (quasi temps réel)

> Créé le 2026-06-03 par l'audit `audit-collab-claude-antigravity` (DEC-032, statut : Acceptée — faible risque).
> Objectif : permettre à chaque agent d'envoyer une commande à l'autre **sans attendre le battement horaire**,
> via un poll rapide (~1–2 min) de sa boîte de réception. No-op quasi gratuit si la boîte est vide.

## Structure

```text
commands/
├── README.md              (ce contrat)
├── claude_inbox/          commandes POUR Claude   (écrites par Antigravity)
├── antigravity_inbox/     commandes POUR Antigravity (écrites par Claude)
└── archive/               commandes traitées (déplacées ici)
```

## Convention de nommage

```
AAAA-MM-JJThhmm__<sujet-court-kebab>.md
```
Exemple : `2026-06-03T1610__reverifier-so103.md`

## Contrat de fichier (frontmatter YAML obligatoire)

```yaml
---
from: claude | antigravity
to: antigravity | claude
date: <ISO 8601>
priorite: low | med | high
statut: nouveau | en_cours | traite
ref: <id fiche / DEC / sujet, optionnel>
---
```
Corps : la commande en clair (1 action = 1 fichier, principe atomique).

## Cycle de vie

1. **Émission** : l'émetteur écrit un fichier dans l'inbox du destinataire (`statut: nouveau`).
2. **Lecture** : le destinataire poll sa propre inbox (`claude_inbox/` pour Claude,
   `antigravity_inbox/` pour Antigravity).
3. **Prise en charge** : passe `statut: en_cours` (optionnel pour les commandes courtes).
4. **Clôture** : après traitement, déplacer le fichier vers `archive/` avec `statut: traite`
   (ajouter une ligne `# Résultat:` en bas si utile).

## Garde-fous

- **Chacun n'écrit que dans l'inbox de l'AUTRE** + déplace vers `archive/` ce qu'il a traité.
  Personne n'édite les commandes en attente dans sa propre inbox sauf pour les clôturer.
- **Indépendant du verrou `ETAT_PARTAGE.md`** : ce canal ne touche ni les fiches, ni le vault,
  ni les journaux. Pas besoin de poser le verrou pour déposer/lire une commande.
- **Aucune écriture vault via ce canal** : une commande peut *demander* une intégration vault,
  mais l'intégration elle-même reste soumise aux règles métier (2 sources, dry-run, verrou).
- **Ne déclenche pas l'autre agent** : tant qu'aucun watcher/déclencheur externe (DEC-033/034)
  n'est validé, ce canal fonctionne en **poll** — latence = fréquence du poll de chaque côté.
- **Côté Antigravity** : Sébastien/Antigravity câble son propre poll (Claude ne touche jamais
  les crons d'Antigravity — DEC-025).

## Câblage (à finaliser après validation Sébastien)

- **Claude** : ajouter la lecture de `claude_inbox/` au prompt `sync-antigravity-fiches`
  (battement horaire) et/ou un cron léger dédié ~2 min.
- **Antigravity** : poll de `antigravity_inbox/` ~1–2 min dans son propre planificateur.
