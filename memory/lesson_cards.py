from __future__ import annotations

import json
import os
from typing import Dict, Any, List, Tuple


_LESSONS_PATH = os.path.join(os.getcwd(), "logs", "lessons.jsonl")


def _ensure_dir(path: str) -> None:
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
    except Exception:
        pass


def record_lesson(card: Dict[str, Any]) -> None:
    _ensure_dir(_LESSONS_PATH)
    try:
        with open(_LESSONS_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(card, ensure_ascii=False) + "\n")
    except Exception:
        # best-effort; ignore persistence errors
        return None


def _load_all() -> List[Dict[str, Any]]:
    try:
        if not os.path.exists(_LESSONS_PATH):
            return []
        out: List[Dict[str, Any]] = []
        with open(_LESSONS_PATH, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    out.append(json.loads(line))
                except Exception:
                    continue
        return out
    except Exception:
        return []


def _score(query: Dict[str, Any], item: Dict[str, Any]) -> float:
    # Simple ranking: objective token overlap + modules overlap
    q_obj = str(query.get("objective", "")).lower().split()
    i_obj = str(item.get("objective", "")).lower().split()
    obj_overlap = len(set(q_obj) & set(i_obj))
    q_mods = set(query.get("modules", []) or [])
    i_mods = set(item.get("modules", []) or [])
    mod_overlap = len(q_mods & i_mods)
    return float(obj_overlap * 2 + mod_overlap)


def retrieve_lessons(query: Dict[str, Any], k: int = 5) -> List[Dict[str, Any]]:
    items = _load_all()
    scored: List[Tuple[float, Dict[str, Any]]] = [(_score(query, it), it) for it in items]
    scored.sort(key=lambda x: x[0], reverse=True)
    return [it for s, it in scored[: max(0, int(k))] if s > 0.0]
