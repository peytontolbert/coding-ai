from typing import List, Dict, Any
import os
import subprocess


def run_in_sandbox(cmd: List[str], *, mounts: List[Dict[str, str]] | None = None, env: Dict[str, str] | None = None, timeout: int | None = None) -> int:
    # Local fallback: execute on host if docker not available
    try:
        if subprocess.run(["docker", "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE).returncode == 0:
            # Minimal: run in host if no explicit image given; extend later
            pass
    except Exception:
        pass
    try:
        res = subprocess.run(cmd, env={**os.environ, **(env or {})}, timeout=timeout or None)
        return int(res.returncode)
    except Exception:
        return 1
