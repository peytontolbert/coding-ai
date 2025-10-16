import subprocess
from typing import List


def ripgrep(pattern: str, path: str = ".") -> List[str]:
    try:
        out = subprocess.check_output(["rg", "-n", pattern, path], text=True)
        return out.splitlines()
    except Exception:
        return []
