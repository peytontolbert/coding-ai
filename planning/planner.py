from typing import Any, Dict, List
from tools.code_graph import CodeGraph


def _extract_modules_from_task(task: str) -> List[str]:
    mods: List[str] = []
    # naive heuristic: tokens with dots that look like modules
    for tok in task.replace("\n", " ").split():
        if tok.count(".") >= 1 and all(part.isidentifier() for part in tok.split(".")):
            mods.append(tok.strip(",.:;"))
    return list(dict.fromkeys(mods))  # preserve order, dedup


def _tests_for_modules(graph: Any, modules: List[str]) -> List[str]:
    pats: List[str] = []
    for m in modules:
        try:
            pats.extend(graph.tests_for_module(m))
        except Exception:
            continue
    # fallback: if nothing found, return empty to run full pytest
    return sorted(list(dict.fromkeys(pats)))


def plan(*, task: str, graph: Any) -> Dict[str, Any]:
    mods = _extract_modules_from_task(task)
    # Expand impacted modules via reverse imports
    impacted: List[str] = []
    try:
        if isinstance(graph, CodeGraph):
            # For each mentioned module, include modules that import it (reverse deps)
            rev = set()
            for m in mods:
                for mod, deps in getattr(graph, "module_imports", {}).items():
                    if m in deps or m.split(".")[0] in deps:
                        rev.add(mod)
            impacted = sorted(set(mods) | rev)
        else:
            impacted = mods
    except Exception:
        impacted = mods
    tests = _tests_for_modules(graph, impacted)
    return {
        "objective": task,
        "files": [],
        "invariants": [],
        "tests_to_run": tests,
        "risks": [],
    }
