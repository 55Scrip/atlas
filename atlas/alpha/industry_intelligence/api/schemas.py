"""HTTP response schemas for the Industry Intelligence API. Wire format
is camelCase via the shared Core `CamelModel` (ADR-004), matching every
other Alpha schema module. Every enum is sent as its `.value` string.
"""
from __future__ import annotations

from atlas.alpha.industry_intelligence.models import (
    IndustryClassification,
    IndustryContext,
    IndustryLeverageNote,
    IndustryMoatContext,
    IndustryValuationNote,
)
from atlas.core.infrastructure.api.serialization import CamelModel

__all__ = [
    "IndustryClassificationView",
    "IndustryValuationNoteView",
    "IndustryLeverageNoteView",
    "IndustryMoatContextView",
    "IndustryContextView",
]


class IndustryClassificationView(CamelModel):
    family: str
    raw_sector: str | None
    raw_industry: str | None

    @classmethod
    def from_domain(cls, classification: IndustryClassification) -> "IndustryClassificationView":
        return cls(
            family=classification.family.value,
            raw_sector=classification.raw_sector,
            raw_industry=classification.raw_industry,
        )


class IndustryValuationNoteView(CamelModel):
    applicability: str
    reasoning: str

    @classmethod
    def from_domain(cls, note: IndustryValuationNote) -> "IndustryValuationNoteView":
        return cls(applicability=note.applicability.value, reasoning=note.reasoning)


class IndustryLeverageNoteView(CamelModel):
    interpretation: str
    reasoning: str

    @classmethod
    def from_domain(cls, note: IndustryLeverageNote) -> "IndustryLeverageNoteView":
        return cls(interpretation=note.interpretation.value, reasoning=note.reasoning)


class IndustryMoatContextView(CamelModel):
    relevant_evidence_types: list[str]
    reasoning: str

    @classmethod
    def from_domain(cls, context: IndustryMoatContext) -> "IndustryMoatContextView":
        return cls(relevant_evidence_types=list(context.relevant_evidence_types), reasoning=context.reasoning)


class IndustryContextView(CamelModel):
    classification: IndustryClassificationView
    support_level: str
    valuation_note: IndustryValuationNoteView
    leverage_note: IndustryLeverageNoteView
    moat_context: IndustryMoatContextView

    @classmethod
    def from_domain(cls, context: IndustryContext) -> "IndustryContextView":
        return cls(
            classification=IndustryClassificationView.from_domain(context.classification),
            support_level=context.support_level.value,
            valuation_note=IndustryValuationNoteView.from_domain(context.valuation_note),
            leverage_note=IndustryLeverageNoteView.from_domain(context.leverage_note),
            moat_context=IndustryMoatContextView.from_domain(context.moat_context),
        )
