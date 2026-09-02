"""CIK-backed issuer reconciliation.

The live database cannot exercise the end-to-end case: `GOOG` and
`GOOGL` genuinely share CIK `0001652044`, but `GOOG` has no
`CanonicalSecurity` row at all and none of its CIK-bearing records carry
a `canonical_security_id`, so there is nothing to reconcile. These tests
therefore build a GOOG/GOOGL-*shaped* pair explicitly, so the capability
is proven by construction rather than by whatever happens to be stored.

The invariant every test here defends: this operation may reduce the
number of duplicate **issuers** and must never reduce the number of
distinct **securities**.
"""
from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.pool import StaticPool

from atlas.alpha.canonical_security.issuer import CanonicalIssuer
from atlas.alpha.canonical_security.issuer_cik import (
    CikEvidenceState,
    IssuerReconciliationPlan,
    SecurityCikEvidence,
    extract_cik_evidence,
    normalize_cik,
    plan_issuer_reconciliation,
)
from atlas.alpha.canonical_security.models import CanonicalSecurity, ListingRef
from atlas.alpha.canonical_security.repository import (
    SqlAlchemyCanonicalIssuerRepository,
    SqlAlchemyCanonicalSecurityRepository,
)
from atlas.alpha.canonical_security.table import (
    canonical_securities_table,
    create_canonical_security_tables,
)
from atlas.alpha.canonical_security.value_objects import MicCode, TradingCurrency

ALPHABET_CIK = "0001652044"
APPLE_CIK = "0000320193"
_T0 = datetime(2026, 9, 1, tzinfo=timezone.utc)


@pytest.fixture
def engine():
    engine = create_engine(
        "sqlite:///:memory:", future=True, poolclass=StaticPool, connect_args={"check_same_thread": False}
    )
    create_canonical_security_tables(engine)
    return engine


def _security(name, ticker, mic, currency, country="USA"):
    return CanonicalSecurity.discover(
        canonical_company_name=name,
        native_ticker=ticker,
        primary_exchange_mic=MicCode(mic),
        country=country,
        trading_currency=TradingCurrency(currency),
    )


class TestNormalization:
    @pytest.mark.parametrize(
        "raw,expected",
        [
            ("0001652044", "0001652044"),
            ("1652044", "0001652044"),
            (1652044, "0001652044"),
            ("  1652044  ", "0001652044"),
        ],
    )
    def test_equivalent_forms_normalise_identically(self, raw, expected):
        """SEC returns the same filer padded from one endpoint and bare
        from another. Raw string comparison would manufacture a
        contradiction out of formatting."""
        assert normalize_cik(raw) == expected

    @pytest.mark.parametrize("raw", [None, "", "   ", "abc", "12a45", "12345678901", "0"])
    def test_malformed_is_absent_evidence_never_a_distinct_identity(self, raw):
        """A malformed value must not make two securities look
        different from each other."""
        assert normalize_cik(raw) is None

    def test_excess_padding_is_still_the_same_filer(self):
        """CIK 1 is a real filer id. Extra leading zeros are formatting,
        not a different identity."""
        assert normalize_cik("00000000000000001") == normalize_cik("1") == "0000000001"

    def test_is_deterministic(self):
        assert normalize_cik("1652044") == normalize_cik("0001652044")


class TestEvidenceExtraction:
    def test_no_cik_is_no_evidence(self):
        result = extract_cik_evidence("sec-1", ({"currency": "USD"}, {}))
        assert result.state is CikEvidenceState.NO_EVIDENCE
        assert result.is_linkable is False

    def test_consistent_cik_across_records_is_linkable(self):
        result = extract_cik_evidence(
            "sec-1", ({"sec_cik": "0001652044"}, {"sec_cik": "1652044"}, {"sec_cik": "0001652044"})
        )
        assert result.state is CikEvidenceState.ONE_CONSISTENT_CIK
        assert result.cik == ALPHABET_CIK
        assert result.is_linkable is True

    def test_disagreeing_records_withhold_the_security_entirely(self):
        """Atlas does not know which filer this is, so it does not pick a
        majority -- it declines."""
        result = extract_cik_evidence(
            "sec-1", ({"sec_cik": ALPHABET_CIK}, {"sec_cik": APPLE_CIK}, {"sec_cik": ALPHABET_CIK})
        )
        assert result.state is CikEvidenceState.CONTRADICTORY_CIKS
        assert result.cik is None
        assert result.is_linkable is False

    def test_malformed_alongside_valid_does_not_create_a_contradiction(self):
        result = extract_cik_evidence(
            "sec-1", ({"sec_cik": ALPHABET_CIK}, {"sec_cik": "not-a-cik"}, {"sec_cik": None})
        )
        assert result.state is CikEvidenceState.ONE_CONSISTENT_CIK

    def test_is_deterministic(self):
        metadata = ({"sec_cik": ALPHABET_CIK}, {"sec_cik": "1652044"})
        assert extract_cik_evidence("s", metadata) == extract_cik_evidence("s", metadata)


def _ev(security_id, cik):
    return SecurityCikEvidence(
        canonical_security_id=security_id,
        state=CikEvidenceState.ONE_CONSISTENT_CIK if cik else CikEvidenceState.NO_EVIDENCE,
        cik=cik,
        observed=(cik,) if cik else (),
    )


class TestPlanning:
    def test_two_securities_one_cik_yields_a_merge(self):
        plans = plan_issuer_reconciliation(
            (_ev("goog", ALPHABET_CIK), _ev("googl", ALPHABET_CIK)),
            {"goog": "issuer-b", "googl": "issuer-a"},
            {"issuer-a": _T0, "issuer-b": _T0 + timedelta(days=1)},
        )
        assert len(plans) == 1
        assert plans[0].surviving_issuer_id == "issuer-a"  # older
        assert plans[0].merged_issuer_ids == ("issuer-b",)
        assert set(plans[0].security_ids) == {"goog", "googl"}

    def test_survivor_is_the_oldest_issuer(self):
        plans = plan_issuer_reconciliation(
            (_ev("a", ALPHABET_CIK), _ev("b", ALPHABET_CIK)),
            {"a": "zzz-old", "b": "aaa-new"},
            {"zzz-old": _T0, "aaa-new": _T0 + timedelta(days=5)},
        )
        assert plans[0].surviving_issuer_id == "zzz-old"

    def test_ties_break_lexically_never_by_row_order(self):
        """Two issuers created in the same backfill share a timestamp.
        Without the tie-break the outcome would depend on database row
        order, which is an accident rather than a decision."""
        same = {"issuer-b": _T0, "issuer-a": _T0}
        first = plan_issuer_reconciliation(
            (_ev("x", ALPHABET_CIK), _ev("y", ALPHABET_CIK)), {"x": "issuer-b", "y": "issuer-a"}, same
        )
        second = plan_issuer_reconciliation(
            (_ev("y", ALPHABET_CIK), _ev("x", ALPHABET_CIK)), {"y": "issuer-a", "x": "issuer-b"}, same
        )
        assert first[0].surviving_issuer_id == second[0].surviving_issuer_id == "issuer-a"

    def test_one_issuer_for_a_cik_is_a_noop_not_a_merge(self):
        plans = plan_issuer_reconciliation(
            (_ev("a", ALPHABET_CIK),), {"a": "issuer-a"}, {"issuer-a": _T0}
        )
        assert plans[0].is_noop is True
        assert plans[0].merged_issuer_ids == ()

    def test_different_ciks_never_merge(self):
        plans = plan_issuer_reconciliation(
            (_ev("a", ALPHABET_CIK), _ev("b", APPLE_CIK)),
            {"a": "issuer-a", "b": "issuer-b"},
            {"issuer-a": _T0, "issuer-b": _T0},
        )
        assert all(p.is_noop for p in plans)

    def test_a_contradictory_security_is_excluded(self):
        contradictory = SecurityCikEvidence("bad", CikEvidenceState.CONTRADICTORY_CIKS, None, (ALPHABET_CIK, APPLE_CIK))
        plans = plan_issuer_reconciliation(
            (_ev("good", ALPHABET_CIK), contradictory),
            {"good": "issuer-a", "bad": "issuer-b"},
            {"issuer-a": _T0, "issuer-b": _T0},
        )
        assert plans[0].security_ids == ("good",)
        assert plans[0].is_noop is True

    def test_no_evidence_never_merges(self):
        plans = plan_issuer_reconciliation(
            (_ev("a", None), _ev("b", None)), {"a": "issuer-a", "b": "issuer-b"}, {}
        )
        assert plans == ()

    def test_planning_is_deterministic(self):
        args = (
            (_ev("a", ALPHABET_CIK), _ev("b", ALPHABET_CIK)),
            {"a": "issuer-b", "b": "issuer-a"},
            {"issuer-a": _T0, "issuer-b": _T0 + timedelta(days=1)},
        )
        assert plan_issuer_reconciliation(*args) == plan_issuer_reconciliation(*args)


class TestTheProofCaseByConstruction:
    """GOOG/GOOGL-shaped: one issuer, two securities, nothing merged
    that is a security."""

    def _build(self, engine):
        issuers = SqlAlchemyCanonicalIssuerRepository(engine)
        securities = SqlAlchemyCanonicalSecurityRepository(engine)
        issuer_c = CanonicalIssuer.create(legal_name="Alphabet Inc Class C", clock=lambda: _T0 + timedelta(days=1))
        issuer_a = CanonicalIssuer.create(legal_name="Alphabet Inc Class A", clock=lambda: _T0)
        issuers.save(issuer_c)
        issuers.save(issuer_a)
        goog = replace(_security("Alphabet Inc Class C", "GOOG", "XNAS", "USD"), issuer_id=issuer_c.id)
        goog = goog.add_listing(ListingRef("GOOG", MicCode("XNAS"), TradingCurrency("USD"), "NATIVE", "COMMON_STOCK", share_class="C"))
        googl = replace(_security("Alphabet Inc Class A", "GOOGL", "XNAS", "USD"), issuer_id=issuer_a.id)
        googl = googl.add_listing(ListingRef("GOOGL", MicCode("XNAS"), TradingCurrency("USD"), "NATIVE", "COMMON_STOCK", share_class="A"))
        securities.save(goog)
        securities.save(googl)
        return issuers, securities, goog, googl, issuer_a, issuer_c

    def _reconcile(self, issuers, goog, googl, issuer_a, issuer_c):
        plans = plan_issuer_reconciliation(
            (_ev(str(goog.id), ALPHABET_CIK), _ev(str(googl.id), ALPHABET_CIK)),
            {str(goog.id): str(issuer_c.id), str(googl.id): str(issuer_a.id)},
            {str(issuer_a.id): _T0, str(issuer_c.id): _T0 + timedelta(days=1)},
        )
        for plan in plans:
            for security_id in plan.security_ids:
                issuers.reassign_security_issuer(security_id, plan.surviving_issuer_id)
        return plans

    def test_they_end_up_sharing_one_issuer(self, engine):
        issuers, securities, goog, googl, issuer_a, issuer_c = self._build(engine)
        self._reconcile(issuers, goog, googl, issuer_a, issuer_c)
        assert issuers.issuer_id_for_security(str(goog.id)) == str(issuer_a.id)
        assert issuers.issuer_id_for_security(str(googl.id)) == str(issuer_a.id)

    def test_they_remain_two_distinct_securities(self, engine):
        """The invariant. Reducing issuers must never reduce
        securities."""
        issuers, securities, goog, googl, issuer_a, issuer_c = self._build(engine)
        with engine.connect() as connection:
            before = connection.execute(select(canonical_securities_table.c.id)).all()
        self._reconcile(issuers, goog, googl, issuer_a, issuer_c)
        with engine.connect() as connection:
            after = connection.execute(select(canonical_securities_table.c.id)).all()
        assert len(before) == len(after) == 2
        assert goog.id != googl.id

    def test_ticker_exchange_currency_and_share_class_survive_untouched(self, engine):
        issuers, securities, goog, googl, issuer_a, issuer_c = self._build(engine)
        self._reconcile(issuers, goog, googl, issuer_a, issuer_c)
        reloaded_goog = securities.load(str(goog.id))
        reloaded_googl = securities.load(str(googl.id))
        assert reloaded_goog.native_ticker == "GOOG"
        assert reloaded_googl.native_ticker == "GOOGL"
        assert reloaded_goog.listings[0].share_class == "C"
        assert reloaded_googl.listings[0].share_class == "A"
        assert reloaded_goog.trading_currency.value == reloaded_googl.trading_currency.value == "USD"

    def test_issuer_now_resolves_to_both_securities(self, engine):
        """Phase 12: issuer-level retrieval becomes possible."""
        issuers, securities, goog, googl, issuer_a, issuer_c = self._build(engine)
        self._reconcile(issuers, goog, googl, issuer_a, issuer_c)
        assert set(issuers.security_ids_for_issuer(str(issuer_a.id))) == {str(goog.id), str(googl.id)}

    def test_reconciliation_is_idempotent(self, engine):
        issuers, securities, goog, googl, issuer_a, issuer_c = self._build(engine)
        self._reconcile(issuers, goog, googl, issuer_a, issuer_c)
        with engine.connect() as connection:
            first = connection.execute(select(canonical_securities_table)).mappings().all()
        # Re-planning now sees both securities on one issuer -> no-op.
        plans = plan_issuer_reconciliation(
            (_ev(str(goog.id), ALPHABET_CIK), _ev(str(googl.id), ALPHABET_CIK)),
            {str(goog.id): str(issuer_a.id), str(googl.id): str(issuer_a.id)},
            {str(issuer_a.id): _T0},
        )
        assert all(p.is_noop for p in plans)
        with engine.connect() as connection:
            second = connection.execute(select(canonical_securities_table)).mappings().all()
        assert [dict(r) for r in first] == [dict(r) for r in second]


class TestSecurityDataNeverCrosses:
    def test_sharing_an_issuer_does_not_share_currency_or_exchange(self, engine):
        """A SEK Stockholm line and a USD OTC line under one issuer keep
        their own market identity."""
        issuers = SqlAlchemyCanonicalIssuerRepository(engine)
        securities = SqlAlchemyCanonicalSecurityRepository(engine)
        issuer = CanonicalIssuer.create(legal_name="Volvo AB")
        issuers.save(issuer)
        sek = replace(_security("Volvo AB", "VOLV-B", "XSTO", "SEK", country="SWE"), issuer_id=issuer.id)
        usd = replace(_security("Volvo AB", "VOLVF", "XNAS", "USD"), issuer_id=issuer.id)
        securities.save(sek)
        securities.save(usd)
        assert securities.load(str(sek.id)).trading_currency.value == "SEK"
        assert securities.load(str(usd.id)).trading_currency.value == "USD"
        assert securities.load(str(sek.id)).primary_exchange_mic.value == "XSTO"

    def test_the_plan_moves_only_the_issuer_link(self):
        """`IssuerReconciliationPlan` carries no field capable of
        changing a security's own identity."""
        plan = IssuerReconciliationPlan(cik=ALPHABET_CIK, surviving_issuer_id="i", merged_issuer_ids=(), security_ids=())
        for forbidden in ("ticker", "currency", "exchange", "price", "share_class", "quantity"):
            assert forbidden not in plan.__dataclass_fields__
