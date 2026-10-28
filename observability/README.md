# observability/ — Prometheus + Grafana (supervision système)

> Composant net-new (DEC-051, roadmap B) — démarré le 2026-06-19. **Complément** de Langfuse (qui couvre les traces/coûts LLM) : ici = métriques système/services.

## Quoi
- `compose.monitoring.yml` — services Prometheus (`:9090`) + Grafana (`:3002`, Langfuse occupe `:3001`), **bind loopback**, volumes persistants.
- `prometheus/prometheus.yml` — scrape config (self + cibles node_exporter / gateway à activer).
- `grafana/datasources/prometheus.yml` — datasource auto-provisionnée.

## Démarrer (à la demande — Docker on-demand)
```
set GRAFANA_ADMIN_PASSWORD=...   # via env, jamais en clair dans le repo
docker compose -f observability/compose.monitoring.yml up -d
```
Grafana : http://localhost:3002 (admin / $GRAFANA_ADMIN_PASSWORD).

## Sécurité
Loopback only · mot de passe admin via env (défaut `CHANGE_ME` à remplacer) · sign-up désactivé. Ne pas exposer publiquement (Traefik réservé aux services publics).

## Limites / à compléter
node_exporter (métriques OS) à déployer + décommenter la cible ; dashboards Grafana à ajouter sous `grafana/dashboards/`. Démarrer seulement si supervision système riche nécessaire (sinon `cpu_guard`/sysstat suffisent).
