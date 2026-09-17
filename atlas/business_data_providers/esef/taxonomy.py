"""What an issuer's own taxonomy says about its own concepts.

The facts in an ESEF report are just concept/period/value triples. Everything
that gives an extension concept meaning lives in the taxonomy package, which is
a separate download: the calculation linkbase says which concepts add up to
which, and ESMA's anchoring relation says which standard IFRS concept an
extension is wider or narrower than.

Anchoring is what makes generic normalization possible at all. Volvo tags its
capital expenditure with two concepts of its own invention, and no amount of
reading their names would prove what they are -- but the taxonomy states that
both are *narrower than* the standard
`PurchaseOfPropertyPlantAndEquipmentClassifiedAsInvestingActivities`, which is
a fact about meaning rather than a guess about spelling.

Direction is preserved and is not decoration. `wider` means the extension
contains at least the standard concept and possibly more; `narrower` means it
is a part of it. Treating the two as equality is how a bucket that happens to
include lease liabilities silently becomes "borrowings".
"""
from __future__ import annotations

import collections
import xml.etree.ElementTree as ET
import zipfile
from dataclasses import dataclass, field

_XLINK = "{http://www.w3.org/1999/xlink}"
#: ESMA's anchoring arc, the relation ESEF requires an issuer to declare for
#: every extension concept it creates.
ANCHOR_ARCROLE = "http://www.esma.europa.eu/xbrl/esef/arcrole/wider-narrower"

__all__ = ["EsefTaxonomy", "ANCHOR_ARCROLE", "read_taxonomy", "to_qname"]


def to_qname(concept: str) -> str:
    """Linkbases write `abvolvo_CurrentOtherLoans`; facts write
    `abvolvo:CurrentOtherLoans`.

    The separator is the first underscore, for every prefix rather than just
    `ifrs-full`: XBRL local names are camel case and contain none, while the
    prefixes that matter here are exactly the issuers' own. Converting only
    the standard prefix leaves every extension unfindable, which looks like an
    issuer that tagged nothing.
    """
    if ":" in concept or "_" not in concept:
        return concept
    prefix, local = concept.split("_", 1)
    return f"{prefix}:{local}"


@dataclass(frozen=True)
class EsefTaxonomy:
    #: parent concept -> [(child concept, weight)] from the calculation linkbase.
    calculations: dict[str, tuple[tuple[str, str], ...]] = field(default_factory=dict)
    #: (wider concept, narrower concept) pairs from the ESMA anchoring relation.
    anchors: tuple[tuple[str, str], ...] = ()

    def children(self, parent: str) -> tuple[str, ...]:
        return tuple(child for child, _ in self.calculations.get(parent, ()))

    def is_extension(self, concept: str) -> bool:
        return not concept.startswith(("ifrs-full_", "ifrs-full:"))

    def standards_narrower_than(self, extension: str) -> frozenset[str]:
        """The standard concepts this extension is declared to *contain*.

        A non-empty answer means the extension is a bucket: it holds at least
        these things, which is exactly what has to be known before deciding
        whether the bucket is safe to read as one Atlas field.
        """
        return frozenset(n for w, n in self.anchors if w == extension and not self.is_extension(n))

    def standards_wider_than(self, extension: str) -> frozenset[str]:
        """The standard concepts this extension is declared to be *part of*."""
        return frozenset(w for w, n in self.anchors if n == extension and not self.is_extension(w))

    def extensions_narrower_than(self, standard: str) -> frozenset[str]:
        """Extensions declared to be a part of `standard` -- the generic route
        from a concept Atlas knows to the concepts one issuer invented for it."""
        return frozenset(n for w, n in self.anchors if w == standard and self.is_extension(n))


def _locators(root: ET.Element) -> dict[str, str]:
    return {
        element.get(_XLINK + "label"): element.get(_XLINK + "href", "").split("#")[-1]
        for element in root.iter()
        if element.tag.endswith("}loc")
    }


def read_taxonomy(package: zipfile.ZipFile) -> EsefTaxonomy:
    """Read every calculation and anchoring relation in an ESEF package.

    Linkbases are located by filename suffix (`_cal.xml`, `_def.xml`), the
    convention ESEF packages follow. A package that carries neither yields an
    empty taxonomy, and every caller treats that as "cannot interpret this
    issuer's extensions" rather than as permission to fall back on names.
    """
    calculations: dict[str, list[tuple[str, str]]] = collections.defaultdict(list)
    anchors: list[tuple[str, str]] = []

    for name in package.namelist():
        if name.endswith("_cal.xml"):
            root = ET.fromstring(package.read(name))
            locators = _locators(root)
            for element in root.iter():
                if element.tag.endswith("}calculationArc"):
                    parent = locators.get(element.get(_XLINK + "from"))
                    child = locators.get(element.get(_XLINK + "to"))
                    if parent and child:
                        calculations[parent].append((child, element.get("weight") or "1.0"))
        elif name.endswith("_def.xml"):
            root = ET.fromstring(package.read(name))
            locators = _locators(root)
            for element in root.iter():
                if element.tag.endswith("}definitionArc") and element.get(_XLINK + "arcrole") == ANCHOR_ARCROLE:
                    wider = locators.get(element.get(_XLINK + "from"))
                    narrower = locators.get(element.get(_XLINK + "to"))
                    if wider and narrower:
                        anchors.append((wider, narrower))

    return EsefTaxonomy(
        calculations={k: tuple(v) for k, v in calculations.items()},
        anchors=tuple(anchors),
    )
