from typer.testing import CliRunner

from atlas.cli.main import app


def test_compare_cli_outputs_comparison_report():
    runner = CliRunner()

    result = runner.invoke(app, ["compare", "NVDA", "AMD", "MSFT"])

    assert result.exit_code == 0
    assert "Investment Comparison" in result.output
    assert "NVDA" in result.output
    assert "AMD" in result.output
    assert "MSFT" in result.output
    assert "Comparison Rating" in result.output
    assert "Full Reasoning" in result.output
