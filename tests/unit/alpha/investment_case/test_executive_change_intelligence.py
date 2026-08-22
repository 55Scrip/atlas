"""Tests for `atlas.alpha.investment_case.executive_change_intelligence`
(Capability Expansion Sprint 10, Phases 2 through 8).
"""
from __future__ import annotations

from datetime import date, datetime, timezone

from atlas.alpha.investment_case.earnings_call import extract_earnings_call_knowledge
from atlas.alpha.investment_case.executive_change_intelligence import (
    ExecutiveRoleCategory,
    LeadershipChangeEventType,
    LeadershipChangeFindingKind,
    changes_between,
    executive_at,
    executives_present_during,
    extract_executive_change_intelligence,
    find_executive_for_statement,
)
from atlas.analysis_engine.business_data.models import RawBusinessDocument
from atlas.analysis_engine.business_data.pipeline import IngestedRecord, ingest

_EVALUATED_AT = datetime(2026, 8, 22, tzinfo=timezone.utc)


def _statement(quarter: str, index: int, speaker: str, title: str | None, content: str, *, period_end: date):
    metadata = {"quarter": quarter, "statement_index": index, "speaker": speaker, "content": content}
    if title is not None:
        metadata["title"] = title
    document = RawBusinessDocument(
        identifier=f"AAPL:transcript:{quarter}:{index}",
        company="AAPL",
        source_kind="transcript",
        published_at=datetime(period_end.year, period_end.month, period_end.day, tzinfo=timezone.utc),
        provider_id="alpha_vantage",
        raw_reference="https://example.test/transcript",
        content_hash=f"hash-{quarter}-{index}",
        language="en",
        period_start=period_end,
        period_end=period_end,
        metadata=metadata,
    )
    result = ingest(document, evaluated_at=_EVALUATED_AT)
    assert isinstance(result, IngestedRecord)
    return result.record


def _knowledge(records, ticker="AAPL"):
    return extract_executive_change_intelligence(ticker, extract_earnings_call_knowledge(records))


class TestEmptyInput:
    def test_no_transcripts_yields_empty_history(self):
        knowledge = _knowledge(())
        assert knowledge.executives == ()
        assert knowledge.leadership_changes == ()
        assert knowledge.successions == ()
        assert knowledge.findings[0].kind is LeadershipChangeFindingKind.INSUFFICIENT_LEADERSHIP_HISTORY


class TestIdentityExtraction:
    def test_ceo_title_is_classified(self):
        records = (_statement("2023Q4", 0, "Alice Smith", "Chief Executive Officer", "Strong quarter.", period_end=date(2023, 12, 31)),)
        knowledge = _knowledge(records)
        assert len(knowledge.executives) == 1
        assert knowledge.executives[0].role_category is ExecutiveRoleCategory.CEO
        assert knowledge.executives[0].name == "Alice Smith"

    def test_missing_title_is_other_executive(self):
        records = (_statement("2023Q4", 0, "Alice Smith", None, "Strong quarter.", period_end=date(2023, 12, 31)),)
        knowledge = _knowledge(records)
        assert knowledge.executives[0].role_category is ExecutiveRoleCategory.OTHER_EXECUTIVE

    def test_start_and_end_date_are_always_none(self):
        records = (_statement("2023Q4", 0, "Alice Smith", "CFO", "Solid results.", period_end=date(2023, 12, 31)),)
        knowledge = _knowledge(records)
        assert knowledge.executives[0].start_date is None
        assert knowledge.executives[0].end_date is None

    def test_interim_title_is_detected(self):
        records = (_statement("2023Q4", 0, "Bob Jones", "Interim Chief Financial Officer", "Update.", period_end=date(2023, 12, 31)),)
        knowledge = _knowledge(records)
        assert knowledge.executives[0].is_interim is True

    def test_observed_window_spans_all_transcripts(self):
        records = (
            _statement("2022Q4", 0, "Alice Smith", "CEO", "Year one.", period_end=date(2022, 12, 31)),
            _statement("2023Q4", 0, "Alice Smith", "CEO", "Year two.", period_end=date(2023, 12, 31)),
        )
        knowledge = _knowledge(records)
        assert knowledge.executives[0].first_observed_date == date(2022, 12, 31)
        assert knowledge.executives[0].last_observed_date == date(2023, 12, 31)
        assert knowledge.executives[0].source_transcripts == ("2022Q4", "2023Q4")


class TestSuccession:
    def test_interim_to_permanent_succession_is_detected(self):
        records = (
            _statement("2022Q4", 0, "Bob Jones", "Interim CFO", "Update.", period_end=date(2022, 12, 31)),
            _statement("2023Q4", 0, "Carol Lee", "Chief Financial Officer", "Update.", period_end=date(2023, 12, 31)),
        )
        knowledge = _knowledge(records)
        assert len(knowledge.successions) == 1
        succession = knowledge.successions[0]
        assert succession.outgoing_executive_name == "Bob Jones"
        assert succession.incoming_executive_name == "Carol Lee"
        assert succession.role_category is ExecutiveRoleCategory.CFO

    def test_no_succession_when_neither_is_interim(self):
        records = (
            _statement("2022Q4", 0, "Bob Jones", "CFO", "Update.", period_end=date(2022, 12, 31)),
            _statement("2023Q4", 0, "Carol Lee", "CFO", "Update.", period_end=date(2023, 12, 31)),
        )
        knowledge = _knowledge(records)
        assert knowledge.successions == ()

    def test_same_person_dropping_interim_is_not_a_succession(self):
        records = (
            _statement("2022Q4", 0, "Bob Jones", "Interim CFO", "Update.", period_end=date(2022, 12, 31)),
            _statement("2023Q4", 0, "Bob Jones", "CFO", "Update.", period_end=date(2023, 12, 31)),
        )
        knowledge = _knowledge(records)
        assert knowledge.successions == ()


class TestLeadershipChangeEvents:
    def test_first_appearance_is_appointment(self):
        records = (_statement("2023Q4", 0, "Alice Smith", "CEO", "Update.", period_end=date(2023, 12, 31)),)
        knowledge = _knowledge(records)
        assert knowledge.leadership_changes[0].event_type is LeadershipChangeEventType.APPOINTMENT

    def test_interim_first_appearance_is_interim_appointment(self):
        records = (_statement("2023Q4", 0, "Bob Jones", "Interim CFO", "Update.", period_end=date(2023, 12, 31)),)
        knowledge = _knowledge(records)
        assert knowledge.leadership_changes[0].event_type is LeadershipChangeEventType.INTERIM_APPOINTMENT

    def test_departure_is_recorded_when_superseded(self):
        records = (
            _statement("2022Q4", 0, "Alice Smith", "CEO", "Year one.", period_end=date(2022, 12, 31)),
            _statement("2023Q4", 0, "Dave Kim", "CEO", "Year two.", period_end=date(2023, 12, 31)),
        )
        knowledge = _knowledge(records)
        departure = next(
            e for e in knowledge.leadership_changes
            if e.executive_name == "Alice Smith" and e.event_type is LeadershipChangeEventType.DEPARTURE
        )
        assert departure.effective_date is None
        assert departure.announcement_date is None

    def test_role_change_detected_for_same_person_different_role(self):
        records = (
            _statement("2022Q4", 0, "Dave Kim", "CEO", "Year one.", period_end=date(2022, 12, 31)),
            _statement("2023Q4", 0, "Dave Kim", "President", "Year two.", period_end=date(2023, 12, 31)),
        )
        knowledge = _knowledge(records)
        role_change = next(e for e in knowledge.leadership_changes if e.event_type is LeadershipChangeEventType.ROLE_CHANGE)
        assert role_change.executive_name == "Dave Kim"
        assert role_change.role_category is ExecutiveRoleCategory.PRESIDENT
        assert role_change.prior_role_category is ExecutiveRoleCategory.CEO

    def test_role_change_does_not_also_produce_a_departure(self):
        records = (
            _statement("2022Q4", 0, "Dave Kim", "CEO", "Year one.", period_end=date(2022, 12, 31)),
            _statement("2023Q4", 0, "Dave Kim", "President", "Year two.", period_end=date(2023, 12, 31)),
        )
        knowledge = _knowledge(records)
        departures = [e for e in knowledge.leadership_changes if e.event_type is LeadershipChangeEventType.DEPARTURE]
        assert departures == []

    def test_a_non_first_non_succession_holder_still_gets_an_appointment_event(self):
        records = (
            _statement("2022Q4", 0, "Alice Smith", "CEO", "Year one.", period_end=date(2022, 12, 31)),
            _statement("2023Q4", 0, "Dave Kim", "CEO", "Year two.", period_end=date(2023, 12, 31)),
        )
        knowledge = _knowledge(records)
        dave_events = [e for e in knowledge.leadership_changes if e.executive_name == "Dave Kim"]
        assert len(dave_events) == 1
        assert dave_events[0].event_type is LeadershipChangeEventType.APPOINTMENT
        assert dave_events[0].observed_date == date(2023, 12, 31)

    def test_succession_produces_permanent_appointment_not_generic_appointment(self):
        records = (
            _statement("2022Q4", 0, "Bob Jones", "Interim CFO", "Update.", period_end=date(2022, 12, 31)),
            _statement("2023Q4", 0, "Carol Lee", "CFO", "Update.", period_end=date(2023, 12, 31)),
        )
        knowledge = _knowledge(records)
        carol_event = next(e for e in knowledge.leadership_changes if e.executive_name == "Carol Lee")
        assert carol_event.event_type is LeadershipChangeEventType.PERMANENT_APPOINTMENT


class TestCompositionQueries:
    def test_executive_at_returns_the_holder_covering_the_date(self):
        records = (
            _statement("2022Q4", 0, "Alice Smith", "CEO", "Year one.", period_end=date(2022, 12, 31)),
            _statement("2023Q4", 0, "Dave Kim", "CEO", "Year two.", period_end=date(2023, 12, 31)),
        )
        knowledge = _knowledge(records)
        assert executive_at(knowledge.executives, ExecutiveRoleCategory.CEO, date(2022, 12, 31)).name == "Alice Smith"
        assert executive_at(knowledge.executives, ExecutiveRoleCategory.CEO, date(2023, 12, 31)).name == "Dave Kim"
        assert executive_at(knowledge.executives, ExecutiveRoleCategory.CEO, date(2020, 1, 1)) is None

    def test_executives_present_during_a_range(self):
        records = (
            _statement("2022Q4", 0, "Alice Smith", "CEO", "Year one.", period_end=date(2022, 12, 31)),
            _statement("2023Q4", 0, "Dave Kim", "CEO", "Year two.", period_end=date(2023, 12, 31)),
        )
        knowledge = _knowledge(records)
        present = executives_present_during(knowledge.executives, date(2022, 1, 1), date(2022, 12, 31))
        assert [e.name for e in present] == ["Alice Smith"]

    def test_changes_between_two_dates(self):
        records = (
            _statement("2022Q4", 0, "Alice Smith", "CEO", "Year one.", period_end=date(2022, 12, 31)),
            _statement("2023Q4", 0, "Dave Kim", "CEO", "Year two.", period_end=date(2023, 12, 31)),
        )
        knowledge = _knowledge(records)
        changes = changes_between(knowledge.leadership_changes, date(2023, 1, 1), date(2023, 12, 31))
        assert len(changes) == 1
        assert changes[0].executive_name == "Dave Kim"
        assert changes[0].event_type is LeadershipChangeEventType.APPOINTMENT


class TestManagementKnowledgeLinking:
    def test_find_executive_for_statement_resolves_speaker_and_date(self):
        records = (_statement("2023Q4", 0, "Alice Smith", "CEO", "Update.", period_end=date(2023, 12, 31)),)
        knowledge = _knowledge(records)
        resolved = find_executive_for_statement(knowledge.executives, "Alice Smith", date(2023, 12, 31))
        assert resolved is not None
        assert resolved.role_category is ExecutiveRoleCategory.CEO

    def test_unknown_speaker_resolves_to_none(self):
        records = (_statement("2023Q4", 0, "Alice Smith", "CEO", "Update.", period_end=date(2023, 12, 31)),)
        knowledge = _knowledge(records)
        assert find_executive_for_statement(knowledge.executives, "Unknown Person", date(2023, 12, 31)) is None


class TestFindings:
    def test_ceo_and_cfo_transition_findings(self):
        records = (
            _statement("2022Q4", 0, "Alice Smith", "CEO", "Year one.", period_end=date(2022, 12, 31)),
            _statement("2023Q4", 0, "Dave Kim", "CEO", "Year two.", period_end=date(2023, 12, 31)),
        )
        knowledge = _knowledge(records)
        kinds = {f.kind for f in knowledge.findings}
        assert LeadershipChangeFindingKind.CEO_TRANSITION_OCCURRED in kinds

    def test_long_tenure_finding_with_four_transcripts(self):
        records = tuple(
            _statement(f"202{i}Q4", 0, "Alice Smith", "CEO", "Update.", period_end=date(2020 + i, 12, 31))
            for i in range(4)
        )
        knowledge = _knowledge(records)
        kinds = {f.kind for f in knowledge.findings}
        assert LeadershipChangeFindingKind.LONG_EXECUTIVE_TENURE in kinds

    def test_single_stable_executive_yields_no_transition_findings(self):
        records = (_statement("2023Q4", 0, "Alice Smith", "CEO", "Update.", period_end=date(2023, 12, 31)),)
        knowledge = _knowledge(records)
        kinds = {f.kind for f in knowledge.findings}
        assert LeadershipChangeFindingKind.CEO_TRANSITION_OCCURRED not in kinds
        assert LeadershipChangeFindingKind.REPEATED_EXECUTIVE_TURNOVER not in kinds
