"""The write-side bridge: a parsed filing becomes persisted observations, and
an instance that is not the filing it was fetched as is refused."""
from __future__ import annotations

from datetime import date, datetime, timezone
from pathlib import Path

import pytest

from atlas.alpha.business_data_refresh.security_share_evidence import (
    PARSER_VERSION,
    FilingRefused,
    ShareClassFilingSource,
    evidence_from_instance,
)
from atlas.alpha.security_share_evidence.models import ShareClassLinkKind
from atlas.business_data_providers.sec_edgar_share_classes import FetchedInstance, LinkKind

FIXTURES = Path(__file__).resolve().parents[2] / "business_data_providers" / "fixtures" / "share_classes"
NOW = datetime(2026, 9, 14, tzinfo=timezone.utc)
ALPHABET = ShareClassFilingSource("0001652044", "0001652044-26-000018", "10-K", date(2026, 2, 5))


def _fetched(source: ShareClassFilingSource, text: str | None = None) -> FetchedInstance:
    xml = text if text is not None else (FIXTURES / f"{source.accession}.xml").read_text()
    return FetchedInstance(source.issuer_cik, source.accession, "x_htm.xml", "https://www.sec.gov/x_htm.xml", xml, 2)


def test_link_kinds_are_one_vocabulary():
    assert [k.value for k in LinkKind] == [k.value for k in ShareClassLinkKind]


def test_a_filing_becomes_its_observations():
    filing, observations = evidence_from_instance(ALPHABET, _fetched(ALPHABET), recorded_at=NOW)
    assert (filing.observations, filing.proven, filing.ambiguous, filing.no_link, filing.conflicts) == (6, 4, 0, 2, 0)
    assert (filing.fiscal_period, filing.document_period_end, filing.parser_version) == (
        "FY2025", date(2025, 12, 31), PARSER_VERSION)
    proven = {(o.cover_symbol, o.cover_mic, o.period_end.isoformat(), o.shares) for o in observations
              if o.link_kind is ShareClassLinkKind.PROVEN_BY_SHARED_DIMENSION}
    assert ("GOOG", "XNAS", "2025-12-31", 5_429_000_000.0) in proven
    assert ("GOOGL", "XNAS", "2025-12-31", 5_822_000_000.0) in proven
    assert all(o.issuer_cik == ALPHABET.issuer_cik and o.filing_date == ALPHABET.filing_date for o in observations)
    unlinked = [o for o in observations if o.link_kind is ShareClassLinkKind.NO_LINK]
    assert all(o.cover_symbol is None and o.cover_mic is None for o in unlinked)


@pytest.mark.parametrize("source, text_change", [
    (ShareClassFilingSource("0001141391", ALPHABET.accession, "10-K", ALPHABET.filing_date), None),  # another filer
    (ShareClassFilingSource(ALPHABET.issuer_cik, ALPHABET.accession, "40-F", ALPHABET.filing_date), None),  # another form
    (ALPHABET, (">false</dei:AmendmentFlag>", ">true</dei:AmendmentFlag>")),  # an amendment
])
def test_an_instance_that_is_not_the_filing_is_refused(source, text_change):
    text = (FIXTURES / f"{ALPHABET.accession}.xml").read_text()
    if text_change:
        assert text_change[0] in text
        text = text.replace(*text_change, 1)
    with pytest.raises(FilingRefused):
        evidence_from_instance(source, _fetched(ALPHABET, text), recorded_at=NOW)
