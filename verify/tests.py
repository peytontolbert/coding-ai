import os as _os
import subprocess
from typing import List, Optional
import os


def run_tests(select_patterns: Optional[List[str]] = None, *, nodeids: Optional[List[str]] = None) -> bool:
    # Save junit xml to logs/ and coverage xml for later gating
    junit_path = "logs/junit.xml"
    try:
        os.makedirs(os.path.dirname(junit_path), exist_ok=True)
    except Exception:
        pass
    args = [
        "pytest",
        "-q",
        "--maxfail=1",
        f"--junitxml={junit_path}",
        "--cov=.",
        "--cov-report=xml:logs/coverage.xml",
        "-o",
        "junit_family=xunit2",
    ]
    # Optional coverage threshold via env (percent integer)
    try:
        cov_under = int(_os.environ.get("COV_FAIL_UNDER", "0") or 0)
        if cov_under > 0:
            args.extend(["--cov-fail-under", str(cov_under)])
    except Exception:
        pass
    # If explicit nodeids are provided, pass them as positional args
    if nodeids:
        args.extend(list(nodeids))
    if (not nodeids) and select_patterns:
        for pat in select_patterns:
            args.extend(["-k", pat])
    try:
        timeout = None
        try:
            timeout = int(_os.environ.get("PER_STEP_SECONDS", "0") or 0) or None
        except Exception:
            timeout = None
        res = subprocess.run(
            args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout,
        )
        return res.returncode == 0
    except Exception:
        return False
