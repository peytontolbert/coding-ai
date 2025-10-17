from pathlib import Path


def test_runner_writes_junit_and_coverage(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)

    # Create a tiny repo with one test to get coverage XML produced
    (tmp_path / "repo").mkdir(parents=True, exist_ok=True)
    (tmp_path / "repo" / "__init__.py").write_text("", encoding="utf-8")
    (tmp_path / "repo" / "mod.py").write_text("def add(a,b):\n    return a+b\n", encoding="utf-8")
    tests_dir = tmp_path / "repo" / "tests"
    tests_dir.mkdir(parents=True, exist_ok=True)
    (tests_dir / "test_mod.py").write_text(
        "from repo.mod import add\n\n\ndef test_add():\n    assert add(1,2) == 3\n",
        encoding="utf-8",
    )

    import runner as runner_mod

    # Make the pipeline fast
    monkeypatch.setattr(runner_mod, "PER_STEP_SECONDS", 5, raising=False)
    monkeypatch.setattr(runner_mod, "run_static", lambda: True)
    monkeypatch.setattr(runner_mod, "run_runtime", lambda: True)

    class StubGraph:
        def __init__(self):
            self.pytest_nodes_by_module = {}

    class StubCG:
        @classmethod
        def load_or_build(cls, root):
            return StubGraph()

    class StubLLM:
        def __init__(self, *args, **kwargs):
            pass

    def fake_propose_and_apply(**kwargs):
        return ""  # no changes

    monkeypatch.setattr(runner_mod, "CodeGraph", StubCG)
    monkeypatch.setattr(runner_mod, "LLMClient", lambda: StubLLM())
    monkeypatch.setattr(runner_mod, "propose_and_apply", fake_propose_and_apply)

    res = runner_mod.run_task("Run tests with coverage & junit")
    assert res.get("status") in ("pass", "fail")

    junit = tmp_path / "logs" / "junit.xml"
    cov = tmp_path / "logs" / "coverage.xml"
    assert junit.exists()
    assert cov.exists()


def test_coverage_threshold_env(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "repo").mkdir(parents=True, exist_ok=True)
    (tmp_path / "repo" / "__init__.py").write_text("", encoding="utf-8")
    (tmp_path / "repo" / "mod.py").write_text("def f():\n    return 1\n", encoding="utf-8")
    tests_dir = tmp_path / "repo" / "tests"
    tests_dir.mkdir(parents=True, exist_ok=True)
    (tests_dir / "test_mod.py").write_text(
        "def test_dummy():\n    assert True\n",
        encoding="utf-8",
    )

    import runner as runner_mod

    # Set a very high threshold to force failure
    monkeypatch.setenv("COV_FAIL_UNDER", "99")
    monkeypatch.setattr(runner_mod, "run_static", lambda: True)
    monkeypatch.setattr(runner_mod, "run_runtime", lambda: True)

    class StubGraph:
        def __init__(self):
            self.pytest_nodes_by_module = {}

    class StubCG:
        @classmethod
        def load_or_build(cls, root):
            return StubGraph()

    class StubLLM:
        def __init__(self, *args, **kwargs):
            pass

    def fake_propose_and_apply(**kwargs):
        return ""  # no changes

    monkeypatch.setattr(runner_mod, "CodeGraph", StubCG)
    monkeypatch.setattr(runner_mod, "LLMClient", lambda: StubLLM())
    monkeypatch.setattr(runner_mod, "propose_and_apply", fake_propose_and_apply)

    res = runner_mod.run_task("Force low coverage fail")
    # Expect fail due to coverage threshold
    assert res.get("status") == "fail"


