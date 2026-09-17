"""One bad filing is one bad filing.

A batch ingests eight issuers from a public index, and the script that runs
it says so in as many words: "One issuer's failure is that issuer's failure.
Everything already ingested stays, and every other issuer still runs." It
keeps that promise by catching `EsefSourceError`.

A rehearsal against a deliberately corrupted cache showed the promise was
only half kept. A refused download was an `EsefSourceError` and was isolated;
a download that *arrived truncated* was a `BadZipFile` from inside the zip
module, which escaped the batch and ended it. Four issuers that had not had
their turn yet never got one -- not because their filings were bad, but
because an earlier issuer's bytes were.

The distinction the code was drawing -- "could not fetch" against "fetched
something unusable" -- is not one the caller can act on differently. Both
mean Atlas does not have this filing. So both are the same failure now.

The second half of this is the cache. A truncated file is the right size and
the right name, so it satisfies the cache on every later run: a transient
network fault, cached, becomes a permanent one for that filing. It is
discarded on the way out instead.
"""
from __future__ import annotations

import json
import zipfile
from datetime import date
from pathlib import Path

import pytest

from atlas.business_data_providers.esef.source import (
    EsefFiling,
    EsefSourceError,
    fetch_facts,
    fetch_package,
)


def _filing(**overrides) -> EsefFiling:
    base = dict(
        lei="549300YECS8HKCIMMB67",
        period_end=date(2024, 12, 31),
        published_at=date(2025, 5, 8),
        country="SE",
        facts_path="/a/report.json",
        package_path="/a/report.zip",
        report_path="/a/report.xhtml",
        sha256=None,
        filing_id="an-issuer-2024",
    )
    base.update(overrides)
    return EsefFiling(**base)


def _seed(cache: Path, path: str, payload: bytes) -> Path:
    """Put bytes where `_download` will find them, so nothing is fetched."""
    from atlas.business_data_providers.esef.source import _cached

    cache.mkdir(parents=True, exist_ok=True)
    target = _cached(cache, path)
    target.write_bytes(payload)
    return target


# --- A truncated download is a retrieval failure -----------------------


def test_a_package_that_will_not_open_is_a_source_error(tmp_path: Path) -> None:
    """The failure that ended a live batch: not a refused connection, but
    bytes that are not the zip they claim to be."""
    filing = _filing()
    _seed(tmp_path, filing.package_path, b"not a zip file at all")

    with pytest.raises(EsefSourceError) as raised:
        fetch_package(filing, tmp_path)
    assert filing.filing_id in str(raised.value)


def test_facts_that_are_not_json_are_a_source_error(tmp_path: Path) -> None:
    """The same hole on the other document. It had not been hit yet only
    because the packages are the large downloads."""
    filing = _filing()
    _seed(tmp_path, filing.facts_path, b'{"facts": {"ifrs-full:Revenue')

    with pytest.raises(EsefSourceError):
        fetch_facts(filing, tmp_path)


def test_a_missing_document_is_still_a_source_error(tmp_path: Path) -> None:
    """The pre-existing behaviour, unchanged: the index itself saying the
    filing has no such document."""
    with pytest.raises(EsefSourceError):
        fetch_package(_filing(package_path=None), tmp_path)
    with pytest.raises(EsefSourceError):
        fetch_facts(_filing(facts_path=None), tmp_path)


# --- The failure is not cached ----------------------------------------


def test_an_unreadable_package_is_not_kept(tmp_path: Path) -> None:
    """Otherwise one interrupted download poisons that filing forever: the
    file is present and non-empty, so the cache is satisfied and the real
    package is never fetched again."""
    filing = _filing()
    target = _seed(tmp_path, filing.package_path, b"not a zip file at all")

    with pytest.raises(EsefSourceError):
        fetch_package(filing, tmp_path)
    assert not target.exists()


def test_unreadable_facts_are_not_kept(tmp_path: Path) -> None:
    filing = _filing()
    target = _seed(tmp_path, filing.facts_path, b"{ truncated")

    with pytest.raises(EsefSourceError):
        fetch_facts(filing, tmp_path)
    assert not target.exists()


# --- A good document is untouched -------------------------------------


def test_a_readable_package_is_returned_and_kept(tmp_path: Path) -> None:
    """The check proves the package opens; it must not cost the caller the
    package, nor re-download what is already there."""
    filing = _filing()
    target = _cached_zip(tmp_path, filing)

    assert fetch_package(filing, tmp_path) == target
    assert target.exists()


def test_readable_facts_are_returned_and_kept(tmp_path: Path) -> None:
    filing = _filing()
    target = _seed(tmp_path, filing.facts_path, json.dumps({"facts": {}}).encode())

    assert fetch_facts(filing, tmp_path) == {"facts": {}}
    assert target.exists()


def _cached_zip(cache: Path, filing: EsefFiling) -> Path:
    from atlas.business_data_providers.esef.source import _cached

    cache.mkdir(parents=True, exist_ok=True)
    target = _cached(cache, filing.package_path)
    with zipfile.ZipFile(target, "w") as archive:
        archive.writestr("a/report_cal.xml", "<linkbase/>")
    return target
