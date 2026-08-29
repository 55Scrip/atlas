"""Industry Intelligence models (Calibration Phase 7).

Every enum below is a closed vocabulary, mirroring the exact discipline
`atlas.alpha.canonical_security.value_objects.SecurityType` already
established for the identical problem shape (translate a raw,
unvalidated provider string into a small, closed, decision-usable
vocabulary, falling through to an honest catch-all rather than `None`
or a crash). Never a numeric score, never inferred from company size,
never asserted as a fact about a specific company merely because it is
common in that company's industry -- see `docs/Calibration-Phase-7
-Industry-Intelligence.md` Part D for the full "attach, never override"
design rationale.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

__all__ = [
    "IndustryFamily",
    "IndustryClassification",
    "IndustrySupportLevel",
    "ValuationApplicability",
    "LeverageInterpretation",
    "IndustryValuationNote",
    "IndustryLeverageNote",
    "IndustryMoatContext",
    "IndustryContext",
]


class IndustryFamily(str, Enum):
    """18 economically meaningful families, derived from the brief's
    own suggested list and cross-checked against the real Alpha-Vantage
    sector/industry strings Atlas actually ingests (see the design
    doc's own Part A/B). `UNCLASSIFIED` is a real, mapped string this
    table does not recognize; `UNKNOWN` is the honest "no
    `CompanyProfile` at all" floor -- these are deliberately different
    (one is a translation-table gap, the other is a data-coverage gap)."""

    SOFTWARE = "software"
    SEMICONDUCTORS = "semiconductors"
    INTERNET_PLATFORMS = "internet_platforms"
    BANKS = "banks"
    INSURANCE = "insurance"
    ASSET_MANAGERS = "asset_managers"
    INDUSTRIALS = "industrials"
    CONSUMER_STAPLES = "consumer_staples"
    CONSUMER_DISCRETIONARY = "consumer_discretionary"
    LUXURY = "luxury"
    PHARMA_BIOTECH = "pharma_biotech"
    MEDICAL_DEVICES = "medical_devices"
    UTILITIES = "utilities"
    ENERGY = "energy"
    REAL_ESTATE = "real_estate"
    TELECOM = "telecom"
    PAYMENTS = "payments"
    HOLDING_COMPANIES = "holding_companies"
    UNCLASSIFIED = "unclassified"
    UNKNOWN = "unknown"


class IndustrySupportLevel(str, Enum):
    """Phase 14's own coverage-honesty requirement -- generated from
    the real rule tables in `valuation_context.py`/`capital_allocation
    _context.py`, never asserted independently of them (see
    `support.py`'s own module docstring), so this can never silently
    drift out of sync with what Atlas can actually do."""

    STRONG = "strong"
    PARTIAL = "partial"
    UNSUPPORTED = "unsupported"


@dataclass(frozen=True)
class IndustryClassification:
    family: IndustryFamily
    raw_sector: str | None
    raw_industry: str | None


class ValuationApplicability(str, Enum):
    """Phase 8. Never a claim that Atlas *has* a better method --
    `POOR_FIT` is always paired with an honest disclosure, never a
    fabricated alternative valuation (the brief's own explicit
    instruction)."""

    APPROPRIATE = "appropriate"
    USEFUL_WITH_CAVEATS = "useful_with_caveats"
    POOR_FIT = "poor_fit"
    UNKNOWN = "unknown"


class LeverageInterpretation(str, Enum):
    """Phase 7/9. Never changes the underlying `BusinessCategoryStatus`/
    `RiskStatus` it annotates -- see `capital_allocation_context.py`'s
    own module docstring for why this is additive context, never a
    replacement judgment."""

    STRUCTURALLY_NORMAL = "structurally_normal"
    METRIC_NOT_APPROPRIATE = "metric_not_appropriate"
    GENERIC_INTERPRETATION_APPLIES = "generic_interpretation_applies"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class IndustryValuationNote:
    applicability: ValuationApplicability
    reasoning: str


@dataclass(frozen=True)
class IndustryLeverageNote:
    interpretation: LeverageInterpretation
    reasoning: str


@dataclass(frozen=True)
class IndustryMoatContext:
    """Phase 6. Names which qualitative moat-evidence *type* this
    family's own economics would make most relevant -- never a claim
    that the specific company being analyzed has it. Empty
    `relevant_evidence_types` for families with no single dominant
    moat-evidence type in the brief's own economics research."""

    relevant_evidence_types: tuple[str, ...]
    reasoning: str


@dataclass(frozen=True)
class IndustryContext:
    classification: IndustryClassification
    support_level: IndustrySupportLevel
    valuation_note: IndustryValuationNote
    leverage_note: IndustryLeverageNote
    moat_context: IndustryMoatContext
