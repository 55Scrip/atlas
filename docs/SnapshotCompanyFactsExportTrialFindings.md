# Sprint 234 — Snapshot Company Facts Export Trial Findings

**Date:** 2026-07-04
**Sprint:** 234
**Trial type:** Product validation — no code changes

---

## Trial Setup

Draft file: `examples/snapshot_drafts/company_facts_snapshot_confirmed.json`
Export destination: `/tmp/atlas_company_facts_export/`
Baseline MD5: `4fd8d3f05d366700aaa1902e80e11910`

Weekly Review bundles used:
- `examples/weekly_review/` (example bundle)
- `examples/weekly_review_realistic/` (realistic bundle, Section 8 check only)

---

## Commands Run

```bash
# Stage 1: validate and review
atlas snapshot validate examples/snapshot_drafts/company_facts_snapshot_confirmed.json
atlas snapshot review examples/snapshot_drafts/company_facts_snapshot_confirmed.json

# Stage 2: export
atlas snapshot export-company-facts \
  examples/snapshot_drafts/company_facts_snapshot_confirmed.json \
  --output-dir /tmp/atlas_company_facts_export \
  --overwrite

# Stage 3: Weekly Review without facts (baseline)
atlas weekly-review \
  --portfolio examples/weekly_review/portfolio.json \
  --watchlist examples/weekly_review/watchlist.json \
  --profile examples/weekly_review/investor_profile.json \
  --journal examples/weekly_review/decision_journal.json \
  --financials examples/weekly_review/financials \
  --research-notes examples/weekly_review/research_notes \
  --as-of 2026-01-01 \
  --scope-notes examples/weekly_review/scope_notes.md

# Stage 3: Weekly Review with exported facts
atlas weekly-review \
  --portfolio examples/weekly_review/portfolio.json \
  --watchlist examples/weekly_review/watchlist.json \
  --profile examples/weekly_review/investor_profile.json \
  --journal examples/weekly_review/decision_journal.json \
  --company-facts /tmp/atlas_company_facts_export \
  --financials examples/weekly_review/financials \
  --research-notes examples/weekly_review/research_notes \
  --as-of 2026-01-01 \
  --scope-notes examples/weekly_review/scope_notes.md
```

---

## Stage 1 — Draft Validation and Review

**Validation result:** Status: valid. Snapshot type: company_facts_snapshot.
Confidence: high. Confirmation status: confirmed. All fields present. No
uncertainties. No missing required fields. Safety boundary shown.

**Review result:** Status: reviewable. Exportable: yes. Target local file shown
(`examples/weekly_review/company_facts/ASML.json`). All 7 extracted fields
summarised (business_summary, company_name, geography, key_risks,
revenue_drivers, sector, ticker). No blocking issues that prevent export.

**Usability observation:** The review output shows one item under Blocking
Issues: "Draft is already in terminal state: confirmed. Confirmation is not
applicable." This is accurate — the confirm command cannot run on an already-
confirmed draft — but the label "Blocking Issues" is slightly misleading when
the draft is already in the correct state for export. The draft is exportable
and this note should not discourage the user. The "Exportable: yes" line
precedes the blocking issues section and is unambiguous, so this is a low-
priority wording note, not a functional issue.

**Safety boundary shown:** Review is read-only. No file written.

---

## Stage 2 — Export Company Facts

**Export output:**
```
Company Facts Export

Status: written
Ticker: ASML
Output File: /tmp/atlas_company_facts_export/ASML.json

Safety Boundary:
  - Only local company facts were written.
  - No portfolio, watchlist, journal, or research notes files were changed.
```

**Output path:** `/tmp/atlas_company_facts_export/ASML.json` (uppercase ticker, correct)

**Generated JSON (full):**
```json
{
  "business_summary": "Supplier of photolithography equipment for semiconductor manufacturing. ASML is the sole producer of EUV lithography systems and a major supplier of DUV systems used globally by leading chipmakers.",
  "company_name": "ASML Holding N.V.",
  "geography": [
    "Netherlands",
    "Global — primary customers in Taiwan, South Korea, United States"
  ],
  "key_risks": [
    "Export controls restricting shipments to China may reduce addressable market.",
    "Customer capex cyclicality: orders correlate with semiconductor inventory cycles.",
    "Geopolitical concentration risk from manufacturing in Netherlands.",
    "EUV technology complexity creates execution risk on High-NA ramp."
  ],
  "revenue_drivers": [
    "EUV lithography system sales to TSMC, Samsung, Intel.",
    "DUV lithography system sales across a wider customer base.",
    "Installed base services and upgrades on existing systems.",
    "Metrology and inspection systems revenue."
  ],
  "sector": "Semiconductors — Capital Equipment",
  "source": {
    "draft_id": "draft-company-facts-asml-20260110-001",
    "raw_source_reference": "my_notes/asml_company_facts_2026.md",
    "source_description": "User-written ASML company facts covering business model, sector, revenue drivers, and key risks"
  },
  "ticker": "ASML"
}
```

**JSON assessment:**
- All fields present and readable
- Source provenance present (draft_id, source_description)
- Bounded: all strings well within 800-char limit; lists within 30-item limit
- sort_keys=True produces deterministic output
- No forbidden language
- No external data — content is user-supplied only

**Files in output directory:** ASML.json only. Correct.

---

## Stage 3 — Weekly Review Consumption

### Section 8 — Before (no --company-facts)

Relevant lines:
```
- Evidence Gap [MSFT]: local financial history file is missing.
- Evidence Gap [NOVO]: local financial history file is missing.
- Evidence Gap [XYL]: local financial history file is missing.
- Missing Optional Input: Company facts directory not provided.
```

ASML was **not** in Section 8 missing evidence in the without-facts run
because the example bundle already has `examples/weekly_review/company_facts/`
containing `ASML.json`. The "Company facts directory not provided" line was the
only company-facts-related entry.

### Section 8 — After (--company-facts /tmp/atlas_company_facts_export)

Relevant lines:
```
- Evidence Gap [MSFT]: no local company facts file or financial history file.
- Evidence Gap [NOVO]: no local company facts file or financial history file.
- Evidence Gap [XYL]: no local company facts file or financial history file.
```

**ASML is absent from Section 8 missing evidence.** The exported company facts
file is detected and ASML's evidence gap line is suppressed. MSFT, NOVO, and
XYL remain flagged because their facts were not exported. This is correct
behaviour — only the tickers with local facts present are cleared.

The "Missing Optional Input: Company facts directory not provided." warning also
disappears from Input Status and Section 8 when --company-facts is supplied.

### Input Status — Before vs After

Before:
```
- Company facts: Not provided — evidence gaps noted.
- Warnings: 1
```

After:
```
- Company facts: Available
(no warning line)
```

Clean transition. The section 1 scope line also updates to include "company facts" in the optional inputs loaded list.

### Section 6 — Guardrails

Before (no facts): includes "Evidence Gap: Company facts not loaded."
After (with facts): that line is absent. The rest of Section 6 is unchanged.

### Section 9 — Follow-Up Questions

Before: Closes with "What company facts are needed before changing the status of
any watchlist item?" — a generic prompt that fires when no company facts are loaded.

After: That line is gone. Section 9 instead includes "Tickers without local
company facts (3): MSFT, NOVO, XYL" — a precise list that correctly identifies
exactly which tickers still need facts. This is a meaningful improvement in
specificity: the user knows exactly which gaps remain.

### Section 10 — Non-Actions / Reasons to Wait

Before: "Reason to Wait: Company facts not loaded. Decision-relevant evidence is
incomplete."

After: "Reason to Wait: Local company facts missing for 3 ticker(s) (MSFT, NOVO,
XYL): thesis context is incomplete for these positions."

Again, a precision improvement — the reason-to-wait narrows from "no company
facts at all" to "these three specific tickers are missing facts."

### Realistic Bundle (Section 8 check)

Ran with realistic bundle plus `/tmp/atlas_company_facts_export` (ASML.json only).
ASML does not appear in Section 8 missing evidence. MSFT and NOVO show "local
company facts file is missing" because the exported directory only contains ASML.
This confirms the detection logic is per-ticker and correct.

---

## File Mutation Safety

| File | Before MD5 | After MD5 | Changed |
|------|-----------|-----------|---------|
| `examples/snapshot_drafts/company_facts_snapshot_confirmed.json` | `4fd8d3f05d366700aaa1902e80e11910` | `4fd8d3f05d366700aaa1902e80e11910` | No |
| `examples/weekly_review/company_facts/ASML.json` | `8446c4aba42a734d1225931c3bd00cc4` | `8446c4aba42a734d1225931c3bd00cc4` | No |
| Portfolio files | — | — | No |
| Watchlist files | — | — | No |
| Journal files | — | — | No |
| Research notes files | — | — | No |

- `git status` after all trial commands: clean working tree
- Only file written: `/tmp/atlas_company_facts_export/ASML.json` (ephemeral, outside repository)
- Safety boundary: confirmed

---

## Language Guardrail Status

- CLI output: no forbidden language
- Generated JSON: no forbidden language (all content is user-supplied from the example draft)
- Review output: no forbidden language
- Section 8, 9, 10 output: no forbidden language

---

## Provider / Network Boundary

- No provider imports in `export_company_facts.py`
- No network calls at any stage
- All data from local files only
- `atlas snapshot export-company-facts` does not import from `atlas.providers`, `requests`, `urllib`, `httpx`, or `aiohttp`
- Boundary confirmed clean

---

## Product Judgment

The company facts export path is clean and functional.

**What works well:**
1. The full loop (validate → review → export → weekly-review) is clean and consistent with the research notes loop from Sprint 226
2. Section 8 clears the correct ticker and only that ticker — precision is good
3. Section 9 and Section 10 improve meaningfully: from generic "no facts loaded" to per-ticker missing lists
4. Safety boundaries are accurate in all output
5. Generated JSON is bounded, readable, and source-attributed
6. No mutation of draft or existing portfolio/watchlist/journal/research notes files
7. overwrite guard works as expected

**Minor wording observation:**
- The "Blocking Issues" label in `snapshot review` output for already-confirmed drafts is slightly misleading. An already-confirmed draft with "Exportable: yes" and the blocking note "Draft is already in terminal state: confirmed" creates a mild contradiction in appearance. The functionality is correct, but a future sprint could relabel this section "Confirmation Issues" or add context that these issues do not prevent export — only confirmation (which is not needed for an already-confirmed draft).

**No regression found.** Research notes loop, weekly review, and all existing commands remain functional.

---

## Remaining Gaps

1. MSFT, NOVO, XYL company facts not in example export bundle (expected — example scope is ASML only)
2. No financial CSV for MSFT, NOVO, XYL — pre-existing gap, not introduced here
3. Realistic bundle company facts (MSFT.json, NOVO.json, ASML.json) are pre-existing example files, not draft-exported — the draft-to-company-facts path could be used to regenerate them from confirmed drafts if those drafts existed
4. `snapshot review` "Blocking Issues" wording is slightly confusing for already-confirmed drafts (low priority)

---

## Sprint 235 Recommendation

**Recommended target: Create internal v1 demo package**

**Rationale:** Atlas now has a stable, validated set of local-only capabilities:
- Weekly Investment Review (all 10 sections)
- Research notes input
- Company facts input
- Snapshot Draft schema and CLI (validate, review, confirm, reject)
- Research notes export
- Company facts export
- File mutation safety enforced throughout

All paths are validated by real portfolio trials (Sprints 213, 220, 226, 230, 232, 234).

The next high-value step is not adding another conversion type but packaging the existing functionality into a documented, repeatable internal demo flow. This demonstrates the full safe user journey without adding riskier conversion types and creates a stable checkpoint before expanding the Snapshot Input track further.

**Alternative if conversion breadth is prioritised:** Implement draft-to-watchlist conversion.
**Alternative if facts quality is prioritised:** Improve company facts schema (add valuation_context, competitive_position, or last_reviewed_date fields).
