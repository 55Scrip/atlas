"""The issuer's whole class count set priced by the Case's own listing (no
class proven listed): only through a filed parity group holding at the
count's instant, over a complete class set, with no participating preferred
beside it. Synthetic shapes for each gate, the valuation basis's epoch path,
then Meta's real 10-Ks (trimmed, through the write bridge) as controls: the
2025 10-K states parity for 2022-2024; the 2023 10-K states only conversion
and per-class EPS."""
from __future__ import annotations

import ast
from dataclasses import replace
from datetime import date, datetime, timezone
from pathlib import Path

import pytest
from sqlalchemy import create_engine

from atlas.alpha.business_data_refresh.class_rights_evidence import RightsFilingSource, rights_evidence_from_instance
from atlas.alpha.class_rights_evidence.models import EvidenceStrength, RightKind
from atlas.alpha.investment_case.historical_market_cap import AlignmentQuality, ShareCountScope
from atlas.alpha.issuer_equity.composer import ClassCount, compose_issuer_common_equity_market_cap
from atlas.alpha.security_share_evidence.models import ShareClassLinkKind
from atlas.alpha.security_share_evidence.repository import SqlAlchemySecurityShareEvidenceRepository
from atlas.alpha.security_share_evidence.table import create_security_share_evidence_tables
from atlas.analysis_engine.valuation.contracts import ValuationDataGapKind as G
from atlas.analysis_engine.valuation.issuer_basis import IssuerDenominatorQuality as Q
from atlas.business_data_providers.sec_edgar_share_classes import parse_share_class_filing
from tests.unit.alpha.issuer_equity.test_class_inventory import GENERIC, REPURCHASED, TAG, axis
from tests.unit.alpha.issuer_equity.test_composer import EQUIVALENT, INSUFFICIENT, P, compose, count, price, right
from tests.unit.alpha.issuer_equity.test_valuation_basis import TestHistoryAndClaims, _epoch, _hist, _Reader
from tests.unit.alpha.security_share_evidence.test_repository import filing as annual_filing
from tests.unit.alpha.security_share_evidence.test_repository import observation

ROOT = Path(__file__).resolve().parents[4]
FIXTURES = ROOT / "tests" / "unit" / "business_data_providers" / "fixtures" / "class_rights"
NOW = datetime(2026, 9, 15, tzinfo=timezone.utc)
A, B, C = "x:ClassAMember", "x:ClassBMember", "x:ClassCMember"
PREF = "x:SeriesAPreferredMember"
LATER = "0000000001-26-000099"


def parity(start=date(2023, 1, 1), end=P, *, accession="0000000001-26-000001", members=(A, B)):
    return right(RightKind.ECONOMIC_PARITY, related=members, start=start, end=end, accession=accession)


def classes(a=900.0, b=100.0):
    return [count(A, a), count(B, b)]


def cap(counts, rights):
    return compose(counts, [price("AAA", 10.0)], rights)


class TestTheCasesListingPricesEveryClass:
    def test_a_parity_group_holding_at_the_instant_composes_equivalent(self):
        c = cap(classes(), [parity()])
        assert (c.quality, c.market_cap_low) == (EQUIVALENT, 10_000.0)
        assert "listed_class_unproven_within_parity_group" in c.gaps
        assert {x.treatment for x in c.contributions} == {"case_listing_prices_parity_class"}

    def test_no_parity_withholds(self):
        c = cap(classes(), [])
        assert c.quality is INSUFFICIENT and c.market_cap_low is None

    def test_parity_stated_only_after_the_instant_never_reaches_back(self):
        c = cap(classes(), [parity(start=date(2026, 1, 1), end=date(2026, 12, 31))])
        assert c.quality is INSUFFICIENT

    def test_parity_a_later_filing_no_longer_states_has_expired(self):
        later = right(RightKind.CLASS_INVENTORY, subject=A, equity="common", start=date(2025, 1, 1), end=date(2025, 6, 30),
                      accession=LATER)
        c = cap(classes(), [parity(start=date(2023, 1, 1), end=date(2024, 12, 31)), later])
        assert c.quality is INSUFFICIENT
        carried = cap(classes(), [parity(start=date(2023, 1, 1), end=date(2024, 12, 31))])  # nothing later read
        assert carried.quality is EQUIVALENT and "rights_carried_forward:365d" in carried.gaps

    def test_a_class_the_filing_shows_holding_shares_but_the_set_omits_withholds(self):
        facts = [axis(A, 900.0), axis(B, 100.0), axis(C, 50.0)]
        c = cap(classes(), [parity(), *facts])
        assert c.quality is INSUFFICIENT and f"class_not_counted:{C}" in c.gaps

    def test_a_complete_set_per_its_own_filing_composes(self):
        c = cap(classes(), [parity(), axis(A, 900.0), axis(B, 100.0), axis(GENERIC, 1_000.0)])
        assert c.quality is EQUIVALENT

    def test_an_ambiguous_class_axis_withholds(self):
        facts = [axis(A, 900.0), axis(B, 100.0), axis(TAG, 3.0, REPURCHASED, start=date(2025, 10, 1), kind=None)]
        c = cap(classes(), [parity(), *facts])
        assert c.quality is INSUFFICIENT and "class_inventory:ambiguous_class_axis" in c.gaps

    def test_participating_preferred_beside_the_set_withholds(self):
        inventory = right(RightKind.CLASS_INVENTORY, subject=PREF, equity="preferred")
        converted = right(RightKind.AS_CONVERTED_SHARES, subject=PREF, value=50.0, start=P, end=P)
        c = cap(classes(), [parity(), inventory, converted])
        assert c.quality is INSUFFICIENT and "participating_preferred_beside_unlisted_classes" in c.gaps

    def test_senior_preferred_is_a_claim_not_a_conflict(self):
        outstanding = right(RightKind.PREFERRED_SHARES_OUTSTANDING, subject=PREF, value=10.0, start=P, end=P)
        c = cap(classes(), [parity(), outstanding])
        assert c.quality is EQUIVALENT and "senior_equity_claims_on_free_cash_flow" in c.gaps

    def test_conversion_and_equal_eps_without_parity_are_not_equivalence(self):
        conversion = right(RightKind.CONVERTIBLE_INTO, subject=B, target=A)
        eps = [right(RightKind.EARNINGS_PER_SHARE, subject=m, value=7.65, decimals="2",
                     strength=EvidenceStrength.ACCOUNTING_CORROBORATION) for m in (A, B)]
        c = cap(classes(), [conversion, *eps])
        assert c.quality is INSUFFICIENT

    def test_parity_naming_only_some_classes_withholds(self):
        c = cap([*classes(), count(C, 10.0)], [parity()])
        assert c.quality is INSUFFICIENT

    def test_a_listed_class_keeps_its_own_path(self):
        c = cap([count(A, 900.0, "AAA"), count(B, 100.0)], [parity(), axis(C, 50.0)])
        assert c.quality is EQUIVALENT and {x.treatment for x in c.contributions} == {
            "own_listed_price", "filed_conversion_or_parity"}

    def test_without_recorded_class_facts_the_rule_is_unchanged(self):
        """The current epoch's shape (a count filing recorded under v1):
        exactly the composition it was before these guards."""
        v1 = right(RightKind.CLASS_INVENTORY, subject=A, equity="common")
        c = cap(classes(), [parity(), v1])
        assert (c.quality, c.market_cap_low) == (EQUIVALENT, 10_000.0)


class TestTheValuationBasisEpochPath:
    _build = TestHistoryAndClaims._build  # the same builder harness, not its tests

    def test_a_class_set_epoch_is_composed_at_the_epoch(self):
        priors = [_epoch(2024, "2025-02-28")]
        reader = _Reader(epoch_cap=9e9)
        hist = replace(_hist(priors[0], accession="acc-1"), market_cap=None, share_count_scope=ShareCountScope.ISSUER_CLASSES)
        basis = self._build(reader, priors, [hist])
        assert basis.epochs[0].market_cap.market_cap_low == 9e9 and basis.epochs[0].market_cap.quality is Q.EQUIVALENT
        assert ("at_epoch", date(2025, 2, 28), "acc-1", 1.0) in reader.calls

    def test_a_class_set_the_composition_withholds_is_withheld_never_proxy_priced(self):
        class Withholding(_Reader):
            def at_epoch(self, *args, **kwargs):
                composed = super().at_epoch(*args, **kwargs)
                return replace(composed, quality=__import__(
                    "atlas.alpha.issuer_equity.composer", fromlist=["DenominatorQuality"]).DenominatorQuality.INSUFFICIENT_EVIDENCE,
                    market_cap_low=None, market_cap_high=None)

        priors = [_epoch(2024, "2025-02-28")]
        hist = replace(_hist(priors[0], accession="acc-1"), market_cap=None, share_count_scope=ShareCountScope.ISSUER_CLASSES)
        basis = self._build(Withholding(), priors, [hist])
        assert basis.epochs[0].market_cap is None and basis.epochs[0].gap is G.DENOMINATOR_EVIDENCE_MISSING

    def test_an_issuer_level_epoch_still_needs_its_own_market_cap(self):
        priors = [_epoch(2024, "2025-02-28")]
        basis = self._build(_Reader(), priors, [replace(_hist(priors[0]), market_cap=None)])
        assert basis.epochs[0].market_cap is None and basis.epochs[0].gap is G.DENOMINATOR_EVIDENCE_MISSING

    def test_an_unaligned_class_set_epoch_is_withheld(self):
        priors = [_epoch(2024, "2025-02-28")]
        hist = replace(_hist(priors[0], accession="acc-1", quality=AlignmentQuality.INSUFFICIENT), market_cap=None)
        reader = _Reader(epoch_cap=9e9)
        basis = self._build(reader, priors, [hist])
        assert basis.epochs[0].gap is G.DENOMINATOR_EVIDENCE_MISSING and not any(c[0] == "at_epoch" for c in reader.calls)


# -- Meta's real 10-Ks --------------------------------------------------------------------------------------

META_CIK = "0001326801"
FILED_2025 = ("0001326801-25-000017", date(2025, 1, 30))
FILED_2023 = ("0001326801-23-000013", date(2023, 2, 2))
META_A, META_B = "us-gaap:CommonClassAMember", "us-gaap:CommonClassBMember"


def _rights(filing):
    accession, filed = filing
    source = RightsFilingSource(META_CIK, accession, "10-K", filed, f"https://www.sec.gov/Archives/edgar/data/1326801/{accession}.xml")
    return rights_evidence_from_instance(source, (FIXTURES / f"{accession}.xml").read_text(), retrieved_at=NOW, recorded_at=NOW)[1]


def _counts(filing, period):
    accession, filed = filing
    parsed = parse_share_class_filing((FIXTURES / f"{accession}.xml").read_text())
    return tuple(ClassCount(f.class_member, f.shares, f.period_end, accession, filed) for f in parsed.facts if f.period_end == period)


def _meta(counts, rights, observed, raw):
    return compose_issuer_common_equity_market_cap(META_CIK, observed, counts, {"META": price("META", raw, on=observed)},
                                                   tuple(rights), case_symbol="META")


class TestMetaControls:
    def test_the_2025_10k_states_parity_for_the_years_it_presents(self):
        (statement,) = [o for o in _rights(FILED_2025) if o.kind is RightKind.ECONOMIC_PARITY]
        assert set(statement.related_members) == {META_A, META_B} and statement.strength is EvidenceStrength.FILING_STATEMENT
        assert (statement.effective_from, statement.effective_to) == (date(2022, 1, 1), date(2024, 12, 31))
        assert "identical liquidation and dividend rights" in statement.excerpt

    def test_the_2023_10k_states_no_parity_only_per_class_eps(self):
        rights = _rights(FILED_2023)
        assert not [o for o in rights if o.kind in (RightKind.ECONOMIC_PARITY, RightKind.CONVERTIBLE_INTO)]
        fy2022 = {o.subject_member: o.value for o in rights if o.kind is RightKind.EARNINGS_PER_SHARE
                  and o.effective_to == date(2022, 12, 31)}
        assert fy2022[META_A] == fy2022[META_B] == 8.63  # accounting corroboration, never contractual

    def test_fy2022_composes_equivalent_through_parity_filed_later(self):
        counts = _counts(FILED_2023, date(2022, 12, 31))
        assert {(c.member, c.shares) for c in counts} == {(META_A, 2_247_000_000.0), (META_B, 367_000_000.0)}
        c = _meta(counts, [*_rights(FILED_2023), *_rights(FILED_2025)], date(2023, 2, 28), 174.94)
        assert (c.quality, c.market_cap_low) == (EQUIVALENT, pytest.approx(2_614_000_000 * 174.94))
        assert c.gaps == ("listed_class_unproven_within_parity_group",)

    def test_fy2022_without_the_later_statement_is_withheld(self):
        c = _meta(_counts(FILED_2023, date(2022, 12, 31)), _rights(FILED_2023), date(2023, 2, 28), 174.94)
        assert c.quality is INSUFFICIENT and c.market_cap_low is None

    def test_fy2021_is_before_any_filed_parity(self):
        c = _meta(_counts(FILED_2023, date(2021, 12, 31)), [*_rights(FILED_2023), *_rights(FILED_2025)], date(2022, 2, 28), 211.03)
        assert c.quality is INSUFFICIENT

    def test_the_count_filings_own_class_facts_account_for_both_classes(self):
        c = _meta(_counts(FILED_2023, date(2022, 12, 31)), [*_rights(FILED_2023), *_rights(FILED_2025)], date(2023, 2, 28), 174.94)
        assert not [g for g in c.gaps if g.startswith(("class_not_counted:", "class_inventory:"))]


class TestReadingTheIssuersClassSets:
    def test_every_link_kind_of_the_filer_one_query(self, tmp_path):
        engine = create_engine(f"sqlite:///{tmp_path / 's.db'}")
        create_security_share_evidence_tables(engine)
        repo = SqlAlchemySecurityShareEvidenceRepository(engine)
        obs = [observation(issuer_cik="0000000007", accession="0000000007-25-000001", class_member=m, link_kind=k,
                           context_id=f"c{i}")
               for i, (m, k) in enumerate(((A, ShareClassLinkKind.AMBIGUOUS), (B, ShareClassLinkKind.NO_LINK)))]
        repo.record_filing(annual_filing(obs, issuer_cik="0000000007", accession="0000000007-25-000001"), tuple(obs))
        got = repo.class_counts_for_issuers(frozenset({"0000000007", "0000000009"}))
        assert {o.class_member for o in got["0000000007"]} == {A, B} and got["0000000009"] == ()


class TestTheServicePassesTheIssuersClassSets:
    """Both assembly paths hand the Case's own filer's class sets to the
    historical reconstruction -- read, never written."""

    class _Repo:
        def __init__(self, sets):
            self.sets, self.asked = sets, []

        def proven_for_securities(self, cik_by_ticker):
            return {t: () for t in cik_by_ticker}

        def class_counts_for_issuers(self, ciks):
            self.asked.append(ciks)
            return {cik: self.sets.get(cik, ()) for cik in ciks}

    def _service(self, monkeypatch, sets):
        import hashlib

        import atlas.alpha.investment_case.service as service_module
        from atlas.analysis_engine.business_data.models import RawBusinessDocument
        from atlas.analysis_engine.business_data.pipeline import ingest
        from tests.unit.alpha.investment_case.test_service import _Harness, _new_engine

        harness = _Harness(_new_engine())
        harness.business_record_repository.add(ingest(RawBusinessDocument(
            identifier="SYN:FY:2025", company="SYN", source_kind="financial_statement",
            published_at=datetime(2026, 2, 1, tzinfo=timezone.utc), provider_id="sec_edgar", raw_reference="x",
            content_hash=hashlib.sha256(b"syn").hexdigest(), period_start=date(2025, 1, 1), period_end=date(2025, 12, 31),
            language="en", metadata={"sec_cik": "0000000042", "free_cash_flow": 1.0, "currency": "USD"}),
            evaluated_at=NOW).record)
        repo = self._Repo(sets)
        seen = []

        def spy(evidence, records, *, shared_issuer, security_share_counts, as_of, issuer_class_counts):
            seen.append(issuer_class_counts)
            return None

        monkeypatch.setattr(service_module, "reconstruct_historical_market_caps", spy)
        service = harness.fresh_composition_service()
        service._security_share_repository = repo
        return harness, service, repo, seen

    def test_build_and_build_many_both_pass_them(self, monkeypatch):
        sets = {"0000000042": (observation(issuer_cik="0000000042", link_kind=ShareClassLinkKind.AMBIGUOUS),)}
        harness, service, repo, seen = self._service(monkeypatch, sets)
        service.build(harness.add_to_watchlist("SYN"))
        service.build_many((harness.import_holding("SYN"),))
        assert seen == [sets["0000000042"], sets["0000000042"]]
        assert repo.asked == [frozenset({"0000000042"})] * 2


def test_no_issuer_is_named_on_the_historical_class_path():
    modules = ["atlas/alpha/investment_case/historical_market_cap.py", "atlas/alpha/investment_case/service.py",
               "atlas/alpha/issuer_equity/composer.py", "atlas/alpha/issuer_equity/valuation_basis.py",
               "atlas/alpha/security_share_evidence/repository.py"]
    names = ("META", "Meta", "Facebook", "0001326801", "1326801", "fb-", "meta-")
    for module in modules:
        tree = ast.parse((ROOT / module).read_text())
        literals = [n.value for n in ast.walk(tree) if isinstance(n, ast.Constant) and isinstance(n.value, str)]
        assert not [lit for lit in literals for name in names if name in lit], module
