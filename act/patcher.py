from typing import Any, Dict
import os
from tools.patch_utils import apply_diff_unified


def _render_context(plan: Dict[str, Any]) -> str:
    parts = [
        f"Objective: {plan.get('objective','')}",
        f"Files: {', '.join(plan.get('files', []) or [])}",
        f"Invariants: {', '.join(plan.get('invariants', []) or [])}",
        f"Tests: {', '.join(plan.get('tests_to_run', []) or [])}",
    ]
    return "\n".join(parts)


def propose_and_apply(*, plan: Dict[str, Any], graph: Any, llm: Any) -> str:
    context = _render_context(plan)
    prompt = plan.get("objective", "")
    diff = llm.generate_diff(prompt=prompt, context=context)
    ok, msg = apply_diff_unified(diff, repo_root=os.path.abspath("./repo"))
    if not ok:
        # If apply failed, return the diff for inspection; verifiers will fail
        return diff
    return diff


