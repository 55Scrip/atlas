from dataclasses import dataclass
from enum import Enum

from atlas.decision.comparison import ComparisonResult
from atlas.analysis.engine import InvestmentReport
from atlas.analysis.memory import MemoryComparison
from atlas.analysis.portfolio import PortfolioAnalysis
from atlas.capabilities.watchlist_intelligence.models import WatchlistIntelligenceReport


class DecisionAction(str, Enum):
    BUY = "Buy"
    HOLD = "Hold"
    REDUCE = "Reduce"
    AVOID = "Avoid"
    WATCH = "Watch"
    LEARN_MORE = "Learn More"


@dataclass(frozen=True)
class DecisionResult:
    ticker: str
    action: DecisionAction
    has_enough_information: bool
    decision_quality: int
    portfolio_fit: int
    capital_allocation_quality: int
    confidence: int
    reasoning: str
    next_best_action: str
    what_could_change_my_mind: str
    uncertainty: str
    investment_report: InvestmentReport
    portfolio_analysis: PortfolioAnalysis | None = None
    comparison_result: ComparisonResult | None = None
    watchlist_intelligence: WatchlistIntelligenceReport | None = None
    memory_comparison: MemoryComparison | None = None
