"""Sprint 276 — Value Scenario schema dataclass tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from atlas.value_scenario import (
    HoldingScenario,
    PortfolioContribution,
    PortfolioScenario,
    ScenarioAssumption,
    ScenarioAssumptionType,
    ScenarioCaseType,
    ScenarioChangeTrigger,
    ScenarioChangeTriggerType,
    ScenarioConfidence,
    ScenarioDirection,
    ScenarioEvidenceItem,
    ScenarioEvidenceQuality,
    ScenarioEvidenceType,
    ScenarioExpectedEffect,
    ScenarioFreshness,
    ScenarioRange,
    ScenarioRangeImpactLevel,
    ScenarioRevision,
    ScenarioReviewType,
    ScenarioSafetyBoundary,
    ScenarioSubject,
    ScenarioSubjectType,
    ScenarioTimeHorizon,
    ValueScenarioReview,
)

CLI_FILE = Path("atlas/cli/main.py")

# ---------------------------------------------------------------------------
# Fixture helpers
# ---------------------------------------------------------------------------


def _subject(**kwargs) -> ScenarioSubject:
    defaults = {
        "subject_id": "subj_001",
        "subject_type": "holding",
        "display_name": "Hypothetical Co.",
    }
    defaults.update(kwargs)
    return ScenarioSubject(**defaults)


def _range(**kwargs) -> ScenarioRange:
    defaults = {
        "range_id": "rng_001",
        "horizon": "medium_term",
        "case_type": "base",
        "lower_percent": 5.0,
        "upper_percent": 15.0,
    }
    defaults.update(kwargs)
    return ScenarioRange(**defaults)


def _assumption(**kwargs) -> ScenarioAssumption:
    defaults = {
        "assumption_id": "asm_001",
        "assumption_type": "revenue_growth",
        "description": "Revenue grows 7–9% in base case.",
    }
    defaults.update(kwargs)
    return ScenarioAssumption(**defaults)


def _evidence_item(**kwargs) -> ScenarioEvidenceItem:
    defaults = {
        "evidence_item_id": "evi_001",
        "evidence_type": "company_report",
        "description": "Q2 2026 earnings: revenue +8% YoY.",
    }
    defaults.update(kwargs)
    return ScenarioEvidenceItem(**defaults)


def _trigger(**kwargs) -> ScenarioChangeTrigger:
    defaults = {
        "trigger_id": "trg_001",
        "trigger_type": "earnings_report",
        "description": "Q3 earnings — tests margin assumption.",
    }
    defaults.update(kwargs)
    return ScenarioChangeTrigger(**defaults)


def _revision(**kwargs) -> ScenarioRevision:
    defaults = {
        "revision_id": "rev_001",
        "revised_at": "2026-07-07T12:00:00Z",
        "reason": "Margin assumptions reduced after Q3 miss.",
    }
    defaults.update(kwargs)
    return ScenarioRevision(**defaults)


def _contribution(**kwargs) -> PortfolioContribution:
    defaults = {
        "contribution_id": "ctb_001",
        "holding_id": "hld_001",
        "display_name": "Hypothetical Co.",
    }
    defaults.update(kwargs)
    return PortfolioContribution(**defaults)


def _holding_scenario(**kwargs) -> HoldingScenario:
    defaults = {
        "holding_scenario_id": "hsc_001",
        "subject": _subject(),
        "ranges": [_range()],
    }
    defaults.update(kwargs)
    return HoldingScenario(**defaults)


def _portfolio_scenario(**kwargs) -> PortfolioScenario:
    defaults = {
        "portfolio_scenario_id": "psc_001",
        "portfolio_id": "port_001",
        "ranges": [_range()],
    }
    defaults.update(kwargs)
    return PortfolioScenario(**defaults)


def _review(review_type: str = "holding", **kwargs) -> ValueScenarioReview:
    if review_type == "holding":
        defaults = {
            "scenario_review_id": "vsr_001",
            "review_type": "holding",
            "created_at": "2026-07-07T12:00:00Z",
            "subject": _subject(),
            "time_horizons": ["medium_term"],
            "holding_scenarios": [_holding_scenario()],
        }
    else:
        defaults = {
            "scenario_review_id": "vsr_002",
            "review_type": "portfolio",
            "created_at": "2026-07-07T12:00:00Z",
            "subject": _subject(subject_type="portfolio", portfolio_id="port_001"),
            "time_horizons": ["medium_term"],
            "portfolio_scenario": _portfolio_scenario(),
        }
    defaults.update(kwargs)
    return ValueScenarioReview(**defaults)


# ---------------------------------------------------------------------------
# Package / module exists
# ---------------------------------------------------------------------------


class TestPackageExists:
    def test_package_importable(self):
        import atlas.value_scenario  # noqa: F401

    def test_schema_module_importable(self):
        import atlas.value_scenario.schema  # noqa: F401

    def test_all_exports_importable(self):
        from atlas.value_scenario import (  # noqa: F401
            HoldingScenario,
            PortfolioContribution,
            PortfolioScenario,
            ScenarioAssumption,
            ScenarioAssumptionType,
            ScenarioCaseType,
            ScenarioChangeTrigger,
            ScenarioChangeTriggerType,
            ScenarioConfidence,
            ScenarioDirection,
            ScenarioEvidenceItem,
            ScenarioEvidenceQuality,
            ScenarioEvidenceType,
            ScenarioExpectedEffect,
            ScenarioFreshness,
            ScenarioRange,
            ScenarioRangeImpactLevel,
            ScenarioRevision,
            ScenarioReviewType,
            ScenarioSafetyBoundary,
            ScenarioSubject,
            ScenarioSubjectType,
            ScenarioTimeHorizon,
            ValueScenarioReview,
        )


# ---------------------------------------------------------------------------
# Canonical enum values
# ---------------------------------------------------------------------------


class TestCanonicalEnums:
    def test_review_types(self):
        assert ScenarioReviewType.HOLDING.value == "holding"
        assert ScenarioReviewType.PORTFOLIO.value == "portfolio"
        assert ScenarioReviewType.MIXED.value == "mixed"

    def test_subject_types(self):
        assert ScenarioSubjectType.HOLDING.value == "holding"
        assert ScenarioSubjectType.PORTFOLIO.value == "portfolio"
        assert ScenarioSubjectType.WATCHLIST_ITEM.value == "watchlist_item"

    def test_time_horizons(self):
        assert ScenarioTimeHorizon.SHORT_TERM.value == "short_term"
        assert ScenarioTimeHorizon.MEDIUM_TERM.value == "medium_term"
        assert ScenarioTimeHorizon.LONG_TERM.value == "long_term"

    def test_case_types(self):
        assert ScenarioCaseType.BEAR.value == "bear"
        assert ScenarioCaseType.BASE.value == "base"
        assert ScenarioCaseType.BULL.value == "bull"
        assert ScenarioCaseType.DOWNSIDE.value == "downside"
        assert ScenarioCaseType.UPSIDE.value == "upside"
        assert ScenarioCaseType.UNCERTAINTY_BAND.value == "uncertainty_band"

    def test_evidence_quality_values(self):
        values = {e.value for e in ScenarioEvidenceQuality}
        assert values == {"strong", "adequate", "incomplete", "weak", "outdated", "conflicting"}

    def test_confidence_values(self):
        values = {e.value for e in ScenarioConfidence}
        assert values == {"low", "medium", "high", "unknown"}

    def test_assumption_types_count(self):
        assert len(ScenarioAssumptionType) == 12

    def test_assumption_types_include_key_values(self):
        values = {e.value for e in ScenarioAssumptionType}
        assert "revenue_growth" in values
        assert "margin" in values
        assert "valuation_multiple" in values
        assert "capital_allocation" in values
        assert "macro_rate_sensitivity" in values

    def test_direction_values(self):
        values = {e.value for e in ScenarioDirection}
        assert values == {"positive", "negative", "mixed", "neutral", "unknown"}

    def test_evidence_types_count(self):
        assert len(ScenarioEvidenceType) == 8

    def test_freshness_values(self):
        values = {e.value for e in ScenarioFreshness}
        assert values == {"current", "recent", "stale", "unknown"}

    def test_trigger_types_count(self):
        assert len(ScenarioChangeTriggerType) == 15

    def test_trigger_types_include_key_values(self):
        values = {e.value for e in ScenarioChangeTriggerType}
        assert "earnings_report" in values
        assert "thesis_evidence_improved" in values
        assert "thesis_evidence_weakened" in values
        assert "margin_surprise" in values
        assert "regulatory_change" in values

    def test_expected_effect_values(self):
        values = {e.value for e in ScenarioExpectedEffect}
        assert "range_may_expand" in values
        assert "range_may_compress" in values
        assert "range_may_shift_up" in values
        assert "range_may_shift_down" in values
        assert "confidence_may_increase" in values
        assert "confidence_may_decrease" in values
        assert "unknown" in values

    def test_range_impact_levels(self):
        values = {e.value for e in ScenarioRangeImpactLevel}
        assert values == {"low", "medium", "high", "dominant"}


# ---------------------------------------------------------------------------
# ScenarioSubject
# ---------------------------------------------------------------------------


class TestScenarioSubject:
    def test_valid_subject(self):
        s = _subject()
        assert s.subject_id == "subj_001"
        assert s.display_name == "Hypothetical Co."

    def test_subject_type_coerced(self):
        s = _subject(subject_type="watchlist_item")
        assert s.subject_type == "watchlist_item"

    def test_empty_subject_id_raises(self):
        with pytest.raises(ValueError, match="subject_id"):
            _subject(subject_id="")

    def test_empty_display_name_raises(self):
        with pytest.raises(ValueError, match="display_name"):
            _subject(display_name="")

    def test_invalid_subject_type_raises(self):
        with pytest.raises(ValueError, match="ScenarioSubjectType"):
            _subject(subject_type="invalid_type_xyz")

    def test_optional_fields_default_none(self):
        s = _subject()
        assert s.ticker is None
        assert s.portfolio_id is None
        assert s.source_reference is None

    def test_optional_fields_set(self):
        s = _subject(ticker="HYPO", portfolio_id="p1", source_reference="note_001")
        assert s.ticker == "HYPO"
        assert s.portfolio_id == "p1"
        assert s.source_reference == "note_001"


# ---------------------------------------------------------------------------
# ScenarioRange
# ---------------------------------------------------------------------------


class TestScenarioRange:
    def test_valid_range(self):
        r = _range()
        assert r.range_id == "rng_001"
        assert r.lower_percent == 5.0
        assert r.upper_percent == 15.0

    def test_horizon_coerced(self):
        r = _range(horizon="long_term")
        assert r.horizon == "long_term"

    def test_case_type_coerced(self):
        r = _range(case_type="bear")
        assert r.case_type == "bear"

    def test_confidence_coerced(self):
        r = _range(confidence="medium")
        assert r.confidence == "medium"

    def test_evidence_quality_coerced(self):
        r = _range(evidence_quality="strong")
        assert r.evidence_quality == "strong"

    def test_rejects_lower_equal_upper(self):
        with pytest.raises(ValueError, match="single-point"):
            _range(lower_percent=10.0, upper_percent=10.0)

    def test_rejects_lower_greater_than_upper(self):
        with pytest.raises(ValueError, match="strictly less than"):
            _range(lower_percent=20.0, upper_percent=5.0)

    def test_empty_range_id_raises(self):
        with pytest.raises(ValueError, match="range_id"):
            _range(range_id="")

    def test_invalid_horizon_raises(self):
        with pytest.raises(ValueError, match="ScenarioTimeHorizon"):
            _range(horizon="yearly")

    def test_invalid_case_type_raises(self):
        with pytest.raises(ValueError, match="ScenarioCaseType"):
            _range(case_type="neutral")

    def test_invalid_confidence_raises(self):
        with pytest.raises(ValueError, match="ScenarioConfidence"):
            _range(confidence="very_high")

    def test_invalid_evidence_quality_raises(self):
        with pytest.raises(ValueError, match="ScenarioEvidenceQuality"):
            _range(evidence_quality="excellent")

    def test_assumption_ids_stored(self):
        r = _range(assumption_ids=["asm_001", "asm_002"])
        assert r.assumption_ids == ["asm_001", "asm_002"]

    def test_uncertainty_note_preserved(self):
        note = "Margin durability is the main source of uncertainty."
        r = _range(uncertainty_note=note)
        assert r.uncertainty_note == note

    def test_negative_range_valid(self):
        r = _range(lower_percent=-15.0, upper_percent=-5.0)
        assert r.lower_percent == -15.0
        assert r.upper_percent == -5.0


# ---------------------------------------------------------------------------
# ScenarioAssumption
# ---------------------------------------------------------------------------


class TestScenarioAssumption:
    def test_valid_assumption(self):
        a = _assumption()
        assert a.assumption_id == "asm_001"
        assert a.assumption_type == "revenue_growth"

    def test_empty_id_raises(self):
        with pytest.raises(ValueError, match="assumption_id"):
            _assumption(assumption_id="")

    def test_empty_description_raises(self):
        with pytest.raises(ValueError, match="description"):
            _assumption(description="")

    def test_invalid_type_raises(self):
        with pytest.raises(ValueError, match="ScenarioAssumptionType"):
            _assumption(assumption_type="price_momentum")

    def test_invalid_direction_raises(self):
        with pytest.raises(ValueError, match="ScenarioDirection"):
            _assumption(direction="upward")

    def test_invalid_confidence_raises(self):
        with pytest.raises(ValueError, match="ScenarioConfidence"):
            _assumption(confidence="certain")

    def test_related_horizon_optional(self):
        a = _assumption(related_horizon="long_term")
        assert a.related_horizon == "long_term"

    def test_invalid_related_horizon_raises(self):
        with pytest.raises(ValueError, match="ScenarioTimeHorizon"):
            _assumption(related_horizon="5_years")

    def test_description_preserved(self):
        desc = "Revenue grows 7–9% in the base case; bear 3%; bull 12%+."
        a = _assumption(description=desc)
        assert a.description == desc

    def test_defaults(self):
        a = _assumption()
        assert a.direction == "unknown"
        assert a.confidence == "unknown"
        assert a.related_horizon is None


# ---------------------------------------------------------------------------
# ScenarioEvidenceItem
# ---------------------------------------------------------------------------


class TestScenarioEvidenceItem:
    def test_valid_evidence_item(self):
        e = _evidence_item()
        assert e.evidence_item_id == "evi_001"
        assert e.evidence_type == "company_report"

    def test_empty_id_raises(self):
        with pytest.raises(ValueError, match="evidence_item_id"):
            _evidence_item(evidence_item_id="")

    def test_empty_description_raises(self):
        with pytest.raises(ValueError, match="description"):
            _evidence_item(description="")

    def test_invalid_evidence_type_raises(self):
        with pytest.raises(ValueError, match="ScenarioEvidenceType"):
            _evidence_item(evidence_type="press_release")

    def test_invalid_freshness_raises(self):
        with pytest.raises(ValueError, match="ScenarioFreshness"):
            _evidence_item(freshness="very_old")

    def test_invalid_evidence_quality_raises(self):
        with pytest.raises(ValueError, match="ScenarioEvidenceQuality"):
            _evidence_item(evidence_quality="excellent")

    def test_source_reference_preserved(self):
        e = _evidence_item(source_reference="Q2 2026 earnings release")
        assert e.source_reference == "Q2 2026 earnings release"

    def test_defaults(self):
        e = _evidence_item()
        assert e.freshness == "unknown"
        assert e.evidence_quality == "incomplete"
        assert e.related_assumption_ids == []


# ---------------------------------------------------------------------------
# ScenarioChangeTrigger
# ---------------------------------------------------------------------------


class TestScenarioChangeTrigger:
    def test_valid_trigger(self):
        t = _trigger()
        assert t.trigger_id == "trg_001"
        assert t.trigger_type == "earnings_report"

    def test_empty_id_raises(self):
        with pytest.raises(ValueError, match="trigger_id"):
            _trigger(trigger_id="")

    def test_empty_description_raises(self):
        with pytest.raises(ValueError, match="description"):
            _trigger(description="")

    def test_invalid_trigger_type_raises(self):
        with pytest.raises(ValueError, match="ScenarioChangeTriggerType"):
            _trigger(trigger_type="random_event")

    def test_invalid_expected_effect_raises(self):
        with pytest.raises(ValueError, match="ScenarioExpectedEffect"):
            _trigger(expected_effect="price_goes_up")

    def test_default_expected_effect(self):
        t = _trigger()
        assert t.expected_effect == "unknown"

    def test_monitoring_note_preserved(self):
        note = "Watch gross margin trajectory."
        t = _trigger(monitoring_note=note)
        assert t.monitoring_note == note

    def test_all_15_trigger_types_valid(self):
        for tt in ScenarioChangeTriggerType:
            t = _trigger(trigger_type=tt.value)
            assert t.trigger_type == tt.value


# ---------------------------------------------------------------------------
# ScenarioRevision
# ---------------------------------------------------------------------------


class TestScenarioRevision:
    def test_valid_revision(self):
        r = _revision()
        assert r.revision_id == "rev_001"
        assert r.reason == "Margin assumptions reduced after Q3 miss."

    def test_empty_revision_id_raises(self):
        with pytest.raises(ValueError, match="revision_id"):
            _revision(revision_id="")

    def test_empty_revised_at_raises(self):
        with pytest.raises(ValueError, match="revised_at"):
            _revision(revised_at="")

    def test_empty_reason_raises(self):
        with pytest.raises(ValueError, match="reason"):
            _revision(reason="")

    def test_reason_preserved(self):
        reason = "Evidence quality weakened — margin durability now conflicting."
        r = _revision(reason=reason)
        assert r.reason == reason

    def test_previous_and_updated_range_ids(self):
        r = _revision(previous_range_ids=["rng_old"], updated_range_ids=["rng_new"])
        assert r.previous_range_ids == ["rng_old"]
        assert r.updated_range_ids == ["rng_new"]

    def test_revision_note_preserved(self):
        note = "This revision was prompted by Q3 earnings miss."
        r = _revision(revision_note=note)
        assert r.revision_note == note


# ---------------------------------------------------------------------------
# PortfolioContribution
# ---------------------------------------------------------------------------


class TestPortfolioContribution:
    def test_valid_contribution(self):
        c = _contribution()
        assert c.contribution_id == "ctb_001"
        assert c.holding_id == "hld_001"

    def test_empty_contribution_id_raises(self):
        with pytest.raises(ValueError, match="contribution_id"):
            _contribution(contribution_id="")

    def test_empty_holding_id_raises(self):
        with pytest.raises(ValueError, match="holding_id"):
            _contribution(holding_id="")

    def test_empty_display_name_raises(self):
        with pytest.raises(ValueError, match="display_name"):
            _contribution(display_name="")

    def test_invalid_range_impact_level_raises(self):
        with pytest.raises(ValueError, match="ScenarioRangeImpactLevel"):
            _contribution(range_impact_level="extreme")

    def test_invalid_evidence_quality_raises(self):
        with pytest.raises(ValueError, match="ScenarioEvidenceQuality"):
            _contribution(evidence_quality="excellent")

    def test_all_impact_levels_valid(self):
        for level in ScenarioRangeImpactLevel:
            c = _contribution(range_impact_level=level.value)
            assert c.range_impact_level == level.value

    def test_portfolio_weight_stored(self):
        c = _contribution(portfolio_weight=0.15)
        assert c.portfolio_weight == 0.15

    def test_key_reason_preserved(self):
        reason = "High weight combined with wide scenario range."
        c = _contribution(key_reason=reason)
        assert c.key_reason == reason


# ---------------------------------------------------------------------------
# HoldingScenario
# ---------------------------------------------------------------------------


class TestHoldingScenario:
    def test_valid_holding_scenario(self):
        h = _holding_scenario()
        assert h.holding_scenario_id == "hsc_001"
        assert len(h.ranges) == 1

    def test_empty_id_raises(self):
        with pytest.raises(ValueError, match="holding_scenario_id"):
            _holding_scenario(holding_scenario_id="")

    def test_subject_coerced_from_dict(self):
        d = {
            "subject_id": "subj_002",
            "subject_type": "holding",
            "display_name": "Another Co.",
        }
        h = _holding_scenario(subject=d)
        assert isinstance(h.subject, ScenarioSubject)
        assert h.subject.display_name == "Another Co."

    def test_ranges_coerced_from_dicts(self):
        rd = {
            "range_id": "rng_002",
            "horizon": "short_term",
            "case_type": "bear",
            "lower_percent": -10.0,
            "upper_percent": -2.0,
        }
        h = _holding_scenario(ranges=[rd])
        assert isinstance(h.ranges[0], ScenarioRange)

    def test_invalid_evidence_quality_raises(self):
        with pytest.raises(ValueError, match="ScenarioEvidenceQuality"):
            _holding_scenario(evidence_quality="excellent")

    def test_key_drivers_preserved(self):
        h = _holding_scenario(key_drivers=["Revenue growth", "Margin durability"])
        assert h.key_drivers == ["Revenue growth", "Margin durability"]

    def test_key_risks_preserved(self):
        h = _holding_scenario(key_risks=["Input cost pressure", "Rate sensitivity"])
        assert h.key_risks == ["Input cost pressure", "Rate sensitivity"]

    def test_notes_preserved(self):
        note = "Review after Q3 earnings report."
        h = _holding_scenario(notes=note)
        assert h.notes == note

    def test_defaults(self):
        h = _holding_scenario()
        assert h.evidence_quality == "incomplete"
        assert h.confidence == "unknown"
        assert h.notes is None


# ---------------------------------------------------------------------------
# PortfolioScenario
# ---------------------------------------------------------------------------


class TestPortfolioScenario:
    def test_valid_portfolio_scenario(self):
        p = _portfolio_scenario()
        assert p.portfolio_scenario_id == "psc_001"
        assert p.portfolio_id == "port_001"

    def test_empty_portfolio_scenario_id_raises(self):
        with pytest.raises(ValueError, match="portfolio_scenario_id"):
            _portfolio_scenario(portfolio_scenario_id="")

    def test_empty_portfolio_id_raises(self):
        with pytest.raises(ValueError, match="portfolio_id"):
            _portfolio_scenario(portfolio_id="")

    def test_contributions_coerced(self):
        cd = {
            "contribution_id": "ctb_002",
            "holding_id": "hld_002",
            "display_name": "Test Co.",
        }
        p = _portfolio_scenario(weighted_contributions=[cd])
        assert isinstance(p.weighted_contributions[0], PortfolioContribution)

    def test_upside_drivers_preserved(self):
        p = _portfolio_scenario(main_upside_drivers=["Semiconductor position"])
        assert p.main_upside_drivers == ["Semiconductor position"]

    def test_downside_drivers_preserved(self):
        p = _portfolio_scenario(main_downside_drivers=["Rate sensitivity"])
        assert p.main_downside_drivers == ["Rate sensitivity"]

    def test_evidence_gaps_preserved(self):
        p = _portfolio_scenario(evidence_gaps=["Margin evidence incomplete for 3 positions."])
        assert p.evidence_gaps[0] == "Margin evidence incomplete for 3 positions."

    def test_concentration_sensitivity_preserved(self):
        note = "Semiconductor position dominates the portfolio range."
        p = _portfolio_scenario(concentration_sensitivity=note)
        assert p.concentration_sensitivity == note


# ---------------------------------------------------------------------------
# ScenarioSafetyBoundary
# ---------------------------------------------------------------------------


class TestScenarioSafetyBoundary:
    def test_default_all_true(self):
        sb = ScenarioSafetyBoundary()
        assert sb.no_single_point_targets is True
        assert sb.no_action_calls is True
        assert sb.no_execution_instructions is True
        assert sb.no_prediction_certainty is True
        assert sb.assumptions_required is True
        assert sb.evidence_quality_required is True
        assert sb.uncertainty_required is True
        assert sb.change_triggers_required is True

    @pytest.mark.parametrize("field_name", [
        "no_single_point_targets",
        "no_action_calls",
        "no_execution_instructions",
        "no_prediction_certainty",
        "assumptions_required",
        "evidence_quality_required",
        "uncertainty_required",
        "change_triggers_required",
    ])
    def test_false_flag_raises(self, field_name: str):
        with pytest.raises(ValueError, match=field_name):
            ScenarioSafetyBoundary(**{field_name: False})

    def test_from_dict_defaults_all_true(self):
        sb = ScenarioSafetyBoundary.from_dict({})
        assert sb.no_single_point_targets is True

    def test_to_dict_all_true(self):
        d = ScenarioSafetyBoundary().to_dict()
        assert all(v is True for v in d.values())


# ---------------------------------------------------------------------------
# ValueScenarioReview
# ---------------------------------------------------------------------------


class TestValueScenarioReview:
    def test_valid_holding_review(self):
        r = _review("holding")
        assert r.scenario_review_id == "vsr_001"
        assert r.review_type == "holding"
        assert len(r.holding_scenarios) == 1

    def test_valid_portfolio_review(self):
        r = _review("portfolio")
        assert r.review_type == "portfolio"
        assert r.portfolio_scenario is not None

    def test_empty_review_id_raises(self):
        with pytest.raises(ValueError, match="scenario_review_id"):
            _review("holding", scenario_review_id="")

    def test_invalid_review_type_raises(self):
        with pytest.raises(ValueError, match="ScenarioReviewType"):
            ValueScenarioReview(
                scenario_review_id="vsr_x",
                review_type="snapshot",
                created_at="2026-07-07T12:00:00Z",
                subject=_subject(),
                holding_scenarios=[_holding_scenario()],
            )

    def test_empty_created_at_raises(self):
        with pytest.raises(ValueError, match="created_at"):
            _review("holding", created_at="")

    def test_holding_review_requires_holding_scenario(self):
        with pytest.raises(ValueError, match="holding_scenario"):
            _review("holding", holding_scenarios=[])

    def test_portfolio_review_requires_portfolio_scenario(self):
        with pytest.raises(ValueError, match="portfolio_scenario"):
            _review("portfolio", portfolio_scenario=None)

    def test_mixed_review_no_structural_requirement(self):
        r = ValueScenarioReview(
            scenario_review_id="vsr_mixed",
            review_type="mixed",
            created_at="2026-07-07T12:00:00Z",
            subject=_subject(),
            holding_scenarios=[_holding_scenario()],
            portfolio_scenario=_portfolio_scenario(),
        )
        assert r.review_type == "mixed"

    def test_safety_boundary_defaults_applied(self):
        r = _review("holding")
        assert isinstance(r.safety_boundary, ScenarioSafetyBoundary)
        assert r.safety_boundary.no_single_point_targets is True

    def test_subject_coerced_from_dict(self):
        d = {
            "subject_id": "subj_x",
            "subject_type": "holding",
            "display_name": "Test Co.",
        }
        r = _review("holding", subject=d)
        assert isinstance(r.subject, ScenarioSubject)

    def test_safety_boundary_coerced_from_dict(self):
        r = _review("holding", safety_boundary={
            "no_single_point_targets": True,
            "no_action_calls": True,
            "no_execution_instructions": True,
            "no_prediction_certainty": True,
            "assumptions_required": True,
            "evidence_quality_required": True,
            "uncertainty_required": True,
            "change_triggers_required": True,
        })
        assert isinstance(r.safety_boundary, ScenarioSafetyBoundary)

    def test_safety_boundary_false_raises_via_review(self):
        with pytest.raises(ValueError):
            _review("holding", safety_boundary={"no_action_calls": False})

    def test_time_horizons_coerced(self):
        r = _review("holding", time_horizons=["short_term", "medium_term"])
        assert r.time_horizons == ["short_term", "medium_term"]

    def test_invalid_time_horizon_raises(self):
        with pytest.raises(ValueError, match="ScenarioTimeHorizon"):
            _review("holding", time_horizons=["quarterly"])


# ---------------------------------------------------------------------------
# Serialization — to_dict / from_dict
# ---------------------------------------------------------------------------


class TestSerialization:
    def test_scenario_range_roundtrip(self):
        r = _range(uncertainty_note="Test note.", assumption_ids=["asm_001"])
        d = r.to_dict()
        r2 = ScenarioRange.from_dict(d)
        assert r2.range_id == r.range_id
        assert r2.lower_percent == r.lower_percent
        assert r2.upper_percent == r.upper_percent
        assert r2.uncertainty_note == r.uncertainty_note
        assert r2.assumption_ids == r.assumption_ids

    def test_assumption_roundtrip(self):
        a = _assumption(direction="positive", related_horizon="medium_term")
        d = a.to_dict()
        a2 = ScenarioAssumption.from_dict(d)
        assert a2.assumption_id == a.assumption_id
        assert a2.description == a.description
        assert a2.direction == "positive"
        assert a2.related_horizon == "medium_term"

    def test_evidence_item_roundtrip(self):
        e = _evidence_item(freshness="current", evidence_quality="strong")
        d = e.to_dict()
        e2 = ScenarioEvidenceItem.from_dict(d)
        assert e2.evidence_item_id == e.evidence_item_id
        assert e2.freshness == "current"
        assert e2.evidence_quality == "strong"

    def test_trigger_roundtrip(self):
        t = _trigger(expected_effect="range_may_compress")
        d = t.to_dict()
        t2 = ScenarioChangeTrigger.from_dict(d)
        assert t2.trigger_id == t.trigger_id
        assert t2.expected_effect == "range_may_compress"

    def test_revision_roundtrip(self):
        r = _revision(previous_range_ids=["rng_old"], revision_note="Context.")
        d = r.to_dict()
        r2 = ScenarioRevision.from_dict(d)
        assert r2.revision_id == r.revision_id
        assert r2.reason == r.reason
        assert r2.previous_range_ids == ["rng_old"]
        assert r2.revision_note == "Context."

    def test_holding_scenario_roundtrip(self):
        h = _holding_scenario(
            key_drivers=["Revenue growth"],
            key_risks=["Rate risk"],
            notes="Review after earnings.",
        )
        d = h.to_dict()
        h2 = HoldingScenario.from_dict(d)
        assert h2.holding_scenario_id == h.holding_scenario_id
        assert h2.key_drivers == ["Revenue growth"]
        assert h2.key_risks == ["Rate risk"]
        assert h2.notes == "Review after earnings."

    def test_portfolio_scenario_roundtrip(self):
        p = _portfolio_scenario(
            main_upside_drivers=["Semiconductor position"],
            evidence_gaps=["Forward guidance missing."],
        )
        d = p.to_dict()
        p2 = PortfolioScenario.from_dict(d)
        assert p2.portfolio_scenario_id == p.portfolio_scenario_id
        assert p2.main_upside_drivers == ["Semiconductor position"]
        assert p2.evidence_gaps == ["Forward guidance missing."]

    def test_safety_boundary_roundtrip(self):
        sb = ScenarioSafetyBoundary()
        d = sb.to_dict()
        sb2 = ScenarioSafetyBoundary.from_dict(d)
        assert sb2.no_single_point_targets is True
        assert sb2.change_triggers_required is True

    def test_full_review_roundtrip(self):
        r = _review("holding")
        d = r.to_dict()
        r2 = ValueScenarioReview.from_dict(d)
        assert r2.scenario_review_id == r.scenario_review_id
        assert r2.review_type == r.review_type
        assert len(r2.holding_scenarios) == 1

    def test_canonical_values_preserved_in_dict(self):
        r = _range()
        d = r.to_dict()
        assert d["horizon"] == "medium_term"
        assert d["case_type"] == "base"
        assert d["confidence"] == "unknown"
        assert d["evidence_quality"] == "incomplete"


# ---------------------------------------------------------------------------
# JSON round trip
# ---------------------------------------------------------------------------


class TestJsonRoundTrip:
    def test_scenario_range_json_roundtrip(self):
        r = _range(uncertainty_note="Wide range due to macro uncertainty.")
        text = r.to_json()
        r2 = ScenarioRange.from_json(text)
        assert r2.range_id == r.range_id
        assert r2.uncertainty_note == r.uncertainty_note

    def test_assumption_json_roundtrip(self):
        a = _assumption(description="Revenue grows 7–9% in the base case.")
        text = a.to_json()
        a2 = ScenarioAssumption.from_json(text)
        assert a2.description == a.description

    def test_full_review_json_roundtrip(self):
        r = _review("holding")
        text = r.to_json()
        r2 = ValueScenarioReview.from_json(text)
        assert r2.scenario_review_id == r.scenario_review_id

    def test_invalid_json_raises(self):
        with pytest.raises(ValueError, match="invalid JSON"):
            ScenarioRange.from_json("not json at all")

    def test_non_object_json_raises(self):
        with pytest.raises(ValueError, match="expected a JSON object"):
            ScenarioSubject.from_json("[1, 2, 3]")

    def test_json_output_is_valid_json(self):
        r = _review("holding")
        text = r.to_json()
        data = json.loads(text)
        assert data["scenario_review_id"] == "vsr_001"

    def test_portfolio_review_json_roundtrip(self):
        r = _review("portfolio")
        text = r.to_json()
        r2 = ValueScenarioReview.from_json(text)
        assert r2.portfolio_scenario is not None
        assert isinstance(r2.portfolio_scenario, PortfolioScenario)


# ---------------------------------------------------------------------------
# User-content preservation
# ---------------------------------------------------------------------------


class TestUserContentPreservation:
    def test_assumption_description_preserved(self):
        desc = 'User note: "Revenue grew 8% in Q2; base case assumes continuation."'
        a = _assumption(description=desc)
        assert a.description == desc
        assert ScenarioAssumption.from_dict(a.to_dict()).description == desc

    def test_evidence_description_preserved(self):
        desc = "Q2 earnings: margins at 22.8%, beat estimate by 0.4pp."
        e = _evidence_item(description=desc)
        assert e.description == desc

    def test_trigger_description_preserved(self):
        desc = "Watch Q3 gross margin — if below 21%, bear case becomes base case."
        t = _trigger(description=desc)
        assert t.description == desc

    def test_revision_reason_preserved(self):
        reason = "Evidence quality weakened after guidance withdrawal — range widened."
        r = _revision(reason=reason)
        assert r.reason == reason

    def test_holding_notes_preserved(self):
        note = 'User note: "Water infrastructure thesis needs more evidence before acting."'
        h = _holding_scenario(notes=note)
        assert h.notes == note

    def test_portfolio_concentration_note_preserved(self):
        note = "Semiconductor position exceeds 30% — portfolio range highly sensitive."
        p = _portfolio_scenario(concentration_sensitivity=note)
        assert p.concentration_sensitivity == note


# ---------------------------------------------------------------------------
# No calculations, no persistence, no runtime changes
# ---------------------------------------------------------------------------


class TestNoBehaviorChanges:
    def test_no_calculations_in_schema(self):
        src = Path("atlas/value_scenario/schema.py").read_text(encoding="utf-8")
        for forbidden in ["math.log", "numpy", "scipy", "pandas", "statistics.mean"]:
            assert forbidden not in src

    def test_no_file_writes_in_schema(self):
        src = Path("atlas/value_scenario/schema.py").read_text(encoding="utf-8")
        assert "open(" not in src
        assert "write_text" not in src
        assert "Path(" not in src

    def test_no_network_imports_in_schema(self):
        src = Path("atlas/value_scenario/schema.py").read_text(encoding="utf-8")
        for forbidden in ["requests", "httpx", "aiohttp", "urllib.request"]:
            assert forbidden not in src

    def test_no_ai_imports_in_schema(self):
        src = Path("atlas/value_scenario/schema.py").read_text(encoding="utf-8")
        for forbidden in ["openai", "anthropic", "langchain"]:
            assert forbidden not in src

    def test_cli_value_scenario_validate_command_present(self):
        cli_source = CLI_FILE.read_text(encoding="utf-8")
        assert "value_scenario_app" in cli_source
        assert 'name="value-scenario"' in cli_source
        assert '@value_scenario_app.command("validate")' in cli_source

    def test_schema_creates_no_files_on_import(self, tmp_path):
        files_before = set(tmp_path.iterdir())
        import atlas.value_scenario.schema  # noqa: F401
        files_after = set(tmp_path.iterdir())
        assert files_before == files_after
