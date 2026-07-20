"""Tests for DomainObjectType (DO-IMP-002).

Corrected per docs/atlas_domain_object_architecture/
Domain-Object-Type-Set-Discrepancy-Investigation.md, Outcome 1: OE-002
§4's own closed Domain Object Set — Observation, Knowledge Reference,
Reasoning Trace, Judgment, Decision, Outcome — remains controlling.
Case is excluded: it is the ownership boundary (OE-002 §3.1), not a
member of the closed set, and not reference-eligible.
"""
from __future__ import annotations

import pytest

from atlas.core.domain.shared.domain_object_type import DomainObjectType
from atlas.core.domain.shared.exceptions import UnknownDomainObjectTypeError

_ADOPTED = {
    "Observation": DomainObjectType.OBSERVATION,
    "KnowledgeReference": DomainObjectType.KNOWLEDGE_REFERENCE,
    "ReasoningTrace": DomainObjectType.REASONING_TRACE,
    "Judgment": DomainObjectType.JUDGMENT,
    "Decision": DomainObjectType.DECISION,
    "Outcome": DomainObjectType.OUTCOME,
}

_REJECTED_LEGACY_OR_NON_ADOPTED = [
    "ReasoningAct",
    "Candidate",
    "Hypothesis",
    "Evaluation",
    "Learning",
    "Evidence",
    "Case",  # the ownership boundary (OE-002 §3.1) — not a reference target
    "Question",
    "Interpretation",
    "Conclusion",
    "reasoning_link",
    "case",  # wrong casing is not an alias
    "observation",
    "decision",
    "",
    "Something else entirely",
]


class TestExactlySixAdoptedValues:
    def test_cardinality_is_exactly_six(self):
        assert len(list(DomainObjectType)) == 6

    def test_the_exact_set_matches_oe_002_section_4(self):
        assert {member.value for member in DomainObjectType} == {
            "Observation",
            "KnowledgeReference",
            "ReasoningTrace",
            "Judgment",
            "Decision",
            "Outcome",
        }

    @pytest.mark.parametrize("canonical_value,member", list(_ADOPTED.items()))
    def test_every_adopted_type_is_accepted(self, canonical_value, member):
        assert DomainObjectType.parse(canonical_value) is member

    def test_no_aliases_exist(self):
        # Every member's own .value is a distinct string; nothing maps
        # two different accepted strings onto the same member.
        values = [member.value for member in DomainObjectType]
        assert len(values) == len(set(values))


class TestCaseIsAbsent:
    def test_case_is_not_a_member_by_name(self):
        assert not hasattr(DomainObjectType, "CASE")

    def test_case_is_not_a_member_by_value(self):
        assert "Case" not in {member.value for member in DomainObjectType}

    def test_parsing_case_is_rejected(self):
        with pytest.raises(UnknownDomainObjectTypeError):
            DomainObjectType.parse("Case")


class TestCanonicalSerialization:
    @pytest.mark.parametrize("canonical_value,member", list(_ADOPTED.items()))
    def test_value_serializes_to_its_own_canonical_string(self, canonical_value, member):
        # `.value` is the canonical serialized form (what Pydantic and
        # any future persistence layer store/emit). `str(member)`, by
        # contrast, is NOT: a manual `(str, Enum)` mixin (matching this
        # codebase's own existing precedent — DecisionType,
        # DecisionSource, evidence.Direction — none of which is Python
        # 3.11's built-in `enum.StrEnum`) uses Enum's own __str__,
        # yielding "DomainObjectType.OBSERVATION" rather than
        # "Observation". Only `.value` — and direct string equality,
        # since `str, Enum` members compare equal to their own value —
        # is canonical.
        assert member.value == canonical_value
        assert member == canonical_value

    def test_observation_serializes_canonically(self):
        assert DomainObjectType.OBSERVATION.value == "Observation"


class TestCanonicalParsing:
    @pytest.mark.parametrize("canonical_value,member", list(_ADOPTED.items()))
    def test_parse_returns_the_matching_member(self, canonical_value, member):
        assert DomainObjectType.parse(canonical_value) == member

    def test_observation_parses_canonically(self):
        assert DomainObjectType.parse("Observation") is DomainObjectType.OBSERVATION

    @pytest.mark.parametrize("rejected", _REJECTED_LEGACY_OR_NON_ADOPTED)
    def test_parse_rejects_unknown_or_non_adopted_values(self, rejected):
        with pytest.raises(UnknownDomainObjectTypeError):
            DomainObjectType.parse(rejected)


class TestEqualityIsStable:
    def test_same_member_is_equal_to_itself(self):
        assert DomainObjectType.DECISION == DomainObjectType.DECISION

    def test_different_members_are_not_equal(self):
        assert DomainObjectType.DECISION != DomainObjectType.OUTCOME

    def test_member_equals_its_own_canonical_string(self):
        # (str, Enum): this is deliberate and matches this codebase's own
        # precedent (DecisionType, DecisionSource, evidence.Direction).
        assert DomainObjectType.DECISION == "Decision"
