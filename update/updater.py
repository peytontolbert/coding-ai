from typing import Any, Dict, List
from memory.lesson_cards import record_lesson
from planning.planner import impacted_from_diff
from tools.code_graph import CodeGraph


def update_memory(
    *, plan: Dict[str, Any], diff: str, verifiers: Dict[str, Any]
) -> None:
    modules: List[str] = []
    files: List[str] = []
    try:
        graph = CodeGraph.load_or_build("./repo")
        files, impacted = impacted_from_diff(diff, graph)
        modules = impacted
    except Exception:
        modules = []
    card = {
        "objective": plan.get("objective"),
        "modules": modules,
        "files": files,
        "diff_signature": (diff.splitlines()[0] if diff else ""),
        "verifiers": verifiers,
    }
    record_lesson(card)
    return None
