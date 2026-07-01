"""Sprint 85: Legacy atlas daily brief command retired.

Tests for the legacy `atlas.daily_brief` engine were removed in Sprint 77
when the engine itself was deleted. The CLI command stub was retired in Sprint 85.

The Blueprint-aligned Daily Brief is tested in test_daily_brief_capability.py.
"""

from typer.testing import CliRunner

from atlas.cli.main import app


def test_daily_brief_cli_command_is_retired():
    # Sprint 85: atlas daily brief command body removed — no longer a valid command
    runner = CliRunner()
    result = runner.invoke(app, ["daily", "brief"])
    assert result.exit_code != 0
