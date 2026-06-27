from typer.testing import CliRunner

from atlas.cli.main import app
from atlas.profile import (
    InvestmentGoal,
    InvestorProfileEngine,
    PortfolioPurpose,
    RiskCapacity,
    RiskPreference,
    RiskTolerance,
    TimeHorizon,
    render_investor_profile,
)


def test_default_profile_generates_investor_context():
    profile = InvestorProfileEngine().create_default_profile()
    context = InvestorProfileEngine().investor_context(profile)

    assert profile.name == "Atlas Investor"
    assert context.investment_goals == ("Wealth accumulation",)
    assert context.portfolio_purpose == "Core Portfolio"
    assert context.risk_profile == "Balanced"
    assert "short-term liquidity" in context.capital_safety_context
    assert any("Time horizon: 10+ years" in item for item in context.reasoning_context)


def test_profile_can_be_created_and_updated_deterministically():
    engine = InvestorProfileEngine()
    profile = engine.create_profile(
        name="Research Account",
        investment_goals=(InvestmentGoal.FINANCIAL_INDEPENDENCE,),
        portfolio_purpose=PortfolioPurpose.GROWTH_PORTFOLIO,
        risk_preference=RiskPreference.GROWTH,
        risk_tolerance=RiskTolerance.BALANCED,
        risk_capacity=RiskCapacity.HIGH,
        time_horizon=TimeHorizon.LONG,
    )

    updated = engine.update_profile(
        profile,
        risk_preference=RiskPreference.AGGRESSIVE,
        risk_capacity=RiskCapacity.LOW,
        time_horizon=TimeHorizon.SHORT,
    )
    context = engine.investor_context(updated)

    assert updated.risk_preference == RiskPreference.AGGRESSIVE
    assert updated.risk_capacity == RiskCapacity.LOW
    assert context.risk_profile == "Aggressive"
    assert context.capital_safety_context.startswith("Short horizon")


def test_profile_save_and_load_round_trips_json(tmp_path):
    engine = InvestorProfileEngine()
    profile = engine.create_default_profile(name="Long-Term Investor")
    path = tmp_path / "nested" / "atlas_profile.json"

    engine.save_profile(profile, path)
    loaded = engine.load_profile(path)

    assert loaded == profile


def test_profile_requires_at_least_one_investment_goal():
    engine = InvestorProfileEngine()

    try:
        engine.create_profile(
            name="Empty",
            investment_goals=(),
            portfolio_purpose=PortfolioPurpose.CORE_PORTFOLIO,
            risk_preference=RiskPreference.BALANCED,
            risk_tolerance=RiskTolerance.BALANCED,
            risk_capacity=RiskCapacity.MEDIUM,
            time_horizon=TimeHorizon.LONG,
        )
    except ValueError as exc:
        assert "at least one investment goal" in str(exc)
    else:
        raise AssertionError("Expected ValueError for an empty investment goal set.")


def test_profile_renderer_includes_context_without_advice():
    profile = InvestorProfileEngine().create_default_profile()

    rendered = render_investor_profile(profile)

    assert "Investor Profile" in rendered
    assert "Capital Safety Context" in rendered
    assert "Investor Context" in rendered
    assert "Research Framing" in rendered
    assert "not financial advice" in rendered


def test_profile_cli_create_show_and_update(tmp_path):
    runner = CliRunner()
    path = tmp_path / "profile.json"

    created = runner.invoke(
        app,
        [
            "profile",
            "create",
            "--path",
            str(path),
            "--name",
            "Axel",
            "--goal",
            "Financial Independence",
            "--risk-profile",
            "Growth",
        ],
    )

    assert created.exit_code == 0
    assert path.exists()
    assert "Financial Independence" in created.output
    assert "Growth" in created.output

    shown = runner.invoke(app, ["profile", "show", "--path", str(path)])

    assert shown.exit_code == 0
    assert "Investor Profile" in shown.output
    assert "Axel" in shown.output

    updated = runner.invoke(
        app,
        [
            "profile",
            "update",
            "--path",
            str(path),
            "--risk-capacity",
            "High",
            "--time-horizon",
            "<3 years",
        ],
    )

    assert updated.exit_code == 0
    assert "Risk Capacity: High" in updated.output
    assert "Short horizon" in updated.output
