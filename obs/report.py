from __future__ import annotations

import argparse
import html
import json
import os
from typing import Any, Dict, Iterable, List


def _read_json_lines(path: str) -> Iterable[Dict[str, Any]]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    yield json.loads(line)
                except Exception:
                    continue
    except Exception:
        return []


def _load_static_summary(path: str) -> Dict[str, Any]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"ok": None, "gates": []}


def generate_html_report(logs_dir: str) -> str:
    os.makedirs(logs_dir, exist_ok=True)
    run_log = os.path.join(logs_dir, "run.jsonl")
    static_summary_path = os.path.join(logs_dir, "static_summary.json")
    out_path = os.path.join(logs_dir, "report.html")

    events: List[Dict[str, Any]] = list(_read_json_lines(run_log))
    static_summary: Dict[str, Any] = _load_static_summary(static_summary_path)

    # Build simple HTML
    parts: List[str] = []
    parts.append("<!doctype html><html><head><meta charset='utf-8'><title>Run Report</title>")
    parts.append(
        "<style>body{font-family:system-ui,Arial,sans-serif;margin:20px;}table{border-collapse:collapse;}td,th{border:1px solid #ddd;padding:6px;} .ok{color:#0a0;} .fail{color:#a00;} code{background:#f6f8fa;padding:2px 4px;border-radius:4px;}</style>"
    )
    parts.append("</head><body>")
    parts.append("<h1>AI Runner Report</h1>")

    # Steps timeline
    parts.append("<h2>Steps</h2>")
    parts.append("<table><thead><tr><th>Type</th><th>Name</th><th>Duration (s)</th><th>Status</th></tr></thead><tbody>")
    for ev in events:
        if ev.get("type") not in ("step_start", "step_end"):
            continue
        if ev.get("type") == "step_end":
            name = html.escape(str(ev.get("name", "")))
            dur = ev.get("duration_s")
            ok = bool(ev.get("ok", False))
            cls = "ok" if ok else "fail"
            parts.append(
                f"<tr><td>step</td><td>{name}</td><td>{html.escape(str(dur))}</td><td class='{cls}'>" + ("ok" if ok else "fail") + "</td></tr>"
            )
    parts.append("</tbody></table>")

    # Static gates
    parts.append("<h2>Static Checks</h2>")
    gates = static_summary.get("gates", []) or []
    if not gates:
        parts.append("<p>No static summary available.</p>")
    else:
        parts.append("<table><thead><tr><th>Gate</th><th>Command</th><th>Status</th><th>Log</th></tr></thead><tbody>")
        for g in gates:
            name = html.escape(str(g.get("name", "")))
            cmd = " ".join(map(str, g.get("cmd", [])))
            cmd = html.escape(cmd)
            ok = bool(g.get("ok", False))
            cls = "ok" if ok else "fail"
            log_file = html.escape(str(g.get("log_file", "")))
            parts.append(
                f"<tr><td>{name}</td><td><code>{cmd}</code></td><td class='{cls}'>" + ("ok" if ok else "fail") + f"</td><td>{log_file}</td></tr>"
            )
        parts.append("</tbody></table>")

    parts.append("</body></html>")
    html_text = "".join(parts)
    try:
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(html_text)
    except Exception:
        pass
    return out_path


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Generate HTML run report")
    p.add_argument("--logs", default=os.path.join(os.getcwd(), "logs"))
    return p.parse_args()


def main() -> None:
    args = _parse_args()
    generate_html_report(args.logs)


if __name__ == "__main__":
    main()


