"""Standalone CLI entry point for Pattern Recognition (ATLAS-005).

    python -m atlas.core.application.pattern_recognition.cli

Deliberately separate from atlas/cli/main.py and atlas/conversation/ —
same independence discipline as the First Decision Conversation,
Decision Review, and Decision Timeline CLIs. Uses the same shared,
neutral database configuration (ATLAS-003). Read-only throughout:
nothing in this file, or anything it calls, ever writes to any
repository.
"""
from __future__ import annotations

from atlas.core.application.pattern_recognition.composition import (
    build_pattern_recognition_query,
    create_pattern_recognition_tables,
)
from atlas.core.application.pattern_recognition.recognized_pattern import RecognizedPattern
from atlas.core.infrastructure.config.database import create_database_engine


def _describe(recognized: RecognizedPattern) -> str:
    decision_ids = ", ".join(str(decision_id) for decision_id in recognized.member_decision_ids)
    return f"[{recognized.strategy_name}] {recognized.description}\n    Decisions: {decision_ids}"


def run() -> None:
    engine = create_database_engine()
    create_pattern_recognition_tables(engine)
    query = build_pattern_recognition_query(engine)
    recognized_patterns = query.build()

    if not recognized_patterns:
        print("No Patterns recognized yet. Record more Decisions and try again.")
        return

    print("Recognized Patterns:")
    for recognized in recognized_patterns:
        print(f"\n{_describe(recognized)}")


if __name__ == "__main__":
    run()
