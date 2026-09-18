"""The names a filer gives its own taxonomy elements.

An XBRL element is a QName. A label linkbase is where the filer says
what that QName is called in prose, and it is the only place in a
filing that does. Entity Identity Resolution earned exactly one basis
-- `TAXONOMY_LABEL` -- on that evidence, and this module is how it is
read.

**Structure, not filename or spelling.** A label reaches an element
through three nodes: a `loc` pointing at the element, a `label`
carrying the text, and a `labelArc` joining them. All three are read by
*local name*, because real linkbases in this corpus serialise them both
bare and `link:`-prefixed, and a parser that insisted on one spelling
would silently return nothing for half of them -- the worst failure
available here, since an empty label set looks exactly like "the filer
declared no labels".

The same applies to finding the file at all: SEC writes
`vistra-20251231_lab.xml`, ESEF packages write
`abvolvo-2022-12-31_lab-sv.xml`. `endswith("_lab.xml")` finds the first
and misses the second.

**Nothing is collapsed.** One element commonly carries several labels:
a standard label, a terse one, documentation, period-start and
period-end variants, each under its own role, and potentially in
several languages. They are returned as separate records. Choosing one
would be a judgment this layer has no basis for, and the role is often
the whole point -- a documentation label is a sentence about the
element, not a name for it.

**The filer's spelling is preserved exactly**, including the typo in
Volvo's `FinancialServciesMember`. That typo is what makes it a
different element from `FinancialServicesMember`, and normalising it
away would erase the distinction the identity layer exists to keep.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

__all__ = [
    "TAXONOMY_LABEL_READER_VERSION",
    "TaxonomyLabel",
    "is_label_linkbase",
    "read_label_linkbase",
]

TAXONOMY_LABEL_READER_VERSION = "taxonomy-labels-1"

#: Matches `..._lab.xml` and `..._lab-sv.xml` alike. The language
#: suffix is a real ESEF convention, not a curiosity.
_LABEL_FILENAME = re.compile(r"_lab(?:-[\w-]+)?\.xml$", re.I)

#: Elements by LOCAL name, so `<loc>` and `<link:loc>` both match.
_LOC = re.compile(
    r"<(?:[\w.-]+:)?loc\b([^>]*)/?>", re.I)
_LABEL = re.compile(
    r"<(?:[\w.-]+:)?label\b([^>]*)>(.*?)</(?:[\w.-]+:)?label>", re.I | re.S)
_ARC = re.compile(
    r"<(?:[\w.-]+:)?labelArc\b([^>]*)/?>", re.I)


def _attr(attributes: str, name: str) -> str | None:
    """An attribute by local name: `xlink:href` and `href` both work,
    and so does `xml:lang` against a document that omits the prefix."""
    found = re.search(rf'(?:[\w.-]+:)?{name}\s*=\s*"([^"]*)"', attributes, re.I)
    return found.group(1) if found else None


@dataclass(frozen=True)
class TaxonomyLabel:
    """One label a filer declared for one element."""

    element_href: str
    """The locator's href exactly as written: `abvolvo-2022-12-31.xsd#abvolvo_X`."""
    element_id: str
    """The fragment -- the element's id within its schema."""
    element_qname: str | None
    """`prefix:LocalName` when the id encodes it, else `None`. Derived
    from the id's own separator, never guessed from the issuer."""
    text: str
    """The label, as the filer spelled it."""
    role: str
    """The full label role URI. Never reduced to "the label"."""
    language: str | None
    source_document: str
    """Which linkbase file this came from."""
    source_locator: str = ""
    """Which filing or package. Supplied by the caller that read it."""

    @property
    def namespace_prefix(self) -> str | None:
        return self.element_qname.split(":")[0] if self.element_qname else None

    @property
    def is_member(self) -> bool:
        return self.element_id.endswith("Member")


_STANDARD_ROLE = "http://www.xbrl.org/2003/role/label"


def is_label_linkbase(filename: str) -> bool:
    """Whether a filename names a label linkbase, in either convention."""
    return bool(_LABEL_FILENAME.search(filename))


def _qname_from_id(element_id: str) -> str | None:
    """`abvolvo_FinancialServicesMember` -> `abvolvo:FinancialServicesMember`.

    Split on the first underscore only, because a local name may itself
    contain underscores. Returns `None` when the id carries no prefix,
    rather than inventing one from the file or the issuer."""
    prefix, separator, local = element_id.partition("_")
    if not separator or not local:
        return None
    return f"{prefix}:{local}"


def read_label_linkbase(body: str, *, source_document: str,
                        source_locator: str = "") -> tuple[TaxonomyLabel, ...]:
    """Every label the linkbase declares, joined through its own arcs.

    A `loc` and a `label` that no arc connects are not a declaration,
    and are not returned: the arc is the filer's statement that this
    text names that element.
    """
    locators: dict[str, tuple[str, str]] = {}
    for attributes in _LOC.findall(body):
        href, xlink_label = _attr(attributes, "href"), _attr(attributes, "label")
        if href and xlink_label:
            locators[xlink_label] = (href, href.partition("#")[2])

    resources: dict[str, list[tuple[str, str, str | None]]] = {}
    for attributes, text in _LABEL.findall(body):
        xlink_label = _attr(attributes, "label")
        if not xlink_label:
            continue
        resources.setdefault(xlink_label, []).append((
            " ".join(re.sub(r"<[^>]+>", " ", text).split()),
            _attr(attributes, "role") or _STANDARD_ROLE,
            _attr(attributes, "lang"),
        ))

    out: list[TaxonomyLabel] = []
    seen: set[tuple[str, str, str, str | None]] = set()
    for attributes in _ARC.findall(body):
        source, target = _attr(attributes, "from"), _attr(attributes, "to")
        if source not in locators or target not in resources:
            continue
        href, element_id = locators[source]
        for text, role, language in resources[target]:
            key = (element_id, text, role, language)
            if key in seen:
                continue
            seen.add(key)
            out.append(TaxonomyLabel(
                element_href=href, element_id=element_id,
                element_qname=_qname_from_id(element_id), text=text, role=role,
                language=language, source_document=source_document,
                source_locator=source_locator))
    return tuple(out)
