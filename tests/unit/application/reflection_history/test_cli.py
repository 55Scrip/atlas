"""Tests for reflection_history's CLI display (ATLAS-010).

Replaces a forbidden-vocabulary approach (which would wrongly forbid the
CLI from ever printing "Pattern"/"Strategy Signature" as neutral field
labels it must legitimately display) with direct verification of actual
behavior: complete, verbatim, untruncated display of every persisted
field, with no additional generated commentary.
"""
from __future__ import annotations

from datetime import datetime, timezone

from atlas.core.application.reflection_history.cli import _print_entry
from atlas.core.domain.decision.value_objects import DecisionId
from atlas.core.domain.reflection_response.entity import ReflectionResponse
from atlas.core.domain.reflection_response.value_objects import (
    PatternMembershipSnapshot,
    ProvenanceSnapshot,
    ResponseText,
)

_RECORDED_AT = datetime(2026, 7, 21, 9, 30, 0, tzinfo=timezone.utc)


def _make_entry() -> ReflectionResponse:
    member_id_a = DecisionId()
    member_id_b = DecisionId()
    signature_member_id = DecisionId()
    return ReflectionResponse.register(
        decision_id=DecisionId(),
        response_text=ResponseText(
            "  This time feels DIFFERENT because guidance keeps beating.  "
        ),
        provenance=ProvenanceSnapshot(
            reflection_description="You have made 2 BUY decisions on NVIDIA.",
            coaching_question_text="What's similar or different this time, if anything?",
            grounding_pattern=PatternMembershipSnapshot(
                strategy_name="same_subject_and_type",
                member_decision_ids=(member_id_a, member_id_b),
            ),
            strategy_signature_patterns=(
                PatternMembershipSnapshot(
                    strategy_name="same_confidence",
                    member_decision_ids=(signature_member_id,),
                ),
            ),
            reasoning_context_subject="NVIDIA",
            reasoning_context_decision_type="BUY",
            reasoning_context_confidence=80,
        ),
        clock=lambda: _RECORDED_AT,
    )


class TestVerbatimDisplay:
    def test_every_persisted_field_appears_completely_and_verbatim(self, capsys):
        entry = _make_entry()

        _print_entry(1, entry)

        output = capsys.readouterr().out
        provenance = entry.provenance
        assert entry.response_text.value in output
        assert provenance.reflection_description in output
        assert provenance.coaching_question_text in output
        assert provenance.grounding_pattern.strategy_name in output
        for member_id in provenance.grounding_pattern.member_decision_ids:
            assert str(member_id) in output
        for pattern in provenance.strategy_signature_patterns:
            assert pattern.strategy_name in output
            for member_id in pattern.member_decision_ids:
                assert str(member_id) in output
        assert provenance.reasoning_context_subject in output
        assert provenance.reasoning_context_decision_type in output
        assert str(provenance.reasoning_context_confidence) in output

    def test_output_is_exactly_reproducible_from_persisted_fields_and_static_labels(
        self, capsys
    ):
        entry = _make_entry()

        _print_entry(1, entry)

        output = capsys.readouterr().out
        provenance = entry.provenance
        member_ids = ", ".join(str(d) for d in provenance.grounding_pattern.member_decision_ids)
        expected = (
            f"\n1. Recorded: {entry.recorded_at.isoformat()}\n"
            f"   Response: {entry.response_text.value}\n"
            f"   Reflection: {provenance.reflection_description}\n"
            f"   Coaching Question: {provenance.coaching_question_text}\n"
            f"   Grounding Pattern: {provenance.grounding_pattern.strategy_name} "
            f"({member_ids})\n"
            "   Strategy Signature Patterns:\n"
        )
        for pattern in provenance.strategy_signature_patterns:
            pattern_member_ids = ", ".join(str(d) for d in pattern.member_decision_ids)
            expected += f"     - {pattern.strategy_name} ({pattern_member_ids})\n"
        expected += (
            f"   Reasoning Context — Subject: {provenance.reasoning_context_subject}\n"
            f"   Reasoning Context — Decision Type: "
            f"{provenance.reasoning_context_decision_type}\n"
            f"   Reasoning Context — Confidence: "
            f"{provenance.reasoning_context_confidence}\n"
        )

        assert output == expected

    def test_no_generated_commentary_appears(self, capsys):
        entry = _make_entry()

        _print_entry(1, entry)

        output = capsys.readouterr().out.lower()
        for forbidden in (
            "trend",
            "compared to",
            "this suggests",
            "conclusion",
            "overall,",
            "in summary",
            "relevance",
        ):
            assert forbidden not in output

    def test_response_text_is_not_stripped_or_normalized(self, capsys):
        entry = _make_entry()

        _print_entry(1, entry)

        output = capsys.readouterr().out
        # The original leading/trailing whitespace on response_text must
        # survive untouched — no truncation, no reformatting.
        assert "  This time feels DIFFERENT because guidance keeps beating.  " in output

    def test_no_strategy_signature_patterns_is_displayed_as_explicit_none_not_omitted(
        self, capsys
    ):
        entry = ReflectionResponse.register(
            decision_id=DecisionId(),
            response_text=ResponseText("Keeping this."),
            provenance=ProvenanceSnapshot(
                reflection_description="You have made 2 BUY decisions on NVIDIA.",
                coaching_question_text="What's similar or different this time?",
                grounding_pattern=PatternMembershipSnapshot(
                    strategy_name="same_subject_and_type",
                    member_decision_ids=(DecisionId(),),
                ),
                strategy_signature_patterns=(),
                reasoning_context_subject=None,
                reasoning_context_decision_type=None,
                reasoning_context_confidence=None,
            ),
            clock=lambda: _RECORDED_AT,
        )

        _print_entry(1, entry)

        output = capsys.readouterr().out
        assert "Strategy Signature Patterns: (none)" in output
