from dataclasses import dataclass
from enum import Enum


class ChangeType(str, Enum):
    """Supported deterministic historical change categories."""

    PORTFOLIO_POSITION_ADDED = "portfolio_position_added"
    PORTFOLIO_POSITION_REMOVED = "portfolio_position_removed"
    PORTFOLIO_WEIGHT_CHANGED = "portfolio_weight_changed"
    WATCHLIST_ITEM_ADDED = "watchlist_item_added"
    WATCHLIST_ITEM_REMOVED = "watchlist_item_removed"
    QUALITY_SCORE_CHANGED = "quality_score_changed"
    RISK_SCORE_CHANGED = "risk_score_changed"


class ChangeSeverity(str, Enum):
    """Severity level for structural historical changes."""

    INFO = "info"
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"


@dataclass(frozen=True)
class HistoricalChange:
    """Single deterministic change between two historical snapshots."""

    change_type: ChangeType
    subject: str
    previous_value: object
    current_value: object
    severity: ChangeSeverity


@dataclass(frozen=True)
class HistoricalComparison:
    """Structured comparison result for two snapshots."""

    previous_timestamp: str
    current_timestamp: str
    changes: tuple[HistoricalChange, ...]

    @property
    def has_changes(self) -> bool:
        """Return whether the comparison contains any changes."""

        return bool(self.changes)
