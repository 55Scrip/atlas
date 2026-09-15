"""fiscal_epoch_v3: every fiscal epoch priced on the issuer basis, over the
free cash flow attributable to common equity -- and withheld, with its reason,
whenever the basis cannot price it. Never priced on the retired proxy."""
from __future__ import annotations

from dataclasses import replace
from datetime import date

import pytest

from atlas.analysis_engine.exceptions import AnalysisEngineContractError
from atlas.analysis_engine.methodology import ANALYSIS_METHODOLOGY
from atlas.analysis_engine.valuation import cash_flow
from atlas.analysis_engine.valuation.cash_flow import (
    FCF_YIELD_METHODOLOGY,
    FISCAL_EPOCH_V2,
    VALUATION_METHODOLOGY,
    evaluate_fcf_yield_relative,
    evaluate_fcf_yield_relative_v2,
    fiscal_epochs,
)
from atlas.analysis_engine.valuation.contracts import (
    HistoricalYieldPosition as P,
    ShareCountMethod,
    ValuationDataGapKind as G,
    ValuationDecisionEligibility as E,
    ValuationStatus,
)
from atlas.analysis_engine.valuation.issuer_basis import (
    COMMON_FCF_NUMERATOR_METHODOLOGY,
    ISSUER_MARKET_CAP_METHODOLOGY,
    NCI_TREATMENT,
    EpochDenominator,
    IssuerDenominatorQuality as Q,
    IssuerMarketCap,
    IssuerValuationBasis,
    SeniorClaim,
)
from atlas.analysis_engine.valuation.models import FcfYieldEpochObservation
from tests.unit.analysis_engine.valuation._epochs import APPLICABLE, AS_OF, annual_history
from tests.unit.analysis_engine.valuation._issuer_basis import basis_for_epochs


def _facts(fcf=None, prices=None):
    fcf = fcf or {2021: 100.0, 2022: 100.0, 2023: 100.0, 2024: 100.0, 2025: 100.0}
    prices = prices or {2021: 10.0, 2022: 20.0, 2023: 25.0, 2024: 40.0, 2025: 50.0}
    return annual_history(fcf, prices)


def _statements(business):
    return frozenset(f.source_record_id for f in business if f.source_record_id.startswith("stmt-"))


def _epochs(business, market):
    return fiscal_epochs(tuple(business), tuple(market), statement_record_ids=_statements(business),
                         industry=APPLICABLE, evaluated_at=AS_OF)


def _evaluate(business, market, basis):
    return evaluate_fcf_yield_relative(tuple(business), tuple(market), statement_record_ids=_statements(business),
                                       industry=APPLICABLE, evaluated_at=AS_OF, basis=basis)


class TestMethodologyIdentity:
    def test_the_active_construction_is_fiscal_epoch_v3_with_its_numerator_and_denominator(self):
        assert FCF_YIELD_METHODOLOGY == "fiscal_epoch_v3"
        assert FISCAL_EPOCH_V2 == "fiscal_epoch_v2"
        assert COMMON_FCF_NUMERATOR_METHODOLOGY == "common_attributable_fcf_v1"
        assert ISSUER_MARKET_CAP_METHODOLOGY == "issuer_common_equity_market_cap_v1"
        assert VALUATION_METHODOLOGY == "fiscal_epoch_v3+issuer_common_equity_market_cap_v1+common_attributable_fcf_v1"
        assert f"valuation={VALUATION_METHODOLOGY}" in ANALYSIS_METHODOLOGY

    def test_production_evidence_is_priced_on_the_issuer_basis(self):
        business, market = _facts()
        finding = _evaluate(business, market, basis_for_epochs(_epochs(business, market)))
        evidence = finding.fcf_yield_evidence
        assert cash_flow.SHARE_COUNT_METHOD is ShareCountMethod.ISSUER_COMMON_EQUITY_MARKET_CAP
        assert evidence.share_count_method is ShareCountMethod.ISSUER_COMMON_EQUITY_MARKET_CAP
        assert evidence.numerator_method == COMMON_FCF_NUMERATOR_METHODOLOGY
        assert evidence.nci_treatment == NCI_TREATMENT == "unmeasured"
        assert all(e.is_issuer_basis for e in (evidence.current, *evidence.prior_epochs))


class TestNoFallback:
    def test_without_a_basis_the_valuation_is_withheld_never_priced_on_the_proxy(self):
        business, market = _facts()
        v2 = evaluate_fcf_yield_relative_v2(tuple(business), tuple(market), statement_record_ids=_statements(business),
                                            industry=APPLICABLE, evaluated_at=AS_OF)
        assert v2.status is ValuationStatus.EXPENSIVE  # the retired proxy would have classified
        finding = _evaluate(business, market, None)
        assert finding.status is ValuationStatus.INSUFFICIENT_INPUT
        assert finding.fcf_yield_evidence.withheld_reasons == (G.DENOMINATOR_EVIDENCE_MISSING,)
        assert finding.current_yield is None and finding.fcf_yield_evidence.prior_epochs == ()

    def test_an_epoch_the_basis_cannot_price_is_left_out_not_proxy_priced(self):
        business, market = _facts()
        basis = basis_for_epochs(_epochs(business, market))
        first = basis.epochs[0]
        basis = replace(basis, epochs=(EpochDenominator(first.fiscal_period, first.observed_on,
                                                        gap=G.DENOMINATOR_EVIDENCE_MISSING), *basis.epochs[1:]))
        evidence = _evaluate(business, market, basis).fcf_yield_evidence
        assert [e.fiscal_period for e in evidence.prior_epochs] == ["2022-12-31", "2023-12-31", "2024-12-31"]
        assert evidence.eligibility is E.ELIGIBLE

    def test_production_code_never_calls_the_retired_construction(self):
        import pathlib

        root = pathlib.Path(__file__).resolve().parents[4] / "atlas"
        callers = sorted(str(p.relative_to(root.parent)) for p in root.rglob("*.py")
                         if "evaluate_fcf_yield_relative_v2" in p.read_text())
        assert callers == ["atlas/analysis_engine/valuation/cash_flow.py"]


class TestIssuerDenominator:
    def test_exact_single_class_matches_its_own_price_times_count(self):
        business, market = _facts()
        finding = _evaluate(business, market, basis_for_epochs(_epochs(business, market)))
        assert finding.status is ValuationStatus.EXPENSIVE
        assert finding.current_yield == pytest.approx(100.0 / (50.0 * 100.0))

    def test_multi_class_issuer_cap_replaces_the_security_cap(self):
        business, market = _facts()
        epochs = _epochs(business, market)
        basis = basis_for_epochs(epochs)
        # the issuer has a second class worth as much as this listing, today only
        doubled = replace(basis.current, market_cap_low=basis.current.market_cap_low * 2,
                          market_cap_high=basis.current.market_cap_high * 2)
        finding = _evaluate(business, market, replace(basis, current=doubled))
        assert finding.current_yield == pytest.approx(100.0 / (50.0 * 100.0 * 2))

    def test_bounded_denominator_classifies_only_when_both_ends_agree(self):
        business, market = _facts()
        epochs = _epochs(business, market)
        agree = _evaluate(business, market, basis_for_epochs(epochs, current_scale=(0.99, 1.01)))
        assert agree.status is ValuationStatus.EXPENSIVE
        cur = agree.fcf_yield_evidence.current
        assert cur.fcf_yield_low == pytest.approx(100.0 / (5000.0 * 1.01))
        assert cur.fcf_yield_high == pytest.approx(100.0 / (5000.0 * 0.99))
        assert cur.fcf_yield_low < cur.fcf_yield < cur.fcf_yield_high
        # a current interval reaching into the prior range: the two ends disagree
        split = _evaluate(business, market, basis_for_epochs(epochs, current_scale=(0.5, 1.0)))
        assert split.status is ValuationStatus.INSUFFICIENT_INPUT
        assert split.fcf_yield_evidence.withheld_reasons == (G.BOUNDED_DENOMINATOR_DISAGREEMENT,)
        assert G.BOUNDED_DENOMINATOR_DISAGREEMENT in split.missing_evidence

    def test_market_cap_bounds_are_ordered(self):
        with pytest.raises(AnalysisEngineContractError):
            IssuerMarketCap(date(2026, 1, 2), 10.0, 200.0, 100.0, Q.BOUNDED, "USD")
        with pytest.raises(AnalysisEngineContractError):
            IssuerMarketCap(date(2026, 1, 2), 10.0, 100.0, 200.0, Q.EXACT, "USD")


class TestStrictCurrentTiming:
    def test_a_composition_from_another_date_is_not_current(self):
        business, market = _facts()
        basis = basis_for_epochs(_epochs(business, market))
        stale = replace(basis.current, economic_date=basis.current.economic_date.replace(month=1, day=2))
        finding = _evaluate(business, market, replace(basis, current=stale))
        assert finding.status is ValuationStatus.INSUFFICIENT_INPUT
        assert finding.fcf_yield_evidence.withheld_reasons == (G.CURRENT_ISSUER_PRICE_NOT_SYNCHRONIZED,)
        assert finding.current_yield is None

    def test_the_builders_reason_is_carried(self):
        business, market = _facts()
        basis = replace(basis_for_epochs(_epochs(business, market)), current=None,
                        current_gap=G.CURRENT_ISSUER_PRICE_NOT_SYNCHRONIZED)
        evidence = _evaluate(business, market, basis).fcf_yield_evidence
        assert evidence.withheld_reasons == (G.CURRENT_ISSUER_PRICE_NOT_SYNCHRONIZED,)
        assert len(evidence.prior_epochs) == 4  # history is still described

    def test_a_prior_denominator_from_another_date_is_a_temporal_gap(self):
        business, market = _facts()
        basis = basis_for_epochs(_epochs(business, market))
        e = basis.epochs[0]
        moved = EpochDenominator(e.fiscal_period, e.observed_on,
                                 replace(e.market_cap, economic_date=e.market_cap.economic_date.replace(day=1)))
        evidence = _evaluate(business, market, replace(basis, epochs=(moved, *basis.epochs[1:]))).fcf_yield_evidence
        assert "2021-12-31" not in [p.fiscal_period for p in evidence.prior_epochs]


class TestCommonAttributableNumerator:
    def test_senior_claims_are_deducted_at_the_middle_of_their_interval(self):
        business, market = _facts()
        basis = basis_for_epochs(_epochs(business, market), claims={"2025-12-31": (10.0, 12.0)})
        current = _evaluate(business, market, basis).fcf_yield_evidence.current
        assert current.raw_free_cash_flow == 100.0
        assert current.free_cash_flow == pytest.approx(89.0)
        assert current.fcf_yield_low == pytest.approx(88.0 / 5000.0)
        assert current.fcf_yield_high == pytest.approx(90.0 / 5000.0)

    def test_a_claim_names_only_its_own_fiscal_year(self):
        business, market = _facts()
        basis = basis_for_epochs(_epochs(business, market), claims={"2025-12-31": (10.0, 10.0)})
        evidence = _evaluate(business, market, basis).fcf_yield_evidence
        assert all(e.free_cash_flow == e.raw_free_cash_flow == 100.0 for e in evidence.prior_epochs)

    def test_an_unquantified_claim_withholds_the_current_numerator(self):
        business, market = _facts()
        basis = replace(basis_for_epochs(_epochs(business, market)), unquantified_claims=("2025-12-31",))
        finding = _evaluate(business, market, basis)
        assert finding.fcf_yield_evidence.withheld_reasons == (G.NUMERATOR_EVIDENCE_MISSING,)
        assert finding.status is ValuationStatus.INSUFFICIENT_INPUT

    def test_an_unquantified_prior_claim_drops_only_that_epoch(self):
        business, market = _facts()
        basis = replace(basis_for_epochs(_epochs(business, market)), unquantified_claims=("2022-12-31",))
        evidence = _evaluate(business, market, basis).fcf_yield_evidence
        assert [e.fiscal_period for e in evidence.prior_epochs] == ["2021-12-31", "2023-12-31", "2024-12-31"]

    def test_a_claim_consuming_the_whole_free_cash_flow_withholds(self):
        business, market = _facts()
        basis = basis_for_epochs(_epochs(business, market), claims={"2025-12-31": (90.0, 100.0)})
        finding = _evaluate(business, market, basis)
        assert finding.fcf_yield_evidence.withheld_reasons == (G.CASH_FLOW_NOT_POSITIVE,)

    def test_the_epoch_contract_refuses_a_raw_figure_labelled_common(self):
        business, market = _facts()
        current = _evaluate(business, market, basis_for_epochs(
            _epochs(business, market), claims={"2025-12-31": (10.0, 10.0)})).fcf_yield_evidence.current
        with pytest.raises(AnalysisEngineContractError):
            replace(current, free_cash_flow=current.raw_free_cash_flow)


class TestHistoryAndMultipleBlockers:
    def test_minimum_history_is_unchanged(self):
        business, market = _facts(prices={2023: 25.0, 2024: 40.0, 2025: 50.0})
        finding = _evaluate(business, market, basis_for_epochs(_epochs(business, market)))
        assert finding.fcf_yield_evidence.eligibility is E.LIMITED
        assert finding.missing_evidence == (G.INSUFFICIENT_HISTORICAL_VALUATION_PERIODS,)

    def test_every_blocker_is_named(self):
        business, market = _facts(prices={2024: 40.0, 2025: 50.0})
        basis = replace(basis_for_epochs(_epochs(business, market)), current=None,
                        current_gap=G.DENOMINATOR_EVIDENCE_MISSING)
        finding = _evaluate(business, market, basis)
        assert finding.missing_evidence == (G.DENOMINATOR_EVIDENCE_MISSING, G.INSUFFICIENT_HISTORICAL_VALUATION_PERIODS)

    def test_a_withheld_valuation_never_classifies(self):
        business, market = _facts()
        basis = replace(basis_for_epochs(_epochs(business, market)), current=None,
                        current_gap=G.DENOMINATOR_EVIDENCE_MISSING)
        evidence = _evaluate(business, market, basis).fcf_yield_evidence
        assert evidence.position is None and evidence.decision_status is ValuationStatus.INSUFFICIENT_INPUT


class TestEpochContract:
    def _epoch(self, **kw):
        base = dict(fiscal_period="2025-12-31", available_from=date(2026, 2, 14), observed_on="2026-03-02",
                    free_cash_flow=90.0, share_price=10.0, shares_outstanding=100.0, currency="USD",
                    free_cash_flow_fact_id="f", share_price_fact_id="p", shares_outstanding_fact_id=None,
                    market_cap_low=1000.0, market_cap_high=1000.0, raw_free_cash_flow=100.0,
                    senior_claim_low=10.0, senior_claim_high=10.0, denominator_quality="issuer_exact")
        base.update(kw)
        return FcfYieldEpochObservation(**base)

    def test_issuer_basis_epoch_yield_is_common_fcf_over_issuer_cap(self):
        assert self._epoch().fcf_yield == pytest.approx(0.09)

    def test_inverted_bounds_are_refused(self):
        with pytest.raises(AnalysisEngineContractError):
            self._epoch(market_cap_low=1200.0, market_cap_high=1000.0)

    def test_shares_are_the_issuer_cap_in_this_securitys_price(self):
        with pytest.raises(AnalysisEngineContractError):
            self._epoch(shares_outstanding=90.0)  # a claim folded into the denominator

    def test_provider_share_count_is_not_named_on_an_issuer_epoch(self):
        with pytest.raises(AnalysisEngineContractError):
            self._epoch(shares_outstanding_fact_id="s")

    def test_mixed_bases_are_refused(self):
        business, market = _facts()
        evidence = _evaluate(business, market, basis_for_epochs(_epochs(business, market))).fcf_yield_evidence
        proxy = _epochs(business, market).prior_epochs[0]
        with pytest.raises(AnalysisEngineContractError):
            replace(evidence, prior_epochs=(proxy, *evidence.prior_epochs[1:]))


class TestDeterminism:
    def test_input_order_never_matters(self):
        business, market = _facts()
        basis = basis_for_epochs(_epochs(business, market), claims={"2024-12-31": (1.0, 2.0)})
        a = _evaluate(business, market, basis)
        b = _evaluate(list(reversed(business)), list(reversed(market)),
                      replace(basis, epochs=tuple(reversed(basis.epochs))))
        assert a == b


class TestWithheldCasesNeverFallBack:
    """The withheld shapes of the corpus: each withheld, none proxy-priced."""

    def _withheld_current(self, prices, gap=G.DENOMINATOR_EVIDENCE_MISSING):
        business, market = _facts(prices=prices)
        basis = replace(basis_for_epochs(_epochs(business, market)), current=None, current_gap=gap)
        return _evaluate(business, market, basis)

    def test_denominator_missing_with_full_history(self):  # AMD
        f = self._withheld_current(None)
        assert f.status is ValuationStatus.INSUFFICIENT_INPUT and f.current_yield is None
        assert f.missing_evidence == (G.DENOMINATOR_EVIDENCE_MISSING,)
        assert len(f.fcf_yield_evidence.prior_epochs) == 4

    def test_denominator_missing_and_no_history(self):  # CRWD, MCO
        f = self._withheld_current({2025: 50.0})
        assert f.missing_evidence == (G.DENOMINATOR_EVIDENCE_MISSING, G.INSUFFICIENT_HISTORICAL_VALUATION_PERIODS)

    def test_valid_current_and_no_history(self):  # META
        business, market = _facts(prices={2025: 50.0})
        f = _evaluate(business, market, basis_for_epochs(_epochs(business, market)))
        assert f.status is ValuationStatus.INSUFFICIENT_INPUT
        assert f.fcf_yield_evidence.current.is_issuer_basis and f.fcf_yield_evidence.prior_epochs == ()
        assert f.missing_evidence == (G.INSUFFICIENT_HISTORICAL_VALUATION_PERIODS,)

    def test_two_priors_describe_but_never_classify(self):  # AMZN, DE
        business, market = _facts(prices={2023: 25.0, 2024: 40.0, 2025: 50.0})
        f = _evaluate(business, market, basis_for_epochs(_epochs(business, market)))
        assert f.fcf_yield_evidence.position is P.BELOW_ALL_PRIOR and f.status is ValuationStatus.INSUFFICIENT_INPUT
        evidence = f.fcf_yield_evidence  # described on the issuer basis, never the proxy
        assert evidence.share_count_method is ShareCountMethod.ISSUER_COMMON_EQUITY_MARKET_CAP
        assert all(e.is_issuer_basis for e in (evidence.current, *evidence.prior_epochs))


class TestProductionPipeline:
    def test_evaluate_valuation_prices_on_the_basis_it_is_given(self):
        from atlas.analysis_engine.valuation.pipeline import evaluate_valuation

        business, market = _facts()
        epochs = _epochs(business, market)
        basis = basis_for_epochs(epochs)
        doubled = replace(basis, current=replace(basis.current, market_cap_low=basis.current.market_cap_low * 2,
                                                 market_cap_high=basis.current.market_cap_high * 2))
        result = evaluate_valuation(tuple(business), tuple(market), statement_record_ids=_statements(business),
                                    industry=APPLICABLE, evaluated_at=AS_OF, valuation_basis=doubled)
        fcf = next(f for f in result.findings if f.fcf_yield_evidence is not None)
        assert fcf.fcf_yield_evidence.share_count_method is ShareCountMethod.ISSUER_COMMON_EQUITY_MARKET_CAP
        assert fcf.current_yield == pytest.approx(100.0 / 10_000.0)


class TestNoTickerLogic:
    def test_no_v3_module_names_a_ticker_or_an_issuer(self):
        import ast
        import pathlib

        root = pathlib.Path(__file__).resolve().parents[4] / "atlas"
        modules = ["analysis_engine/valuation/cash_flow.py", "analysis_engine/valuation/issuer_basis.py",
                   "alpha/issuer_equity/claims.py", "alpha/issuer_equity/valuation_basis.py",
                   "alpha/class_rights_evidence/series_terms.py", "alpha/issuer_equity/reader.py"]
        names = {"MA", "VST", "V", "GOOG", "GOOGL", "AMD", "AMZN", "META", "CRWD", "MCO", "DE", "UNP", "CAT",
                 "0001692819", "0001652044", "0001141391", "0001403161"}
        for module in modules:
            tree = ast.parse((root / module).read_text())
            literals = {n.value for n in ast.walk(tree) if isinstance(n, ast.Constant) and isinstance(n.value, str)}
            assert not literals & names, (module, literals & names)
