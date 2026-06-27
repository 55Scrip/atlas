from typer.testing import CliRunner

from atlas.cli.main import app
from atlas.market import (
    MarketHealthEngine,
    MarketSignal,
    MarketSignalGroup,
    render_market_health,
)


def test_market_health_engine_returns_required_signal_groups():
    report = MarketHealthEngine().analyze()
    group_names = {group.name for group in report.signal_groups}

    assert group_names == {
        "Credit",
        "Liquidity",
        "Macro",
        "Volatility",
        "Market Breadth",
    }
    assert report.overall_market_health == "Fragile"
    assert report.overall_risk_level == "Elevated"
    assert report.overall_score == 61


def test_market_health_credit_group_includes_required_placeholders():
    report = MarketHealthEngine().analyze()
    credit_group = next(group for group in report.signal_groups if group.name == "Credit")
    signal_names = {signal.name.lower() for signal in credit_group.key_signals}

    assert "high yield spreads" in signal_names
    assert "investment grade spreads" in signal_names
    assert "default rates" in signal_names
    assert "bank lending standards" in signal_names
    assert credit_group.status == "Watchful"
    assert credit_group.score == 68


def test_market_health_engine_accepts_replaceable_signal_groups():
    groups = (
        MarketSignalGroup(
            name="Credit",
            status="Strong",
            score=90,
            key_signals=(
                MarketSignal(
                    name="High yield spreads",
                    status="Calm",
                    value="Tight",
                    interpretation="Credit risk is low.",
                ),
            ),
            interpretation="Credit is strong.",
            monitoring_items=("Credit spreads",),
            what_would_improve=("Defaults fall further.",),
            what_would_worsen=("Spreads widen.",),
        ),
    )

    report = MarketHealthEngine().analyze(groups)

    assert report.overall_market_health == "Healthy"
    assert report.overall_risk_level == "Low"
    assert report.overall_score == 90


def test_market_health_renderer_includes_required_sections():
    report = MarketHealthEngine().analyze()

    rendered = render_market_health(report)

    assert "Overall Market Health" in rendered
    assert "Overall Risk Level" in rendered
    assert "Credit Conditions" in rendered
    assert "Liquidity Conditions" in rendered
    assert "Macro Conditions" in rendered
    assert "Volatility" in rendered
    assert "Market Breadth" in rendered
    assert "Atlas View" in rendered
    assert "What Could Change Atlas' View" in rendered
    assert "not investment advice" in rendered


def test_market_health_cli_outputs_report():
    runner = CliRunner()

    result = runner.invoke(app, ["market", "health"])

    assert result.exit_code == 0
    assert "Market Health Report" in result.output
    assert "Overall Market Health: Fragile" in result.output
    assert "Credit Conditions" in result.output
    assert "high yield spreads" in result.output.lower()
