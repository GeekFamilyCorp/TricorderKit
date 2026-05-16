# security-audit-cli — Skill Audit de Sécurité TricorderKit
> Version : 0.1.0 — 16/05/2026
> Ancrage : TricorderKit v0.8 — Phase 5 active
> Statut : Scaffoldé — en développement

---

## 🎯 Rôle & déclencheurs

`security-audit-cli` est le **gardien de sécurité** de l'écosystème TricorderKit. Il détecte les fuites de secrets, les permissions excessives, les dépendances vulnérables et les patterns de code à risque — avant qu'ils n'atteignent le dépôt public.

### Responsabilités
1. **Secret scanning** — détecter clés API, tokens, mots de passe dans les fichiers sources
2. **Dependency audit** — scanner `requirements.txt`, `package.json`, `pyproject.toml` vs CVE connus
3. **Permission check** — vérifier les permissions fichiers (exécutables non intentionnels, .env exposés)
4. **Pattern check** — détecter anti-patterns sécurité (eval(), subprocess shell=True, hardcoded paths)
5. **Anonymisation check** — vérifier l'absence de termes privés dans les fichiers destinés au repo public

### Déclencheurs
- Commande : `/tk:security audit` (scan complet)
- Commande : `/tk:security check-anonymization <file>`
- Avant tout push vers un repo GitHub public
- En CI/CD (exit code 2 si CRITICAL bloque le push)

### Ce qu'il N'EST PAS
- ❌ Un scanner SAST complet (Bandit/Semgrep font ça — security-audit-cli les orchestre)
- ❌ Un gestionnaire de secrets (HashiCorp Vault / SOPS font ça)
- ❌ Un firewall réseau ou WAF

---

## ⚙️ Architecture

```
plugins/security-audit-cli/
├── SKILL.md                   ← Ce fichier
├── manifest.yml               ← Compatible cli-forge
├── security_runner.py         ← CLI principale (Typer)
├── secret_scanner.py          ← Regex patterns API keys, tokens, passwords
├── dependency_auditor.py      ← Pip-audit / npm audit wrapper
├── permission_checker.py      ← Vérification chmod + fichiers sensibles exposés
├── pattern_checker.py         ← Anti-patterns code (eval, shell=True, etc.)
├── anonymization_checker.py   ← Détection termes privés pour push public
└── tests/
    ├── __init__.py
    ├── conftest.py
    ├── test_secret_scanner.py
    ├── test_anonymization_checker.py
    └── test_security_runner.py
```

---

## 🔍 Règles de détection

### Secret Scanner — patterns CRITICAL
| Pattern               | Exemple détecté                          |
|---|---|
| API Key générique     | `api_key = "sk-..."`, `API_KEY=abc123`  |
| Token GitHub          | `ghp_...`, `github_pat_...`             |
| Token Anthropic       | `sk-ant-...`                            |
| Clé AWS               | `AKIA[0-9A-Z]{16}`                      |
| Password hardcodé     | `password = "..."`, `passwd = "..."`    |
| Connection string DB  | `postgresql://user:pass@host/db`        |

### Anonymisation — termes privés bloquants (push public)
| Terme bloquant         | Raison                                 |
|---|---|
| `Japan-Alliance`       | Nom du projet privé                    |
| `MangaTracker`         | Nom de l'app privée                    |
| `mangatracker-cli`     | Nom de la CLI privée                   |

### Pattern Checker — sévérité HIGH
- `eval(` dans du code Python non test
- `subprocess.*shell=True` sans commentaire justificatif
- `os.system(` sans whitelist explicite
- `pickle.loads(` sur input non validé

---

## 📤 Output Contract

```json
{
  "status": "success|partial|error|dry_run",
  "skill_name": "security-audit-cli",
  "skill_version": "0.1.0",
  "timestamp": "...",
  "output": {
    "summary": "Audit OK — 0 secret, 0 CVE critique, 2 warnings pattern",
    "data": {
      "secrets_found": 0,
      "cve_critical": 0,
      "cve_high": 0,
      "pattern_warnings": 2,
      "anonymization_violations": 0,
      "files_scanned": 47,
      "findings": []
    },
    "files_created": ["reports/security/security_report_2026-05-16.md"],
    "next_steps": ["Corriger pattern eval() dans plugins/x/y.py:L42"]
  }
}
```

---

## 🚀 Commandes CLI

```bash
# Audit complet du repo
python plugins/security-audit-cli/security_runner.py audit

# Scanner uniquement les secrets
python plugins/security-audit-cli/security_runner.py scan-secrets --path plugins/

# Vérifier anonymisation avant push public
python plugins/security-audit-cli/security_runner.py check-anon --path plugins/tk-orchestrator/

# Auditer les dépendances
python plugins/security-audit-cli/security_runner.py audit-deps

# Dry-run complet
python plugins/security-audit-cli/security_runner.py audit --dry-run
```

---

## 🛡️ Niveaux de sévérité

| Niveau   | Critères                                      | Comportement CI          |
|---|---|---|
| CRITICAL | Secret exposé, terme privé dans repo public   | Bloquer push — exit 2    |
| HIGH     | Pattern dangereux, CVE score >= 9.0           | Warning — exit 1         |
| MEDIUM   | CVE score 7.0–8.9, permission incorrecte      | Warning — exit 0         |
| LOW      | CVE score < 7.0, style recommendation        | Info — exit 0            |

---

## 📊 Notes de fiabilité

| Élément               | Niveau        | Commentaire                                              |
|---|---|---|
| Secret scanning regex | ✅ Confirmé   | Patterns battle-tested (gitleaks / trufflehog patterns) |
| Anonymisation check   | ✅ Confirmé   | Critique pour workflow public/privé TricorderKit        |
| Dependency audit      | 🟡 Probable   | Dépend de pip-audit — disponible Python 3.10+           |
| Pattern check         | 🟡 Probable   | Faux positifs possibles sur code commenté               |
| Intégration CI        | 🟠 À vérifier | Hook pre-push Git à configurer                         |

---

*security-audit-cli v0.1.0 — 16/05/2026 — TricorderKit v0.8*
