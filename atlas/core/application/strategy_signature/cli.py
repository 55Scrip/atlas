"""Standalone CLI entry point for Strategy Signature Recognition (ATLAS-006).

    python -m atlas.core.application.strategy_signature.cli

Deliberately separate from atlas/cli/main.py and atlas/conversation/ —
same independence discipline as the existing CLIs. Uses the same
shared, neutral database configuration (ATLAS-003). Read-only
throughout: nothing in this file, or anything it calls, ever writes to
any repository.
"""
from __future__ import annotations

from atlas.core.application.strategy_signature.composition import (
    build_strategy_signature_recognition_query,
    create_strategy_signature_tables,
)
from atlas.core.application.strategy_signature.recognized_strategy_signature import (
    RecognizedStrategySignature,
)
from atlas.core.infrastructure.config.database import create_database_engine


def _describe(signature: RecognizedStrategySignature) -> str:
    lines = [f"[{signature.strategy_name}] {signature.description}"]
    for pattern in signature.member_patterns:
        decision_ids = ", ".join(str(decision_id) for decision_id in pattern.member_decision_ids)
        lines.append(f"    Pattern [{pattern.strategy_name}]: {pattern.description}")
        lines.append(f"        Decisions: {decision_ids}")
    return "\n".join(lines)


def run() -> None:
    engine = create_database_engine()
    create_strategy_signature_tables(engine)
    query = build_strategy_signature_recognition_query(engine)
    signatures = query.build()

    if not signatures:
        print("No Strategy Signatures recognized yet. Record more Decisions and try again.")
        return

    print("Recognized Strategy Signatures:")
    for signature in signatures:
        print(f"\n{_describe(signature)}")


if __name__ == "__main__":
    run()
