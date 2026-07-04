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

REMINDER_NO_ACTION_VALID = "Påminnelse: Ingen åtgärd är ett giltigt och ofta lämpligt resultat av en veckogranskning."
REMINDER_ATLAS_SUPPORTS_JUDGMENT = "Atlas stöder bättre omdöme. Det ersätter det inte."

# ---------------------------------------------------------------------------
# Section 1 — Review Scope body messages
# ---------------------------------------------------------------------------

SCOPE_REVIEW_DATE_NOT_SPECIFIED = "Granskningsdatum: Inte angivet"
SCOPE_INPUT_MODE = "Indataläge: Lokala filer enbart. Inga externa data, ingen live-prissättning."
SCOPE_PORTFOLIO_SUMMARY = "Portfölj: {count} innehav i {accounts} konto(n)"
SCOPE_WATCHLIST_SUMMARY = "Bevakningslista: {count} post(er) i '{name}'"
SCOPE_OPTIONAL_INPUTS_LOADED = "Valfria indata inlästa: {items}"
SCOPE_OPTIONAL_INPUTS_NONE = (
    "Valfria indata: inga angivna — granskning använder portfölj och bevakningslista enbart"
)

# ---------------------------------------------------------------------------
# Section 2 — Portfolio Context body messages
# ---------------------------------------------------------------------------

PORTFOLIO_HOLDINGS_HEADER = "Innehav efter vikt (användarsupplerade värden, högst först):"
PORTFOLIO_SECTOR_HEADER = "Sektorexponering:"
PORTFOLIO_NOTE_LOCAL_ONLY = (
    "Notering: Alla värden är användarsupplerade. Ingen live-prissättning eller externa data används."
)

# ---------------------------------------------------------------------------
# Section 3 — Watchlist Review body messages
# ---------------------------------------------------------------------------

WATCHLIST_NO_ITEMS = "Inga bevakningsposter inlästa."

# ---------------------------------------------------------------------------
# Section 4 — Company Reviews Needing Attention body messages
# ---------------------------------------------------------------------------

ATTENTION_NO_ITEMS = (
    "Inga poster flaggade för omedelbar uppmärksamhet från tillgängliga lokala indata."
)
ATTENTION_NOTE_LOCAL_ONLY = (
    "Notering: Alla observationer härrör enbart från användarsupplerade lokala indata. "
    "Inga externa data, ingen motoranalys, inga rekommendationer."
)

# ---------------------------------------------------------------------------
# Section 5 — Portfolio Fit and Suitability Notes body messages
# ---------------------------------------------------------------------------

SUITABILITY_PROFILE_PROVIDED = "Investerarprofil: Angiven."
SUITABILITY_PROFILE_NOT_PROVIDED = (
    "Investerarprofil: Inte angiven. "
    "Lämplighetsnoteringar nedan är strukturella enbart och ej personaliserade."
)
SUITABILITY_INVESTED_POSITIONS = "Investerade positioner: {count} (exklusive kassainnehav)."
SUITABILITY_ENGINE_DEFERRED = (
    "Fullständig lämplighetsbedömning är uppskjuten tills motorkoppling finns. "
    "Portföljpassningsnoteringar är begränsade till inläst lokal struktur."
)
SUITABILITY_NOTE_NO_MERIT_JUDGMENT = (
    "Notering: Atlas bedömer inte investeringsmerit eller ger personaliserad vägledning. "
    "Lämplighetsbedömning kräver manuell granskning."
)

# ---------------------------------------------------------------------------
# Section 6 — Risk and Principle Guardrails body messages
# ---------------------------------------------------------------------------

GUARDRAILS_ENGINE_DEFERRED = (
    "Motorkoppling för risk- och principgränser är uppskjuten till ett senare sprint."
)
GUARDRAILS_PRINCIPLE_GUARDRAIL = (
    "Principgräns: Ingen åtgärd är motiverad när underlag är ofullständigt."
)
GUARDRAILS_NOTE_LOCAL_ONLY = (
    "Notering: Gränskontroller baseras enbart på användarsupplerade data. "
    "Inga live-marknadsdata eller extern analys används."
)
GUARDRAILS_NO_FLAGS = "Inga gränskontrollflaggor höjda från tillgängliga lokala indata."

# ---------------------------------------------------------------------------
# Section 7 — Open Decisions body messages
# ---------------------------------------------------------------------------

DECISIONS_NO_JOURNAL = "Ingen beslutsjournal angiven. Öppna beslut granskas inte."
DECISIONS_JOURNAL_REVIEWED = "Beslutsjournal: {count} post(er) granskade."
DECISIONS_DATE_MISSING = (
    "[Datum saknas] Inget beslutsdatum registrerat; ålder kan inte bedömas."
)
AGING_NOTE_SUFFIX = (
    "Granskningsdatum är äldre än 90 dagar ({days} dagar). "
    "Antaganden för tesen kan behöva kontrolleras."
)

# ---------------------------------------------------------------------------
# Section 8 — Missing Evidence body messages
# ---------------------------------------------------------------------------

EVIDENCE_NO_GAPS = "Inga underlagsluckor identifierade från tillgängliga lokala indata."

# ---------------------------------------------------------------------------
# Section 9 — Follow-Up Questions body messages
# ---------------------------------------------------------------------------

QUESTIONS_NO_COMPANY_FACTS = (
    "Vilken företagsfakta behövs innan statusen för något bevakningsobjekt ändras?"
)
QUESTIONS_NO_FINANCIALS = (
    "Vilka finansiella trender bör granskas innan beslut om bevakningslista ändras?"
)
QUESTIONS_OPEN_WATCHLIST_GAPS = (
    "Vilket underlag skulle bekräfta eller försvaga nuvarande antaganden för varje öppet bevakningsobjekt?"
)
QUESTIONS_NONE = (
    "Inga uppföljningsfrågor identifierade. "
    "Lägg till open_questions till bevakningsposter för att de ska visas här."
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
