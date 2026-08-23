"""Legal Proceedings Intelligence: transforms Filing Content
Intelligence's own structured filing objects into structured,
traceable legal-disclosure knowledge (Capability Expansion Sprint 18).

**Phase 1 audit finding.** Re-read fresh, not assumed: 10-K's own real
Item 3 (`FilingSectionKind.LEGAL_PROCEEDINGS`) is already mapped in
Filing Content Intelligence, unchanged since Sprint 13. **10-Q's own
Part II Item 1 -- also literally titled "Legal Proceedings" -- is
not.** `_TEN_Q_ITEM_MAP` maps only `("I","1")`/`("I","2")`/`("I","4")`/
`("II","1A")`; Part II Item 1 is one of the Items that module's own
comment already names as deliberately left unmapped ("Part II Items
1/2/3/5/6 ... have no member in Phase 3's own 10-Q taxonomy list").

This sprint's own Success Criteria explicitly lists "Filing Content
Intelligence remains unchanged" as a pass/fail condition, stronger than
the Scope section's own "must not redesign" -- so this module does not
add the missing item-map entry, even though it would be a minimal,
literal one-line registry addition using an already-existing
`FilingSectionKind` member. **10-Q Part II Item 1 is therefore a real,
disclosed, currently-unreachable source** -- not a bug, not silently
worked around by scanning `unattributed_paragraphs` either, since
Phase 3's own "do not indiscriminately scan unrelated sections" would
be violated by that (10-Q's own unattributed content mixes Item 1
alongside Items 2/3/5/6, with no reliable way to isolate just Item 1
without re-implementing Filing Content Intelligence's own Item-heading
detection inside this module -- exactly the "duplicate filing parsing"
the Architectural Rule also forbids).

**What real 10-Q legal coverage this module still has**: 10-Q's own
Risk Factors Update (`RISK_UPDATES`) and MD&A (`MDA`) sections *are*
reliably mapped, and litigation-flavored language appearing there is
still captured, honestly sourced as such (never mislabeled as coming
from a "Legal Proceedings" section that, for a 10-Q, this module never
actually reads). A future, separately-authorized sprint that is allowed
to touch Filing Content Intelligence could close this gap with the
single missing item-map entry; this sprint is not that sprint.

No `KnowledgeDomain` existed for legal disclosures -- `RISK_FACTORS`
(Item 1A) is a real, disclosed, *different* filing location and a
different disclosure-history convention (Item 3 has no SEC-mandated
"material changes only" convention the way a 10-Q's own Risk Factors
Update does). `KnowledgeDomain.LEGAL_PROCEEDINGS` is a new, minimum
necessary registry addition (`knowledge_coverage/models.py`), the same
category of change Sprint 15 made for `GOVERNANCE` -- not a redesign.

**Architecture is a direct, deliberate mirror of `risk_factor_
intelligence.py`** (Sprint 17, rebuilt against its own formal spec) --
the same `UNCLASSIFIED` fallback, the same five-state pairwise
disclosure history, and the identical filing-scope-awareness fix (a
10-Q as the *later* filing in a comparison never yields a reliable
"no longer disclosed" claim). This sprint's own spec asks for exactly
that architecture, phase by phase; reusing it faithfully rather than
inventing a parallel design is itself "prefer registry additions over
engine changes" applied at the whole-module level.

**"This company disclosed litigation" vs. "the litigation is
material"**: this module never determines liability, probability of
loss, or outcome. `ProceedingCategory` classifies *topic*, never
severity; `LegalChangeKind.LEGAL_PROCEEDING_NO_LONGER_DISCLOSED` means
only that a later comparable filing's own text omits a category --
never dismissal, settlement, victory, or loss, which this module has
no way to know and must never imply, in code, in this docstring, or in
any future API surface built on top of it."""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from atlas.alpha.investment_case.filing_content_intelligence import (
    FilingContent,
    FilingParagraph,
    FilingSection,
    FilingSectionKind,
    FilingSubsection,
    ExtractionStatus,
    find_section,
)

__all__ = [
    "ProceedingCategory",
    "LegalDisclosureSource",
    "LegalChangeKind",
    "LegalProceedingDisclosure",
    "ProceedingCategorySummary",
    "LegalChangeObservation",
    "LegalProceedingsKnowledge",
    "extract_legal_proceedings_knowledge",
]


class ProceedingCategory(str, Enum):
    """A closed, disclosed vocabulary of legal-proceeding topics -- the
    nine named in this sprint's own mission, plus `UNCLASSIFIED` for
    real, disclosed legal-section text this module cannot confidently
    classify. `UNCLASSIFIED` is never a placeholder for "not yet
    supported" -- it is the honest result of "this is real disclosed
    legal content, but no bounded phrase pattern here matches it,"
    exactly Phase 2's own instruction: preserve, never force a match."""

    LITIGATION = "litigation"
    REGULATORY_INVESTIGATION = "regulatory_investigation"
    INTELLECTUAL_PROPERTY = "intellectual_property"
    ENVIRONMENTAL = "environmental"
    TAX = "tax"
    LABOR = "labor"
    ANTITRUST = "antitrust"
    SECURITIES = "securities"
    CONTRACT = "contract"
    UNCLASSIFIED = "unclassified"


class LegalDisclosureSource(str, Enum):
    """Where a `LegalProceedingDisclosure` was read from -- not a
    strength judgment in itself, but real, disclosed provenance a
    reader can weigh."""

    LEGAL_PROCEEDINGS_SECTION = "legal_proceedings_section"
    """10-K Item 3 (`FilingSectionKind.LEGAL_PROCEEDINGS`) -- the only
    filing type this source is ever produced for; see this module's
    own top docstring for why a 10-Q's own Part II Item 1 cannot be."""
    RISK_FACTORS_SECTION = "risk_factors_section"
    """10-K Item 1A (`FilingSectionKind.RISK_FACTORS`)."""
    RISK_UPDATES_SECTION = "risk_updates_section"
    """10-Q Part II Item 1A (`FilingSectionKind.RISK_UPDATES`) -- the
    main real source of 10-Q legal disclosure this module can reach."""
    MDA_SECTION = "mda_section"
    """10-K Item 7 / 10-Q Part I Item 2 (`FilingSectionKind.MDA`)."""


class LegalChangeKind(str, Enum):
    """Phase 6's own closed, explicit change vocabulary -- derived by
    comparing one filing's own legal-proceedings-relevant disclosure
    against the *immediately preceding* comparable filing this call was
    given (an immutable, pairwise history, not a single cumulative
    snapshot)."""

    LEGAL_PROCEEDING_NEW = "legal_proceeding_new"
    """A category present in this filing with no matching category in
    the immediately preceding comparable filing -- never a claim a
    lawsuit is new to the company, which this module cannot know."""
    LEGAL_PROCEEDING_CONTINUES = "legal_proceeding_continues"
    """A category present in both filings, with byte-identical
    disclosed text on both sides -- a real, mechanical comparison, not
    a semantic "is it the same case" judgment."""
    LEGAL_PROCEEDING_WORDING_CHANGED = "legal_proceeding_wording_changed"
    """A category present in both filings, but the disclosed text
    differs -- see `previous_excerpts`/`current_excerpts` for exactly
    what changed. This module never characterizes *how* (escalated,
    narrowed, resolved) -- only that the text differs."""
    LEGAL_PROCEEDING_NO_LONGER_DISCLOSED = "legal_proceeding_no_longer_disclosed"
    """A category present in the earlier filing's own comparable legal
    disclosure, absent from the later one -- **only** when the later
    filing is itself expected to comprehensively restate its own legal
    proceedings (i.e. not a 10-Q; see `LEGAL_PROCEEDING_NOT_
    COMPARABLE`). Means only: the later filing's own text does not
    repeat this category in the comparable disclosure scope. **It must
    never be read as: case dismissed, settled, won, or lost** -- this
    module has no way to know any of those, and neither the API
    surface nor this docstring may ever imply otherwise (Phase 6's own
    explicit semantic rule)."""
    LEGAL_PROCEEDING_NOT_COMPARABLE = "legal_proceeding_not_comparable"
    """A category present in the earlier filing's own comparable legal
    disclosure, absent from the later one, where the later filing is a
    10-Q. **Phase 7's own explicit rule**: a 10-Q frequently updates
    only material changes -- its own silence on a category is expected
    and uninformative, never evidence a proceeding ended. This state
    exists specifically so `LEGAL_PROCEEDING_NO_LONGER_DISCLOSED` is
    never over-interpreted from an inherently partial filing."""


@dataclass(frozen=True)
class LegalProceedingDisclosure:
    """The bottom of Phase 2's own hierarchy -- one real, disclosed
    paragraph, always traceable to the exact filing, section,
    subsection, and paragraph (or, when a future filer discloses legal
    matters via a table, table cell) it came from. This sprint's own
    Phase 2 also names a "proceeding identifier" -- never populated
    here: SEC filings carry no mandated per-case identifier (a docket
    number, when disclosed at all, is free text embedded in prose, not
    a structured field), and inventing one by hashing text or assigning
    a sequence number would itself be fabricated structure the
    document never disclosed. A reader can already address any specific
    disclosure precisely via `accession_number` + `paragraph_order_
    index`, the same "structured provenance instead of an opaque
    identifier" discipline this codebase already applies elsewhere."""

    categories: tuple[ProceedingCategory, ...]
    """Never empty -- at least `(UNCLASSIFIED,)` for a Legal
    Proceedings/Risk Factors/Risk Updates paragraph matching no named
    category. May hold more than one real category when the text
    explicitly supports both."""
    text: str
    """Verbatim, whitespace-normalized disclosed text -- never
    rewritten, summarized, or reordered."""
    source: LegalDisclosureSource
    accession_number: str
    form_type: str
    filed_at: datetime
    source_reference: str
    section_kind: FilingSectionKind | None
    section_item_number: str | None
    subsection_heading: str | None
    paragraph_order_index: int
    table_order_index: int | None = None
    """Always `None` today -- real legal-proceeding disclosure is, in
    practice, prose, not tabular data. Kept for shape-readiness, the
    same "framework, not fabricated dataset" precedent `governance_
    intelligence.Director` and `risk_factor_intelligence.RiskDisclosure`
    already established."""


@dataclass(frozen=True)
class ProceedingCategorySummary:
    kind: ProceedingCategory
    disclosures: tuple[LegalProceedingDisclosure, ...]
    """Never empty -- a `ProceedingCategorySummary` only exists for a
    kind at least one real disclosure matched. A disclosure with more
    than one category appears in more than one summary's own
    `disclosures` -- an index, not a partition."""


@dataclass(frozen=True)
class LegalChangeObservation:
    kind: LegalChangeKind
    category: ProceedingCategory
    previous_excerpts: tuple[str, ...]
    """Every distinct verbatim text this category matched in the
    earlier filing's own comparable legal disclosure -- empty for
    `LEGAL_PROCEEDING_NEW`, where there is no earlier side."""
    current_excerpts: tuple[str, ...]
    """The mirror of `previous_excerpts` for the later filing -- empty
    for `LEGAL_PROCEEDING_NO_LONGER_DISCLOSED`/`LEGAL_PROCEEDING_NOT_
    COMPARABLE`, where there is no later side."""
    accession_number: str
    form_type: str
    filed_at: datetime
    source_reference: str
    """The *later* filing in the comparison -- the one whose own
    content this observation is reported against."""


@dataclass(frozen=True)
class LegalProceedingsKnowledge:
    categories: tuple[ProceedingCategorySummary, ...]
    """Every category with at least one real disclosure, across every
    filing supplied -- ordered by `ProceedingCategory.value`."""
    changes: tuple[LegalChangeObservation, ...]
    """Phase 5/6's own immutable, pairwise disclosure history --
    chronologically ordered, one full comparison per pair of
    consecutive filings (among those with any real comparable-section
    evidence) this call was given."""
    disclosures: tuple[LegalProceedingDisclosure, ...]
    """Every disclosure this call detected, across every filing
    supplied, in filing-then-document order."""
    filings_considered: tuple[str, ...]
    """Accession numbers of every filing actually used, chronological
    -- `extraction_status in (EXTRACTED, STRUCTURE_UNKNOWN)` only; a
    `FETCH_FAILED`/`NOT_ATTEMPTED` filing contributes nothing, silently,
    the same way Filing Content Intelligence itself never raises on one."""


#: A closed, bounded set of real, disclosed English phrases per
#: category -- Phase 4's own named examples, matching the identical
#: discipline `risk_factor_intelligence._CATEGORY_PATTERNS` and
#: `governance_intelligence._COMMITTEE_PATTERNS` already apply.
_CATEGORY_PATTERNS: tuple[tuple[re.Pattern[str], ProceedingCategory], ...] = (
    (
        re.compile(r"\b(securities class action|shareholder litigation)\b", re.IGNORECASE),
        ProceedingCategory.SECURITIES,
    ),
    (
        re.compile(r"\b(SEC investigation|DOJ|regulatory investigation|subpoena|inquiry)\b", re.IGNORECASE),
        ProceedingCategory.REGULATORY_INVESTIGATION,
    ),
    (
        re.compile(r"\b(patents?|copyrights?|trademarks?|intellectual property)\b", re.IGNORECASE),
        ProceedingCategory.INTELLECTUAL_PROPERTY,
    ),
    (
        re.compile(r"\b(environmental|EPA|remediation)\b", re.IGNORECASE),
        ProceedingCategory.ENVIRONMENTAL,
    ),
    (
        re.compile(r"\b(tax dispute|tax authority|tax authorities)\b", re.IGNORECASE),
        ProceedingCategory.TAX,
    ),
    (
        re.compile(r"\b(employment|labor|workplace)\b", re.IGNORECASE),
        ProceedingCategory.LABOR,
    ),
    (
        re.compile(r"\b(antitrust|monopoly|monopolization)\b", re.IGNORECASE),
        ProceedingCategory.ANTITRUST,
    ),
    (
        re.compile(r"\b(breach of contract|contractual dispute)\b", re.IGNORECASE),
        ProceedingCategory.CONTRACT,
    ),
    (
        re.compile(r"\b(lawsuit|litigation|legal proceedings?|defendants?|plaintiffs?)\b", re.IGNORECASE),
        ProceedingCategory.LITIGATION,
    ),
)
#: `LITIGATION`'s own pattern is deliberately last: a broad, generic
#: filing-wide word like "litigation" should not preempt a more
#: specific real match (e.g. "securities class action," itself
#: obviously litigation too) -- every pattern is still independently
#: tested against the full text regardless of order (a paragraph may
#: match both), this ordering only reflects reading intent, not control
#: flow -- there is no early-exit here.

_RELEVANT_SECTION_SOURCE: dict[FilingSectionKind, LegalDisclosureSource] = {
    FilingSectionKind.LEGAL_PROCEEDINGS: LegalDisclosureSource.LEGAL_PROCEEDINGS_SECTION,
    FilingSectionKind.RISK_FACTORS: LegalDisclosureSource.RISK_FACTORS_SECTION,
    FilingSectionKind.RISK_UPDATES: LegalDisclosureSource.RISK_UPDATES_SECTION,
    FilingSectionKind.MDA: LegalDisclosureSource.MDA_SECTION,
}
#: The "primary" comparable-disclosure sources for Phase 5/6/7's own
#: pairwise history -- `LEGAL_PROCEEDINGS_SECTION` (10-K Item 3, the
#: SEC-mandated legal disclosure) and `RISK_UPDATES_SECTION` (10-Q's
#: own real, reachable proxy for legal-relevant "material changes").
#: `MDA_SECTION` is real but incidental, exactly like `risk_factor_
#: intelligence.py`'s own identical exclusion, and is never allowed to
#: seed or break a comparison baseline on its own.
_COMPARABLE_SOURCES = frozenset({LegalDisclosureSource.LEGAL_PROCEEDINGS_SECTION, LegalDisclosureSource.RISK_UPDATES_SECTION})
_USABLE_STATUSES = frozenset({ExtractionStatus.EXTRACTED, ExtractionStatus.STRUCTURE_UNKNOWN})


def _iter_relevant_paragraphs(
    content: FilingContent,
) -> "list[tuple[FilingParagraph, LegalDisclosureSource, FilingSection, FilingSubsection | None]]":
    """Only the real, disclosed sections this module's own mission
    names -- Legal Proceedings, Risk Factors, Risk Updates, MD&A.
    Unlike `governance_intelligence.py`, this module never falls back
    to `unattributed_paragraphs`: a legal claim detached from a
    confirmed heading is not the disclosure this module means to
    describe (Phase 3's own "do not indiscriminately scan unrelated
    sections")."""
    result: list[tuple[FilingParagraph, LegalDisclosureSource, FilingSection, FilingSubsection | None]] = []
    for section_kind, source in _RELEVANT_SECTION_SOURCE.items():
        section = find_section(content, section_kind)
        if section is None:
            continue
        for paragraph in section.paragraphs:
            result.append((paragraph, source, section, None))
        for subsection in section.subsections:
            for paragraph in subsection.paragraphs:
                result.append((paragraph, source, section, subsection))
    return result


def _matching_categories(text: str) -> tuple[ProceedingCategory, ...]:
    return tuple(category for pattern, category in _CATEGORY_PATTERNS if pattern.search(text) is not None)


def _no_longer_disclosed_is_reliable(later_form_type: str) -> bool:
    """`False` only when the *later* filing is a 10-Q -- Phase 7's own
    explicit rule, identical to `risk_factor_intelligence.py`'s own
    corrected logic. A 10-K, regardless of what preceded it, is
    expected to comprehensively restate its own Item 3, so its own
    silence on a category IS real, comparable evidence; a 10-Q's own
    Part II Item 1 update is not."""
    return later_form_type != "10-Q"


def extract_legal_proceedings_knowledge(filing_contents: tuple[FilingContent, ...]) -> LegalProceedingsKnowledge:
    """Built entirely upon Filing Content Intelligence's own output --
    never fetches, parses HTML, or reads a `RegulatoryFiling` directly.
    Filings are processed chronologically (`filed_at`, oldest first);
    `changes` compares each filing with real comparable-section evidence
    against the *immediately preceding* such filing only -- an
    immutable, pairwise history (Phase 5), never a single cumulative
    "ever seen" snapshot."""
    usable = tuple(sorted((c for c in filing_contents if c.extraction_status in _USABLE_STATUSES), key=lambda c: c.filed_at))

    all_disclosures: list[LegalProceedingDisclosure] = []
    disclosures_by_category: dict[ProceedingCategory, list[LegalProceedingDisclosure]] = {}
    #: (filing, {category: frozenset(verbatim texts)}) -- comparable-
    #: source evidence only (`_COMPARABLE_SOURCES`, never MD&A), one
    #: entry per usable filing that produced any such evidence at all.
    filing_summaries: list[tuple[FilingContent, dict[ProceedingCategory, frozenset[str]]]] = []

    for content in usable:
        comparable_texts: dict[ProceedingCategory, set[str]] = {}

        for paragraph, source, section, subsection in _iter_relevant_paragraphs(content):
            text = paragraph.text
            is_comparable = source in _COMPARABLE_SOURCES
            is_legal_relevant = source in (LegalDisclosureSource.LEGAL_PROCEEDINGS_SECTION, LegalDisclosureSource.RISK_UPDATES_SECTION)
            categories = _matching_categories(text)
            if not categories:
                if not is_legal_relevant:
                    continue
                categories = (ProceedingCategory.UNCLASSIFIED,)

            disclosure = LegalProceedingDisclosure(
                categories=categories, text=text, source=source, accession_number=content.accession_number,
                form_type=content.form_type, filed_at=content.filed_at, source_reference=content.source_reference,
                section_kind=section.kind, section_item_number=section.item_number,
                subsection_heading=subsection.heading_text if subsection is not None else None,
                paragraph_order_index=paragraph.order_index,
            )
            all_disclosures.append(disclosure)
            for category in categories:
                disclosures_by_category.setdefault(category, []).append(disclosure)
                if is_comparable:
                    comparable_texts.setdefault(category, set()).add(text)

        if comparable_texts:
            filing_summaries.append((content, {k: frozenset(v) for k, v in comparable_texts.items()}))

    changes: list[LegalChangeObservation] = []
    for i in range(1, len(filing_summaries)):
        earlier_content, earlier_categories = filing_summaries[i - 1]
        later_content, later_categories = filing_summaries[i]
        no_longer_disclosed_reliable = _no_longer_disclosed_is_reliable(later_content.form_type)
        all_categories = set(earlier_categories) | set(later_categories)

        for category in sorted(all_categories, key=lambda k: k.value):
            earlier_texts = earlier_categories.get(category)
            later_texts = later_categories.get(category)

            if earlier_texts is not None and later_texts is not None:
                kind = LegalChangeKind.LEGAL_PROCEEDING_CONTINUES if earlier_texts == later_texts else LegalChangeKind.LEGAL_PROCEEDING_WORDING_CHANGED
            elif later_texts is not None:
                kind = LegalChangeKind.LEGAL_PROCEEDING_NEW
            elif no_longer_disclosed_reliable:
                kind = LegalChangeKind.LEGAL_PROCEEDING_NO_LONGER_DISCLOSED
            else:
                kind = LegalChangeKind.LEGAL_PROCEEDING_NOT_COMPARABLE

            changes.append(
                LegalChangeObservation(
                    kind=kind, category=category, previous_excerpts=tuple(sorted(earlier_texts or ())),
                    current_excerpts=tuple(sorted(later_texts or ())), accession_number=later_content.accession_number,
                    form_type=later_content.form_type, filed_at=later_content.filed_at,
                    source_reference=later_content.source_reference,
                )
            )

    categories = tuple(
        ProceedingCategorySummary(kind=kind, disclosures=tuple(disclosures_by_category[kind]))
        for kind in sorted(disclosures_by_category, key=lambda k: k.value)
    )

    return LegalProceedingsKnowledge(
        categories=categories, changes=tuple(changes), disclosures=tuple(all_disclosures),
        filings_considered=tuple(c.accession_number for c in usable),
    )
