"""Data model for one enrichment batch's progress -- see package
docstring for why this is deliberately one flat row shape, not a
job/job-item pair."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class EnrichmentProgressStatus(str, Enum):
    PENDING = "PENDING"
    ANALYZING = "ANALYZING"
    DONE = "DONE"
    DEFERRED = "DEFERRED"


@dataclass(frozen=True)
class EnrichmentProgressEntry:
    batch_id: str
    ticker: str
    company_name: str | None
    status: EnrichmentProgressStatus
    updated_at: datetime


@dataclass(frozen=True)
class EnrichmentProgressBatch:
    batch_id: str
    entries: tuple[EnrichmentProgressEntry, ...]

    @property
    def total(self) -> int:
        return len(self.entries)

    @property
    def done_count(self) -> int:
        return sum(1 for e in self.entries if e.status == EnrichmentProgressStatus.DONE)

    @property
    def currently_analyzing(self) -> str | None:
        for entry in self.entries:
            if entry.status == EnrichmentProgressStatus.ANALYZING:
                return entry.company_name or entry.ticker
        return None

    @property
    def complete(self) -> bool:
        return all(
            e.status in (EnrichmentProgressStatus.DONE, EnrichmentProgressStatus.DEFERRED)
            for e in self.entries
        )
