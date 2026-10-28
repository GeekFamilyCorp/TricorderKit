#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
promote_skill.py — Étape 5 (finale) de la boucle learning-engine (DEC-046, Lot A).

Promeut un skill UNIQUEMENT si la proposition satisfait toutes les conditions
non négociables (DEC-046). Sinon : REFUS explicite, aucun changement.

  SkillUpdateProposal --> [gate des 8 tests + humain + rollback] --> promoted | refusé

Conditions de promotion (toutes requises) :
  1. Les 8 tests = "passed" (ou "n/a" justifié) — aucun "pending"/"failed".
  2. human_review_required satisfait : reviewed_by renseigné ET tests.human_validation == passed.
  3. rollback.available == true ET un backup réel existe (sauf --dry-run).
  4. Le draft existe sous skills/<id>/drafts/ (jamais le skill actif modifié hors backup).

Comportement :
  - DRY-RUN PAR DÉFAUT : simule la promotion, n'écrit rien (Règle 4).
  - --apply : effectue la promotion seulement si le gate passe ET --backup-path fourni
    (le backup du SKILL.md actif est créé avant remplacement). Refus sinon.

Ce script NE génère PAS de contenu de skill : il promeut un draft validé existant
(`--draft-content` = fichier markdown du nouveau SKILL.md, optionnel pour --apply).

Sortie : enveloppe skill_output (--format json|md).

Exemple (simulation) :
  python promote_skill.py --proposal draft.json
Exemple (réel) :
  python promote_skill.py --proposal draft.json --apply \
      --draft-content new_skill.md --backup-path skills/x/backups/SKILL.md.bak
"""
from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

import _common as C

SKILL = "learning-promote-skill"
REPO_SKILLS = C.REPO_ROOT / "skills"

REQUIRED_TESTS = ["historical_data", "fresh_sources", "non_regression", "schema_validity",
                  "token_cost", "security", "rollback_tested", "human_validation"]


def gate(proposal: dict, *, applying: bool, backup_path: str | None) -> list[str]:
    """Retourne la liste des blocages (vide = promotion autorisée)."""
    blockers: list[str] = []
    tests = proposal.get("tests", {}) or {}
    for t in REQUIRED_TESTS:
        state = tests.get(t, "pending")
        if state not in ("passed", "n/a"):
            blockers.append(f"test '{t}' = {state} (exigé: passed)")

    if not proposal.get("reviewed_by"):
        blockers.append("reviewed_by manquant (validation humaine non tracée)")
    if tests.get("human_validation") != "passed":
        blockers.append("tests.human_validation != passed")

    rb = proposal.get("rollback", {}) or {}
    if not rb.get("available"):
        blockers.append("rollback.available != true")

    draft = proposal.get("draft_path", "")
    if "drafts" not in draft.lower():
        blockers.append("draft_path n'est pas sous 'drafts/' (garde-fou skill actif)")

    if applying:
        if not backup_path:
            blockers.append("--backup-path requis pour --apply")
    return blockers


def main(argv=None) -> int:
    C.setup_utf8()
    ap = argparse.ArgumentParser(description="Promeut un skill si le gate DEC-046 passe.")
    ap.add_argument("--proposal", required=True, help="Fichier skill_update_proposal JSON")
    ap.add_argument("--apply", action="store_true",
                    help="Effectue réellement la promotion (sinon: dry-run)")
    ap.add_argument("--draft-content", default=None,
                    help="Markdown du nouveau SKILL.md (requis pour --apply réel)")
    ap.add_argument("--backup-path", default=None,
                    help="Chemin du backup du SKILL.md actif (requis pour --apply)")
    ap.add_argument("--target-skill-md", default=None,
                    help="Override du SKILL.md cible (défaut: skills/<skill_id>/SKILL.md)")
    C.add_format_arg(ap)
    args = ap.parse_args(argv)

    try:
        proposal = C.read_json(args.proposal)
    except Exception as e:  # noqa: BLE001
        return C.fail(SKILL, "ERR_INPUT", f"Lecture proposition impossible: {e}", fmt=args.format)

    errs = C.validate(proposal, "skill_update_proposal")
    if errs:
        return C.fail(SKILL, "ERR_SCHEMA_PROPOSAL",
                      "Proposition non conforme: " + " | ".join(errs[:5]), fmt=args.format)

    applying = bool(args.apply)
    blockers = gate(proposal, applying=applying, backup_path=args.backup_path)

    if blockers:
        # REFUS — aucun changement. Statut reflété sans écraser le fichier source.
        C.emit(C.skill_output(
            skill_name=SKILL, status="error",
            summary=f"Promotion REFUSÉE ({len(blockers)} blocage(s)). Skill inchangé.",
            data={"proposal_id": proposal.get("proposal_id"), "blockers": blockers,
                  "resulting_status": "test_failed" if any("test" in b for b in blockers)
                  else "human_review_required"},
            error={"code": "ERR_GATE_BLOCKED",
                   "message": "; ".join(blockers),
                   "recoverable": True, "rollback_available": True},
        ), args.format)
        return 1

    skill_id = proposal["skill_id"]
    target = Path(args.target_skill_md) if args.target_skill_md \
        else REPO_SKILLS / skill_id / "SKILL.md"

    if not applying:
        C.emit(C.skill_output(
            skill_name=SKILL, status="dry_run",
            summary=f"Gate OK pour {proposal['proposal_id']} — promotion simulée (non appliquée).",
            data={"proposal_id": proposal["proposal_id"], "would_promote_skill": skill_id,
                  "target": str(target), "resulting_status": "promoted"},
            dry_run_report={"actions_that_would_run":
                            [f"backup {target} -> {args.backup_path or '<backup-path requis>'}",
                             f"write {target} (depuis --draft-content)",
                             "set proposal.status = promoted"],
                            "risk_level": proposal.get("risk_level", "HIGH")},
        ), args.format)
        return 0

    # ── Application réelle ───────────────────────────────────────────────────────
    if not args.draft_content or not Path(args.draft_content).exists():
        return C.fail(SKILL, "ERR_NO_CONTENT",
                      "--draft-content (markdown du nouveau SKILL.md) requis et doit exister.",
                      fmt=args.format)

    backup = Path(args.backup_path)
    files = []
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            backup.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(target, backup)
            files.append(str(backup))
        shutil.copy2(args.draft_content, target)
        files.append(str(target))
    except Exception as e:  # noqa: BLE001
        return C.fail(SKILL, "ERR_PROMOTE_IO", f"Échec écriture: {e}",
                      recoverable=True, rollback_available=backup.exists(), fmt=args.format)

    # Met à jour la proposition (status promoted)
    proposal["status"] = "promoted"
    proposal.setdefault("rollback", {})["backup_path"] = str(backup)
    files.append(str(C.write_json(args.proposal, proposal)))

    C.emit(C.skill_output(
        skill_name=SKILL, status="success",
        summary=f"Skill '{skill_id}' promu depuis {proposal['proposal_id']}. "
                f"Backup créé, rollback disponible.",
        data={"proposal_id": proposal["proposal_id"], "skill_id": skill_id,
              "backup_path": str(backup)},
        files_created=files,
        decisions_logged=[proposal["decision_ref"]] if proposal.get("decision_ref") else None,
        next_steps=["Monitorer la non-régression post-promotion (eval-lab)",
                    "Loguer DEC-NNN si impact élevé"],
    ), args.format)
    return 0


if __name__ == "__main__":
    sys.exit(main())
