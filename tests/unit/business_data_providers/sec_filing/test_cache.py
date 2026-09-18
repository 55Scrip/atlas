"""Fetching politely, storing reproducibly, refusing a corrupt file."""
import pytest

from atlas.business_data_providers.sec_filing.cache import (
    MIN_REQUEST_INTERVAL_SECONDS,
    CorruptCachedFiling,
    SecFilingCache,
    validate_instance,
    validate_primary_document,
)

ARCHIVE = "https://www.sec.gov/Archives/edgar/data/1652044/000165204426000018/"
URL = ARCHIVE + "goog-20251231.htm"
INSTANCE_URL = ARCHIVE + "goog-20251231_htm.xml"

GOOD_PRIMARY = (b"<?xml version='1.0'?><html>" + b"x" * 20_000 +
                b"<ix:nonFraction contextRef='c-1'>1</ix:nonFraction></html>")
GOOD_INSTANCE = b"<xbrl xmlns='http://www.xbrl.org/2003/instance'>" + b"y" * 20_000 + b"</xbrl>"


class Recorder:
    def __init__(self, body, *, fail_first=False):
        self.body = body
        self.calls = []
        self.fail_first = fail_first

    def __call__(self, url, headers):
        self.calls.append((url, headers))
        return self.body.decode()


def cache(tmp_path, fetcher, **kwargs):
    slept = []
    now = [0.0]
    return SecFilingCache(
        root=tmp_path / "cache", fetch_text=fetcher,
        headers={"User-Agent": "Atlas test contact@example.com"},
        sleep=lambda s: (slept.append(s), now.__setitem__(0, now[0] + s)),
        clock=lambda: now[0], **kwargs), slept, now


# ------------------------------------------------------------------ 1,2
def test_a_filing_is_fetched_from_its_own_archive_url(tmp_path):
    fetcher = Recorder(GOOD_PRIMARY)
    c, _, _ = cache(tmp_path, fetcher)
    assert c.fetch(URL, validate=validate_primary_document) == GOOD_PRIMARY
    assert fetcher.calls[0][0] == URL


def test_the_sec_identity_header_is_sent(tmp_path):
    fetcher = Recorder(GOOD_PRIMARY)
    c, _, _ = cache(tmp_path, fetcher)
    c.fetch(URL)
    (_, headers), = fetcher.calls
    assert "User-Agent" in headers and "@" in headers["User-Agent"]


def test_a_url_outside_the_sec_archive_is_refused(tmp_path):
    c, _, _ = cache(tmp_path, Recorder(GOOD_PRIMARY))
    with pytest.raises(ValueError, match="SEC EDGAR archive"):
        c.fetch("https://example.com/not-sec.htm")


# -------------------------------------------------------------- pacing
def test_consecutive_requests_are_paced_below_the_fair_access_limit(tmp_path):
    fetcher = Recorder(GOOD_PRIMARY)
    c, slept, _ = cache(tmp_path, fetcher)
    c.fetch(URL)
    c.fetch(ARCHIVE + "other.htm")
    assert slept and slept[0] >= MIN_REQUEST_INTERVAL_SECONDS - 1e-9
    assert MIN_REQUEST_INTERVAL_SECONDS >= 0.1   # SEC publishes 10 req/s


# ------------------------------------------------------------- caching
def test_a_second_read_of_one_url_fetches_nothing(tmp_path):
    fetcher = Recorder(GOOD_PRIMARY)
    c, _, _ = cache(tmp_path, fetcher)
    c.fetch(URL)
    c.fetch(URL)
    assert len(fetcher.calls) == 1


def test_the_cache_path_is_the_same_for_the_same_url(tmp_path):
    c, _, _ = cache(tmp_path, Recorder(GOOD_PRIMARY))
    assert c.path_for(URL) == c.path_for(URL)
    assert c.path_for(URL) != c.path_for(INSTANCE_URL)


# ---------------------------------------------------------- validation
def test_a_truncated_instance_is_rejected():
    with pytest.raises(CorruptCachedFiling, match="truncated"):
        validate_instance(GOOD_INSTANCE[: len(GOOD_INSTANCE) // 2])


def test_an_empty_body_is_rejected():
    with pytest.raises(CorruptCachedFiling):
        validate_instance(b"")
    with pytest.raises(CorruptCachedFiling):
        validate_primary_document(b"")


def test_a_primary_document_with_no_inline_xbrl_is_rejected():
    with pytest.raises(CorruptCachedFiling, match="inline XBRL"):
        validate_primary_document(b"<html>" + b"x" * 20_000 + b"</html>")


def test_a_good_filing_passes_validation():
    validate_primary_document(GOOD_PRIMARY)
    validate_instance(GOOD_INSTANCE)


# ------------------------------------------------------------ recovery
def test_a_corrupt_cached_file_is_discarded_and_refetched(tmp_path):
    fetcher = Recorder(GOOD_INSTANCE)
    c, _, _ = cache(tmp_path, fetcher)
    c.fetch(INSTANCE_URL, validate=validate_instance)
    # something truncates it on disk
    c.path_for(INSTANCE_URL).write_bytes(GOOD_INSTANCE[:400])
    assert c.fetch(INSTANCE_URL, validate=validate_instance) == GOOD_INSTANCE
    assert len(fetcher.calls) == 2
    # and the good body replaced it, so a later run does not fetch again
    assert c.read(INSTANCE_URL) == GOOD_INSTANCE


def test_a_corrupt_body_that_refetches_corrupt_raises_for_that_filing(tmp_path):
    c, _, _ = cache(tmp_path, Recorder(b"<xbrl>truncated"))
    with pytest.raises(CorruptCachedFiling):
        c.fetch(INSTANCE_URL, validate=validate_instance)
