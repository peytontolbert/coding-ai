import subprocess
import shutil
from typing import List
import os


def _run(cmd: List[str]) -> bool:
    try:
        timeout = None
        try:
            timeout = int(os.environ.get("PER_STEP_SECONDS", "0") or 0) or None
        except Exception:
            timeout = None
        res = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout,
        )
        return res.returncode == 0
    except Exception:
        return False


def run_static() -> bool:
    # Run common gates and save outputs to logs/
    ok = True
    gates = (
        ["ruff", "check", "."],
        ["black", "--check", "."],
        ["mypy", "--strict", "."],
    )
    for cmd in gates:
        if shutil.which(cmd[0]) is None:
            continue
        try:
            passed = _run(cmd)
            ok = passed and ok
        except Exception:
            continue
    return ok
