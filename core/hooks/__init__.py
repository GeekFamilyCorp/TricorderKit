"""
core.hooks — Hook Layer TricorderKit v0.2.0

Exports principaux :
    run_pre_intent_hook     (pre_intent_hook.py)
    run_pre_execution_hook  (pre_execution_hook.py)
    run_post_execution_hook (post_execution_hook.py)

Usage typique dans MainBrain :
    from core.hooks import run_pre_intent_hook, run_pre_execution_hook, run_post_execution_hook

    enriched_input = run_pre_intent_hook(raw_user_input)
    enriched_plan  = run_pre_execution_hook(plan)
    final_result   = run_post_execution_hook(enriched_plan, skill_result)
"""
from .pre_intent_hook import run_pre_intent_hook
from .pre_execution_hook import run_pre_execution_hook
from .post_execution_hook import run_post_execution_hook

__all__ = [
    "run_pre_intent_hook",
    "run_pre_execution_hook",
    "run_post_execution_hook",
]
