# eval-lab — Skill Non-Régression & Validation Qualité
> Version : 0.1.0 — 16/05/2026
> Ancrage : TricorderKit v0.8 — Phase 5 active
> Statut : Implémenté — prod_ready

---

## 🎯 Rôle & déclencheurs

`eval-lab` est le **gardien de contrat** de l'écosystème TricorderKit. Il valide que :
1. Chaque skill produit un output conforme à `skill_output.schema.json` v1.0.0
2. Aucune régression silencieuse n'est introduite lors d'une modification de skill
3. Les baselines de référence sont persistées et comparées automatiquement

### Déclencheurs
- Commande : `/tk:eval <skill_name>` ou `/tk:eval --all`
- Avant tout merge ou push impliquant un skill
- Après modification d'un SKILL.md ou d'un script de skill
- Batch nocturne (workflow Temporal `skill_eval`) — Phase 3

### Ce qu'il N'EST PAS
- ❌ Un test runner généraliste (pytest fait ça — eval-lab teste les contrats d'output)
- ❌ Un linter de code (QualityGuard fait ça)
- ❌ Un validateur de sécurité (security-audit-cli)

---

## ⚙️ Architecture

```
plugins/eval-lab/
├── SKILL.md                  ← Ce fichier
├── README.md
├── manifest.yml              ← Compatible cli-forge
├── eval_runner.py            ← CLI principale (Typer)
├── schema_validator.py       ← Validation JSON vs skill_output.schema.json
├── regression_checker.py     ← Comparaison output courant vs baseline
├── baseline_store.py         ← Persistance SQLite des baselines
├── report_generator.py       ← Rapport Markdown + JSON
└── tests/
    ├── __init__.py
    ├── conftest.py
    ├── test_schema_validator.py
    ├── test_regression_checker.py
    └── test_eval_runner.py
```

---

## 🔄 Pipeline d'évaluation

```text
1. collect_output(skill_name, input_fixture)
   → Exécute le skill avec une fixture d'entrée standardisée
   → Capture stdout JSON

2. validate_schema(output)
   → Valide contre skill_output.schema.json v1.0.0
   → Échoue si champ obligatoire manquant ou type incorrect

3. check_regression(skill_name, output)
   → Charge baseline depuis SQLite (baseline_store)
   → Compare champs critiques : status, output.summary structure, tokens_used plausibilité
   → Détecte : champs disparus, types changés, valeurs aberrantes

4. update_baseline(skill_name, output)  [si --update-baseline]
   → Persiste l'output courant comme nouvelle baseline

5. generate_report(results)
   → Markdown : tableau récap + détails erreurs
   → JSON : conforme skill_output.schema.json pour chaînage
```

---

## 📤 Output Contract

```json
{
  "status": "success|partial|error|dry_run",
  "skill_name": "eval-lab",
  "skill_version": "0.1.0",
  "timestamp": "...",
  "output": {
    "summary": "Eval 3/3 skills — 2 OK, 1 régression détectée (tk-boot: champ tokens_used.total absent)",
    "data": {
      "skills_evaluated": 3,
      "passed": 2,
      "failed": 1,
      "regressions": [
        {
          "skill": "tk-boot",
          "field": "tokens_used.total",
          "expected": "integer",
          "got": null,
          "severity": "CRITICAL"
        }
      ],
      "schema_violations": [],
      "baseline_updated": false
    },
    "files_created": ["reports/eval_report_2026-05-16.md"],
    "next_steps": ["Corriger tk-boot : ajouter tokens_used.total", "Relancer eval tk-boot"]
  }
}
```

---

## 🚀 Commandes CLI

```bash
# Eval un skill spécifique
python plugins/eval-lab/eval_runner.py eval tk-orchestrator

# Eval tous les skills du registry
python plugins/eval-lab/eval_runner.py eval --all

# Dry-run (simulation sans exécution)
python plugins/eval-lab/eval_runner.py --dry-run eval tk-boot

# Mettre à jour la baseline après correction
python plugins/eval-lab/eval_runner.py eval tk-boot --update-baseline

# Rapport seul (sans re-run)
python plugins/eval-lab/eval_runner.py report --skill tk-orchestrator

# Validation schema seule (input depuis stdin)
echo '{"status":"success",...}' | python plugins/eval-lab/eval_runner.py validate-schema
```

---

## 🛡️ Niveaux de sévérité régression

| Niveau | Critères | Comportement |
|---|---|---|
| CRITICAL | Champ obligatoire disparu, type changé | Bloquer merge — exit code 2 |
| HIGH | Valeur aberrante (score négatif, timestamp futur) | Warning + log |
| MEDIUM | Champ optionnel disparu | Warning |
| LOW | Changement de contenu attendu | Info |

---

## 📊 Notes de fiabilité

| Élément | Niveau | Commentaire |
|---|---|---|
| Schema validation | ✅ Confirmé | `jsonschema` v4 — même lib que test_schema_compliance.py |
| Baseline SQLite | ✅ Confirmé | Pattern éprouvé (QualityGuard error_memory) |
| Regression check | 🟡 Probable | Comparaison structurelle, pas sémantique |
| Intégration CI | 🟠 À vérifier | Exit codes à tester en environnement Windows |

---

*eval-lab v0.1.0 — 16/05/2026 — TricorderKit v0.8*
