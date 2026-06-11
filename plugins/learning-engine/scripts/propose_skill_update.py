#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
propose_skill_update.py — Étape 4 de la boucle learning-engine (DEC-046, Lot A).

Transforme des leçons acceptées en une proposition de mise à jour de skill
(skill_update_proposal.schema.json). Le draft est écrit dans
`skills/<skill_id>/drafts/` — JAMAIS le skill actif.

  Lessons (accepted) --> SkillUpdateProposal (draft, tests=pending)

Garde-fous (DEC-046) :
  - draft uniquement, jamais le SKILL.md actif ;
  - les 8 tests sont initialisés à "pending" (la promotion exige tous "passed") ;
  - human_review_required: true ; rollback décrit (backup obligatoire à la promotion) ;
  - par défaut, seules les leçons status="accepted" sont prises (--include-observed
    pour forcer, déconseillé).

Sortie : enveloppe skill_output (--format json|md).

Exemple :
  python propose_skill_update.py --skill-id mangatracker-lookup \
      --lessons-dir runs/learning/lessons --skill-version 1.2.0
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import _common as C

SKILL = "learning-propose-skill-update"
REPO_SKILLS = C.REPO_ROOT / "skills"

EIGHT_TESTS = ["historical_data", "fresh_sources", "non_regression", "schema_validity",
               "token_cost", "security", "rollback_tested", "human_validation"]


def _slug(text: str) -> str:
    return "".join(ch if ch.isalnum() else "_" for ch in text.lower()).strip("_") or "skill"


def build_proposal(skill_id: str, lessons: list[dict], skill_version: str | None,
                   draft_path: str, risk_level: str) -> dict:
    today = C.today()
    actions = [ls["action"] for ls in lessons]
    proposed_change = " ; ".join(dict.fromkeys(actions))  # dédup en préservant l'ordre

    evidence = []
    for ls in lessons:
        evidence.append({
            "claim": ls["observation"],
            "metric": "confidence",
            "new_value": ls.get("confidence", 0),
            "source_runs": ls.get("source_runs", []),
        })

    proposal = {
        "proposal_id": f"sup_{today.replace('-', '_')}_{_slug(skill_id)}",
        "date": today,
        "skill_id": skill_id,
        "lesson_ids": [ls["lesson_id"] for ls in lessons],
        "proposed_change": proposed_change,
        "draft_path": draft_path,
        "evidence": evidence,
        "risk_level": risk_level,
        "tests": {t: "pending" for t in EIGHT_TESTS},
        "rollback": {
            "available": False,
            "procedure": "Restaurer le SKILL.md depuis le backup horodaté avant promotion.",
            "backup_path": f"skills/{skill_id}/backups/SKILL.md.<timestamp>.bak",
        },
        "status": "draft_created",
        "human_review_required": True,
    }
    if skill_version:
        proposal["skill_current_version"] = skill_version
    return proposal


def render_draft_md(skill_id: str, proposal: dict, lessons: list[dict]) -> str:
    lines = [f"# DRAFT — proposition de mise à jour : `{skill_id}`",
             f"\n> Proposition `{proposal['proposal_id']}` — {proposal['date']}",
             "> ⚠️ DRAFT non promu. Ne remplace PAS le skill actif. "
             "Promotion conditionnée aux 8 tests + validation humaine (DEC-046).\n",
             "## Changement proposé", proposal["proposed_change"], "",
             "## Leçons sources"]
    for ls in lessons:
        lines.append(f"- `{ls['lesson_id']}` (conf. {ls.get('confidence', 0):.2f}) — "
                     f"{ls['observation']}")
    lines += ["", "## Tests requis (tous 'passed' avant promotion)"]
    for t in EIGHT_TESTS:
        lines.append(f"- [ ] {t}")
    lines += ["", "## Rollback", f"- {proposal['rollback']['procedure']}",
              f"- Backup : `{proposal['rollback']['backup_path']}`", ""]
    return "\n".join(lines) + "\n"


def main(argv=None) -> int:
    C.setup_utf8()
    ap = argparse.ArgumentParser(description="Propose une mise à jour de skill (draft).")
    ap.add_argument("--skill-id", required=True)
    ap.add_argument("--lessons-dir", default=str(C.PLUGIN_ROOT / "runs" / "learning" / "lessons"))
    ap.add_argument("--lesson", action="append", default=[],
                    help="Fichier(s) de leçon explicite(s) (sinon: tout le dossier)")
    ap.add_argument("--skill-version", default=None)
    ap.add_argument("--risk-level", choices=["LOW", "MEDIUM", "HIGH", "CRITICAL"], default="MEDIUM")
    ap.add_argument("--include-observed", action="store_true",
                    help="Inclure les leçons status='observed' (déconseillé)")
    ap.add_argument("--drafts-dir", default=None,
                    help="Override du dossier draft (défaut: skills/<skill_id>/drafts)")
    ap.add_argument("--dry-run", action="store_true")
    C.add_format_arg(ap)
    args = ap.parse_args(argv)

    paths = [Path(p) for p in args.lesson] if args.lesson \
        else C.iter_json_files(args.lessons_dir)
    lessons = []
    for p in paths:
        try:
            ls = C.read_json(p)
        except Exception:  # noqa: BLE001
            continue
        if C.validate(ls, "lesson"):
            continue  # ignore les fichiers non-leçon
        accepted = ls.get("status") == "accepted"
        if accepted or (args.include_observed and ls.get("status") == "observed"):
            lessons.append(ls)

    if not lessons:
        return C.fail(SKILL, "ERR_NO_LESSONS",
                      "Aucune leçon acceptée trouvée (utiliser --include-observed pour forcer, "
                      "après revue humaine).", fmt=args.format)

    drafts_dir = Path(args.drafts_dir) if args.drafts_dir \
        else REPO_SKILLS / args.skill_id / "drafts"
    # Garde-fou dur : interdiction d'écrire un SKILL.md actif
    proposal_stub = f"sup_{C.today().replace('-', '_')}_{_slug(args.skill_id)}"
    draft_json = drafts_dir / f"{proposal_stub}.json"
    draft_md = drafts_dir / f"{proposal_stub}.md"
    if draft_json.name.upper() == "SKILL.MD" or "drafts" not in str(drafts_dir).lower():
        return C.fail(SKILL, "ERR_GUARD_ACTIVE_SKILL",
                      "Refus : le chemin de sortie n'est pas un dossier 'drafts/'.",
                      recoverable=False, fmt=args.format)

    proposal = build_proposal(args.skill_id, lessons, args.skill_version,
                              draft_path=str(draft_json), risk_level=args.risk_level)
    errs = C.validate(proposal, "skill_update_proposal")
    if errs:
        return C.fail(SKILL, "ERR_SCHEMA_PROPOSAL",
                      "Proposition non conforme: " + " | ".join(errs[:5]), fmt=args.format)

    if args.dry_run:
        C.emit(C.skill_output(
            skill_name=SKILL, status="dry_run",
            summary=f"Proposition {proposal['proposal_id']} prête (draft, {len(lessons)} leçon(s)).",
            data={"proposal": proposal},
            dry_run_report={"actions_that_would_run": [f"write {draft_json}", f"write {draft_md}"],
                            "risk_level": args.risk_level},
        ), args.format)
        return 0

    files = [str(C.write_json(draft_json, proposal))]
    drafts_dir.mkdir(parents=True, exist_ok=True)
    draft_md.write_text(render_draft_md(args.skill_id, proposal, lessons), encoding="utf-8")
    files.append(str(draft_md))

    C.emit(C.skill_output(
        skill_name=SKILL, status="success",
        summary=f"Draft {proposal['proposal_id']} créé (tests pending, review requise). "
                f"Skill actif intact.",
        data={"proposal_id": proposal["proposal_id"], "tests": proposal["tests"],
              "draft_path": str(draft_json)},
        files_created=files,
        next_steps=["Faire passer les 8 tests (eval-lab) -> 'passed'",
                    "Validation humaine -> reviewed_by",
                    "promote_skill.py --proposal " + str(draft_json) + " --apply"],
    ), args.format)
    return 0


if __name__ == "__main__":
    sys.exit(main())
