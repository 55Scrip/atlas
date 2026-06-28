from typer.testing import CliRunner

from atlas.cli.main import app
from atlas.decision_journal import (
    DecisionJournalEngine,
    DecisionJournalInput,
    DecisionJournalLesson,
    DecisionType,
    render_decision_journal_entry,
    render_decision_journal_review,
)
from atlas.evidence import EvidenceClaim, EvidenceInput, EvidenceSource


def test_journal_entry_captures_thesis_risks_and_evidence_quality():
    entry = DecisionJournalEngine().create_entry(_journal_input())

    assert "AI infrastructure" in entry.investment_thesis
    assert entry.main_risks
    assert entry.evidence_quality
    assert "review" in entry.evidence_summary.lower()


def test_atlas_rating_snapshot_is_stored():
    entry = DecisionJournalEngine().create_entry(_journal_input())

    assert entry.atlas_rating == "Balanced"
    assert entry.atlas_view == "Constructive"
    assert entry.atlas_fit == "Moderate Fit"
    assert entry.atlas_confidence > 0


def test_review_date_and_empty_lessons_are_included_initially():
    entry = DecisionJournalEngine().create_entry(_journal_input())

    assert entry.planned_review_date == "2026-09-30"
    assert entry.lessons_learned == ()
    rendered = render_decision_journal_entry(entry)
    assert "Lessons Learned" in rendered
    assert "None yet" in rendered


def test_journal_distinguishes_decision_quality_from_outcome():
    entry = DecisionJournalEngine().create_entry(_journal_input())
    review = DecisionJournalEngine().review_entry(entry)
    rendered = render_decision_journal_review(review)

    assert "Decision Quality" in rendered
    assert "Outcome Quality" in rendered
    assert "A good decision can have" in rendered


def test_journal_renderer_avoids_forbidden_instruction_language():
    rendered = render_decision_journal_entry(
        DecisionJournalEngine().create_entry(_journal_input())
    )

    assert "Strong Buy" not in rendered
    assert "Strong Sell" not in rendered
    assert " Buy " not in rendered
    assert " Sell " not in rendered
    assert "Guaranteed" not in rendered
    assert "Risk-free" not in rendered
    assert "Sure thing" not in rendered


def test_journal_cli_create_list_review_works_with_local_json(tmp_path):
    path = tmp_path / "decision_journal.json"
    runner = CliRunner()

    create = runner.invoke(app, ["journal", "create", "--path", str(path)])
    listed = runner.invoke(app, ["journal", "list", "--path", str(path)])
    review = runner.invoke(app, ["journal", "review", "--path", str(path)])

    assert create.exit_code == 0
    assert "Decision Journal Entry" in create.output
    assert listed.exit_code == 0
    assert "Decision Journal" in listed.output
    assert review.exit_code == 0
    assert "Decision Journal Review" in review.output


def test_language_layer_is_used():
    entry = DecisionJournalEngine().create_entry(_journal_input())

    assert entry.language_report is not None
    assert "Decision Journal Engine" in entry.language_report.engines_used


def test_evidence_quality_can_affect_confidence():
    engine = DecisionJournalEngine()
    strong = engine.create_entry(_journal_input())
    weak = engine.create_entry(
        DecisionJournalInput(
            decision_title="Weak evidence idea",
            asset_or_idea="Viral AI chart",
            decision_date="2026-06-28",
            planned_review_date="2026-09-30",
            evidence_input=EvidenceInput(
                claim=EvidenceClaim("A screenshot claims a material change."),
                source=EvidenceSource.SCREENSHOT_WITHOUT_SOURCE,
            ),
        )
    )

    assert weak.atlas_confidence < strong.atlas_confidence
    assert weak.evidence_quality in {"Unverified", "Insufficient"}


def test_lessons_can_be_added_during_review():
    entry = DecisionJournalEngine().create_entry(_journal_input())
    lesson = DecisionJournalLesson(
        summary="The process separated thesis quality from outcome quality.",
        decision_quality="Thoughtful process",
        outcome_quality="Still developing",
        behavior_to_repeat="Write assumptions before acting.",
        behavior_to_improve="Define review triggers sooner.",
    )
    review = DecisionJournalEngine().review_entry(entry, lessons=(lesson,))

    assert review.lessons_learned == (lesson,)
    assert review.status.value == "Lesson Captured"


def _journal_input() -> DecisionJournalInput:
    return DecisionJournalInput(
        decision_title="Consider AI infrastructure exposure",
        asset_or_idea="AI infrastructure",
        decision_type=DecisionType.CONSIDERING,
        decision_date="2026-06-28",
        planned_review_date="2026-09-30",
        atlas_rating="Balanced",
        atlas_view="Constructive",
        atlas_fit="Moderate Fit",
        atlas_confidence=72,
        investment_thesis=(
            "AI infrastructure appears worth monitoring because power and data "
            "center bottlenecks may shape long-term outcomes."
        ),
        key_reasons=(
            "The thesis has identifiable monitoring signals.",
            "Evidence appears sufficient for a structured journal entry.",
        ),
        main_risks=(
            "The evidence could become stale.",
            "The thesis may be too sensitive to market expectations.",
        ),
        evidence_input=EvidenceInput(
            claim=EvidenceClaim("Theme evidence is structured enough for review."),
            source=EvidenceSource.ANALYST_REPORT,
        ),
    )
