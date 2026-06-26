from typer.testing import CliRunner

from atlas.cli.main import app


def test_report_cli_outputs_investment_report():
    runner = CliRunner()

    result = runner.invoke(app, ["report", "NVDA"])

    assert result.exit_code == 0
    assert "Investment Report" in result.output
    assert "Company: NVIDIA (NVDA)" in result.output
    assert "Quality" in result.output
    assert "Atlas Score" in result.output
    assert "Overall Recommendation: Buy" in result.output
    assert "Financial Strength" in result.output
    assert "Reasoning" in result.output


def test_analyze_cli_outputs_company_report_alias():
    runner = CliRunner()

    result = runner.invoke(app, ["analyze", "NVDA"])

    assert result.exit_code == 0
    assert "Investment Report" in result.output
    assert "Company: NVIDIA (NVDA)" in result.output


def test_analyze_cli_exits_for_unknown_ticker():
    runner = CliRunner()

    result = runner.invoke(app, ["analyze", "TSM"])

    assert result.exit_code == 1
    assert "Analysis failed" in result.output
    assert "No mock company analysis available for TSM" in result.output


def test_report_cli_exits_for_unknown_ticker():
    runner = CliRunner()

    result = runner.invoke(app, ["report", "TSM"])

    assert result.exit_code == 1
    assert "Report failed" in result.output
    assert "No mock company analysis available for TSM" in result.output
