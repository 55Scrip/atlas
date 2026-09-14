"""Aligned Historical Market Cap -- descriptive evidence only.

Real controls rebuild the persisted corpus (`fixtures/historical_market_cap_
corpus.json`: public month-end prices and SEC share counts with their filing
provenance, exactly as Atlas stores them, and the production fiscal_epoch_v2
epochs for each company). Synthetic cases cover what the corpus has not
exercised; each says so.
"""
from __future__ import annotations

import ast
import hashlib
import json
import random
import re
from dataclasses import fields, replace
from datetime import date, datetime, timezone
from pathlib import Path

import pytest

from atlas.alpha.investment_case import historical_market_cap as hmc
from atlas.alpha.investment_case.historical_market_cap import (
    HISTORICAL_MARKET_CAP_METHODOLOGY,
    AlignmentGap,
    AlignmentQuality,
    BasisEventStatus,
    EndpointKind,
    FactorSource,
    SecurityScope,
    ShareCountScope,
    ShareCountSource,
    derive_basis_events,
    reconstruct_historical_market_caps,
)
from atlas.alpha.security_share_evidence.models import SecurityShareCountObservation, ShareClassLinkKind
from atlas.analysis_engine.business_data.models import RawBusinessDocument
from atlas.analysis_engine.business_data.pipeline import ingest
from atlas.analysis_engine.valuation.cash_flow import FCF_YIELD_METHODOLOGY
from atlas.analysis_engine.valuation.contracts import ShareCountMethod, ValuationDecisionEligibility
from atlas.analysis_engine.valuation.models import FcfYieldEpochObservation, FcfYieldEvidence

CORPUS = json.loads((Path(__file__).parent / "fixtures" / "historical_market_cap_corpus.json").read_text())
NOW = datetime(2026, 9, 11, tzinfo=timezone.utc)
ROOT = Path(__file__).resolve().parents[4]


# -- building records exactly as Atlas stores them ----------------------------------------------------------


def _hash(*parts) -> str:
    return hashlib.sha256(json.dumps(parts, sort_keys=True, default=str).encode()).hexdigest()


def _price_record(ticker: str, bar: dict, *, adjusted_key: str = "adjusted"):
    metadata = {"currency": bar["currency"], "share_price": bar[adjusted_key], "shares_outstanding": bar["shares"]}
    if bar.get("raw") is not None:
        metadata.update(raw_close=bar["raw"], dividend_amount=bar["dividend"], price_basis="split_and_dividend_adjusted")
    on = date.fromisoformat(bar["on"])
    doc = RawBusinessDocument(
        identifier=f"{ticker}:historical_snapshot:{bar['on']}", company=ticker, source_kind="market_data_snapshot",
        published_at=datetime.combine(on, datetime.min.time(), tzinfo=timezone.utc), provider_id="alpha_vantage",
        raw_reference=f"https://www.alphavantage.co/query?function=TIME_SERIES_MONTHLY_ADJUSTED&symbol={ticker}",
        content_hash=_hash(bar["on"], metadata), period_start=on, period_end=on, language="en", metadata=metadata,
    )
    return ingest(doc, evaluated_at=NOW).record


def _statement_record(ticker: str, row: dict):
    metadata = {"sec_form": row.get("sec_form") or "10-K", "shares_outstanding": row["shares"]}
    metadata.update({f"shares_outstanding_{k}": v for k, v in row.items()
                     if k in ("filed", "accession", "first_reported", "first_reported_filed", "first_reported_accession")})
    period = date.fromisoformat(row["period"])
    doc = RawBusinessDocument(
        identifier=row.get("identifier", f"{ticker}:FY:{row['period']}"), company=ticker, source_kind="financial_statement",
        published_at=datetime.fromisoformat(row["published"]).replace(tzinfo=timezone.utc), provider_id="sec_edgar",
        raw_reference=f"https://data.sec.gov/{ticker}", content_hash=_hash(row.get("identifier"), row["period"], row["shares"]),
        period_start=period, period_end=period, language="en", metadata=metadata,
    )
    return ingest(doc, evaluated_at=NOW).record


def _case(ticker: str, *, monthly=None, statements=None, epochs=None, adjusted_key="adjusted"):
    """(records, evidence) for one company, from the corpus unless overridden."""
    data = CORPUS[ticker]
    prices = [_price_record(ticker, b, adjusted_key=adjusted_key if adjusted_key in b else "adjusted")
              for b in (monthly if monthly is not None else data["monthly"])]
    stmts = [_statement_record(ticker, s) for s in (statements if statements is not None else data["statements"])]
    price_id = {p.period_end.isoformat(): p.id for p in prices}
    stmt_id = {s.period_end.isoformat(): s.id for s in stmts if s.identifier == f"{ticker}:FY:{s.period_end.isoformat()}"}
    obs = tuple(
        FcfYieldEpochObservation(
            fiscal_period=e["fiscal"], available_from=date.fromisoformat(e["available"]), observed_on=e["observed"],
            free_cash_flow=e["fcf"], share_price=e["adjusted"], shares_outstanding=e["shares"], currency=e["currency"],
            free_cash_flow_fact_id=f"{stmt_id.get(e['fiscal'], ticker + ':FY:' + e['fiscal'] + ':v1')}:free_cash_flow:{e['fiscal']}",
            share_price_fact_id=f"{price_id.get(e['observed'], ticker + ':m:' + e['observed'] + ':v1')}:share_price:{e['observed']}",
            shares_outstanding_fact_id=f"{price_id.get(e['observed'], ticker + ':m:' + e['observed'] + ':v1')}:shares_outstanding:{e['observed']}",
        )
        for e in (epochs if epochs is not None else data["epochs"])
    )
    evidence = FcfYieldEvidence(eligibility=ValuationDecisionEligibility.INSUFFICIENT, minimum_prior_epochs=3,
                                share_count_method=ShareCountMethod.CURRENT_SHARE_COUNT_PROXY, prior_epochs=obs)
    return tuple(prices + stmts), evidence


def _run(ticker, *, shared_issuer=False, **kwargs):
    records, evidence = _case(ticker, **kwargs)
    return reconstruct_historical_market_caps(evidence, records, shared_issuer=shared_issuer)


def _epoch(result, fiscal):
    return next(e for e in result.epochs if e.fiscal_period == fiscal)


def _without_first_report(ticker, period):
    return [{k: v for k, v in s.items() if not k.startswith("first_reported")} if s["period"] == period else s
            for s in CORPUS[ticker]["statements"]]


# -- the step rule, pinned on the corpus it came from -------------------------------------------------------


class TestStepRule:
    def test_the_corpus_separates_dividend_drift_from_split_like_steps(self):
        steps = []
        for data in CORPUS.values():
            bars = [b for b in data["monthly"] if b.get("raw")]
            steps += [(a["raw"] / a["adjusted"]) / (b["raw"] / b["adjusted"]) for a, b in zip(bars, bars[1:])]
        drift = [s for s in steps if s < 1.5]
        splits = [s for s in steps if s >= 1.5]
        assert max(drift) < hmc.SMALL_STEP[1] and min(drift) >= hmc.SMALL_STEP[0]
        assert min(splits) > hmc.LARGE_STEP
        assert not [s for s in steps if hmc.SMALL_STEP[1] < s < hmc.LARGE_STEP]

    def test_methodology_is_its_own_and_the_valuation_names_its_own(self):
        assert HISTORICAL_MARKET_CAP_METHODOLOGY == "raw_price_split_aligned_shares_v1"
        assert FCF_YIELD_METHODOLOGY == "fiscal_epoch_v3"


# -- real controls ------------------------------------------------------------------------------------------


class TestCrm:
    def test_the_split_restatement_agrees_with_the_price_step(self):
        (event,) = _run("CRM").basis_events
        assert event.factor_source is FactorSource.SHARE_RESTATEMENT
        assert event.factor == pytest.approx(585_627_000 / 146_406_655, rel=1e-12)  # 4.0000026: counts rounded
        assert event.price_factor == pytest.approx(4.0, rel=1e-4)
        assert (event.after, event.on_or_before) == (date(2013, 3, 28), date(2014, 3, 5))
        assert event.on_or_before_kind is EndpointKind.FILING

    def test_fy2013_market_cap_from_raw_price_and_first_reported_shares(self):
        e = _epoch(_run("CRM"), "2013-01-31")
        assert e.quality is AlignmentQuality.FULLY_ALIGNED and e.share_count_source is ShareCountSource.FIRST_REPORTED
        assert e.aligned_share_count == 146_406_655
        assert e.market_cap == pytest.approx(178.83 * 146_406_655)
        assert e.market_cap == pytest.approx(26.18e9, rel=1e-3)
        assert e.latest_reported_share_count == 585_627_000
        assert e.latest_reported_aligned_share_count == pytest.approx(146_406_655, rel=1e-6)

    def test_real_divide_branch_with_a_price_only_factor(self):
        """Without FY2013's own restatement, its later count is placed by the
        price step's factor alone, located by a different period's unchanged
        restatement -- no circularity."""
        e = _epoch(_run("CRM", statements=_without_first_report("CRM", "2013-01-31")), "2013-01-31")
        assert e.quality is AlignmentQuality.BASIS_EVENT_REVERSED
        assert e.share_count_source is ShareCountSource.LATEST_REPORTED
        (event,) = e.basis_events
        assert event.factor_source is FactorSource.PRICE_STEP
        assert e.aligned_share_count == pytest.approx(146_406_655, rel=1e-4)
        assert e.aligned_share_count < e.share_count  # divided, never multiplied

    def test_an_economic_revision_is_kept_beside_the_first_report(self):
        e = _epoch(_run("CRM"), "2018-01-31")
        assert e.aligned_share_count == 707_460_000
        assert e.share_count_revision == pytest.approx(730 / 707.46, rel=1e-6)

    def test_every_epoch_is_aligned(self):
        result = _run("CRM")
        assert {e.quality for e in result.epochs} == {AlignmentQuality.FULLY_ALIGNED}


class TestTsla:
    def test_fy2019_first_report_is_pre_event(self):
        e = _epoch(_run("TSLA"), "2019-12-31")
        assert (e.quality, e.aligned_share_count) == (AlignmentQuality.FULLY_ALIGNED, 181_000_000)
        assert e.market_cap == pytest.approx(667.99 * 181e6)

    def test_real_divide_branch_905m_over_5(self):
        e = _epoch(_run("TSLA", statements=_without_first_report("TSLA", "2019-12-31")), "2019-12-31")
        assert e.quality is AlignmentQuality.BASIS_EVENT_REVERSED
        assert (e.share_count, e.aligned_share_count) == (905_000_000, pytest.approx(181_000_000, rel=1e-4))

    def test_fy2021_boundary_is_withheld_not_trusted(self):
        """Its first report (3.1B, filed 2023-01-31) is already post-split; the
        event's upper bound is the 2023-01-31 close itself, so its order
        relative to that filing cannot be proven."""
        e = _epoch(_run("TSLA"), "2021-12-31")
        assert e.quality is AlignmentQuality.AMBIGUOUS and e.gaps == (AlignmentGap.EVENT_AT_WINDOW_BOUNDARY,)
        assert e.market_cap is None and e.aligned_share_count is None

    def test_fy2021_divides_by_three_once_the_order_is_provable(self):
        """Synthetic shift of the filing past the event's upper bound."""
        statements = [dict(s, first_reported_filed="2023-02-15", filed="2023-02-15") if s["period"] == "2021-12-31" else s
                      for s in CORPUS["TSLA"]["statements"]]
        e = _epoch(_run("TSLA", statements=statements), "2021-12-31")
        assert e.quality is AlignmentQuality.BASIS_EVENT_REVERSED
        assert e.aligned_share_count == pytest.approx(3.1e9 / 3, rel=1e-6)

    def test_fy2022_uses_its_placeable_later_report(self):
        e = _epoch(_run("TSLA"), "2022-12-31")
        assert (e.quality, e.share_count_source) == (AlignmentQuality.FULLY_ALIGNED, ShareCountSource.LATEST_REPORTED)
        assert e.aligned_share_count == 3_164_000_000

    def test_the_first_report_is_never_assumed_safe(self):
        assert _epoch(_run("TSLA"), "2021-12-31").aligned_share_count != 3.1e9


class TestNoSplitControls:
    def test_amat_needs_no_correction(self):
        result = _run("AMAT")
        assert result.basis_events == ()
        assert {e.quality for e in result.epochs} == {AlignmentQuality.FULLY_ALIGNED}
        assert all(e.cumulative_factor == 1.0 and e.market_cap == pytest.approx(e.raw_close * e.aligned_share_count)
                   for e in result.epochs)

    def test_amd_issuance_difference_from_the_proxy_is_kept(self):
        e = _epoch(_run("AMD"), "2011-12-31")
        assert e.quality is AlignmentQuality.FULLY_ALIGNED
        assert e.proxy_market_cap / e.market_cap == pytest.approx(2.34, rel=0.01)

    def test_vst_uses_historical_not_current_shares(self):
        e = _epoch(_run("VST"), "2019-12-31")
        assert e.aligned_share_count == pytest.approx(487_698_111)
        assert e.market_cap > e.proxy_market_cap

    def test_mu_every_epoch_aligned(self):
        assert {e.quality for e in _run("MU").epochs} == {AlignmentQuality.FULLY_ALIGNED}


class TestBoundedControls:
    def test_aapl_uses_only_its_safe_bounded_epochs(self):
        result = _run("AAPL")
        q = {e.fiscal_period: e.quality for e in result.epochs}
        assert [p for p, x in q.items() if x is AlignmentQuality.FULLY_ALIGNED_BOUNDED] == [
            "2021-09-25", "2022-09-24", "2023-09-30", "2024-09-28"]
        near = [e for e in result.epochs if e.gaps == (AlignmentGap.MISSING_SHARE_PROVENANCE,)]
        assert len(near) == 11 and all(e.market_cap is None for e in near)
        assert AlignmentQuality.FULLY_ALIGNED not in q.values()  # bounded is never called exact

    def test_aapl_splits_are_found_from_prices_alone(self):
        factors = [round(e.factor, 2) for e in _run("AAPL").basis_events]
        assert factors == [7.01, 3.99]

    def test_cat_is_bounded_aligned_without_any_event(self):
        result = _run("CAT")
        assert result.basis_events == ()
        assert sum(e.quality is AlignmentQuality.FULLY_ALIGNED_BOUNDED for e in result.epochs) == 15
        assert all(e.share_count_filed_bounds and e.share_count_filed is None
                   for e in result.epochs if e.quality is AlignmentQuality.FULLY_ALIGNED_BOUNDED)

    def test_amzn_bounded_only_after_its_split(self):
        result = _run("AMZN")
        assert [round(e.factor) for e in result.basis_events] == [20]
        assert [e.fiscal_period for e in result.epochs if e.market_cap] == ["2023-12-31", "2024-12-31"]


class TestRevisionStability:
    def test_aapl_dividend_rescale_does_not_move_the_split_factors(self):
        before = _run("AAPL").basis_events
        after = _run("AAPL", adjusted_key="legacy_adjusted").basis_events
        assert [(e.after, e.on_or_before) for e in before] == [(e.after, e.on_or_before) for e in after]
        for a, b in zip(before, after):
            assert a.factor == pytest.approx(b.factor, rel=1e-4)

    def test_the_legacy_series_really_was_rescaled(self):
        bars = [b for b in CORPUS["AAPL"]["monthly"] if "legacy_adjusted" in b]
        ratios = [b["adjusted"] / b["legacy_adjusted"] for b in bars]
        assert len(bars) >= 15 and all(0.9991 < r < 0.99914 for r in ratios)


# -- synthetic matrix: what the corpus has not exercised ----------------------------------------------------


def _synthetic(r_levels, *, shares=100.0, first=None, first_filed=None, filed="2021-02-10", published=None,
               fiscal="2020-12-31", sec_form="10-K", extra_statements=()):
    """One bar each 26 February 2015..2024 with raw/adjusted = `r_levels[i]`;
    the epoch prices the 2021 bar."""
    monthly = [{"on": f"{2015 + i}-02-26", "raw": 10.0 * r, "adjusted": 10.0, "dividend": 0.0, "shares": 50.0,
                "currency": "USD"} for i, r in enumerate(r_levels)]
    stmt = {"period": fiscal, "published": published or filed, "sec_form": sec_form, "shares": shares}
    if filed:
        stmt["filed"] = filed
    if first is not None:
        stmt.update(first_reported=first, first_reported_filed=first_filed)
    epochs = [{"fiscal": fiscal, "available": "2021-02-10", "observed": "2021-02-26", "fcf": 5.0, "adjusted": 10.0,
               "shares": 50.0, "currency": "USD"}]
    CORPUS["SYN"] = {"monthly": monthly, "statements": [stmt, *extra_statements], "epochs": epochs}
    return monthly


@pytest.fixture(autouse=True)
def _drop_synthetic():
    yield
    CORPUS.pop("SYN", None)


class TestSyntheticMatrix:
    # R levels, one per yearly bar 2015..2024; the epoch prices the 2021 bar.
    NO_SPLIT = [1.0] * 10
    DIVIDEND = [1.02 ** (9 - i) for i in range(10)]

    def test_no_split(self):
        _synthetic(self.NO_SPLIT)
        e = _run("SYN").epochs[0]
        assert (e.quality, e.aligned_share_count) == (AlignmentQuality.FULLY_ALIGNED, 100.0)

    def test_dividend_drift_is_not_a_split(self):
        _synthetic(self.DIVIDEND)
        assert _run("SYN").basis_events == ()

    def test_single_forward_split_after_the_price_divides_a_later_count(self):
        _synthetic([2.0] * 7 + [1.0] * 3, filed="2023-03-01")  # event in (2021, 2022]; count filed 2023
        e = _run("SYN").epochs[0]
        assert e.quality is AlignmentQuality.BASIS_EVENT_REVERSED and e.aligned_share_count == pytest.approx(50.0)

    def test_dividend_plus_split_isolates_the_split_factor(self):
        r = [1.02 ** (9 - i) * (3.0 if i < 7 else 1.0) for i in range(10)]
        _synthetic(r, filed="2023-03-01")
        (event,) = _run("SYN").basis_events
        assert event.factor == pytest.approx(3.0, rel=1e-9)

    def test_first_reported_pre_event_is_used_as_reported(self):
        _synthetic([2.0] * 7 + [1.0] * 3, shares=200.0, first=100.0, first_filed="2021-02-10", filed="2023-03-01")
        e = _run("SYN").epochs[0]
        assert (e.quality, e.aligned_share_count, e.share_count_source) == (
            AlignmentQuality.FULLY_ALIGNED, 100.0, ShareCountSource.FIRST_REPORTED)
        assert e.latest_reported_aligned_share_count == pytest.approx(100.0)

    def test_count_filed_before_a_split_that_precedes_the_price_is_multiplied(self):
        """The multiply branch: never exercised by the real corpus."""
        _synthetic([2.0] * 6 + [1.0] * 4, filed="2020-01-15", fiscal="2019-12-31")  # event in (2020, 2021]
        e = _run("SYN").epochs[0]
        assert e.quality is AlignmentQuality.BASIS_EVENT_REVERSED and e.aligned_share_count == pytest.approx(200.0)

    def test_multiple_events_compose(self):
        """Capability only: no real share window contains two events."""
        _synthetic([6.0] * 7 + [3.0] + [1.0] * 2, filed="2024-02-01")  # x2 then x3 after the price
        e = _run("SYN").epochs[0]
        assert len(e.basis_events) == 2 and e.cumulative_factor == pytest.approx(1 / 6)
        assert e.aligned_share_count == pytest.approx(100.0 / 6)

    def test_non_integer_factor_is_not_rounded(self):
        _synthetic([1.5] * 7 + [1.0] * 3, filed="2023-03-01")
        (event,) = _run("SYN").basis_events
        assert event.factor == pytest.approx(1.5, rel=1e-12)

    def test_a_step_between_the_bands_is_ambiguous(self):
        _synthetic([1.12] * 7 + [1.0] * 3, filed="2023-03-01")
        e = _run("SYN").epochs[0]
        assert e.quality is AlignmentQuality.AMBIGUOUS and e.gaps == (AlignmentGap.AMBIGUOUS_STEP,)
        assert _run("SYN").basis_events[0].status is BasisEventStatus.AMBIGUOUS

    def test_an_event_straddling_the_filing_is_withheld(self):
        _synthetic([2.0] * 7 + [1.0] * 3, filed="2021-09-01")  # event in (2021-02, 2022-02], filing inside it
        e = _run("SYN").epochs[0]
        assert e.quality is AlignmentQuality.AMBIGUOUS and e.gaps == (AlignmentGap.EVENT_STRADDLES_WINDOW,)

    def test_bounded_no_event_window(self):
        _synthetic(self.NO_SPLIT, filed=None, published="2024-02-01")
        e = _run("SYN").epochs[0]
        assert e.quality is AlignmentQuality.FULLY_ALIGNED_BOUNDED and e.share_count_filed is None
        assert e.share_count_filed_bounds == (date(2020, 12, 31), date(2024, 2, 1))

    def test_bounded_with_an_event_inside_needs_provenance(self):
        _synthetic([2.0] * 7 + [1.0] * 3, filed=None, published="2024-02-01")
        e = _run("SYN").epochs[0]
        assert (e.quality, e.gaps) == (AlignmentQuality.INSUFFICIENT, (AlignmentGap.MISSING_SHARE_PROVENANCE,))

    def test_conflicting_duplicate_comparative_is_withheld(self):
        _synthetic(self.NO_SPLIT, extra_statements=({"period": "2020-12-31", "identifier": "SYN:FY:2020-12-31:restated",
                                                      "published": "2021-02-10", "shares": 150.0, "filed": "2021-02-10"},))
        e = _run("SYN").epochs[0]
        assert (e.quality, e.gaps) == (AlignmentQuality.AMBIGUOUS, (AlignmentGap.CONFLICTING_EVIDENCE,))

    def test_missing_raw_close(self):
        monthly = _synthetic(self.NO_SPLIT)
        for bar in monthly:
            bar.pop("raw")
        e = _run("SYN").epochs[0]
        assert (e.quality, e.gaps) == (AlignmentQuality.INSUFFICIENT, (AlignmentGap.MISSING_RAW_PRICE,))

    def test_missing_period_shares(self):
        _synthetic(self.NO_SPLIT)
        CORPUS["SYN"]["statements"] = []
        e = _run("SYN").epochs[0]
        assert (e.quality, e.gaps) == (AlignmentQuality.INSUFFICIENT, (AlignmentGap.MISSING_PERIOD_SHARES,))

    def test_a_filing_before_the_first_stored_price_cannot_be_spanned(self):
        _synthetic(self.NO_SPLIT, filed="2014-06-01", fiscal="2014-03-31")
        e = _run("SYN").epochs[0]
        assert e.gaps == (AlignmentGap.PRICE_HISTORY_DOES_NOT_SPAN,)

    def test_multi_class_is_unsafe(self):
        _synthetic(self.NO_SPLIT)
        result = _run("SYN", shared_issuer=True)
        assert result.security_scope is SecurityScope.SHARED_ISSUER
        assert result.epochs[0].quality is AlignmentQuality.SECURITY_SCOPE_UNSAFE and result.epochs[0].market_cap is None

    def test_foreign_filer_is_unsafe(self):
        _synthetic(self.NO_SPLIT, sec_form="20-F")
        result = _run("SYN")
        assert result.security_scope is SecurityScope.FOREIGN_FILER
        assert result.epochs[0].gaps == (AlignmentGap.FOREIGN_FILER,)

    def test_not_applicable_valuation_has_no_evidence(self):
        evidence = FcfYieldEvidence(eligibility=ValuationDecisionEligibility.NOT_APPLICABLE, minimum_prior_epochs=3,
                                    share_count_method=ShareCountMethod.CURRENT_SHARE_COUNT_PROXY)
        assert reconstruct_historical_market_caps(evidence, (), shared_issuer=False) is None
        assert reconstruct_historical_market_caps(None, (), shared_issuer=False) is None


# -- security-level class counts (Security-Level Share-Class Evidence v1) -------------------------------------


def _class_count(period="2020-12-31", filed="2021-02-10", shares=40.0, *, accession=None, member="abc:ClassCMember",
                 kind=ShareClassLinkKind.PROVEN_BY_SHARED_DIMENSION, conflict=False):
    """One class count as a filing links it (synthetic: the adapter's real
    controls live in `test_sec_edgar_share_classes.py`)."""
    return SecurityShareCountObservation(
        issuer_cik="0000000001", accession=accession or f"0000000001-{filed[2:4]}-000001", form="10-K",
        filing_date=date.fromisoformat(filed), fiscal_period=None, document_period_end=None,
        period_end=date.fromisoformat(period), class_axis="us-gaap:StatementClassOfStockAxis", class_member=member,
        shares=None if conflict else shares, conflict=conflict, source_concept="us-gaap:CommonStockSharesOutstanding",
        context_id="c", link_kind=kind, cover_title="t", cover_symbol="SYN", cover_exchange="NASDAQ", cover_mic="XNAS",
        parser_version="share_class_links_v1", recorded_at=NOW,
    )


def _run_classes(counts, *, shared_issuer=True, as_of=None, **kwargs):
    records, evidence = _case("SYN", **kwargs)
    return reconstruct_historical_market_caps(evidence, records, shared_issuer=shared_issuer,
                                              security_share_counts=tuple(counts), as_of=as_of)


class TestSecurityLevelCounts:
    NO_SPLIT = [1.0] * 10

    def test_a_shared_issuer_is_priced_on_its_own_class_count(self):
        _synthetic(self.NO_SPLIT, shares=100.0)  # the issuer-level count spans every class
        result = _run_classes([_class_count(shares=40.0)])
        e = result.epochs[0]
        assert (result.security_scope, result.share_count_scope) == (SecurityScope.SHARED_ISSUER, ShareCountScope.SECURITY)
        assert (e.quality, e.aligned_share_count, e.market_cap) == (AlignmentQuality.FULLY_ALIGNED, 40.0, 400.0)
        assert (e.share_count_scope, e.share_count_class_member, e.share_count_source) == (
            ShareCountScope.SECURITY, "abc:ClassCMember", ShareCountSource.FIRST_REPORTED)
        assert e.share_count_accession == e.first_reported_share_count_accession == "0000000001-21-000001"

    def test_a_shared_issuer_period_without_a_class_count_stays_unsafe(self):
        _synthetic(self.NO_SPLIT)
        e = _run_classes([_class_count(period="2019-12-31", filed="2020-02-10")]).epochs[0]
        assert (e.quality, e.gaps, e.market_cap) == (AlignmentQuality.SECURITY_SCOPE_UNSAFE, (AlignmentGap.SHARED_ISSUER,), None)

    def test_one_share_source_per_case_never_a_mix(self):
        _synthetic(self.NO_SPLIT, shares=100.0)
        e = _run_classes([_class_count(period="2019-12-31", filed="2020-02-10")], shared_issuer=False).epochs[0]
        assert (e.quality, e.gaps) == (AlignmentQuality.INSUFFICIENT, (AlignmentGap.MISSING_PERIOD_SHARES,))

    def test_a_class_restatement_between_filings_names_the_split(self):
        """The Alphabet shape: a first report before a 20-for-1 split, its
        restatement after -- the split's factor comes from the class counts."""
        _synthetic([20.0] * 7 + [1.0] * 3)  # a x20 event in (2021-02-26, 2022-02-26]
        counts = [_class_count(shares=100.0), _class_count(filed="2023-02-01", shares=2000.0)]
        result = _run_classes(counts)
        (event,) = result.basis_events
        assert (event.factor_source, event.factor) == (FactorSource.SHARE_RESTATEMENT, 20.0)
        e = result.epochs[0]
        assert (e.quality, e.aligned_share_count) == (AlignmentQuality.FULLY_ALIGNED, 100.0)
        assert e.latest_reported_aligned_share_count == pytest.approx(100.0) and e.share_count_revision == pytest.approx(1.0)
        assert e.latest_reported_share_count_accession == "0000000001-23-000001"

    def test_a_conflicting_class_report_withholds(self):
        _synthetic(self.NO_SPLIT)
        e = _run_classes([_class_count(conflict=True)]).epochs[0]
        assert (e.quality, e.gaps) == (AlignmentQuality.AMBIGUOUS, (AlignmentGap.CONFLICTING_EVIDENCE,))

    def test_a_count_filed_after_the_evaluation_is_not_read(self):
        _synthetic(self.NO_SPLIT)
        result = _run_classes([_class_count()], as_of=date(2021, 2, 9))
        assert result.share_count_scope is ShareCountScope.ISSUER
        assert result.epochs[0].quality is AlignmentQuality.SECURITY_SCOPE_UNSAFE
        assert _run_classes([_class_count()], as_of=date(2021, 2, 10)).share_count_scope is ShareCountScope.SECURITY

    @pytest.mark.parametrize("kind", [ShareClassLinkKind.AMBIGUOUS, ShareClassLinkKind.NO_LINK])
    def test_only_a_proven_link_counts(self, kind):
        _synthetic(self.NO_SPLIT)
        result = _run_classes([_class_count(kind=kind)])
        assert result.share_count_scope is ShareCountScope.ISSUER
        assert result.epochs[0].quality is AlignmentQuality.SECURITY_SCOPE_UNSAFE

    def test_an_impossible_filing_date_is_ignored(self):
        _synthetic(self.NO_SPLIT)
        assert _run_classes([_class_count(filed="2020-12-31")]).share_count_scope is ShareCountScope.ISSUER

    def test_a_foreign_filer_stays_unsafe(self):
        _synthetic(self.NO_SPLIT, sec_form="20-F")
        e = _run_classes([_class_count()], shared_issuer=False).epochs[0]
        assert e.gaps == (AlignmentGap.FOREIGN_FILER,)

    def test_order_does_not_matter(self):
        _synthetic([20.0] * 7 + [1.0] * 3)
        counts = [_class_count(shares=100.0), _class_count(filed="2023-02-01", shares=2000.0),
                  _class_count(period="2019-12-31", filed="2020-02-10", shares=90.0)]
        assert _run_classes(counts) == _run_classes(counts[::-1])

    def test_without_class_counts_nothing_changes(self):
        records, evidence = _case("CRM")
        assert reconstruct_historical_market_caps(evidence, records, shared_issuer=False, security_share_counts=()) == \
            reconstruct_historical_market_caps(evidence, records, shared_issuer=False)
        assert reconstruct_historical_market_caps(evidence, records, shared_issuer=False).share_count_scope is \
            ShareCountScope.ISSUER

    def test_the_wire_says_which_count(self):
        from atlas.alpha.investment_case.api.schemas import HistoricalMarketCapView

        _synthetic(self.NO_SPLIT)
        body = HistoricalMarketCapView.from_domain(_run_classes([_class_count()])).model_dump(by_alias=True, mode="json")
        (epoch,) = body["epochs"]
        assert (body["securityScope"], body["shareCountScope"], epoch["shareCountScope"]) == (
            "shared_issuer", "security", "security")
        assert (epoch["shareCountClassMember"], epoch["shareCountAccession"]) == ("abc:ClassCMember", "0000000001-21-000001")


# -- Alphabet: GOOG and GOOGL on their own class counts (GOOG / GOOGL Held Price Revision Acceptance) ------


ALPHABET_CIK = "0001652044"
OWN_MEMBER = {"GOOG": "goog:CapitalClassCMember", "GOOGL": "us-gaap:CommonClassAMember"}


def _alphabet_joined(ticker: str, rows=None):
    """Every class count the persisted Alphabet filings hold (all link
    kinds), recorded and read back through the production repository's
    own join (CIK + symbol + MIC)."""
    from sqlalchemy import create_engine
    from sqlalchemy.pool import StaticPool

    from atlas.alpha.security_share_evidence.models import SecurityShareFiling
    from atlas.alpha.security_share_evidence.repository import SqlAlchemySecurityShareEvidenceRepository
    from atlas.alpha.security_share_evidence.table import create_security_share_evidence_tables

    engine = create_engine("sqlite:///:memory:", future=True, poolclass=StaticPool,
                           connect_args={"check_same_thread": False})
    create_security_share_evidence_tables(engine)
    repo = SqlAlchemySecurityShareEvidenceRepository(
        engine, listing_mics=lambda tickers: {t: frozenset({"XNAS"}) for t in tickers})
    by_filing: dict[str, list[SecurityShareCountObservation]] = {}
    for row in rows if rows is not None else CORPUS[ticker]["class_counts"]:
        proven = row["link"] == ShareClassLinkKind.PROVEN_BY_SHARED_DIMENSION.value
        by_filing.setdefault(row["accession"], []).append(SecurityShareCountObservation(
            issuer_cik=ALPHABET_CIK, accession=row["accession"], form="10-K", filing_date=date.fromisoformat(row["filed"]),
            fiscal_period=None, document_period_end=None, period_end=date.fromisoformat(row["period"]),
            class_axis="us-gaap:StatementClassOfStockAxis", class_member=row["member"], shares=row["shares"],
            conflict=False, source_concept="us-gaap:CommonStockSharesOutstanding", context_id=f"c-{row['member']}",
            link_kind=ShareClassLinkKind(row["link"]), cover_title="title" if proven else None,
            cover_symbol=row["symbol"], cover_exchange="NASDAQ" if proven else None, cover_mic=row["mic"],
            parser_version="share_class_links_v1", recorded_at=NOW,
        ))
    for accession, observations in by_filing.items():
        o = observations[0]
        repo.record_filing(SecurityShareFiling(
            issuer_cik=ALPHABET_CIK, accession=accession, form="10-K", filing_date=o.filing_date, fiscal_period=None,
            document_period_end=None, instance_url="https://www.sec.gov/x", cover_rows=2, dimensioned_cover_rows=2,
            observations=len(observations), proven=0, ambiguous=0, no_link=0, conflicts=0,
            parser_version="share_class_links_v1", processed_at=NOW), tuple(observations))
    return repo.proven_for_securities({ticker: ALPHABET_CIK})[ticker]


def _alphabet(ticker: str, *, adjusted_key="adjusted", rows=None):
    records, evidence = _case(ticker, adjusted_key=adjusted_key)
    return reconstruct_historical_market_caps(evidence, records, shared_issuer=True,
                                              security_share_counts=_alphabet_joined(ticker, rows), as_of=NOW.date())


@pytest.mark.parametrize("ticker", ["GOOG", "GOOGL"])
class TestAlphabetClassCounts:
    """Real controls: GOOG and GOOGL after their held price revisions were
    accepted, each priced only on its own listed class's count."""

    def test_seven_exact_epochs_on_its_own_class_count(self, ticker):
        result = _alphabet(ticker)
        assert (result.security_scope, result.share_count_scope) == (SecurityScope.SHARED_ISSUER, ShareCountScope.SECURITY)
        aligned = [e for e in result.epochs if e.market_cap is not None]
        assert [e.fiscal_period for e in aligned] == [f"{y}-12-31" for y in range(2018, 2025)]
        assert {e.quality for e in aligned} == {AlignmentQuality.FULLY_ALIGNED}
        own = {(r["period"], r["accession"]): r["shares"] for r in CORPUS[ticker]["class_counts"]
               if r["member"] == OWN_MEMBER[ticker]}
        for e in aligned:
            assert e.share_count_class_member == OWN_MEMBER[ticker]
            assert e.share_count == own[(e.fiscal_period, e.share_count_accession)]
            assert e.market_cap == pytest.approx(e.raw_close * e.aligned_share_count)

    def test_class_b_and_the_issuer_total_are_never_the_count(self, ticker):
        rows = CORPUS[ticker]["class_counts"]
        assert {r["link"] for r in rows if r["member"] == "us-gaap:CommonClassBMember"} == {"no_link"}
        assert {o.class_member for o in _alphabet_joined(ticker)} == {OWN_MEMBER[ticker]}
        by_filing: dict[tuple[str, str], float] = {}
        for r in rows:
            by_filing[(r["period"], r["accession"])] = by_filing.get((r["period"], r["accession"]), 0.0) + r["shares"]
        issuer = {s["period"]: s["shares"] for s in CORPUS[ticker]["statements"]}
        for e in _alphabet(ticker).epochs:
            if e.share_count is not None:
                assert e.share_count not in (issuer.get(e.fiscal_period), by_filing[(e.fiscal_period, e.share_count_accession)])

    def test_pre_2019_covers_link_nothing_so_fy2015_to_fy2017_stay_unsafe(self, ticker):
        """The FY2018 filing (February 2019) reports 2017 year-end class
        counts but links no member: later filings naming the member never
        reach back."""
        assert any(r["period"] == "2017-12-31" and r["link"] == "no_link" for r in CORPUS[ticker]["class_counts"])
        for period in ("2015-12-31", "2016-12-31", "2017-12-31"):
            e = _epoch(_alphabet(ticker), period)
            assert (e.quality, e.gaps, e.market_cap) == (
                AlignmentQuality.SECURITY_SCOPE_UNSAFE, (AlignmentGap.SHARED_ISSUER,), None)

    def test_the_2022_split_is_its_class_restatement(self, ticker):
        (event,) = _alphabet(ticker).basis_events
        assert (event.after, event.on_or_before) == (date(2022, 2, 28), date(2023, 2, 3))
        assert event.factor_source is FactorSource.SHARE_RESTATEMENT and event.factor == pytest.approx(20.0, rel=1e-3)
        assert event.price_factor == pytest.approx(20.0, rel=1e-5)

    def test_the_accepted_rescale_moves_no_event_and_no_aligned_cap(self, ticker):
        after, before = _alphabet(ticker), _alphabet(ticker, adjusted_key="legacy_adjusted")
        assert [(e.after, e.on_or_before, e.factor_source, e.status) for e in before.basis_events] == [
            (e.after, e.on_or_before, e.factor_source, e.status) for e in after.basis_events]
        assert [(e.fiscal_period, e.quality, e.aligned_share_count, e.market_cap) for e in before.epochs] == [
            (e.fiscal_period, e.quality, e.aligned_share_count, e.market_cap) for e in after.epochs]


# -- determinism and provenance -----------------------------------------------------------------------------


class TestDeterminismAndProvenance:
    @pytest.mark.parametrize("ticker", ["CRM", "TSLA", "AAPL"])
    def test_shuffled_reversed_and_duplicated_input_changes_nothing(self, ticker):
        records, evidence = _case(ticker)
        reference = reconstruct_historical_market_caps(evidence, records, shared_issuer=False)
        shuffled = list(records)
        random.Random(3).shuffle(shuffled)
        for variant in (tuple(shuffled), records[::-1], records + records[:20]):
            assert reconstruct_historical_market_caps(evidence, variant, shared_issuer=False) == reference

    def test_every_aligned_epoch_names_its_evidence(self):
        records, evidence = _case("CRM", statements=_without_first_report("CRM", "2013-01-31"))
        ids = {r.id for r in records}
        for e in reconstruct_historical_market_caps(evidence, records, shared_issuer=False).epochs:
            assert e.price_record_id in ids and e.statement_record_id in ids
            assert e.raw_close and e.adjusted_close and e.share_count and e.share_count_source
            assert e.share_count_filed is not None
            for event in e.basis_events:
                assert set(event.price_record_ids) <= ids and set(event.statement_record_ids) <= ids

    def test_derive_basis_events_matches_the_evidence(self):
        records, _ = _case("TSLA")
        assert derive_basis_events(records) == _run("TSLA").basis_events


# -- the decision firewall ----------------------------------------------------------------------------------


_MODULE = ROOT / "atlas" / "alpha" / "investment_case" / "historical_market_cap.py"
_ALLOWED_IMPORTERS = {
    "atlas/alpha/investment_case/historical_market_cap.py",
    "atlas/alpha/investment_case/models.py",
    "atlas/alpha/investment_case/service.py",
    "atlas/alpha/investment_case/api/schemas.py",
    # Borrows the share-basis event reader (firewalled in
    # tests/unit/alpha/class_rights_evidence/test_firewall.py).
    "atlas/alpha/issuer_equity/reader.py",
    # fiscal_epoch_v3: prices each aligned epoch as the issuer's common equity.
    "atlas/alpha/issuer_equity/valuation_basis.py",
}


class TestDecisionFirewall:
    def test_no_ticker_names_or_event_dates_in_the_primitive(self):
        source = _MODULE.read_text()
        code = ast.unparse(ast.parse(source))  # docstrings and comments removed from the check below
        tickers = set(CORPUS) | {"GOOG", "GOOGL", "NVDA", "MSFT", "UNP", "ASML", "AZN", "TSM", "JPM", "GS"}
        literals = [n.value for n in ast.walk(ast.parse(source)) if isinstance(n, ast.Constant) and isinstance(n.value, str)]
        assert not [t for t in tickers if re.search(rf"\b{t}\b", code)]
        assert not [s for s in literals if re.fullmatch(r"\d{4}-\d{2}-\d{2}", s)]
        assert not [s for s in literals if s in tickers]

    def test_only_the_composition_the_api_and_itself_import_it(self):
        importers = set()
        for path in (ROOT / "atlas").rglob("*.py"):
            text = path.read_text()
            if "historical_market_cap import" in text or "import historical_market_cap" in text:
                importers.add(str(path.relative_to(ROOT)))
        assert importers <= _ALLOWED_IMPORTERS, importers - _ALLOWED_IMPORTERS

    def test_canonical_analysis_has_no_descriptive_field(self):
        from atlas.analysis_engine.models import CanonicalAnalysis
        from atlas.analysis_engine.valuation.models import FcfYieldEvidence as Evidence, ValuationFinding

        for cls in (CanonicalAnalysis, ValuationFinding, Evidence, FcfYieldEpochObservation):
            assert not [f.name for f in fields(cls) if "aligned" in f.name or "historical_market_cap" in f.name]

    def test_the_service_reconstructs_the_valuations_own_epochs_before_the_analysis(self, monkeypatch):
        """The aligned caps are reconstructed for exactly the fiscal epochs the
        valuation compares, from the same records, before the analysis runs --
        they reach the decision only through the issuer valuation basis, so a
        service without a basis builder decides nothing from them."""
        import atlas.alpha.investment_case.service as service_module
        from atlas.analysis_engine.pipeline import fiscal_epochs_for_records
        from tests.unit.alpha.investment_case.test_service import _Harness, _new_engine

        monkeypatch.setattr(service_module, "_utc_now", lambda: NOW)
        harness = _Harness(_new_engine())
        case_id = harness.add_to_watchlist("CRM")
        reference = harness.fresh_composition_service().build(case_id)
        seen, sentinel = [], object()

        def spy(evidence, records, *, shared_issuer, security_share_counts, as_of):
            seen.append((evidence, records, shared_issuer, security_share_counts, as_of))
            return sentinel

        monkeypatch.setattr(service_module, "reconstruct_historical_market_caps", spy)
        spied = harness.fresh_composition_service().build(case_id)
        assert spied.historical_market_cap is sentinel
        assert spied.canonical_analysis == reference.canonical_analysis
        ((evidence, records, shared_issuer, security_share_counts, as_of),) = seen
        assert evidence == fiscal_epochs_for_records(records, generated_at=NOW) and shared_issuer is False
        # No security-level repository wired: no class counts, read as of the Case's own clock.
        assert security_share_counts == () and as_of == NOW.date()


class TestApiView:
    def test_the_wire_says_descriptive_and_carries_provenance(self):
        from atlas.alpha.investment_case.api.schemas import HistoricalMarketCapView

        records, evidence = _case("CRM", statements=_without_first_report("CRM", "2013-01-31"))
        body = HistoricalMarketCapView.from_domain(
            reconstruct_historical_market_caps(evidence, records, shared_issuer=False)
        ).model_dump(by_alias=True, mode="json")
        assert (body["role"], body["methodology"], body["securityScope"]) == (
            "descriptive", "raw_price_split_aligned_shares_v1", "single_security")
        fy13 = next(e for e in body["epochs"] if e["fiscalPeriod"] == "2013-01-31")
        assert fy13["alignmentQuality"] == "basis_event_reversed" and fy13["shareCountSource"] == "latest_reported"
        assert fy13["alignedHistoricalMarketCap"] == pytest.approx(178.83 * fy13["alignedShareCount"])
        assert fy13["alignedHistoricalFcfYield"] == pytest.approx(fy13["freeCashFlow"] / fy13["alignedHistoricalMarketCap"])
        (event,) = fy13["basisEvents"]
        assert event["factorSource"] == "price_step" and len(event["priceRecordIds"]) == 2 and event["statementRecordIds"]
        assert fy13["priceRecordId"] and fy13["statementRecordId"] and fy13["proxyMarketCap"] > 0


class TestAcceptedPriceRevisions:
    """MSFT, NVDA and UNP after their held adjusted-close revisions were
    accepted (Held Historical Price Revision Acceptance): the stored series
    before (`legacy_adjusted`) and after is one uniform rescale, and it moves
    no inferred basis event."""

    @pytest.mark.parametrize("ticker", ["MSFT", "NVDA", "UNP"])
    def test_split_inference_is_identical_before_and_after_the_rescale(self, ticker):
        after = _run(ticker).basis_events
        before = _run(ticker, adjusted_key="legacy_adjusted").basis_events
        assert [(e.after, e.on_or_before, e.factor_source) for e in before] == [
            (e.after, e.on_or_before, e.factor_source) for e in after]
        for a, b in zip(after, before):
            assert a.factor == pytest.approx(b.factor, rel=1e-6)
            assert a.price_factor == pytest.approx(b.price_factor, rel=1e-3)

    def test_nvda_splits_are_its_share_restatements_on_persisted_prices(self):
        events = _run("NVDA").basis_events
        assert [e.factor_source for e in events] == [FactorSource.SHARE_RESTATEMENT] * 2
        assert [round(e.factor, 6) for e in events] == [3.998387, 10.001218]
        assert [round(e.price_factor, 1) for e in events] == [4.0, 10.0]

    def test_nvda_every_epoch_is_exactly_aligned(self):
        assert {e.quality for e in _run("NVDA").epochs} == {AlignmentQuality.FULLY_ALIGNED}

    def test_msft_and_unp_gain_bounded_history(self):
        counts = {t: sum(e.quality is AlignmentQuality.FULLY_ALIGNED_BOUNDED for e in _run(t).epochs) for t in ("MSFT", "UNP")}
        assert counts == {"MSFT": 15, "UNP": 10}
        assert [round(e.factor, 3) for e in _run("UNP").basis_events] == [1.988]
