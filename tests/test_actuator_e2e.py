import os
import tempfile
import subprocess
from pathlib import Path

from act.actuator import Actuator


def _init_git_repo(repo: str) -> None:
    subprocess.run(
        ["git", "init"],
        cwd=repo,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    # Configure identity for commits if needed
    subprocess.run(["git", "config", "user.email", "you@example.com"], cwd=repo)
    subprocess.run(["git", "config", "user.name", "You"], cwd=repo)
    Path(os.path.join(repo, "a.txt")).write_text("hello\nfoo\n", encoding="utf-8")
    subprocess.run(["git", "add", "a.txt"], cwd=repo)
    subprocess.run(["git", "commit", "-m", "init"], cwd=repo)


def test_actuator_apply_hunk_split_e2e():
    with tempfile.TemporaryDirectory() as td:
        _init_git_repo(td)
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
        )
        # Introduce a conflicting change to make one hunk fail
        Path(os.path.join(td, "a.txt")).write_text("hello\nzzz\n", encoding="utf-8")
        actuator = Actuator(logs_root=os.path.join(td, "logs"))
        res = actuator.apply_in_temp(td, diff, prefer_three_way=True)
        assert res.total_hunks == 2
        assert res.applied_hunks >= 1
        # Refined diff should be non-empty when at least one hunk applied
        if res.applied_hunks > 0:
            assert res.refined_diff.strip() != ""
