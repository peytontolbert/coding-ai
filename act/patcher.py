from typing import Any, Dict, List
import os
from tools.patch_utils import apply_diff_unified
from act.actuator import Actuator


def _render_context(plan: Dict[str, Any]) -> str:
    parts = [
        f"Objective: {plan.get('objective','')}",
        f"Files: {', '.join(plan.get('files', []) or [])}",
        f"Invariants: {', '.join(plan.get('invariants', []) or [])}",
        f"Tests: {', '.join(plan.get('tests_to_run', []) or [])}",
    ]
    return "\n".join(parts)


def _graph_context(graph: Any, plan: Dict[str, Any]) -> str:
    # Attempt to include defs, callers, and owners for referenced modules/symbols
    lines: List[str] = []
    try:
        # Extract tokens that look like symbols/modules from objective
        tokens: List[str] = []
        for tok in str(plan.get("objective", "")).replace("\n", " ").split():
            t = tok.strip(",.:;()[]{}")
            if t and ("." in t or t.isidentifier()):
                tokens.append(t)
        tokens = list(dict.fromkeys(tokens))
        for t in tokens[:20]:
            try:
                owners = graph.owners_of(t) if hasattr(graph, "owners_of") else []
            except Exception:
                owners = []
            if owners:
                lines.append(f"Owners({t}): {', '.join(owners[:5])}")
            try:
                # If token looks like module path, include defs
                if hasattr(graph, "defs_in") and "." in t:
                    defs = graph.defs_in(t)[:10]
                    if defs:
                        lines.append(f"Defs({t}): {', '.join(defs)}")
                        # Include callers of first few defs
                        for fqn in defs[:3]:
                            try:
                                callers = (
                                    graph.who_calls(fqn)
                                    if hasattr(graph, "who_calls")
                                    else []
                                )
                                if callers:
                                    lines.append(
                                        f"WhoCalls({fqn}): {', '.join(callers[:5])}"
                                    )
                            except Exception:
                                pass
            except Exception:
                pass
    except Exception:
        return ""
    return "\n".join(lines)


def propose_and_apply(*, plan: Dict[str, Any], graph: Any, llm: Any) -> str:
    # Compose prompt context with CodeGraph details
    context = _render_context(plan)
    try:
        gctx = _graph_context(graph, plan)
        if gctx:
            context = context + "\n\n" + gctx
    except Exception:
        pass
    prompt = plan.get("objective", "")
    diff = llm.generate_diff(prompt=prompt, context=context)
    repo_root = os.environ.get("CODE_REPO", "./repo")
    # Prefer safe actuator that applies in temp clone with 3-way and hunk splitting
    try:
        actuator = Actuator(logs_root=os.path.join(os.getcwd(), "logs"))
        res = actuator.apply_in_temp(
            os.path.abspath(str(repo_root)), diff, prefer_three_way=True
        )
        # If nothing applied, fall back to naive apply for compatibility
        if not res.ok:
            ok, _ = apply_diff_unified(diff, repo_root=os.path.abspath(str(repo_root)))
            if not ok:
                return diff
        return res.refined_diff if res.refined_diff.strip() else diff
    except Exception:
        ok, _ = apply_diff_unified(diff, repo_root=os.path.abspath(str(repo_root)))
        if not ok:
            return diff
        return diff
