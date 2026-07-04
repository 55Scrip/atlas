# Snapshot Confirm/Export Trial Findings

**Sprint:** 230
**Date:** 2026-07-04
**Trial type:** Fourth real portfolio trial — full review-confirm-export-Weekly Review loop
**Status:** Green

---

## Commands Run

### Stage 1 — Review Original Draft

```bash
atlas snapshot review examples/snapshot_drafts/research_notes_snapshot.json
```

### Stage 2 — Confirm Draft Copy

```bash
atlas snapshot confirm \
  examples/snapshot_drafts/research_notes_snapshot.json \
  --output-draft /tmp/atlas_research_notes_confirmed.json \
  --overwrite
```

### Stage 3 — Validate and Review Confirmed Copy

```bash
atlas snapshot validate /tmp/atlas_research_notes_confirmed.json
atlas snapshot review /tmp/atlas_research_notes_confirmed.json
```

### Stage 4 — Export Research Notes

```bash
atlas snapshot export-research-notes \
  /tmp/atlas_research_notes_confirmed.json \
  --output-dir /tmp/atlas_research_notes_export
```

### Stage 5 — Weekly Review (example bundle)

```bash
atlas weekly-review \
  --portfolio examples/weekly_review/portfolio.json \
  --watchlist examples/weekly_review/watchlist.json \
  --profile examples/weekly_review/investor_profile.json \
  --journal examples/weekly_review/decision_journal.json \
  --company-facts examples/weekly_review/company_facts \
  --financials examples/weekly_review/financials \
  --research-notes /tmp/atlas_research_notes_export \
  --as-of 2026-01-01 \
  --scope-notes examples/weekly_review/scope_notes.md
```

### Stage 5 — Weekly Review (realistic bundle)

```bash
atlas weekly-review \
  --portfolio examples/weekly_review_realistic/portfolio.json \
  --watchlist examples/weekly_review_realistic/watchlist.json \
  --profile examples/weekly_review_realistic/investor_profile.json \
  --journal examples/weekly_review_realistic/decision_journal.json \
  --company-facts examples/weekly_review_realistic/company_facts \
  --financials examples/weekly_review_realistic/financials \
  --research-notes /tmp/atlas_research_notes_export \
  --as-of 2026-01-01 \
  --scope-notes examples/weekly_review_realistic/scope_notes.md
```

---

## Stage 1 — Original Review

**Result:** Pass

- Draft state: `draft`
- Exportable: no (reason shown)
- Blocking issues: none
- Review checklist: all required fields present
- Research Notes Review section: `thesis_notes` and `reasons_to_wait` shown as missing (correct — not in this example draft)
- Safety boundary: clearly visible
- Read-only status: clearly communicated

**Assessment:** Review output is clear and honest. The exportability reason is actionable. Missing fields are surfaced as informational, not blocking. The "read-only" safety boundary is present and direct.

**One observation:** The `Review Checklist` section lists `Snapshot Type: present` as a checklist item, but `Snapshot Type` is always present once the schema validates — it cannot be missing at this point. This is mildly redundant. Low priority.

---

## Stage 2 — Confirm Draft Copy

**Result:** Pass

**First run:** output collision correctly blocked with clear reason and `--overwrite` instruction.

**Second run (with `--overwrite`):**

```
Snapshot Draft Confirmation

Status: confirmed
Input Draft: examples/snapshot_drafts/research_notes_snapshot.json
Output Draft: /tmp/atlas_research_notes_confirmed.json
Snapshot Type: research_notes_snapshot
Confirmation Status: confirmed

Safety Boundary:
  - Original draft was not modified.
  - No Atlas local input files were changed.
  - Export commands must still be run separately.
```

**Checksum verification:**
- Before confirm: `MD5 = 82e25d52aa28a6dd940c87baa99754be`
- After confirm: `MD5 = 82e25d52aa28a6dd940c87baa99754be`
- Original draft unchanged. ✓

**Assessment:** Confirm output is clear and correct. Safety boundary is prominent. Output path is explicit. The collision guard worked correctly on first run. The `--overwrite` flag follows existing CLI style. `Confirmation Status: confirmed` is shown in output, which pairs well with the review output.

---

## Stage 3 — Validate and Review Confirmed Copy

**Validation result:**
```
Status: valid
Snapshot Type: research_notes_snapshot
Confidence: high
Confirmation Status: confirmed
```

**Review result:**
```
Confirmation Status: confirmed
Exportable: yes
```

**Assessment:** Confirmed copy passes validation and reviews as exportable. The `Exportable: yes` line is unambiguous. The "Blocking Issues" section shows "Draft is already in terminal state: confirmed. Confirmation is not applicable." — this is informative (tells the user `atlas snapshot confirm` would refuse the confirmed copy) but the draft is still shown as Exportable: yes. This is correct behavior: the blocking issue is about re-confirmation, not about exportability.

**One observation:** The blocking issue message on a confirmed copy could be slightly clearer. "Draft is already in terminal state: confirmed. Confirmation is not applicable." is accurate but may confuse a user who just ran `confirm` and sees "blocking issue" on the output. A follow-up wording improvement could help (e.g., "Draft is confirmed — use export commands to proceed."). Logged as a future improvement, not a blocker.

---

## Stage 4 — Export Research Notes

**Result:** Pass

**Generated Markdown:**
```markdown
# ASML Research Notes

## Evidence Gaps
- Margin durability through a downcycle has not been reviewed recently.
- China revenue exposure needs updated context.

## Open Questions
- What assumptions about EUV demand durability should be rechecked?
- Which financial history quarters are most relevant for margin review?

## Risks to Monitor
- Export controls affecting China shipments.
- Customer capex cyclicality during semiconductor inventory corrections.

## Source
- Source description: User-written ASML research notes covering thesis, evidence gaps, and risks
- Draft ID: draft-research-asml-20260105-001
- Source reference: my_notes/asml_notes_2026.md
```

**Assessment:** Markdown is readable and well-structured. Source attribution is present. Content is specific and actionable. The example draft lacks `thesis_notes` and `reasons_to_wait` — these sections are correctly absent from the output (not rendered as empty stubs). Export correctly writes only `ASML/notes.md` under the output directory.

**Mutation safety:**
- Input draft unchanged (checksum confirmed above)
- Confirmed copy written only to requested path
- Export wrote only `/tmp/atlas_research_notes_export/ASML/notes.md`
- No portfolio, watchlist, journal, or company facts files changed

---

## Stage 5 — Weekly Review Consumption

### Example Bundle

**Result:** Pass. All 10 sections rendered. Exit 0.

**Section 8 findings:**
- ASML evidence gaps surfaced from research notes:
  - `Evidence Gap [ASML] (research notes): Margin durability through a downcycle has not been reviewed recently.`
  - `Evidence Gap [ASML] (research notes): China revenue exposure needs updated context.`
- `(research notes)` provenance label present — distinguishable from watchlist gaps
- Combined with watchlist gaps (XYL, NOVO) without duplication
- ASML not on watchlist in example bundle, so no watchlist gaps for ASML — research notes gaps are the only ASML evidence in Section 8

**Section 9 findings:**
- ASML research notes questions surfaced:
  - `[ASML] Research notes — open questions:`
  - `- What assumptions about EUV demand durability should be rechecked?`
  - `- Which financial history quarters are most relevant for margin review?`
- Risk-to-monitor items surfaced:
  - `[ASML] Risk to Monitor (research notes): Export controls affecting China shipments.`
  - `[ASML] Risk to Monitor (research notes): Customer capex cyclicality during semiconductor inventory corrections.`
- Clear separation from watchlist questions (XYL, NOVO)

**Section 10 findings:**
- `Reason to Wait: ASML research notes contain 2 unresolved evidence gap(s). Gathering evidence is the appropriate next step.`
- Research notes content integrates naturally alongside principle/constraint reasons to wait
- Section 10 remains non-empty and actionable

**Assessment:** Research notes from the confirm/export path integrate correctly into all three sections. Output is specific and source-attributed. No duplication with watchlist items. No forbidden language.

### Realistic Bundle

**Result:** Pass. ASML is in the realistic portfolio.

**Section 8:** ASML research notes gaps appear alongside 16 watchlist evidence gaps. The `(research notes)` provenance label keeps ASML gaps identifiable.

**Section 9:** ASML open questions and risks-to-monitor appear in the correct position. Section 9 remains navigable despite the larger realistic watchlist.

**Section 10:** `Reason to Wait: ASML research notes contain 2 unresolved evidence gap(s)` present. NESTE aging alert (473 days) also present. Section 10 is substantive and useful.

---

## File Mutation Safety

| File | Expected | Actual |
|------|----------|--------|
| `examples/snapshot_drafts/research_notes_snapshot.json` | Unchanged | ✓ MD5 same before and after |
| `/tmp/atlas_research_notes_confirmed.json` | Written (confirmed copy) | ✓ |
| `/tmp/atlas_research_notes_export/ASML/notes.md` | Written (export) | ✓ |
| Any portfolio file | Unchanged | ✓ Not touched |
| Any watchlist file | Unchanged | ✓ Not touched |
| Any journal file | Unchanged | ✓ Not touched |
| Any company facts file | Unchanged | ✓ Not touched |
| Any research notes in `examples/` | Unchanged | ✓ Not touched |

---

## Generated Markdown Assessment

The generated `notes.md` is:
- Readable as a standalone research reference
- Specific to ASML (not generic)
- Source-attributed (draft ID, source description, reference)
- Correctly bounded (no overlong bullets in this example)
- Absent of forbidden language
- Free of AI/LLM-generated content (all content is user-supplied from extracted_fields)

Missing from this example (not a bug):
- No `## Thesis Notes` section (not in extracted_fields)
- No `## Reasons to Wait` section (not in extracted_fields)

---

## Language Guardrail Status

All outputs checked. No forbidden language found in:
- `atlas snapshot review` output
- `atlas snapshot confirm` output
- `atlas snapshot validate` output
- `atlas snapshot export-research-notes` output
- Generated `notes.md` Markdown
- Weekly Review output (all 10 sections)

---

## Provider / Network Boundary

No provider, network, or external API calls made during any stage. All data is from local files. No `atlas.providers`, `requests`, `urllib`, `httpx`, or `aiohttp` imports introduced.

---

## Product Judgment

The review-confirm-export-Weekly Review loop works correctly end-to-end.

**What works well:**
1. The collision guard on `confirm` (`--overwrite` required) is useful — it prevents accidental overwrites and makes the output path explicit
2. The safety boundary in `confirm` output is prominent and direct
3. `Exportable: yes` in review output is a clear gate signal
4. The `(research notes)` provenance label in Sections 8/9 makes source attribution traceable
5. Section 10 "Reason to Wait: ASML research notes contain N unresolved evidence gap(s)" is a clean integration

**Known gaps (non-blocking):**
1. The example draft lacks `thesis_notes` and `reasons_to_wait` — a richer example draft would make the full-section export more visible for documentation
2. The blocking issue message "Draft is already in terminal state: confirmed. Confirmation is not applicable." on a confirmed draft's review output could be clearer — e.g., "Draft is confirmed. Re-confirmation is not applicable. Use export commands to proceed."
3. No `reasons_to_wait` field in the example draft means Section 10 gets no per-ticker reasons-to-wait from research notes for ASML — only the evidence gap count line

**Workflow clarity:**
The four-command chain (`review` → `confirm` → `validate` → `export-research-notes`) is coherent. Each command has a clear purpose and a clear safety boundary. The flow is understandable as a user-facing process. No command is confusing.

**Worth extending to more draft types?**
Yes. The pattern is sound. The confirm command is type-agnostic — it works on any valid draft type. The export layer is type-specific (`export-research-notes` requires `research_notes_snapshot`). Adding a `reject` command would complete the basic status workflow before adding more conversion types.

---

## Remaining Gaps

1. No `atlas snapshot reject` command — drafts cannot be marked as rejected without manually editing the JSON
2. No `atlas snapshot supersede` command
3. No `draft-to-company-facts` conversion
4. No `draft-to-watchlist` conversion
5. Example draft is sparse (missing `thesis_notes`, `reasons_to_wait`) — a richer example would better demonstrate the full export
6. Wording improvement opportunity: review blocking issue message on confirmed drafts

---

## Recommended Sprint 231 Target

**Add snapshot draft reject CLI.**

After confirming the review-confirm-export path is sound, the next small workflow-completeness step is to allow users to mark unusable drafts as rejected. A `reject` command writes a rejected copy (sets `confirmation_status: rejected`) without touching any Atlas local input files. This follows the same non-mutating copy pattern as `confirm`, is low risk, and completes the basic status workflow (confirm/reject) before adding conversion types.

Alternative: Implement `draft-to-company-facts` conversion if conversion breadth is the priority.
