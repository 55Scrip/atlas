"""Forward-Looking Evidence, Stage 4.2 -- economic synthesis.

Several interpreted forward signals, laid side by side for one company
and horizon. The questions: does every dimension keep its own state,
does absence stay distinct from "unchanged", does a mixed picture stay
mixed rather than become a verdict, and does every state lead back to
the transcript passages behind it?
"""
from __future__ import annotations

import ast
import dataclasses
import random
from dataclasses import dataclass
from pathlib import Path

import pytest

from atlas.analysis_engine.forward_claims import (
    DimensionState,
    DimensionSummary,
    EconomicDimension,
    ExpectedMovement,
    ForwardEconomicSignal,
    ForwardEconomicSynthesis,
    ForwardEvidenceKind,
    HorizonKind,
    OutlookEffect,
    SignalEntry,
    describe_synthesis,
    detect_revisions,
    extract_forward_claims,
    interpret_revisions,
    synthesize_forward_signals,
)
from tests.unit.analysis_engine.forward_claims.test_interpretation import CRM, GOOGL, VST, statement

_EFFECT = {
    (EconomicDimension.INVESTMENT_SPENDING, ExpectedMovement.INCREASED): OutlookEffect.AMBIGUOUS,
    (EconomicDimension.INVESTMENT_SPENDING, ExpectedMovement.DECREASED): OutlookEffect.AMBIGUOUS,
}


@dataclass(frozen=True)
class Signal:
    """Any forward evidence kind that satisfies the seam -- the synthesis
    never sees what produced it."""

    signal_id: str
    dimension: EconomicDimension
    movement: ExpectedMovement
    source_period: str | None
    company: str = "ACME"
    horizon_period: str = "2027"
    horizon_kind: HorizonKind = HorizonKind.UNSPECIFIED_YEAR
    evidence_kind: ForwardEvidenceKind = ForwardEvidenceKind.GUIDANCE_REVISION

    @property
    def outlook_effect(self) -> OutlookEffect:
        if self.movement is ExpectedMovement.UNCHANGED:
            return OutlookEffect.UNCHANGED
        default = OutlookEffect.STRENGTHENING if self.movement is ExpectedMovement.INCREASED else OutlookEffect.WEAKENING
        return _EFFECT.get((self.dimension, self.movement), default)


def one(*signals) -> ForwardEconomicSynthesis:
    (synthesis,) = synthesize_forward_signals(signals)
    return synthesis


REV, EARN, CASH, CAPEX = (EconomicDimension.REVENUE, EconomicDimension.EARNINGS,
                          EconomicDimension.CASH_GENERATION, EconomicDimension.INVESTMENT_SPENDING)
UP, DOWN, SAME = ExpectedMovement.INCREASED, ExpectedMovement.DECREASED, ExpectedMovement.UNCHANGED


class TestOneDimension:
    @pytest.mark.parametrize("movement,state", [(UP, DimensionState.STRENGTHENING), (DOWN, DimensionState.WEAKENING),
                                                (SAME, DimensionState.UNCHANGED)])
    def test_a_single_signal_sets_its_dimension(self, movement, state):
        assert one(Signal("s1", REV, movement, "2026Q2")).summary(REV).state is state

    def test_every_other_dimension_is_unsupported(self):
        synthesis = one(Signal("s1", REV, UP, "2026Q2"))
        for dimension in (EARN, CASH, CAPEX):
            summary = synthesis.summary(dimension)
            assert summary.state is DimensionState.UNSUPPORTED and summary.history == ()

    def test_missing_is_never_unchanged(self):
        synthesis = one(Signal("s1", EARN, SAME, "2026Q2"))
        assert synthesis.summary(EARN).state is DimensionState.UNCHANGED
        assert synthesis.summary(REV).state is DimensionState.UNSUPPORTED
        assert DimensionState.UNCHANGED is not DimensionState.UNSUPPORTED

    def test_investment_spending_stays_ambiguous_whichever_way_it_moves(self):
        assert one(Signal("s1", CAPEX, UP, "2026Q2")).summary(CAPEX).state is DimensionState.AMBIGUOUS
        assert one(Signal("s1", CAPEX, DOWN, "2026Q2")).summary(CAPEX).state is DimensionState.AMBIGUOUS


class TestSameDimensionHistory:
    def test_two_raises_stay_strengthening_with_both_in_history(self):
        summary = one(Signal("s1", REV, UP, "2026Q1"), Signal("s2", REV, UP, "2026Q2")).summary(REV)
        assert summary.state is DimensionState.STRENGTHENING
        assert [e.signal_id for e in summary.history] == ["s1", "s2"]

    def test_a_raise_then_a_cut_is_the_cut_now_and_both_in_order(self):
        summary = one(Signal("s1", REV, UP, "2026Q1"), Signal("s2", REV, DOWN, "2026Q2")).summary(REV)
        assert summary.state is DimensionState.WEAKENING
        assert [(e.source_period, e.movement) for e in summary.history] == [("2026Q1", UP), ("2026Q2", DOWN)]
        assert summary.history_has_opposite_effects

    def test_a_reaffirmation_after_a_raise_is_unchanged_now_with_the_raise_kept(self):
        summary = one(Signal("s1", REV, UP, "2026Q1"), Signal("s2", REV, SAME, "2026Q2")).summary(REV)
        assert summary.state is DimensionState.UNCHANGED
        assert summary.history[0].outlook_effect is OutlookEffect.STRENGTHENING

    def test_opposite_signals_from_the_same_period_are_a_conflict_not_a_choice(self):
        summary = one(Signal("s1", REV, UP, "2026Q2"), Signal("s2", REV, DOWN, "2026Q2")).summary(REV)
        assert summary.state is DimensionState.CONFLICTING

    def test_an_unplaceable_signal_that_disagrees_leaves_the_state_unestablished(self):
        summary = one(Signal("s1", REV, UP, "2026Q2"), Signal("s2", REV, DOWN, None)).summary(REV)
        assert summary.state is DimensionState.CONFLICTING
        assert summary.unordered_signal_ids == ("s2",)
        assert summary.history[-1].signal_id == "s2"

    def test_an_unplaceable_signal_that_agrees_does_not_invent_a_conflict(self):
        summary = one(Signal("s1", REV, UP, "2026Q2"), Signal("s2", REV, UP, None)).summary(REV)
        assert summary.state is DimensionState.STRENGTHENING

    def test_chronology_crosses_a_fiscal_year_boundary(self):
        summary = one(Signal("late", REV, DOWN, "2027Q1"), Signal("early", REV, UP, "2026Q4")).summary(REV)
        assert [e.signal_id for e in summary.history] == ["early", "late"]
        assert summary.state is DimensionState.WEAKENING


class TestAcrossDimensions:
    def test_revenue_strengthening_with_cash_weakening_stays_two_states(self):
        synthesis = one(Signal("r", REV, UP, "2026Q2"), Signal("c", CASH, DOWN, "2026Q2"))
        assert synthesis.summary(REV).state is DimensionState.STRENGTHENING
        assert synthesis.summary(CASH).state is DimensionState.WEAKENING
        assert DimensionState.CONFLICTING not in {d.state for d in synthesis.dimensions}

    def test_earnings_strengthening_with_more_capex_is_not_a_net_anything(self):
        synthesis = one(Signal("e", EARN, UP, "2026Q2"), Signal("k", CAPEX, UP, "2026Q2"))
        assert (synthesis.summary(EARN).state, synthesis.summary(CAPEX).state) == (
            DimensionState.STRENGTHENING, DimensionState.AMBIGUOUS,
        )

    def test_there_is_no_aggregate_sentiment_score_or_verdict_field(self):
        tokens = {
            token
            for cls in (ForwardEconomicSynthesis, DimensionSummary, SignalEntry)
            for field in dataclasses.fields(cls)
            for token in field.name.split("_")
        }
        for forbidden in ("sentiment", "score", "polarity", "net", "overall", "verdict", "confidence",
                          "conviction", "recommendation", "thesis", "bullish", "bearish", "rating", "aggregate"):
            assert forbidden not in tokens, forbidden

    def test_no_recommendation_vocabulary_anywhere_in_the_states(self):
        for member in DimensionState:
            assert member.value not in ("positive", "negative", "bullish", "bearish", "buy", "sell", "hold",
                                        "trim", "intact", "broken", "good", "bad", "stable_thesis")


class TestHorizonsAndDeterminism:
    def test_fiscal_and_calendar_years_are_separate_pictures(self):
        syntheses = synthesize_forward_signals((
            Signal("f", REV, UP, "2026Q2", horizon_kind=HorizonKind.FISCAL_YEAR, horizon_period="2026"),
            Signal("c", REV, DOWN, "2026Q2", horizon_kind=HorizonKind.CALENDAR_YEAR, horizon_period="2026"),
            Signal("u", REV, SAME, "2026Q2", horizon_kind=HorizonKind.UNSPECIFIED_YEAR, horizon_period="2026"),
        ))
        assert {(s.horizon_kind, s.summary(REV).state) for s in syntheses} == {
            (HorizonKind.FISCAL_YEAR, DimensionState.STRENGTHENING),
            (HorizonKind.CALENDAR_YEAR, DimensionState.WEAKENING),
            (HorizonKind.UNSPECIFIED_YEAR, DimensionState.UNCHANGED),
        }

    def test_different_years_and_companies_never_share_a_picture(self):
        syntheses = synthesize_forward_signals((
            Signal("a", REV, UP, "2026Q2", horizon_period="2026"),
            Signal("b", CAPEX, UP, "2026Q2", horizon_period="2028"),
            Signal("c", REV, DOWN, "2026Q2", company="OTHER", horizon_period="2026"),
        ))
        assert len(syntheses) == 3

    def test_input_order_never_changes_the_result(self):
        signals = [Signal(f"s{i}", dim, mv, f"2026Q{1 + i % 4}")
                   for i, (dim, mv) in enumerate([(REV, UP), (REV, DOWN), (CASH, SAME), (CAPEX, UP), (EARN, UP), (REV, UP)])]
        expected = synthesize_forward_signals(signals)
        for seed in range(5):
            shuffled = signals[:]
            random.Random(seed).shuffle(shuffled)
            assert synthesize_forward_signals(shuffled) == expected


class TestTheGenericSeam:
    def test_a_non_guidance_signal_fits_without_any_change(self):
        """A stand-in for a future contract interpretation: same shape,
        different producer. The synthesis reads it like any other."""

        @dataclass(frozen=True)
        class FutureContractSignal:
            signal_id: str = "contract-1"
            evidence_kind: ForwardEvidenceKind = ForwardEvidenceKind.GUIDANCE_REVISION  # only kind that exists today
            company: str = "ACME"
            horizon_period: str = "2027"
            horizon_kind: HorizonKind = HorizonKind.UNSPECIFIED_YEAR
            dimension: EconomicDimension = EARN
            movement: ExpectedMovement = UP
            outlook_effect: OutlookEffect = OutlookEffect.STRENGTHENING
            source_period: str | None = "2026Q2"

        signal = FutureContractSignal()
        assert isinstance(signal, ForwardEconomicSignal)
        assert one(signal, Signal("g", REV, UP, "2026Q2")).summary(EARN).history[0].signal_id == "contract-1"

    def test_the_synthesis_does_not_import_the_guidance_interpretation_type(self):
        source = (Path(__file__).resolve().parents[4] / "atlas" / "analysis_engine" / "forward_claims" / "synthesis.py")
        tree = ast.parse(source.read_text(encoding="utf-8"))
        names = {alias.name for node in ast.walk(tree) if isinstance(node, ast.ImportFrom) for alias in node.names}
        assert "GuidanceEconomicInterpretation" not in names
        assert "GuidanceRevision" not in names and "ForwardClaim" not in names


class TestFirewalls:
    _SOURCE = Path(__file__).resolve().parents[4] / "atlas" / "analysis_engine" / "forward_claims" / "synthesis.py"

    def test_only_the_fiscal_period_is_read_as_time(self):
        tree = ast.parse(self._SOURCE.read_text(encoding="utf-8"))
        attributes = {node.attr for node in ast.walk(tree) if isinstance(node, ast.Attribute)}
        for forbidden in ("published_at", "period_end", "statement_at", "created_at", "reported_at", "now", "today"):
            assert forbidden not in attributes, forbidden

    def test_it_reads_no_historical_valuation_risk_or_outlook_layer(self):
        tree = ast.parse(self._SOURCE.read_text(encoding="utf-8"))
        imported = {node.module or "" for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)}
        assert all(m.startswith("atlas.analysis_engine.forward_claims") or m in (
            "__future__", "collections.abc", "dataclasses", "enum", "typing") for m in imported), imported

    def test_the_description_states_evidence_not_conclusions(self):
        lines = describe_synthesis(one(Signal("r", REV, UP, "2026Q2"), Signal("k", CAPEX, UP, "2026Q2"),
                                       Signal("c", CASH, SAME, "2026Q2")))
        text = " ".join(lines).lower()
        for forbidden in ("improv", "better", "worse", "bullish", "bearish", "stronger case", "investment case",
                          "thesis", "because", "driven by", "recent", "positive", "negative", "overall"):
            assert forbidden not in text, forbidden
        assert "Earnings: no forward signal." in lines


# -- real companies, from verbatim transcript sentences -------------------------

def real(company, sentences, title="Chief Financial Officer"):
    from datetime import datetime, timezone
    records = [statement(text, company=company, quarter=q, title=title) for q, text in sentences.items()]
    claims = tuple(c for r in records for c in extract_forward_claims(r, extracted_at=datetime(2026, 9, 11, tzinfo=timezone.utc))[0])
    revisions, _ = detect_revisions(claims)
    interpretations = interpret_revisions(revisions, claims)
    (synthesis,) = synthesize_forward_signals(interpretations)
    return synthesis, claims, revisions, interpretations


class TestRealCompanies:
    def test_googl_investment_spending_increased_twice_and_stays_ambiguous(self):
        synthesis, *_ = real("GOOGL", GOOGL)
        capex = synthesis.summary(CAPEX)
        assert capex.state is DimensionState.AMBIGUOUS
        assert [(e.source_period, e.movement) for e in capex.history] == [("2026Q1", UP), ("2026Q2", UP)]
        assert {synthesis.summary(d).state for d in (REV, EARN, CASH)} == {DimensionState.UNSUPPORTED}

    def test_crm_revenue_strengthening_and_nothing_else_known(self):
        synthesis, *_ = real("CRM", CRM, title="Chief Operating & Financial Officer")
        assert synthesis.horizon_kind is HorizonKind.FISCAL_YEAR
        assert synthesis.summary(REV).state is DimensionState.STRENGTHENING
        assert {synthesis.summary(d).state for d in (EARN, CASH, CAPEX)} == {DimensionState.UNSUPPORTED}

    def test_vst_is_earnings_and_cash_unchanged_and_says_how_little_else_is_known(self):
        synthesis, *_ = real("VST", VST)
        assert (synthesis.summary(EARN).state, synthesis.summary(CASH).state) == (
            DimensionState.UNCHANGED, DimensionState.UNCHANGED,
        )
        assert (synthesis.summary(REV).state, synthesis.summary(CAPEX).state) == (
            DimensionState.UNSUPPORTED, DimensionState.UNSUPPORTED,
        )
        assert synthesis.evidence_kinds == (ForwardEvidenceKind.GUIDANCE_REVISION,)

    def test_every_state_leads_back_to_the_transcript_passage(self):
        synthesis, claims, revisions, interpretations = real("GOOGL", GOOGL)
        by_signal = {i.signal_id: i for i in interpretations}
        by_revision = {r.id: r for r in revisions}
        by_claim = {c.id: c for c in claims}
        for entry in synthesis.summary(CAPEX).history:
            interpretation = by_signal[entry.signal_id]
            revision = by_revision[interpretation.revision_id]
            claim = by_claim[revision.new_claim_id]
            assert claim.source_text in GOOGL[claim.source_period]
            assert entry.source_period == claim.source_period
