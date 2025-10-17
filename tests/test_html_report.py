import json
from pathlib import Path


def test_generate_html_report(monkeypatch, tmp_path):
    logs = tmp_path / "logs"
    logs.mkdir(parents=True, exist_ok=True)

    # write a minimal run.jsonl
    run = logs / "run.jsonl"
    run.write_text(
        "\n".join(
            [
                json.dumps({"type": "step_start", "name": "static"}),
                json.dumps({"type": "step_end", "name": "static", "duration_s": 1.23, "ok": True}),
            ]
        ),
        encoding="utf-8",
    )

    # write static summary
    summary = logs / "static_summary.json"
    summary.write_text(
        json.dumps(
            {
                "ok": True,
                "gates": [
                    {
                        "name": "ruff_check",
                        "cmd": ["ruff", "check", "."],
                        "ok": True,
                        "log_file": str(logs / "static_ruff_check.txt"),
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    import obs.report as report_mod

    out = report_mod.generate_html_report(str(logs))
    assert out.endswith("report.html")
    html_text = Path(out).read_text(encoding="utf-8")
    assert "AI Runner Report" in html_text
    assert "ruff_check" in html_text
    assert "static" in html_text


