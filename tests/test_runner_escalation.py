"""Tests for runner test escalation."""


def test_runner_escalation(monkeypatch):
    # Simulate plan returns some test patterns and verify escalation calls happen
    calls = {"runs": []}

    def fake_plan(task: str, graph):
        return {"objective": task, "tests_to_run": ["unit_only"]}

    def fake_impacted(diff, graph):
        # simulate one impacted module
        return [], ["modA"]

    def fake_run_tests(select_patterns=None, nodeids=None):
        # First call: with nodeids -> fail
        calls["runs"].append((tuple(select_patterns or []), tuple(nodeids or [])))
        if nodeids is not None:
            return False
        # Second call: with patterns only -> pass
        if select_patterns == ["unit_only"] and nodeids is None:
            return True
        return True

    def fake_propose_and_apply(**kwargs):
        return "diff --git a/x b/x\n--- a/x\n+++ b/x\n@@ -1 +1 @@\n-a\n+b\n"

    monkeypatch.setenv("PER_STEP_SECONDS", "5")
    monkeypatch.setenv("COV_FAIL_UNDER", "0")
    import runner as runner_mod

    # Stub CodeGraph to provide pytest nodeids for impacted module
    class StubGraph:
        def __init__(self):
            self.pytest_nodes_by_module = {"modA": ["tests/test_x.py::test_y"]}

    class StubCG:
        @classmethod
        def load_or_build(cls, root):
            return StubGraph()

    monkeypatch.setattr(runner_mod, "CodeGraph", StubCG)

    monkeypatch.setattr(runner_mod, "plan", fake_plan)
    monkeypatch.setattr(runner_mod, "impacted_from_diff", fake_impacted)
    monkeypatch.setattr(runner_mod, "run_tests", fake_run_tests)
    monkeypatch.setattr(runner_mod, "propose_and_apply", fake_propose_and_apply)
    monkeypatch.setattr(runner_mod, "run_static", lambda: True)
    monkeypatch.setattr(runner_mod, "run_runtime", lambda: True)
    res = runner_mod.run_task("Test escalation")
    assert res.get("status") == "pass"
    # Ensure we attempted nodeids then patterns (2 calls)
    assert len(calls["runs"]) >= 2
