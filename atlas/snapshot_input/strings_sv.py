"""Swedish display string constants for Snapshot CLI renderers.

Preparation-only module — Sprint 249.
These constants are NOT imported by active renderers.
They are NOT used in runtime output.
sv is NOT a supported locale. locale_support.py is unchanged.

All Swedish wording follows docs/SwedishSafeLanguageGuardrails.md.
No recommendation, urgency, price-target, certainty, execution, outperformance,
or personalized advice language is used.

Canonical internal values (enum values, schema keys, snapshot_type values,
confirmation_status values, warning codes, ticker symbols, file paths,
CLI command names) are NOT here and are NOT translated.
User-provided content is NOT here.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Command headings
# ---------------------------------------------------------------------------

HEADING_VALIDATION = "Validering av Snapshot Draft"
HEADING_REVIEW = "Granskning av Snapshot Draft"
HEADING_CONFIRMATION = "Bekräftelse av Snapshot Draft"
HEADING_REJECTION = "Avvisning av Snapshot Draft"
HEADING_RESEARCH_NOTES_EXPORT = "Export av analysnotisar"
HEADING_COMPANY_FACTS_EXPORT = "Export av företagsfakta"

# ---------------------------------------------------------------------------
# Status display lines
# ---------------------------------------------------------------------------

STATUS_VALID = "Status: giltig"
STATUS_INVALID = "Status: ogiltig"
STATUS_REVIEWABLE = "Status: granskningsbar"
STATUS_BLOCKED = "Status: blockerad"
STATUS_WRITTEN = "Status: skriven"
STATUS_CONFIRMED = "Status: bekräftad"
STATUS_REJECTED = "Status: avvisad"

# ---------------------------------------------------------------------------
# Exportability display lines
# ---------------------------------------------------------------------------

EXPORTABLE_YES = "Exporterbar: ja"
EXPORTABLE_NO = "Exporterbar: nej"
EXPORTABLE_NO_REASON = "  Orsak: endast bekräftade utkast kan exporteras."

# ---------------------------------------------------------------------------
# Section header labels
# ---------------------------------------------------------------------------

SECTION_SAFETY_BOUNDARY = "Säkerhetsgräns:"
SECTION_SOURCE = "Källa:"
SECTION_REVIEW_CHECKLIST = "Granskningschecklista:"
SECTION_UNCERTAINTIES = "Osäkerheter:"
SECTION_MISSING_REQUIRED_FIELDS = "Saknade obligatoriska fält:"
SECTION_MISSING_REQUIRED_FIELDS_WARNINGS = (
    "Saknade obligatoriska fält (varningar — granska innan bekräftelse):"
)
SECTION_EXTRACTED_FIELDS = "Extraherade fält:"
SECTION_BLOCKING_ISSUES = "Blockerande problem:"
SECTION_RESEARCH_NOTES_REVIEW = "Granskning av analysnotisar:"

# ---------------------------------------------------------------------------
# Inline compound phrases
# ---------------------------------------------------------------------------

UNCERTAINTIES_NONE = "Osäkerheter: inga"
MISSING_REQUIRED_FIELDS_NONE = "Saknade obligatoriska fält: inga"

# ---------------------------------------------------------------------------
# Safety boundary lines — validate
# ---------------------------------------------------------------------------

SAFETY_VALIDATION_NO_WRITE = (
    "  - Validering av utkast skriver inte till lokala Atlas-indatafiler."
)

# ---------------------------------------------------------------------------
# Safety boundary lines — review
# ---------------------------------------------------------------------------

SAFETY_REVIEW_READONLY = "  - Granskning är skrivskyddad."
SAFETY_REVIEW_NO_CONFIRM = "  - Granskning bekräftar inte utkastet."
SAFETY_REVIEW_NO_WRITE = "  - Granskning skriver inte till lokala Atlas-indatafiler."

# ---------------------------------------------------------------------------
# Safety boundary lines — confirm and reject (shared)
# ---------------------------------------------------------------------------

SAFETY_ORIGINAL_NOT_MODIFIED = "  - Originalutkastet ändrades inte."
SAFETY_NO_INPUT_FILES_CHANGED = "  - Inga lokala Atlas-indatafiler ändrades."

# ---------------------------------------------------------------------------
# Safety boundary lines — confirm specific
# ---------------------------------------------------------------------------

SAFETY_CONFIRM_EXPORT_SEPARATE = "  - Exportkommandon måste fortfarande köras separat."

# ---------------------------------------------------------------------------
# Safety boundary lines — reject specific
# ---------------------------------------------------------------------------

SAFETY_REJECT_NOT_EXPORTABLE = "  - Avvisade utkast kan inte exporteras."

# ---------------------------------------------------------------------------
# Safety boundary lines — research notes export
# ---------------------------------------------------------------------------

SAFETY_RESEARCH_NOTES_ONLY = "  - Endast lokala analysnotisar skrevs."
SAFETY_RESEARCH_NOTES_NO_OTHER = (
    "  - Inga portfölj-, bevaklingslist-, journal- eller företagsfaktafiler ändrades."
)

# ---------------------------------------------------------------------------
# Safety boundary lines — company facts export
# ---------------------------------------------------------------------------

SAFETY_COMPANY_FACTS_ONLY = "  - Endast lokala företagsfakta skrevs."
SAFETY_COMPANY_FACTS_NO_OTHER = (
    "  - Inga portfölj-, bevakninglist-, journal- eller analysnotisar-filer ändrades."
)

# ---------------------------------------------------------------------------
# Confirm/reject note lines
# ---------------------------------------------------------------------------

NOTE_ALREADY_CONFIRMED = (
    "Notering: indata-utkastet var redan bekräftat; en bekräftad kopia skrevs."
)
NOTE_ALREADY_REJECTED = (
    "Notering: indata-utkastet var redan avvisat; en avvisad kopia skrevs."
)
NOTE_CONFIRMED_TO_REJECTED = (
    "Notering: indata-utkastet var bekräftat; en avvisad kopia skrevs för detta arbetsflöde."
)
