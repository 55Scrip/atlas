"""Tests for `atlas.analysis_engine.evidence_resolution` (Product Sprint
14 -- Evidence & Explanation Quality). Every fact/finding fed into the
resolver here is the real output of this codebase's own real extraction/
evaluation functions -- never a hand-built fake -- so a passing test here
is proof the resolver works against the exact shapes production code
actually produces."""
from __future__ import annotations

from datetime import date, datetime, timezone

from atlas.analysis_engine.business_data.models import RawBusinessDocument
from atlas.analysis_engine.business_data.pipeline import IngestedRecord, ingest
from atlas.analysis_engine.business_facts.extraction import extract_facts_from_records
from atlas.analysis_engine.evidence_resolution import resolve_evidence_references
from atlas.analysis_engine.growth import evaluate_growth
from atlas.analysis_engine.risk.business_risk import evaluate_business_risk
from tests.unit.decision_engine._fixtures import CASE_ID, build_observation

EVALUATED_AT = datetime(2026, 8, 8, 12, 0, tzinfo=timezone.utc)


def _make_record(identifier: str, period_end: date, **metadata) -> object:
    document = RawBusinessDocument(
        identifier=identifier,
        company="ASML",
        source_kind="annual_report",
        published_at=EVALUATED_AT,
        provider_id="structured_test",
        raw_reference=f"ref://{identifier}",
        content_hash=f"hash-{identifier}",
        language="en",
        period_end=period_end,
        metadata=metadata,
    )
    result = ingest(document, evaluated_at=EVALUATED_AT)
    assert isinstance(result, IngestedRecord)
    return result.record


def _strong_growth_records():
    return (
        _make_record("fy22", date(2022, 12, 31), revenue=1000.0, free_cash_flow=200.0),
        _make_record("fy23", date(2023, 12, 31), revenue=1100.0, free_cash_flow=240.0),
        _make_record("fy24", date(2024, 12, 31), revenue=1250.0, free_cash_flow=300.0),
    )


class TestResolveBusinessFactReference:
    def test_resolves_a_real_business_fact_id_into_a_readable_sentence(self):
        records = _strong_growth_records()
        facts = extract_facts_from_records(records, evaluated_at=EVALUATED_AT)
        revenue_fact = next(f for f in facts if f.kind.value == "revenue" and f.period == "2024-12-31")

        (resolved,) = resolve_evidence_references(
            (revenue_fact.id,),
            facts_by_id={f.id: f for f in facts},
            findings_by_id={},
            observations_by_id={},
        )

        assert resolved != revenue_fact.id
        assert " " in resolved  # real prose, not a bare reference
        assert "1,250" in resolved
        assert "2024-12-31" in resolved
        assert "Revenue" in resolved

    def test_resolved_sentence_never_contains_the_raw_reference_shape(self):
        """The exact live-discovered Sprint 13 shape
        (`{hash}:v1:{metric}:{date}`) must not survive resolution."""
        records = _strong_growth_records()
        facts = extract_facts_from_records(records, evaluated_at=EVALUATED_AT)
        fact = facts[0]
        assert ":v1:" in fact.id or ":v" in fact.id  # sanity: this really is the raw shape

        (resolved,) = resolve_evidence_references(
            (fact.id,), facts_by_id={f.id: f for f in facts}, findings_by_id={}, observations_by_id={}
        )
        assert ":v1:" not in resolved
        assert fact.id not in resolved


class TestResolveFindingSelfReference:
    def test_resolves_a_real_finding_self_reference_into_its_own_status(self):
        records = _strong_growth_records()
        facts = extract_facts_from_records(records, evaluated_at=EVALUATED_AT)
        growth_finding = evaluate_growth(facts, evaluated_at=EVALUATED_AT)
        assert growth_finding.id == "business_finding:growth"

        risk_finding = evaluate_business_risk(growth_finding, evaluated_at=EVALUATED_AT)
        assert growth_finding.id in risk_finding.supporting_facts

        (resolved,) = resolve_evidence_references(
            (growth_finding.id,),
            facts_by_id={},
            findings_by_id={growth_finding.id: growth_finding},
            observations_by_id={},
        )

        assert resolved != growth_finding.id
        assert "business_finding:" not in resolved
        assert "Growth" in resolved
        assert growth_finding.status.value.replace("_", " ") in resolved.lower()


class TestResolveObservationReference:
    def test_resolves_a_real_observation_id_into_its_own_recorded_statement(self):
        observation = build_observation(statement="Q2 revenue grew 12% year over year.")

        (resolved,) = resolve_evidence_references(
            (str(observation.id),),
            facts_by_id={},
            findings_by_id={},
            observations_by_id={str(observation.id): observation},
        )

        assert resolved == "Q2 revenue grew 12% year over year."


class TestUnresolvableReference:
    def test_an_unrecognized_reference_falls_back_to_the_original_string_unchanged(self):
        """A stale or unknown reference must never be silently dropped
        or replaced with a fabricated sentence."""
        (resolved,) = resolve_evidence_references(
            ("some_stale_reference_id",), facts_by_id={}, findings_by_id={}, observations_by_id={}
        )
        assert resolved == "some_stale_reference_id"


class TestOrderingAndCount:
    def test_preserves_order_and_count_including_a_mix_of_resolvable_and_not(self):
        observation = build_observation(statement="Real recorded statement.")
        resolved = resolve_evidence_references(
            ("unknown_ref", str(observation.id), "unknown_ref_2"),
            facts_by_id={},
            findings_by_id={},
            observations_by_id={str(observation.id): observation},
        )
        assert len(resolved) == 3
        assert resolved[0] == "unknown_ref"
        assert resolved[1] == "Real recorded statement."
        assert resolved[2] == "unknown_ref_2"
