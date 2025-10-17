from pathlib import Path


def test_mypy_cache_is_created(monkeypatch, tmp_path):
    # Isolate working directory
    monkeypatch.chdir(tmp_path)

    import verify.static as static_mod

    # Pretend tools exist
    monkeypatch.setattr(static_mod.shutil, "which", lambda cmd: f"/usr/bin/{cmd}")

    def fake_run_in_sandbox(cmd, **kwargs):  # type: ignore[no-redef]
        out = kwargs.get("capture_stdout_file")
        err = kwargs.get("capture_stderr_file")
        if out:
            Path(out).parent.mkdir(parents=True, exist_ok=True)
            Path(out).write_text("ok", encoding="utf-8")
        if err:
            Path(err).parent.mkdir(parents=True, exist_ok=True)
            Path(err).write_text("", encoding="utf-8")
        # Simulate mypy producing its incremental cache
        if cmd and cmd[0] == "mypy":
            (tmp_path / ".mypy_cache").mkdir(parents=True, exist_ok=True)
            return 0
        return 0

    monkeypatch.setattr(static_mod, "run_in_sandbox", fake_run_in_sandbox)

    ok = static_mod.run_static()
    assert ok is True
    assert (tmp_path / ".mypy_cache").exists()


