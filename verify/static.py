import subprocess
from typing import List


def _run(cmd: List[str]) -> bool:
    try:
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return res.returncode == 0
    except Exception:
        return False


def run_static() -> bool:
    # Run common gates; tolerate missing tools by skipping
    ok = True
    for cmd in (["ruff", "check", "."], ["black", "--check", "."], ["mypy", "--strict", "."]):
        try:
            ok = _run(cmd) and ok
        except Exception:
            continue
    return ok


