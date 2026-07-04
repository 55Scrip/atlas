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
# Disclaimer
# ---------------------------------------------------------------------------

WEEKLY_REVIEW_DISCLAIMER = (
    "Atlas Weekly Investment Review — deterministic, local-only, no recommendations.\n"
    "Atlas supports better judgment. It does not replace it."
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
