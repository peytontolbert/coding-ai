import os
from memory.lesson_cards import record_lesson, retrieve_lessons


def test_record_and_retrieve_lessons(tmp_path):
    logs = tmp_path / "logs"
    logs.mkdir(parents=True, exist_ok=True)
    # Seed two lessons
    os.chdir(tmp_path)
    record_lesson(
        {
            "objective": "Refactor client retry logic",
            "modules": ["client.network"],
            "files": ["client/network.py"],
            "diff_signature": "diff --git a/x b/x",
            "verifiers": {"tests": True},
        }
    )
    record_lesson(
        {
            "objective": "Fix bug in parser",
            "modules": ["parser.core"],
            "files": ["parser/core.py"],
            "diff_signature": "diff --git a/y b/y",
            "verifiers": {"tests": True},
        }
    )
    # Query overlapping objective and module
    res = retrieve_lessons(
        {"objective": "client retry", "modules": ["client.network"]}, k=5
    )
    assert res, "Expected some lessons returned"
    # Best match should include the client.network entry
    assert any("client.network" in (it.get("modules") or []) for it in res)
