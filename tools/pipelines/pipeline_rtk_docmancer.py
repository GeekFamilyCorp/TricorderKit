#!/usr/bin/env python3
"""
pipeline_rtk_docmancer.py — Pipeline rtk → docmancer
TricorderKit v0.9 — M3

Chaîne rtk (deep-research-core) → docmancer (obsidian-agent-layer) :
  1. Collecte via deep-research-core (MangaDex + AniList)
  2. Déduplication + scoring fiabilité
  3. Export rapport JSON
  4. Construction note Obsidian via note_builder
  5. Écriture dans le vault via obsidian_client (ou dry-run)

Usage:
  python3 tools/pipelines/pipeline_rtk_docmancer.py --query "Chainsaw Man" --domain manga
  python3 tools/pipelines/pipeline_rtk_docmancer.py --query "Studio Ghibli" --domain anime --dry-run

Options:
  --query      Terme de recherche
  --domain     manga | anime (défaut: manga)
  --note-type  Forcer le type de note (manga | anime | mangaka | studio | note)
  --vault      "tricorderkit" | "japan-alliance" (défaut: japan-alliance)
  --dry-run    Simule sans écrire dans le vault
  --json       Sortie JSON résumé
  --skip-collect  Utiliser un fichier de résultats existant (--input)
  --input      Chemin vers un fichier JSON de résultats pre-collectés
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


# ── Chemins ──────────────────────────────────────────────────────────────────

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT_DIR = SCRIPT_DIR.parent.parent
DEEP_RESEARCH_DIR = ROOT_DIR / "plugins" / "deep-research-core" / "scripts"
OBSIDIAN_LAYER_DIR = ROOT_DIR / "plugins" / "obsidian-agent-layer"

sys.path.insert(0, str(OBSIDIAN_LAYER_DIR))

# Import conditionnel note_builder (disponible si obsidian-agent-layer présent)
try:
    from note_builder import NoteSpec, BuiltNote, build_note
    HAS_NOTE_BUILDER = True
except ImportError:
    HAS_NOTE_BUILDER = False


# ── Types ─────────────────────────────────────────────────────────────────────

@dataclass
class PipelineResult:
    query: str
    domain: str
    vault: str
    dry_run: bool
    steps: List[Dict[str, Any]] = field(default_factory=list)
    findings: List[Dict] = field(default_factory=list)
    note_path: Optional[str] = None
    status: str = "pending"
    errors: List[str] = field(default_factory=list)

    def add_step(self, name: str, status: str, detail: Any = None):
        self.steps.append({
            "step": name,
            "status": status,
            "detail": detail,
            "ts": datetime.now(timezone.utc).isoformat(),
        })

    def to_dict(self) -> Dict:
        return {
            "status": self.status,
            "query": self.query,
            "domain": self.domain,
            "vault": self.vault,
            "dry_run": self.dry_run,
            "findings_count": len(self.findings),
            "note_path": self.note_path,
            "steps": self.steps,
            "errors": self.errors,
        }


# ── Étape 1 — Collect ────────────────────────────────────────────────────────

def step_collect(result: PipelineResult, dry_run: bool) -> List[Dict]:
    collect_script = DEEP_RESEARCH_DIR / "collect_sources.py"
    if not collect_script.exists():
        result.errors.append(f"collect_sources.py introuvable : {collect_script}")
        result.add_step("collect", "skip", "Script absent — résultats vides")
        return []

    cmd = [
        sys.executable, str(collect_script),
        "--query", result.query,
        "--domain", result.domain,
        "--output", "json",
    ]
    if dry_run:
        cmd.append("--dry-run")

    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=60,
                              cwd=str(DEEP_RESEARCH_DIR.parent))
        if proc.returncode != 0:
            result.errors.append(f"collect_sources error: {proc.stderr[:300]}")
            result.add_step("collect", "error", proc.stderr[:200])
            return []

        findings = json.loads(proc.stdout)
        if isinstance(findings, dict) and "findings" in findings:
            findings = findings["findings"]
        elif not isinstance(findings, list):
            findings = []

        result.add_step("collect", "ok", f"{len(findings)} findings")
        return findings

    except subprocess.TimeoutExpired:
        result.errors.append("collect_sources timeout (60s)")
        result.add_step("collect", "timeout")
        return []
    except (json.JSONDecodeError, Exception) as e:
        result.errors.append(f"collect_sources exception: {e}")
        result.add_step("collect", "error", str(e))
        return []


# ── Étape 2 — Deduplicate ────────────────────────────────────────────────────

def step_dedup(findings: List[Dict], result: PipelineResult) -> List[Dict]:
    if not findings:
        result.add_step("dedup", "skip", "aucune donnée")
        return findings

    dedup_script = DEEP_RESEARCH_DIR / "deduplicate_findings.py"
    if not dedup_script.exists():
        result.add_step("dedup", "skip", "script absent")
        return findings

    try:
        import tempfile, os
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8") as f:
            json.dump(findings, f)
            tmp_in = f.name

        proc = subprocess.run(
            [sys.executable, str(dedup_script), "--input", tmp_in, "--output", "json"],
            capture_output=True, text=True, timeout=30
        )
        os.unlink(tmp_in)

        if proc.returncode == 0:
            deduped = json.loads(proc.stdout)
            if isinstance(deduped, list):
                result.add_step("dedup", "ok", f"{len(findings)} → {len(deduped)}")
                return deduped
        result.add_step("dedup", "passthrough", f"Script non applicable — {proc.stderr[:100]}")
        return findings
    except Exception as e:
        result.add_step("dedup", "passthrough", str(e))
        return findings


# ── Étape 3 — Score ──────────────────────────────────────────────────────────

def step_score(findings: List[Dict], result: PipelineResult) -> List[Dict]:
    if not findings:
        result.add_step("score", "skip", "aucune donnée")
        return findings

    score_script = DEEP_RESEARCH_DIR / "score_reliability.py"
    if not score_script.exists():
        result.add_step("score", "skip", "script absent")
        return findings

    try:
        import tempfile, os
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8") as f:
            json.dump(findings, f)
            tmp_in = f.name

        proc = subprocess.run(
            [sys.executable, str(score_script), "--input", tmp_in, "--output", "json"],
            capture_output=True, text=True, timeout=30
        )
        os.unlink(tmp_in)

        if proc.returncode == 0:
            scored = json.loads(proc.stdout)
            if isinstance(scored, list):
                result.add_step("score", "ok", f"{len(scored)} findings scorés")
                return scored
        result.add_step("score", "passthrough", proc.stderr[:100])
        return findings
    except Exception as e:
        result.add_step("score", "passthrough", str(e))
        return findings


# ── Étape 4 — Build note ─────────────────────────────────────────────────────

def _infer_note_type(domain: str, findings: List[Dict]) -> str:
    if domain == "anime":
        return "anime"
    if domain == "manga":
        return "manga"
    return "note"


def _extract_title(query: str, findings: List[Dict]) -> str:
    if findings:
        for f in findings:
            title = f.get("title") or f.get("name") or f.get("romaji") or f.get("english")
            if title:
                return str(title)
    return query


def _extract_fields(findings: List[Dict], domain: str) -> Dict[str, Any]:
    if not findings:
        return {}
    top = findings[0]
    fields = {}
    # Champs communs
    for key in ("title", "genres", "status", "year", "url", "score", "description",
                "authors", "publishers", "volumes", "chapters", "episodes",
                "romaji", "english", "japanese", "startDate", "endDate",
                "coverImage", "source", "reliability_score"):
        if key in top:
            fields[key] = top[key]
    # Synthèse multi-findings
    if len(findings) > 1:
        all_urls = list({f["url"] for f in findings if "url" in f})
        if all_urls:
            fields["sources_urls"] = all_urls[:5]
    return fields


def step_build_note(
    findings: List[Dict],
    result: PipelineResult,
    note_type: Optional[str],
) -> Optional[str]:
    if not HAS_NOTE_BUILDER:
        result.add_step("build_note", "skip", "note_builder non disponible")
        return None

    try:
        ntype = note_type or _infer_note_type(result.domain, findings)
        title = _extract_title(result.query, findings)
        fields = _extract_fields(findings, result.domain)

        # Corps libre : résumé des findings
        body_lines = []
        if findings:
            body_lines.append("\n## Résultats de recherche\n")
            for i, f in enumerate(findings[:5], 1):
                src = f.get("source", "?")
                ftitle = f.get("title") or f.get("name", "—")
                url = f.get("url", "")
                score = f.get("reliability_score") or f.get("score", "")
                score_str = f" | score: {score}" if score else ""
                url_str = f" | [{url}]({url})" if url else ""
                body_lines.append(f"{i}. **{ftitle}** ({src}{score_str}){url_str}")

        spec = NoteSpec(
            note_type=ntype,
            title=title,
            fields=fields,
            tags=[result.domain, "rtk-pipeline", "auto-generated"],
            body_extra="\n".join(body_lines),
        )
        built = build_note(spec)
        result.add_step("build_note", "ok", f"type={ntype} | path={built.path}")
        return built.content, built.path

    except Exception as e:
        result.errors.append(f"build_note error: {e}")
        result.add_step("build_note", "error", str(e))
        return None


# ── Étape 5 — Write Obsidian ──────────────────────────────────────────────────

def step_write_obsidian(
    content: str,
    note_path: str,
    result: PipelineResult,
) -> bool:
    if result.dry_run:
        result.add_step("write_obsidian", "dry_run", f"Cible : {note_path}")
        result.note_path = note_path
        return True

    try:
        sys.path.insert(0, str(OBSIDIAN_LAYER_DIR))
        from obsidian_client import ObsidianClient
        vault_name = result.vault

        client = ObsidianClient(vault=vault_name)
        ok = client.write_note(note_path, content)
        if ok:
            result.add_step("write_obsidian", "ok", f"Écrit : {note_path} (vault: {vault_name})")
            result.note_path = note_path
            return True
        else:
            result.add_step("write_obsidian", "error", "client.write_note returned False")
            return False
    except Exception as e:
        result.errors.append(f"write_obsidian error: {e}")
        result.add_step("write_obsidian", "error", str(e))
        return False


# ── Pipeline principal ────────────────────────────────────────────────────────

def run_pipeline(
    query: str,
    domain: str = "manga",
    note_type: Optional[str] = None,
    vault: str = "japan-alliance",
    dry_run: bool = True,
    skip_collect: bool = False,
    input_file: Optional[Path] = None,
) -> PipelineResult:
    result = PipelineResult(
        query=query,
        domain=domain,
        vault=vault,
        dry_run=dry_run,
    )

    # Étape 1 — Collect ou chargement fichier
    if skip_collect and input_file and input_file.exists():
        with open(input_file, encoding="utf-8") as f:
            findings = json.load(f)
        if isinstance(findings, dict) and "findings" in findings:
            findings = findings["findings"]
        result.add_step("collect", "loaded", f"{len(findings)} findings depuis {input_file.name}")
    else:
        findings = step_collect(result, dry_run)

    result.findings = findings

    if not findings:
        result.status = "partial" if result.errors else "empty"
        return result

    # Étape 2 — Dedup
    findings = step_dedup(findings, result)
    result.findings = findings

    # Étape 3 — Score
    findings = step_score(findings, result)
    result.findings = findings

    # Étape 4 — Build note
    note_result = step_build_note(findings, result, note_type)

    if note_result is None:
        result.status = "partial"
        return result

    note_content, note_path = note_result

    # Étape 5 — Write Obsidian
    step_write_obsidian(note_content, note_path, result)
    result.status = "success"
    return result


# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Pipeline rtk → docmancer")
    parser.add_argument("--query", required=True)
    parser.add_argument("--domain", default="manga", choices=["manga", "anime", "publishers", "github"])
    parser.add_argument("--note-type", default=None)
    parser.add_argument("--vault", default="japan-alliance", choices=["japan-alliance", "tricorderkit"])
    parser.add_argument("--dry-run", action="store_true", default=True)
    parser.add_argument("--no-dry-run", dest="dry_run", action="store_false")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--skip-collect", action="store_true")
    parser.add_argument("--input", type=Path, default=None)
    args = parser.parse_args()

    result = run_pipeline(
        query=args.query,
        domain=args.domain,
        note_type=args.note_type,
        vault=args.vault,
        dry_run=args.dry_run,
        skip_collect=args.skip_collect,
        input_file=args.input,
    )

    if args.json:
        print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
    else:
        icon = "✅" if result.status == "success" else "⚠️" if result.status == "partial" else "🔴"
        print(f"{icon} Pipeline rtk→docmancer : {result.status}")
        print(f"   Query : {result.query} | Domain : {result.domain} | Dry-run : {result.dry_run}")
        print(f"   Findings : {len(result.findings)} | Note : {result.note_path or '—'}")
        for step in result.steps:
            s = step['status']
            icon2 = "✅" if s == "ok" else "⏭" if s in ("skip","passthrough","dry_run","loaded") else "🔴"
            detail = f" — {step['detail']}" if step.get('detail') else ""
            print(f"   {icon2} {step['step']}: {s}{detail}")
        if result.errors:
            print(f"   Erreurs : {result.errors}")

    return 0 if result.status in ("success", "partial", "empty") else 1


if __name__ == "__main__":
    sys.exit(main())
