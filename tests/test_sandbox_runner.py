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
