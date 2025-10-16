import json


def test_runner_writes_observability_logs(monkeypatch, tmp_path):
    # Direct logs into tmp_path/logs/run.jsonl by chdir
    monkeypatch.chdir(tmp_path)
    import runner as runner_mod

    # Make runner steps fast and deterministic
    monkeypatch.setattr(runner_mod, "run_static", lambda: True)
    monkeypatch.setattr(runner_mod, "run_runtime", lambda: True)
    monkeypatch.setenv("PER_STEP_SECONDS", "1")

    # Use trivial CodeGraph and LLM interactions
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

    runner_mod.run_task("No-op")
    log_file = tmp_path / "logs" / "run.jsonl"
    assert log_file.exists()
    lines = log_file.read_text(encoding="utf-8").strip().splitlines()
    assert any(json.loads(line).get("type") == "step_start" for line in lines)
    assert any(json.loads(line).get("type") == "step_end" for line in lines)
