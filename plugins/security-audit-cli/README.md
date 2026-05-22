# security-audit-cli

> TricorderKit plugin v0.1.0 — Audit de sécurité (secrets, anonymisation, patterns)

---

## Commandes

```bash
# Via tk CLI (recommandé)
tk security scan                        # Scanner les secrets hardcodés
tk security scan --path plugins/        # Scanner un répertoire spécifique
tk security check-anon --path plugins/  # Vérifier l'anonymisation avant push public
tk security check-patterns              # Détecter les anti-patterns de sécurité
tk security audit                       # Audit complet
tk security audit --report              # Audit + sauvegarde rapport JSON
tk security dry-run                     # Simuler sans persistance

# Direct (depuis la racine du repo)
python plugins/security-audit-cli/scripts/security_runner.py audit
python plugins/security-audit-cli/scripts/security_runner.py scan-secrets --path . --json
python plugins/security-audit-cli/scripts/security_runner.py check-anon --path plugins/
```

---

## Modules

| Module | Rôle |
|---|---|
| `secret_scanner.py` | Détection clés API, tokens, passwords, connection strings (10 patterns) |
| `pattern_checker.py` | Détection anti-patterns (`eval()`, `shell=True`, `os.system()`, `pickle.loads()`) + `# nosec` |
| `anonymization_checker.py` | Détection termes privés avant push public (Japan-Alliance, MangaTracker, …) |
| `scripts/security_runner.py` | CLI Typer — point d'entrée principal |

---

## Sévérités

| Niveau | Critères | Exit code |
|---|---|---|
| CRITICAL | Secret exposé, terme privé dans repo public | 2 |
| HIGH | Anti-pattern dangereux | 1 |
| MEDIUM/LOW | Avertissements | 0 |

---

## Tests

```bash
pytest tests/test_security_audit.py -v   # 16 tests
```

---

*security-audit-cli v0.1.0 — TricorderKit v0.9*
