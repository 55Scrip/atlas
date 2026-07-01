from typer.testing import CliRunner

from atlas.cli.main import app
from atlas.evidence import (
    EvidenceAction,
    EvidenceClaim,
    EvidenceInput,
    EvidenceQualityEngine,
    EvidenceSource,
    EvidenceStrength,
    render_evidence_assessment,
)


def test_audited_reports_are_treated_as_strong_evidence():
    assessment = EvidenceQualityEngine().assess(
        EvidenceInput(
            claim=EvidenceClaim("Audited revenue disclosure changed materially."),
            source=EvidenceSource.AUDITED_ANNUAL_REPORT,
        )
    )

    assert assessment.strength == EvidenceStrength.VERY_STRONG
    assert "Primary evidence" in assessment.rationale.primary_or_secondary
    assert assessment.confidence_impact > 0


def test_company_filings_are_treated_as_strong_evidence():
    assessment = EvidenceQualityEngine().assess(
        EvidenceInput(
            claim=EvidenceClaim("A filing shows lower reported margins."),
            source=EvidenceSource.REGULATORY_FILING,
        )
    )

    assert assessment.strength == EvidenceStrength.VERY_STRONG
    assert "regulatory" in assessment.rationale.why_strength.lower()


def test_tiktok_and_screenshots_are_weak_or_unverified():
    video = EvidenceQualityEngine().assess(
        EvidenceInput(
            claim=EvidenceClaim("A short video claims demand collapsed."),
            source=EvidenceSource.SHORT_FORM_VIDEO,
        )
    )
    screenshot = EvidenceQualityEngine().assess(
        EvidenceInput(
            claim=EvidenceClaim("A screenshot shows a dramatic chart."),
            source=EvidenceSource.SCREENSHOT_WITHOUT_SOURCE,
        )
    )

    assert video.strength == EvidenceStrength.VERY_WEAK
    assert screenshot.strength == EvidenceStrength.UNVERIFIED
    assert screenshot.action == EvidenceAction.REQUEST_SOURCE


def test_weak_social_claims_do_not_change_atlas_view_directly():
    assessment = EvidenceQualityEngine().assess(
        EvidenceInput(
            claim=EvidenceClaim(
                "A social post says the thesis is wrong.",
                materially_contradicts_current_view=True,
            ),
            source=EvidenceSource.SOCIAL_MEDIA_POST,
        )
    )

    assert assessment.should_change_view is False
    assert assessment.action in {
        EvidenceAction.REDUCE_CONFIDENCE,
        EvidenceAction.MONITOR_FOR_CONFIRMATION,
    }
    assert "not enough to change Atlas' view" in assessment.atlas_response


def test_strong_contradictory_evidence_can_trigger_update_assessment():
    assessment = EvidenceQualityEngine().assess(
        EvidenceInput(
            claim=EvidenceClaim(
                "A filing contradicts the current margin assumption.",
                materially_contradicts_current_view=True,
            ),
            source=EvidenceSource.REGULATORY_FILING,
        )
    )

    assert assessment.action == EvidenceAction.UPDATE_ASSESSMENT
    assert assessment.should_change_view is True
    assert assessment.confidence_impact < 0


def test_missing_source_triggers_request_source():
    assessment = EvidenceQualityEngine().assess(
        EvidenceInput(
            claim=EvidenceClaim("A user says a key data point changed."),
            source=EvidenceSource.UNKNOWN_SOURCE,
        )
    )

    assert assessment.action == EvidenceAction.REQUEST_SOURCE
    assert assessment.strength == EvidenceStrength.INSUFFICIENT
    assert "Original source" in assessment.rationale.additional_data_needed[0]


def test_evidence_assessments_include_rationale_and_can_reduce_confidence():
    assessment = EvidenceQualityEngine().assess(
        EvidenceInput(
            claim=EvidenceClaim("A stale analyst note raises a concern."),
            source=EvidenceSource.ANALYST_REPORT,
            is_recent=False,
        )
    )

    assert assessment.rationale.why_strength
    assert assessment.rationale.additional_data_needed
    assert assessment.confidence_impact < 0


def test_evidence_renderer_avoids_forbidden_instruction_language():
    rendered = render_evidence_assessment(EvidenceQualityEngine().example_assessment())

    assert "Atlas Evidence Quality Assessment" in rendered
    assert "Evidence Strength" in rendered
    assert "Strong Buy" not in rendered
    assert "Strong Sell" not in rendered
    assert " Buy " not in rendered
    assert " Sell " not in rendered
    assert "Guaranteed" not in rendered
    assert "Risk-free" not in rendered


def test_language_layer_integration_works_lightly():
    assessment = EvidenceQualityEngine().assess(
        EvidenceInput(
            claim=EvidenceClaim("Exchange data confirms a liquidity signal."),
            source=EvidenceSource.EXCHANGE_DATA,
        )
    )

    assert assessment.language_report is not None
    assert "Evidence Quality Engine" in assessment.language_report.engines_used
    assert assessment.language_report.confidence.missing_information


def test_evidence_cli_command_is_retired():
    # Sprint 86: atlas evidence assess command body retired — no longer a valid command
    result = CliRunner().invoke(app, ["evidence", "assess"])
    assert result.exit_code != 0
