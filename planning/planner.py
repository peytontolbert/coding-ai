from typing import Any, Dict, List, Tuple
from tools.code_graph import CodeGraph
import os


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
    # Also compute minimal pytest nodeids if graph has mapping
    nodeids: List[str] = []
    try:
        m2n = getattr(graph, "pytest_nodes_by_module", {}) or {}
        for m in impacted:
            for n in m2n.get(m, []):
                nodeids.append(n)
        nodeids = sorted(list(dict.fromkeys(nodeids)))
    except Exception:
        nodeids = []
    return {
        "objective": task,
        "files": [],
        "invariants": [],
        "tests_to_run": tests,
        "nodeids": nodeids,
        "risks": [],
    }


def impacted_from_diff(diff_text: str, graph: CodeGraph) -> Tuple[List[str], List[str]]:
    files: List[str] = []
    for line in diff_text.splitlines():
        if line.startswith("+++ "):
            try:
                part = line.split(" ", 1)[1].strip()
                if part == "/dev/null":
                    continue
                if part.startswith("a/") or part.startswith("b/"):
                    rel = part[2:]
                else:
                    rel = part
                files.append(rel)
            except Exception:
                continue
    modules: List[str] = []
    for f in files:
        try:
            m = graph.module_for_file(os.path.join(graph.root, f))
            if m:
                modules.append(m)
        except Exception:
            continue
    modules = list(dict.fromkeys(modules))
    # Reverse importers
    rev = set()
    for m in modules:
        for mod, deps in getattr(graph, "module_imports", {}).items():
            if m in deps or m.split(".")[0] in deps:
                rev.add(mod)
    impacted = sorted(set(modules) | rev)
    return files, impacted
