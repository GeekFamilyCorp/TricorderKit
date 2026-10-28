# Format des alertes

## Niveaux d'alerte

| Seuil | Nom | Action automatique | Message utilisateur |
|-------|-----|---------------------|---------------------|
| 50% | INFO | Aucune | "Info : budget mensuel a 50%. Ritme normal." |
| 80% | WARNING | Router desescalade d'un tier par defaut | "Attention : budget a 80%. Je desescalade automatiquement les taches non critiques." |
| 95% | CRITICAL | Router force Haiku sauf urgence explicite | "Budget a 95% ! Je force Haiku pour le reste du mois. Dites 'urgence' ou 'critique' pour forcer Sonnet/Opus." |
| 100% | BLOCKED | Router refuse nouvelles taches non taggees | "Budget depasse. Validez explicitement chaque tache ou attendez le reset du mois." |

## Per-modele

Chaque modele (Haiku, Sonnet, Opus) a son propre quota. Un depassement sur Opus ne bloque pas Haiku.

Exemple :

- Haiku 45% -> vert
- Sonnet 87% -> warning, router desescalade T2->T1
- Opus 23% -> vert

Le router consulte les 3 jauges et applique la plus conservatrice.

## Override manuel

L'utilisateur peut toujours forcer un modele par :

- "utilise Opus pour cette tache"
- "critique : ..." (mot-cle qui desactive les desescalades)
- `--force-model opus` en argument du skill

Dans ce cas le router respecte la demande mais affiche l'impact budget :

```
Override utilisateur : Opus force malgre 87% budget consomme.
Impact estime : +3% du budget mensuel.
```
