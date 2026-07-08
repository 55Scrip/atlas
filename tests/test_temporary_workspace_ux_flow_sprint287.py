"""Sprint 287 — Temporary Workspace UX Flow document tests."""

from __future__ import annotations

from pathlib import Path

import pytest

UX_DOC = Path("docs/TemporaryWorkspaceUXFlow.md")
SPEC_DOC = Path("docs/AtlasAlphaExperienceSpecification.md")
CLI_FILE = Path("atlas/cli/main.py")
ATLAS_DIR = Path("atlas")

PROHIBITED_PHRASES = [
    "strong buy",
    "buy now",
    "sell now",
    "guaranteed return",
    "must purchase",
    "must sell",
]

REQUIRED_SCREENS = [
    "Landing Screen",
    "Processing State",
    "Temporary Workspace",
    "Weekly Review Preview",
    "Snapshot Draft",
    "Save Workspace",
]

SCREEN_FIELDS = [
    "Purpose",
    "User Goal",
    "Atlas Goal",
    "Primary Content",
    "Secondary Content",
    "Available Actions",
    "Empty State",
    "Error State",
    "Success State",
    "Emotional Objective",
]

CARD_TYPES_WITH_POSITIONS = [
    "Entity Card",
    "Evidence Card",
    "Assumption Card",
    "Risk Card",
    "Open Question Card",
    "Uncertainty Card",
]

CARD_RATIONALE_PHRASES = [
    "why it exists",
    "why it appears",
    "when it is omitted",
]

ANTI_GOALS = [
    "dashboard",
    "gamification",
    "urgency",
    "prediction",
    "recommendation",
    "account wall",
]

EMOTIONAL_JOURNEY_STEPS = [
    "Landing",
    "Processing",
    "Temporary Workspace",
    "Weekly Review",
    "Snapshot Draft",
    "Save Workspace",
]

OUT_OF_SCOPE_TERMS = [
    "backend",
    "authentication",
    "api endpoint",
    "sql",
    "graphql",
]


# ---------------------------------------------------------------------------
# Document existence
# ---------------------------------------------------------------------------


class TestDocumentExists:
    def test_ux_doc_exists(self):
        assert UX_DOC.exists()

    def test_ux_doc_is_file(self):
        assert UX_DOC.is_file()

    def test_ux_doc_is_nonempty(self):
        assert UX_DOC.stat().st_size > 1000

    def test_ux_doc_is_utf8(self):
        UX_DOC.read_bytes().decode("utf-8")

    def test_ux_doc_is_markdown(self):
        assert UX_DOC.suffix == ".md"

    def test_ux_doc_has_header(self):
        content = UX_DOC.read_text(encoding="utf-8")
        assert "Temporary Workspace UX Flow" in content

    def test_ux_doc_is_complete(self):
        assert UX_DOC.stat().st_size > 8000

    def test_ux_doc_references_experience_spec(self):
        content = UX_DOC.read_text(encoding="utf-8")
        assert "AtlasAlphaExperienceSpecification.md" in content

    def test_ux_doc_answers_purpose(self):
        lower = UX_DOC.read_text(encoding="utf-8").lower()
        assert "prototype" in lower or "build" in lower or "designer" in lower


# ---------------------------------------------------------------------------
# All six screens documented
# ---------------------------------------------------------------------------


class TestAllScreensDocumented:
    @pytest.fixture(autouse=True)
    def load_doc(self):
        self.content = UX_DOC.read_text(encoding="utf-8")

    @pytest.mark.parametrize("screen", REQUIRED_SCREENS)
    def test_screen_present(self, screen: str):
        assert screen.lower() in self.content.lower(), f"Screen missing: {screen!r}"

    def test_landing_screen_documented(self):
        lower = self.content.lower()
        assert "landing screen" in lower or "landing" in lower

    def test_processing_state_documented(self):
        lower = self.content.lower()
        assert "processing state" in lower or "processing" in lower

    def test_temporary_workspace_screen_documented(self):
        lower = self.content.lower()
        assert "temporary workspace" in lower

    def test_weekly_review_preview_documented(self):
        lower = self.content.lower()
        assert "weekly review preview" in lower

    def test_snapshot_draft_preview_documented(self):
        lower = self.content.lower()
        assert "snapshot draft" in lower

    def test_save_workspace_prompt_documented(self):
        lower = self.content.lower()
        assert "save workspace" in lower

    def test_screens_in_logical_order(self):
        lower = self.content.lower()
        landing = lower.index("# screen 1") if "# screen 1" in lower else lower.index("landing screen")
        processing = lower.index("# screen 2") if "# screen 2" in lower else lower.index("processing state")
        workspace = lower.index("# screen 3") if "# screen 3" in lower else lower.rindex("temporary workspace")
        assert landing < processing < workspace


# ---------------------------------------------------------------------------
# Screen fields documented
# ---------------------------------------------------------------------------


class TestScreenFieldsDocumented:
    @pytest.fixture(autouse=True)
    def load_doc(self):
        self.content = UX_DOC.read_text(encoding="utf-8")

    @pytest.mark.parametrize("field", SCREEN_FIELDS)
    def test_field_present(self, field: str):
        assert field.lower() in self.content.lower(), f"Screen field missing: {field!r}"

    def test_purpose_documented_for_each_screen(self):
        count = self.content.lower().count("## purpose")
        assert count >= 5

    def test_user_goal_documented(self):
        lower = self.content.lower()
        assert "user goal" in lower

    def test_atlas_goal_documented(self):
        lower = self.content.lower()
        assert "atlas goal" in lower

    def test_emotional_objective_for_each_screen(self):
        count = self.content.lower().count("emotional objective")
        assert count >= 5

    def test_available_actions_documented(self):
        lower = self.content.lower()
        assert "available actions" in lower

    def test_user_question_documented(self):
        lower = self.content.lower()
        assert "user question" in lower

    def test_earn_next_interaction_documented(self):
        lower = self.content.lower()
        assert "earn" in lower and "interaction" in lower


# ---------------------------------------------------------------------------
# Landing screen
# ---------------------------------------------------------------------------


class TestLandingScreenDocumented:
    @pytest.fixture(autouse=True)
    def load_doc(self):
        self.content = UX_DOC.read_text(encoding="utf-8")
        self.lower = self.content.lower()

    def test_headline_specified(self):
        assert "headline" in self.lower

    def test_supporting_text_specified(self):
        assert "supporting text" in self.lower

    def test_paste_box_specified(self):
        assert "paste box" in self.lower

    def test_placeholder_text_specified(self):
        assert "placeholder" in self.lower

    def test_examples_specified(self):
        assert "example" in self.lower

    def test_privacy_messaging_specified(self):
        assert "privacy" in self.lower or "nothing is stored" in self.lower

    def test_no_account_messaging_specified(self):
        assert "no account" in self.lower or "account required" in self.lower

    def test_submit_button_specified(self):
        assert "analyse" in self.lower or "submit" in self.lower

    def test_empty_paste_box_behaviour_specified(self):
        assert "empty paste box" in self.lower or "empty" in self.lower

    def test_no_error_on_empty_submit(self):
        assert "no error" in self.lower or "no error message" in self.lower or "not alarming" in self.lower

    def test_landing_has_no_navigation_bar(self):
        assert "no navigation" in self.lower or "minimal" in self.lower

    def test_example_chips_specified(self):
        assert "chip" in self.lower or "clickable" in self.lower

    def test_three_example_inputs_specified(self):
        count = self.lower.count(">`")
        assert count >= 3 or "three" in self.lower


# ---------------------------------------------------------------------------
# Processing state
# ---------------------------------------------------------------------------


class TestProcessingStateDocumented:
    @pytest.fixture(autouse=True)
    def load_doc(self):
        self.content = UX_DOC.read_text(encoding="utf-8")
        self.lower = self.content.lower()

    def test_progress_statement_specified(self):
        assert "progress statement" in self.lower or "reading your input" in self.lower

    def test_no_ai_thinking_language(self):
        if "ai thinking" in self.lower:
            assert "not" in self.lower or "avoid" in self.lower

    def test_three_progress_lines(self):
        assert "reading your input" in self.lower
        assert "finding" in self.lower
        assert "structuring" in self.lower

    def test_no_spinner(self):
        assert "no spinner" in self.lower or "not a spinner" in self.lower or "spinner" not in self.lower

    def test_no_progress_bar(self):
        assert "no percentage" in self.lower or "no progress bar" in self.lower or "no animation beyond" in self.lower

    def test_crossfade_transition(self):
        assert "crossfade" in self.lower or "fade" in self.lower

    def test_long_wait_fallback_specified(self):
        assert "3 second" in self.lower or "seconds" in self.lower

    def test_error_state_specified(self):
        assert "input has not been lost" in self.lower or "has not been lost" in self.lower

    def test_what_lines_must_not_say(self):
        assert "must not say" in self.lower or "must not" in self.lower


# ---------------------------------------------------------------------------
# Temporary workspace screen
# ---------------------------------------------------------------------------


class TestTemporaryWorkspaceScreenDocumented:
    @pytest.fixture(autouse=True)
    def load_doc(self):
        self.content = UX_DOC.read_text(encoding="utf-8")
        self.lower = self.content.lower()

    def test_layout_zones_specified(self):
        assert "header zone" in self.lower or "card zone" in self.lower

    def test_three_zones_specified(self):
        assert "header zone" in self.lower and "card zone" in self.lower and "footer zone" in self.lower

    def test_status_badge_specified(self):
        assert "status badge" in self.lower or "temporary · not saved" in self.lower

    def test_summary_line_specified(self):
        assert "summary line" in self.lower or "atlas found" in self.lower

    def test_first_aha_moment_specified(self):
        lower = self.lower
        assert "aha" in lower

    def test_aha_timing_specified(self):
        assert "90 second" in self.lower or "first 90" in self.lower

    def test_card_zone_is_scrollable(self):
        assert "scrollable" in self.lower

    def test_header_stays_visible_while_scrolling(self):
        assert "stays visible" in self.lower or "fixed" in self.lower or "sticky" in self.lower

    @pytest.mark.parametrize("card_type", CARD_TYPES_WITH_POSITIONS)
    def test_card_type_documented(self, card_type: str):
        assert card_type.lower() in self.lower, f"Card type missing: {card_type!r}"

    @pytest.mark.parametrize("rationale", CARD_RATIONALE_PHRASES)
    def test_card_rationale_documented(self, rationale: str):
        assert rationale.lower() in self.lower, f"Card rationale phrase missing: {rationale!r}"

    def test_card_ordering_specified(self):
        lower = self.lower
        pos1 = lower.index("position 1") if "position 1" in lower else lower.index("entity card")
        pos2 = lower.index("position 2") if "position 2" in lower else lower.index("evidence card")
        pos3 = lower.index("position 3") if "position 3" in lower else lower.index("assumption card")
        pos4 = lower.index("position 4") if "position 4" in lower else lower.index("risk card")
        assert pos1 < pos2 < pos3 < pos4

    def test_disambiguation_card_specified(self):
        assert "disambiguation" in self.lower

    def test_second_person_for_assumptions(self):
        assert "second person" in self.lower or "you are assuming" in self.lower

    def test_no_scores_on_cards(self):
        assert "no score" in self.lower or "scores" in self.lower and "must not" in self.lower

    def test_no_probability_on_cards(self):
        assert "probability estimate" in self.lower or "no probability" in self.lower

    def test_no_action_recommendations_on_cards(self):
        assert "no action" in self.lower or "must not contain" in self.lower

    def test_expand_behaviour_specified(self):
        assert "expand" in self.lower

    def test_first_assumption_card_pre_expanded(self):
        assert "pre-expanded" in self.lower or "expanded" in self.lower


# ---------------------------------------------------------------------------
# Weekly review preview
# ---------------------------------------------------------------------------


class TestWeeklyReviewPreviewDocumented:
    @pytest.fixture(autouse=True)
    def load_doc(self):
        self.content = UX_DOC.read_text(encoding="utf-8")
        self.lower = self.content.lower()

    def test_weekly_review_preview_section_present(self):
        assert "weekly review preview" in self.lower

    def test_when_it_appears_specified(self):
        assert "when it appears" in self.lower

    def test_appears_inline(self):
        assert "inline" in self.lower

    def test_trigger_conditions_specified(self):
        assert "45 second" in self.lower or "two entity" in self.lower or "at least" in self.lower

    def test_preview_header_specified(self):
        assert "preview" in self.lower and "based on current workspace" in self.lower or "based on" in self.lower

    def test_sections_not_shown_specified(self):
        assert "sections not" in self.lower or "not yet available" in self.lower

    def test_quiet_link_affordance(self):
        assert "quiet" in self.lower

    def test_expected_user_reaction_documented(self):
        assert "expected user reaction" in self.lower

    def test_adds_more_grows_stated(self):
        assert "grows" in self.lower or "add more" in self.lower


# ---------------------------------------------------------------------------
# Snapshot draft preview
# ---------------------------------------------------------------------------


class TestSnapshotDraftPreviewDocumented:
    @pytest.fixture(autouse=True)
    def load_doc(self):
        self.content = UX_DOC.read_text(encoding="utf-8")
        self.lower = self.content.lower()

    def test_snapshot_draft_section_present(self):
        assert "snapshot draft" in self.lower

    def test_when_it_appears_specified(self):
        assert "when it appears" in self.lower

    def test_trigger_conditions_specified(self):
        assert "price observation" in self.lower or "order" in self.lower

    def test_three_actions_specified(self):
        assert "confirm" in self.lower and "edit" in self.lower and "discard" in self.lower

    def test_three_actions_equally_prominent(self):
        assert "equally prominent" in self.lower or "none is pre-selected" in self.lower

    def test_confirmed_state_specified(self):
        assert "confirmed" in self.lower

    def test_unconfirmed_state_specified(self):
        assert "unconfirmed" in self.lower

    def test_discard_state_specified(self):
        assert "discarded" in self.lower or "discard" in self.lower

    def test_undo_link_specified(self):
        assert "undo" in self.lower

    def test_undo_timing_specified(self):
        assert "5 second" in self.lower

    def test_low_confidence_state_specified(self):
        assert "low confidence" in self.lower or "confidence:  low" in self.lower or "low" in self.lower

    def test_never_comments_on_price_quality(self):
        lower = self.lower
        assert "commentary" in lower or "must not contain" in lower

    def test_card_appears_between_evidence_and_assumption(self):
        lower = self.lower
        assert "between evidence" in lower or "between" in lower and "evidence" in lower and "assumption" in lower

    def test_expected_user_reaction_documented(self):
        assert "expected user reaction" in self.lower


# ---------------------------------------------------------------------------
# Save workspace prompt
# ---------------------------------------------------------------------------


class TestSaveWorkspacePromptDocumented:
    @pytest.fixture(autouse=True)
    def load_doc(self):
        self.content = UX_DOC.read_text(encoding="utf-8")
        self.lower = self.content.lower()

    def test_save_workspace_section_present(self):
        assert "save workspace" in self.lower

    def test_when_it_appears_specified(self):
        assert "when it appears" in self.lower

    def test_timing_conditions_specified(self):
        assert "60 second" in self.lower

    def test_prompt_is_not_modal(self):
        assert "not a modal" in self.lower or "not modal" in self.lower or "sticky footer" in self.lower

    def test_prompt_does_not_block(self):
        assert "never blocking" in self.lower or "not blocking" in self.lower or "blocking" not in self.lower

    def test_two_equally_prominent_actions(self):
        assert "equally prominent" in self.lower

    def test_continue_without_saving_option(self):
        assert "continue without saving" in self.lower

    def test_local_storage_specified(self):
        assert "local storage" in self.lower or "browser" in self.lower

    def test_no_server_before_account(self):
        assert "no server" in self.lower or "browser" in self.lower and "not" in self.lower

    def test_why_account_offered_here_specified(self):
        assert "why this is the first time" in self.lower or "first time" in self.lower

    def test_account_only_after_value(self):
        assert "after" in self.lower and "value" in self.lower

    def test_footer_before_conditions_specified(self):
        assert "before save prompt conditions" in self.lower or "before" in self.lower and "conditions" in self.lower

    def test_footer_after_conditions_specified(self):
        assert "after save prompt conditions" in self.lower or "after" in self.lower and "conditions" in self.lower

    def test_save_error_state_specified(self):
        assert "save to local storage fails" in self.lower or "storage quota" in self.lower

    def test_no_account_suggested_on_save_error(self):
        lower = self.lower
        assert "no account creation" in lower or "not suggested" in lower or "not" in lower


# ---------------------------------------------------------------------------
# Emotional journey map
# ---------------------------------------------------------------------------


class TestEmotionalJourneyMapDocumented:
    @pytest.fixture(autouse=True)
    def load_doc(self):
        self.content = UX_DOC.read_text(encoding="utf-8")
        self.lower = self.content.lower()

    def test_emotional_journey_map_present(self):
        assert "emotional journey" in self.lower or "journey map" in self.lower

    @pytest.mark.parametrize("step", EMOTIONAL_JOURNEY_STEPS)
    def test_journey_step_present(self, step: str):
        assert step.lower() in self.lower, f"Journey step missing: {step!r}"

    def test_user_question_column_present(self):
        assert "question" in self.lower and "user" in self.lower

    def test_earns_next_interaction_column(self):
        assert "earn" in self.lower


# ---------------------------------------------------------------------------
# Anti-goals applied
# ---------------------------------------------------------------------------


class TestAntiGoalsApplied:
    @pytest.fixture(autouse=True)
    def load_doc(self):
        self.content = UX_DOC.read_text(encoding="utf-8")
        self.lower = self.content.lower()

    def test_anti_goals_section_present(self):
        assert "anti-goal" in self.lower

    @pytest.mark.parametrize("goal", ANTI_GOALS)
    def test_anti_goal_addressed(self, goal: str):
        assert goal.lower() in self.lower, f"Anti-goal missing: {goal!r}"

    def test_no_dashboards_addressed(self):
        assert "dashboard" in self.lower

    def test_no_gamification_addressed(self):
        assert "gamification" in self.lower

    def test_no_urgency_addressed(self):
        assert "urgency" in self.lower

    def test_no_account_walls_addressed(self):
        assert "account wall" in self.lower

    def test_prediction_language_anti_goal(self):
        assert "prediction" in self.lower

    def test_no_recommendations_anti_goal(self):
        assert "recommendation" in self.lower


# ---------------------------------------------------------------------------
# No runtime code
# ---------------------------------------------------------------------------


class TestNoRuntimeCode:
    def test_no_python_imports_in_doc(self):
        content = UX_DOC.read_text(encoding="utf-8")
        assert "import atlas" not in content
        assert "from atlas" not in content

    def test_atlas_dir_not_modified(self):
        for py_file in ATLAS_DIR.rglob("*.py"):
            text = py_file.read_text(encoding="utf-8")
            assert "ux_flow" not in text, f"Sprint 287 runtime code found in {py_file}"

    def test_no_cli_changes(self):
        cli_source = CLI_FILE.read_text(encoding="utf-8")
        assert "ux_flow" not in cli_source

    @pytest.mark.parametrize("term", OUT_OF_SCOPE_TERMS)
    def test_no_implementation_technology(self, term: str):
        content = UX_DOC.read_text(encoding="utf-8").lower()
        assert term not in content, f"Out-of-scope technology term found: {term!r}"


# ---------------------------------------------------------------------------
# Safe language
# ---------------------------------------------------------------------------


class TestSafeLanguage:
    @pytest.fixture(autouse=True)
    def load_doc(self):
        self.content = UX_DOC.read_text(encoding="utf-8").lower()

    @pytest.mark.parametrize("phrase", PROHIBITED_PHRASES)
    def test_no_prohibited_phrase(self, phrase: str):
        assert phrase.lower() not in self.content, f"Prohibited phrase found: {phrase!r}"

    def test_no_buy_word(self):
        words = self.content.split()
        assert "buy" not in words

    def test_no_sell_word(self):
        words = self.content.split()
        assert "sell" not in words

    def test_no_action_recommendation(self):
        assert "you should invest" not in self.content

    def test_no_guaranteed_returns(self):
        assert "guaranteed" not in self.content

    def test_no_price_prediction(self):
        assert "stock will" not in self.content


# ---------------------------------------------------------------------------
# Cross-document consistency
# ---------------------------------------------------------------------------


class TestCrossDocumentConsistency:
    def test_spec_doc_unchanged(self):
        content = SPEC_DOC.read_text(encoding="utf-8")
        assert "Atlas Alpha" in content

    def test_cli_unchanged(self):
        cli_source = CLI_FILE.read_text(encoding="utf-8")
        assert "ux_flow" not in cli_source

    def test_ux_doc_references_card_rendering_contract(self):
        content = UX_DOC.read_text(encoding="utf-8")
        assert "TemporaryWorkspaceCardRenderingContract.md" in content or "card rendering" in content.lower()

    def test_ux_doc_references_experience_specification(self):
        content = UX_DOC.read_text(encoding="utf-8")
        assert "AtlasAlphaExperienceSpecification.md" in content

    def test_sprint_288_recommendation_present(self):
        content = UX_DOC.read_text(encoding="utf-8")
        assert "288" in content

    def test_wireframes_recommended_next(self):
        lower = UX_DOC.read_text(encoding="utf-8").lower()
        assert "wireframe" in lower


# ---------------------------------------------------------------------------
# Decision log and release candidate updated
# ---------------------------------------------------------------------------


class TestDocumentationUpdated:
    def test_decision_log_mentions_sprint_287(self):
        log = Path("docs/DecisionLog.md").read_text(encoding="utf-8")
        assert "287" in log

    def test_decision_log_mentions_ux_flow(self):
        log = Path("docs/DecisionLog.md").read_text(encoding="utf-8").lower()
        assert "ux flow" in log or "experience" in log

    def test_rc_doc_mentions_sprint_287(self):
        rc = Path("docs/InternalV1ReleaseCandidate.md").read_text(encoding="utf-8")
        assert "287" in rc

    def test_rc_doc_sprint_287_entry_no_forbidden_language(self):
        rc = Path("docs/InternalV1ReleaseCandidate.md").read_text(encoding="utf-8")
        sprint_287_idx = rc.find("Sprint 287")
        if sprint_287_idx == -1:
            pytest.skip("Sprint 287 entry not found in RC doc")
        sprint_288_idx = rc.find("Sprint 288", sprint_287_idx)
        if sprint_288_idx == -1:
            chunk = rc[sprint_287_idx:]
        else:
            chunk = rc[sprint_287_idx:sprint_288_idx]
        for phrase in ["buy", "sell"]:
            words = chunk.lower().split()
            assert phrase not in words, f"Forbidden word {phrase!r} found in Sprint 287 RC entry"

    def test_ux_flow_doc_present(self):
        assert UX_DOC.exists()
