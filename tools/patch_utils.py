from typing import Tuple
import subprocess
import os
import shutil
import tempfile


def _has_cmd(name: str) -> bool:
    try:
        return shutil.which(name) is not None
    except Exception:
        return False


def apply_diff_unified(diff_text: str, repo_root: str) -> Tuple[bool, str]:
    """Apply a unified diff to repo_root using system tools if available.

    Preference order: patch, then git apply. Returns (ok, message).
    """
    repo_root = os.path.abspath(repo_root)
    if not os.path.isdir(repo_root):
        return False, f"repo_root not found: {repo_root}"
    # Try patch
    if _has_cmd("patch"):
        try:
            p = subprocess.run(
                ["patch", "-p0", "-t", "-N", "-r", "-"],
                input=diff_text,
                text=True,
                cwd=repo_root,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            if p.returncode == 0:
                return True, p.stdout
            return False, (p.stderr or p.stdout)
        except Exception as e:
            return False, str(e)
    # Fallback: git apply if available
    if _has_cmd("git"):
        try:
            with tempfile.NamedTemporaryFile("w", delete=False, encoding="utf-8") as tf:
                tf.write(diff_text)
                tf.flush()
                tmp_path = tf.name
            try:
                p = subprocess.run(
                    ["git", "apply", "--reject", "--unsafe-paths", tmp_path],
                    cwd=repo_root,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                )
                if p.returncode == 0:
                    return True, p.stdout
                return False, (p.stderr or p.stdout)
            finally:
                try:
                    os.unlink(tmp_path)
                except Exception:
                    pass
        except Exception as e:
            return False, str(e)
    return False, "no patch/git available to apply diff"
