from dataclasses import dataclass
from enum import Enum

from atlas.analysis.engine import AtlasInvestmentEngine
from atlas.analysis.portfolio import Portfolio, PortfolioIntelligenceEngine
from atlas.analysis.watchlist import Watchlist
from atlas.capabilities.watchlist_intelligence import WatchlistIntelligenceEngine
from atlas.capabilities.watchlist_intelligence.models import (
    WatchlistIntelligenceInput,
    WatchlistItem as IntelligenceWatchlistItem,
)
from atlas.intelligence import IntelligenceContext, IntelligenceEngine, IntelligenceInput
from atlas.market import (
    MarketHealthEngine,
    MarketHealthReport,
    MarketIndicators,
    MarketRegimeEngine,
    MarketSnapshot,
)
from atlas.providers import CompanyDataProvider, MockCompanyAnalysisProvider
from atlas.risk import RiskAnalysis
from atlas.themes import ThemeEngine, ThemeInput


class ConversationIntent(str, Enum):
    COMPANY_ANALYSIS = "Company Analysis"
    PORTFOLIO_REVIEW = "Portfolio Review"
    WATCHLIST_REVIEW = "Watchlist Review"
    THEME_RESEARCH = "Theme Research"
    MARKET_HEALTH = "Market Health"
    MARKET_REGIME = "Market Regime"
    RISK_ASSESSMENT = "Risk Assessment"
    GENERAL_INVESTMENT_GUIDANCE = "General Investment Guidance"


@dataclass(frozen=True)
class ConversationInput:
    question: str
    provider: CompanyDataProvider | None = None
    ticker: str | None = None
    portfolio: Portfolio | None = None
    watchlist: Watchlist | None = None
    theme: str = "AI infrastructure"
    market_snapshot: MarketSnapshot | None = None
    market_health_report: MarketHealthReport | None = None
    risk_analysis: RiskAnalysis | None = None


@dataclass(frozen=True)
class ConversationResponse:
    intent: ConversationIntent
    short_answer: str
    supporting_reasoning: tuple[str, ...]
    engines_used: tuple[str, ...]
    confidence: int
    suggested_follow_up_questions: tuple[str, ...]


class IntentClassifier:
    def classify(self, question: str) -> ConversationIntent:
        normalized = _normalize(question)
        if _contains_any(normalized, ("portfolio", "holdings", "positions")):
            return ConversationIntent.PORTFOLIO_REVIEW
        if _contains_any(normalized, ("watchlist", "opportunities", "rank")):
            return ConversationIntent.WATCHLIST_REVIEW
        if _contains_any(normalized, ("theme", "themes", "bottleneck", "tailwind")):
            return ConversationIntent.THEME_RESEARCH
        if _contains_any(normalized, ("healthy", "health", "fragile", "stressed")):
            return ConversationIntent.MARKET_HEALTH
        if _contains_any(normalized, ("regime", "bull", "bear", "correction", "crisis")):
            return ConversationIntent.MARKET_REGIME
        if _contains_any(normalized, ("risk", "risky", "downside", "danger")):
            return ConversationIntent.RISK_ASSESSMENT
        if _contains_any(normalized, ("analyze", "analysis", "company", "nvidia", "nvda")):
            return ConversationIntent.COMPANY_ANALYSIS
        return ConversationIntent.GENERAL_INVESTMENT_GUIDANCE


class ConversationEngine:
    def __init__(
        self,
        intent_classifier: IntentClassifier | None = None,
        investment_engine: AtlasInvestmentEngine | None = None,
        portfolio_engine: PortfolioIntelligenceEngine | None = None,
        theme_engine: ThemeEngine | None = None,
        market_health_engine: MarketHealthEngine | None = None,
        market_regime_engine: MarketRegimeEngine | None = None,
        intelligence_engine: IntelligenceEngine | None = None,
    ) -> None:
        self.intent_classifier = intent_classifier or IntentClassifier()
        self.investment_engine = investment_engine or AtlasInvestmentEngine()
        self.portfolio_engine = portfolio_engine or PortfolioIntelligenceEngine()
        self.theme_engine = theme_engine or ThemeEngine()
        self.market_health_engine = market_health_engine or MarketHealthEngine()
        self.market_regime_engine = market_regime_engine or MarketRegimeEngine()
        self.intelligence_engine = intelligence_engine or IntelligenceEngine(
            investment_engine=self.investment_engine,
            portfolio_engine=self.portfolio_engine,
            theme_engine=self.theme_engine,
            market_health_engine=self.market_health_engine,
            market_regime_engine=self.market_regime_engine,
        )

    def answer(self, conversation_input: ConversationInput) -> ConversationResponse:
        intent = self.intent_classifier.classify(conversation_input.question)
        provider = conversation_input.provider or MockCompanyAnalysisProvider()
        ticker = _resolve_ticker(conversation_input.question, conversation_input.ticker)
        if intent == ConversationIntent.COMPANY_ANALYSIS:
            return self._answer_company_analysis(conversation_input, provider, ticker)
        if intent == ConversationIntent.PORTFOLIO_REVIEW:
            return self._answer_portfolio_review(conversation_input, provider, ticker)
        if intent == ConversationIntent.WATCHLIST_REVIEW:
            return self._answer_watchlist_review(conversation_input)
        if intent == ConversationIntent.THEME_RESEARCH:
            return self._answer_theme_research(conversation_input)
        if intent == ConversationIntent.MARKET_HEALTH:
            return self._answer_market_health(conversation_input)
        if intent == ConversationIntent.MARKET_REGIME:
            return self._answer_market_regime(conversation_input)
        if intent == ConversationIntent.RISK_ASSESSMENT:
            return self._answer_risk_assessment(conversation_input, provider, ticker)
        return self._answer_general_guidance(conversation_input, provider, ticker)

    def _answer_company_analysis(
        self,
        conversation_input: ConversationInput,
        provider: CompanyDataProvider,
        ticker: str,
    ) -> ConversationResponse:
        report = self.intelligence_engine.analyze(
            IntelligenceInput(
                ticker=ticker,
                provider=provider,
                context=IntelligenceContext(
                    portfolio=conversation_input.portfolio,
                    watchlist=conversation_input.watchlist,
                    theme=conversation_input.theme,
                    market_snapshot=conversation_input.market_snapshot,
                    market_health_report=conversation_input.market_health_report,
                    risk_analysis=conversation_input.risk_analysis,
                ),
            )
        )
        return ConversationResponse(
            intent=ConversationIntent.COMPANY_ANALYSIS,
            short_answer=(
                f"Atlas sees {ticker} as a company with Atlas Score "
                f"{report.investment_report.atlas_score}/100 and confidence "
                f"{report.confidence}/100."
            ),
            supporting_reasoning=(
                report.executive_summary,
                *report.company_positioning[:3],
                report.atlas_conclusion,
            ),
            engines_used=("Intelligence Engine", "Investment Engine", "Theme Engine"),
            confidence=report.confidence,
            suggested_follow_up_questions=_default_followups(),
        )

    def _answer_portfolio_review(
        self,
        conversation_input: ConversationInput,
        provider: CompanyDataProvider,
        ticker: str,
    ) -> ConversationResponse:
        if conversation_input.portfolio is None:
            return _needs_context_response(
                intent=ConversationIntent.PORTFOLIO_REVIEW,
                missing_context="portfolio",
                engines_used=("Portfolio Engine",),
            )
        analysis = self.portfolio_engine.analyze_ticker(
            portfolio=conversation_input.portfolio,
            ticker=ticker,
            provider=provider,
        )
        return ConversationResponse(
            intent=ConversationIntent.PORTFOLIO_REVIEW,
            short_answer=(
                f"Atlas measured portfolio fit for {ticker} at "
                f"{analysis.portfolio_score}/100."
            ),
            supporting_reasoning=(
                analysis.diversification_impact.reasoning,
                analysis.sector_concentration.reasoning,
                analysis.overlap_with_existing_holdings.reasoning,
                analysis.final_reasoning,
            ),
            engines_used=("Portfolio Engine",),
            confidence=78,
            suggested_follow_up_questions=(
                "Analyze portfolio impact",
                "Explain risks",
                "Show market health",
            ),
        )

    def _answer_watchlist_review(
        self,
        conversation_input: ConversationInput,
    ) -> ConversationResponse:
        if conversation_input.watchlist is None:
            return _needs_context_response(
                intent=ConversationIntent.WATCHLIST_REVIEW,
                missing_context="watchlist",
                engines_used=("Watchlist Intelligence Engine",),
            )
        watchlist = conversation_input.watchlist
        intelligence_input = WatchlistIntelligenceInput(
            name=watchlist.name,
            items=tuple(
                IntelligenceWatchlistItem(id=item.ticker.lower(), ticker=item.ticker)
                for item in watchlist.items
            ),
        )
        report = WatchlistIntelligenceEngine().analyze(intelligence_input)
        first_ticker = (
            report.companies_needing_attention[0].ticker
            if report.companies_needing_attention
            else report.observations[0].ticker
            if report.observations
            else "the watchlist"
        )
        first_detail = (
            report.companies_needing_attention[0].detail
            if report.companies_needing_attention
            else report.overview
        )
        evidence_context = (
            report.evidence_gaps[0].detail
            if report.evidence_gaps
            else report.observations[0].detail
            if report.observations
            else report.overview
        )
        research_context = (
            report.observations[0].detail
            if report.observations
            else report.overview
        )
        return ConversationResponse(
            intent=ConversationIntent.WATCHLIST_REVIEW,
            short_answer=(
                f"Atlas highlights {first_ticker} for research attention in "
                f"{report.name}."
            ),
            supporting_reasoning=(
                first_detail,
                evidence_context,
                research_context,
                report.overview,
            ),
            engines_used=("Watchlist Intelligence Engine",),
            confidence=70,
            suggested_follow_up_questions=(
                "Compare with AMD",
                "Show theme analysis",
                "Explain risks",
            ),
        )

    def _answer_theme_research(
        self,
        conversation_input: ConversationInput,
    ) -> ConversationResponse:
        theme = _resolve_theme(conversation_input.question, conversation_input.theme)
        analysis = self.theme_engine.analyze(ThemeInput(theme=theme))
        bottlenecks = ", ".join(item.name for item in analysis.key_bottlenecks[:4])
        risks = tuple(f"{risk.name}: {risk.why_it_matters}" for risk in analysis.key_risks[:3])
        return ConversationResponse(
            intent=ConversationIntent.THEME_RESEARCH,
            short_answer=(
                f"Atlas' {analysis.theme.value} research points first to bottlenecks "
                f"such as {bottlenecks}."
            ),
            supporting_reasoning=(
                analysis.summary,
                f"Affected industries: {', '.join(analysis.affected_industries)}.",
                *risks,
            ),
            engines_used=("Theme Engine",),
            confidence=analysis.confidence,
            suggested_follow_up_questions=(
                "Show theme analysis",
                "What should I monitor?",
                "Show market health",
            ),
        )

    def _answer_market_health(
        self,
        conversation_input: ConversationInput,
    ) -> ConversationResponse:
        report = conversation_input.market_health_report or self.market_health_engine.analyze()
        weakest_group = min(report.signal_groups, key=lambda group: group.score)
        return ConversationResponse(
            intent=ConversationIntent.MARKET_HEALTH,
            short_answer=(
                f"Atlas sees market health as {report.overall_market_health}, "
                f"with {report.overall_risk_level.lower()} overall risk."
            ),
            supporting_reasoning=(
                f"Overall score: {report.overall_score}/100.",
                f"Weakest signal group: {weakest_group.name} at {weakest_group.score}/100.",
                report.atlas_view,
            ),
            engines_used=("Market Health Engine",),
            confidence=76,
            suggested_follow_up_questions=(
                "Show market regime",
                "What should I monitor?",
                "Explain risks",
            ),
        )

    def _answer_market_regime(
        self,
        conversation_input: ConversationInput,
    ) -> ConversationResponse:
        analysis = self.market_regime_engine.analyze(
            conversation_input.market_snapshot or _default_market_snapshot()
        )
        return ConversationResponse(
            intent=ConversationIntent.MARKET_REGIME,
            short_answer=(
                f"Atlas classifies the market regime as {analysis.regime.value} "
                f"with confidence {analysis.confidence}/100."
            ),
            supporting_reasoning=(
                analysis.summary,
                *analysis.risks[:3],
                *analysis.suggested_investment_behaviour[:2],
            ),
            engines_used=("Market Regime Engine",),
            confidence=analysis.confidence,
            suggested_follow_up_questions=(
                "Show market health",
                "What should I monitor?",
                "Explain risks",
            ),
        )

    def _answer_risk_assessment(
        self,
        conversation_input: ConversationInput,
        provider: CompanyDataProvider,
        ticker: str,
    ) -> ConversationResponse:
        if conversation_input.risk_analysis is not None:
            risk = conversation_input.risk_analysis
            return ConversationResponse(
                intent=ConversationIntent.RISK_ASSESSMENT,
                short_answer=(
                    f"Atlas' risk sizing context for {risk.target_ticker} says: "
                    f"{risk.position_sizing.final_risk_recommendation}"
                ),
                supporting_reasoning=(
                    risk.position_sizing.liquidity_warning,
                    risk.position_sizing.concentration_warning,
                    risk.deployment_plan.market_regime_adjustment,
                    *risk.reasoning[:2],
                ),
                engines_used=("Risk Engine",),
                confidence=82,
                suggested_follow_up_questions=(
                    "Analyze portfolio impact",
                    "Show market health",
                    "What should I monitor?",
                ),
            )
        report = self.investment_engine.analyze_ticker(ticker, provider)
        return ConversationResponse(
            intent=ConversationIntent.RISK_ASSESSMENT,
            short_answer=f"Atlas gives {ticker} a risk profile score of {report.risk.score}/100.",
            supporting_reasoning=(
                report.risk.reasoning,
                f"Valuation context: {report.valuation.score}/100.",
                f"Confidence: {report.confidence}/100.",
            ),
            engines_used=("Investment Engine",),
            confidence=report.risk.confidence,
            suggested_follow_up_questions=(
                "Explain risks",
                "Analyze portfolio impact",
                "Show market health",
            ),
        )

    def _answer_general_guidance(
        self,
        conversation_input: ConversationInput,
        provider: CompanyDataProvider,
        ticker: str,
    ) -> ConversationResponse:
        report = self.intelligence_engine.analyze(
            IntelligenceInput(
                ticker=ticker,
                provider=provider,
                context=IntelligenceContext(
                    portfolio=conversation_input.portfolio,
                    watchlist=conversation_input.watchlist,
                    theme=conversation_input.theme,
                    market_snapshot=conversation_input.market_snapshot,
                    market_health_report=conversation_input.market_health_report,
                    risk_analysis=conversation_input.risk_analysis,
                ),
            )
        )
        return ConversationResponse(
            intent=ConversationIntent.GENERAL_INVESTMENT_GUIDANCE,
            short_answer=(
                "Atlas would focus on business quality, valuation, risk, portfolio "
                "fit, market context, and capital safety before forming a view."
            ),
            supporting_reasoning=(
                report.executive_summary,
                report.current_market_environment[1],
                report.atlas_conclusion,
                "This is deterministic research guidance, not personalized financial advice.",
            ),
            engines_used=("Intelligence Engine", "Market Health Engine", "Theme Engine"),
            confidence=report.confidence,
            suggested_follow_up_questions=_default_followups(),
        )


def render_conversation_response(response: ConversationResponse) -> str:
    return "\n".join(
        [
            "Atlas Conversation Response",
            "",
            f"Intent: {response.intent.value}",
            f"Confidence: {response.confidence}/100",
            "",
            "Short Answer",
            response.short_answer,
            "",
            "Supporting Reasoning",
            *_render_list(response.supporting_reasoning),
            "",
            "Engines Used",
            *_render_list(response.engines_used),
            "",
            "Suggested Follow-up Questions",
            *_render_list(response.suggested_follow_up_questions),
            "",
            "Research Framing",
            "This is deterministic research context, not personalized financial advice.",
        ]
    )


def _needs_context_response(
    intent: ConversationIntent,
    missing_context: str,
    engines_used: tuple[str, ...],
) -> ConversationResponse:
    return ConversationResponse(
        intent=intent,
        short_answer=f"Atlas needs {missing_context} context to answer this fully.",
        supporting_reasoning=(
            f"No {missing_context} was supplied with the question.",
            "Atlas should not invent missing facts.",
        ),
        engines_used=engines_used,
        confidence=52,
        suggested_follow_up_questions=_default_followups(),
    )


def _resolve_ticker(question: str, explicit_ticker: str | None) -> str:
    if explicit_ticker:
        return explicit_ticker.upper()
    normalized = _normalize(question)
    aliases = {
        "nvidia": "NVDA",
        "nvda": "NVDA",
        "amd": "AMD",
        "microsoft": "MSFT",
        "msft": "MSFT",
        "apple": "AAPL",
        "aapl": "AAPL",
        "evolution": "EVO",
        "evo": "EVO",
    }
    for alias, ticker in aliases.items():
        if alias in normalized:
            return ticker
    return "NVDA"


def _resolve_theme(question: str, default_theme: str) -> str:
    normalized = _normalize(question)
    if "semiconductor" in normalized:
        return "Semiconductors"
    if "energy" in normalized:
        return "Energy transition"
    if "electrification" in normalized:
        return "Electrification"
    if "healthcare" in normalized or "health care" in normalized:
        return "Healthcare innovation"
    if "ai" in normalized or "bottleneck" in normalized:
        return "AI infrastructure"
    return default_theme


def _default_market_snapshot() -> MarketSnapshot:
    return MarketSnapshot(
        indicators=MarketIndicators(
            sp500_drawdown=-0.04,
            nasdaq_drawdown=-0.07,
            vix=19,
            interest_rate_trend="stable",
            inflation_trend="stable",
        ),
        source="deterministic-placeholder",
    )


def _default_followups() -> tuple[str, ...]:
    return (
        "Compare with AMD",
        "Show theme analysis",
        "Analyze portfolio impact",
        "Show market health",
        "Explain risks",
    )


def _contains_any(value: str, candidates: tuple[str, ...]) -> bool:
    return any(candidate in value for candidate in candidates)


def _normalize(value: str) -> str:
    return value.strip().lower().replace("?", "").replace("-", " ")


def _render_list(items: tuple[str, ...]) -> list[str]:
    if not items:
        return ["- None"]
    return [f"- {item}" for item in items]
