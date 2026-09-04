"""Reasoning persistence, serialization and legacy compatibility.

The canonical analytical rationale must survive storage without loss,
and a row written before it existed must stay honestly distinguishable
from one whose reasoning was genuinely empty. Conflating those two is
how a benchmark ends up reporting that Atlas had no reasoning when in
truth the row simply predates the field.
"""
from __future__ import annotations

from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.pool import StaticPool

from atlas.alpha.investment_decision.models import (
    DecisionAction,
    InvestmentDecision,
)
from atlas.alpha.investment_decision.repository import SqlAlchemyInvestmentDecisionResultRepository
from atlas.analysis_engine.business_contracts import BusinessCategoryStatus
from atlas.analysis_engine.reasoning import (
    LEGACY_RESULT_WITHOUT_REASONING,
    REASONING_SCHEMA_VERSION,
    CanonicalEngine,
    KeyUnknownKind,
    SignalState,
    build_drivers,
    build_key_unknowns,
    build_signal_summary,
    deserialize_reasoning,
    serialize_reasoning,
)
from atlas.analysis_engine.valuation.contracts import ValuationStatus
from atlas.analysis_engine.valuation.support import ValuationSupportStatus

_NOW = datetime(2026, 9, 4, tzinfo=timezone.utc)


class _Reasoning:
    """Minimal stand-in carrying only the fields serialization reads."""

    def __init__(self, **kw):
        self.__dict__.update(kw)


def _reasoning(**overrides):
    signals = dict(
        growth_status=BusinessCategoryStatus.WEAK,
        capital_allocation_status=BusinessCategoryStatus.STRONG,
        valuation_status=ValuationStatus.EXPENSIVE,
        valuation_support_status=ValuationSupportStatus.SUPPORTED,
        has_high_financial_or_valuation_risk=True,
        has_real_risk_evidence=True,
    )
    signals.update(overrides)
    primary, counter = build_drivers(**signals)
    summary = build_signal_summary(**signals)
    return _Reasoning(
        primary_drivers=primary,
        counter_drivers=counter,
        signal_summary=summary,
        key_unknowns=build_key_unknowns(summary),
        what_would_change=(),
        conviction_reasoning=None,
    )


@pytest.fixture
def repository():
    engine = create_engine(
        "sqlite:///:memory:", future=True, poolclass=StaticPool,
        connect_args={"check_same_thread": False})
    from atlas.alpha.investment_decision.table import investment_decision_result_table
    from atlas.core.infrastructure.persistence.shared.schema_sync import sync_table_schema
    sync_table_schema(engine, investment_decision_result_table)
    return SqlAlchemyInvestmentDecisionResultRepository(engine), engine


def _decision(payload):
    return InvestmentDecision(
        case_id="case-1", action=DecisionAction.HOLD, qualifiers=(), supporting_reasons=(),
        blockers=(), change_trigger=None, generated_at=_NOW, reasoning_payload=payload)


class TestSerializationRoundTrip:
    def test_drivers_survive_a_round_trip_without_loss(self):
        payload = serialize_reasoning(_reasoning())
        restored = deserialize_reasoning(payload)
        original = _reasoning()
        assert restored.primary_drivers == original.primary_drivers
        assert restored.counter_drivers == original.counter_drivers

    def test_signal_summary_survives_including_disconnected_engines(self):
        restored = deserialize_reasoning(serialize_reasoning(_reasoning()))
        by_engine = {c.engine: c for c in restored.signal_summary}
        assert set(by_engine) == set(CanonicalEngine)
        assert by_engine[CanonicalEngine.BUSINESS_QUALITY].state is SignalState.NOT_IN_DIRECTION_CONTRACT

    def test_key_unknowns_survive_with_their_kind(self):
        restored = deserialize_reasoning(serialize_reasoning(_reasoning()))
        kinds = {u.engine: u.kind for u in restored.key_unknowns}
        assert kinds[CanonicalEngine.BUSINESS_QUALITY] is KeyUnknownKind.NOT_CONNECTED_TO_DIRECTION

    def test_serialization_is_deterministic(self):
        import json
        blobs = {json.dumps(serialize_reasoning(_reasoning()), sort_keys=True) for _ in range(20)}
        assert len(blobs) == 1

    def test_payload_carries_only_closed_vocabulary_strings(self):
        """A stored row must be readable without importing an engine --
        the property that lets a benchmark score it directly."""
        payload = serialize_reasoning(_reasoning())
        for driver in payload["primaryDrivers"] + payload["counterDrivers"]:
            assert all(isinstance(v, str) for v in driver.values())
        assert payload["schemaVersion"] == REASONING_SCHEMA_VERSION

    def test_no_presentation_text_is_persisted(self):
        """Every persisted string is a closed-vocabulary token, never
        prose: no spaces, no sentence case, nothing translated. UI text
        is derived at the edge from these tokens, so it can change
        without rewriting history."""
        import re
        payload = serialize_reasoning(_reasoning())

        def check(value):
            if isinstance(value, str):
                assert re.fullmatch(r"[a-z0-9_]+", value), value
            elif isinstance(value, dict):
                for v in value.values():
                    check(v)
            elif isinstance(value, list):
                for v in value:
                    check(v)

        check({k: v for k, v in payload.items() if k != "schemaVersion"})


class TestStorage:
    def test_reasoning_survives_upsert_and_read(self, repository):
        repo, _ = repository
        payload = serialize_reasoning(_reasoning())
        repo.upsert(_decision(payload), ticker="MSFT")
        restored = repo.get("case-1")
        assert restored.reasoning_payload == payload
        assert deserialize_reasoning(restored.reasoning_payload).counter_drivers

    def test_a_row_written_without_reasoning_reads_back_as_none(self, repository):
        repo, _ = repository
        repo.upsert(_decision(None), ticker="MSFT")
        assert repo.get("case-1").reasoning_payload is None


class TestLegacyRows:
    def test_a_row_predating_the_field_still_deserializes(self, repository):
        """The exact historical shape: no `reasoning` key at all."""
        repo, engine = repository
        import json
        from atlas.alpha.investment_decision.table import investment_decision_result_table
        legacy = {"caseId": "case-legacy", "action": "hold", "qualifiers": [],
                  "supportingReasons": [], "blockers": [], "changeTrigger": None,
                  "generatedAt": _NOW.isoformat()}
        with engine.begin() as connection:
            connection.execute(investment_decision_result_table.insert().values(
                case_id="case-legacy", ticker="OLD", generated_at=_NOW.isoformat(),
                result_json=json.dumps(legacy)))
        restored = repo.get("case-legacy")
        assert restored.action is DecisionAction.HOLD
        assert restored.reasoning_payload is None

    def test_legacy_is_distinguishable_from_empty_reasoning(self):
        """`None` means the row predates the field. An empty-but-present
        payload means reasoning was computed and found nothing. A
        benchmark must never report the first as the second."""
        assert deserialize_reasoning(None) is None
        computed = deserialize_reasoning(serialize_reasoning(_reasoning(
            growth_status=BusinessCategoryStatus.NOT_EVALUATED,
            capital_allocation_status=BusinessCategoryStatus.NOT_EVALUATED,
            valuation_status=ValuationStatus.NOT_EVALUATED,
            valuation_support_status=ValuationSupportStatus.INSUFFICIENT_INPUT,
            has_high_financial_or_valuation_risk=False,
            has_real_risk_evidence=False)))
        assert computed is not None
        assert computed.primary_drivers == () and computed.counter_drivers == ()

    def test_the_legacy_marker_is_a_named_constant(self):
        assert LEGACY_RESULT_WITHOUT_REASONING == "legacy_result_without_reasoning"


class TestPersistenceDoesNotReinterpret:
    def test_the_repository_never_builds_reasoning(self):
        """Storage serializes and deserializes. If it could construct
        reasoning it would be a second producer."""
        import ast
        from pathlib import Path
        source = Path("atlas/alpha/investment_decision/repository.py").read_text(encoding="utf-8")
        for node in ast.walk(ast.parse(source)):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                assert node.func.id not in {"build_drivers", "build_signal_summary",
                                            "build_key_unknowns", "RecommendationReasoning"}

    def test_the_readiness_blocker_is_not_the_canonical_change_trigger(self, repository):
        """`change_trigger` remains a readiness blocker for backward
        compatibility; the authoritative investment trigger now lives
        in the reasoning payload and is produced by the gate."""
        repo, _ = repository
        payload = serialize_reasoning(_reasoning())
        repo.upsert(_decision(payload), ticker="MSFT")
        stored = repo.get("case-1")
        assert stored.change_trigger is None
        assert "whatWouldChange" in stored.reasoning_payload
