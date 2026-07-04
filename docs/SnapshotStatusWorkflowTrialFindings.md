# Snapshot Status Workflow Trial Findings

**Sprint:** 232
**Date:** 2026-07-04
**Trial type:** Fifth real portfolio trial — confirm and reject branch validation
**Status:** Green

---

## Trial Setup

Source draft: `examples/snapshot_drafts/research_notes_snapshot.json`
- Snapshot type: `research_notes_snapshot`
- Confirmation status: `draft`
- Ticker: ASML
- MD5 before trial: `82e25d52aa28a6dd940c87baa99754be`

Confirm branch output: `/tmp/atlas_snapshot_confirm_branch_confirmed.json`
Reject branch output: `/tmp/atlas_snapshot_reject_branch_rejected.json`
Export output: `/tmp/atlas_research_notes_confirm_branch/ASML/notes.md`

---

## Confirm Branch

### Commands Run

```bash
atlas snapshot review examples/snapshot_drafts/research_notes_snapshot.json
atlas snapshot confirm examples/snapshot_drafts/research_notes_snapshot.json --output-draft /tmp/atlas_snapshot_confirm_branch_confirmed.json --overwrite
atlas snapshot validate /tmp/atlas_snapshot_confirm_branch_confirmed.json
atlas snapshot review /tmp/atlas_snapshot_confirm_branch_confirmed.json
atlas snapshot export-research-notes /tmp/atlas_snapshot_confirm_branch_confirmed.json --output-dir /tmp/atlas_research_notes_confirm_branch --overwrite
atlas weekly-review --portfolio examples/weekly_review/portfolio.json --watchlist examples/weekly_review/watchlist.json --profile examples/weekly_review/investor_profile.json --journal examples/weekly_review/decision_journal.json --company-facts examples/weekly_review/company_facts --financials examples/weekly_review/financials --research-notes /tmp/atlas_research_notes_confirm_branch --as-of 2026-01-01 --scope-notes examples/weekly_review/scope_notes.md
```

### Stage Results

**Review (original):** Pass. `Confirmation Status: draft`. `Exportable: no` with reason. Blocking Issues: None. Research Notes Review shows evidence_gaps, open_questions, risks_to_monitor present; thesis_notes and reasons_to_wait missing (correct — not in this example draft). Safety boundary visible.

**Confirm:** Pass. `Status: confirmed`. Safety boundary present. All three safety lines shown.

**Validate (confirmed copy):** Pass. `Status: valid`. `Confirmation Status: confirmed`.

**Review (confirmed copy):** Pass. `Exportable: yes`. `Confirmation Status: confirmed`. Blocking Issues shows "already in terminal state: confirmed. Confirmation is not applicable." — this is correct and informative, not an error. Exportability is unambiguous.

**Export:** Pass. `Status: written`. Output: `/tmp/atlas_research_notes_confirm_branch/ASML/notes.md`.

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

**Weekly Review — Section 8:**
```
Evidence Gap [ASML] (research notes): Margin durability through a downcycle has not been reviewed recently.
Evidence Gap [ASML] (research notes): China revenue exposure needs updated context.
```

**Weekly Review — Section 9:**
```
[ASML] Risk to Monitor (research notes): Export controls affecting China shipments.
[ASML] Risk to Monitor (research notes): Customer capex cyclicality during semiconductor inventory corrections.
```

**Weekly Review — Section 10:**
```
Reason to Wait: ASML research notes contain 2 unresolved evidence gap(s). Gathering evidence is the appropriate next step.
```

---

## Reject Branch

### Commands Run

```bash
atlas snapshot review examples/snapshot_drafts/research_notes_snapshot.json
atlas snapshot reject examples/snapshot_drafts/research_notes_snapshot.json --output-draft /tmp/atlas_snapshot_reject_branch_rejected.json --overwrite
atlas snapshot validate /tmp/atlas_snapshot_reject_branch_rejected.json
atlas snapshot review /tmp/atlas_snapshot_reject_branch_rejected.json
atlas snapshot export-research-notes /tmp/atlas_snapshot_reject_branch_rejected.json --output-dir /tmp/atlas_research_notes_reject_branch
```

### Stage Results

**Review (original):** Same as confirm branch. Draft state clear. No blocking issues. Branch choice is visible from review output — user sees `Exportable: no (draft)` and can choose to confirm or reject.

**Reject:** Pass. `Status: rejected`. Safety boundary present: "Rejected drafts are not exportable." Output path and snapshot type shown.

**Validate (rejected copy):** Pass. `Status: valid`. `Confirmation Status: rejected`.

**Review (rejected copy):** Pass. `Exportable: no`. Reason: "only confirmed drafts are exportable." `Confirmation Status: rejected`. Blocking Issues shows "already in terminal state: rejected. Confirmation is not applicable." — correct.

**Export (blocked):** Pass — correctly blocked. `Status: blocked`. `Reason: Draft is not confirmed. Conversion requires confirmation_status=confirmed.` Exit code 1. No export directory created.

---

## File Mutation Safety

| File / Location | Expected | Actual |
|----------------|----------|--------|
| `examples/snapshot_drafts/research_notes_snapshot.json` | Unchanged | ✓ MD5 = `82e25d52aa28a6dd940c87baa99754be` before and after |
| `/tmp/atlas_snapshot_confirm_branch_confirmed.json` | Written (confirmed copy) | ✓ |
| `/tmp/atlas_snapshot_reject_branch_rejected.json` | Written (rejected copy) | ✓ |
| `/tmp/atlas_research_notes_confirm_branch/ASML/notes.md` | Written (export) | ✓ |
| `/tmp/atlas_research_notes_reject_branch/` | Not created | ✓ Absent |
| Any portfolio file | Unchanged | ✓ Not touched |
| Any watchlist file | Unchanged | ✓ Not touched |
| Any journal file | Unchanged | ✓ Not touched |
| Any company facts file | Unchanged | ✓ Not touched |

---

## Language Guardrail Status

No forbidden language found in any output across both branches:
- Review, confirm, reject, validate outputs
- Generated `notes.md` Markdown
- Weekly Review output (all sections)
- Export blocked output

---

## Provider / Network Boundary

No provider, network, or external API calls made. All data from local files. No boundary expansion.

---

## Product Judgment

Both branches of the Snapshot Draft status workflow are clear, safe, and non-mutating.

**What works well:**

1. **Branch choice is visible from review.** A user who reads the review output sees: draft state, exportability (no), blocking issues (none), and a clear Research Notes Review section. The choice to confirm or reject follows naturally.

2. **The confirm branch is a clean three-step chain.** `confirm` → `validate` → `export-research-notes`. Each command is self-contained with its own safety boundary. Weekly Review immediately consumes the result.

3. **The reject branch is a clean two-step chain.** `reject` → `validate/review`. Export is blocked at the command level with a clear reason. No export directory is created.

4. **Safety boundaries are distinct per command.** Confirm says "Export commands must still be run separately." Reject says "Rejected drafts are not exportable." These are different and correct.

5. **The `(research notes)` provenance label in Sections 8/9 remains accurate.** ASML gaps appear with clear source attribution even when generated from the confirm branch.

**Known gaps (non-blocking, unchanged from Sprint 230):**

1. The "Blocking Issues: Draft is already in terminal state: confirmed/rejected. Confirmation is not applicable." message on confirmed/rejected copy reviews could be clearer. It is accurate but may confuse a user who just ran `confirm` or `reject` and then runs `review`. A future wording improvement (e.g., "Draft is confirmed. Re-confirmation is not applicable. Use export commands to proceed.") would help.

2. The example draft is sparse (`thesis_notes` and `reasons_to_wait` absent). A richer example would demonstrate the full generated Markdown output.

3. No `supersede` command. Drafts cannot be marked as superseded without editing JSON.

**Is the status workflow ready before adding conversion types?**

Yes. Both branches work correctly. The confirm/reject pattern is consistent, the safety boundaries are clear, and the export-block is reliable. The workflow is ready to support future conversion types that produce richer local files from confirmed drafts.

---

## Remaining Gaps

1. No `atlas snapshot supersede` command
2. No `draft-to-company-facts` conversion
3. No `draft-to-watchlist` conversion
4. Example draft sparse — richer example would better demonstrate full Markdown output
5. Review blocking issue wording on confirmed/rejected copies could be improved (non-blocking)

---

## Recommended Sprint 233 Target

**Implement draft-to-company-facts conversion.**

After confirming both status branches, the next safest conversion type is company facts. A `atlas snapshot export-company-facts` command would write `company_facts/<TICKER>.json` from a confirmed `company_facts_snapshot` draft without touching portfolio, watchlist, or journal files. It improves Weekly Review evidence presence (Section 8 per-ticker facts check) and follows the same safe export pattern as `export-research-notes`. Less risky than portfolio or watchlist conversion.

Alternative: Add snapshot draft supersede planning if lifecycle completeness is the priority.
