"""Stage 2.1 -- the three defects real Q1->Q2 history exposed in Stage 2.

Every fixture here uses phrasing taken from the persisted corpus, and
every test was written, and seen failing, before the repair.
"""
from datetime import date, datetime, timezone

from atlas.analysis_engine.business_data.pipeline import IngestedRecord, ingest
from atlas.analysis_engine.forward_claims import (
    ClaimBound,
    NonRevisionReason,
    RevisionBasis,
    RevisionType,
    compare_claims,
    detect_revisions,
    extract_forward_claims,
    group_claims,
)
from tests.unit.analysis_engine.business_data._fixtures import build_raw_document
from tests.unit.analysis_engine.forward_claims.test_revisions import claim

Q1_AT = datetime(2026, 6, 12, tzinfo=timezone.utc)
Q2_AT = datetime(2026, 8, 25, tzinfo=timezone.utc)
EXTRACTED = datetime(2026, 9, 11, tzinfo=timezone.utc)

GOOGL_Q1 = (
    "We are updating our full year 2026 CapEx guidance range to $180 billion to $190 billion, "
    "up from our previous estimate of $175 billion to $185 billion to now include investment "
    "related to the acquisition of Intersect, which closed in March."
)
GOOGL_Q2 = (
    "We are updating our full year 2026 CapEx guidance range to $195 billion to $205 billion, "
    "up from our previous estimate of $180 billion to $190 billion."
)


def statement(content: str, *, quarter: str, at: datetime, company: str = "GOOGL", index: int = 0,
              title: str = "Chief Financial Officer"):
    end = {"Q1": (3, 31), "Q2": (6, 30), "Q3": (9, 30), "Q4": (12, 31)}[quarter[4:]]
    result = ingest(
        build_raw_document(
            identifier=f"{company}:transcript:{quarter}:{index}",
            company=company,
            source_kind="transcript",
            published_at=at,
            period_start=date(int(quarter[:4]), *end),
            period_end=date(int(quarter[:4]), *end),
            content_hash=f"{company}-{quarter}-{index}",
            metadata={"quarter": quarter, "statement_index": index, "speaker": "A. Executive",
                      "title": title, "content": content},
        ),
        evaluated_at=at,
    )
    assert isinstance(result, IngestedRecord)
    return result.record


def claims_of(*records):
    out = []
    for record in records:
        found, _ = extract_forward_claims(record, extracted_at=EXTRACTED)
        out.extend(found)
    return tuple(out)


def bases_for(revisions, new_claim_id):
    """Every evidence basis Atlas holds for the change to one claim."""
    return {evidence.basis for r in revisions if r.new_claim_id == new_claim_id for evidence in r.evidence}


class TestDefect1MoreEvidenceMustNotDeleteEvidence:
    """Before Q1 was ingested, GOOGL Q2's own "up from our previous
    estimate" produced a revision. Adding Q1 made it disappear, because
    only the earliest claim in a group had its stated prior read."""

    def test_the_later_calls_own_stated_prior_survives_an_earlier_call_arriving(self):
        q1 = statement(GOOGL_Q1, quarter="2026Q1", at=Q1_AT)
        q2 = statement(GOOGL_Q2, quarter="2026Q2", at=Q2_AT)
        claims = claims_of(q1, q2)
        q2_claim = next(c for c in claims if c.source_record_id == q2.id)
        revisions, _ = detect_revisions(claims)
        assert bases_for(revisions, q2_claim.id) == {
            RevisionBasis.OBSERVED_PRIOR_CLAIM,
            RevisionBasis.PRIOR_VALUE_STATED_IN_SAME_SOURCE,
        }

    def test_adding_evidence_only_ever_adds_evidence(self):
        q1 = statement(GOOGL_Q1, quarter="2026Q1", at=Q1_AT)
        q2 = statement(GOOGL_Q2, quarter="2026Q2", at=Q2_AT)
        only_q2 = claims_of(q2)
        with_q1 = claims_of(q1, q2)
        q2_id = only_q2[0].id

        before = bases_for(detect_revisions(only_q2)[0], q2_id)
        after = bases_for(detect_revisions(with_q1)[0], q2_id)
        assert before, "the same-source revision exists on its own"
        assert before <= after, f"evidence was lost: {before - after}"

    def test_the_earlier_call_keeps_its_own_stated_prior_too(self):
        q1 = statement(GOOGL_Q1, quarter="2026Q1", at=Q1_AT)
        q2 = statement(GOOGL_Q2, quarter="2026Q2", at=Q2_AT)
        claims = claims_of(q1, q2)
        q1_claim = next(c for c in claims if c.source_record_id == q1.id)
        assert RevisionBasis.PRIOR_VALUE_STATED_IN_SAME_SOURCE in bases_for(detect_revisions(claims)[0], q1_claim.id)


class TestDefect2PartialRangeMoves:
    """Salesforce "raise[d] the low end" from $41.0-41.3B to $41.1-41.3B.
    Nothing moved down, so this is a raise -- not a mixed change."""

    def _range(self, low, high, at):
        return claim(bound=ClaimBound.RANGE, low=low, high=high, reported_at=at)

    def test_raising_only_the_low_end_is_raised(self):
        assert compare_claims(self._range(41.0, 41.3, Q1_AT), self._range(41.1, 41.3, Q2_AT)).revision_type is RevisionType.RAISED

    def test_raising_only_the_high_end_is_raised(self):
        assert compare_claims(self._range(180, 190, Q1_AT), self._range(180, 195, Q2_AT)).revision_type is RevisionType.RAISED

    def test_lowering_only_the_high_end_is_lowered(self):
        assert compare_claims(self._range(41.0, 41.3, Q1_AT), self._range(41.0, 41.2, Q2_AT)).revision_type is RevisionType.LOWERED

    def test_lowering_only_the_low_end_is_lowered(self):
        assert compare_claims(self._range(180, 190, Q1_AT), self._range(175, 190, Q2_AT)).revision_type is RevisionType.LOWERED


class TestDefect3FiscalAndCalendarYearsNeverCollapse:
    """AMAT, CRM and MU each use both fiscal-year and calendar-year
    wording on real calls. A fiscal year is not a calendar year merely
    because they share a number."""

    def test_a_fiscal_year_and_a_calendar_year_are_never_compared(self):
        q1 = statement("We expect fiscal year 2026 revenue of $10 billion.", quarter="2026Q1", at=Q1_AT, company="ACME")
        q2 = statement("We expect calendar 2026 revenue of $11 billion.", quarter="2026Q2", at=Q2_AT, company="ACME")
        claims = claims_of(q1, q2)
        assert len(claims) == 2
        revisions, _ = detect_revisions(claims)
        assert revisions == (), "a fiscal-year figure was compared with a calendar-year one"

    def test_they_are_never_even_grouped_together(self):
        q1 = statement("We expect fiscal year 2026 revenue of $10 billion.", quarter="2026Q1", at=Q1_AT, company="ACME")
        q2 = statement("We expect calendar year 2026 revenue of $11 billion.", quarter="2026Q2", at=Q2_AT, company="ACME")
        assert len(group_claims(claims_of(q1, q2))) == 2


class TestRangeTruthTable:
    """One truth table, for every bound shape and every evidence basis.
    Midpoints are never consulted."""

    import pytest as _pytest

    @_pytest.mark.parametrize(
        "old,new,expected",
        [
            ((180, 190), (185, 195), RevisionType.RAISED),     # both up
            ((180, 190), (185, 190), RevisionType.RAISED),     # low up only
            ((180, 190), (180, 195), RevisionType.RAISED),     # high up only
            ((180, 190), (175, 185), RevisionType.LOWERED),    # both down
            ((180, 190), (180, 185), RevisionType.LOWERED),    # high down only
            ((180, 190), (175, 190), RevisionType.LOWERED),    # low down only
            ((180, 190), (180, 190), RevisionType.REAFFIRMED),
        ],
    )
    def test_directions(self, old, new, expected):
        a = claim(bound=ClaimBound.RANGE, low=old[0], high=old[1], reported_at=Q1_AT)
        b = claim(bound=ClaimBound.RANGE, low=new[0], high=new[1], reported_at=Q2_AT)
        assert compare_claims(a, b).revision_type is expected

    @_pytest.mark.parametrize(
        "old,new",
        [
            ((180, 190), (185, 185)),  # contracts from both sides to a point
            ((180, 190), (175, 195)),  # widens both ways
            ((41.0, 41.3), (40.9, 41.4)),
        ],
    )
    def test_opposing_endpoint_moves_are_mixed(self, old, new):
        a = claim(bound=ClaimBound.RANGE, low=old[0], high=old[1], reported_at=Q1_AT)
        b = claim(bound=ClaimBound.RANGE, low=new[0], high=new[1], reported_at=Q2_AT)
        result = compare_claims(a, b)
        assert result.revision_type is None
        assert result.reason is NonRevisionReason.MIXED_RANGE_CHANGE

    def test_an_unchanged_midpoint_does_not_make_a_widening_a_reaffirmation(self):
        a = claim(bound=ClaimBound.RANGE, low=180, high=190, reported_at=Q1_AT)
        b = claim(bound=ClaimBound.RANGE, low=175, high=195, reported_at=Q2_AT)  # same 185 midpoint
        assert compare_claims(a, b).revision_type is not RevisionType.REAFFIRMED

    def test_a_raised_midpoint_does_not_make_a_mixed_move_a_raise(self):
        a = claim(bound=ClaimBound.RANGE, low=180, high=200, reported_at=Q1_AT)
        b = claim(bound=ClaimBound.RANGE, low=190, high=195, reported_at=Q2_AT)  # midpoint 190 -> 192.5
        assert compare_claims(a, b).reason is NonRevisionReason.MIXED_RANGE_CHANGE


class TestHorizonComparability:
    def _kind(self, text):
        record = statement(f"We expect {text} revenue of $10 billion.", quarter="2026Q1", at=Q1_AT, company="ACME")
        (found,), _ = extract_forward_claims(record, extracted_at=EXTRACTED)
        return found

    def test_fiscal_wording_is_read_as_fiscal(self):
        from atlas.analysis_engine.forward_claims import HorizonKind

        for text in ("fiscal year 2026", "fiscal 2026", "FY2026", "FY 2026"):
            assert self._kind(text).horizon_kind is HorizonKind.FISCAL_YEAR, text

    def test_calendar_wording_is_read_as_calendar(self):
        from atlas.analysis_engine.forward_claims import HorizonKind

        for text in ("calendar year 2026", "calendar 2026", "CY2026"):
            assert self._kind(text).horizon_kind is HorizonKind.CALENDAR_YEAR, text

    def test_an_unqualified_year_is_never_assumed_to_be_either(self):
        from atlas.analysis_engine.forward_claims import HorizonKind

        for text in ("full year 2026", "2026"):
            assert self._kind(text).horizon_kind is HorizonKind.UNSPECIFIED_YEAR, text

    def _pair(self, first, second):
        q1 = statement(f"We expect {first} revenue of $10 billion.", quarter="2026Q1", at=Q1_AT, company="ACME")
        q2 = statement(f"We expect {second} revenue of $11 billion.", quarter="2026Q2", at=Q2_AT, company="ACME")
        return claims_of(q1, q2)

    def test_fiscal_against_fiscal_is_comparable(self):
        revisions, _ = detect_revisions(self._pair("fiscal year 2026", "fiscal 2026"))
        assert [r.revision_type for r in revisions] == [RevisionType.RAISED]

    def test_calendar_against_calendar_is_comparable(self):
        revisions, _ = detect_revisions(self._pair("calendar 2026", "calendar year 2026"))
        assert [r.revision_type for r in revisions] == [RevisionType.RAISED]

    def test_an_unqualified_year_is_never_compared_with_an_explicit_one(self):
        for explicit in ("fiscal year 2026", "calendar 2026"):
            a, b = self._pair("2026", explicit)
            assert compare_claims(a, b).reason is NonRevisionReason.DIFFERENT_HORIZON_KIND
            assert detect_revisions((a, b))[0] == ()

    def test_one_sentence_naming_the_same_year_both_ways_is_rejected_rather_than_guessed(self):
        from atlas.analysis_engine.forward_claims import ClaimRejectionReason

        record = statement(
            "We expect fiscal 2026 revenue of $10 billion, and calendar 2026 revenue of $11 billion.",
            quarter="2026Q1", at=Q1_AT, company="ACME",
        )
        found, rejected = extract_forward_claims(record, extracted_at=EXTRACTED)
        assert found == ()
        assert [r.reason for r in rejected] == [ClaimRejectionReason.AMBIGUOUS_HORIZON]

    def test_the_horizon_kind_is_part_of_a_claims_identity(self):
        fiscal = self._kind("fiscal year 2026")
        calendar = self._kind("calendar 2026")
        assert fiscal.id != calendar.id
        assert "fiscal_year" in fiscal.id and "calendar_year" in calendar.id


class TestSameSourceCorroboration:
    def test_a_matching_observed_prior_is_linked_as_corroboration(self):
        q1 = statement(GOOGL_Q1, quarter="2026Q1", at=Q1_AT)
        q2 = statement(GOOGL_Q2, quarter="2026Q2", at=Q2_AT)
        claims = claims_of(q1, q2)
        q1_claim = next(c for c in claims if c.source_record_id == q1.id)
        event = next(r for r in detect_revisions(claims)[0] if r.new_source_record_id == q2.id)
        stated = next(e for e in event.evidence if e.basis is RevisionBasis.PRIOR_VALUE_STATED_IN_SAME_SOURCE)
        assert stated.corroborates_claim_id == q1_claim.id
        assert stated.prior_claim_id is None, "a stated prior is never presented as an observation"
        assert event.corroborated and not event.evidence_disagrees

    def test_it_is_one_revision_event_not_two_management_raises(self):
        q1 = statement(GOOGL_Q1, quarter="2026Q1", at=Q1_AT)
        q2 = statement(GOOGL_Q2, quarter="2026Q2", at=Q2_AT)
        revisions, _ = detect_revisions(claims_of(q1, q2))
        assert len([r for r in revisions if r.new_source_record_id == q2.id]) == 1
        # Q1 -> Q2 and the Q1 call's own restatement are two genuine events.
        assert len(revisions) == 2

    def test_a_non_matching_observed_prior_never_erases_the_stated_one(self):
        q1 = statement(
            "We are updating our full year 2026 CapEx guidance range to $182 billion to $192 billion.",
            quarter="2026Q1", at=Q1_AT,
        )
        q2 = statement(GOOGL_Q2, quarter="2026Q2", at=Q2_AT)
        event = next(r for r in detect_revisions(claims_of(q1, q2))[0] if r.new_source_record_id == q2.id)
        assert {e.basis for e in event.evidence} == {
            RevisionBasis.OBSERVED_PRIOR_CLAIM,
            RevisionBasis.PRIOR_VALUE_STATED_IN_SAME_SOURCE,
        }
        stated = next(e for e in event.evidence if e.basis is RevisionBasis.PRIOR_VALUE_STATED_IN_SAME_SOURCE)
        assert stated.corroborates_claim_id is None
        assert event.evidence_disagrees and not event.corroborated
        assert event.revision_type is RevisionType.RAISED, "both bases still agree on the direction"

    def test_a_match_deeper_in_history_is_never_guessed_at(self):
        """Management's "previous estimate" is the latest one. A figure
        that happens to match an older call is not linked."""
        q4 = statement("We are updating our full year 2026 CapEx guidance range to $180 billion to $190 billion.",
                       quarter="2025Q4", at=datetime(2026, 3, 1, tzinfo=timezone.utc))
        q1 = statement("We are updating our full year 2026 CapEx guidance range to $185 billion to $195 billion.",
                       quarter="2026Q1", at=Q1_AT)
        q2 = statement(GOOGL_Q2, quarter="2026Q2", at=Q2_AT)
        event = next(r for r in detect_revisions(claims_of(q4, q1, q2))[0] if r.new_source_record_id == q2.id)
        stated = next(e for e in event.evidence if e.basis is RevisionBasis.PRIOR_VALUE_STATED_IN_SAME_SOURCE)
        assert stated.corroborates_claim_id is None

    def test_an_even_earlier_call_still_leaves_the_later_stated_prior_in_place(self):
        q4 = statement("We are updating our full year 2026 CapEx guidance range to $170 billion to $180 billion.",
                       quarter="2025Q4", at=datetime(2026, 3, 1, tzinfo=timezone.utc))
        q1 = statement(GOOGL_Q1, quarter="2026Q1", at=Q1_AT)
        q2 = statement(GOOGL_Q2, quarter="2026Q2", at=Q2_AT)
        claims = claims_of(q4, q1, q2)
        q2_id = next(c.id for c in claims if c.source_record_id == q2.id)
        assert RevisionBasis.PRIOR_VALUE_STATED_IN_SAME_SOURCE in bases_for(detect_revisions(claims)[0], q2_id)


class TestInvariantsOnRealShapes:
    def test_claims_are_not_mutated_by_revision_detection(self):
        q1 = statement(GOOGL_Q1, quarter="2026Q1", at=Q1_AT)
        q2 = statement(GOOGL_Q2, quarter="2026Q2", at=Q2_AT)
        claims = claims_of(q1, q2)
        snapshot = tuple(claims)
        detect_revisions(claims)
        assert claims == snapshot == claims_of(q1, q2)

    def test_adding_an_earlier_call_never_changes_a_later_claim(self):
        q1 = statement(GOOGL_Q1, quarter="2026Q1", at=Q1_AT)
        q2 = statement(GOOGL_Q2, quarter="2026Q2", at=Q2_AT)
        (alone,) = claims_of(q2)
        with_history = next(c for c in claims_of(q1, q2) if c.source_record_id == q2.id)
        assert alone == with_history

    def test_the_result_does_not_depend_on_arrival_order(self):
        q1 = statement(GOOGL_Q1, quarter="2026Q1", at=Q1_AT)
        q2 = statement(GOOGL_Q2, quarter="2026Q2", at=Q2_AT)
        claims = claims_of(q1, q2)
        assert detect_revisions(claims) == detect_revisions(tuple(reversed(claims)))

    def test_raised_revenue_and_raised_capex_are_the_same_fact(self):
        crm = compare_claims(
            claim(bound=ClaimBound.RANGE, low=41.0, high=41.3, reported_at=Q1_AT),
            claim(bound=ClaimBound.RANGE, low=41.1, high=41.3, reported_at=Q2_AT),
        )
        googl = detect_revisions(claims_of(statement(GOOGL_Q2, quarter="2026Q2", at=Q2_AT)))[0][0]
        assert crm.revision_type is googl.revision_type is RevisionType.RAISED

    def test_a_language_only_reaffirmation_creates_nothing(self):
        """Vistra's Q1 CEO reaffirmed 2026 guidance without restating a
        number. Nothing numeric to compare, so nothing is inferred."""
        q1 = statement(
            "We are reaffirming the guidance ranges for 2026 adjusted EBITDA and adjusted free cash flow "
            "before growth, both of which we introduced on our third quarter 2025 call.",
            quarter="2026Q1", at=Q1_AT, company="VST",
        )
        q2 = statement(
            "Turning to slide nine, we are reaffirming our 2026 Adjusted EBITDA guidance range of "
            "$6.8 billion-$7.6 billion and our adjusted free cash flow before growth guidance range of "
            "$3.925 billion-$4.725 billion.",
            quarter="2026Q2", at=Q2_AT, company="VST",
        )
        revisions, unrevised = detect_revisions(claims_of(q1, q2))
        assert revisions == ()
        assert set(unrevised.values()) == {NonRevisionReason.NO_PRIOR_CLAIM}
