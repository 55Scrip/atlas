"""The one-shot scheduled-composition command.

This is the only way a batch runs today, so these tests cover the guard it
shares with every other `atlas.dev` command, the modes that must compose
nothing, and the report an operator reads to decide whether the run was
sound.
"""
from __future__ import annotations

import pytest

from atlas.alpha.scheduled_composition.service import (
    CaseCompositionOutcome,
    ScheduledCompositionResult,
)
from atlas.dev.compose_scheduled_cases import main
from atlas.dev.guard import NotDevelopmentEnvironmentError


class _FakeService:
    def __init__(self, scope=(("c1", "AAA"),), result=None) -> None:
        self._scope = scope
        self._result = result
        self.runs: list[object] = []

    def scope(self):
        return self._scope

    def run(self, *, scope=None):
        self.runs.append(scope)
        return self._result


def _result(**kwargs):
    defaults = dict(
        started_at=__import__("datetime").datetime(2026, 9, 16, 12, 0, tzinfo=__import__("datetime").timezone.utc),
        duration_seconds=0.5,
        attempted=1,
        succeeded=1,
        failed=0,
        snapshots_written=1,
        snapshots_deduplicated=0,
        outcomes=(CaseCompositionOutcome(case_id="c1", ticker="AAA", composed=True, snapshot_written=True),),
    )
    defaults.update(kwargs)
    return ScheduledCompositionResult(**defaults)


@pytest.fixture
def wired(monkeypatch):
    """Replace the wiring factory so the command's own behaviour is under
    test rather than the whole composition object graph."""
    holder: dict[str, _FakeService] = {}

    def install(service):
        holder["service"] = service
        monkeypatch.setattr(
            "atlas.dev.compose_scheduled_cases.build_scheduled_composition_service",
            lambda engine: service,
        )
        return service

    return install


class TestProductionGuard:
    def test_refuses_when_atlas_env_is_production(self, monkeypatch, tmp_path):
        monkeypatch.setenv("ATLAS_ENV", "production")
        with pytest.raises(NotDevelopmentEnvironmentError):
            main(["--database", str(tmp_path / "atlas.db")])

    def test_refuses_before_touching_any_database(self, monkeypatch, tmp_path):
        database = tmp_path / "atlas.db"
        monkeypatch.setenv("ATLAS_ENV", "production")
        with pytest.raises(NotDevelopmentEnvironmentError):
            main(["--database", str(database)])
        assert not database.exists()


class TestModesThatComposeNothing:
    def test_list_scope_composes_nothing(self, monkeypatch, tmp_path, wired, capsys):
        monkeypatch.setenv("ATLAS_ENV", "development")
        service = wired(_FakeService(scope=(("c1", "AAA"), ("c2", "BBB"))))
        assert main(["--database", str(tmp_path / "a.db"), "--list-scope"]) == 0
        assert service.runs == []
        out = capsys.readouterr().out
        assert "c1" in out and "c2" in out
        assert "nothing composed, nothing written" in out

    def test_dry_run_composes_nothing(self, monkeypatch, tmp_path, wired, capsys):
        monkeypatch.setenv("ATLAS_ENV", "development")
        service = wired(_FakeService())
        assert main(["--database", str(tmp_path / "a.db"), "--dry-run"]) == 0
        assert service.runs == []
        assert "nothing composed" in capsys.readouterr().out


class TestReport:
    def test_reports_every_number_an_operator_needs(self, monkeypatch, tmp_path, wired, capsys):
        """Scope, attempted, succeeded, failed, written, deduplicated,
        duration -- and that no provider was called."""
        monkeypatch.setenv("ATLAS_ENV", "development")
        wired(_FakeService(result=_result()))
        assert main(["--database", str(tmp_path / "a.db")]) == 0
        out = capsys.readouterr().out
        for expected in (
            "scope           : 1 Cases",
            "attempted       : 1",
            "succeeded       : 1",
            "failed          : 0",
            "snapshots written: 1",
            "unchanged (deduplicated): 0",
            "duration        : 0.5s",
            "provider calls  : 0",
        ):
            assert expected in out

    def test_it_composes_the_scope_it_reported(self, monkeypatch, tmp_path, wired, capsys):
        """The report says "scope: N Cases" and then composes. Reading
        membership a second time would let the batch compose a different
        set than the one it just printed -- the app can add a Watchlist
        entry between the two reads -- so the operator's record of what ran
        would be wrong."""
        monkeypatch.setenv("ATLAS_ENV", "development")
        scope = (("c1", "AAA"), ("c2", "BBB"))
        service = wired(_FakeService(scope=scope, result=_result()))
        main(["--database", str(tmp_path / "a.db")])
        assert service.runs == [scope]

    def test_states_that_no_recurring_trigger_is_wired(self, monkeypatch, tmp_path, wired, capsys):
        """The command is the only way a batch runs; saying so stops a
        reader assuming Atlas is already composing on its own."""
        monkeypatch.setenv("ATLAS_ENV", "development")
        wired(_FakeService())
        main(["--database", str(tmp_path / "a.db"), "--dry-run"])
        assert "no recurring trigger is wired" in capsys.readouterr().out

    def test_reports_the_configured_cadence(self, monkeypatch, tmp_path, wired, capsys):
        monkeypatch.setenv("ATLAS_ENV", "development")
        monkeypatch.setenv("ATLAS_SCHEDULED_COMPOSITION_INTERVAL_SECONDS", "3600")
        wired(_FakeService())
        main(["--database", str(tmp_path / "a.db"), "--dry-run"])
        assert "cadence         : 3600s" in capsys.readouterr().out

    def test_names_each_case_whose_record_moved(self, monkeypatch, tmp_path, wired, capsys):
        monkeypatch.setenv("ATLAS_ENV", "development")
        wired(_FakeService(result=_result()))
        main(["--database", str(tmp_path / "a.db")])
        assert "recorded  AAA" in capsys.readouterr().out

    def test_an_unchanged_batch_names_nothing_and_succeeds(self, monkeypatch, tmp_path, wired, capsys):
        """The expected steady state: everything composed, nothing moved."""
        monkeypatch.setenv("ATLAS_ENV", "development")
        wired(_FakeService(result=_result(
            snapshots_written=0, snapshots_deduplicated=1,
            outcomes=(CaseCompositionOutcome(case_id="c1", ticker="AAA", composed=True, snapshot_written=False),),
        )))
        assert main(["--database", str(tmp_path / "a.db")]) == 0
        captured = capsys.readouterr()
        assert "recorded" not in captured.out
        assert "snapshots written: 0" in captured.out


class TestFailureReporting:
    def test_a_partial_batch_exits_non_zero(self, monkeypatch, tmp_path, wired, capsys):
        """A batch that lost a Case must not look like a clean run to
        whatever invoked it."""
        monkeypatch.setenv("ATLAS_ENV", "development")
        wired(_FakeService(result=_result(
            attempted=2, succeeded=1, failed=1,
            outcomes=(
                CaseCompositionOutcome(case_id="c1", ticker="AAA", composed=True, snapshot_written=True),
                CaseCompositionOutcome(case_id="c2", ticker="BBB", composed=False, snapshot_written=False,
                                       error="RuntimeError: boom"),
            ),
        )))
        assert main(["--database", str(tmp_path / "a.db")]) == 3
        captured = capsys.readouterr()
        assert "FAILED    BBB" in captured.err
        assert "RuntimeError: boom" in captured.err
        assert "1 Case(s) did not compose -- the rest did" in captured.err

    def test_the_successful_cases_are_still_reported(self, monkeypatch, tmp_path, wired, capsys):
        monkeypatch.setenv("ATLAS_ENV", "development")
        wired(_FakeService(result=_result(
            attempted=2, succeeded=1, failed=1,
            outcomes=(
                CaseCompositionOutcome(case_id="c1", ticker="AAA", composed=True, snapshot_written=True),
                CaseCompositionOutcome(case_id="c2", ticker="BBB", composed=False, snapshot_written=False,
                                       error="RuntimeError: boom"),
            ),
        )))
        main(["--database", str(tmp_path / "a.db")])
        assert "recorded  AAA" in capsys.readouterr().out
