"""Issuer Identity Foundation -- the three-layer separation and the
hazards that motivated it.

Every case here comes from a real identity problem found during
Calibration Phase 8, not from imagination:

* Alpha Vantage returned `VOLVF` (Volvo AB) and `VLVOF` (**Volvo Car
  AB**) tied at match score 0.8000 -- two different companies, identical
  provider confidence.
* The portfolio holds `SU.PA` (Schneider Electric) while the database
  holds `SU` (Suncor Energy).
* The portfolio holds `TSMC` while Alpha Vantage covers `TSM`.
* SEC needs `BRK-B` where the portfolio holds `BRK.B`.

The governing rule these tests exist to enforce: **wrong-company data is
worse than missing data.** Every tie resolves toward Unknown.
"""
from __future__ import annotations

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.pool import StaticPool

from atlas.alpha.canonical_security.exceptions import (
    IssuerEquivalenceEvidenceTooWeakError,
    UnsupportedShareClassError,
)
from atlas.alpha.canonical_security.issuer import (
    STRONG_ISSUER_EVIDENCE,
    WEAK_ISSUER_EVIDENCE,
    CanonicalIssuer,
    IssuerEquivalenceEvidence,
    IssuerIdentifier,
    may_link_to_existing_issuer,
    require_strong_issuer_evidence,
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
from atlas.alpha.canonical_security.value_objects import (
    MicCode,
    TradingCurrency,
    validate_share_class,
)


@pytest.fixture
def engine():
    engine = create_engine(
        "sqlite:///:memory:", future=True, poolclass=StaticPool, connect_args={"check_same_thread": False}
    )
    # `SqlAlchemyCanonicalSecurityRepository` does not create its own
    # tables (only the issuer repository does), so create them here.
    create_canonical_security_tables(engine)
    return engine


def _security(name: str, ticker: str, mic: str, currency: str, country: str = "SWE"):
    return CanonicalSecurity.discover(
        canonical_company_name=name,
        native_ticker=ticker,
        primary_exchange_mic=MicCode(mic),
        country=country,
        trading_currency=TradingCurrency(currency),
    )


def _listing(ticker: str, mic: str, currency: str, *, share_class="UNKNOWN", relationship="NATIVE"):
    return ListingRef(
        ticker=ticker,
        exchange_mic=MicCode(mic),
        currency=TradingCurrency(currency),
        relationship=relationship,
        security_type="COMMON_STOCK",
        share_class=share_class,
    )


class TestIssuerIsNotASecurity:
    def test_issuer_carries_no_instrument_attributes(self):
        """The whole point: naming Volvo AB must not require asserting a
        ticker, an exchange or a currency."""
        issuer = CanonicalIssuer.create(legal_name="Volvo AB", jurisdiction="SWE")
        for forbidden in ("ticker", "exchange", "exchange_mic", "trading_currency", "currency", "share_class", "provider_symbol"):
            assert not hasattr(issuer, forbidden), forbidden

    def test_issuer_requires_a_legal_name(self):
        with pytest.raises(ValueError):
            CanonicalIssuer.create(legal_name="   ")

    def test_isin_is_not_an_issuer_identifier(self):
        """An ISIN names a security. Allowing it here would put both
        layers back in one identifier space."""
        from atlas.alpha.canonical_security.exceptions import (
            UnsupportedIssuerIdentifierTypeError,
        )

        with pytest.raises(UnsupportedIssuerIdentifierTypeError):
            IssuerIdentifier(identifier_type="ISIN", value="SE0000115446")  # type: ignore[arg-type]

    def test_issuer_identifiers_are_idempotent(self):
        issuer = CanonicalIssuer.create(legal_name="Volvo AB")
        identifier = IssuerIdentifier(identifier_type="LEI", value="549300ABCDEF")
        once = issuer.add_identifier(identifier)
        twice = once.add_identifier(identifier)
        assert len(twice.identifiers) == 1
        assert twice.identifier_of("LEI") == "549300ABCDEF"


class TestWeakEvidenceCanNeverMergeIssuers:
    def test_name_similarity_alone_is_refused(self):
        evidence = IssuerEquivalenceEvidence(frozenset({"COMPANY_NAME_SIMILARITY"}))
        assert may_link_to_existing_issuer(evidence) is False

    def test_exact_name_match_alone_is_still_refused(self):
        """Deliberately asymmetric. An exact name match is still a name,
        and name comparison was shown to fail in both directions at
        once."""
        evidence = IssuerEquivalenceEvidence(frozenset({"COMPANY_NAME_EXACT_MATCH"}))
        assert may_link_to_existing_issuer(evidence) is False

    def test_every_weak_kind_combined_is_still_refused(self):
        """The Volvo tie in one assertion: no accumulation of
        resemblance reaches a merge."""
        evidence = IssuerEquivalenceEvidence(WEAK_ISSUER_EVIDENCE)
        assert may_link_to_existing_issuer(evidence) is False
        with pytest.raises(IssuerEquivalenceEvidenceTooWeakError):
            require_strong_issuer_evidence(evidence)

    def test_provider_match_score_is_weak(self):
        """`VOLVF` and `VLVOF` both scored 0.8000 and are different
        companies, so a score can never be strong evidence."""
        assert "PROVIDER_MATCH_SCORE" in WEAK_ISSUER_EVIDENCE
        assert "PROVIDER_MATCH_SCORE" not in STRONG_ISSUER_EVIDENCE

    @pytest.mark.parametrize("kind", sorted(STRONG_ISSUER_EVIDENCE))
    def test_each_strong_kind_alone_permits_a_link(self, kind):
        assert may_link_to_existing_issuer(IssuerEquivalenceEvidence(frozenset({kind}))) is True

    def test_strong_and_weak_together_still_permits(self):
        evidence = IssuerEquivalenceEvidence(WEAK_ISSUER_EVIDENCE | {"LEI"})
        assert may_link_to_existing_issuer(evidence) is True

    def test_the_two_vocabularies_never_overlap(self):
        assert not (STRONG_ISSUER_EVIDENCE & WEAK_ISSUER_EVIDENCE)


class TestShareClassIsSecurityIdentity:
    def test_share_class_lives_on_the_listing_not_the_issuer(self):
        assert "share_class" in ListingRef.__dataclass_fields__
        assert "share_class" not in CanonicalIssuer.__dataclass_fields__

    def test_defaults_to_unknown_and_is_never_guessed(self):
        """`VOLV-B` ends in B, and that is still not evidence: the `-B`
        is a Nasdaq Stockholm convention, the `.B` in `BRK.B` a
        different one, and no approved mapping exists for either."""
        assert _listing("VOLV-B", "XSTO", "SEK").share_class == "UNKNOWN"

    def test_a_and_b_are_distinguishable(self):
        a = _listing("VOLV-A", "XSTO", "SEK", share_class="A")
        b = _listing("VOLV-B", "XSTO", "SEK", share_class="B")
        assert a.share_class != b.share_class

    def test_adr_is_not_a_share_class(self):
        """`ListingRelationship` already owns that fact; encoding it
        twice would let the two disagree."""
        with pytest.raises(UnsupportedShareClassError):
            validate_share_class("ADR")

    def test_unknown_and_other_are_not_interchangeable(self):
        assert validate_share_class("UNKNOWN") != validate_share_class("OTHER")


class TestOneIssuerManySecurities:
    def test_an_issuer_can_own_several_distinct_securities(self, engine):
        issuers = SqlAlchemyCanonicalIssuerRepository(engine)
        securities = SqlAlchemyCanonicalSecurityRepository(engine)
        volvo = CanonicalIssuer.create(legal_name="Volvo AB", jurisdiction="SWE")
        issuers.save(volvo)

        stockholm = _security("Volvo AB", "VOLV-B", "XSTO", "SEK")
        stockholm = stockholm.add_listing(_listing("VOLV-B", "XSTO", "SEK", share_class="B"))
        otc = _security("Volvo AB", "VOLVF", "XNAS", "USD", country="USA")
        otc = otc.add_listing(_listing("VOLVF", "XNAS", "USD", share_class="B", relationship="OTC"))

        from dataclasses import replace

        securities.save(replace(stockholm, issuer_id=volvo.id))
        securities.save(replace(otc, issuer_id=volvo.id))

        with engine.connect() as connection:
            rows = connection.execute(
                select(canonical_securities_table.c.native_ticker).where(
                    canonical_securities_table.c.issuer_id == str(volvo.id)
                )
            ).all()
        assert {r[0] for r in rows} == {"VOLV-B", "VOLVF"}

    def test_they_remain_separate_securities_with_their_own_currency(self, engine):
        """Same issuer must never mean same security -- SEK and USD lines
        stay distinct rows."""
        securities = SqlAlchemyCanonicalSecurityRepository(engine)
        issuers = SqlAlchemyCanonicalIssuerRepository(engine)
        volvo = CanonicalIssuer.create(legal_name="Volvo AB")
        issuers.save(volvo)
        from dataclasses import replace

        sek = replace(_security("Volvo AB", "VOLV-B", "XSTO", "SEK"), issuer_id=volvo.id)
        usd = replace(_security("Volvo AB", "VOLVF", "XNAS", "USD", country="USA"), issuer_id=volvo.id)
        securities.save(sek)
        securities.save(usd)

        assert securities.load(str(sek.id)).trading_currency.value == "SEK"
        assert securities.load(str(usd.id)).trading_currency.value == "USD"
        assert sek.id != usd.id

    def test_issuer_is_recoverable_from_a_security(self, engine):
        issuers = SqlAlchemyCanonicalIssuerRepository(engine)
        securities = SqlAlchemyCanonicalSecurityRepository(engine)
        volvo = CanonicalIssuer.create(legal_name="Volvo AB")
        issuers.save(volvo)
        from dataclasses import replace

        security = replace(_security("Volvo AB", "VOLV-B", "XSTO", "SEK"), issuer_id=volvo.id)
        securities.save(security)
        assert issuers.issuer_id_for_security(str(security.id)) == str(volvo.id)

    def test_unresolved_security_yields_no_issuer_rather_than_a_guess(self, engine):
        issuers = SqlAlchemyCanonicalIssuerRepository(engine)
        assert issuers.issuer_id_for_security("not-a-real-security-id") is None


class TestTheRealHazards:
    """A, B, F and G from the sprint's safety matrix."""

    def test_volvo_ab_and_volvo_car_ab_are_different_issuers(self, engine):
        issuers = SqlAlchemyCanonicalIssuerRepository(engine)
        trucks = CanonicalIssuer.create(legal_name="Volvo AB", jurisdiction="SWE")
        cars = CanonicalIssuer.create(legal_name="Volvo Car AB", jurisdiction="SWE")
        issuers.save(trucks)
        issuers.save(cars)
        assert trucks.id != cars.id
        # And nothing in the model can join them without strong evidence.
        assert may_link_to_existing_issuer(
            IssuerEquivalenceEvidence(frozenset({"COMPANY_NAME_SIMILARITY", "COUNTRY_MATCH", "INDUSTRY_MATCH"}))
        ) is False

    def test_schneider_and_suncor_can_never_collapse(self, engine):
        """`SU.PA` vs `SU`. Two independent guarantees: they are separate
        securities, and no weak evidence can join their issuers."""
        from atlas.alpha.canonical_security_resolution.normalization import normalize_ticker

        assert normalize_ticker("SU.PA") != normalize_ticker("SU")
        securities = SqlAlchemyCanonicalSecurityRepository(engine)
        schneider = _security("Schneider Electric SE", "SU.PA", "XPAR", "EUR", country="FRA")
        suncor = _security("Suncor Energy Inc", "SU", "XNYS", "USD", country="USA")
        securities.save(schneider)
        securities.save(suncor)
        assert schneider.id != suncor.id
        assert may_link_to_existing_issuer(
            IssuerEquivalenceEvidence(frozenset({"TICKER_SIMILARITY"}))
        ) is False

    def test_same_name_different_issuer_does_not_auto_merge(self):
        assert may_link_to_existing_issuer(
            IssuerEquivalenceEvidence(frozenset({"COMPANY_NAME_EXACT_MATCH", "INDUSTRY_MATCH"}))
        ) is False

    def test_tsmc_and_tsm_are_representable_but_not_auto_linked(self, engine):
        """C: the model can express same-issuer/different-security, but
        nothing links them without evidence."""
        securities = SqlAlchemyCanonicalSecurityRepository(engine)
        native = _security("Taiwan Semiconductor Manufacturing", "TSMC", "XTAI", "USD", country="TWN")
        adr = _security("Taiwan Semiconductor Manufacturing", "TSM", "XNYS", "USD", country="USA")
        securities.save(native)
        securities.save(adr)
        assert native.issuer_id is None and adr.issuer_id is None
        assert may_link_to_existing_issuer(
            IssuerEquivalenceEvidence(frozenset({"COMPANY_NAME_EXACT_MATCH"}))
        ) is False


class TestGateCreatesAnIssuerConservatively:
    def test_new_security_gets_its_own_issuer_never_a_shared_one(self, engine):
        """Phase 13's safe default: create, never reuse. Two securities
        with the *same* company name still get two issuers, because the
        only evidence available is a name."""
        from atlas.alpha.canonical_security_gate.factory import build_identity_gate

        gate = build_identity_gate(engine)
        first = gate._ensure_issuer(_security("Volvo AB", "VOLV-B", "XSTO", "SEK"))
        second = gate._ensure_issuer(_security("Volvo AB", "VOLVF", "XNAS", "USD", country="USA"))
        assert first.issuer_id is not None and second.issuer_id is not None
        assert first.issuer_id != second.issuer_id

    def test_is_idempotent_for_an_already_linked_security(self, engine):
        from atlas.alpha.canonical_security_gate.factory import build_identity_gate

        gate = build_identity_gate(engine)
        once = gate._ensure_issuer(_security("Volvo AB", "VOLV-B", "XSTO", "SEK"))
        twice = gate._ensure_issuer(once)
        assert once.issuer_id == twice.issuer_id


class TestBackwardCompatibility:
    def test_pre_issuer_securities_still_load(self, engine):
        """A row written before the issuer layer existed has
        `issuer_id=None` -- meaning "recorded earlier", never "belongs to
        no company"."""
        securities = SqlAlchemyCanonicalSecurityRepository(engine)
        security = _security("Microsoft Corporation", "MSFT", "XNAS", "USD", country="USA")
        securities.save(security)
        loaded = securities.load(str(security.id))
        assert loaded is not None
        assert loaded.issuer_id is None

    def test_listings_without_share_class_load_as_unknown(self, engine):
        securities = SqlAlchemyCanonicalSecurityRepository(engine)
        security = _security("Microsoft Corporation", "MSFT", "XNAS", "USD", country="USA")
        security = security.add_listing(_listing("MSFT", "XNAS", "USD"))
        securities.save(security)
        loaded = securities.load(str(security.id))
        assert loaded.listings[0].share_class == "UNKNOWN"

    def test_round_trip_preserves_issuer_and_share_class(self, engine):
        from dataclasses import replace

        issuers = SqlAlchemyCanonicalIssuerRepository(engine)
        securities = SqlAlchemyCanonicalSecurityRepository(engine)
        volvo = CanonicalIssuer.create(legal_name="Volvo AB")
        issuers.save(volvo)
        security = replace(_security("Volvo AB", "VOLV-B", "XSTO", "SEK"), issuer_id=volvo.id)
        security = security.add_listing(_listing("VOLV-B", "XSTO", "SEK", share_class="B"))
        securities.save(security)
        loaded = securities.load(str(security.id))
        assert str(loaded.issuer_id) == str(volvo.id)
        assert loaded.listings[0].share_class == "B"


class TestDeterminism:
    def test_evidence_evaluation_is_pure(self):
        evidence = IssuerEquivalenceEvidence(frozenset({"COMPANY_NAME_EXACT_MATCH"}))
        assert may_link_to_existing_issuer(evidence) is may_link_to_existing_issuer(evidence)

    def test_no_name_based_issuer_lookup_exists(self):
        """Structural: offering one would put the forbidden merge a
        single convenient call away."""
        assert not hasattr(SqlAlchemyCanonicalIssuerRepository, "find_by_legal_name")
        assert not hasattr(SqlAlchemyCanonicalIssuerRepository, "find_by_name")
