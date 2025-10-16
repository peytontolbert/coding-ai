import os
import subprocess
from typing import List


def run_tests(select_patterns: List[str] | None = None) -> bool:
    args = ["pytest", "-q", "--maxfail=1"]
    if select_patterns:
        for pat in select_patterns:
            args.extend(["-k", pat])
    try:
        res = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return res.returncode == 0
    except Exception:
        return False


