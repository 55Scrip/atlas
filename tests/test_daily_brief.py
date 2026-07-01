"""Sprint 77: Legacy DailyBriefEngine removed.

Tests for the legacy `atlas.daily_brief` engine were removed in Sprint 77
when the engine itself was deleted. The CLI deprecation test is retained here
as the canonical record of `atlas daily brief` command behavior.

The Blueprint-aligned Daily Brief is tested in test_daily_brief_capability.py.
"""

import json

from typer.testing import CliRunner

from atlas.cli.main import app


def test_daily_brief_cli_outputs_clean_text(tmp_path):
    portfolio_path = tmp_path / "portfolio.json"
    portfolio_path.write_text(
        json.dumps(
            {
                "positions": [
                    {
                        "ticker": "NVDA",
                        "company": "NVIDIA",
                        "sector": "Semiconductors",
                        "country": "United States",
                        "market_cap": 3_300_000_000_000,
                        "weight": 0.42,
                        "quality_score": 92,
                        "risk_score": 77,
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    runner = CliRunner()

    result = runner.invoke(app, ["daily", "brief", "--portfolio", str(portfolio_path)])

    # Sprint 76: atlas daily brief is deprecated — expect deprecation message, not brief content
    assert result.exit_code == 0
    assert "deprecated" in result.output.lower()
    assert "daily summary" in result.output.lower()
