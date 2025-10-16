import os
import shutil
import subprocess
import tempfile
from act.actuator import split_unified_diff_by_hunk

from tools.patch_utils import apply_diff_unified


def _has_cmd(name: str) -> bool:
    try:
        return shutil.which(name) is not None
    except Exception:
        return False


def test_apply_diff_unified_changes_file():
    # Skip if neither patch nor git is available
    if not (_has_cmd("patch") or _has_cmd("git")):
        return
    with tempfile.TemporaryDirectory() as td:
        repo = td
        path = os.path.join(repo, "a.txt")
        with open(path, "w", encoding="utf-8") as f:
            f.write("hello\n")
        # If using git fallback, initialize a repo so git apply works
        if (not _has_cmd("patch")) and _has_cmd("git"):
            subprocess.run(
                ["git", "init"],
                cwd=repo,
                check=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
        diff = "--- a.txt\n" "+++ a.txt\n" "@@ -1 +1 @@\n" "-hello\n" "+world\n"
        ok, msg = apply_diff_unified(diff, repo)
        assert ok, f"apply failed: {msg}"
        with open(path, "r", encoding="utf-8") as f:
            assert f.read() == "world\n"


def test_split_unified_diff_by_hunk_splits_correctly():
    diff = (
        "diff --git a/a.txt b/a.txt\n"
        "--- a/a.txt\n"
        "+++ b/a.txt\n"
        "@@ -1 +1 @@\n"
        "-hello\n"
        "+world\n"
        "@@ -2 +2 @@\n"
        "-foo\n"
        "+bar\n"
        "diff --git a/b.py b/b.py\n"
        "--- a/b.py\n"
        "+++ b/b.py\n"
        "@@ -1,2 +1,2 @@\n"
        "-print(1)\n"
        "+print(2)\n"
    )
    hunks = split_unified_diff_by_hunk(diff)
    assert len(hunks) == 3
    assert any("a.txt" in h for h in hunks)
    assert any("b.py" in h for h in hunks)
