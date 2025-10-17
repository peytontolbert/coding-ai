from __future__ import annotations

import json
import os
import time
from typing import Any, Dict, Optional


class JsonLogger:
    def __init__(self, *, log_path: Optional[str] = None) -> None:
        base = log_path or os.path.join(os.getcwd(), "logs", "run.jsonl")
        os.makedirs(os.path.dirname(base), exist_ok=True)
        self.path = base

    def emit(self, event: Dict[str, Any]) -> None:
        try:
            event = {**event}
            event.setdefault("ts", time.time())
            with open(self.path, "a", encoding="utf-8") as f:
                f.write(json.dumps(event, ensure_ascii=False) + "\n")
        except Exception:
            return

    def step(self, name: str) -> "StepCtx":
        return StepCtx(self, name)


class StepCtx:
    def __init__(self, logger: JsonLogger, name: str) -> None:
        self.logger = logger
        self.name = name
        self.start_ts: float = 0.0

    def __enter__(self) -> "StepCtx":
        self.start_ts = time.time()
        self.logger.emit({"type": "step_start", "name": self.name})
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        dur = max(0.0, time.time() - self.start_ts)
        self.logger.emit(
            {
                "type": "step_end",
                "name": self.name,
                "duration_s": round(dur, 3),
                "ok": exc is None,
                "error": str(exc) if exc else None,
            }
        )
