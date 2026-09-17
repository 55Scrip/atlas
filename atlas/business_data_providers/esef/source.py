"""Finding a European issuer's filings, and fetching them once.

Two public sources, neither of which needs a key or a contract:

* **GLEIF** turns an ISIN into the LEI of the entity that issued it. That is
  the link Atlas was missing: an ISIN identifies a security, ESEF identifies a
  filer, and nothing in Atlas connected the two. GLEIF is the authority that
  issues LEIs, so this is a lookup rather than an inference.
* **filings.xbrl.org** is XBRL International's index of ESEF filings. Each
  entry carries the report's facts, its taxonomy package, and -- the reason
  Atlas is here rather than at a data vendor -- the date the filing was
  actually added, which is an availability date a vendor's normalized feed
  does not have.

Downloads are cached on disk by filing identity. A taxonomy package is several
megabytes and never changes once published; fetching one twice is waste, and
fetching a hundred is rudeness to a free public service.
"""
from __future__ import annotations

import hashlib
import json
import urllib.parse
import urllib.request
import zipfile
from dataclasses import dataclass
from datetime import date
from pathlib import Path

__all__ = ["EsefFiling", "EsefSourceError", "lei_for_isin", "annual_filings", "index_filings",
           "fetch_facts", "fetch_package", "FILINGS_INDEX", "GLEIF_API"]

FILINGS_INDEX = "https://filings.xbrl.org"
GLEIF_API = "https://api.gleif.org/api/v1"
_TIMEOUT_SECONDS = 120.0
_USER_AGENT = "Atlas/1.0 (European fundamentals evidence; contact via repository)"


class EsefSourceError(Exception):
    """A retrieval failed. Never raised because a filing simply does not
    exist -- an issuer with no ESEF filings is an ordinary empty answer."""


@dataclass(frozen=True)
class EsefFiling:
    """One annual report, as the index describes it."""

    lei: str
    period_end: date
    #: When the filing entered the public index. Atlas's availability boundary:
    #: the evidence could not have been acted on before this date.
    published_at: date
    country: str
    facts_path: str | None
    package_path: str | None
    report_path: str | None
    sha256: str | None
    filing_id: str

    @property
    def source_reference(self) -> str:
        return f"{FILINGS_INDEX}{self.report_path or self.facts_path or ''}"


def _get_json(url: str) -> dict:
    request = urllib.request.Request(
        url, headers={"Accept": "application/vnd.api+json", "User-Agent": _USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=_TIMEOUT_SECONDS) as response:
            return json.load(response)
    except Exception as error:                       # noqa: BLE001
        raise EsefSourceError(f"{url.split('?')[0]} failed: {type(error).__name__}") from error


def lei_for_isin(isin: str) -> str | None:
    """The LEI of the entity that issued this security, or `None`.

    `None` is a real answer -- not every ISIN is mapped -- and the caller must
    treat it as "no filings can be found for this holding", never as a reason
    to search by name.
    """
    query = urllib.parse.urlencode({"filter[isin]": isin, "page[size]": 1})
    payload = _get_json(f"{GLEIF_API}/lei-records?{query}")
    records = payload.get("data") or []
    return records[0]["id"] if records else None


def index_filings(countries: tuple[str, ...] = ("SE", "FR", "DK", "FI", "NO")) -> dict[str, tuple[EsefFiling, ...]]:
    """Every indexed filing in these countries, grouped by LEI.

    The index has no filter for the entity, so finding one issuer means paging
    a whole country. Doing that once for a batch rather than once per issuer is
    the difference between a few hundred requests and a few dozen against a
    free public service that nobody is paid to run.
    """
    by_lei: dict[str, list[EsefFiling]] = {}
    for country in countries:
        page = 1
        while True:
            query = urllib.parse.urlencode(
                {"filter[country]": country, "page[size]": 200, "page[number]": page})
            payload = _get_json(f"{FILINGS_INDEX}/api/filings?{query}")
            rows = payload.get("data") or []
            for row in rows:
                attributes = row.get("attributes", {})
                identifier = attributes.get("fxo_id") or ""
                lei = identifier.split("-")[0]
                if not lei:
                    continue
                try:
                    period_end = date.fromisoformat(attributes["period_end"][:10])
                    published_at = date.fromisoformat(attributes["date_added"][:10])
                except (KeyError, TypeError, ValueError):
                    continue
                by_lei.setdefault(lei, []).append(EsefFiling(
                    lei=lei, period_end=period_end, published_at=published_at,
                    country=attributes.get("country") or country,
                    facts_path=attributes.get("json_url"),
                    package_path=attributes.get("package_url"),
                    report_path=attributes.get("report_url"),
                    sha256=attributes.get("sha256"), filing_id=identifier,
                ))
            if not rows or page * 200 >= payload.get("meta", {}).get("count", 0):
                break
            page += 1
    return {lei: tuple(sorted(f, key=lambda x: x.period_end, reverse=True))
            for lei, f in by_lei.items()}


def annual_filings(lei: str, *, countries: tuple[str, ...] = ("SE", "FR", "DK", "FI", "NO"),
                   index: dict[str, tuple[EsefFiling, ...]] | None = None) -> tuple[EsefFiling, ...]:
    """Every indexed ESEF filing for one LEI, newest period first.

    Pass `index` when handling several issuers; without it this builds one for
    a single lookup, which is correct but pays for a whole scan each time.
    """
    return (index if index is not None else index_filings(countries)).get(lei, ())


def _cached(cache: Path, path: str) -> Path:
    cache.mkdir(parents=True, exist_ok=True)
    return cache / f"{hashlib.sha256(path.encode()).hexdigest()[:24]}{Path(path).suffix}"


def _download(path: str, cache: Path) -> Path:
    """Fetch once, then never again: a published filing does not change."""
    target = _cached(cache, path)
    if target.exists() and target.stat().st_size > 0:
        return target
    request = urllib.request.Request(FILINGS_INDEX + path, headers={"User-Agent": _USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=_TIMEOUT_SECONDS) as response:
            payload = response.read()
    except Exception as error:                       # noqa: BLE001
        raise EsefSourceError(f"download of {path} failed: {type(error).__name__}") from error
    target.write_bytes(payload)
    return target


def _unreadable(target: Path, description: str, error: Exception) -> EsefSourceError:
    """Turn "these bytes are not that document" into a retrieval failure.

    A download can end early -- a dropped connection, a full disk, an
    interrupted run -- and what lands on disk is then a file of the right
    name that is not the document. The caller cannot do anything more
    useful about that than about a refused connection, so it is the same
    kind of failure and is raised as one, which keeps one issuer's bad
    filing from ending a batch.

    The truncated file is discarded on the way out. Left in place it would
    satisfy the cache on every future run, and a transient network fault
    would become a permanent one for that filing.
    """
    target.unlink(missing_ok=True)
    return EsefSourceError(f"{description} is unreadable ({type(error).__name__})")


def fetch_facts(filing: EsefFiling, cache: Path) -> dict:
    """The report's facts, as xbrl-json."""
    if not filing.facts_path:
        raise EsefSourceError(f"{filing.filing_id} has no facts document in the index")
    target = _download(filing.facts_path, cache)
    try:
        return json.loads(target.read_text())
    except (ValueError, UnicodeDecodeError) as error:
        raise _unreadable(target, f"the facts of {filing.filing_id}", error) from error


def fetch_package(filing: EsefFiling, cache: Path) -> Path:
    """The taxonomy package, which is where concept meaning lives.

    Opened here to prove it can be, rather than left for the caller to
    discover: a package that will not open is a failed retrieval, and this
    is where retrieval failures are named.
    """
    if not filing.package_path:
        raise EsefSourceError(f"{filing.filing_id} has no taxonomy package in the index")
    target = _download(filing.package_path, cache)
    try:
        with zipfile.ZipFile(target):
            pass
    except (zipfile.BadZipFile, OSError) as error:
        raise _unreadable(target, f"the taxonomy package of {filing.filing_id}", error) from error
    return target
