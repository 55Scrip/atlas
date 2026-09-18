"""Acquiring and keeping SEC primary documents, at SEC's pace.

Three jobs, deliberately separate from parsing: fetch politely, store
reproducibly, and refuse a cached file that cannot be what it claims.

**Pacing is here because it is nowhere else.** `http.fetch_text` is a
bare request with no delay, and SEC's fair-access policy is a published
rate, not a suggestion -- a caller that ignores it gets the whole
installation blocked, not one failed request. `SecFilingCache` holds
the clock, so every filing fetched through it is paced whether or not
the caller remembered to.

**Nothing here is allowed on a request path.** Fetching a 10-K is
seconds of network and megabytes of body; the Investment Case
composition was engineered to cost a fixed number of reads regardless
of how many Cases exist, and a per-Case fetch would undo that. This is
a background, batch operation.

**Configure a real contact before any larger run.** The identity sent
is whatever `sec_edgar_identity.sec_user_agent()` returns, and this
module deliberately does not invent one. With `ATLAS_SEC_EDGAR_USER_AGENT`
unset that is the placeholder `admin@atlas-investment-os.local`, which
SEC accepts -- twelve requests were served under it during this
sprint's bounded verification -- but which is not a reachable address.
SEC's fair-access policy exists so they can contact an operator before
blocking them, and a contact nobody reads removes the warning and
leaves the block. Set the variable to a real address before acquiring
more than a handful of filings.

**A cached file is validated before it is believed.** A truncated
download is the failure that matters, because a half-written instance
still parses into a smaller, wrong set of facts rather than raising.
"""
from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

__all__ = [
    "SEC_ARCHIVE_PREFIX",
    "MIN_REQUEST_INTERVAL_SECONDS",
    "CorruptCachedFiling",
    "SecFilingCache",
    "validate_instance",
    "validate_primary_document",
]

SEC_ARCHIVE_PREFIX = "https://www.sec.gov/Archives/edgar/data/"

#: SEC publishes a 10 requests/second ceiling. This is a third of it:
#: the corpus is a few hundred filings fetched in the background, so
#: there is nothing to gain by crowding the limit and an installation-
#: wide block to lose.
MIN_REQUEST_INTERVAL_SECONDS = 0.35

#: Smaller than any real 10-K primary document or extracted instance.
#: The four benchmark filings run 2.2-5.6 MB; a truncation that leaves
#: less than this is not a filing at all.
_MIN_PLAUSIBLE_BYTES = 10_000


class CorruptCachedFiling(Exception):
    """A cached file is not what it claims. Raised per filing, never for
    the batch: one bad download must cost that filing and no other."""


def validate_primary_document(body: bytes) -> None:
    if len(body) < _MIN_PLAUSIBLE_BYTES:
        raise CorruptCachedFiling(f"primary document is {len(body)} bytes; truncated or empty")
    head = body[:4096].lower()
    if b"<html" not in head and b"<?xml" not in head:
        raise CorruptCachedFiling("primary document is neither HTML nor XML")
    lowered = body.lower()
    if b"ix:nonfraction" not in lowered and b"ix:nonnumeric" not in lowered:
        raise CorruptCachedFiling("primary document carries no inline XBRL tags")


def validate_instance(body: bytes) -> None:
    if len(body) < _MIN_PLAUSIBLE_BYTES:
        raise CorruptCachedFiling(f"instance is {len(body)} bytes; truncated or empty")
    if b"<xbrl" not in body[:8192] and b":xbrl" not in body[:8192]:
        raise CorruptCachedFiling("instance has no xbrl root")
    tail = body.rstrip()[-256:].lower()
    # The check that matters: a half-written instance still parses, into
    # a smaller and wrong set of facts, so the close tag is the evidence
    # that the download finished.
    if b"</xbrl>" not in tail and b":xbrl>" not in tail:
        raise CorruptCachedFiling("instance does not close its xbrl root; truncated")


@dataclass
class SecFilingCache:
    """Content-addressed storage for filing bodies.

    The path is the digest of the URL, so the same URL always resolves
    to the same file and a second run fetches nothing. Bodies stay on
    disk rather than in the database: four filings are 26.6 MB, and the
    operational database has no reason to carry bytes nothing queries.
    """

    root: Path
    fetch_text: Callable[[str, "dict[str, str] | None"], str]
    headers: dict[str, str]
    min_interval: float = MIN_REQUEST_INTERVAL_SECONDS
    sleep: Callable[[float], None] = time.sleep
    clock: Callable[[], float] = time.monotonic
    _last_request: float = -1e9

    def path_for(self, url: str) -> Path:
        return self.root / f"{hashlib.sha256(url.encode()).hexdigest()}.body"

    def read(self, url: str) -> bytes | None:
        path = self.path_for(url)
        return path.read_bytes() if path.exists() else None

    def fetch(self, url: str, *, validate: Callable[[bytes], None] | None = None) -> bytes:
        """The cached body, fetching it once if absent.

        A cached body that fails validation is discarded and refetched,
        rather than trusted or merely rejected -- a truncated file that
        stays on disk makes every later run fail the same way.
        """
        if not url.startswith(SEC_ARCHIVE_PREFIX):
            raise ValueError(f"not an SEC EDGAR archive URL: {url}")
        cached = self.read(url)
        if cached is not None:
            if validate is None:
                return cached
            try:
                validate(cached)
                return cached
            except CorruptCachedFiling:
                self.path_for(url).unlink(missing_ok=True)
        body = self._fetch_paced(url)
        if validate is not None:
            validate(body)
        self.root.mkdir(parents=True, exist_ok=True)
        self.path_for(url).write_bytes(body)
        return body

    def _fetch_paced(self, url: str) -> bytes:
        waited = self.min_interval - (self.clock() - self._last_request)
        if waited > 0:
            self.sleep(waited)
        self._last_request = self.clock()
        return self.fetch_text(url, self.headers).encode("utf-8")
