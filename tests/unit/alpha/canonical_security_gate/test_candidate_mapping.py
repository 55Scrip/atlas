"""`candidate_mapping.candidates_from_documents` -- Sprint O Phase 3."""
from __future__ import annotations

from datetime import datetime, timezone

from atlas.alpha.canonical_security_gate.candidate_mapping import candidates_from_documents
from atlas.analysis_engine.business_data.models import RawBusinessDocument

_NOW = datetime(2026, 8, 18, tzinfo=timezone.utc)


def _profile_doc(*, provider_id: str = "alpha_vantage", metadata: dict) -> RawBusinessDocument:
    return RawBusinessDocument(
        identifier="AAPL:profile",
        company="AAPL",
        source_kind="company_profile",
        published_at=_NOW,
        provider_id=provider_id,
        raw_reference="https://example.test/profile",
        content_hash="hash",
        language="en",
        metadata=metadata,
    )


def test_recognized_provider_with_full_fields_produces_a_rich_candidate() -> None:
    doc = _profile_doc(
        metadata={
            "name": "Apple Inc.",
            "exchange": "NASDAQ",
            "country": "USA",
            "currency": "USD",
            "security_type": "COMMON_STOCK",
        }
    )
    candidates = candidates_from_documents((doc,))
    assert len(candidates) == 1
    candidate = candidates[0]
    assert candidate.provider_name == "ALPHA_VANTAGE"
    assert candidate.symbol == "AAPL"
    assert candidate.company_name == "Apple Inc."
    assert candidate.exchange_mic.value == "XNAS"
    assert candidate.country == "USA"
    assert candidate.currency.value == "USD"
    assert candidate.security_type == "COMMON_STOCK"


def test_unrecognized_provider_id_produces_no_candidate() -> None:
    doc = _profile_doc(provider_id="fake_provider", metadata={"name": "Apple Inc."})
    assert candidates_from_documents((doc,)) == ()


def test_non_profile_document_types_are_never_read_for_identity() -> None:
    doc = RawBusinessDocument(
        identifier="AAPL:FY:2023",
        company="AAPL",
        source_kind="financial_statement",
        published_at=_NOW,
        provider_id="alpha_vantage",
        raw_reference="https://example.test/fs",
        content_hash="hash",
        language="en",
        metadata={"name": "Apple Inc.", "exchange": "NASDAQ", "country": "USA", "currency": "USD"},
    )
    assert candidates_from_documents((doc,)) == ()


def test_unrecognized_exchange_display_name_leaves_exchange_mic_none_not_a_guess() -> None:
    doc = _profile_doc(metadata={"name": "Apple Inc.", "exchange": "SOME_UNKNOWN_VENUE", "country": "USA", "currency": "USD"})
    candidate = candidates_from_documents((doc,))[0]
    assert candidate.exchange_mic is None
    assert candidate.exchange_display_name == "SOME_UNKNOWN_VENUE"


def test_invalid_currency_is_omitted_not_raised() -> None:
    doc = _profile_doc(metadata={"name": "Apple Inc.", "currency": "NOT-A-CURRENCY"})
    candidate = candidates_from_documents((doc,))[0]
    assert candidate.currency is None


def test_invalid_security_type_is_omitted_not_raised() -> None:
    doc = _profile_doc(metadata={"name": "Apple Inc.", "security_type": "NOT_A_REAL_TYPE"})
    candidate = candidates_from_documents((doc,))[0]
    assert candidate.security_type is None


def test_a_profile_document_without_asset_type_still_leaves_security_type_none() -> None:
    """Sprint O's original finding, corrected by Sprint O.1: it is no
    longer true that the real Alpha Vantage provider can *never*
    supply `security_type` (see `test_real_alpha_vantage_identity_
    field_map_now_includes_asset_type`, below, for the corrected,
    now-populated case). What remains true, and is what this test
    actually exercises, is the narrower, still-honest fact: a profile
    document that genuinely carries no `asset_type` (or `security_
    type`) field at all -- e.g. a provider response missing that one
    field for this particular ticker -- still honestly leaves
    `security_type=None` rather than guessing one."""
    doc = _profile_doc(
        metadata={
            "name": "Apple Inc.",
            "exchange": "NASDAQ",
            "sector": "Technology",
            "industry": "Consumer Electronics",
            "country": "USA",
            "description": "Apple Inc. designs...",
            "currency": "USD",
            "fiscal_year_end": "September",
        }
    )
    candidate = candidates_from_documents((doc,))[0]
    assert candidate.security_type is None


def test_asset_type_common_stock_is_translated_to_the_closed_vocabulary() -> None:
    """Sprint O.1 -- the real Alpha Vantage provider now supplies the
    raw `AssetType` display string under `metadata["asset_type"]`; this
    is the deterministic translation table doing its job."""
    doc = _profile_doc(metadata={"name": "Apple Inc.", "exchange": "NASDAQ", "country": "USA", "currency": "USD", "asset_type": "Common Stock"})
    candidate = candidates_from_documents((doc,))[0]
    assert candidate.security_type == "COMMON_STOCK"


def test_asset_type_etf_is_translated_to_the_closed_vocabulary() -> None:
    doc = _profile_doc(metadata={"name": "Some ETF Trust", "asset_type": "ETF"})
    candidate = candidates_from_documents((doc,))[0]
    assert candidate.security_type == "ETF"


def test_asset_type_depositary_receipt_is_translated_to_the_closed_vocabulary() -> None:
    doc = _profile_doc(metadata={"name": "Some Foreign Co", "asset_type": "Depositary Receipt"})
    candidate = candidates_from_documents((doc,))[0]
    assert candidate.security_type == "DEPOSITARY_RECEIPT"


def test_unrecognized_asset_type_deterministically_falls_back_to_other() -> None:
    """`"Preferred Stock"` is a real Alpha Vantage `AssetType` value not
    explicitly named in the translation table -- it becomes `"OTHER"`,
    never `None` (the provider did report *something*) and never a
    fuzzy/invented guess at which named category it belongs to."""
    doc = _profile_doc(metadata={"name": "Some Co", "asset_type": "Preferred Stock"})
    candidate = candidates_from_documents((doc,))[0]
    assert candidate.security_type == "OTHER"


def test_absent_asset_type_still_leaves_security_type_none() -> None:
    doc = _profile_doc(metadata={"name": "Apple Inc.", "exchange": "NASDAQ", "country": "USA", "currency": "USD"})
    candidate = candidates_from_documents((doc,))[0]
    assert candidate.security_type is None


def test_direct_security_type_key_takes_precedence_over_asset_type() -> None:
    """An already-canonical `security_type` (the pre-Sprint-O.1 path,
    still used by every existing fixture that supplies one directly)
    wins over an `asset_type` translation when both happen to be
    present -- exact, non-guessed data always outranks a translated
    display string."""
    doc = _profile_doc(metadata={"name": "Apple Inc.", "security_type": "ETF", "asset_type": "Common Stock"})
    candidate = candidates_from_documents((doc,))[0]
    assert candidate.security_type == "ETF"


def test_real_alpha_vantage_identity_field_map_now_includes_asset_type() -> None:
    """Sprint O.1's own correction of Sprint O's finding, exercised
    directly: a candidate built from exactly the fields the real,
    unmodified `AlphaVantageMarketDataProvider._IDENTITY_FIELD_MAP` can
    populate as of Sprint O.1 (now including `AssetType` ->
    `asset_type`) has a real `security_type`, not `None`."""
    doc = _profile_doc(
        metadata={
            "name": "Apple Inc.",
            "asset_type": "Common Stock",
            "exchange": "NASDAQ",
            "sector": "Technology",
            "industry": "Consumer Electronics",
            "country": "USA",
            "description": "Apple Inc. designs...",
            "currency": "USD",
            "fiscal_year_end": "September",
        }
    )
    candidate = candidates_from_documents((doc,))[0]
    assert candidate.security_type == "COMMON_STOCK"


def test_multiple_profile_documents_produce_multiple_candidates() -> None:
    first = _profile_doc(metadata={"name": "Apple Inc.", "exchange": "NASDAQ", "country": "USA", "currency": "USD"})
    second = RawBusinessDocument(
        identifier="AAPL:profile2",
        company="AAPL",
        source_kind="company_profile",
        published_at=_NOW,
        provider_id="sec_edgar",
        raw_reference="https://example.test/profile2",
        content_hash="hash2",
        language="en",
        metadata={"name": "Apple Inc."},
    )
    candidates = candidates_from_documents((first, second))
    assert len(candidates) == 2
    assert {c.provider_name for c in candidates} == {"ALPHA_VANTAGE", "SEC_EDGAR"}
