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


def _calls(speaker: str, titled: list[tuple[str, str]]):
    """One statement per `(quarter, title)` call, each on its own quarter end."""
    ends = {"Q1": (3, 31), "Q2": (6, 30), "Q3": (9, 30), "Q4": (12, 31)}
    return tuple(
        _statement(quarter, index, speaker, title, "Remarks.", period_end=date(int(quarter[:4]), *ends[quarter[4:]]))
        for index, (quarter, title) in enumerate(titled)
    )


def _roles(title: str) -> ExecutiveRoleCategory | None:
    executives = _knowledge(_calls("Someone", [("2025Q3", title)])).executives
    return executives[0].role_category if executives else None


class TestWholeWordRoleTitles:
    """Real persisted titles. As bare substrings, "cto" matched inside
    "director" and "president" inside "vice president"."""

    def test_a_director_job_title_is_not_a_cto(self):
        assert _roles("Director, Autopilot Software") is ExecutiveRoleCategory.OTHER_EXECUTIVE
        assert _roles("Director of Self-Driving AI") is ExecutiveRoleCategory.OTHER_EXECUTIVE
        assert _roles("Chief Technology Officer") is ExecutiveRoleCategory.CTO

    def test_a_vice_president_is_not_the_president(self):
        for title in ("Senior Vice President, Vehicle Engineering", "Executive Vice President & Chief Commercial Officer",
                      "Executive Vice President, Upstream", "Vice-President, Sales"):
            assert _roles(title) is ExecutiveRoleCategory.OTHER_EXECUTIVE, title
        assert _roles("President & Chief Business Officer") is ExecutiveRoleCategory.PRESIDENT

    def test_priority_order_is_kept(self):
        assert _roles("Chairman, President & CEO") is ExecutiveRoleCategory.CEO
        assert _roles("Executive Vice President and CFO") is ExecutiveRoleCategory.CFO
        assert _roles("President, Asia Pacific, Europe, Middle East & Africa (incoming CFO)") is ExecutiveRoleCategory.CFO
        assert _roles("Chief Executive Officer (CEO)") is ExecutiveRoleCategory.CEO

    def test_board_seats_and_chairs_still_classify(self):
        assert _roles("Director") is ExecutiveRoleCategory.BOARD_DIRECTOR
        assert _roles("Independent Director") is ExecutiveRoleCategory.BOARD_DIRECTOR
        assert _roles("Chairwoman") is ExecutiveRoleCategory.CHAIR

    def test_exclusions_are_kept(self):
        assert _roles("Corporate Vice President, Investor Relations") is None
        assert _roles("Director of Investor Relations") is None
        assert _roles("Analyst (Bernstein Research)") is None

    def test_one_director_turned_vp_stays_one_person(self):
        """TSLA's Ashok Elluswamy -- once a CTO under one title, another role under the next."""
        knowledge = _knowledge(_calls("Ashok Elluswamy", [("2025Q3", "Director, Autopilot Software"), ("2026Q2", "VP of AI")]))
        assert [(e.name, e.role_category) for e in knowledge.executives] == [
            ("Ashok Elluswamy", ExecutiveRoleCategory.OTHER_EXECUTIVE)
        ]
        assert not any(e.event_type is LeadershipChangeEventType.ROLE_CHANGE for e in knowledge.leadership_changes)

    def test_one_title_abbreviated_and_spelled_out_stays_one_person(self):
        """TSLA's Lars Moravy -- "SVP" and "Senior Vice President" are one role."""
        knowledge = _knowledge(_calls(
            "Lars Moravy", [("2025Q4", "SVP, Vehicle Engineering"), ("2026Q2", "Senior Vice President, Vehicle Engineering")]
        ))
        assert len(knowledge.executives) == 1
        assert not any(e.event_type is LeadershipChangeEventType.ROLE_CHANGE for e in knowledge.leadership_changes)

    def test_an_evp_is_not_split_off_as_a_president(self):
        """VST's Stacey Dore."""
        knowledge = _knowledge(_calls(
            "Stacey Dore", [("2025Q3", "Senior Executive"), ("2025Q4", "Executive Vice President & Chief Commercial Officer")]
        ))
        assert [e.role_category for e in knowledge.executives] == [ExecutiveRoleCategory.OTHER_EXECUTIVE]

    def test_a_real_promotion_to_president_is_still_a_role_change(self):
        """GOOGL's Philipp Schindler -- a genuine change of title."""
        knowledge = _knowledge(_calls(
            "Philipp Schindler", [("2025Q3", "Chief Business Officer"), ("2026Q2", "President & Chief Business Officer")]
        ))
        assert [e.role_category for e in knowledge.executives] == [
            ExecutiveRoleCategory.OTHER_EXECUTIVE, ExecutiveRoleCategory.PRESIDENT,
        ]
        (change,) = [e for e in knowledge.leadership_changes if e.event_type is LeadershipChangeEventType.ROLE_CHANGE]
        assert (change.prior_role_category, change.role_category) == (
            ExecutiveRoleCategory.OTHER_EXECUTIVE, ExecutiveRoleCategory.PRESIDENT,
        )

    def test_an_inconsistent_provider_label_is_not_special_cased(self):
        """ASML's Christophe Fouquet is CEO; one call labels him "Chief
        Technology Officer". Atlas reads the titles literally."""
        knowledge = _knowledge(_calls(
            "Christophe Fouquet", [("2025Q3", "CEO"), ("2026Q1", "Chief Technology Officer"), ("2026Q2", "CEO")]
        ))
        assert {e.role_category for e in knowledge.executives} == {ExecutiveRoleCategory.CEO, ExecutiveRoleCategory.CTO}


def _people(calls: list[tuple[str, str, str]]):
    """`(speaker, quarter, title)` statements across one company's calls."""
    ends = {"Q1": (3, 31), "Q2": (6, 30), "Q3": (9, 30), "Q4": (12, 31)}
    return _knowledge(tuple(
        _statement(quarter, index, speaker, title, "Remarks.", period_end=date(int(quarter[:4]), *ends[quarter[4:]]))
        for index, (speaker, quarter, title) in enumerate(calls)
    ))


def _of(knowledge, kind: LeadershipChangeEventType) -> list[str]:
    return [e.executive_name for e in knowledge.leadership_changes if e.event_type is kind]


class TestMultiHolderRolesFormNoChain:
    """`OTHER_EXECUTIVE` and `BOARD_DIRECTOR` are held by many people at
    once: a later holder is not the earlier one's successor."""

    def test_two_other_executives_are_not_a_departure_and_a_successor(self):
        """TSLA: Ashok Elluswamy, then Lars Moravy, first observed in turn."""
        knowledge = _people([
            ("Ashok Elluswamy", "2025Q3", "Director, Autopilot Software"),
            ("Lars Moravy", "2025Q4", "SVP, Vehicle Engineering"),
            ("Ashok Elluswamy", "2026Q2", "VP of AI"),
            ("Lars Moravy", "2026Q2", "Senior Vice President, Vehicle Engineering"),
        ])
        assert _of(knowledge, LeadershipChangeEventType.DEPARTURE) == []
        assert sorted(_of(knowledge, LeadershipChangeEventType.APPOINTMENT)) == ["Ashok Elluswamy", "Lars Moravy"]
        assert all(
            "different individual" not in e.provenance for e in knowledge.leadership_changes
        )
        assert LeadershipChangeFindingKind.REPEATED_EXECUTIVE_TURNOVER not in {f.kind for f in knowledge.findings}

    def test_an_evp_and_an_svp_are_not_a_succession(self):
        """VST: Stacey Dore, then Shawn Stuckey."""
        knowledge = _people([
            ("Stacey Dore", "2025Q4", "Executive Vice President & Chief Commercial Officer"),
            ("Stacey Dore", "2026Q1", "Executive Vice President & Chief Commercial Officer"),
            ("Shawn Stuckey", "2026Q1", "Senior Vice President, Trading & Origination"),
        ])
        assert _of(knowledge, LeadershipChangeEventType.DEPARTURE) == []
        assert knowledge.successions == ()

    def test_an_interim_other_executive_has_no_successor(self):
        knowledge = _people([
            ("Michael Spencer", "2025Q3", "Interim Executive Vice President of Finance and Strategy"),
            ("Jane Doe", "2025Q4", "Chief Marketing Officer"),
        ])
        assert knowledge.successions == ()
        assert _of(knowledge, LeadershipChangeEventType.PERMANENT_APPOINTMENT) == []

    def test_two_directors_are_two_seats(self):
        knowledge = _people([
            ("A Director", "2025Q3", "Independent Director"),
            ("B Director", "2025Q4", "Independent Director"),
        ])
        assert _of(knowledge, LeadershipChangeEventType.DEPARTURE) == []

    def test_a_one_seat_role_still_changes_hands(self):
        knowledge = _people([("Alice Smith", "2025Q3", "CFO"), ("Dave Kim", "2025Q4", "CFO")])
        assert _of(knowledge, LeadershipChangeEventType.DEPARTURE) == ["Alice Smith"]
        assert LeadershipChangeFindingKind.CFO_TRANSITION_OCCURRED in {f.kind for f in knowledge.findings}

    def test_a_move_out_of_the_catch_all_is_still_a_role_change(self):
        """GOOGL: Philipp Schindler, Chief Business Officer, then President."""
        knowledge = _people([
            ("Philipp Schindler", "2025Q3", "Chief Business Officer"),
            ("Someone Else", "2025Q4", "Chief Marketing Officer"),
            ("Philipp Schindler", "2026Q2", "President & Chief Business Officer"),
        ])
        assert _of(knowledge, LeadershipChangeEventType.ROLE_CHANGE) == ["Philipp Schindler"]
        assert _of(knowledge, LeadershipChangeEventType.DEPARTURE) == []


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

    def test_missing_title_is_excluded_not_other_executive(self):
        """Trust Hardening Sprint: an untitled speaker is unknown, not a
        default executive -- Phase 5's own "unknown roles must not
        default into executive identities.\""""
        records = (_statement("2023Q4", 0, "Alice Smith", None, "Strong quarter.", period_end=date(2023, 12, 31)),)
        knowledge = _knowledge(records)
        assert knowledge.executives == ()

    def test_analyst_title_is_never_an_executive(self):
        records = (
            _statement(
                "2023Q4", 0, "Stacy Rasgon", "Analyst (Bernstein Research)", "What's the outlook?",
                period_end=date(2023, 12, 31),
            ),
        )
        knowledge = _knowledge(records)
        assert knowledge.executives == ()

    def test_operator_title_is_never_an_executive(self):
        records = (
            _statement("2023Q4", 0, "Operator", "Operator", "Welcome to the call.", period_end=date(2023, 12, 31)),
        )
        knowledge = _knowledge(records)
        assert knowledge.executives == ()

    def test_investor_relations_title_without_executive_keyword_is_excluded(self):
        records = (
            _statement(
                "2023Q4", 0, "Michael Sullivan", "Corporate Vice President, Investor Relations",
                "Thanks for joining.", period_end=date(2023, 12, 31),
            ),
        )
        knowledge = _knowledge(records)
        assert knowledge.executives == ()

    def test_genuine_executive_title_not_in_keyword_list_is_still_other_executive(self):
        records = (
            _statement(
                "2023Q4", 0, "Jane Doe", "Chief Marketing Officer", "Brand momentum is strong.",
                period_end=date(2023, 12, 31),
            ),
        )
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
        # Stage 3.2: the window is the calls' fiscal periods, never the
        # records' calendar period ends or fetch times.
        assert knowledge.executives[0].first_observed_period == "2022Q4"
        assert knowledge.executives[0].last_observed_period == "2023Q4"
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
        assert dave_events[0].observed_period == "2023Q4"

    def test_succession_produces_permanent_appointment_not_generic_appointment(self):
        records = (
            _statement("2022Q4", 0, "Bob Jones", "Interim CFO", "Update.", period_end=date(2022, 12, 31)),
            _statement("2023Q4", 0, "Carol Lee", "CFO", "Update.", period_end=date(2023, 12, 31)),
        )
        knowledge = _knowledge(records)
        carol_event = next(e for e in knowledge.leadership_changes if e.executive_name == "Carol Lee")
        assert carol_event.event_type is LeadershipChangeEventType.PERMANENT_APPOINTMENT


class TestCompositionQueries:
    def test_executive_at_returns_the_holder_covering_the_period(self):
        records = (
            _statement("2022Q4", 0, "Alice Smith", "CEO", "Year one.", period_end=date(2022, 12, 31)),
            _statement("2023Q4", 0, "Dave Kim", "CEO", "Year two.", period_end=date(2023, 12, 31)),
        )
        knowledge = _knowledge(records)
        assert executive_at(knowledge.executives, ExecutiveRoleCategory.CEO, "2022Q4").name == "Alice Smith"
        assert executive_at(knowledge.executives, ExecutiveRoleCategory.CEO, "2023Q4").name == "Dave Kim"
        assert executive_at(knowledge.executives, ExecutiveRoleCategory.CEO, "2020Q1") is None

    def test_executives_present_during_a_range(self):
        records = (
            _statement("2022Q4", 0, "Alice Smith", "CEO", "Year one.", period_end=date(2022, 12, 31)),
            _statement("2023Q4", 0, "Dave Kim", "CEO", "Year two.", period_end=date(2023, 12, 31)),
        )
        knowledge = _knowledge(records)
        present = executives_present_during(knowledge.executives, "2022Q1", "2022Q4")
        assert [e.name for e in present] == ["Alice Smith"]

    def test_changes_between_two_periods(self):
        records = (
            _statement("2022Q4", 0, "Alice Smith", "CEO", "Year one.", period_end=date(2022, 12, 31)),
            _statement("2023Q4", 0, "Dave Kim", "CEO", "Year two.", period_end=date(2023, 12, 31)),
        )
        knowledge = _knowledge(records)
        changes = changes_between(knowledge.leadership_changes, "2023Q1", "2023Q4")
        assert len(changes) == 1
        assert changes[0].executive_name == "Dave Kim"
        assert changes[0].event_type is LeadershipChangeEventType.APPOINTMENT


class TestManagementKnowledgeLinking:
    def test_find_executive_for_statement_resolves_speaker_and_period(self):
        records = (_statement("2023Q4", 0, "Alice Smith", "CEO", "Update.", period_end=date(2023, 12, 31)),)
        knowledge = _knowledge(records)
        resolved = find_executive_for_statement(knowledge.executives, "Alice Smith", "2023Q4")
        assert resolved is not None
        assert resolved.role_category is ExecutiveRoleCategory.CEO

    def test_unknown_speaker_resolves_to_none(self):
        records = (_statement("2023Q4", 0, "Alice Smith", "CEO", "Update.", period_end=date(2023, 12, 31)),)
        knowledge = _knowledge(records)
        assert find_executive_for_statement(knowledge.executives, "Unknown Person", "2023Q4") is None


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
