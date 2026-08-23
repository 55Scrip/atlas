"""Risk Factor Intelligence: transforms Filing Content Intelligence's
own structured filing objects into structured, traceable risk-factor
knowledge (Capability Expansion Sprint 17).

**Phase 1 audit finding, re-read fresh against this sprint's own,
more detailed specification.** A first, informal version of this
capability already existed in this codebase before this sprint's own
formal spec arrived. Re-reading it fresh (not relying on its own prior
report) against this spec's own Phases 2, 5, 6, and 7 found three
genuine, real gaps -- not renamed for their own sake, but corrected
because the fresh read found them honestly missing:

1. **No `UNCLASSIFIED` fallback (Phase 2)**: a Risk Factors/Risk
   Updates paragraph matching none of the ten named categories was
   previously dropped silently -- real, disclosed risk text, discarded
   rather than preserved. This sprint's own Phase 2 explicitly asks for
   an honest `UNCLASSIFIED` category instead of forcing a match or
   silently losing the disclosure.
2. **No `CONTINUES`/`WORDING_CHANGED` observations (Phase 5/6)**: the
   prior version only ever emitted an observation on a detected change,
   never confirmed that a category was disclosed *again*, identically
   or with different wording. Phase 5's own five-state history
   (newly disclosed / continuing / changed wording / not repeated / not
   comparable) needs all five states represented, not two.
3. **No filing-scope awareness for "no longer disclosed" (Phase 7)**:
   the prior version treated any later filing's own risk-section
   absence as reportable, live-verified against a real AAPL 10-K -> 10-Q
   transition where several categories legitimately dropped out simply
   because a 10-Q's own Risk Factors Update, by real SEC convention,
   discloses only *material changes* since the last 10-K -- not the
   full annual disclosure. That is expected, not evidence of anything,
   and this sprint's own Phase 7 makes the distinction explicit. Fixed
   by gating `RISK_CATEGORY_NO_LONGER_DISCLOSED` on the *later* filing's
   own form type; a 10-Q on that side yields `RISK_DISCLOSURE_NOT_
   COMPARABLE` instead.

Everything else was re-verified, not just re-cited, and already held:
`KnowledgeDomain.RISK_FACTORS` already existed in the base enum (unlike
`GOVERNANCE`, which Sprint 15 had to add) -- it had no real extractor
wired in `knowledge_coverage.engine._DOMAIN_EXTRACTORS` yet, and
`knowledge_strategy.relevance.DOMAIN_RELEVANCE` already carried a real
opinion for it (`MEDIUM`, `ALREADY_REPRESENTED_ELSEWHERE` +
`MAY_MATERIALLY_CHANGE_RISK_ASSESSMENT`). `ALREADY_REPRESENTED_
ELSEWHERE` refers to `atlas.analysis_engine.risk` (`business_risk.py`/
`financial_risk.py`/`valuation_risk.py`/`thesis_risk.py`) -- a real,
already-running Decision Layer evaluator that produces categorical
risk *conclusions* from structured financial facts. This module is a
genuinely different, complementary layer: it reads a filing's own raw
Risk Factors/MD&A *disclosure text* and preserves what topics the
company itself raises, never a conclusion about how risky the company
actually is -- the identical "evidence, not opinion" boundary
`governance_intelligence.py` already established for board/committee
facts. This module never imports `atlas.analysis_engine.risk` and is
never imported by it (a dedicated test guards both).

Filing Content Intelligence already detects everything this module
needs: 10-K's own real Item 1A (`FilingSectionKind.RISK_FACTORS`) and
Item 7 (`MDA`), and 10-Q's own real Part II Item 1A (`RISK_UPDATES`)
and Part I Item 2 (`MDA`) -- all real, SEC-mandated Item numbers,
already mapped, since Sprint 13. **This module requires zero changes
to Filing Content Intelligence** -- confirmed by re-reading that
module fresh before writing a line of this one, and by the fact that
this module's own diff never touches it.

**Why keyword-matching a risk topic is preservation, not judgment.**
SEC Item 1A carries no sub-item numbering the way `Item N` does at the
section level -- there is no mandated convention this module could
reuse to segment "the cybersecurity risk" from "the litigation risk"
within one long Item 1A. What *is* real and disclosed is the topical
vocabulary a risk factor paragraph itself uses -- a paragraph that says
"cybersecurity," "data breach," or "unauthorized access to our systems"
is disclosing a cybersecurity-flavored risk, regardless of whether
Atlas judges that risk to be significant. A closed, bounded set of
real English phrases per category (mirroring `governance_intelligence.
py`'s own `_COMMITTEE_PATTERNS`) classifies *what the paragraph is
about*, never *how bad it is* -- this module assigns no severity, no
score, no ranking. A paragraph may match several categories at once (a
real disclosed risk often spans topics); a Risk Factors/Risk Updates
paragraph matching none is preserved as `UNCLASSIFIED`, never dropped
and never forced into the closest real category. An MD&A paragraph
matching none is not itself a risk disclosure and is simply not
represented -- MD&A is a broad results discussion, not a risk section,
so only its genuinely risk-flavored sentences are pulled in.

**"Uncertainty" (Phase 10) is represented by two existing closed
states, not a third, invented confidence field**: `RiskCategory.
UNCLASSIFIED` at the classification level, and `RiskChangeKind.
RISK_DISCLOSURE_NOT_COMPARABLE` at the comparison level. A numeric or
fuzzy "confidence score" would be exactly the kind of fabricated
precision this whole capability exists to avoid."""
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
    "RiskCategory",
    "RiskDisclosureSource",
    "RiskChangeKind",
    "RiskDisclosure",
    "RiskCategorySummary",
    "RiskChangeObservation",
    "RiskFactorKnowledge",
    "extract_risk_factor_knowledge",
]


class RiskCategory(str, Enum):
    """A closed, disclosed vocabulary of risk topics -- the ten named
    in this sprint's own mission, plus `UNCLASSIFIED` for real,
    disclosed risk-section text this module cannot confidently
    classify. `UNCLASSIFIED` is never a placeholder for "not yet
    supported" -- it is the honest result of "this is real disclosed
    risk content, but no bounded phrase pattern here matches it,"
    exactly Phase 2's own instruction: preserve, never force a match."""

    BUSINESS = "business"
    FINANCIAL = "financial"
    REGULATORY = "regulatory"
    TECHNOLOGY = "technology"
    CYBERSECURITY = "cybersecurity"
    SUPPLY_CHAIN = "supply_chain"
    CUSTOMER_CONCENTRATION = "customer_concentration"
    LITIGATION = "litigation"
    ENVIRONMENTAL = "environmental"
    GEOPOLITICAL = "geopolitical"
    UNCLASSIFIED = "unclassified"


class RiskDisclosureSource(str, Enum):
    """Where a `RiskDisclosure` was read from -- not a strength
    judgment in itself, but real, disclosed provenance a reader can
    weigh: Item 1A/Risk Updates is the SEC-mandated risk disclosure;
    MD&A is management's own narrative discussion, which may touch a
    risk topic only incidentally."""

    RISK_FACTORS_SECTION = "risk_factors_section"
    """10-K Item 1A (`FilingSectionKind.RISK_FACTORS`)."""
    RISK_UPDATES_SECTION = "risk_updates_section"
    """10-Q Part II Item 1A (`FilingSectionKind.RISK_UPDATES`)."""
    MDA_SECTION = "mda_section"
    """10-K Item 7 / 10-Q Part I Item 2 (`FilingSectionKind.MDA`)."""


class RiskChangeKind(str, Enum):
    """Phase 6's own closed, explicit change vocabulary -- derived by
    comparing one filing's own Risk Factors/Risk Updates disclosure
    against the *immediately preceding* comparable filing this call was
    given (an immutable, pairwise history, not a single cumulative
    snapshot -- Phase 5's own "preserve whether a category is newly
    disclosed, still present, changed, not repeated, or not
    comparable")."""

    RISK_CATEGORY_NEWLY_DISCLOSED = "risk_category_newly_disclosed"
    """A category present in this filing's own Risk Factors/Risk
    Updates section with no matching category in the immediately
    preceding comparable filing's own such section -- never a claim
    the underlying risk is new to the company, which this module
    cannot know."""
    RISK_CATEGORY_CONTINUES = "risk_category_continues"
    """A category present in both filings, with byte-identical
    disclosed text on both sides -- a real, mechanical comparison, not
    a semantic "did the meaning change" judgment."""
    RISK_CATEGORY_WORDING_CHANGED = "risk_category_wording_changed"
    """A category present in both filings, but the disclosed text
    differs -- see `previous_excerpts`/`current_excerpts` for exactly
    what changed. This module never characterizes *how* the wording
    changed (softer, stronger, more specific) -- only that it did."""
    RISK_CATEGORY_NO_LONGER_DISCLOSED = "risk_category_no_longer_disclosed"
    """A category present in the earlier filing's own Risk Factors/
    Risk Updates section, absent from the later one -- **only** when
    the later filing is itself expected to comprehensively restate its
    own risk factors (i.e. not a 10-Q; see `RISK_DISCLOSURE_NOT_
    COMPARABLE`). Means only: the later filing's own text does not
    repeat this category in the comparable disclosure scope. It must
    never be read as: the underlying risk no longer exists -- this
    module has no way to know that, and neither the API surface nor
    this docstring may ever imply otherwise (Phase 6's own explicit
    semantic rule)."""
    RISK_DISCLOSURE_NOT_COMPARABLE = "risk_disclosure_not_comparable"
    """A category present in the earlier filing's own Risk Factors/
    Risk Updates section, absent from the later one, where the later
    filing is a 10-Q. **Phase 7's own explicit rule**: a 10-Q's Risk
    Factors Update, by real SEC convention, discloses only *material
    changes* since the last 10-K -- not the full annual disclosure. Its
    own silence on a category is expected and uninformative, never
    evidence the category was resolved or dropped. This state exists
    specifically so `RISK_CATEGORY_NO_LONGER_DISCLOSED` is never
    over-interpreted from an inherently partial filing."""


@dataclass(frozen=True)
class RiskDisclosure:
    """The bottom of Phase 2's own hierarchy -- one real, disclosed
    paragraph, always traceable to the exact filing, section,
    subsection, and paragraph (or, when a future filer discloses risk
    via a table, table cell) it came from."""

    categories: tuple[RiskCategory, ...]
    """Never empty -- at least `(UNCLASSIFIED,)` for a Risk Factors/
    Risk Updates paragraph matching no named category. May hold more
    than one real category when the text explicitly supports both."""
    text: str
    """Verbatim, whitespace-normalized disclosed text -- never
    rewritten, summarized, or reordered."""
    source: RiskDisclosureSource
    accession_number: str
    form_type: str
    filed_at: datetime
    source_reference: str
    section_kind: FilingSectionKind | None
    section_item_number: str | None
    subsection_heading: str | None
    paragraph_order_index: int
    table_order_index: int | None = None
    """Always `None` today -- real risk-factor disclosure is, in
    practice, prose, not tabular data (unlike Governance Intelligence's
    own board/committee tables). Kept for shape-readiness, the same
    "framework, not fabricated dataset" precedent `governance_
    intelligence.Director` already established, should a future filer
    ever disclose risk content in a structured table."""


@dataclass(frozen=True)
class RiskCategorySummary:
    kind: RiskCategory
    disclosures: tuple[RiskDisclosure, ...]
    """Never empty -- a `RiskCategorySummary` only exists for a kind at
    least one real disclosure matched. A disclosure with more than one
    category appears in more than one summary's own `disclosures` --
    an index, not a partition."""


@dataclass(frozen=True)
class RiskChangeObservation:
    kind: RiskChangeKind
    category: RiskCategory
    previous_excerpts: tuple[str, ...]
    """Every distinct verbatim text this category matched in the
    earlier filing's own Risk Factors/Risk Updates section -- empty for
    `RISK_CATEGORY_NEWLY_DISCLOSED`, where there is no earlier side."""
    current_excerpts: tuple[str, ...]
    """The mirror of `previous_excerpts` for the later filing -- empty
    for `RISK_CATEGORY_NO_LONGER_DISCLOSED`/`RISK_DISCLOSURE_NOT_
    COMPARABLE`, where there is no later side."""
    accession_number: str
    form_type: str
    filed_at: datetime
    source_reference: str
    """The *later* filing in the comparison -- the one whose own
    content this observation is reported against."""


@dataclass(frozen=True)
class RiskFactorKnowledge:
    categories: tuple[RiskCategorySummary, ...]
    """Every risk category with at least one real disclosure, across
    every filing supplied -- ordered by `RiskCategory.value`."""
    changes: tuple[RiskChangeObservation, ...]
    """Phase 5/6's own immutable, pairwise disclosure history --
    chronologically ordered, one full comparison per pair of
    consecutive filings (among those with any real Risk Factors/Risk
    Updates evidence) this call was given."""
    disclosures: tuple[RiskDisclosure, ...]
    """Every disclosure this call detected, across every filing
    supplied, in filing-then-document order."""
    filings_considered: tuple[str, ...]
    """Accession numbers of every filing actually used, chronological
    -- `extraction_status in (EXTRACTED, STRUCTURE_UNKNOWN)` only; a
    `FETCH_FAILED`/`NOT_ATTEMPTED` filing contributes nothing, silently,
    the same way Filing Content Intelligence itself never raises on one."""


#: A closed, bounded set of real, disclosed English phrases per
#: category -- the same "match a real, literal phrase, never an
#: open-ended heuristic" discipline `governance_intelligence.py`'s own
#: `_COMMITTEE_PATTERNS` already applies.
_CATEGORY_PATTERNS: tuple[tuple[re.Pattern[str], RiskCategory], ...] = (
    (
        re.compile(r"\b(cybersecurity|cyber[\s-]?attack|data breach|security breach|unauthorized access|information security)\b", re.IGNORECASE),
        RiskCategory.CYBERSECURITY,
    ),
    (
        re.compile(r"\b(litigation|lawsuit|legal proceeding|claims? against us)\b", re.IGNORECASE),
        RiskCategory.LITIGATION,
    ),
    (
        re.compile(r"\b(supply chain|suppliers?|supplier disruptions?|component shortages?|sole[\s-]?source|single[\s-]?source)\b", re.IGNORECASE),
        RiskCategory.SUPPLY_CHAIN,
    ),
    (
        re.compile(
            r"\b(customer concentration|significant customers?|major customers?|limited number of customers?)\b",
            re.IGNORECASE,
        ),
        RiskCategory.CUSTOMER_CONCENTRATION,
    ),
    (
        re.compile(r"\b(regulat(?:ion|ory|ions)|compliance requirements?|compliance with (?:applicable )?laws)\b", re.IGNORECASE),
        RiskCategory.REGULATORY,
    ),
    (
        re.compile(r"\b(climate change|environmental (?:regulation|law|matters?|compliance)|emissions|sustainability)\b", re.IGNORECASE),
        RiskCategory.ENVIRONMENTAL,
    ),
    (
        re.compile(r"\b(geopolitical|political instability|trade war|trade restrictions?|tariffs?|sanctions|armed conflict)\b", re.IGNORECASE),
        RiskCategory.GEOPOLITICAL,
    ),
    (
        re.compile(r"\b(intellectual property|information technology systems?|software (?:failures?|defects?)|technological changes?)\b", re.IGNORECASE),
        RiskCategory.TECHNOLOGY,
    ),
    (
        re.compile(r"\b(indebtedness|liquidity|credit rating|interest rate|currency exchange|financial condition)\b", re.IGNORECASE),
        RiskCategory.FINANCIAL,
    ),
    (
        re.compile(r"\b(competition|competitive pressures?|economic conditions?|market conditions?)\b", re.IGNORECASE),
        RiskCategory.BUSINESS,
    ),
)

_RELEVANT_SECTION_SOURCE: dict[FilingSectionKind, RiskDisclosureSource] = {
    FilingSectionKind.RISK_FACTORS: RiskDisclosureSource.RISK_FACTORS_SECTION,
    FilingSectionKind.RISK_UPDATES: RiskDisclosureSource.RISK_UPDATES_SECTION,
    FilingSectionKind.MDA: RiskDisclosureSource.MDA_SECTION,
}
_RISK_SECTION_SOURCES = frozenset({RiskDisclosureSource.RISK_FACTORS_SECTION, RiskDisclosureSource.RISK_UPDATES_SECTION})
_USABLE_STATUSES = frozenset({ExtractionStatus.EXTRACTED, ExtractionStatus.STRUCTURE_UNKNOWN})


def _iter_relevant_paragraphs(
    content: FilingContent,
) -> "list[tuple[FilingParagraph, RiskDisclosureSource, FilingSection, FilingSubsection | None]]":
    """Only the real, disclosed sections this module's own mission
    names -- Risk Factors, Risk Updates, MD&A. Unlike `governance_
    intelligence.py`, this module never falls back to
    `unattributed_paragraphs`: a risk claim detached from a confirmed
    Item 1A/7 heading is not the disclosure this module means to
    describe (Phase 3's own "do not scan the entire filing
    indiscriminately if a reliable section boundary exists")."""
    result: list[tuple[FilingParagraph, RiskDisclosureSource, FilingSection, FilingSubsection | None]] = []
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


def _matching_categories(text: str) -> tuple[RiskCategory, ...]:
    return tuple(category for pattern, category in _CATEGORY_PATTERNS if pattern.search(text) is not None)


def _no_longer_disclosed_is_reliable(later_form_type: str) -> bool:
    """`False` only when the *later* filing is a 10-Q -- Phase 7's own
    explicit rule. A 10-K, regardless of what preceded it, is expected
    to comprehensively restate its own risk factors, so its own
    silence on a category IS real, comparable evidence; a 10-Q's own
    Risk Factors Update is not."""
    return later_form_type != "10-Q"


def extract_risk_factor_knowledge(filing_contents: tuple[FilingContent, ...]) -> RiskFactorKnowledge:
    """Built entirely upon Filing Content Intelligence's own output --
    never fetches, parses HTML, or reads a `RegulatoryFiling` directly.
    Filings are processed chronologically (`filed_at`, oldest first);
    `changes` compares each filing with real Risk Factors/Risk Updates
    evidence against the *immediately preceding* such filing only --
    an immutable, pairwise history (Phase 5), never a single cumulative
    "ever seen" snapshot that would silently lose a category's own
    reappearance after a gap."""
    usable = tuple(sorted((c for c in filing_contents if c.extraction_status in _USABLE_STATUSES), key=lambda c: c.filed_at))

    all_disclosures: list[RiskDisclosure] = []
    disclosures_by_category: dict[RiskCategory, list[RiskDisclosure]] = {}
    #: (filing, {category: frozenset(verbatim texts)}) -- Risk Factors/
    #: Risk Updates evidence only (never MD&A), one entry per usable
    #: filing that produced any such evidence at all.
    filing_summaries: list[tuple[FilingContent, dict[RiskCategory, frozenset[str]]]] = []

    for content in usable:
        risk_section_texts: dict[RiskCategory, set[str]] = {}

        for paragraph, source, section, subsection in _iter_relevant_paragraphs(content):
            text = paragraph.text
            is_risk_section = source in _RISK_SECTION_SOURCES
            categories = _matching_categories(text)
            if not categories:
                if not is_risk_section:
                    continue
                categories = (RiskCategory.UNCLASSIFIED,)

            disclosure = RiskDisclosure(
                categories=categories, text=text, source=source, accession_number=content.accession_number,
                form_type=content.form_type, filed_at=content.filed_at, source_reference=content.source_reference,
                section_kind=section.kind, section_item_number=section.item_number,
                subsection_heading=subsection.heading_text if subsection is not None else None,
                paragraph_order_index=paragraph.order_index,
            )
            all_disclosures.append(disclosure)
            for category in categories:
                disclosures_by_category.setdefault(category, []).append(disclosure)
                if is_risk_section:
                    risk_section_texts.setdefault(category, set()).add(text)

        if risk_section_texts:
            filing_summaries.append((content, {k: frozenset(v) for k, v in risk_section_texts.items()}))

    changes: list[RiskChangeObservation] = []
    for i in range(1, len(filing_summaries)):
        earlier_content, earlier_categories = filing_summaries[i - 1]
        later_content, later_categories = filing_summaries[i]
        no_longer_disclosed_reliable = _no_longer_disclosed_is_reliable(later_content.form_type)
        all_categories = set(earlier_categories) | set(later_categories)

        for category in sorted(all_categories, key=lambda k: k.value):
            earlier_texts = earlier_categories.get(category)
            later_texts = later_categories.get(category)

            if earlier_texts is not None and later_texts is not None:
                kind = RiskChangeKind.RISK_CATEGORY_CONTINUES if earlier_texts == later_texts else RiskChangeKind.RISK_CATEGORY_WORDING_CHANGED
            elif later_texts is not None:
                kind = RiskChangeKind.RISK_CATEGORY_NEWLY_DISCLOSED
            elif no_longer_disclosed_reliable:
                kind = RiskChangeKind.RISK_CATEGORY_NO_LONGER_DISCLOSED
            else:
                kind = RiskChangeKind.RISK_DISCLOSURE_NOT_COMPARABLE

            changes.append(
                RiskChangeObservation(
                    kind=kind, category=category, previous_excerpts=tuple(sorted(earlier_texts or ())),
                    current_excerpts=tuple(sorted(later_texts or ())), accession_number=later_content.accession_number,
                    form_type=later_content.form_type, filed_at=later_content.filed_at,
                    source_reference=later_content.source_reference,
                )
            )

    categories = tuple(
        RiskCategorySummary(kind=kind, disclosures=tuple(disclosures_by_category[kind]))
        for kind in sorted(disclosures_by_category, key=lambda k: k.value)
    )

    return RiskFactorKnowledge(
        categories=categories, changes=tuple(changes), disclosures=tuple(all_disclosures),
        filings_considered=tuple(c.accession_number for c in usable),
    )
