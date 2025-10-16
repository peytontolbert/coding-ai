import subprocess
from sandbox.docker_runner import run_in_sandbox


def test_sandbox_local_fallback(monkeypatch):
    # Force docker unavailable, but preserve real subprocess.run for fallback
    real_run = subprocess.run

    def fake_run(argv, **kwargs):
        if argv and argv[0] == "docker":

            class R:
                returncode = 1
                stdout = ""
                stderr = ""

            return R()
        return real_run(argv, **kwargs)

    monkeypatch.setattr(subprocess, "run", fake_run)
    rc = run_in_sandbox(["python", "-c", "print('ok')"], mounts=[], env={}, timeout=5)
    assert rc == 0


def test_sandbox_docker_command_build(monkeypatch, tmp_path):
    # Simulate docker available and capture argv
    calls = {"argv": None}

    def fake_run(argv, **kwargs):
        # First call is docker info, second is docker run
        if isinstance(argv, list) and argv[:2] == ["docker", "info"]:

            class R0:
                returncode = 0
                stdout = ""
                stderr = ""

            return R0()
        if isinstance(argv, list) and argv[:2] == ["docker", "run"]:
            calls["argv"] = argv

            class R1:
                returncode = 0
                stdout = ""
                stderr = ""

            return R1()

        # Fallback subprocess for python local exec
        class Rx:
            returncode = 0
            stdout = ""
            stderr = ""

        return Rx()

    monkeypatch.setattr(subprocess, "run", fake_run)
    # Enable sandbox via env by dropping a minimal config next to CWD
    cfg = tmp_path / "configs"
    cfg.mkdir(parents=True, exist_ok=True)
    (cfg / "sandbox.yaml").write_text(
        "enabled: true\nimage: python:3.11-slim\nlimits:\n  cpus: '1'\n  memory: '1g'\n",
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)
    # Run and assert docker args include network none, limits, workdir and env passthrough
    rc = run_in_sandbox(
        ["pytest", "-q"],
        mounts=[{"source": str(tmp_path), "target": "/work"}],
        env={"PYTHONUNBUFFERED": "1", "PER_STEP_SECONDS": "5", "COV_FAIL_UNDER": "80"},
        timeout=5,
        workdir="/work",
    )
    assert rc == 0
    argv = calls["argv"]
    assert argv is not None
    # Basic flags
    assert "--network" in argv and "none" in argv
    assert "--cpus" in argv and "1" in argv
    assert "--memory" in argv and "1g" in argv
    # Working directory flag
    assert "-w" in argv and "/work" in argv
    # Mount
    assert any(arg.startswith("-v") for arg in argv)
    # Env passthrough entries (Docker uses separate args: "-e", "KEY=VAL")
    assert "PER_STEP_SECONDS=5" in argv
    assert "COV_FAIL_UNDER=80" in argv
