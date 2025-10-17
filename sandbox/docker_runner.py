from typing import List, Dict, Optional
import os
import subprocess
from pathlib import Path


def run_in_sandbox(
    cmd: List[str],
    *,
    mounts: List[Dict[str, str]] | None = None,
    env: Dict[str, str] | None = None,
    timeout: int | None = None,
    workdir: Optional[str] = None,
    capture_stdout_file: Optional[str] = None,
    capture_stderr_file: Optional[str] = None,
) -> int:
    # Read sandbox config
    cfg_path = Path(os.getcwd()) / "configs" / "sandbox.yaml"
    image = "python:3.11-slim"
    limits: Dict[str, str] = {"cpus": "2", "memory": "4g"}
    enabled = False
    default_mounts: List[Dict[str, str]] = list(mounts) if mounts else []
    try:
        import yaml  # type: ignore

        if cfg_path.exists():
            data = yaml.safe_load(cfg_path.read_text(encoding="utf-8")) or {}
            enabled = bool(data.get("enabled", False))
            image = str(data.get("image", image))
            ld = data.get("limits", limits) or limits
            # coerce to str->str map
            limits = {str(k): str(v) for k, v in (ld or {}).items()}
            for m in data.get("mounts", []) or []:
                if isinstance(m, dict):
                    s = m.get("source")
                    t = m.get("target")
                    if isinstance(s, str) and isinstance(t, str) and s and t:
                        default_mounts.append({"source": s, "target": t})
    except Exception:
        pass

    docker_ok = False
    try:
        docker_ok = (
            subprocess.run(
                ["docker", "info"], stdout=subprocess.PIPE, stderr=subprocess.PIPE
            ).returncode
            == 0
        )
    except Exception:
        docker_ok = False

    if docker_ok and enabled:
        argv = [
            "docker",
            "run",
            "--rm",
            "--network",
            "none",
        ]
        # CPU/RAM caps
        if limits.get("cpus"):
            argv += ["--cpus", str(limits.get("cpus"))]
        if limits.get("memory"):
            argv += ["--memory", str(limits.get("memory"))]
        # Mounts
        for m in default_mounts:
            s = m.get("source")
            t = m.get("target")
            if s and t:
                argv += ["-v", f"{os.path.abspath(s)}:{t}"]
        # Working directory inside container
        if workdir:
            argv += ["-w", workdir]
        # Env
        merged_env: Dict[str, str] = dict(os.environ)
        if env:
            merged_env.update(env)
        # Always pass through a safe subset of env vars
        for k, v in merged_env.items():
            if (
                k
                and v is not None
                and k
                in (
                    "PYTHONDONTWRITEBYTECODE",
                    "PYTHONUNBUFFERED",
                    "PATH",
                    "PER_STEP_SECONDS",
                    "COV_FAIL_UNDER",
                )
            ):
                argv += ["-e", f"{k}={v}"]
        argv += [image] + cmd
        try:
            p = subprocess.run(
                argv,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=timeout or None,
            )
            # Optionally persist outputs for callers that need logs
            try:
                if capture_stdout_file is not None:
                    os.makedirs(os.path.dirname(capture_stdout_file) or ".", exist_ok=True)
                    with open(capture_stdout_file, "w", encoding="utf-8") as f_out:
                        f_out.write(p.stdout or "")
                if capture_stderr_file is not None:
                    os.makedirs(os.path.dirname(capture_stderr_file) or ".", exist_ok=True)
                    with open(capture_stderr_file, "w", encoding="utf-8") as f_err:
                        f_err.write(p.stderr or "")
            except Exception:
                # Best-effort logging; ignore failures
                pass
            return int(p.returncode)
        except Exception:
            return 1

    # Local fallback
    try:
        if capture_stdout_file is not None or capture_stderr_file is not None:
            p = subprocess.run(
                cmd,
                env={**os.environ, **(env or {})},
                timeout=timeout or None,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            try:
                if capture_stdout_file is not None:
                    os.makedirs(os.path.dirname(capture_stdout_file) or ".", exist_ok=True)
                    with open(capture_stdout_file, "w", encoding="utf-8") as f_out:
                        f_out.write(p.stdout or "")
                if capture_stderr_file is not None:
                    os.makedirs(os.path.dirname(capture_stderr_file) or ".", exist_ok=True)
                    with open(capture_stderr_file, "w", encoding="utf-8") as f_err:
                        f_err.write(p.stderr or "")
            except Exception:
                pass
            return int(p.returncode)
        # No capture requested; run as before
        res = subprocess.run(
            cmd, env={**os.environ, **(env or {})}, timeout=timeout or None
        )
        return int(res.returncode)
    except Exception:
        return 1
