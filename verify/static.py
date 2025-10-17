import subprocess
import shutil
from typing import List, Dict, Any
import os
import json
from sandbox.docker_runner import run_in_sandbox


def _exec_with_capture(cmd: List[str], *, stdout_file: str, stderr_file: str) -> int:
    """Execute command in sandbox if available, capturing outputs to files.

    Always attempts to persist stdout/stderr for later inspection.
    Returns the process return code.
    """
    try:
        timeout = None
        try:
            timeout = int(os.environ.get("PER_STEP_SECONDS", "0") or 0) or None
        except Exception:
            timeout = None
        rc = run_in_sandbox(
            cmd,
            mounts=[{"source": os.getcwd(), "target": "/work"}],
            env={},
            timeout=timeout or None,
            workdir="/work",
            capture_stdout_file=stdout_file,
            capture_stderr_file=stderr_file,
        )
        return int(rc)
    except Exception:
        # Local fallback with capture
        try:
            p = subprocess.run(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
            )
            try:
                os.makedirs(os.path.dirname(stdout_file) or ".", exist_ok=True)
                with open(stdout_file, "w", encoding="utf-8") as f_out:
                    f_out.write(p.stdout or "")
                with open(stderr_file, "w", encoding="utf-8") as f_err:
                    f_err.write(p.stderr or "")
            except Exception:
                pass
            return int(p.returncode)
        except Exception:
            # Best-effort: ensure empty files exist
            try:
                os.makedirs(os.path.dirname(stdout_file) or ".", exist_ok=True)
                open(stdout_file, "a", encoding="utf-8").close()
                open(stderr_file, "a", encoding="utf-8").close()
            except Exception:
                pass
            return 1


def run_static() -> bool:
    # Run common gates and save outputs to logs/
    logs_dir = os.path.join(os.getcwd(), "logs")
    os.makedirs(logs_dir, exist_ok=True)
    results: List[Dict[str, Any]] = []
    ok = True

    gates = [
        {
            "name": "ruff_check",
            "cmd": ["ruff", "check", "."],
            "outfile": os.path.join(logs_dir, "static_ruff_check.txt"),
        },
        {
            "name": "ruff_format",
            "cmd": ["ruff", "format", "--check", "."],
            "outfile": os.path.join(logs_dir, "static_ruff_format.txt"),
        },
        {
            # Rely on mypy.ini 'files' to scope targets
            "name": "mypy",
            "cmd": ["mypy", "--strict"],
            "outfile": os.path.join(logs_dir, "static_mypy.txt"),
        },
    ]

    for gate in gates:
        cmd = gate["cmd"]
        name = gate["name"]
        outfile = gate["outfile"]
        item: Dict[str, Any] = {"name": name, "cmd": cmd, "log_file": outfile}
        if shutil.which(cmd[0]) is None:
            item["skipped"] = True
            item["ok"] = True
            results.append(item)
            continue
        try:
            tmp_out = outfile + ".out"
            tmp_err = outfile + ".err"
            rc = _exec_with_capture(cmd, stdout_file=tmp_out, stderr_file=tmp_err)
            # Merge stdout/stderr into a single human-friendly log
            try:
                with open(outfile, "w", encoding="utf-8") as f_all:
                    if os.path.exists(tmp_out):
                        f_all.write(open(tmp_out, "r", encoding="utf-8").read())
                    if os.path.exists(tmp_err):
                        err = open(tmp_err, "r", encoding="utf-8").read()
                        if err.strip():
                            f_all.write("\n[stderr]\n")
                            f_all.write(err)
            except Exception:
                pass
            finally:
                try:
                    if os.path.exists(tmp_out):
                        os.remove(tmp_out)
                    if os.path.exists(tmp_err):
                        os.remove(tmp_err)
                except Exception:
                    pass
            passed = int(rc) == 0
            item["rc"] = int(rc)
            item["ok"] = bool(passed)
            ok = passed and ok
        except Exception:
            item["rc"] = 1
            item["ok"] = False
            ok = False and ok
        results.append(item)

    # Write summarized report
    summary_path = os.path.join(logs_dir, "static_summary.json")
    try:
        with open(summary_path, "w", encoding="utf-8") as f:
            json.dump({"ok": bool(ok), "gates": results}, f, ensure_ascii=False)
    except Exception:
        pass
    return bool(ok)
