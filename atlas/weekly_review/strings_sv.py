"""Swedish display string constants for the Weekly Review renderer.

Preparation-only module — Sprint 249.
These constants are NOT imported by active renderers.
They are NOT used in runtime output.
sv is NOT a supported locale. locale_support.py is unchanged.

All Swedish wording follows docs/SwedishSafeLanguageGuardrails.md.
No recommendation, urgency, price-target, certainty, execution, outperformance,
or personalized advice language is used.

Canonical internal values (enum values, schema keys, warning codes, ticker
symbols, file paths) are NOT here and are NOT translated.
User-provided content is NOT here.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Document title
# ---------------------------------------------------------------------------

WEEKLY_REVIEW_TITLE = "Atlas veckovis investeringsgranskning"

# ---------------------------------------------------------------------------
# Section titles
# ---------------------------------------------------------------------------

SECTION_REVIEW_SCOPE = "1. Granskningens omfattning"
SECTION_PORTFOLIO_CONTEXT = "2. Portföljkontext"
SECTION_WATCHLIST_REVIEW = "3. Bevakningslista"
SECTION_COMPANY_REVIEWS_NEEDING_ATTENTION = "4. Bolagsgranskningar som behöver uppmärksamhet"
SECTION_PORTFOLIO_FIT_AND_SUITABILITY_NOTES = "5. Portföljpassning och lämplighetsnoteringar"
SECTION_RISK_AND_PRINCIPLE_GUARDRAILS = "6. Risk- och principgränser"
SECTION_OPEN_DECISIONS = "7. Öppna beslut"
SECTION_MISSING_EVIDENCE = "8. Saknat underlag"
SECTION_FOLLOW_UP_QUESTIONS = "9. Uppföljningsfrågor"
SECTION_NON_ACTIONS_REASONS_TO_WAIT = "10. Icke-åtgärder / skäl att avvakta"

# ---------------------------------------------------------------------------
# Repeated section body labels
# ---------------------------------------------------------------------------

LABEL_EVIDENCE_GAP = "Underlagslucka"
LABEL_RISK_TO_MONITOR = "Risk att följa"
LABEL_REASON_TO_WAIT = "Skäl att avvakta"
LABEL_DECISION_DEFERRED = "Beslut uppskjutet"
LABEL_NO_ACTION_WARRANTED = "Ingen åtgärd motiverad"
LABEL_AGING_NOTE = "Äldre notering"
LABEL_MISSING_OPTIONAL_INPUT = "Saknat valfritt indata"

# ---------------------------------------------------------------------------
# Input status / warnings section headings
# ---------------------------------------------------------------------------

LABEL_INPUT_STATUS = "Indatastatus"
LABEL_INPUT_WARNINGS = "Indatavarningar"

# ---------------------------------------------------------------------------
# Input status message templates
# ---------------------------------------------------------------------------

INPUT_STATUS_PORTFOLIO_LOADED = "Portfölj: {count} innehav inlästa."
INPUT_STATUS_WATCHLIST_LOADED = "Bevakningslista: {count} post(er) inlästa från '{name}'."
INPUT_STATUS_INVESTOR_PROFILE_AVAILABLE = "Investerarprofil: Tillgänglig"
INPUT_STATUS_INVESTOR_PROFILE_NOT_PROVIDED = "Investerarprofil: Inte angiven — standardvärden används."
INPUT_STATUS_JOURNAL_LOADED = "Beslutsjournal: {count} post(er) inlästa."
INPUT_STATUS_JOURNAL_NOT_PROVIDED = "Beslutsjournal: Inte angiven."
INPUT_STATUS_COMPANY_FACTS_AVAILABLE = "Företagsfakta: Tillgänglig"
INPUT_STATUS_COMPANY_FACTS_NOT_PROVIDED = "Företagsfakta: Inte angiven — underlagsluckor noterade."
INPUT_STATUS_FINANCIALS_AVAILABLE = "Finansiell historik: Tillgänglig"
INPUT_STATUS_FINANCIALS_NOT_PROVIDED = "Finansiell historik: Inte angiven — underlagsluckor noterade."
INPUT_STATUS_RESEARCH_NOTES_LOADED = "Analysnotisar: {count} ticker(s) med lokala notisar."
INPUT_STATUS_RESEARCH_NOTES_NOT_PROVIDED = "Analysnotisar: Inte angivna."
INPUT_STATUS_REVIEW_DATE = "Granskningsdatum: {date}"
INPUT_STATUS_WARNINGS_COUNT = "Varningar: {count}"

# ---------------------------------------------------------------------------
# Warning display templates
# ---------------------------------------------------------------------------

WARNING_ROW = "- [{code}] {message}"
WARNING_SCOPE_SUMMARY = "Varningar: {count} indatavarning(ar) noterade — se avsnittet Indatavarningar"

# ---------------------------------------------------------------------------
# Disclaimer
# ---------------------------------------------------------------------------

WEEKLY_REVIEW_DISCLAIMER = (
    "Atlas veckovis investeringsgranskning — deterministisk, lokal, utan rekommendationer.\n"
    "Atlas stöder bättre omdöme. Det ersätter det inte."
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
