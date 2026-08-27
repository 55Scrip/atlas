"""Tests for `atlas.dev.reset_user`.

Covers the sprint's own required scenarios: idempotence, the production
guard, correct scoping (single-tenant wholesale clear), per-domain
reset (portfolio/watchlist/Daily Brief/decision journal/cases), dry-run
(no writes), and preservation of shared company intelligence.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine, insert, select
from sqlalchemy.engine import Engine
from sqlalchemy.pool import StaticPool

from atlas.alpha.business_data_refresh.quota_table import (
    alpha_vantage_daily_call_count_table,
    create_alpha_vantage_daily_call_count_table,
)
from atlas.alpha.business_data_refresh.table import business_record_table, create_business_record_table
# Deliberately not importing atlas.alpha.canonical_security directly --
# tests/unit/alpha/canonical_security/test_integration_safety.py enforces
# that only canonical_security's own package/tests, the Resolution
# Service, and the Identity Gate may do so. reset_user.py itself never
# touches those tables (see its own module docstring), so there's
# nothing of that module's for this test file to exercise anyway.
from atlas.alpha.daily_brief_change_log.case_baseline import (
    create_daily_brief_case_baseline_table,
    daily_brief_case_baseline_table,
)
from atlas.alpha.daily_brief_change_log.table import (
    create_daily_brief_change_log_table,
    daily_brief_change_log_table,
)
from atlas.alpha.daily_brief_view_state.table import (
    create_daily_brief_view_state_table,
    daily_brief_view_state_table,
)
from atlas.alpha.decision_memory.table import (
    create_decision_memory_snapshot_table,
    decision_memory_snapshot_table,
)
from atlas.alpha.monitoring.table import create_monitoring_result_table, monitoring_result_table
from atlas.alpha.portfolio.models import AlphaHolding, AlphaPortfolioState, AlphaPreferences, EntryMode
from atlas.alpha.portfolio.store import AlphaPortfolioStore
from atlas.alpha.portfolio.table import create_alpha_portfolio_state_table
from atlas.alpha.watchlist.models import AlphaWatchlistEntry
from atlas.alpha.watchlist.store import AlphaWatchlistStore
from atlas.alpha.watchlist.table import create_alpha_watchlist_entry_table
from atlas.core.application.investor_identity.composition import resolve_investor_identity
from atlas.core.infrastructure.persistence.case.table import cases_table, create_case_table
from atlas.core.infrastructure.persistence.decision.table import create_decision_table, decisions_table
from atlas.core.infrastructure.persistence.observation.table import create_observation_table, observations_table
from atlas.core.infrastructure.persistence.outcome.table import create_outcome_table, outcomes_table
from atlas.dev.guard import NotDevelopmentEnvironmentError
from atlas.dev.reset_user import reset_development_user

_NOW = datetime(2026, 8, 27, tzinfo=timezone.utc)


@pytest.fixture
def engine() -> Engine:
    return create_engine(
        "sqlite:///:memory:",
        future=True,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )


def _seed_portfolio_and_watchlist(engine: Engine) -> None:
    create_alpha_portfolio_state_table(engine)
    create_alpha_watchlist_entry_table(engine)
    AlphaPortfolioStore(engine).replace(
        AlphaPortfolioState(
            established_at=_NOW,
            updated_at=_NOW,
            entry_mode=EntryMode.IMPORTED,
            holdings=(
                AlphaHolding(ticker="AAPL", weight_percent=60.0, case_id="case-aapl"),
                AlphaHolding(ticker="MSFT", weight_percent=40.0, case_id="case-msft"),
            ),
            cash_weight_percent=None,
            cash_value_absolute=None,
            preferences=AlphaPreferences(notes=None),
        )
    )
    watchlist_store = AlphaWatchlistStore(engine)
    watchlist_store.add(AlphaWatchlistEntry(ticker="NVDA", case_id="case-nvda", added_at=_NOW))
    watchlist_store.add(AlphaWatchlistEntry(ticker="AMD", case_id="case-amd", added_at=_NOW))
    watchlist_store.remove("AMD", removed_at=_NOW)  # soft-removed -- must still be hard-cleared


def _seed_cases(engine: Engine) -> None:
    create_case_table(engine)
    with engine.begin() as connection:
        for case_id in ("case-aapl", "case-msft", "case-nvda", "case-amd"):
            connection.execute(insert(cases_table).values(case_id=case_id, recorded_at=_NOW.isoformat()))


def _seed_decision_journal(engine: Engine) -> None:
    create_decision_table(engine)
    create_outcome_table(engine)
    create_observation_table(engine)
    with engine.begin() as connection:
        connection.execute(
            insert(decisions_table).values(
                id="decision-1",
                case_id="case-aapl",
                user_id="whatever-value-was-stamped",
                decision_type="ADD",
                subject="AAPL",
                reason="Strong thesis",
                confidence=80,
                decided_at=_NOW.isoformat(),
                recorded_at=_NOW.isoformat(),
                source="user",
                observation_id=None,
            )
        )
        connection.execute(
            insert(outcomes_table).values(
                outcome_id="outcome-1",
                case_id="case-aapl",
                decision_id="decision-1",
                statement="Bought 10 shares",
                note=None,
                occurred_at=_NOW.isoformat(),
                recorded_at=_NOW.isoformat(),
            )
        )
        connection.execute(
            insert(observations_table).values(
                observation_id="observation-1",
                case_id="case-aapl",
                subject="AAPL",
                statement="Margins expanded",
                source="10-Q",
                note=None,
                observed_at=_NOW.isoformat(),
                recorded_at=_NOW.isoformat(),
            )
        )


def _seed_daily_brief(engine: Engine) -> None:
    create_daily_brief_change_log_table(engine)
    create_daily_brief_case_baseline_table(engine)
    create_daily_brief_view_state_table(engine)
    with engine.begin() as connection:
        connection.execute(
            insert(daily_brief_change_log_table).values(
                id="change-1",
                user_id="00000000-0000-0000-0000-000000000001",
                ticker="AAPL",
                case_id="case-aapl",
                reason_code="thesis_strengthened",
                value=None,
                secondary_value=None,
                label=None,
                headline="Thesis strengthened",
                detected_at=_NOW.isoformat(),
                seen_at=None,
                priority_rank=1,
                is_baseline=False,
            )
        )
        connection.execute(
            insert(daily_brief_case_baseline_table).values(
                user_id="00000000-0000-0000-0000-000000000001",
                case_id="case-aapl",
                first_seen_at=_NOW.isoformat(),
            )
        )
        connection.execute(
            insert(daily_brief_view_state_table).values(
                user_id="00000000-0000-0000-0000-000000000001",
                last_viewed_at=_NOW.isoformat(),
            )
        )


def _seed_decision_layer_caches(engine: Engine) -> None:
    create_monitoring_result_table(engine)
    create_decision_memory_snapshot_table(engine)
    with engine.begin() as connection:
        connection.execute(
            insert(monitoring_result_table).values(
                case_id="case-aapl",
                ticker="AAPL",
                generated_at=_NOW.isoformat(),
                result_json="{}",
            )
        )
        connection.execute(
            insert(decision_memory_snapshot_table).values(
                id="case-aapl:2026-08-27T00:00:00",
                case_id="case-aapl",
                ticker="AAPL",
                recorded_at=_NOW.isoformat(),
                content_hash="abc",
                snapshot_json="{}",
                change_json=None,
            )
        )


def _seed_preserved_tables(engine: Engine) -> None:
    create_business_record_table(engine)
    create_alpha_vantage_daily_call_count_table(engine)
    with engine.begin() as connection:
        connection.execute(
            insert(business_record_table).values(
                id="lineage-1:v1",
                lineage_id="lineage-1",
                identifier="AAPL",
                company="AAPL",
                document_type="10-K",
                published_at="2026-01-01",
                provider_id="sec_edgar",
                source_reference="https://example.com",
                content_hash="hash",
                version_number=1,
                version_created_at=_NOW.isoformat(),
                version_supersedes=None,
                version_provider_revision=None,
                validation_status="valid",
                period_start=None,
                period_end=None,
                language="en",
                metadata_json="{}",
                provenance_json="{}",
            )
        )
        connection.execute(
            insert(alpha_vantage_daily_call_count_table).values(call_date="2026-08-27", call_count=5)
        )


def _seed_everything(engine: Engine) -> None:
    _seed_portfolio_and_watchlist(engine)
    _seed_cases(engine)
    _seed_decision_journal(engine)
    _seed_daily_brief(engine)
    _seed_decision_layer_caches(engine)
    _seed_preserved_tables(engine)


class TestProductionGuard:
    def test_refuses_when_atlas_env_is_production(self, engine, monkeypatch):
        monkeypatch.setenv("ATLAS_ENV", "production")
        with pytest.raises(NotDevelopmentEnvironmentError):
            reset_development_user(engine)

    def test_refuses_for_any_non_development_value(self, engine, monkeypatch):
        monkeypatch.setenv("ATLAS_ENV", "staging")
        with pytest.raises(NotDevelopmentEnvironmentError):
            reset_development_user(engine)

    def test_allows_when_unset(self, engine, monkeypatch):
        monkeypatch.delenv("ATLAS_ENV", raising=False)
        reset_development_user(engine)  # must not raise

    def test_allows_when_explicitly_development(self, engine, monkeypatch):
        monkeypatch.setenv("ATLAS_ENV", "development")
        reset_development_user(engine)  # must not raise

    def test_refusal_leaves_data_untouched(self, engine, monkeypatch):
        _seed_everything(engine)
        monkeypatch.setenv("ATLAS_ENV", "production")
        with pytest.raises(NotDevelopmentEnvironmentError):
            reset_development_user(engine)
        assert AlphaPortfolioStore(engine).get() is not None


class TestDryRun:
    def test_dry_run_reports_counts_but_changes_nothing(self, engine):
        _seed_everything(engine)
        report = reset_development_user(engine, dry_run=True)

        assert report.portfolio_holdings_removed == 2
        assert report.counts["Watchlist entries"] == 2
        assert report.counts["Cases"] == 4
        assert report.counts["Decisions"] == 1

        # Nothing was actually deleted.
        assert AlphaPortfolioStore(engine).get() is not None
        with engine.connect() as connection:
            assert connection.execute(select(cases_table)).fetchall()
            assert connection.execute(select(decisions_table)).fetchall()


class TestPortfolioAndWatchlistReset:
    def test_portfolio_is_emptied(self, engine):
        _seed_everything(engine)
        reset_development_user(engine)
        assert AlphaPortfolioStore(engine).get() is None

    def test_portfolio_holdings_removed_count_reflects_real_holdings_not_row_count(self, engine):
        _seed_everything(engine)
        report = reset_development_user(engine)
        assert report.portfolio_holdings_removed == 2

    def test_watchlist_is_emptied_including_soft_removed_entries(self, engine):
        _seed_everything(engine)
        reset_development_user(engine)
        with engine.connect() as connection:
            from atlas.alpha.watchlist.table import alpha_watchlist_entry_table

            rows = connection.execute(select(alpha_watchlist_entry_table)).fetchall()
        assert rows == []

    def test_watchlist_entries_removed_count_includes_soft_removed(self, engine):
        _seed_everything(engine)
        report = reset_development_user(engine)
        # NVDA (active) + AMD (soft-removed) = 2
        assert report.counts["Watchlist entries"] == 2


class TestDailyBriefReset:
    def test_change_log_baseline_and_view_state_all_cleared(self, engine):
        _seed_everything(engine)
        reset_development_user(engine)
        with engine.connect() as connection:
            assert connection.execute(select(daily_brief_change_log_table)).fetchall() == []
            assert connection.execute(select(daily_brief_case_baseline_table)).fetchall() == []
            assert connection.execute(select(daily_brief_view_state_table)).fetchall() == []

    def test_clears_rows_stamped_with_the_frontend_placeholder_user_id(self, engine):
        """Real dev data uses `ALPHA_PLACEHOLDER_USER_ID`
        (00000000-0000-0000-0000-000000000001), a frontend constant
        disconnected from the resolved InvestorIdentity -- this must
        still be cleared, not skipped because it doesn't match the
        resolved identity."""
        _seed_everything(engine)
        report = reset_development_user(engine)
        assert report.counts["Daily Brief change-log entries"] == 1
        assert report.counts["Daily Brief baseline markers"] == 1
        assert report.counts["Daily Brief read-state rows"] == 1


class TestDecisionJournalAndCasesReset:
    def test_decisions_outcomes_observations_cleared(self, engine):
        _seed_everything(engine)
        reset_development_user(engine)
        with engine.connect() as connection:
            assert connection.execute(select(decisions_table)).fetchall() == []
            assert connection.execute(select(outcomes_table)).fetchall() == []
            assert connection.execute(select(observations_table)).fetchall() == []

    def test_decision_layer_caches_cleared(self, engine):
        _seed_everything(engine)
        reset_development_user(engine)
        with engine.connect() as connection:
            assert connection.execute(select(monitoring_result_table)).fetchall() == []
            assert connection.execute(select(decision_memory_snapshot_table)).fetchall() == []

    def test_cases_cleared(self, engine):
        _seed_everything(engine)
        report = reset_development_user(engine)
        assert report.counts["Cases"] == 4
        with engine.connect() as connection:
            assert connection.execute(select(cases_table)).fetchall() == []


class TestPreservesSharedIntelligence:
    def test_business_records_untouched(self, engine):
        _seed_everything(engine)
        reset_development_user(engine)
        with engine.connect() as connection:
            rows = connection.execute(select(business_record_table)).fetchall()
        assert len(rows) == 1
        assert rows[0].company == "AAPL"

    def test_alpha_vantage_quota_untouched(self, engine):
        _seed_everything(engine)
        reset_development_user(engine)
        with engine.connect() as connection:
            rows = connection.execute(select(alpha_vantage_daily_call_count_table)).fetchall()
        assert len(rows) == 1
        assert rows[0].call_count == 5

    def test_investor_identity_preserved_not_regenerated(self, engine):
        _seed_everything(engine)
        before = resolve_investor_identity(engine)
        reset_development_user(engine)
        after = resolve_investor_identity(engine)
        assert before == after

    def test_report_names_the_preserved_investor_identity(self, engine):
        _seed_everything(engine)
        expected = str(resolve_investor_identity(engine))
        report = reset_development_user(engine)
        assert report.investor_user_id == expected


class TestIdempotence:
    def test_running_twice_in_a_row_is_safe_and_reports_zero_the_second_time(self, engine):
        _seed_everything(engine)
        first = reset_development_user(engine)
        assert first.total_removed > 0

        second = reset_development_user(engine)
        assert second.total_removed == 0
        assert second.portfolio_holdings_removed == 0

    def test_running_against_an_already_empty_database_never_raises(self, engine):
        reset_development_user(engine)  # never seeded anything at all
        report = reset_development_user(engine)
        assert report.total_removed == 0


class TestTransactionality:
    def test_dry_run_never_commits_even_if_counts_are_computed(self, engine):
        _seed_everything(engine)
        reset_development_user(engine, dry_run=True)
        # A second, real run should still find everything -- proving
        # the dry run truly changed nothing.
        report = reset_development_user(engine, dry_run=False)
        assert report.portfolio_holdings_removed == 2
        assert report.counts["Cases"] == 4
