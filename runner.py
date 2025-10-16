import os
import sys
import time
from tools.code_graph import CodeGraph
from llm_client import LLMClient
from planning.planner import plan, impacted_from_diff
from verify.tests import run_tests
from act.patcher import propose_and_apply
from verify.static import run_static
from verify.runtime import run_runtime
from update.updater import update_memory


class Cfg:
    max_refine_loops = 4
    total_seconds = 900
    per_step_seconds = 120
    total_seconds = 900
    per_step_seconds = 120


cfg = Cfg()


def run_task(task: str) -> dict:
    # Load policy if present
    try:
        import yaml  # type: ignore

        p = os.path.join("configs", "policy.yaml")
        if os.path.exists(p):
            data = yaml.safe_load(open(p, "r", encoding="utf-8")) or {}
            budgets = data.get("budgets", {}) or {}
            cfg.total_seconds = int(budgets.get("total_seconds", cfg.total_seconds))
            cfg.max_refine_loops = int(
                budgets.get("max_refine_loops", cfg.max_refine_loops)
            )
            cfg.per_step_seconds = int(
                budgets.get("per_step_seconds", cfg.per_step_seconds)
            )
            merge_policy = data.get("merge_policy", {}) or {}
            cov_req = merge_policy.get("require_coverage")
            if cov_req is not None:
                os.environ["COV_FAIL_UNDER"] = str(int(float(cov_req) * 100))
    except Exception:
        pass
    # Export per-step timeout for verifiers
    os.environ["PER_STEP_SECONDS"] = str(int(cfg.per_step_seconds))

    graph = CodeGraph.load_or_build("./repo")
    llm = LLMClient()
    state = {"loops": 0}
    start = time.time()

    def _time_left() -> float:
        return max(0.0, cfg.total_seconds - (time.time() - start))

    while state["loops"] < cfg.max_refine_loops and _time_left() > 0:
        p = plan(task=task, graph=graph)
        diff = propose_and_apply(plan=p, graph=graph, llm=llm)
        if _time_left() <= 0:
            break
        static_ok = run_static()
        if not static_ok:
            state["loops"] += 1
            continue
        # Prefer selective tests from plan if available
        try:
            test_patterns = (
                p.get("tests_to_run", [])
                if isinstance(p.get("tests_to_run", []), list)
                else []
            )
        except Exception:
            test_patterns = []
        if _time_left() <= 0:
            break
        # Prefer nodeids from CodeGraph when possible using diff
        nodeids = None
        try:
            if isinstance(diff, str) and diff.strip():
                files, impacted = impacted_from_diff(diff, graph)  # type: ignore[arg-type]
                nodes: list[str] = []
                for m in impacted:
                    nodes.extend(graph.pytest_nodes_by_module.get(m, []))
                nodeids = sorted(list(dict.fromkeys(nodes))) if nodes else None
        except Exception:
            nodeids = None
        tests_ok = run_tests(test_patterns if test_patterns else None, nodeids=nodeids)
        if not tests_ok:
            state["loops"] += 1
            continue
        if _time_left() <= 0:
            break
        runtime_ok = run_runtime()
        if not runtime_ok:
            state["loops"] += 1
            continue
        update_memory(
            plan=p,
            diff=diff,
            verifiers={"static": static_ok, "tests": tests_ok, "runtime": runtime_ok},
        )
        return {"status": "pass", "diff": diff}
    return {"status": "fail"}


if __name__ == "__main__":
    task = " ".join(sys.argv[1:]) or os.environ.get(
        "TASK", "Refactor logging; add retry to client"
    )
    res = run_task(task)
    print(res)
