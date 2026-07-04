"""Display string constants for Snapshot CLI renderers.

Atlas-generated user-facing display strings only.
Canonical internal values (enum values, schema keys) are NOT here.
User-provided content is NOT here.
No localization is implemented. These are English-only constants.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Command headings
# ---------------------------------------------------------------------------

HEADING_VALIDATION = "Snapshot Draft Validation"
HEADING_REVIEW = "Snapshot Draft Review"
HEADING_CONFIRMATION = "Snapshot Draft Confirmation"
HEADING_REJECTION = "Snapshot Draft Rejection"
HEADING_RESEARCH_NOTES_EXPORT = "Research Notes Export"
HEADING_COMPANY_FACTS_EXPORT = "Company Facts Export"

# ---------------------------------------------------------------------------
# Status display lines
# ---------------------------------------------------------------------------

STATUS_VALID = "Status: valid"
STATUS_INVALID = "Status: invalid"
STATUS_REVIEWABLE = "Status: reviewable"
STATUS_BLOCKED = "Status: blocked"
STATUS_WRITTEN = "Status: written"
STATUS_CONFIRMED = "Status: confirmed"
STATUS_REJECTED = "Status: rejected"

# ---------------------------------------------------------------------------
# Exportability display lines
# ---------------------------------------------------------------------------

EXPORTABLE_YES = "Exportable: yes"
EXPORTABLE_NO = "Exportable: no"
EXPORTABLE_NO_REASON = "  Reason: only confirmed drafts are exportable."

# ---------------------------------------------------------------------------
# Section header labels
# ---------------------------------------------------------------------------

SECTION_SAFETY_BOUNDARY = "Safety Boundary:"
SECTION_SOURCE = "Source:"
SECTION_REVIEW_CHECKLIST = "Review Checklist:"
SECTION_UNCERTAINTIES = "Uncertainties:"
SECTION_MISSING_REQUIRED_FIELDS = "Missing Required Fields:"
SECTION_MISSING_REQUIRED_FIELDS_WARNINGS = (
    "Missing Required Fields (warnings — review before confirming):"
)
SECTION_EXTRACTED_FIELDS = "Extracted Fields:"
SECTION_BLOCKING_ISSUES = "Blocking Issues:"
SECTION_RESEARCH_NOTES_REVIEW = "Research Notes Review:"

# ---------------------------------------------------------------------------
# Inline compound phrases
# ---------------------------------------------------------------------------

UNCERTAINTIES_NONE = "Uncertainties: none"
MISSING_REQUIRED_FIELDS_NONE = "Missing Required Fields: none"

# ---------------------------------------------------------------------------
# Safety boundary lines — validate
# ---------------------------------------------------------------------------

SAFETY_VALIDATION_NO_WRITE = (
    "  - Draft validation does not write to Atlas local input files."
)

# ---------------------------------------------------------------------------
# Safety boundary lines — review
# ---------------------------------------------------------------------------

SAFETY_REVIEW_READONLY = "  - Review is read-only."
SAFETY_REVIEW_NO_CONFIRM = "  - Review does not confirm the draft."
SAFETY_REVIEW_NO_WRITE = "  - Review does not write Atlas local input files."

# ---------------------------------------------------------------------------
# Safety boundary lines — confirm and reject (shared)
# ---------------------------------------------------------------------------

SAFETY_ORIGINAL_NOT_MODIFIED = "  - Original draft was not modified."
SAFETY_NO_INPUT_FILES_CHANGED = "  - No Atlas local input files were changed."

# ---------------------------------------------------------------------------
# Safety boundary lines — confirm specific
# ---------------------------------------------------------------------------

SAFETY_CONFIRM_EXPORT_SEPARATE = "  - Export commands must still be run separately."

# ---------------------------------------------------------------------------
# Safety boundary lines — reject specific
# ---------------------------------------------------------------------------

SAFETY_REJECT_NOT_EXPORTABLE = "  - Rejected drafts are not exportable."

# ---------------------------------------------------------------------------
# Safety boundary lines — research notes export
# ---------------------------------------------------------------------------

SAFETY_RESEARCH_NOTES_ONLY = "  - Only local research notes were written."
SAFETY_RESEARCH_NOTES_NO_OTHER = (
    "  - No portfolio, watchlist, journal, or company facts files were changed."
)

# ---------------------------------------------------------------------------
# Safety boundary lines — company facts export
# ---------------------------------------------------------------------------

SAFETY_COMPANY_FACTS_ONLY = "  - Only local company facts were written."
SAFETY_COMPANY_FACTS_NO_OTHER = (
    "  - No portfolio, watchlist, journal, or research notes files were changed."
)

# ---------------------------------------------------------------------------
# Confirm/reject note lines
# ---------------------------------------------------------------------------

NOTE_ALREADY_CONFIRMED = (
    "Note: input draft was already confirmed; a confirmed copy was written."
)
NOTE_ALREADY_REJECTED = (
    "Note: input draft was already rejected; a rejected copy was written."
)
NOTE_CONFIRMED_TO_REJECTED = (
    "Note: input draft was confirmed; a rejected copy was written for this workflow branch."
)
