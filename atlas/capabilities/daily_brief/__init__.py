"""Daily Brief capability.

Organises existing Atlas domain and capability structures into a calm,
deterministic daily overview.

Daily Brief answers:
  - What deserves attention?
  - What remains unresolved?
  - What can safely wait?
  - What research should continue?

It does not generate recommendations, fetch news, call market data, or
invent events. If no meaningful input is supplied it returns a calm
no-developments result.
"""

from atlas.capabilities.daily_brief.engine import DailyBriefCapability
from atlas.capabilities.daily_brief.input_builder import build_daily_brief_input
from atlas.capabilities.daily_brief.models import (
    DailyBriefEvidenceLink,
    DailyBriefInput,
    DailyBriefItem,
    DailyBriefObservation,
    DailyBriefPriority,
    DailyBriefReport,
    DailyBriefSection,
    DailyBriefSummary,
    DailyBriefUnknown,
)

__all__ = [
    "DailyBriefCapability",
    "build_daily_brief_input",
    "DailyBriefEvidenceLink",
    "DailyBriefInput",
    "DailyBriefItem",
    "DailyBriefObservation",
    "DailyBriefPriority",
    "DailyBriefReport",
    "DailyBriefSection",
    "DailyBriefSummary",
    "DailyBriefUnknown",
]
