import os
import sys
from tools.code_graph import CodeGraph
from llm_client import LLMClient
from verify.tests import run_tests
from planning.planner import plan
from act.patcher import propose_and_apply
from verify.static import run_static
from verify.tests import run_tests
from verify.runtime import run_runtime
from update.updater import update_memory


class Cfg:
    max_refine_loops = 4


cfg = Cfg()


def run_task(task: str) -> dict:
    graph = CodeGraph.load_or_build("./repo")
    llm = LLMClient()
    state = {"loops": 0}
    while state["loops"] < cfg.max_refine_loops:
        p = plan(task=task, graph=graph)
        diff = propose_and_apply(plan=p, graph=graph, llm=llm)
        static_ok = run_static()
        if not static_ok:
            state["loops"] += 1
            continue
        # Prefer selective tests from plan if available
        try:
            test_patterns = p.get("tests_to_run", []) if isinstance(p.get("tests_to_run", []), list) else []
        except Exception:
            test_patterns = []
        tests_ok = run_tests(test_patterns if test_patterns else None)
        if not tests_ok:
            state["loops"] += 1
            continue
        runtime_ok = run_runtime()
        if not runtime_ok:
            state["loops"] += 1
            continue
        update_memory(plan=p, diff=diff, verifiers={"static": static_ok, "tests": tests_ok, "runtime": runtime_ok})
        return {"status": "pass", "diff": diff}
    return {"status": "fail"}


if __name__ == "__main__":
    task = " ".join(sys.argv[1:]) or os.environ.get("TASK", "Refactor logging; add retry to client")
    res = run_task(task)
    print(res)


