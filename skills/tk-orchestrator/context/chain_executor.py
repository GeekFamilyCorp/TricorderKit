"""
chain_executor.py - Execution de chaines avec politique Abort-on-Failure
TricorderKit v0.8 - tk-orchestrator v0.2.0
"""

from __future__ import annotations
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from budget.token_tracker import TokenBudget


MAX_CHAIN_STEPS = 5
CHAIN_STATUS_SUCCESS = "success"
CHAIN_STATUS_ERROR = "error"
CHAIN_STATUS_SKIPPED = "skipped"
CHAIN_STATUS_DRY_RUN = "dry_run"
CHAIN_STATUS_LIMIT = "chain_limit_exceeded"


@dataclass
class ChainStep:
    tool: str
    command: str
    args: Dict[str, Any] = field(default_factory=dict)
    risk_level: str = "LOW"


@dataclass
class StepResult:
    step: int
    tool: str
    command: str
    status: str
    tokens: int = 0
    duration_ms: int = 0
    output: Optional[Dict] = None
    error: Optional[str] = None


@dataclass
class ChainResult:
    overall_status: str
    steps: List[StepResult] = field(default_factory=list)
    total_tokens: int = 0
    total_duration_ms: int = 0
    aborted_at_step: Optional[int] = None
    abort_reason: Optional[str] = None

    @property
    def success_count(self):
        return sum(1 for s in self.steps if s.status == CHAIN_STATUS_SUCCESS)

    @property
    def skipped_count(self):
        return sum(1 for s in self.steps if s.status == CHAIN_STATUS_SKIPPED)

    def to_dict(self):
        return {
            "overall_status": self.overall_status,
            "steps": [
                {
                    "step": s.step,
                    "tool": s.tool,
                    "command": s.command,
                    "status": s.status,
                    "tokens": s.tokens,
                    "duration_ms": s.duration_ms,
                    "error": s.error,
                }
                for s in self.steps
            ],
            "total_tokens": self.total_tokens,
            "total_duration_ms": self.total_duration_ms,
            "aborted_at_step": self.aborted_at_step,
            "abort_reason": self.abort_reason,
            "summary": {
                "success": self.success_count,
                "skipped": self.skipped_count,
                "total": len(self.steps),
            },
        }


class ChainExecutor:
    def __init__(self, budget: TokenBudget, dry_run: bool = False, max_steps: int = MAX_CHAIN_STEPS):
        self.budget = budget
        self.dry_run = dry_run
        self.max_steps = max_steps

    def execute(self, steps: List[ChainStep], step_runner: Callable) -> ChainResult:
        result = ChainResult(overall_status=CHAIN_STATUS_SUCCESS)
        previous_output = None

        if len(steps) > self.max_steps:
            steps = steps[:self.max_steps]
            result.abort_reason = "Chaine tronquee a {} etapes".format(self.max_steps)

        for i, step in enumerate(steps, start=1):
            t_start = time.time()

            if self.dry_run:
                result.steps.append(StepResult(
                    step=i, tool=step.tool, command=step.command,
                    status=CHAIN_STATUS_DRY_RUN, tokens=0, duration_ms=0,
                    output={"would_execute": True, "args": step.args},
                ))
                continue

            try:
                raw = step_runner(step, previous_output, self.dry_run)
            except Exception as exc:
                raw = {"status": "error", "error": str(exc), "tokens": 0, "output": None}

            duration_ms = int((time.time() - t_start) * 1000)
            tokens = raw.get("tokens", 0)
            self.budget.consume(tokens, purpose="step_{}:{}".format(i, step.tool), step=i)
            result.total_tokens += tokens
            result.total_duration_ms += duration_ms

            step_status = raw.get("status", "error")
            result.steps.append(StepResult(
                step=i, tool=step.tool, command=step.command,
                status=step_status, tokens=tokens, duration_ms=duration_ms,
                output=raw.get("output"), error=raw.get("error"),
            ))

            if step_status == CHAIN_STATUS_ERROR:
                result.overall_status = "partial"
                result.aborted_at_step = i
                result.abort_reason = raw.get("error", "Erreur inconnue")
                self._add_skipped(result, steps[i:], i + 1)
                break

            previous_output = raw.get("output")

        if self.dry_run and result.overall_status == CHAIN_STATUS_SUCCESS:
            result.overall_status = CHAIN_STATUS_DRY_RUN

        return result

    def _add_skipped(self, result, remaining_steps, start_index):
        for j, step in enumerate(remaining_steps, start=start_index):
            result.steps.append(StepResult(
                step=j, tool=step.tool, command=step.command, status=CHAIN_STATUS_SKIPPED,
            ))
