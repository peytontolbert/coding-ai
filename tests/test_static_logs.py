import json
from pathlib import Path


def test_static_writes_logs_and_fails_on_lint(monkeypatch, tmp_path):
    # Run within a temp directory to isolate logs
    monkeypatch.chdir(tmp_path)

    import verify.static as static_mod

    # Pretend the tools are installed
    monkeypatch.setattr(static_mod.shutil, "which", lambda cmd: f"/usr/bin/{cmd}")

    def fake_run_in_sandbox(cmd, **kwargs):  # type: ignore[no-redef]
        out = kwargs.get("capture_stdout_file")
        err = kwargs.get("capture_stderr_file")
        if out:
            Path(out).parent.mkdir(parents=True, exist_ok=True)
        if err:
            Path(err).parent.mkdir(parents=True, exist_ok=True)
        # Simulate failures for ruff, success for mypy
        if cmd[:2] == ["ruff", "check"]:
            if out:
                Path(out).write_text("E999 syntax error", encoding="utf-8")
            if err:
                Path(err).write_text("", encoding="utf-8")
            return 1
        if cmd[:2] == ["ruff", "format"]:
            if out:
                Path(out).write_text("would reformat bad.py", encoding="utf-8")
            return 1
        if cmd[0] == "mypy":
            if out:
                Path(out).write_text("Success: no issues found", encoding="utf-8")
            return 0
        return 0

    # Ensure our static runner uses the fake sandbox executor
    monkeypatch.setattr(static_mod, "run_in_sandbox", fake_run_in_sandbox)

    ok = static_mod.run_static()
    assert ok is False

    logs_dir = tmp_path / "logs"
    assert (logs_dir / "static_ruff_check.txt").exists()
    assert (logs_dir / "static_ruff_format.txt").exists()
    assert (logs_dir / "static_mypy.txt").exists()

    summary = json.loads((logs_dir / "static_summary.json").read_text(encoding="utf-8"))
    assert summary["ok"] is False
    # Ensure ruff gate reported failure in summary
    by_name = {item["name"]: item for item in summary["gates"]}
    assert by_name["ruff_check"]["ok"] is False
    assert by_name["ruff_format"]["ok"] is False
    assert by_name["mypy"]["ok"] is True


