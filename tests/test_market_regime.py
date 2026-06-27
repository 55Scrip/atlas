import json

from typer.testing import CliRunner

from atlas.cli.main import app
from atlas.market import (
    MarketIndicators,
    MarketRegime,
    MarketRegimeEngine,
    MarketSnapshot,
    render_market_regime,
)


def _analyze(
    sp500_drawdown: float,
    nasdaq_drawdown: float,
    vix: float,
    interest_rate_trend: str = "stable",
    inflation_trend: str = "stable",
):
    snapshot = MarketSnapshot(
        indicators=MarketIndicators(
            sp500_drawdown=sp500_drawdown,
            nasdaq_drawdown=nasdaq_drawdown,
            vix=vix,
            interest_rate_trend=interest_rate_trend,
            inflation_trend=inflation_trend,
        )
    )
    return MarketRegimeEngine().analyze(snapshot)


def test_market_regime_engine_classifies_bull_market():
    analysis = _analyze(
        sp500_drawdown=-0.02,
        nasdaq_drawdown=-0.03,
        vix=15,
        interest_rate_trend="falling",
        inflation_trend="easing",
    )

    assert analysis.regime == MarketRegime.BULL
    assert "Continue investing." in analysis.suggested_investment_behaviour
    assert "Avoid chasing momentum." in analysis.suggested_investment_behaviour


def test_market_regime_engine_classifies_neutral_market():
    analysis = _analyze(
        sp500_drawdown=-0.04,
        nasdaq_drawdown=-0.07,
        vix=19,
    )

    assert analysis.regime == MarketRegime.NEUTRAL
    assert "Invest normally." in analysis.suggested_investment_behaviour


def test_market_regime_engine_classifies_correction():
    analysis = _analyze(
        sp500_drawdown=-0.12,
        nasdaq_drawdown=-0.16,
        vix=26,
    )

    assert analysis.regime == MarketRegime.CORRECTION
    assert "Build watchlists." in analysis.suggested_investment_behaviour
    assert "Prepare capital for opportunities." in analysis.suggested_investment_behaviour


def test_market_regime_engine_classifies_bear_market():
    analysis = _analyze(
        sp500_drawdown=-0.22,
        nasdaq_drawdown=-0.31,
        vix=36,
    )

    assert analysis.regime == MarketRegime.BEAR
    assert "Buy gradually." in analysis.suggested_investment_behaviour
    assert "Focus on profitable, high-quality companies." in (
        analysis.suggested_investment_behaviour
    )


def test_market_regime_engine_classifies_crisis():
    analysis = _analyze(
        sp500_drawdown=-0.36,
        nasdaq_drawdown=-0.46,
        vix=52,
    )

    assert analysis.regime == MarketRegime.CRISIS
    assert "Never panic sell." in analysis.suggested_investment_behaviour
    assert "Preserve liquidity." in analysis.suggested_investment_behaviour


def test_market_snapshot_loads_nested_json_and_normalizes_percent_drawdowns(tmp_path):
    path = tmp_path / "market.json"
    path.write_text(
        json.dumps(
            {
                "as_of": "2026-06-27",
                "source": "mock",
                "indicators": {
                    "sp500_drawdown": 12,
                    "nasdaq_drawdown": 16,
                    "vix": 26,
                    "interest_rate_trend": "stable",
                    "inflation_trend": "stable",
                },
            }
        ),
        encoding="utf-8",
    )

    snapshot = MarketSnapshot.from_json_file(path)
    analysis = MarketRegimeEngine().analyze(snapshot)

    assert snapshot.as_of == "2026-06-27"
    assert snapshot.source == "mock"
    assert snapshot.indicators.sp500_drawdown == -0.12
    assert analysis.regime == MarketRegime.CORRECTION


def test_market_snapshot_reports_missing_required_fields(tmp_path):
    path = tmp_path / "market.json"
    path.write_text(json.dumps({"sp500_drawdown": 0.02}), encoding="utf-8")

    try:
        MarketSnapshot.from_json_file(path)
    except ValueError as exc:
        assert "missing required field" in str(exc)
    else:
        raise AssertionError("MarketSnapshot should reject incomplete market JSON")


def test_market_regime_renderer_includes_required_sections():
    analysis = _analyze(
        sp500_drawdown=-0.22,
        nasdaq_drawdown=-0.31,
        vix=36,
    )

    rendered = render_market_regime(analysis)

    assert "Current market regime" in rendered
    assert "Confidence" in rendered
    assert "Key Indicators" in rendered
    assert "Opportunities" in rendered
    assert "Risks" in rendered
    assert "Suggested Investment Behaviour" in rendered


def test_market_cli_outputs_regime_report(tmp_path):
    path = tmp_path / "market.json"
    path.write_text(
        json.dumps(
            {
                "sp500_drawdown": 0.36,
                "nasdaq_drawdown": 0.46,
                "vix": 52,
                "interest_rate_trend": "rising",
                "inflation_trend": "rising",
            }
        ),
        encoding="utf-8",
    )
    runner = CliRunner()

    result = runner.invoke(app, ["market", "analyze", str(path)])

    assert result.exit_code == 0
    assert "Market Regime Analysis" in result.output
    assert "Current market regime: Crisis" in result.output
    assert "Never panic sell." in result.output
