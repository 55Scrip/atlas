from typer.testing import CliRunner

from atlas.cli.main import app
from atlas.themes import Theme, ThemeEngine, ThemeInput, render_theme_analysis


def test_theme_engine_supports_initial_theme_templates():
    engine = ThemeEngine()

    assert engine.supported_themes() == (
        Theme.AI_INFRASTRUCTURE,
        Theme.ENERGY_TRANSITION,
        Theme.ELECTRIFICATION,
        Theme.SEMICONDUCTORS,
        Theme.HEALTHCARE_INNOVATION,
    )


def test_theme_engine_analyzes_ai_infrastructure_bottlenecks():
    analysis = ThemeEngine().analyze(ThemeInput(theme="AI infrastructure"))
    bottlenecks = {bottleneck.name for bottleneck in analysis.key_bottlenecks}

    assert analysis.theme == Theme.AI_INFRASTRUCTURE
    assert "electricity supply" in {name.lower() for name in bottlenecks}
    assert "grid capacity" in {name.lower() for name in bottlenecks}
    assert "data center construction" in {name.lower() for name in bottlenecks}
    assert "cooling" in {name.lower() for name in bottlenecks}
    assert "transformers" in {name.lower() for name in bottlenecks}
    assert "hbm memory" in {name.lower() for name in bottlenecks}
    assert "advanced packaging" in {name.lower() for name in bottlenecks}
    assert "Utilities" in analysis.affected_industries
    assert "Copper" in analysis.related_commodities
    assert analysis.confidence == 88


def test_theme_engine_supports_aliases():
    analysis = ThemeEngine().analyze("semiconductor")

    assert analysis.theme == Theme.SEMICONDUCTORS


def test_theme_engine_rejects_unsupported_themes():
    try:
        ThemeEngine().analyze("space tourism")
    except ValueError as exc:
        assert "Unsupported theme" in str(exc)
        assert "AI infrastructure" in str(exc)
    else:
        raise AssertionError("ThemeEngine should reject unsupported themes")


def test_theme_renderer_includes_required_sections():
    analysis = ThemeEngine().analyze("energy transition")

    rendered = render_theme_analysis(analysis)

    assert "Theme Summary" in rendered
    assert "Key Bottlenecks" in rendered
    assert "Affected Industries" in rendered
    assert "Potential Beneficiaries" in rendered
    assert "Related Assets" in rendered
    assert "Second-Order Winners" in rendered
    assert "Key Risks" in rendered
    assert "What Atlas Is Monitoring" in rendered
    assert "What Would Change Atlas' View" in rendered
    assert "not personalized financial recommendations" in rendered


def test_theme_cli_outputs_ai_infrastructure_report():
    runner = CliRunner()

    result = runner.invoke(app, ["theme", "analyze", "AI infrastructure"])

    assert result.exit_code == 0
    assert "Theme Analysis" in result.output
    assert "Theme: AI infrastructure" in result.output
    assert "electricity supply" in result.output.lower()
    assert "HBM memory" in result.output
    assert "advanced packaging" in result.output


def test_theme_cli_reports_unknown_theme_without_crashing():
    runner = CliRunner()

    result = runner.invoke(app, ["theme", "analyze", "space tourism"])

    assert result.exit_code == 1
    assert "Theme analysis failed" in result.output
    assert "Unsupported theme" in result.output
