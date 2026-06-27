from typer.testing import CliRunner

from atlas.cli.main import app
from atlas.economics import (
    EconomicSignal,
    EconomicSignalGroup,
    EconomicSignalsEngine,
    render_economic_signal_analysis,
)


def test_economic_signals_engine_returns_required_groups():
    analysis = EconomicSignalsEngine().analyze()
    group_names = {group.name for group in analysis.signal_groups}

    assert group_names == {
        "Credit Markets",
        "Liquidity",
        "Interest Rates",
        "Volatility",
        "Macro",
        "Market Breadth",
    }
    assert analysis.overall_economic_health == "Fragile"
    assert analysis.overall_risk_score == 42


def test_credit_markets_group_contains_required_signals():
    analysis = EconomicSignalsEngine().analyze()
    credit_group = next(
        group for group in analysis.signal_groups if group.name == "Credit Markets"
    )
    signal_names = {signal.name for signal in credit_group.signals}

    assert "High Yield spreads" in signal_names
    assert "Investment Grade spreads" in signal_names
    assert "Default rates" in signal_names
    assert "Bank lending standards" in signal_names
    assert credit_group.status == "Watchful"


def test_economic_signals_engine_accepts_replaceable_signal_groups():
    groups = (
        EconomicSignalGroup(
            name="Credit Markets",
            score=88,
            status="Supportive",
            signals=(
                EconomicSignal(
                    name="High Yield spreads",
                    current_state="Tight",
                    direction="Improving",
                    importance=90,
                    confidence=80,
                    why_it_matters="Credit stress is low.",
                    score=88,
                ),
            ),
            interpretation="Credit is supportive.",
        ),
    )

    analysis = EconomicSignalsEngine().analyze(groups)

    assert analysis.overall_economic_health == "Healthy"
    assert analysis.overall_risk_score == 12
    assert analysis.strongest_positive_signals[0].name == "High Yield spreads"


def test_economic_signal_renderer_includes_required_sections():
    analysis = EconomicSignalsEngine().analyze()

    rendered = render_economic_signal_analysis(analysis)

    assert "Overall Economic Health" in rendered
    assert "Overall Risk Score" in rendered
    assert "Strongest Positive Signals" in rendered
    assert "Strongest Negative Signals" in rendered
    assert "What Atlas Is Watching Most Closely" in rendered
    assert "What Would Improve The Outlook" in rendered
    assert "What Would Worsen The Outlook" in rendered
    assert "not forecasting or buy/sell advice" in rendered


def test_economics_cli_outputs_analysis():
    runner = CliRunner()

    result = runner.invoke(app, ["economics", "analyze"])

    assert result.exit_code == 0
    assert "Economic Signals Analysis" in result.output
    assert "Credit Markets" in result.output
    assert "High Yield spreads" in result.output
