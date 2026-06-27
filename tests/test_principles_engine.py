from typer.testing import CliRunner

from atlas.cli.main import app
from atlas.conversation import ConversationIntent, ConversationResponse
from atlas.principles import (
    PrincipleCategory,
    PrinciplesEngine,
    PrinciplesResult,
    check_conversation_response,
    check_text_against_principles,
    render_principles_check,
)


def test_principles_engine_passes_contextual_profile_first_text():
    text = (
        "Given the investor profile, portfolio context, and long-term time horizon, "
        "this appears compatible with the stated objectives. The main risk is "
        "volatility, and the assumption is that missing information remains limited. "
        "There is not enough information to be certain, so Atlas would monitor the "
        "position and explain why the view is consistent with the profile."
    )

    check = PrinciplesEngine().check(text)

    assert check.overall_result == PrinciplesResult.PASS
    assert not check.guardrail_warnings
    followed_categories = {item.principle.category for item in check.principles_followed}
    assert PrincipleCategory.USER_FIRST in followed_categories
    assert PrincipleCategory.RISK_BEFORE_RETURN in followed_categories
    assert PrincipleCategory.HUMILITY in followed_categories


def test_principles_engine_flags_prohibited_language():
    check = PrinciplesEngine().check("Buy this now. It is guaranteed and risk-free.")

    assert check.overall_result == PrinciplesResult.FAIL
    assert any("buy" in warning.lower() for warning in check.guardrail_warnings)
    assert any("guaranteed" in warning.lower() for warning in check.guardrail_warnings)
    assert any("risk free" in warning.lower() for warning in check.guardrail_warnings)


def test_principles_engine_ignores_clearly_quoted_external_language():
    check = PrinciplesEngine().check(
        'The headline says "Strong Buy", but Atlas says there is not enough '
        "information and this depends on the investor profile."
    )

    assert not check.guardrail_warnings
    assert check.overall_result != PrinciplesResult.FAIL


def test_conversation_helper_validates_response_text():
    response = ConversationResponse(
        intent=ConversationIntent.GENERAL_INVESTMENT_GUIDANCE,
        short_answer="This depends on the investor profile and portfolio context.",
        supporting_reasoning=(
            "Risk, assumptions, and missing information should be reviewed first.",
            "Atlas would monitor consistency with the long-term objectives.",
        ),
        engines_used=("Conversation Engine",),
        confidence=72,
        suggested_follow_up_questions=("What risks matter most?",),
    )

    check = check_conversation_response(response)

    assert check.overall_result == PrinciplesResult.PASS
    assert check.confidence > 60


def test_principles_renderer_and_cli_output():
    check = check_text_against_principles("Buy this. It can't lose.")
    rendered = render_principles_check(check)

    assert "Atlas Principles Check" in rendered
    assert "Overall Principles Result: Fail" in rendered
    assert "Guardrail Warnings" in rendered

    runner = CliRunner()
    result = runner.invoke(
        app,
        ["principles", "check", "This depends on the investor profile and risk context."],
    )

    assert result.exit_code == 0
    assert "Atlas Principles Check" in result.output
    assert "Overall Principles Result" in result.output
