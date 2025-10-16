from typing import Any, Dict
from memory.lesson_cards import record_lesson


def update_memory(
    *, plan: Dict[str, Any], diff: str, verifiers: Dict[str, Any]
) -> None:
    card = {
        "objective": plan.get("objective"),
        "diff_signature": (diff.splitlines()[0] if diff else ""),
        "verifiers": verifiers,
    }
    record_lesson(card)
    return None
