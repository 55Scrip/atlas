"""Resolving an imported holding to the security it actually is.

Eleven of twenty-six followed holdings -- about 42% of portfolio weight --
resolve to no security, and not for want of evidence: the import captures an
ISIN, the provider answers an ISIN precisely, and the master holds share-class
identifiers. Nothing joined them. These tests are about that join, and about
the two ways it could be worse than leaving it undone:

* resolving the **wrong** company, which a ticker genuinely cannot prevent --
  `SU` is Schneider Electric in Paris and Suncor Energy in New York, and
  Suncor is a real row in this database;
* resolving the **right** company and then implying Atlas can analyse it,
  when identity and fundamentals coverage are separate facts.

Every FIGI and ISIN below was measured against the live provider (see
`figi_fixtures`); the provider itself is faked here so the tests are
deterministic and make no network calls.
"""
from __future__ import annotations

from datetime import datetime, timezone

import pytest

from atlas.alpha.canonical_security.models import CanonicalSecurity, ListingRef, SecurityIdentifier
from atlas.alpha.canonical_security.value_objects import MicCode, TradingCurrency
from atlas.alpha.canonical_security_gate.import_resolution import (
    ImportedIdentity,
    ImportIdentityStatus,
    resolve_imported_identity,
)
from atlas.alpha.security_identity_evidence.openfigi_adapter import (
    OpenFigiMappingResult,
    OpenFigiProviderUnavailable,
)
from tests.unit.alpha.canonical_security_gate import figi_fixtures as fx


class FakeMaster:
    """The security master, as much of it as a resolver can see."""

    def __init__(self, securities: tuple[CanonicalSecurity, ...] = ()) -> None:
        self.securities = list(securities)

    def find_by_identifier(self, identifier_type: str, value: str) -> CanonicalSecurity | None:
        for security in self.securities:
            for identifier in security.identifiers:
                if identifier.identifier_type == identifier_type and identifier.value == value:
                    return security
        return None

    def find_by_ticker_and_exchange(self, ticker: str, exchange_mic: str) -> CanonicalSecurity | None:
        for security in self.securities:
            if (
                security.native_ticker.upper() == ticker.upper()
                and security.primary_exchange_mic.value == exchange_mic
            ):
                return security
            for listing in security.listings:
                if listing.ticker.upper() == ticker.upper() and listing.exchange_mic.value == exchange_mic:
                    return security
        return None


class CountingProvider:
    """Every call is counted, because "identity resolution does not fetch"
    is a claim that has to be measurable rather than asserted in prose."""

    def __init__(self, by_isin: dict | None = None, raises: Exception | None = None) -> None:
        self.by_isin = by_isin if by_isin is not None else dict(fx.BY_ISIN)
        self.raises = raises
        self.calls: list[str] = []

    def __call__(self, isin: str) -> OpenFigiMappingResult:
        self.calls.append(isin)
        if self.raises is not None:
            raise self.raises
        return self.by_isin.get(isin, fx.NO_MATCH)

    @property
    def call_count(self) -> int:
        return len(self.calls)


def existing_security(
    *, name: str, ticker: str, mic: str, country: str, share_class: str | None = None,
    isin: str | None = None, currency: str | None = "USD",
) -> CanonicalSecurity:
    """A security already in the master, shaped like the live rows: a
    currency, a listing, and a share-class identifier from OpenFIGI."""
    security = CanonicalSecurity.discover(
        canonical_company_name=name, native_ticker=ticker,
        primary_exchange_mic=MicCode(mic), country=country,
        trading_currency=TradingCurrency(currency) if currency else None,
    ).add_listing(
        ListingRef(ticker=ticker, exchange_mic=MicCode(mic),
                   currency=TradingCurrency(currency) if currency else None,
                   relationship="NATIVE", security_type="COMMON_STOCK")
    )
    recorded = datetime(2026, 9, 16, tzinfo=timezone.utc)
    if share_class is not None:
        security = security.add_identifier(
            SecurityIdentifier(identifier_type="SHARE_CLASS_FIGI", value=share_class,
                               recorded_at=recorded, provider="OPENFIGI")
        )
    if isin is not None:
        security = security.add_identifier(
            SecurityIdentifier(identifier_type="ISIN", value=isin, recorded_at=recorded,
                               provider="BROKER_IMPORT")
        )
    return security


def volvo_row(**overrides) -> ImportedIdentity:
    """The realistic Swedish broker row this sprint exists for."""
    fields = dict(
        ticker="VOLV-B", company_name="Volvo AB ser. B", isin=fx.VOLVO_B_ISIN,
        market="Nasdaq Stockholm", account_currency="SEK",
    )
    fields.update(overrides)
    return ImportedIdentity(**fields)


def resolve(identity, master=None, provider=None):
    provider = provider or CountingProvider()
    result = resolve_imported_identity(
        identity, master=master or FakeMaster(), map_isin_fn=provider
    )
    return result, provider


# --- The strong identifier is consumed at all --------------------------


def test_a_valid_isin_reaches_the_resolver_and_creates_the_security() -> None:
    result, provider = resolve(volvo_row())
    assert result.status is ImportIdentityStatus.CONSTRUCTED
    assert provider.calls == [fx.VOLVO_B_ISIN]
    assert result.security.canonical_company_name == "VOLVO AB-B SHS"


def test_it_is_volvo_b_specifically_not_volvo_generally() -> None:
    """`VOLVO AB-B SHS` with share class BBG001S69SV8. Volvo A is a
    different security with a different share class, and "Volvo" alone is
    not a security at all."""
    result, _ = resolve(volvo_row())
    assert result.share_class_figi == fx.VOLVO_B_SHARE_CLASS
    assert result.venue_figi == "BBG000BCH2F1"
    assert "-B" in result.security.canonical_company_name


def test_an_invalid_isin_is_not_evidence_and_never_reaches_the_provider() -> None:
    result, provider = resolve(volvo_row(isin="SE0000115440"))  # check digit broken
    assert result.status is ImportIdentityStatus.INSUFFICIENT_IDENTITY
    assert provider.call_count == 0


def test_a_ticker_only_row_never_reaches_the_provider() -> None:
    """Asking a provider about a bare ticker is the question that cannot
    tell Schneider from Suncor, so it is not asked."""
    result, provider = resolve(ImportedIdentity(ticker="VOLV-B", market="Nasdaq Stockholm"))
    assert result.status is ImportIdentityStatus.INSUFFICIENT_IDENTITY
    assert provider.call_count == 0
    assert result.security is None


def test_a_company_name_alone_cannot_resolve_a_security() -> None:
    result, provider = resolve(ImportedIdentity(company_name="Volvo AB ser. B"))
    assert result.status is ImportIdentityStatus.INSUFFICIENT_IDENTITY
    assert provider.call_count == 0


# --- The master comes first --------------------------------------------


def test_a_recorded_isin_resolves_with_no_provider_call_at_all() -> None:
    master = FakeMaster((existing_security(
        name="Volvo AB", ticker="VOLV-B", mic="XSTO", country="Sweden",
        isin=fx.VOLVO_B_ISIN, currency="SEK"),))
    result, provider = resolve(volvo_row(), master)
    assert result.status is ImportIdentityStatus.RESOLVED_EXISTING
    assert result.strong_identifier_used == "ISIN"
    assert provider.call_count == 0


def test_an_existing_security_is_reused_rather_than_duplicated() -> None:
    """Broker spelling differs from Atlas's in every one of these fields,
    and none of that makes it a different security."""
    existing = existing_security(
        name="Microsoft Corporation", ticker="MSFT", mic="XNAS", country="USA",
        share_class=fx.MSFT_SHARE_CLASS)
    master = FakeMaster((existing,))
    provider = CountingProvider({"US5949181045": fx.NO_MATCH})
    provider.by_isin["US5949181045"] = OpenFigiMappingResult(matches=(
        fx.match("BBG000BPH459", "MSFT", "UW", fx.MSFT_SHARE_CLASS,
                 "MICROSOFT CORP", "BBG000BPH459"),
    ))
    result, _ = resolve(
        ImportedIdentity(ticker="msft", company_name="Microsoft Corp.",
                         isin="US5949181045", market="NASDAQ", account_currency="SEK"),
        master, provider)
    assert result.status is ImportIdentityStatus.RESOLVED_EXISTING
    assert result.strong_identifier_used == "SHARE_CLASS_FIGI"
    assert str(result.security.id) == str(existing.id)


def test_re_importing_the_same_row_is_idempotent() -> None:
    """The same row twice is the same security, and the second time costs
    nothing: the first import recorded the investor's own ISIN against the
    security it created, so the master answers before the provider is
    reached at all."""
    first, _ = resolve(volvo_row())
    assert first.status is ImportIdentityStatus.CONSTRUCTED

    second, provider = resolve(volvo_row(), FakeMaster((first.security,)))

    assert second.status is ImportIdentityStatus.RESOLVED_EXISTING
    assert str(second.security.id) == str(first.security.id)
    assert second.strong_identifier_used == "ISIN"
    assert provider.call_count == 0


def test_a_first_import_records_what_identified_the_security() -> None:
    """Both halves matter: the FIGIs make the security findable by anything
    that speaks FIGIs, and the ISIN makes the next import free."""
    result, _ = resolve(volvo_row())
    recorded = {i.identifier_type: i.value for i in result.security.identifiers}
    assert recorded == {
        "ISIN": fx.VOLVO_B_ISIN,
        "SHARE_CLASS_FIGI": fx.VOLVO_B_SHARE_CLASS,
        "FIGI": "BBG000BCH2F1",
        "COMPOSITE_FIGI": "BBG000BCH216",
    }


def test_the_imported_isin_is_not_credited_to_the_provider() -> None:
    """OpenFIGI consumes an ISIN and never returns one. Labelling the
    investor's own identifier `OPENFIGI` would turn one unverified source
    into two apparently agreeing ones."""
    result, _ = resolve(volvo_row())
    by_type = {i.identifier_type: i for i in result.security.identifiers}
    assert by_type["ISIN"].provider == "BROKER_IMPORT"
    assert by_type["SHARE_CLASS_FIGI"].provider == "OPENFIGI"
    assert by_type["FIGI"].provider == "OPENFIGI"
    assert by_type["SHARE_CLASS_FIGI"].query_value == fx.VOLVO_B_ISIN


def test_a_later_stronger_import_adds_evidence_without_overwriting() -> None:
    """A legacy holding resolved weakly, then a real broker export arrives
    carrying an ISIN. The identifier list is append-only, so the earlier
    evidence is still there to read afterwards."""
    legacy = existing_security(
        name="Volvo AB", ticker="VOLV-B", mic="XSTO", country="Sweden",
        share_class=fx.VOLVO_B_SHARE_CLASS, currency=None)
    before = tuple(legacy.identifiers)

    result, _ = resolve(volvo_row(), FakeMaster((legacy,)))

    assert result.status is ImportIdentityStatus.RESOLVED_EXISTING
    assert tuple(legacy.identifiers) == before  # the aggregate is immutable
    assert str(result.security.id) == str(legacy.id)


# --- Wrong-company firewall --------------------------------------------


def test_schneider_resolves_schneider() -> None:
    result, _ = resolve(ImportedIdentity(
        ticker="SU.PA", company_name="Schneider Electric", isin=fx.SCHNEIDER_ISIN,
        market="Euronext Paris", account_currency="SEK"))
    assert result.status is ImportIdentityStatus.CONSTRUCTED
    assert result.security.canonical_company_name == "SCHNEIDER ELECTRIC SE"
    assert result.security.country == "France"
    assert result.share_class_figi == fx.SCHNEIDER_SHARE_CLASS


def test_schneider_can_never_resolve_to_suncor() -> None:
    """The negative control that motivated the whole identity programme.
    Suncor is in the live master; Schneider is not. They share the ticker
    `SU` and nothing else."""
    suncor = existing_security(
        name="Suncor Energy Inc", ticker="SU", mic="XNYS", country="USA",
        share_class=fx.SUNCOR_SHARE_CLASS)
    result, _ = resolve(
        ImportedIdentity(ticker="SU.PA", company_name="Schneider Electric",
                         isin=fx.SCHNEIDER_ISIN, market="Euronext Paris"),
        FakeMaster((suncor,)))
    assert "SUNCOR" not in result.security.canonical_company_name.upper()
    assert result.share_class_figi != fx.SUNCOR_SHARE_CLASS
    assert str(result.security.id) != str(suncor.id)


def test_the_two_su_share_classes_are_not_the_same_string() -> None:
    assert fx.SCHNEIDER_SHARE_CLASS != fx.SUNCOR_SHARE_CLASS


def test_a_taiwan_ordinary_share_never_becomes_the_new_york_adr() -> None:
    """TSM in the master is the ADR. The ordinary share is a different
    security of the same issuer, and only a share class can say so."""
    tsm_adr = existing_security(
        name="Taiwan Semiconductor Manufacturing", ticker="TSM", mic="XNYS",
        country="USA", share_class=fx.TSM_ADR_SHARE_CLASS)
    result, _ = resolve(
        ImportedIdentity(ticker="2330", company_name="TSMC",
                         isin=fx.TSMC_ORDINARY_ISIN, market="Taiwan Stock Exchange"),
        FakeMaster((tsm_adr,)))
    assert result.status is ImportIdentityStatus.CONSTRUCTED
    assert str(result.security.id) != str(tsm_adr.id)
    assert result.security.country == "Taiwan"
    assert result.share_class_figi == fx.TSMC_ORDINARY_SHARE_CLASS


def test_the_existing_tsm_adr_is_untouched_by_a_taiwan_import() -> None:
    tsm_adr = existing_security(
        name="Taiwan Semiconductor Manufacturing", ticker="TSM", mic="XNYS",
        country="USA", share_class=fx.TSM_ADR_SHARE_CLASS)
    before = (tsm_adr.canonical_company_name, tsm_adr.primary_exchange_mic.value,
              tuple(i.value for i in tsm_adr.identifiers))
    resolve(ImportedIdentity(ticker="2330", isin=fx.TSMC_ORDINARY_ISIN,
                             market="Taiwan Stock Exchange"), FakeMaster((tsm_adr,)))
    assert (tsm_adr.canonical_company_name, tsm_adr.primary_exchange_mic.value,
            tuple(i.value for i in tsm_adr.identifiers)) == before


def test_an_adr_and_its_ordinary_share_stay_separate_securities() -> None:
    """Same issuer, different securities. NVO is the New York ADR; the
    Copenhagen B share is what a Danish broker would export."""
    nvo = existing_security(name="Novo Nordisk A/S", ticker="NVO", mic="XNYS",
                            country="USA", share_class=fx.NVO_ADR_SHARE_CLASS)
    result, _ = resolve(
        ImportedIdentity(ticker="NOVO-B", company_name="Novo Nordisk B",
                         isin=fx.NOVO_B_ORDINARY_ISIN, market="Nasdaq Copenhagen"),
        FakeMaster((nvo,)))
    assert result.status is ImportIdentityStatus.CONSTRUCTED
    assert str(result.security.id) != str(nvo.id)
    assert result.security.country == "Denmark"
    assert fx.NOVO_ORDINARY_SHARE_CLASS != fx.NVO_ADR_SHARE_CLASS


def test_goog_and_googl_remain_different_securities() -> None:
    """Two share classes of one issuer, distinguished by the only field
    that distinguishes them."""
    goog = existing_security(name="Alphabet Inc Class C", ticker="GOOG", mic="XNAS",
                             country="USA", share_class=fx.GOOG_SHARE_CLASS)
    googl = existing_security(name="Alphabet Inc Class A", ticker="GOOGL", mic="XNAS",
                              country="USA", share_class=fx.GOOGL_SHARE_CLASS)
    master = FakeMaster((goog, googl))
    provider = CountingProvider({"US02079K1079": OpenFigiMappingResult(matches=(
        fx.match("BBG009S3NB30", "GOOGL", "UW", fx.GOOGL_SHARE_CLASS,
                 "ALPHABET INC-CL A", "BBG009S3NB30"),))})
    result, _ = resolve(
        ImportedIdentity(ticker="GOOGL", isin="US02079K1079", market="NASDAQ"),
        master, provider)
    assert str(result.security.id) == str(googl.id)
    assert str(result.security.id) != str(goog.id)
    assert fx.GOOG_SHARE_CLASS != fx.GOOGL_SHARE_CLASS


# --- Conflict withholds ------------------------------------------------


def test_an_isin_and_a_ticker_naming_different_securities_withholds() -> None:
    """The brief's own example: strong evidence says A, weak evidence says
    B. Preferring either silently is how a holding ends up behind the wrong
    company, so neither is used."""
    suncor_at_nyse = existing_security(
        name="Suncor Energy Inc", ticker="SU", mic="XNYS", country="USA",
        share_class=fx.SUNCOR_SHARE_CLASS)
    result, _ = resolve(
        ImportedIdentity(ticker="SU", company_name="Schneider Electric",
                         isin=fx.SCHNEIDER_ISIN, market="NYSE"),
        FakeMaster((suncor_at_nyse,)))
    assert result.status is ImportIdentityStatus.IDENTITY_CONFLICT
    assert result.security is None


def test_a_conflict_withholds_even_when_both_securities_are_already_known() -> None:
    """The same disagreement, one step later: the strong identifier matches
    a security Atlas already holds, and the ticker and venue match a
    *different* one it also already holds. Accepting the strong answer here
    would be silently overruling contradictory evidence rather than never
    having seen it -- so this path withholds too.
    """
    suncor = existing_security(
        name="Suncor Energy Inc", ticker="SU", mic="XNYS", country="USA",
        share_class=fx.SUNCOR_SHARE_CLASS)
    schneider = existing_security(
        name="Schneider Electric SE", ticker="SU.PA", mic="XPAR", country="France",
        share_class=fx.SCHNEIDER_SHARE_CLASS, currency=None)

    result, _ = resolve(
        ImportedIdentity(ticker="SU", company_name="Schneider Electric",
                         isin=fx.SCHNEIDER_ISIN, market="NYSE"),
        FakeMaster((suncor, schneider)))

    assert result.status is ImportIdentityStatus.IDENTITY_CONFLICT
    assert result.security is None


def test_a_matching_ticker_on_the_same_security_is_not_a_conflict() -> None:
    """The check must fire on disagreement, not on agreement -- otherwise
    every ordinary re-import would withhold."""
    volvo = existing_security(
        name="Volvo AB", ticker="VOLV-B", mic="XSTO", country="Sweden",
        share_class=fx.VOLVO_B_SHARE_CLASS, currency=None)
    result, _ = resolve(volvo_row(), FakeMaster((volvo,)))
    assert result.status is ImportIdentityStatus.RESOLVED_EXISTING
    assert str(result.security.id) == str(volvo.id)


def test_an_isin_naming_two_share_classes_withholds() -> None:
    """Constructed deliberately: no real ISIN behaves this way, which is
    exactly why the rule needs a test rather than a sighting."""
    provider = CountingProvider({"SE0000115446": OpenFigiMappingResult(matches=(
        fx.match("BBG000BCH2F1", "VOLVB", "SS", "BBG001S69SV8", "VOLVO AB-B SHS"),
        fx.match("BBG000BCH2F2", "VOLVA", "SS", "BBG001S69SV9", "VOLVO AB-A SHS"),
    ))})
    result, _ = resolve(volvo_row(), provider=provider)
    assert result.status is ImportIdentityStatus.IDENTITY_CONFLICT
    assert result.security is None


def test_two_listings_at_the_same_venue_withhold() -> None:
    provider = CountingProvider({"SE0000115446": OpenFigiMappingResult(matches=(
        fx.match("BBG000BCH2F1", "VOLVB", "SS", fx.VOLVO_B_SHARE_CLASS, "VOLVO AB-B SHS"),
        fx.match("BBG000BCH2F9", "VOLVB", "SS", fx.VOLVO_B_SHARE_CLASS, "VOLVO AB-B SHS"),
    ))})
    result, _ = resolve(volvo_row(), provider=provider)
    assert result.status is ImportIdentityStatus.IDENTITY_CONFLICT


def test_rows_with_no_share_class_are_ignored_rather_than_counted_as_conflict() -> None:
    """Seven of Volvo B's 209 real listings carry no share class. Treating
    those as disagreement would reject a completely unambiguous ISIN."""
    result, _ = resolve(volvo_row())
    assert result.status is ImportIdentityStatus.CONSTRUCTED
    assert any(m.share_class_figi is None for m in fx.VOLVO_B.matches)


def test_a_share_class_with_no_listing_at_the_named_venue_is_no_match() -> None:
    result, _ = resolve(volvo_row(market="Euronext Paris"))
    assert result.status is ImportIdentityStatus.NO_MATCH
    assert result.security is None


def test_an_unknown_venue_withholds_creation() -> None:
    """Strong ISIN, unmappable market. A venue listing must not be picked
    for the investor."""
    result, provider = resolve(volvo_row(market="Some Regional Exchange"))
    assert result.status is ImportIdentityStatus.INSUFFICIENT_IDENTITY
    assert result.security is None
    assert result.share_class_figi == fx.VOLVO_B_SHARE_CLASS  # known, but unusable alone


def test_an_unknown_venue_still_matches_an_existing_security() -> None:
    """Phase I's distinction: venue is needed to *create*, not to
    *recognise* -- the existing security already pins its own venue."""
    known = existing_security(name="Volvo AB", ticker="VOLV-B", mic="XSTO",
                              country="Sweden", share_class=fx.VOLVO_B_SHARE_CLASS,
                              currency="SEK")
    result, _ = resolve(volvo_row(market=None), FakeMaster((known,)))
    assert result.status is ImportIdentityStatus.RESOLVED_EXISTING
    assert str(result.security.id) == str(known.id)


def test_an_unknown_isin_is_no_match_not_a_conflict() -> None:
    result, provider = resolve(volvo_row(isin="SE0000108656"))
    assert result.status is ImportIdentityStatus.NO_MATCH
    assert provider.call_count == 1


def test_a_provider_failure_is_reported_as_itself() -> None:
    """Says nothing about the security -- distinct from `NO_MATCH`, which
    is the provider answering honestly that it knows nothing."""
    provider = CountingProvider(raises=OpenFigiProviderUnavailable("connection reset"))
    result, _ = resolve(volvo_row(), provider=provider)
    assert result.status is ImportIdentityStatus.PROVIDER_UNAVAILABLE
    assert result.security is None


# --- Account currency stays out of identity ----------------------------


def test_the_account_currency_never_becomes_the_trading_currency() -> None:
    """All 25 live holdings carry `SEK` because that is the account's
    reporting currency, Microsoft included. A Stockholm listing quoting in
    SEK does not make that value evidence."""
    result, _ = resolve(volvo_row(account_currency="SEK"))
    assert result.security.trading_currency is None
    assert all(listing.currency is None for listing in result.security.listings)


def test_the_account_currency_never_chooses_the_venue_or_country() -> None:
    result, _ = resolve(ImportedIdentity(
        ticker="SU.PA", isin=fx.SCHNEIDER_ISIN, market="Euronext Paris",
        account_currency="SEK"))
    assert result.exchange_mic == "XPAR"
    assert result.security.country == "France"


@pytest.mark.parametrize("account_currency", ["SEK", "USD", "EUR", None])
def test_resolution_is_identical_whatever_the_account_reports_in(account_currency) -> None:
    result, _ = resolve(volvo_row(account_currency=account_currency))
    assert result.share_class_figi == fx.VOLVO_B_SHARE_CLASS
    assert result.venue_figi == "BBG000BCH2F1"
    assert result.security.trading_currency is None


# --- The Swedish holdings, end to end ----------------------------------


@pytest.mark.parametrize(
    "ticker,name,isin,expected_name,expected_share_class,expected_venue_figi",
    [
        ("VOLV-B", "Volvo AB ser. B", fx.VOLVO_B_ISIN, "VOLVO AB-B SHS",
         fx.VOLVO_B_SHARE_CLASS, "BBG000BCH2F1"),
        ("ASSA-B", "ASSA ABLOY AB ser. B", fx.ASSA_B_ISIN, "ASSA ABLOY AB-B",
         fx.ASSA_B_SHARE_CLASS, "BBG000BGRY70"),
        ("ATCO-B", "Atlas Copco AB ser. B", fx.ATCO_B_ISIN, "ATLAS COPCO AB-B SHS",
         fx.ATCO_B_SHARE_CLASS, "BBG000BBM5J6"),
        ("INVE-B", "Investor AB ser. B", fx.INVE_B_ISIN, "INVESTOR AB-B SHS",
         fx.INVE_B_SHARE_CLASS, "BBG000BG97S6"),
    ],
)
def test_a_stockholm_holding_resolves_to_its_exact_security(
    ticker, name, isin, expected_name, expected_share_class, expected_venue_figi
) -> None:
    result, _ = resolve(ImportedIdentity(
        ticker=ticker, company_name=name, isin=isin,
        market="Nasdaq Stockholm", account_currency="SEK"))
    assert result.status is ImportIdentityStatus.CONSTRUCTED
    assert result.security.canonical_company_name == expected_name
    assert result.share_class_figi == expected_share_class
    assert result.venue_figi == expected_venue_figi
    assert result.security.primary_exchange_mic.value == "XSTO"
    assert result.security.country == "Sweden"
    assert result.security.trading_currency is None
    assert result.security.resolution_status == "CANONICAL"


def test_the_b_share_is_not_the_a_share() -> None:
    """`SE0017486889` looks like Atlas Copco B and is Atlas Copco A -- the
    provider said so. One character of an ISIN is a whole other security,
    which is why the ticker `ATCO-B` can never be the key."""
    result, _ = resolve(ImportedIdentity(
        ticker="ATCO-B", isin=fx.ATCO_B_ISIN, market="Nasdaq Stockholm"))
    assert result.security.canonical_company_name == "ATLAS COPCO AB-B SHS"
    assert "-A" not in result.security.canonical_company_name


def test_the_broker_ticker_survives_rather_than_the_providers_spelling() -> None:
    """OpenFIGI calls it `VOLVB`; the investor's broker calls it `VOLV-B`,
    and so does the rest of Atlas. The provider's own spelling is kept as
    evidence rather than overwriting the investor's."""
    result, _ = resolve(volvo_row())
    assert result.security.native_ticker == "VOLV-B"


# --- Resolution is not coverage ----------------------------------------


def test_resolution_creates_no_business_record_and_fetches_nothing() -> None:
    """A resolved Stockholm security has identity and nothing else. The
    aggregate cannot even hold financial data, and the resolver imports no
    fundamentals module -- checked structurally below."""
    result, provider = resolve(volvo_row())
    assert result.status is ImportIdentityStatus.CONSTRUCTED
    assert provider.call_count == 1
    assert not hasattr(result.security, "business_record")
    assert result.security.resolution_status == "CANONICAL"  # never ACTIVE


def test_the_resolver_cannot_reach_a_fundamentals_source() -> None:
    """Structural, not behavioural: a fetch cannot be triggered by code
    that has no way to name a fundamentals provider.

    Tested by reading the module's imports rather than its text -- prose
    about not fetching fundamentals contains the word "fundamentals", and a
    substring search would fail on the documentation of the very property
    it is checking.
    """
    import ast
    import inspect

    from atlas.alpha.canonical_security_gate import import_resolution

    tree = ast.parse(inspect.getsource(import_resolution))
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module)

    forbidden = (
        "atlas.business_data_providers",
        "atlas.analysis_engine",
        "atlas.alpha.business_data_refresh",
        "atlas.alpha.security_discovery.sec_source",
        "atlas.alpha.issuer_equity",
    )
    reachable = sorted(m for m in imported if m.startswith(forbidden))
    assert not reachable, f"import resolver can reach a data source: {reachable}"
