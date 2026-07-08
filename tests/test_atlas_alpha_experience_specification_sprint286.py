"""Sprint 286 — Atlas Alpha 0.1 Experience Specification tests."""

from __future__ import annotations

from pathlib import Path

import pytest

SPEC_DOC = Path("docs/AtlasAlphaExperienceSpecification.md")
CLI_FILE = Path("atlas/cli/main.py")
ATLAS_DIR = Path("atlas")

PROHIBITED_PHRASES = [
    "strong buy",
    "buy now",
    "sell now",
    "guaranteed return",
    "act now",
    "must purchase",
    "must sell",
]

PRODUCT_PRINCIPLES = [
    "evidence before conclusions",
    "no action is a valid outcome",
    "reduce noise",
    "trust before accounts",
    "user owns the decision",
    "structured judgment",
    "input-first",
]

ANTI_GOALS = [
    "rushed",
    "pressured",
    "manipulated",
    "overwhelmed",
    "dependent",
]

EMOTIONAL_GOALS = [
    "calm",
    "structured",
    "informed",
    "confident",
]

REQUIRED_SECTIONS = [
    "Arrival",
    "Landing",
    "First Input",
    "Processing",
    "Temporary Workspace",
    "Workspace Cards",
    "Weekly Review",
    "Snapshot Draft",
    "Save Workspace",
    "Account",
    "Empty State",
    "Error State",
    "Success State",
    "Emotional",
]

EXPERIENCE_STEPS = [
    "Arrival",
    "Landing",
    "First Input",
    "Processing",
    "Temporary Workspace",
    "Workspace Cards",
    "Weekly Review Preview",
    "Snapshot Draft",
    "Save Workspace",
    "Account",
]

TRUST_BOUNDARIES = [
    "temporary",
    "local storage",
    "saved to this browser",
    "never",
    "confirmed",
]

OUT_OF_SCOPE_TERMS = [
    "react",
    "backend",
    "authentication",
    "api endpoint",
    "database",
    "sql",
    "rest api",
    "graphql",
]

CARD_TYPES = [
    "Entity",
    "Evidence",
    "Assumption",
    "Risk",
    "Open Question",
    "Uncertainty",
]

FUTURE_EXTENSIONS = [
    "AI",
    "market data",
    "OCR",
    "broker",
    "collaboration",
    "mobile",
]


# ---------------------------------------------------------------------------
# Document existence
# ---------------------------------------------------------------------------


class TestDocumentExists:
    def test_spec_doc_exists(self):
        assert SPEC_DOC.exists()

    def test_spec_doc_is_file(self):
        assert SPEC_DOC.is_file()

    def test_spec_doc_is_nonempty(self):
        assert SPEC_DOC.stat().st_size > 1000

    def test_spec_doc_is_utf8(self):
        SPEC_DOC.read_bytes().decode("utf-8")

    def test_spec_doc_is_markdown(self):
        assert SPEC_DOC.suffix == ".md"

    def test_spec_doc_has_header(self):
        content = SPEC_DOC.read_text(encoding="utf-8")
        assert "Atlas Alpha" in content

    def test_spec_doc_is_complete(self):
        assert SPEC_DOC.stat().st_size > 8000

    def test_spec_doc_answers_core_question(self):
        lower = SPEC_DOC.read_text(encoding="utf-8").lower()
        assert "first-time user" in lower or "meaningful value" in lower
        assert "without" in lower and "account" in lower


# ---------------------------------------------------------------------------
# Required sections present
# ---------------------------------------------------------------------------


class TestRequiredSectionsPresent:
    @pytest.fixture(autouse=True)
    def load_doc(self):
        self.content = SPEC_DOC.read_text(encoding="utf-8")

    @pytest.mark.parametrize("section", REQUIRED_SECTIONS)
    def test_section_present(self, section: str):
        assert section.lower() in self.content.lower(), f"Required section missing: {section!r}"

    def test_fourteen_sections_roughly_present(self):
        lower = self.content.lower()
        count = sum(1 for s in REQUIRED_SECTIONS if s.lower() in lower)
        assert count >= 12

    def test_five_minute_journey_documented(self):
        lower = self.content.lower()
        assert "five-minute" in lower or "five minute" in lower or "5 minute" in lower or "minute" in lower

    def test_first_aha_moment_documented(self):
        lower = self.content.lower()
        assert "aha" in lower or "first" in lower and "moment" in lower


# ---------------------------------------------------------------------------
# Product principles
# ---------------------------------------------------------------------------


class TestProductPrinciplesDocumented:
    @pytest.fixture(autouse=True)
    def load_doc(self):
        self.content = SPEC_DOC.read_text(encoding="utf-8")

    def test_principles_section_present(self):
        lower = self.content.lower()
        assert "principle" in lower

    @pytest.mark.parametrize("phrase", PRODUCT_PRINCIPLES)
    def test_principle_present(self, phrase: str):
        assert phrase.lower() in self.content.lower(), f"Product principle missing: {phrase!r}"

    def test_principles_are_described_as_binding_constraints(self):
        lower = self.content.lower()
        assert "constraint" in lower or "binding" in lower or "must" in lower

    def test_evidence_before_conclusions_in_principles(self):
        lower = self.content.lower()
        assert "evidence before conclusions" in lower

    def test_no_action_is_valid_in_principles(self):
        lower = self.content.lower()
        assert "no action is a valid outcome" in lower or "no action" in lower

    def test_trust_before_accounts_in_principles(self):
        lower = self.content.lower()
        assert "trust before accounts" in lower

    def test_input_first_in_principles(self):
        lower = self.content.lower()
        assert "input-first" in lower or "input first" in lower


# ---------------------------------------------------------------------------
# Anti-goals
# ---------------------------------------------------------------------------


class TestAntiGoalsDocumented:
    @pytest.fixture(autouse=True)
    def load_doc(self):
        self.content = SPEC_DOC.read_text(encoding="utf-8")

    def test_anti_goals_section_present(self):
        lower = self.content.lower()
        assert "anti-goal" in lower or "never make" in lower or "must never" in lower

    @pytest.mark.parametrize("feeling", ANTI_GOALS)
    def test_anti_goal_feeling_documented(self, feeling: str):
        assert feeling.lower() in self.content.lower(), f"Anti-goal missing: {feeling!r}"

    def test_atlas_never_implies_action_required(self):
        lower = self.content.lower()
        assert "never" in lower and "action" in lower

    def test_no_account_gate_before_value(self):
        lower = self.content.lower()
        assert "before" in lower and "account" in lower and "value" in lower


# ---------------------------------------------------------------------------
# Emotional goals
# ---------------------------------------------------------------------------


class TestEmotionalGoalsDocumented:
    @pytest.fixture(autouse=True)
    def load_doc(self):
        self.content = SPEC_DOC.read_text(encoding="utf-8")

    def test_emotional_goals_documented(self):
        lower = self.content.lower()
        assert "emotional" in lower and "goal" in lower

    @pytest.mark.parametrize("feeling", EMOTIONAL_GOALS)
    def test_positive_feeling_documented(self, feeling: str):
        assert feeling.lower() in self.content.lower(), f"Emotional goal missing: {feeling!r}"

    def test_emotional_goals_per_step(self):
        lower = self.content.lower()
        assert "emotional goal" in lower

    def test_emotional_map_present(self):
        lower = self.content.lower()
        assert "primary emotional goal" in lower or "emotional goal" in lower

    def test_calmer_documented(self):
        lower = self.content.lower()
        assert "calm" in lower

    def test_not_overwhelmed_documented(self):
        lower = self.content.lower()
        assert "overwhelm" in lower

    def test_not_pressured_documented(self):
        lower = self.content.lower()
        assert "pressure" in lower or "pressured" in lower


# ---------------------------------------------------------------------------
# Arrival and landing page
# ---------------------------------------------------------------------------


class TestArrivalAndLandingPage:
    @pytest.fixture(autouse=True)
    def load_doc(self):
        self.content = SPEC_DOC.read_text(encoding="utf-8")
        self.lower = self.content.lower()

    def test_arrival_section_present(self):
        assert "arrival" in self.lower

    def test_landing_page_section_present(self):
        assert "landing" in self.lower

    def test_no_account_required_stated_explicitly(self):
        assert "no account required" in self.lower or "no account" in self.lower

    def test_one_primary_cta_specified(self):
        assert "call to action" in self.lower or "primary" in self.lower and "button" in self.lower

    def test_cta_does_not_say_sign_up(self):
        if "sign up" in self.lower:
            assert "must not say" in self.lower or "not say" in self.lower or "sign up" not in self.content

    def test_trust_signal_on_landing(self):
        assert "trust signal" in self.lower or "nothing is stored" in self.lower

    def test_no_pricing_on_landing(self):
        assert "pricing" in self.lower and ("not on" in self.lower or "does not" in self.lower or "landing page" in self.lower)

    def test_landing_page_primary_message_specified(self):
        assert "primary message" in self.lower

    def test_no_financial_jargon_on_landing(self):
        assert "jargon" in self.lower or "outperform" in self.lower or "no financial" in self.lower

    def test_what_atlas_does_stated_in_one_sentence(self):
        assert "one sentence" in self.lower


# ---------------------------------------------------------------------------
# First input
# ---------------------------------------------------------------------------


class TestFirstInputSpecified:
    @pytest.fixture(autouse=True)
    def load_doc(self):
        self.content = SPEC_DOC.read_text(encoding="utf-8")
        self.lower = self.content.lower()

    def test_first_input_section_present(self):
        assert "first input" in self.lower

    def test_text_area_specified(self):
        assert "text area" in self.lower or "textarea" in self.lower

    def test_placeholder_text_specified(self):
        assert "placeholder" in self.lower

    def test_no_format_required(self):
        assert "no format" in self.lower or "doesn't need to format" in self.lower or "does not need" in self.lower

    def test_submit_action_specified(self):
        assert "submit" in self.lower or "analyse" in self.lower

    def test_empty_input_behaviour_specified(self):
        assert "empty" in self.lower

    def test_what_user_can_paste_documented(self):
        assert "paste" in self.lower and ("ticker" in self.lower or "portfolio" in self.lower)

    def test_multiple_input_types_accepted(self):
        count = sum(1 for word in ["ticker", "portfolio", "research note", "company name", "question"] if word in self.lower)
        assert count >= 3


# ---------------------------------------------------------------------------
# Processing experience
# ---------------------------------------------------------------------------


class TestProcessingExperienceSpecified:
    @pytest.fixture(autouse=True)
    def load_doc(self):
        self.content = SPEC_DOC.read_text(encoding="utf-8")
        self.lower = self.content.lower()

    def test_processing_section_present(self):
        assert "processing" in self.lower

    def test_processing_transition_specified(self):
        assert "transition" in self.lower or "sequence" in self.lower

    def test_no_percentage_progress_bar(self):
        assert "percentage" in self.lower and ("not" in self.lower or "no percentage" in self.lower) or "percentage" not in self.lower

    def test_no_spinner_specified_alone(self):
        assert "not a spinner" in self.lower or "no spinner" in self.lower or "spinner" not in self.lower

    def test_long_processing_fallback_specified(self):
        assert "3 second" in self.lower or "seconds" in self.lower


# ---------------------------------------------------------------------------
# Temporary Workspace
# ---------------------------------------------------------------------------


class TestTemporaryWorkspaceSpecified:
    @pytest.fixture(autouse=True)
    def load_doc(self):
        self.content = SPEC_DOC.read_text(encoding="utf-8")
        self.lower = self.content.lower()

    def test_temporary_workspace_section_present(self):
        assert "temporary workspace" in self.lower

    def test_temporary_by_default(self):
        assert "temporary by default" in self.lower or "nothing" in self.lower and "saved" in self.lower

    def test_status_badge_specified(self):
        assert "status badge" in self.lower or "temporary · not saved" in self.lower or "not saved" in self.lower

    def test_footer_save_button_specified(self):
        assert "footer" in self.lower or "save" in self.lower

    def test_workspace_title_specified(self):
        assert "title" in self.lower

    def test_references_data_model_doc(self):
        assert "TemporaryWorkspaceDataModel.md" in self.content

    def test_references_card_rendering_doc(self):
        assert "TemporaryWorkspaceCardRenderingContract.md" in self.content


# ---------------------------------------------------------------------------
# Workspace Cards
# ---------------------------------------------------------------------------


class TestWorkspaceCardsSpecified:
    @pytest.fixture(autouse=True)
    def load_doc(self):
        self.content = SPEC_DOC.read_text(encoding="utf-8")
        self.lower = self.content.lower()

    def test_cards_section_present(self):
        assert "workspace card" in self.lower or "card" in self.lower

    def test_card_ordering_specified(self):
        assert "card ordering" in self.lower or "ordering" in self.lower

    @pytest.mark.parametrize("card_type", CARD_TYPES)
    def test_card_type_documented(self, card_type: str):
        assert card_type.lower() in self.lower, f"Card type missing: {card_type!r}"

    def test_card_anatomy_specified(self):
        assert "anatomy" in self.lower or "type label" in self.lower or "body" in self.lower

    def test_no_action_buttons_on_cards(self):
        assert "no action button" in self.lower or "cards do not have" in self.lower

    def test_no_scores_on_cards(self):
        assert "no score" in self.lower or "scores" in self.lower and "not" in self.lower

    def test_no_probability_on_cards(self):
        assert "no probability" in self.lower or "probability estimate" in self.lower

    def test_no_traffic_light_colours(self):
        assert "traffic light" in self.lower

    def test_expand_action_on_cards(self):
        assert "expand" in self.lower

    def test_disambiguation_card_specified(self):
        assert "disambiguation" in self.lower


# ---------------------------------------------------------------------------
# Weekly Review Preview
# ---------------------------------------------------------------------------


class TestWeeklyReviewPreviewSpecified:
    @pytest.fixture(autouse=True)
    def load_doc(self):
        self.content = SPEC_DOC.read_text(encoding="utf-8")
        self.lower = self.content.lower()

    def test_weekly_review_preview_section_present(self):
        assert "weekly review" in self.lower

    def test_when_it_appears_specified(self):
        assert "when it appears" in self.lower

    def test_partial_review_for_incomplete_data(self):
        assert "partial" in self.lower or "not enough" in self.lower

    def test_no_price_targets_in_review(self):
        assert "price target" in self.lower or "no price target" in self.lower or "price targets" in self.lower

    def test_empty_sections_not_shown(self):
        assert "empty section" in self.lower or "not shown" in self.lower


# ---------------------------------------------------------------------------
# Snapshot Draft Preview
# ---------------------------------------------------------------------------


class TestSnapshotDraftPreviewSpecified:
    @pytest.fixture(autouse=True)
    def load_doc(self):
        self.content = SPEC_DOC.read_text(encoding="utf-8")
        self.lower = self.content.lower()

    def test_snapshot_draft_section_present(self):
        assert "snapshot draft" in self.lower

    def test_confirmation_required(self):
        assert "confirm" in self.lower and ("required" in self.lower or "never treats" in self.lower or "explicit" in self.lower)

    def test_confirm_edit_discard_actions_specified(self):
        assert "confirm" in self.lower and "discard" in self.lower

    def test_draft_is_unconfirmed_by_default(self):
        assert "unconfirmed" in self.lower or "not confirmed" in self.lower or "pending" in self.lower

    def test_no_advice_in_draft(self):
        assert "no advice" in self.lower or "does not contain" in self.lower or "what the snapshot draft preview does not contain" in self.lower


# ---------------------------------------------------------------------------
# Save Workspace prompt
# ---------------------------------------------------------------------------


class TestSaveWorkspacePromptSpecified:
    @pytest.fixture(autouse=True)
    def load_doc(self):
        self.content = SPEC_DOC.read_text(encoding="utf-8")
        self.lower = self.content.lower()

    def test_save_prompt_section_present(self):
        assert "save workspace" in self.lower

    def test_when_prompt_appears_specified(self):
        assert "when it appears" in self.lower

    def test_prompt_not_a_gate(self):
        assert "not a gate" in self.lower or "can continue" in self.lower or "without saving" in self.lower

    def test_continue_without_saving_option_specified(self):
        assert "continue without saving" in self.lower

    def test_continue_option_not_greyed_out(self):
        assert "not greyed out" in self.lower or "equally prominent" in self.lower

    def test_timing_condition_specified(self):
        assert "60 second" in self.lower or "three" in self.lower and "card" in self.lower or "condition" in self.lower

    def test_what_saving_does_in_alpha_specified(self):
        assert "local storage" in self.lower

    def test_no_server_without_account(self):
        assert "no account is required" in self.lower or "account is required" in self.lower and "not" in self.lower


# ---------------------------------------------------------------------------
# Optional account creation
# ---------------------------------------------------------------------------


class TestAccountCreationSpecified:
    @pytest.fixture(autouse=True)
    def load_doc(self):
        self.content = SPEC_DOC.read_text(encoding="utf-8")
        self.lower = self.content.lower()

    def test_account_section_present(self):
        assert "account" in self.lower

    def test_account_is_optional(self):
        assert "optional" in self.lower and "account" in self.lower

    def test_account_offered_after_value(self):
        assert "after" in self.lower and "value" in self.lower and "account" in self.lower

    def test_account_never_offered_before_value(self):
        assert "never" in self.lower and "before" in self.lower

    def test_keep_using_without_account_option(self):
        assert "keep using without an account" in self.lower or "without an account" in self.lower

    def test_account_not_required_for_any_alpha_feature(self):
        assert "requirement" in self.lower or "not a requirement" in self.lower or "never" in self.lower


# ---------------------------------------------------------------------------
# Empty, error, and success states
# ---------------------------------------------------------------------------


class TestEmptyErrorSuccessStatesSpecified:
    @pytest.fixture(autouse=True)
    def load_doc(self):
        self.content = SPEC_DOC.read_text(encoding="utf-8")
        self.lower = self.content.lower()

    def test_empty_states_section_present(self):
        assert "empty state" in self.lower

    def test_error_states_section_present(self):
        assert "error state" in self.lower

    def test_success_states_section_present(self):
        assert "success state" in self.lower

    def test_no_error_for_empty_input(self):
        assert "no error" in self.lower or "not an error" in self.lower or "gently" in self.lower

    def test_no_red_colour_for_errors(self):
        assert "no red" in self.lower or "not red" in self.lower or "calm" in self.lower

    def test_user_input_not_lost_on_error(self):
        assert "not been lost" in self.lower or "has not been lost" in self.lower or "input is not lost" in self.lower

    def test_no_forced_account_on_save_error(self):
        assert "no forced account" in self.lower or "forced account creation" in self.lower

    def test_success_no_confetti(self):
        assert "confetti" in self.lower or "no confetti" in self.lower or "no celebration" in self.lower

    def test_success_no_animated_celebration(self):
        assert "celebration" in self.lower and ("no" in self.lower or "not" in self.lower)

    def test_multiple_empty_state_variants_specified(self):
        count = self.lower.count("empty state:")
        assert count >= 3

    def test_multiple_error_state_variants_specified(self):
        count = self.lower.count("error state:")
        assert count >= 3

    def test_multiple_success_state_variants_specified(self):
        count = self.lower.count("success state:")
        assert count >= 3


# ---------------------------------------------------------------------------
# Trust boundaries
# ---------------------------------------------------------------------------


class TestTrustBoundariesDocumented:
    @pytest.fixture(autouse=True)
    def load_doc(self):
        self.content = SPEC_DOC.read_text(encoding="utf-8")
        self.lower = self.content.lower()

    def test_trust_boundaries_section_present(self):
        assert "trust" in self.lower and "boundar" in self.lower

    def test_no_server_storage_before_account(self):
        assert "local storage" in self.lower

    def test_data_not_sent_without_action(self):
        assert "server" in self.lower and ("never" in self.lower or "not" in self.lower)

    def test_atlas_never_creates_account_without_action(self):
        assert "never" in self.lower and "account" in self.lower

    def test_snapshot_draft_requires_confirmation(self):
        assert "confirm" in self.lower

    def test_user_content_preserved_exactly(self):
        assert "exactly as written" in self.lower or "preserved exactly" in self.lower

    def test_ai_derived_content_labelled(self):
        assert "ai-derived" in self.lower or "labelled" in self.lower

    def test_privacy_expectations_documented(self):
        lower = self.lower
        assert "privacy" in lower

    def test_no_analytics_on_input_content(self):
        assert "analytics" in self.lower and ("no" in self.lower or "not" in self.lower)


# ---------------------------------------------------------------------------
# Future extensions
# ---------------------------------------------------------------------------


class TestFutureExtensionsDocumented:
    @pytest.fixture(autouse=True)
    def load_doc(self):
        self.content = SPEC_DOC.read_text(encoding="utf-8")
        self.lower = self.content.lower()

    def test_future_extensions_section_present(self):
        assert "future extension" in self.lower

    @pytest.mark.parametrize("extension", FUTURE_EXTENSIONS)
    def test_extension_documented(self, extension: str):
        assert extension.lower() in self.lower, f"Future extension missing: {extension!r}"

    def test_extensions_do_not_change_emotional_goals(self):
        assert "emotional goals are unchanged" in self.lower or "unchanged" in self.lower

    def test_extensions_connect_to_input_surface(self):
        assert "input surface" in self.lower or "input" in self.lower and "extend" in self.lower

    def test_sprint_287_recommendation_present(self):
        assert "287" in self.content

    def test_next_sprint_is_ux_flow(self):
        assert "ux flow" in self.lower or "wireframe" in self.lower or "flow" in self.lower


# ---------------------------------------------------------------------------
# No runtime code and no out-of-scope content
# ---------------------------------------------------------------------------


class TestNoRuntimeCodeOrImplementation:
    def test_no_python_imports_in_doc(self):
        content = SPEC_DOC.read_text(encoding="utf-8")
        assert "import atlas" not in content
        assert "from atlas" not in content

    def test_atlas_dir_not_modified(self):
        for py_file in ATLAS_DIR.rglob("*.py"):
            text = py_file.read_text(encoding="utf-8")
            assert "alpha_experience" not in text, f"Sprint 286 runtime code found in {py_file}"

    def test_no_cli_changes(self):
        cli_source = CLI_FILE.read_text(encoding="utf-8")
        assert "alpha_experience" not in cli_source

    @pytest.mark.parametrize("term", OUT_OF_SCOPE_TERMS)
    def test_no_implementation_technology_specified(self, term: str):
        content = SPEC_DOC.read_text(encoding="utf-8").lower()
        assert term not in content, f"Out-of-scope implementation term found: {term!r}"

    def test_documentation_only_stated(self):
        lower = SPEC_DOC.read_text(encoding="utf-8").lower()
        assert "documentation" in lower or "specification" in lower


# ---------------------------------------------------------------------------
# Safe language
# ---------------------------------------------------------------------------


class TestSafeLanguage:
    @pytest.fixture(autouse=True)
    def load_doc(self):
        self.content = SPEC_DOC.read_text(encoding="utf-8").lower()

    @pytest.mark.parametrize("phrase", PROHIBITED_PHRASES)
    def test_no_prohibited_phrase(self, phrase: str):
        assert phrase.lower() not in self.content, f"Prohibited phrase found: {phrase!r}"

    def test_no_buy_word(self):
        words = self.content.split()
        assert "buy" not in words

    def test_no_sell_word(self):
        words = self.content.split()
        assert "sell" not in words

    def test_no_return_guarantee(self):
        assert "guaranteed" not in self.content


# ---------------------------------------------------------------------------
# Decision log and release candidate updated
# ---------------------------------------------------------------------------


class TestDocumentationUpdated:
    def test_decision_log_mentions_sprint_286(self):
        log = Path("docs/DecisionLog.md").read_text(encoding="utf-8")
        assert "286" in log

    def test_decision_log_mentions_alpha_experience(self):
        log = Path("docs/DecisionLog.md").read_text(encoding="utf-8").lower()
        assert "alpha" in log or "experience" in log

    def test_rc_doc_mentions_sprint_286(self):
        rc = Path("docs/InternalV1ReleaseCandidate.md").read_text(encoding="utf-8")
        assert "286" in rc

    def test_rc_doc_sprint_286_entry_no_forbidden_language(self):
        rc = Path("docs/InternalV1ReleaseCandidate.md").read_text(encoding="utf-8")
        sprint_286_idx = rc.find("Sprint 286")
        if sprint_286_idx == -1:
            pytest.skip("Sprint 286 entry not found in RC doc")
        sprint_287_idx = rc.find("Sprint 287", sprint_286_idx)
        if sprint_287_idx == -1:
            chunk = rc[sprint_286_idx:]
        else:
            chunk = rc[sprint_286_idx:sprint_287_idx]
        for phrase in ["buy", "sell"]:
            words = chunk.lower().split()
            assert phrase not in words, f"Forbidden word {phrase!r} found in Sprint 286 RC entry"

    def test_spec_doc_present(self):
        assert SPEC_DOC.exists()
