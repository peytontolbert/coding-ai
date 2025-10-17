from typing import Any, Dict, List


def test_impacted_from_diff_includes_reverse_imports(monkeypatch):
    import planning.planner as planner

    class StubGraph:
        root = "."
        module_imports: Dict[str, List[str]] = {
            "pkg.c": ["a.b"],
            "tests.test_c": ["pkg.c"],
        }

        def module_for_file(self, path: str):
            if path.endswith("a/b.py"):
                return "a.b"
            return None

    diff = """diff --git a/a/b.py b/a/b.py
--- a/a/b.py
+++ b/a/b.py
@@ -1 +1 @@
-x
+y
"""

    files, impacted = planner.impacted_from_diff(diff, StubGraph())  # type: ignore[arg-type]
    assert "a.b" in impacted
    assert "pkg.c" in impacted  # reverse importer included


def test_plan_selects_tests_for_impacted(monkeypatch):
    import planning.planner as planner

    class StubGraph:
        module_imports: Dict[str, List[str]] = {"pkg.c": ["a.b"], "tests.test_c": ["pkg.c"]}

        def tests_for_module(self, module: str) -> List[str]:
            if module in ("pkg.c", "a.b"):
                return ["tests/test_c.py::test_ok"]
            return []

    plan = planner.plan(task="touch pkg.c", graph=StubGraph())
    assert "tests_to_run" in plan
    assert plan["tests_to_run"] == ["tests/test_c.py::test_ok"]


