"""Tests for PortfolioIntelligenceCapability engine (Sprint 113 + Sprint 114).

Sprint 113 coverage:
- engine importability and architecture boundary
- all 7 dimensions: diversification, sector, country, market_cap, overlap, quality, risk
- aggregate fit score determinism
- schema gap fallback dimensions return neutral/partial scores with notes
- no provider imports, no legacy portfolio imports
- existing legacy callers unchanged

Sprint 114 coverage:
- Holding enriched fields (quality_score, risk_score, market_cap) enable full parity
- quality_impact full parity (delta from weighted portfolio average)
- risk_impact full parity (delta from weighted portfolio average)
- market_cap_concentration full parity (pro forma mega-cap weight)
- diversification_impact full parity (mega-cap component included)
- adapter carries enriched fields from legacy PortfolioPosition
- conversation engine uses capability for portfolio review path
"""

from __future__ import annotations

import pytest
from atlas.capabilities.portfolio_intelligence import (
    PortfolioFitDimension,
    PortfolioFitInput,
    PortfolioFitResult,
    PortfolioIntelligenceCapability,
)
from atlas.shared.entities import Holding, Portfolio


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_holding(
    ticker: str,
    sector: str = "Technology",
    country: str = "United States",
    weight: float = 0.10,
) -> Holding:
    return Holding(
        company_id=ticker.lower(),
        ticker=ticker,
        weight=weight,
        sector=sector,
        country=country,
    )


def _make_portfolio(*holdings: Holding) -> Portfolio:
    return Portfolio(id="test", name="Test Portfolio", holdings=tuple(holdings))


def _make_fit_input(
    ticker: str = "NVDA",
    sector: str = "Semiconductors",
    country: str = "United States",
    market_cap: float = 3_000_000_000_000.0,
    quality_score: int = 85,
    risk_score: int = 72,
) -> PortfolioFitInput:
    return PortfolioFitInput(
        ticker=ticker,
        company="Test Company",
        sector=sector,
        country=country,
        market_cap=market_cap,
        quality_score=quality_score,
        risk_score=risk_score,
    )


_ENGINE = PortfolioIntelligenceCapability()


# ---------------------------------------------------------------------------
# Importability and architecture boundary
# ---------------------------------------------------------------------------

def test_engine_is_importable() -> None:
    from atlas.capabilities.portfolio_intelligence import PortfolioIntelligenceCapability
    assert PortfolioIntelligenceCapability is not None


def test_engine_does_not_import_legacy_portfolio() -> None:
    import ast
    from pathlib import Path
    engine_file = Path(__file__).resolve().parent.parent / "atlas" / "capabilities" / "portfolio_intelligence" / "engine.py"
    tree = ast.parse(engine_file.read_text())
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            assert "atlas.analysis.portfolio" not in node.module, (
                "engine.py must not import from atlas.analysis.portfolio"
            )


def test_engine_does_not_import_providers() -> None:
    import ast
    from pathlib import Path
    engine_file = Path(__file__).resolve().parent.parent / "atlas" / "capabilities" / "portfolio_intelligence" / "engine.py"
    tree = ast.parse(engine_file.read_text())
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            assert not node.module.startswith("atlas.providers"), (
                "engine.py must not import from atlas.providers"
            )


def test_engine_does_not_import_cli() -> None:
    import ast
    from pathlib import Path
    engine_file = Path(__file__).resolve().parent.parent / "atlas" / "capabilities" / "portfolio_intelligence" / "engine.py"
    tree = ast.parse(engine_file.read_text())
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            assert not node.module.startswith("atlas.cli"), (
                "engine.py must not import from atlas.cli"
            )


# ---------------------------------------------------------------------------
# Engine returns correct types
# ---------------------------------------------------------------------------

def test_analyze_returns_portfolio_fit_result() -> None:
    portfolio = _make_portfolio(_make_holding("AAPL"))
    result = _ENGINE.analyze(portfolio, _make_fit_input())
    assert isinstance(result, PortfolioFitResult)


def test_result_fields_are_portfolio_fit_dimensions() -> None:
    portfolio = _make_portfolio(_make_holding("AAPL"))
    result = _ENGINE.analyze(portfolio, _make_fit_input())
    assert isinstance(result.diversification, PortfolioFitDimension)
    assert isinstance(result.sector_concentration, PortfolioFitDimension)
    assert isinstance(result.country_concentration, PortfolioFitDimension)
    assert isinstance(result.market_cap_concentration, PortfolioFitDimension)
    assert isinstance(result.overlap, PortfolioFitDimension)
    assert isinstance(result.quality_impact, PortfolioFitDimension)
    assert isinstance(result.risk_impact, PortfolioFitDimension)


def test_result_ticker_and_company_match_input() -> None:
    portfolio = _make_portfolio(_make_holding("AAPL"))
    fit_input = PortfolioFitInput(
        ticker="MSFT", company="Microsoft", sector="Software",
        country="United States", market_cap=3_000_000_000_000.0,
        quality_score=88, risk_score=65,
    )
    result = _ENGINE.analyze(portfolio, fit_input)
    assert result.ticker == "MSFT"
    assert result.company == "Microsoft"


def test_fit_score_is_clamped_between_0_and_100() -> None:
    portfolio = _make_portfolio(
        _make_holding("A", sector="Semiconductors", country="United States", weight=0.40),
        _make_holding("B", sector="Semiconductors", country="United States", weight=0.40),
    )
    fit_input = _make_fit_input(sector="Semiconductors", country="United States")
    result = _ENGINE.analyze(portfolio, fit_input)
    assert 0 <= result.fit_score <= 100


# ---------------------------------------------------------------------------
# Sector concentration
# ---------------------------------------------------------------------------

def test_sector_concentration_low_when_no_existing_sector_exposure() -> None:
    portfolio = _make_portfolio(_make_holding("AAPL", sector="Consumer Electronics"))
    fit_input = _make_fit_input(sector="Semiconductors")
    result = _ENGINE.analyze(portfolio, fit_input)
    # pro_forma = 0 + 0.05 = 0.05 < 0.25 preferred → score = 90
    assert result.sector_concentration.score == 90


def test_sector_concentration_penalized_when_concentrated() -> None:
    # 40% in Semiconductors already, adding 5% → 45% > preferred 25%
    portfolio = _make_portfolio(
        _make_holding("A", sector="Semiconductors", weight=0.20),
        _make_holding("B", sector="Semiconductors", weight=0.20),
    )
    fit_input = _make_fit_input(sector="Semiconductors")
    result = _ENGINE.analyze(portfolio, fit_input)
    assert result.sector_concentration.score < 90


def test_sector_concentration_at_hard_limit_returns_25() -> None:
    # 35% existing + 5% target = 40% == hard_limit → score = 25
    portfolio = _make_portfolio(
        _make_holding("A", sector="Semiconductors", weight=0.35),
    )
    fit_input = _make_fit_input(sector="Semiconductors", market_cap=100_000_000.0)
    result = _ENGINE.analyze(portfolio, fit_input)
    assert result.sector_concentration.score == 25


# ---------------------------------------------------------------------------
# Country concentration
# ---------------------------------------------------------------------------

def test_country_concentration_low_when_no_existing_country_exposure() -> None:
    portfolio = _make_portfolio(_make_holding("TSM", country="Taiwan"))
    fit_input = _make_fit_input(country="United States")
    result = _ENGINE.analyze(portfolio, fit_input)
    assert result.country_concentration.score == 90


def test_country_concentration_penalized_when_concentrated() -> None:
    # 60% US + 5% → 65% == hard_limit
    portfolio = _make_portfolio(
        _make_holding("A", country="United States", weight=0.30),
        _make_holding("B", country="United States", weight=0.30),
    )
    fit_input = _make_fit_input(country="United States")
    result = _ENGINE.analyze(portfolio, fit_input)
    assert result.country_concentration.score < 90


# ---------------------------------------------------------------------------
# Overlap with existing holdings
# ---------------------------------------------------------------------------

def test_overlap_score_is_low_for_direct_ticker_match() -> None:
    portfolio = _make_portfolio(_make_holding("NVDA", sector="Semiconductors"))
    fit_input = _make_fit_input(ticker="NVDA", sector="Semiconductors")
    result = _ENGINE.analyze(portfolio, fit_input)
    assert result.overlap.score == 20


def test_overlap_score_penalized_for_sector_overlap() -> None:
    portfolio = _make_portfolio(
        _make_holding("AMD", sector="Semiconductors"),
    )
    fit_input = _make_fit_input(ticker="NVDA", sector="Semiconductors")
    result = _ENGINE.analyze(portfolio, fit_input)
    # 1 sector overlap → 80 - 10 = 70
    assert result.overlap.score == 70


def test_overlap_score_high_when_no_overlap() -> None:
    portfolio = _make_portfolio(_make_holding("AAPL", sector="Consumer Electronics"))
    fit_input = _make_fit_input(ticker="NVDA", sector="Semiconductors")
    result = _ENGINE.analyze(portfolio, fit_input)
    assert result.overlap.score == 92


def test_overlap_score_decreases_with_more_sector_matches() -> None:
    portfolio = _make_portfolio(
        _make_holding("AMD", sector="Semiconductors"),
        _make_holding("INTC", sector="Semiconductors"),
        _make_holding("QCOM", sector="Semiconductors"),
    )
    fit_input = _make_fit_input(ticker="NVDA", sector="Semiconductors")
    result = _ENGINE.analyze(portfolio, fit_input)
    # 3 sector overlaps → 80 - 30 = 50, clamped
    assert result.overlap.score == 50


# ---------------------------------------------------------------------------
# Schema gap dimensions — neutral/partial scores
# ---------------------------------------------------------------------------

def test_market_cap_concentration_returns_neutral_with_note_when_no_market_cap_data() -> None:
    # Holding without market_cap (default None) — fallback neutral score
    portfolio = _make_portfolio(_make_holding("AAPL"))
    fit_input = _make_fit_input()
    result = _ENGINE.analyze(portfolio, fit_input)
    assert result.market_cap_concentration.score == 50
    assert "unavailable" in result.market_cap_concentration.note.lower()


def test_quality_impact_returns_partial_score_based_on_target_when_no_holding_data() -> None:
    # Holding without quality_score (default None) — fallback formula
    portfolio = _make_portfolio(_make_holding("AAPL"))
    # quality_score=90 → 50 + (90-50)*0.5 = 70
    fit_input = _make_fit_input(quality_score=90)
    result = _ENGINE.analyze(portfolio, fit_input)
    assert result.quality_impact.score == 70
    assert "unavailable" in result.quality_impact.note.lower()


def test_risk_impact_returns_partial_score_based_on_target_when_no_holding_data() -> None:
    # Holding without risk_score (default None) — fallback formula
    portfolio = _make_portfolio(_make_holding("AAPL"))
    # risk_score=80 → 50 + (80-50)*0.5 = 65
    fit_input = _make_fit_input(risk_score=80)
    result = _ENGINE.analyze(portfolio, fit_input)
    assert result.risk_impact.score == 65
    assert "unavailable" in result.risk_impact.note.lower()


def test_mega_cap_target_noted_in_market_cap_dimension() -> None:
    portfolio = _make_portfolio(_make_holding("AAPL"))
    fit_input = _make_fit_input(market_cap=3_000_000_000_000.0)
    result = _ENGINE.analyze(portfolio, fit_input)
    assert "mega-cap" in result.market_cap_concentration.note.lower()


def test_small_cap_target_noted_in_market_cap_dimension() -> None:
    portfolio = _make_portfolio(_make_holding("AAPL"))
    fit_input = _make_fit_input(market_cap=1_000_000_000.0)
    result = _ENGINE.analyze(portfolio, fit_input)
    assert "non-mega-cap" in result.market_cap_concentration.note.lower()


# ---------------------------------------------------------------------------
# Diversification
# ---------------------------------------------------------------------------

def test_diversification_penalized_by_sector_exposure() -> None:
    portfolio = _make_portfolio(
        _make_holding("A", sector="Semiconductors", country="Germany", weight=0.50),
    )
    # 50% semiconductor exposure → raw = 100 - round(0.50*55 + 0*25) = 100-28 = 72
    fit_input = _make_fit_input(sector="Semiconductors", country="France")
    result = _ENGINE.analyze(portfolio, fit_input)
    assert result.diversification.score < 100


def test_diversification_note_mentions_missing_market_cap_when_no_holding_data() -> None:
    # Holding without market_cap (default None) — mega-cap component note
    portfolio = _make_portfolio(_make_holding("AAPL"))
    result = _ENGINE.analyze(portfolio, _make_fit_input())
    assert "unavailable" in result.diversification.note.lower()


# ---------------------------------------------------------------------------
# Aggregate score determinism
# ---------------------------------------------------------------------------

def test_fit_score_is_deterministic() -> None:
    portfolio = _make_portfolio(
        _make_holding("AAPL", sector="Consumer Electronics", country="United States", weight=0.15),
        _make_holding("MSFT", sector="Software", country="United States", weight=0.15),
    )
    fit_input = _make_fit_input()
    r1 = _ENGINE.analyze(portfolio, fit_input)
    r2 = _ENGINE.analyze(portfolio, fit_input)
    assert r1 == r2


def test_empty_portfolio_produces_valid_result() -> None:
    portfolio = _make_portfolio()
    fit_input = _make_fit_input()
    result = _ENGINE.analyze(portfolio, fit_input)
    assert isinstance(result, PortfolioFitResult)
    assert 0 <= result.fit_score <= 100


def test_target_weight_normalization_handles_percent_format() -> None:
    portfolio = _make_portfolio(_make_holding("AAPL"))
    fit_input = _make_fit_input()
    r_decimal = _ENGINE.analyze(portfolio, fit_input, target_weight=0.05)
    r_percent = _ENGINE.analyze(portfolio, fit_input, target_weight=5.0)
    assert r_decimal == r_percent


# ---------------------------------------------------------------------------
# Existing legacy callers unchanged
# ---------------------------------------------------------------------------

def test_sprint128_portfolio_intelligence_engine_not_importable() -> None:
    """Sprint 128: PortfolioIntelligenceEngine deleted — import must raise ImportError."""
    import pytest
    with pytest.raises(ImportError):
        from atlas.analysis.portfolio import PortfolioIntelligenceEngine  # noqa: F401


def test_sprint132_portfolio_analysis_deleted() -> None:
    """Sprint 132: PortfolioAnalysis deleted — must NOT be importable from atlas.analysis.portfolio."""
    import pytest
    with pytest.raises(ImportError):
        from atlas.analysis.portfolio import PortfolioAnalysis  # noqa: F401


def test_sprint133_company_portfolio_profile_not_importable() -> None:
    """Sprint 133: CompanyPortfolioProfile deleted — must NOT be importable."""
    import pytest
    with pytest.raises(ImportError):
        from atlas.analysis.portfolio import CompanyPortfolioProfile  # noqa: F401


# ---------------------------------------------------------------------------
# Sprint 114: Enriched Holding fields enable full parity
# ---------------------------------------------------------------------------

def _make_enriched_holding(
    ticker: str,
    sector: str = "Technology",
    country: str = "United States",
    weight: float = 0.10,
    quality_score: int = 80,
    risk_score: int = 60,
    market_cap: float = 2_000_000_000_000.0,
) -> Holding:
    return Holding(
        company_id=ticker.lower(),
        ticker=ticker,
        weight=weight,
        sector=sector,
        country=country,
        quality_score=quality_score,
        risk_score=risk_score,
        market_cap=market_cap,
    )


def test_holding_accepts_enriched_fields() -> None:
    h = _make_enriched_holding("AAPL")
    assert h.quality_score == 80
    assert h.risk_score == 60
    assert h.market_cap == 2_000_000_000_000.0


def test_holding_enriched_fields_default_to_none() -> None:
    h = _make_holding("AAPL")
    assert h.quality_score is None
    assert h.risk_score is None
    assert h.market_cap is None


def test_quality_impact_full_parity_when_enriched_holdings_present() -> None:
    # Existing holding: quality_score=80, weight=1.0
    # Target: quality_score=90, target_weight=0.05
    # current_quality = 80.0
    # pro_forma = 80.0 * 0.95 + 90 * 0.05 = 76.0 + 4.5 = 80.5
    # score = 50 + (80.5 - 80.0) * 4 = 50 + 2 = 52
    portfolio = _make_portfolio(
        _make_enriched_holding("AAPL", quality_score=80, weight=1.0)
    )
    fit_input = _make_fit_input(quality_score=90)
    result = _ENGINE.analyze(portfolio, fit_input)
    assert result.quality_impact.score == 52
    assert "improve" in result.quality_impact.note.lower()
    assert "80.0/100" in result.quality_impact.note


def test_quality_impact_diluting_when_target_lower_than_portfolio() -> None:
    portfolio = _make_portfolio(
        _make_enriched_holding("AAPL", quality_score=90, weight=1.0)
    )
    fit_input = _make_fit_input(quality_score=60)
    result = _ENGINE.analyze(portfolio, fit_input)
    assert result.quality_impact.score < 50
    assert "dilute" in result.quality_impact.note.lower()


def test_risk_impact_full_parity_when_enriched_holdings_present() -> None:
    # Existing holding: risk_score=60, weight=1.0
    # Target: risk_score=80, target_weight=0.05
    # current_risk = 60.0
    # pro_forma = 60.0 * 0.95 + 80 * 0.05 = 57.0 + 4.0 = 61.0
    # score = 50 + (61.0 - 60.0) * 4 = 50 + 4 = 54
    portfolio = _make_portfolio(
        _make_enriched_holding("AAPL", risk_score=60, weight=1.0)
    )
    fit_input = _make_fit_input(risk_score=80)
    result = _ENGINE.analyze(portfolio, fit_input)
    assert result.risk_impact.score == 54
    assert "improve" in result.risk_impact.note.lower()


def test_market_cap_concentration_full_parity_with_enriched_holdings() -> None:
    # Existing holding is mega-cap (market_cap >= 500B), weight=0.30
    # Target is also mega-cap, target_weight=0.05
    # pro_forma = 0.30 + 0.05 = 0.35 == preferred_limit → score = 90
    portfolio = _make_portfolio(
        _make_enriched_holding("AAPL", market_cap=3_000_000_000_000.0, weight=0.30)
    )
    fit_input = _make_fit_input(market_cap=3_000_000_000_000.0)
    result = _ENGINE.analyze(portfolio, fit_input)
    assert result.market_cap_concentration.score == 90
    assert "pro forma" in result.market_cap_concentration.note.lower()


def test_market_cap_concentration_penalized_when_above_preferred_limit() -> None:
    # 40% existing mega-cap + 5% = 45% > 35% preferred
    portfolio = _make_portfolio(
        _make_enriched_holding("A", market_cap=3_000_000_000_000.0, weight=0.40)
    )
    fit_input = _make_fit_input(market_cap=2_000_000_000_000.0)
    result = _ENGINE.analyze(portfolio, fit_input)
    assert result.market_cap_concentration.score < 90


def test_diversification_includes_mega_cap_component_when_enriched() -> None:
    # 50% mega-cap exposure → mega-cap penalty of 0.50 * 20 = 10
    # sector exposure = 0 (different sector), country exposure = 0 (different country)
    # raw = 100 - round(0 + 0 + 0.50 * 20) = 100 - 10 = 90
    portfolio = _make_portfolio(
        _make_enriched_holding(
            "AAPL", sector="Consumer Electronics", country="Germany",
            market_cap=3_000_000_000_000.0, weight=0.50,
        )
    )
    fit_input = _make_fit_input(sector="Semiconductors", country="France")
    result = _ENGINE.analyze(portfolio, fit_input)
    assert result.diversification.score == 90
    assert "unavailable" not in result.diversification.note.lower()


# ---------------------------------------------------------------------------
# Sprint 114: Adapter carries enriched fields
# ---------------------------------------------------------------------------

def test_adapter_carries_quality_score_risk_score_market_cap() -> None:
    from atlas.adapters.portfolio import Portfolio as LegacyPortfolio, PortfolioPosition
    from atlas.adapters.portfolio import legacy_portfolio_to_domain_portfolio

    legacy = LegacyPortfolio(
        positions=(
            PortfolioPosition(
                ticker="MSFT",
                company="Microsoft",
                sector="Software",
                country="United States",
                market_cap=3_400_000_000_000,
                weight=0.20,
                quality_score=90,
                risk_score=78,
            ),
        )
    )
    domain = legacy_portfolio_to_domain_portfolio(legacy)
    assert len(domain.holdings) == 1
    h = domain.holdings[0]
    assert h.quality_score == 90
    assert h.risk_score == 78
    assert h.market_cap == 3_400_000_000_000.0
    assert h.weight == 0.20


def test_adapter_output_enables_full_parity_engine() -> None:
    from atlas.adapters.portfolio import Portfolio as LegacyPortfolio, PortfolioPosition
    from atlas.adapters.portfolio import legacy_portfolio_to_domain_portfolio

    legacy = LegacyPortfolio(
        positions=(
            PortfolioPosition(
                ticker="MSFT",
                company="Microsoft",
                sector="Software",
                country="United States",
                market_cap=3_400_000_000_000,
                weight=0.20,
                quality_score=90,
                risk_score=78,
            ),
        )
    )
    domain = legacy_portfolio_to_domain_portfolio(legacy)
    fit_input = _make_fit_input(ticker="NVDA", sector="Semiconductors")
    result = _ENGINE.analyze(domain, fit_input)
    # With enriched holdings, quality/risk notes should NOT say "unavailable"
    assert "unavailable" not in result.quality_impact.note.lower()
    assert "unavailable" not in result.risk_impact.note.lower()
    assert isinstance(result.fit_score, int)
    assert 0 <= result.fit_score <= 100


# ---------------------------------------------------------------------------
# Sprint 114: Conversation engine uses capability
# ---------------------------------------------------------------------------

def test_conversation_engine_portfolio_review_uses_portfolio_fit_capability() -> None:
    import ast
    from pathlib import Path
    conv_file = Path(__file__).resolve().parent.parent / "atlas" / "conversation" / "engine.py"
    source = conv_file.read_text()
    tree = ast.parse(source)
    capability_imported = False
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            if "portfolio_intelligence" in node.module:
                for alias in (node.names or []):
                    if alias.name == "PortfolioIntelligenceCapability":
                        capability_imported = True
    assert capability_imported, "conversation/engine.py must import PortfolioIntelligenceCapability"


def test_conversation_engine_portfolio_review_returns_fit_score() -> None:
    from atlas.adapters.portfolio import Portfolio as LegacyPortfolio, PortfolioPosition
    from atlas.conversation import ConversationEngine, ConversationInput, ConversationIntent
    from atlas.providers import MockCompanyAnalysisProvider

    portfolio = LegacyPortfolio(
        positions=(
            PortfolioPosition(
                ticker="MSFT",
                company="Microsoft",
                sector="Software",
                country="United States",
                market_cap=3_400_000_000_000,
                weight=0.20,
                quality_score=90,
                risk_score=78,
            ),
        )
    )
    response = ConversationEngine().answer(
        ConversationInput(
            question="Review my portfolio",
            provider=MockCompanyAnalysisProvider(),
            portfolio=portfolio,
            ticker="NVDA",
        )
    )
    assert response.intent == ConversationIntent.PORTFOLIO_REVIEW
    assert "/100" in response.short_answer
    assert "portfolio fit" in response.short_answer.lower()
    # Supporting reasoning should have 4 dimension notes + summary
    assert len(response.supporting_reasoning) == 4
    # No buy/sell/recommendation language
    for text in (response.short_answer, *response.supporting_reasoning):
        assert "strong add" not in text.lower()
        assert "buy" not in text.lower()
        assert "sell" not in text.lower()


def test_conversation_portfolio_review_no_recommendation_language() -> None:
    from atlas.adapters.portfolio import Portfolio as LegacyPortfolio, PortfolioPosition
    from atlas.conversation import ConversationEngine, ConversationInput
    from atlas.providers import MockCompanyAnalysisProvider

    portfolio = LegacyPortfolio(
        positions=(
            PortfolioPosition(
                ticker="MSFT", company="Microsoft", sector="Software",
                country="United States", market_cap=3_400_000_000_000,
                weight=0.20, quality_score=90, risk_score=78,
            ),
        )
    )
    response = ConversationEngine().answer(
        ConversationInput(
            question="Review my portfolio",
            provider=MockCompanyAnalysisProvider(),
            portfolio=portfolio,
            ticker="NVDA",
        )
    )
    forbidden = ["strong add", "add", "neutral", "reduce", "avoid", "buy", "sell"]
    for term in forbidden:
        assert term not in response.short_answer.lower(), f"Forbidden term '{term}' in short_answer"
