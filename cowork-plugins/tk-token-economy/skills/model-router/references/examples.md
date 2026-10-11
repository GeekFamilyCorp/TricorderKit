# Exemples de routage

12 cas concrets pour calibrer le jugement.

## Cas 1 - Haiku
**Prompt** : "Traduis 'bonjour comment allez-vous' en japonais"
**Signaux** : 50 tokens, traduction simple, pas de code
**Decision** : T1 - alias `fast`

## Cas 2 - Haiku
**Prompt** : "Extrais les dates de cet email [200 mots]"
**Signaux** : 300 tokens, extraction basique
**Decision** : T1 - alias `fast`

## Cas 3 - Sonnet
**Prompt** : "Redige un article de blog de 800 mots sur la productivite avec l'IA"
**Signaux** : 80 tokens input, 1200 tokens output attendu, redaction standard
**Decision** : T2 - alias `default`

## Cas 4 - Sonnet
**Prompt** : "Ecris un composant React de formulaire de login avec validation Zod"
**Signaux** : 120 tokens, code non critique, standard
**Decision** : T2 - alias `default`

## Cas 5 - Sonnet (malgre input court)
**Prompt** : "Resume ces 3 docs [10000 tokens total]"
**Signaux** : 10000 tokens input, resume complexe
**Decision** : T2 - alias `default`

## Cas 6 - Opus
**Prompt** : "Concois l'architecture d'un systeme de paiement PCI-DSS compliant multi-tenant"
**Signaux** : 200 tokens input, architecture + securite + compliance
**Decision** : T3 - alias `deep` (domaine sensible + architecture)

## Cas 7 - Opus
**Prompt** : "Debug ce memory leak : [stacktrace 8000 tokens] + [code 12000 tokens]"
**Signaux** : 20000 tokens input, debug complexe, prod
**Decision** : T3 - alias `deep`

## Cas 8 - Opus
**Prompt** : "Analyse les trade-offs entre Kafka, Pulsar et NATS pour notre usage [3000 tokens de contexte]"
**Signaux** : 3100 tokens input, decision architecturale complexe
**Decision** : T3 - alias `deep` (complexite cognitive elevee)

## Cas 9 - Haiku malgre tache "semble complexe"
**Prompt** : "Idee rapide de nom pour une startup de paiement"
**Signaux** : 30 tokens, creativite courte, brouillon
**Decision** : T1 - alias `fast`

## Cas 10 - Sonnet avec desescalade budget
**Prompt** : "Fais-moi un audit de ce script de 2000 lignes"
**Signaux** : 25000 tokens, audit code -> normalement Opus
**Budget mensuel** : 85% consomme
**Decision** : T2 - alias `default` (desescalade budget, avertir utilisateur)

## Cas 11 - Override utilisateur
**Prompt** : "Utilise Opus : donne-moi 5 synonymes de 'rapide'"
**Signaux** : tache T1 mais override explicite
**Decision** : T3 - alias `deep` (override utilisateur respecte)

## Cas 12 - Haiku pour conversation
**Prompt** : "Merci !"
**Signaux** : 1 mot, conversation
**Decision** : Pas de routage, reponse directe (trop court pour delegation)
