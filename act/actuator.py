from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import time as _time
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple


def _has_cmd(name: str) -> bool:
    try:
        return shutil.which(name) is not None
    except Exception:
        return False


def _now_ts() -> str:
    return _time.strftime("%Y%m%dT%H%M%S", _time.gmtime())


def split_unified_diff_by_hunk(diff_text: str) -> List[str]:
    """
    Split a unified diff into per-hunk mini-diffs, preserving file headers.

    Strategy:
    - Partition by file (lines between consecutive "diff --git" blocks)
    - Within each file block, split on lines starting with "@@"
    - For each hunk, include the file headers (diff --git, ---/+++) and the hunk body
    """
    lines = diff_text.splitlines()
    hunks: List[str] = []
    i = 0
    while i < len(lines):
        # Find start of a file block
        if not lines[i].startswith("diff --git "):
            i += 1
            continue
        file_header_start = i
        # Collect until next file block or end
        j = i + 1
        while j < len(lines) and not lines[j].startswith("diff --git "):
            j += 1
        file_block = lines[file_header_start:j]
        # Extract file headers and all hunk starts
        # Ensure we have --- and +++ present
        hdr_1 = None
        hdr_2 = None
        for k, ln in enumerate(file_block):
            if ln.startswith("--- ") and hdr_1 is None:
                hdr_1 = k
            elif ln.startswith("+++ ") and hdr_2 is None:
                hdr_2 = k
            if hdr_1 is not None and hdr_2 is not None:
                break
        if hdr_1 is None or hdr_2 is None:
            # Not a standard unified file block; emit whole block as one hunk
            hunks.append("\n".join(file_block))
        else:
            # Identify hunk boundaries within this file block
            # Hunks start with @@
            # Keep the block header prefix up to +++ (inclusive)
            prefix = file_block[: (hdr_2 + 1)]
            # Find all hunk start indices
            h_starts: List[int] = []
            for idx in range(hdr_2 + 1, len(file_block)):
                if (
                    file_block[idx].startswith("@@ ")
                    or file_block[idx].startswith("@@-")
                    or file_block[idx].startswith("@@+")
                ):
                    h_starts.append(idx)
            if not h_starts:
                hunks.append("\n".join(file_block))
            else:
                h_starts.append(len(file_block))
                for a, b in zip(h_starts[:-1], h_starts[1:]):
                    body = file_block[a:b]
                    mini = prefix + body
                    hunks.append("\n".join(mini))
        i = j
    return hunks


@dataclass
class ApplyResult:
    ok: bool
    total_hunks: int
    applied_hunks: int
    refined_diff: str
    logs_dir: str
    stdout: str = ""
    stderr: str = ""


class Actuator:
    """
    Safe patch actuator:
    - Tries three-way merge in a temp clone
    - Auto-splits reject hunks and applies those that succeed
    - Produces a refined diff and writes artifacts into logs/
    - Applies the refined diff to the original repo if possible
    """

    def __init__(self, logs_root: str | None = None) -> None:
        self.logs_root = logs_root or os.path.join(os.getcwd(), "logs")

    def _ensure_logs_dir(self) -> str:
        out = Path(self.logs_root) / "actuator" / _now_ts()
        out.mkdir(parents=True, exist_ok=True)
        return str(out)

    def _write(self, path: Path, content: str) -> None:
        try:
            path.write_text(content, encoding="utf-8")
        except Exception:
            pass

    def _git(self, cwd: str, args: List[str]) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["git", *args],
            cwd=cwd,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

    def _temp_clone(self, repo_root: str) -> Optional[str]:
        if not _has_cmd("git"):
            return None
        try:
            temp_dir = tempfile.mkdtemp(prefix="ai_act_")
            # Local clone with shared objects disabled to avoid side-effects
            cp = subprocess.run(
                ["git", "clone", "--no-hardlinks", "--local", repo_root, temp_dir],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            if cp.returncode != 0:
                shutil.rmtree(temp_dir, ignore_errors=True)
                return None
            return temp_dir
        except Exception:
            return None

    def _apply_once(
        self, repo_dir: str, patch_path: str, three_way: bool
    ) -> Tuple[bool, str, str]:
        if three_way:
            p = self._git(repo_dir, ["apply", "--3way", patch_path])
            if p.returncode == 0:
                return True, p.stdout, p.stderr
            # Fallback to direct apply with rejects
            p2 = self._git(repo_dir, ["apply", "--reject", patch_path])
            return p2.returncode == 0, p2.stdout, p2.stderr
        p = self._git(repo_dir, ["apply", "--reject", patch_path])
        return p.returncode == 0, p.stdout, p.stderr

    def _apply_refined_to_original(
        self, original_repo: str, refined_diff: str
    ) -> Tuple[bool, str]:
        if not refined_diff.strip():
            return False, "refined diff empty"
        if _has_cmd("git"):
            tmp = None
            try:
                fd, tmp = tempfile.mkstemp(prefix="refined_", suffix=".patch")
                os.write(fd, refined_diff.encode("utf-8"))
                os.close(fd)
                p = self._git(original_repo, ["apply", "--reject", tmp])
                return p.returncode == 0, (p.stdout or p.stderr)
            except Exception as e:
                return False, str(e)
            finally:
                if tmp:
                    try:
                        os.unlink(tmp)
                    except Exception:
                        pass
        # Fallback: best-effort write fails
        return False, "git not available"

    def apply_in_temp(
        self, repo_root: str, diff_text: str, *, prefer_three_way: bool = True
    ) -> ApplyResult:
        logs_dir = Path(self._ensure_logs_dir())
        self._write(logs_dir / "input.diff", diff_text)

        clone_dir = self._temp_clone(repo_root)
        if clone_dir is None:
            # No git available; cannot three-way. Try direct apply to original via git/patch fallback.
            # Defer to refined-apply workflow with single hunk splitting, but operate in-place clone==repo.
            clone_dir = repo_root

        # First attempt: apply entire diff with three-way if possible
        patch_path = str(logs_dir / "candidate.patch")
        self._write(Path(patch_path), diff_text)
        # Try a single three-way attempt without fallback to avoid partial application
        out = ""
        err = ""
        ok = False
        if prefer_three_way and _has_cmd("git"):
            p_try = self._git(clone_dir, ["apply", "--3way", patch_path])
            ok = p_try.returncode == 0
            out, err = p_try.stdout, p_try.stderr
        if ok:
            # Capture refined diff between original tree and temp clone
            refined = self._collect_refined_diff(clone_dir)
            self._write(logs_dir / "refined.diff", refined)
            # Apply refined to original if clone was used
            if clone_dir != repo_root:
                self._apply_refined_to_original(repo_root, refined)
            return ApplyResult(
                True, 1, 1, refined, str(logs_dir), stdout=out, stderr=err
            )

        # If failed, split into hunks and try to apply each one independently
        hunks = split_unified_diff_by_hunk(diff_text)
        applied = 0
        applied_chunks: List[str] = []
        for idx, hunk in enumerate(hunks):
            hp = str(logs_dir / f"hunk_{idx+1}.patch")
            # Ensure trailing newline for patch parser robustness
            if not hunk.endswith("\n"):
                hunk = hunk + "\n"
            self._write(Path(hp), hunk)
            # Detect target file for delta check
            target_file: Optional[str] = None
            for ln in hunk.splitlines():
                if ln.startswith("+++ "):
                    # format: +++ a/path or +++ b/path
                    try:
                        part = ln.split(" ", 1)[1].strip()
                        if part.startswith("a/") or part.startswith("b/"):
                            target_file = part[2:]
                        else:
                            target_file = part
                    except Exception:
                        target_file = None
                    break
            before = None
            if target_file:
                try:
                    before = (Path(clone_dir) / target_file).read_text(encoding="utf-8")
                except Exception:
                    before = None
            # Deterministic per-hunk: avoid 3-way here, prefer --reject
            hok, hout, herr = self._apply_once(clone_dir, hp, three_way=False)
            after_changed = False
            if target_file:
                try:
                    after = (Path(clone_dir) / target_file).read_text(encoding="utf-8")
                    after_changed = (before is not None) and (after != before)
                except Exception:
                    after_changed = False
            if hok or after_changed:
                applied += 1
                applied_chunks.append(hunk)
            else:
                # Save reject stderr for diagnosis
                self._write(
                    logs_dir / f"hunk_{idx+1}.reject.txt",
                    (hout or "") + ("\n" + herr if herr else ""),
                )

        refined = self._collect_refined_diff(clone_dir)
        if (not refined.strip()) and applied_chunks:
            # Fallback: emit concatenated applied hunks as refined diff
            refined = "".join(applied_chunks)
        self._write(logs_dir / "refined.diff", refined)
        if applied > 0 and clone_dir != repo_root:
            self._apply_refined_to_original(repo_root, refined)

        return ApplyResult(
            applied > 0,
            len(hunks),
            applied,
            refined,
            str(logs_dir),
            stdout=out,
            stderr=err,
        )

    def _collect_refined_diff(self, repo_dir: str) -> str:
        if not _has_cmd("git"):
            return ""
        p = self._git(repo_dir, ["diff"])
        if p.returncode == 0:
            return p.stdout
        return ""
