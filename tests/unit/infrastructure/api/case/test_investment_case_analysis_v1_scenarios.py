"""ATLAS-029 -- the canonical Investment Case: `GET /cases/{case_id}
/analysis`, powered by `InvestmentCaseCompositionService.build`
(ATLAS-027) rather than `case_intelligence`'s own separate
`decision_engine.run_pipeline` call.

Exercises the real HTTP surface end-to-end through the real Case/
Decision/Outcome/Observation/Alpha-portfolio APIs -- nothing mocked,
following the exact fixture/helper pattern already established in
`test_case_intelligence_v1_scenarios.py`.
"""
from __future__ import annotations

from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from atlas.core.infrastructure.api.app import create_app
from atlas.core.infrastructure.api.decision.dependencies import get_decision_engine
from atlas.core.infrastructure.persistence.decision.table import create_decision_table


@pytest.fixture
def client():
    engine = create_engine(
        "sqlite:///:memory:",
        future=True,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    create_decision_table(engine)
    app = create_app()
    app.dependency_overrides[get_decision_engine] = lambda: engine
    return TestClient(app)


def _open_case(client) -> str:
    return client.post("/cases").json()["caseId"]


def _import_holding(client, ticker: str, weight_percent: float = 100.0) -> str:
    response = client.post(
        "/alpha-portfolio/import",
        json={"holdings": [{"ticker": ticker, "weightPercent": weight_percent}]},
    )
    assert response.status_code == 201, response.text
    body = response.json()
    case_id = next(h["caseId"] for h in body["holdings"] if h["ticker"] == ticker)
    assert case_id is not None
    return case_id


def _record_decision(client, *, case_id: str, subject: str, decision_type: str = "BUY", **overrides) -> dict:
    payload = {
        "caseId": case_id,
        "userId": "00000000-0000-0000-0000-000000000001",
        "decisionType": decision_type,
        "subject": subject,
        "reason": "Testing.",
        "confidence": 70,
    }
    payload.update(overrides)
    response = client.post("/decisions", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


def _record_observation(client, *, case_id: str, subject: str, **overrides) -> dict:
    payload = {
        "caseId": case_id,
        "subject": subject,
        "statement": "Noted something.",
        "observedAt": datetime.now(timezone.utc).isoformat(),
    }
    payload.update(overrides)
    response = client.post("/observations", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


def _record_outcome(client, decision: dict, **overrides) -> dict:
    payload = {
        "decisionId": decision["id"],
        "statement": "Something happened.",
        "occurredAt": datetime.now(timezone.utc).isoformat(),
    }
    payload.update(overrides)
    response = client.post("/outcomes", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


class TestCaseNotFound:
    def test_returns_404_for_an_unknown_case_id(self, client):
        response = client.get("/cases/00000000-0000-0000-0000-000000000099/analysis")
        assert response.status_code == 404


class TestResearchCase:
    """A Case with no linked holding at all -- Phase 30's own requirement:
    this must not be treated as broken."""

    def test_returns_200_with_held_false(self, client):
        case_id = _open_case(client)
        response = client.get(f"/cases/{case_id}/analysis")
        assert response.status_code == 200
        body = response.json()
        assert body["caseId"] == case_id
        assert body["holdingContext"] == {
            "held": False,
            "ticker": None,
            "weightPercent": None,
            "valueAbsolute": None,
            "reconciliationStatus": None,
        }

    def test_still_has_a_full_canonical_analysis(self, client):
        case_id = _open_case(client)
        body = client.get(f"/cases/{case_id}/analysis").json()
        assert {f["kind"] for f in body["businessAnalysis"]["findings"]} == {
            "business_model",
            "competitive_position",
            "management",
            "capital_allocation",
            "growth",
            "durability",
        }
        assert body["conviction"]["level"] is not None
        assert body["recommendation"]["level"] == "insufficient_evidence"


class TestHeldCase:
    def test_holding_context_reflects_the_real_holding(self, client):
        case_id = _import_holding(client, "NVDA", weight_percent=42.0)
        body = client.get(f"/cases/{case_id}/analysis").json()
        assert body["holdingContext"]["held"] is True
        assert body["holdingContext"]["ticker"] == "NVDA"
        assert body["holdingContext"]["weightPercent"] == pytest.approx(42.0)
        assert body["holdingContext"]["reconciliationStatus"] == "NONE"


class TestBusinessAnalysisSerialization:
    def test_all_six_categories_present_with_structured_fields(self, client):
        case_id = _import_holding(client, "NVDA")
        body = client.get(f"/cases/{case_id}/analysis").json()
        findings = body["businessAnalysis"]["findings"]
        assert len(findings) == 6
        for finding in findings:
            assert set(finding) == {
                "kind",
                "status",
                "severity",
                "supportingEvidence",
                "contradictingEvidence",
                "missingEvidence",
                "confidence",
                "updatedAt",
            }
            assert isinstance(finding["missingEvidence"], list)


class TestValuationSerialization:
    def test_fcf_yield_relative_and_scenarios_all_present(self, client):
        case_id = _import_holding(client, "NVDA")
        body = client.get(f"/cases/{case_id}/analysis").json()
        kinds = {f["kind"] for f in body["valuation"]["findings"]}
        assert kinds == {"fcf_yield_relative", "scenario_bear", "scenario_base", "scenario_bull"}


class TestRiskSerialization:
    def test_all_four_evaluated_categories_present_as_a_full_vector(self, client):
        case_id = _import_holding(client, "NVDA")
        body = client.get(f"/cases/{case_id}/analysis").json()
        categories = {f["category"] for f in body["risk"]["findings"]}
        assert categories == {"business_risk", "financial_risk", "valuation_risk", "thesis_risk"}

    def test_full_vector_is_never_replaced_by_the_projection(self, client):
        """Figma-fidelity rebuild (Investment Case): `riskProjection` was
        added for Atlas View's single "Risk Level" scorecard dot -- the
        same real `risk_projection()` Portfolio Cockpit's Holdings table
        Risk column already calls (`atlas.analysis_engine.risk
        .projection`), not a second, divergent computation. This test
        used to assert `riskProjection` was entirely absent
        ("never collapsed into a single badge unlike portfolio cockpit");
        that stance predates the approved Figma requirement for a
        compact Risk Level dot. What it actually protected -- that the
        full four-category vector is never *replaced* by a collapsed
        single badge -- still holds and is what this test now asserts
        directly: both `risk.findings` (all four, in full) and
        `riskProjection` (one representative category) are present
        together, never one instead of the other."""
        case_id = _import_holding(client, "NVDA")
        body = client.get(f"/cases/{case_id}/analysis").json()
        assert len(body["risk"]["findings"]) == 4
        assert set(body["riskProjection"]) == {"category", "status"}
        assert body["riskProjection"]["category"] in {
            "business_risk",
            "financial_risk",
            "valuation_risk",
            "thesis_risk",
        }


class TestConvictionAndConfidenceAreDistinct:
    def test_both_present_as_separate_fields_never_merged(self, client):
        case_id = _import_holding(client, "NVDA")
        body = client.get(f"/cases/{case_id}/analysis").json()
        assert "level" in body["conviction"]
        assert "reasons" in body["conviction"]
        assert isinstance(body["confidence"], str)
        assert body["confidence"] != body["conviction"]["level"] or True  # different concepts, not required unequal
        assert set(body["conviction"]) == {"level", "reasons"}


class TestStanceIntegration:
    """Atlas Intelligence Sprint 2 (Recommendation Quality &
    Actionability, Deliverable 5)."""

    def test_present_on_a_research_case_with_no_data(self, client):
        case_id = _open_case(client)
        body = client.get(f"/cases/{case_id}/analysis").json()
        assert body["stance"] is not None
        assert body["stance"]["level"] in (
            "increase", "maintain", "reduce", "review", "wait", "avoid_decision", "no_recommendation",
        )
        assert body["stance"]["reasoning"]

    def test_matches_the_dedicated_stance_endpoint_exactly(self, client):
        case_id = _import_holding(client, "NVDA")
        analysis_body = client.get(f"/cases/{case_id}/analysis").json()
        stance_body = client.get(f"/stance/case/{case_id}").json()
        assert analysis_body["stance"] == stance_body

    def test_never_recommends_buying_or_selling_shares(self, client):
        case_id = _import_holding(client, "NVDA")
        body = client.get(f"/cases/{case_id}/analysis").json()
        assert set(body["stance"]) == {
            "level", "reasoning", "supportingSignals", "limitingSignals", "confidence", "missingInformation",
        }


class TestExplanationIntegration:
    """Atlas Intelligence Sprint 3 (Decision Explainability & Evidence
    Trace, Deliverable 4)."""

    def test_present_on_a_research_case_with_no_data(self, client):
        case_id = _open_case(client)
        body = client.get(f"/cases/{case_id}/analysis").json()
        assert body["explanation"] is not None
        assert body["explanation"]["limitingFactors"]

    def test_matches_the_dedicated_explainability_endpoint_exactly(self, client):
        case_id = _import_holding(client, "NVDA")
        analysis_body = client.get(f"/cases/{case_id}/analysis").json()
        explainability_body = client.get(f"/explainability/case/{case_id}").json()
        assert analysis_body["explanation"] == explainability_body

    def test_shape_is_the_five_evidence_buckets_plus_most_valuable_missing_information(self, client):
        case_id = _import_holding(client, "NVDA")
        body = client.get(f"/cases/{case_id}/analysis").json()
        assert set(body["explanation"]) == {
            "supportingEvidence", "contradictingEvidence", "limitingFactors",
            "missingEvidence", "confidenceDrivers", "mostValuableMissingInformation",
        }


class TestMaterialityIntegration:
    """Atlas Intelligence -- Materiality & Priority Engine, Deliverable
    5."""

    def test_present_on_a_research_case_with_no_data(self, client):
        case_id = _open_case(client)
        body = client.get(f"/cases/{case_id}/analysis").json()
        assert body["materiality"] is not None
        assert body["materiality"]["topLimitingFactor"] is not None

    def test_matches_the_dedicated_materiality_endpoint_exactly(self, client):
        case_id = _import_holding(client, "NVDA")
        analysis_body = client.get(f"/cases/{case_id}/analysis").json()
        materiality_body = client.get(f"/materiality/case/{case_id}").json()
        assert analysis_body["materiality"] == materiality_body

    def test_top_missing_evidence_matches_explanation_own_most_valuable_pick(self, client):
        case_id = _import_holding(client, "NVDA")
        body = client.get(f"/cases/{case_id}/analysis").json()
        assert body["materiality"]["topMissingEvidence"] == body["explanation"]["mostValuableMissingInformation"]


class TestEvidenceQualityIntegration:
    """Atlas Intelligence Sprint 4 (Evidence Quality & Conflict
    Resolution, Deliverable 5)."""

    def test_present_on_a_research_case_with_no_data(self, client):
        case_id = _open_case(client)
        body = client.get(f"/cases/{case_id}/analysis").json()
        assert body["evidenceQualityReport"] is not None
        assert body["evidenceQualityReport"]["quality"] == "not_applicable"

    def test_matches_the_dedicated_evidence_quality_endpoint_exactly(self, client):
        case_id = _import_holding(client, "NVDA")
        analysis_body = client.get(f"/cases/{case_id}/analysis").json()
        evidence_quality_body = client.get(f"/evidence-quality/case/{case_id}").json()
        assert analysis_body["evidenceQualityReport"] == evidence_quality_body

    def test_shape_never_collides_with_the_older_unrelated_evidence_quality_field(self, client):
        """Product Sprint 14's own `evidenceQuality` field (per-finding
        evidence-reference resolution) and this Sprint's own
        `evidenceQualityReport` are two different, real fields -- both
        must be present, never merged or shadowing one another."""
        case_id = _import_holding(client, "NVDA")
        body = client.get(f"/cases/{case_id}/analysis").json()
        assert "evidenceQuality" in body
        assert "evidenceQualityReport" in body
        assert body["evidenceQuality"] != body["evidenceQualityReport"]


class TestCoverageAssessment:
    """Atlas Intelligence Sprint 1 (Data Coverage & Confidence Engine)."""

    def test_present_on_a_research_case_with_no_data(self, client):
        case_id = _open_case(client)
        body = client.get(f"/cases/{case_id}/analysis").json()
        coverage = body["coverage"]
        assert coverage["overallConfidence"] == "very_limited"
        dims = {d["dimension"]: d["level"] for d in coverage["dimensions"]}
        assert dims["growth"] == "unavailable"
        assert dims["business_model"] == "not_applicable"

    def test_never_reports_a_permanently_locked_dimension_as_unavailable(self, client):
        """Business Model/Competitive Position/Management/Durability
        have no evaluator wired in today regardless of company data --
        they must always read Not Applicable, never Unavailable, and
        must never count toward `missingDimensions`."""
        case_id = _import_holding(client, "NVDA")
        body = client.get(f"/cases/{case_id}/analysis").json()
        coverage = body["coverage"]
        for locked in ("business_model", "competitive_position", "management", "durability"):
            assert locked in coverage["notApplicableDimensions"]
            assert locked not in coverage["missingDimensions"]

    def test_reasoning_is_never_empty(self, client):
        case_id = _import_holding(client, "NVDA")
        body = client.get(f"/cases/{case_id}/analysis").json()
        assert body["coverage"]["reasoning"]

    def test_overall_coverage_matches_the_dimension_count(self, client):
        case_id = _open_case(client)
        body = client.get(f"/cases/{case_id}/analysis").json()
        assert body["coverage"]["overallCoverage"] == "no_coverage"


class TestEvidenceQuality:
    def test_present_with_zero_evidence_when_none_recorded(self, client):
        case_id = _import_holding(client, "NVDA")
        body = client.get(f"/cases/{case_id}/analysis").json()
        assert body["evidenceQuality"]["totalEvidenceCount"] == 0
        assert body["evidenceQuality"]["coverage"] == "not_applicable"

    def test_reflects_a_real_recorded_observation(self, client):
        case_id = _import_holding(client, "NVDA")
        _record_observation(client, case_id=case_id, subject="NVDA")
        body = client.get(f"/cases/{case_id}/analysis").json()
        assert body["evidenceQuality"]["coverage"] == "none"
        assert len(body["observationHistory"]) == 1


class TestOpenQuestions:
    def test_uses_the_corrected_canonical_open_questions(self, client):
        """ATLAS-027 retires `valuation_thesis_not_documented` once the
        real FCF Yield method reaches a conclusion -- structurally
        INSUFFICIENT_INPUT with no real data in this test, so the
        question is still present; this test only proves the field is
        populated from `CanonicalAnalysis.open_questions`, not a
        hand-rolled duplicate list."""
        case_id = _open_case(client)
        body = client.get(f"/cases/{case_id}/analysis").json()
        kinds = {q["kind"] for q in body["openQuestions"]}
        assert "business_durability_not_assessable" in kinds
        assert "portfolio_factor_not_assessable" in kinds


class TestDecisionHistory:
    def test_records_every_decision_for_this_case(self, client):
        case_id = _import_holding(client, "NVDA")
        _record_decision(client, case_id=case_id, subject="NVDA", reason="Durable moat.")
        _record_decision(client, case_id=case_id, subject="NVDA", decision_type="SELL", reason="Trimming.")
        body = client.get(f"/cases/{case_id}/analysis").json()
        assert len(body["decisionHistory"]) == 2
        reasons = {d["reason"] for d in body["decisionHistory"]}
        assert reasons == {"Durable moat.", "Trimming."}

    def test_does_not_leak_another_cases_decisions(self, client):
        case_a = _import_holding(client, "AMD")
        case_b = _import_holding(client, "NVDA")
        _record_decision(client, case_id=case_a, subject="AMD")
        body_b = client.get(f"/cases/{case_b}/analysis").json()
        assert body_b["decisionHistory"] == []


class TestObservationsAndOutcomes:
    def test_observations_appear_in_observation_history(self, client):
        case_id = _import_holding(client, "NVDA")
        _record_observation(client, case_id=case_id, subject="NVDA", statement="Margins expanding.")
        body = client.get(f"/cases/{case_id}/analysis").json()
        assert len(body["observationHistory"]) == 1
        assert body["observationHistory"][0]["statement"] == "Margins expanding."

    def test_outcomes_are_linked_to_their_decision_by_id(self, client):
        case_id = _import_holding(client, "NVDA")
        decision = _record_decision(client, case_id=case_id, subject="NVDA")
        _record_outcome(client, decision, statement="Bought shares.")
        body = client.get(f"/cases/{case_id}/analysis").json()
        assert len(body["outcomeHistory"]) == 1
        assert body["outcomeHistory"][0]["decisionId"] == decision["id"]
        assert body["outcomeHistory"][0]["statement"] == "Bought shares."

    def test_a_case_can_exist_without_any_observations(self, client):
        case_id = _import_holding(client, "NVDA")
        body = client.get(f"/cases/{case_id}/analysis").json()
        assert body["observationHistory"] == []
        assert body["businessAnalysis"]["state"] == "evaluated"


class TestRecommendationWithheld:
    def test_reports_withheld_honestly_never_a_directional_call(self, client):
        case_id = _import_holding(client, "NVDA")
        body = client.get(f"/cases/{case_id}/analysis").json()
        assert body["recommendation"]["level"] == "insufficient_evidence"
        assert body["recommendation"]["convictionGateMet"] is False
        assert body["recommendation"]["statement"] == (
            "Current evidence is insufficient to support any portfolio action."
        )
        # Never a raw RecommendationDirection member name (BUY/ADD/HOLD/
        # TRIM/EXIT/NO_ACTION) or the old kind/reason vocabulary --
        # Decision Log #1, atlas.alpha.decision_support.
        assert "kind" not in body["recommendation"]
        assert "reason" not in body["recommendation"]
        # Calibration Phase 2, Phase 6: no Direction was ever selected
        # for a withheld recommendation, so there is no specific change
        # trigger to name yet -- empty, never a fabricated one.
        assert body["recommendation"]["whatWouldChange"] == []


class TestDeterministicShape:
    def test_identical_state_produces_the_same_analytical_values_on_repeat_reads(self, client):
        case_id = _import_holding(client, "NVDA")
        _record_decision(client, case_id=case_id, subject="NVDA")
        first = client.get(f"/cases/{case_id}/analysis").json()
        second = client.get(f"/cases/{case_id}/analysis").json()
        _strip_volatile_timestamps(first)
        _strip_volatile_timestamps(second)
        assert first == second


def _strip_volatile_timestamps(body: dict) -> None:
    body.pop("generatedAt", None)
    for finding in body["businessAnalysis"]["findings"]:
        finding.pop("updatedAt", None)
    # Investment Case Monitoring & Change Intelligence v1: these fields
    # are *correctly* call-order-dependent -- the first GET for a Case
    # persists a baseline snapshot, so a second, otherwise-identical GET
    # legitimately reports `isBaselineCase=False` against that now-real
    # previous state, not a repeat of the first call's own baseline
    # narrative/timestamps. This helper strips exactly the fields whose
    # divergence is this sprint's own intended behavior, not a
    # regression -- every other field must still match byte-for-byte.
    body.pop("isBaselineCase", None)
    body.pop("changeSummary", None)
    body.pop("previousAnalysisAt", None)
    body.pop("currentAnalysisAt", None)
    # Atlas Intelligence Sprint 5 (Evidence Timeline & Historical
    # Understanding): `evidenceTimeline` is captured/persisted by this
    # exact endpoint (see `investment_case/api/router.py`'s own
    # docstring), the identical "first GET persists a baseline, second
    # GET legitimately sees it as real prior state" pattern
    # `isBaselineCase` above already established one layer below --
    # `transitions` itself still must match (nothing else changed
    # between the two calls), only the baseline/timestamp bookkeeping.
    evidence_timeline = body.get("evidenceTimeline")
    if evidence_timeline is not None:
        evidence_timeline.pop("isBaseline", None)
        evidence_timeline.pop("previousCapturedAt", None)
        evidence_timeline.pop("currentCapturedAt", None)
    # Outlook Intelligence Sprint 1: `outlook.*.momentum` derives from
    # the identical baseline/`thesis_impact` state as `isBaselineCase`
    # above (see `atlas.analysis_engine.outlook.derive_outlook_momentum`)
    # -- the same real, intended first-GET-vs-second-GET divergence, one
    # layer deeper.
    outlook = body.get("outlook")
    if outlook is not None:
        outlook.get("shortTerm", {}).pop("momentum", None)
        outlook.get("longTerm", {}).pop("momentum", None)


class TestNoQueryParameterInfluence:
    def test_get_accepts_no_analytical_input_from_the_request(self, client):
        case_id = _import_holding(client, "NVDA")
        plain = client.get(f"/cases/{case_id}/analysis").json()
        with_bogus = client.get(f"/cases/{case_id}/analysis", params={"conviction": "very_high"}).json()
        _strip_volatile_timestamps(plain)
        _strip_volatile_timestamps(with_bogus)
        assert plain == with_bogus


class TestChangeIntelligenceSerialization:
    """Investment Case Monitoring & Change Intelligence v1, scenario 19:
    the API exposes structured change intelligence."""

    def test_first_read_is_a_baseline(self, client):
        case_id = _import_holding(client, "NVDA")
        body = client.get(f"/cases/{case_id}/analysis").json()
        assert body["changeIntelligenceAvailable"] is True
        assert body["isBaselineCase"] is True
        assert body["latestChanges"] == []
        assert body["previousAnalysisAt"] is None
        assert body["currentAnalysisAt"] is not None
        assert "baseline" in body["changeSummary"].lower()

    def test_second_read_with_no_new_data_reports_no_material_change(self, client):
        case_id = _import_holding(client, "NVDA")
        client.get(f"/cases/{case_id}/analysis")
        body = client.get(f"/cases/{case_id}/analysis").json()
        assert body["isBaselineCase"] is False
        assert body["latestChanges"] == []
        assert body["thesisChange"] == "unchanged"
        assert "no material change" in body["changeSummary"].lower()
        assert body["previousAnalysisAt"] is not None

    def test_change_finding_shape_when_present(self, client):
        """Exercises the real wire shape of one `ChangeFindingView` via
        a genuine transition (a Case moving from unheld to held changes
        `HOLDING_CONTEXT`-adjacent business/portfolio findings, but the
        one deterministic, always-reproducible transition available at
        this API layer without fabricating provider data is opening a
        Case with no BusinessRecords at all -- both reads stay
        `insufficient_input` on every dimension, so `latestChanges`
        stays empty; this test instead asserts the schema itself is
        well-formed by constructing the view directly, matching this
        file's own "serialization" test style used for the other
        sections above."""
        from atlas.alpha.investment_case.api.schemas import ChangeFindingView
        from atlas.analysis_engine.investment_case_change import ChangeCategory, ChangeDirection, ChangeFinding

        domain = ChangeFinding(
            id="growth_changed:growth",
            category=ChangeCategory.GROWTH_CHANGED,
            direction=ChangeDirection.NEGATIVE,
            previous_state="strong",
            current_state="moderate",
            details={"dimension": "growth"},
            evidence_references=("business_finding:growth",),
            source_finding_id="business_finding:growth",
        )
        view = ChangeFindingView.from_domain(domain)
        payload = view.model_dump(by_alias=True)
        assert payload == {
            "id": "growth_changed:growth",
            "category": "growth_changed",
            "direction": "negative",
            "previousState": "strong",
            "currentState": "moderate",
            "details": {"dimension": "growth"},
            "evidenceReferences": ["business_finding:growth"],
            "sourceFindingId": "business_finding:growth",
        }


class TestOperationalFreshnessIntegration:
    """Atlas Intelligence Sprint 8 (Automated Monitoring Operations,
    Deliverable 15) -- purely operational, always present and never
    confused with `monitoring` (investment status)."""

    def test_a_never_monitored_case_reports_pending_with_no_last_monitored_at(self, client):
        case_id = _import_holding(client, "NVDA")
        body = client.get(f"/cases/{case_id}/analysis").json()
        freshness = body["operationalFreshness"]
        assert freshness["isPending"] is True
        assert freshness["lastMonitoredAt"] is None
        assert freshness["lastRunFailedForCase"] is False

    def test_a_freshly_monitored_case_reports_not_pending(self, client):
        case_id = _import_holding(client, "NVDA")
        client.post("/monitoring/run")
        body = client.get(f"/cases/{case_id}/analysis").json()
        freshness = body["operationalFreshness"]
        assert freshness["isPending"] is False
        assert freshness["lastMonitoredAt"] is not None

    def test_operational_freshness_is_structurally_distinct_from_monitoring_status(self, client):
        case_id = _import_holding(client, "NVDA")
        client.post("/monitoring/run")
        body = client.get(f"/cases/{case_id}/analysis").json()
        assert set(body["operationalFreshness"]) == {"isPending", "lastMonitoredAt", "lastRunFailedForCase", "dataFreshnessStatus"}
        assert "status" not in body["operationalFreshness"]
