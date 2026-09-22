"""Fetching politely, storing reproducibly, refusing a corrupt file."""
import tempfile

import pytest

from atlas.business_data_providers.sec_filing.cache import (
    MIN_REQUEST_INTERVAL_SECONDS,
    SEC_ARCHIVE_PREFIX,
    CorruptCachedFiling,
    SecFilingCache,
    validate_instance,
    validate_label_linkbase,
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


# ------------------------------------------------- label linkbase
GOOD_LABELS = (b'<?xml version="1.0"?><link:linkbase xmlns:link="http://www.xbrl.org/2003/linkbase">'
               + b"<link:labelLink>" + b"<!-- " + b"x" * 4000 + b" -->"
               + b'<link:loc xlink:href="a.xsd#a_Member" xlink:label="a"/>'
               + b'<link:label xlink:label="l">Name</link:label>'
               + b'<link:labelArc xlink:from="a" xlink:to="l"/>'
               + b"</link:labelLink></link:linkbase>")
BARE_LABELS = GOOD_LABELS.replace(b"link:", b"")


def test_a_good_label_linkbase_passes_in_either_serialisation():
    validate_label_linkbase(GOOD_LABELS)
    validate_label_linkbase(BARE_LABELS)


def test_a_truncated_label_linkbase_is_rejected():
    # The failure that matters: a half-written linkbase still parses,
    # into fewer arcs, and the labels it drops are silently the ones a
    # later identity claim would have rested on. Cut just the closing
    # tag, so the arcs survive and only the completeness check can
    # catch it.
    with pytest.raises(CorruptCachedFiling, match="does not close"):
        validate_label_linkbase(GOOD_LABELS[: -len(b"</link:labelLink></link:linkbase>")])


def test_a_linkbase_truncated_before_its_arcs_is_also_rejected():
    with pytest.raises(CorruptCachedFiling):
        validate_label_linkbase(GOOD_LABELS[: len(GOOD_LABELS) // 2])


def test_an_empty_label_linkbase_is_rejected():
    with pytest.raises(CorruptCachedFiling):
        validate_label_linkbase(b"")


def test_a_well_formed_but_implausibly_small_linkbase_is_rejected():
    # Structurally complete and far too small to be a real filing's
    # labels -- only the size check catches this one.
    tiny = b'<?xml version="1.0"?><linkbase><labelArc/></linkbase>'
    with pytest.raises(CorruptCachedFiling, match="bytes"):
        validate_label_linkbase(tiny)


def test_a_body_that_is_not_xml_is_rejected_however_large():
    # Large, mentions labelarc, ends in linkbase> -- and is not XML.
    # Only the XML check stands between this and the parser.
    junk = b"server error: retry later " * 400 + b" labelarc ... linkbase>"
    with pytest.raises(CorruptCachedFiling, match="not XML"):
        validate_label_linkbase(junk)


def test_a_linkbase_with_no_arcs_is_not_a_label_linkbase():
    with pytest.raises(CorruptCachedFiling, match="label arcs"):
        validate_label_linkbase(GOOD_LABELS.replace(b"labelArc", b"presentationArc"))


def test_a_corrupt_cached_label_linkbase_is_discarded_and_refetched(tmp_path):
    fetcher = Recorder(GOOD_LABELS)
    c, _, _ = cache(tmp_path, fetcher)
    url = ARCHIVE + "vistra-20251231_lab.xml"
    c.fetch(url, validate=validate_label_linkbase)
    c.path_for(url).write_bytes(GOOD_LABELS[:300])
    assert c.fetch(url, validate=validate_label_linkbase) == GOOD_LABELS
    assert len(fetcher.calls) == 2
    assert c.read(url) == GOOD_LABELS


# ------------------------------------------------------------------ durable default root
class TestTheDefaultCacheLocationSurvivesATempSweep:
    """Sprint 26: a macOS `/private/tmp` sweep deleted four of sixteen cached
    filings overnight, and the frozen corpus built on them silently shrank
    from 162 records to 109. The default location must not be temporary."""

    def test_the_default_sits_beside_the_database_not_in_a_temp_directory(self, monkeypatch):
        from atlas.business_data_providers.sec_filing.cache import default_cache_root
        from atlas.config import DATABASE_DIR

        monkeypatch.delenv("ATLAS_SEC_FILING_CACHE", raising=False)
        root = default_cache_root()
        assert root.parent == DATABASE_DIR
        assert not str(root).startswith("/tmp")
        assert not str(root).startswith("/private/tmp")
        assert not str(root).startswith(tempfile.gettempdir())

    def test_an_explicit_root_overrides_it_so_tests_can_use_a_tmp_directory(self, monkeypatch, tmp_path):
        from atlas.business_data_providers.sec_filing.cache import default_cache_root

        monkeypatch.setenv("ATLAS_SEC_FILING_CACHE", str(tmp_path / "elsewhere"))
        assert default_cache_root() == (tmp_path / "elsewhere").resolve()

    def test_the_cache_still_reads_a_body_written_under_the_default_root(self, monkeypatch, tmp_path):
        from atlas.business_data_providers.sec_filing.cache import SecFilingCache, default_cache_root

        monkeypatch.setenv("ATLAS_SEC_FILING_CACHE", str(tmp_path / "durable"))
        root = default_cache_root()
        root.mkdir(parents=True)

        def never(url, headers):
            raise AssertionError("a cached body must not be refetched")

        store = SecFilingCache(root=root, fetch_text=never, headers={})
        url = SEC_ARCHIVE_PREFIX + "1/000/x.htm"
        store.path_for(url).write_bytes(GOOD_PRIMARY)
        assert store.fetch(url) == GOOD_PRIMARY
