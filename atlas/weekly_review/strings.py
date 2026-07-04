"""Display string constants for the Weekly Review renderer.

Atlas-generated user-facing display strings only.
Canonical internal values (enum values, schema keys) are NOT here.
User-provided content is NOT here.
No localization is implemented. These are English-only constants.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Document title
# ---------------------------------------------------------------------------

WEEKLY_REVIEW_TITLE = "Atlas Weekly Investment Review"

# ---------------------------------------------------------------------------
# Section titles
# ---------------------------------------------------------------------------

SECTION_REVIEW_SCOPE = "1. Review Scope"
SECTION_PORTFOLIO_CONTEXT = "2. Portfolio Context"
SECTION_WATCHLIST_REVIEW = "3. Watchlist Review"
SECTION_COMPANY_REVIEWS_NEEDING_ATTENTION = "4. Company Reviews Needing Attention"
SECTION_PORTFOLIO_FIT_AND_SUITABILITY_NOTES = "5. Portfolio Fit and Suitability Notes"
SECTION_RISK_AND_PRINCIPLE_GUARDRAILS = "6. Risk and Principle Guardrails"
SECTION_OPEN_DECISIONS = "7. Open Decisions"
SECTION_MISSING_EVIDENCE = "8. Missing Evidence"
SECTION_FOLLOW_UP_QUESTIONS = "9. Follow-Up Questions"
SECTION_NON_ACTIONS_REASONS_TO_WAIT = "10. Non-Actions / Reasons to Wait"

# ---------------------------------------------------------------------------
# Repeated section body labels
# ---------------------------------------------------------------------------

LABEL_EVIDENCE_GAP = "Evidence Gap"
LABEL_RISK_TO_MONITOR = "Risk to Monitor"
LABEL_REASON_TO_WAIT = "Reason to Wait"
LABEL_DECISION_DEFERRED = "Decision Deferred"
LABEL_NO_ACTION_WARRANTED = "No Action Warranted"
LABEL_AGING_NOTE = "Aging Note"
LABEL_MISSING_OPTIONAL_INPUT = "Missing Optional Input"

# ---------------------------------------------------------------------------
# Input status / warnings section headings
# ---------------------------------------------------------------------------

LABEL_INPUT_STATUS = "Input Status"
LABEL_INPUT_WARNINGS = "Input Warnings"

# ---------------------------------------------------------------------------
# Input status message templates
# ---------------------------------------------------------------------------

INPUT_STATUS_PORTFOLIO_LOADED = "Portfolio: {count} holding(s) loaded."
INPUT_STATUS_WATCHLIST_LOADED = "Watchlist: {count} item(s) loaded from '{name}'."
INPUT_STATUS_INVESTOR_PROFILE_AVAILABLE = "Investor profile: Available"
INPUT_STATUS_INVESTOR_PROFILE_NOT_PROVIDED = "Investor profile: Not provided — default will be used."
INPUT_STATUS_JOURNAL_LOADED = "Decision journal: {count} entry/entries loaded."
INPUT_STATUS_JOURNAL_NOT_PROVIDED = "Decision journal: Not provided."
INPUT_STATUS_COMPANY_FACTS_AVAILABLE = "Company facts: Available"
INPUT_STATUS_COMPANY_FACTS_NOT_PROVIDED = "Company facts: Not provided — evidence gaps noted."
INPUT_STATUS_FINANCIALS_AVAILABLE = "Financials: Available"
INPUT_STATUS_FINANCIALS_NOT_PROVIDED = "Financials: Not provided — evidence gaps noted."
INPUT_STATUS_RESEARCH_NOTES_LOADED = "Research notes: {count} ticker(s) with local notes."
INPUT_STATUS_RESEARCH_NOTES_NOT_PROVIDED = "Research notes: Not provided."
INPUT_STATUS_REVIEW_DATE = "Review date: {date}"
INPUT_STATUS_WARNINGS_COUNT = "Warnings: {count}"

# ---------------------------------------------------------------------------
# Warning display templates
# ---------------------------------------------------------------------------

WARNING_ROW = "- [{code}] {message}"
WARNING_SCOPE_SUMMARY = "Warnings: {count} input warning(s) noted — see Input Warnings section"

# ---------------------------------------------------------------------------
# Disclaimer
# ---------------------------------------------------------------------------

WEEKLY_REVIEW_DISCLAIMER = (
    "Atlas Weekly Investment Review — deterministic, local-only, no recommendations.\n"
    "Atlas supports better judgment. It does not replace it."
)

REMINDER_NO_ACTION_VALID = "Reminder: No action is a valid and often appropriate outcome of a weekly review."
REMINDER_ATLAS_SUPPORTS_JUDGMENT = "Atlas supports better judgment. It does not replace it."

# ---------------------------------------------------------------------------
# Section 1 — Review Scope body messages
# ---------------------------------------------------------------------------

SCOPE_REVIEW_DATE_NOT_SPECIFIED = "Review date: Not specified"
SCOPE_INPUT_MODE = "Input mode: Local files only. No external data, no live pricing."
SCOPE_PORTFOLIO_SUMMARY = "Portfolio: {count} holding(s) across {accounts} account(s)"
SCOPE_WATCHLIST_SUMMARY = "Watchlist: {count} item(s) in '{name}'"
SCOPE_OPTIONAL_INPUTS_LOADED = "Optional inputs loaded: {items}"
SCOPE_OPTIONAL_INPUTS_NONE = (
    "Optional inputs: none provided — review uses portfolio and watchlist only"
)

# ---------------------------------------------------------------------------
# Section 2 — Portfolio Context body messages
# ---------------------------------------------------------------------------

PORTFOLIO_HOLDINGS_HEADER = "Holdings by weight (user-supplied values, highest first):"
PORTFOLIO_SECTOR_HEADER = "Sector exposure:"
PORTFOLIO_NOTE_LOCAL_ONLY = (
    "Note: All values are user-supplied. No live pricing or external data used."
)

# ---------------------------------------------------------------------------
# Section 3 — Watchlist Review body messages
# ---------------------------------------------------------------------------

WATCHLIST_NO_ITEMS = "No watchlist items loaded."

# ---------------------------------------------------------------------------
# Section 4 — Company Reviews Needing Attention body messages
# ---------------------------------------------------------------------------

ATTENTION_NO_ITEMS = (
    "No items flagged for immediate attention from available local inputs."
)
ATTENTION_NOTE_LOCAL_ONLY = (
    "Note: All observations are derived from user-supplied local inputs only. "
    "No external data, no engine analysis, no recommendations."
)

# ---------------------------------------------------------------------------
# Section 5 — Portfolio Fit and Suitability Notes body messages
# ---------------------------------------------------------------------------

SUITABILITY_PROFILE_PROVIDED = "Investor profile: Provided."
SUITABILITY_PROFILE_NOT_PROVIDED = (
    "Investor profile: Not provided. "
    "Suitability observations below are structural only and not personalized."
)
SUITABILITY_INVESTED_POSITIONS = "Invested positions: {count} (excluding cash holdings)."
SUITABILITY_ENGINE_DEFERRED = (
    "Full suitability evaluation is deferred until engine wiring. "
    "Portfolio fit notes are limited to loaded local structure."
)
SUITABILITY_NOTE_NO_MERIT_JUDGMENT = (
    "Note: Atlas does not judge investment merit or provide personalized guidance. "
    "Suitability assessment requires manual review."
)

# ---------------------------------------------------------------------------
# Section 6 — Risk and Principle Guardrails body messages
# ---------------------------------------------------------------------------

GUARDRAILS_ENGINE_DEFERRED = (
    "Risk and principle guardrail engine wiring is deferred to a later sprint."
)
GUARDRAILS_PRINCIPLE_GUARDRAIL = (
    "Principle Guardrail: No action is warranted when evidence is incomplete."
)
GUARDRAILS_NOTE_LOCAL_ONLY = (
    "Note: Guardrail checks are based on user-supplied data only. "
    "No live market data or external analysis used."
)
GUARDRAILS_NO_FLAGS = "No guardrail flags raised from available local inputs."

# ---------------------------------------------------------------------------
# Section 7 — Open Decisions body messages
# ---------------------------------------------------------------------------

DECISIONS_NO_JOURNAL = "No decision journal provided. Open decisions not reviewed."
DECISIONS_JOURNAL_REVIEWED = "Decision journal: {count} entry/entries reviewed."
DECISIONS_DATE_MISSING = (
    "[Date Missing] No decision date recorded; aging cannot be assessed."
)
AGING_NOTE_SUFFIX = (
    "Review date is older than 90 days ({days} days). "
    "Thesis assumptions may need to be rechecked."
)

# ---------------------------------------------------------------------------
# Section 8 — Missing Evidence body messages
# ---------------------------------------------------------------------------

EVIDENCE_NO_GAPS = "No evidence gaps identified from available local inputs."

# ---------------------------------------------------------------------------
# Section 9 — Follow-Up Questions body messages
# ---------------------------------------------------------------------------

QUESTIONS_NO_COMPANY_FACTS = (
    "What company facts are needed before changing the status of any watchlist item?"
)
QUESTIONS_NO_FINANCIALS = (
    "Which financial trends should be reviewed before any watchlist decision changes?"
)
QUESTIONS_OPEN_WATCHLIST_GAPS = (
    "What evidence would confirm or weaken the current assumptions for each open watchlist item?"
)
QUESTIONS_NONE = (
    "No follow-up questions identified. "
    "Add open_questions to watchlist items to surface them here."
)

# ---------------------------------------------------------------------------
# Ordered tuple of all section titles (structural reference)
# ---------------------------------------------------------------------------

WEEKLY_REVIEW_SECTION_TITLES = (
    SECTION_REVIEW_SCOPE,
    SECTION_PORTFOLIO_CONTEXT,
    SECTION_WATCHLIST_REVIEW,
    SECTION_COMPANY_REVIEWS_NEEDING_ATTENTION,
    SECTION_PORTFOLIO_FIT_AND_SUITABILITY_NOTES,
    SECTION_RISK_AND_PRINCIPLE_GUARDRAILS,
    SECTION_OPEN_DECISIONS,
    SECTION_MISSING_EVIDENCE,
    SECTION_FOLLOW_UP_QUESTIONS,
    SECTION_NON_ACTIONS_REASONS_TO_WAIT,
)
