"""Reading an XBRL instance document: contexts, units and facts.

Extracted verbatim from `sec_edgar_share_classes.py`, where this
plumbing was written for the share-class work and has been live ever
since. Nothing here was redesigned; the share-class module imports the
same names back, so its behaviour is byte-identical.

It moved because a firewall test said so. That test enumerates exactly
who may import the share-class adapter, and it was right to fail when
the SEC Inline XBRL reader reached in for `read_instance`: reading an
XBRL instance is not part of that adapter's identity, and a second
provider needing it is a reason to share the plumbing rather than a
reason to widen the adapter's door. Writing a second parser over the
same format was the other option, and it would have been two sets of
bugs over one grammar.

What this deliberately does NOT do: interpret. It resolves namespace
prefixes to QNames, reads a context's period and its explicit
dimensions, resolves unit references, and skips nil facts. Every
judgment about what an axis means, which figure to prefer, or what a
value is worth belongs to the provider module that calls it.

Two known limits, both documented where they bite and both worked
around by the SEC reader rather than changed here, because production
code depends on the current behaviour: a context's *typed* dimensions
are counted and their values discarded, and a unit built from a
`<divide>` resolves to `None`.
"""
from __future__ import annotations

import io
from dataclasses import dataclass
from datetime import date
from xml.etree import ElementTree

from atlas.business_data_providers.errors import MalformedProviderResponse

__all__ = ["XBRLI", "XBRLDI", "Context", "parse_day", "read_instance"]

#: Taxonomy namespace families. The us-gaap and dei namespaces carry
#: their taxonomy year, which changes every filing season, so a prefix
#: match is the only stable way to recognise them.
_US_GAAP_PREFIX = "http://fasb.org/us-gaap/"
_DEI_PREFIX = "http://xbrl.sec.gov/dei/"

XBRLI = "http://www.xbrl.org/2003/instance"
XBRLDI = "http://xbrl.org/2006/xbrldi"



def _family(uri: str) -> str | None:
    if uri.startswith(_US_GAAP_PREFIX):
        return "us-gaap"
    if uri.startswith(_DEI_PREFIX):
        return "dei"
    return None

@dataclass(frozen=True)
class Context:
    id: str
    instant: date | None
    start: date | None
    end: date | None
    explicit: tuple[tuple[str, str], ...]  # (dimension, member), normalised
    typed: int


def parse_day(text: str | None) -> date | None:
    try:
        return date.fromisoformat(text.strip()[:10]) if text else None
    except ValueError:
        return None


class _Names:
    """QName normalisation. Standard taxonomies are named by family
    (`us-gaap:`, `dei:`) because their namespace URI carries a year; a
    company extension keeps the prefix the filing itself declares."""

    def __init__(self, prefixes: dict[str, str]) -> None:
        self._prefixes = prefixes
        self._uri_to_prefix = {uri: prefix for prefix, uri in prefixes.items()}

    def of_tag(self, tag: str) -> str:
        if not tag.startswith("{"):
            return tag
        uri, local = tag[1:].split("}", 1)
        family = _family(uri)
        return f"{family or self._uri_to_prefix.get(uri, uri)}:{local}"

    def of_qname(self, text: str) -> str:
        text = (text or "").strip()
        if ":" not in text:
            return text
        prefix, local = text.split(":", 1)
        uri = self._prefixes.get(prefix)
        family = _family(uri) if uri else None
        return f"{family or prefix}:{local}"


def _prefixes(instance_xml: str) -> dict[str, str]:
    prefixes: dict[str, str] = {}
    for _, (prefix, uri) in ElementTree.iterparse(io.StringIO(instance_xml), events=("start-ns",)):
        prefixes.setdefault(prefix, uri)
    return prefixes


def _contexts(root, names: _Names) -> dict[str, Context]:
    out: dict[str, Context] = {}
    for element in root.iter(f"{{{XBRLI}}}context"):
        period = element.find(f"{{{XBRLI}}}period")
        explicit, typed = [], 0
        for holder in (f"{{{XBRLI}}}entity/{{{XBRLI}}}segment", f"{{{XBRLI}}}scenario"):
            container = element.find(holder)
            if container is None:
                continue
            for member in container:
                if member.tag == f"{{{XBRLDI}}}explicitMember":
                    explicit.append((names.of_qname(member.get("dimension", "")), names.of_qname(member.text or "")))
                else:
                    typed += 1
        out[element.get("id", "")] = Context(
            id=element.get("id", ""),
            instant=parse_day(period.findtext(f"{{{XBRLI}}}instant")) if period is not None else None,
            start=parse_day(period.findtext(f"{{{XBRLI}}}startDate")) if period is not None else None,
            end=parse_day(period.findtext(f"{{{XBRLI}}}endDate")) if period is not None else None,
            explicit=tuple(sorted(explicit)),
            typed=typed,
        )
    return out


def _units(root) -> dict[str, str | None]:
    """Unit id -> its single measure's local name (`xbrli:shares` ->
    `shares`); a divide or multi-measure unit -> `None`."""
    out: dict[str, str | None] = {}
    for element in root.iter(f"{{{XBRLI}}}unit"):
        measures = [m.text for m in element.findall(f"{{{XBRLI}}}measure")]
        out[element.get("id", "")] = measures[0].strip().split(":")[-1] if len(measures) == 1 and measures[0] else None
    return out


def _is_nil(element) -> bool:
    return element.get("{http://www.w3.org/2001/XMLSchema-instance}nil") in ("true", "1")


def read_instance(instance_xml: str) -> tuple[tuple[Context, ...], list[tuple[str, Context, str | None, str, str | None]]]:
    """(every context, every non-nil fact as (concept, context, unit, text, decimals))."""
    try:
        root = ElementTree.fromstring(instance_xml)
        names = _Names(_prefixes(instance_xml))
    except ElementTree.ParseError as exc:
        raise MalformedProviderResponse(f"XBRL instance did not parse: {exc}") from exc
    contexts = _contexts(root, names)
    units = _units(root)
    facts: list[tuple[str, Context, str | None, str, str | None]] = []
    for element in root:
        ref = element.get("contextRef")
        if ref is None or _is_nil(element) or ref not in contexts:
            continue
        facts.append((names.of_tag(element.tag), contexts[ref], units.get(element.get("unitRef", "")),
                      (element.text or "").strip(), element.get("decimals")))
    return tuple(contexts.values()), facts
