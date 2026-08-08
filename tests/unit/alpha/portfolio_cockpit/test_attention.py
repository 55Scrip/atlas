"""Tests for `atlas.alpha.portfolio_cockpit.attention.determine_attention`
(ATLAS-028 Phase 19/20) -- the confirmed, deterministic rule table,
exercised directly as a pure function: every individual signal, every
priority tier, and the "large only changes urgency, never severity"
rule."""
from __future__ import annotations

from datetime import datetime, timezone

from atlas.alpha.portfolio_cockpit.attention import determine_attention
from atlas.alpha.portfolio_cockpit.contracts import AttentionReasonKind, ReviewPriority
from atlas.alpha.portfolio_intelligence.thresholds import ELEVATED_CONCENTRATION_WEIGHT_PERCENT
from atlas.analysis_engine.contracts import RiskCategory
from atlas.analysis_engine.conviction import ConvictionAssessment, ConvictionLevel, ConvictionReasonCode
from atlas.analysis_engine.provenance import Provenance, SourceKind, UpdateTrigger
from atlas.analysis_engine.risk.contracts import RiskStatus, severity_for_risk_status
from atlas.analysis_engine.risk.models import EVALUATED_RISK_CATEGORIES, RiskFinding
from atlas.decision_engine.contracts import EvidenceCoverageLevel

_EVALUATED_AT = datetime(2026, 8, 8, 12, 0, tzinfo=timezone.utc)

_SMALL = ELEVATED_CONCENTRATION_WEIGHT_PERCENT - 1.0
_LARGE = ELEVATED_CONCENTRATION_WEIGHT_PERCENT


def _prov() -> Provenance:
    return Provenance(
        source_kind=SourceKind.ANALYSIS_ENGINE_STAGE,
        source_references=(),
        dependencies=(),
        update_trigger=UpdateTrigger.EXTERNAL_BUSINESS_DATA_INGESTED,
        consumers=(),
        computed_at=_EVALUATED_AT,
    )


def _finding(category: RiskCategory, status: RiskStatus) -> RiskFinding:
    return RiskFinding(
        id=f"risk_finding:{category.value}",
        category=category,
        status=status,
        severity=severity_for_risk_status(status),
        supporting_facts=(),
        contradicting_facts=(),
        missing_evidence=(),
        confidence=EvidenceCoverageLevel.FULL,
        provenance=_prov(),
        evaluated_at=_EVALUATED_AT,
    )


def _findings(
    *,
    financial: RiskStatus = RiskStatus.LOW,
    valuation: RiskStatus = RiskStatus.LOW,
    thesis: RiskStatus = RiskStatus.LOW,
    business: RiskStatus = RiskStatus.LOW,
) -> tuple[RiskFinding, ...]:
    by_category = {
        RiskCategory.FINANCIAL_RISK: financial,
        RiskCategory.VALUATION_RISK: valuation,
        RiskCategory.THESIS_RISK: thesis,
        RiskCategory.BUSINESS_RISK: business,
    }
    assert set(by_category) == EVALUATED_RISK_CATEGORIES
    return tuple(_finding(category, status) for category, status in by_category.items())


def _conviction(level: ConvictionLevel) -> ConvictionAssessment:
    reasons = (
        (ConvictionReasonCode.EVIDENCE_COVERAGE_INSUFFICIENT,)
        if level is ConvictionLevel.LOW
        else (ConvictionReasonCode.THESIS_NOT_STALE,)
    )
    return ConvictionAssessment(level=level, reasons=reasons)


def _call(*, weight_percent, conviction_level=ConvictionLevel.MODERATE, confidence=EvidenceCoverageLevel.FULL, **risk):
    return determine_attention(
        weight_percent=weight_percent,
        conviction=_conviction(conviction_level),
        confidence=confidence,
        risk_findings=_findings(**risk),
    )


class TestNoSignalFired:
    def test_small_holding_no_signal_is_none(self):
        result = _call(weight_percent=_SMALL)
        assert result.priority is ReviewPriority.NONE
        assert result.reasons == ()

    def test_large_holding_no_signal_is_still_none(self):
        """Size alone, with no real analytical signal, never triggers
        review -- large is a multiplier on urgency, not its own
        reason."""
        result = _call(weight_percent=_LARGE)
        assert result.priority is ReviewPriority.NONE
        assert result.reasons == ()


class TestEachSignalIndividuallyOnASmallHolding:
    def test_high_financial_risk(self):
        result = _call(weight_percent=_SMALL, financial=RiskStatus.HIGH)
        assert result.reasons == (AttentionReasonKind.HIGH_FINANCIAL_RISK,)
        assert result.priority is ReviewPriority.STANDARD_REVIEW

    def test_high_valuation_risk(self):
        result = _call(weight_percent=_SMALL, valuation=RiskStatus.HIGH)
        assert result.reasons == (AttentionReasonKind.HIGH_VALUATION_RISK,)
        assert result.priority is ReviewPriority.STANDARD_REVIEW

    def test_low_conviction(self):
        result = _call(weight_percent=_SMALL, conviction_level=ConvictionLevel.LOW)
        assert result.reasons == (AttentionReasonKind.LOW_CONVICTION,)
        assert result.priority is ReviewPriority.STANDARD_REVIEW

    def test_contradicting_evidence(self):
        result = _call(weight_percent=_SMALL, thesis=RiskStatus.HIGH)
        assert result.reasons == (AttentionReasonKind.CONTRADICTING_EVIDENCE,)
        assert result.priority is ReviewPriority.STANDARD_REVIEW

    def test_insufficient_evidence_not_applicable(self):
        result = _call(weight_percent=_SMALL, confidence=EvidenceCoverageLevel.NOT_APPLICABLE)
        assert result.reasons == (AttentionReasonKind.INSUFFICIENT_EVIDENCE,)
        assert result.priority is ReviewPriority.STANDARD_REVIEW

    def test_insufficient_evidence_none(self):
        result = _call(weight_percent=_SMALL, confidence=EvidenceCoverageLevel.NONE)
        assert result.reasons == (AttentionReasonKind.INSUFFICIENT_EVIDENCE,)
        assert result.priority is ReviewPriority.STANDARD_REVIEW


class TestLargePositionPriorityTierSignals:
    """Confirmed rule: large + any of {financial, valuation, conviction,
    contradicting evidence} -> PRIORITY_REVIEW."""

    def test_large_plus_high_financial_risk(self):
        result = _call(weight_percent=_LARGE, financial=RiskStatus.HIGH)
        assert result.priority is ReviewPriority.PRIORITY_REVIEW

    def test_large_plus_high_valuation_risk(self):
        result = _call(weight_percent=_LARGE, valuation=RiskStatus.HIGH)
        assert result.priority is ReviewPriority.PRIORITY_REVIEW

    def test_large_plus_low_conviction(self):
        result = _call(weight_percent=_LARGE, conviction_level=ConvictionLevel.LOW)
        assert result.priority is ReviewPriority.PRIORITY_REVIEW

    def test_large_plus_contradicting_evidence(self):
        result = _call(weight_percent=_LARGE, thesis=RiskStatus.HIGH)
        assert result.priority is ReviewPriority.PRIORITY_REVIEW


class TestLargePositionEvidenceOnlySignal:
    def test_large_plus_only_insufficient_evidence_is_evidence_review_not_priority(self):
        result = _call(weight_percent=_LARGE, confidence=EvidenceCoverageLevel.NOT_APPLICABLE)
        assert result.priority is ReviewPriority.EVIDENCE_REVIEW
        assert result.reasons == (AttentionReasonKind.INSUFFICIENT_EVIDENCE,)


class TestMultipleSignalsAreAllNamed:
    def test_every_fired_signal_is_named_not_only_the_deciding_one(self):
        result = _call(
            weight_percent=_LARGE,
            financial=RiskStatus.HIGH,
            valuation=RiskStatus.HIGH,
            conviction_level=ConvictionLevel.LOW,
            thesis=RiskStatus.HIGH,
            confidence=EvidenceCoverageLevel.NONE,
        )
        assert set(result.reasons) == set(AttentionReasonKind)
        assert result.priority is ReviewPriority.PRIORITY_REVIEW


class TestNeverARecommendation:
    def test_reason_kinds_never_encode_buy_sell_trim_add(self):
        forbidden = {"buy", "sell", "trim", "add", "hold"}
        for reason in AttentionReasonKind:
            assert not forbidden & set(reason.value.split("_"))

    def test_priority_values_never_encode_buy_sell_trim_add(self):
        forbidden = {"buy", "sell", "trim", "add", "hold"}
        for priority in ReviewPriority:
            assert not forbidden & set(priority.value.split("_"))


class TestDeterminism:
    def test_identical_inputs_produce_an_equal_result(self):
        first = _call(weight_percent=_LARGE, financial=RiskStatus.HIGH)
        second = _call(weight_percent=_LARGE, financial=RiskStatus.HIGH)
        assert first == second
