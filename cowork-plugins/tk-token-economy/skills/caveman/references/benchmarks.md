# Benchmarks caveman — chiffres tiers, datés

Valeurs annoncées par les projets sources (relevé du 2026-04, non re-mesuré par GeekFamilyCorp).
À prendre comme ordre de grandeur sur des réponses en prose ; sans effet sur le code.

| Mode | Économie annoncée (tokens de sortie) | Source |
|------|--------------------------------------|--------|
| lite | ~40-50 % | JuliusBrussee/caveman |
| full | ~65-75 % | JuliusBrussee/caveman |
| ultra | ~85-90 % | GabrielBarberini/laconic |

Sources : https://github.com/JuliusBrussee/caveman · https://github.com/GabrielBarberini/laconic

Pour mesurer localement : logger deux réponses comparables via `budget.py log --model default --in N --out N`
(avec et sans caveman) et comparer les `out`.
