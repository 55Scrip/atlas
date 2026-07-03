# Atlas Weekly Review — Second Trial Findings

**Sprint:** 220
**Date:** 2026-07-04
**Trial bundle:** `examples/weekly_review_realistic/`
**Review date:** 2026-01-01

---

## Trial Command

```bash
.venv/bin/atlas weekly-review \
  --portfolio examples/weekly_review_realistic/portfolio.json \
  --watchlist examples/weekly_review_realistic/watchlist.json \
  --profile examples/weekly_review_realistic/investor_profile.json \
  --journal examples/weekly_review_realistic/decision_journal.json \
  --company-facts examples/weekly_review_realistic/company_facts \
  --financials examples/weekly_review_realistic/financials \
  --as-of 2026-01-01 \
  --scope-notes examples/weekly_review_realistic/scope_notes.md
```

Exit code: 0

---

## Trial Bundle Coverage

| Criterion | Coverage |
|-----------|----------|
| Portfolio holdings | 11 (ASML 24%, NOVO 21%, MSFT 17.5%, LVMH 14%, COLB 4.5%, CASHEUR 4.2%, HXGN 3.8%, DHR 3.5%, EQT 3.0%, ESSITY 2.5%, NESTE 2.0%) |
| Watchlist items | 5 (XYL, ADYEN, RCKWB, VEEV, DXCM) |
| Sectors | 8+ (Healthcare, Semiconductors, Technology, Consumer Discretionary, Industrial Technology, Financials, Consumer Staples, Unclassified) |
| High-exposure holdings | ASML (24%), NOVO (21%) — combined 45% |
| Small position | NESTE (2%), ESSITY (2.5%) |
| Portfolio/watchlist overlap | None in this bundle (VEEV watchlist, no VEEV holding) |
| Aged journal note (>90 days) | NESTE (473 days) ✓ |
| Recent journal note | MSFT (Dec 2025, 22 days) ✓ |
| Profile principles | 7 ✓ |
| Profile constraints | 5 ✓ |
| Company facts: present | ASML, NOVO, MSFT (3 of 16 investable tickers) |
| Company facts: missing | 13 tickers (all others) |
| Financial history: present | ASML, NOVO, MSFT (3 of 16) |
| Financial history: missing | 13 tickers |
| Scope notes | Multi-section markdown ✓ |

---

## Section-by-Section Findings

### Section 1 — Review Scope

**Works well:** Concise summary of inputs loaded. Scope notes preview is useful. Warning count is correctly surfaced. Date, holdings, and watchlist counts are correct.

**Verdict:** Keep as-is.

---

### Section 2 — Portfolio Context

**Works well:** Holdings sorted by weight, sector exposure summary, combined concentration note (ASML + NOVO = 45%), unclassified sector (NESTE) flagged.

**What is missing:** CASHEUR correctly excluded from non-cash concentration checks.

**Verdict:** Keep as-is.

---

### Section 3 — Watchlist Review

**Works well:** All 5 watchlist items render with status, reason, evidence gaps, open questions, observations, and notes. Content is specific to each ticker. Safe language throughout. No recommendation language.

**What feels long:** 5 watchlist items with 3–4 evidence gaps and 3–4 questions each produces a long section. This is expected; the content is genuinely useful and specific.

**Verdict:** Keep as-is. Length is appropriate for the content depth.

---

### Section 4 — Company Reviews Needing Attention

**Works well:** All 5 watchlist items surface as needing more evidence (correct). ASML and NOVO correctly surface as visible holdings (>20% each).

**Verdict:** Keep as-is.

---

### Section 5 — Portfolio Fit and Suitability Notes

**Works well:** Profile is shown as provided, risk tolerance and time horizon surfaced. Constraints listed clearly. Deferred suitability note is present.

**What is missing:** Concentration note for ASML+NOVO (45% combined) could reference the constraint "Avoid concentrated exposure above 25%" — but this cross-reference requires engine wiring.

**Verdict:** Keep as-is. Engine cross-reference deferred.

---

### Section 6 — Risk and Principle Guardrails

**Works well:** All 7 principles listed clearly. Deferred engine wiring note present. Safe language throughout.

**What feels missing:** Principles are listed but not checked against holdings. This is intentional and noted.

**Verdict:** Keep as-is.

---

### Section 7 — Open Decisions

**Works well:** All 4 journal entries render with status, follow-up triggers, and truncated view. NESTE aging note (473 days) is correctly surfaced. MSFT "No Action Warranted" is correctly shown. Wording is calm.

**Verdict:** Keep as-is.

---

### Section 8 — Missing Evidence

**What worked before this sprint:** Per-ticker watchlist evidence gaps (16 gaps across 5 items) are specific and useful.

**Pre-improvement problem:** Per-ticker file presence lines emitted 2 lines per ticker × 12 tickers = 24 lines. Since all 12 tickers were missing both facts and financials, this was highly repetitive.

**Post-improvement (Sprint 220):** Combined line per ticker when both are missing: `Evidence Gap [TICKER]: no local company facts file or financial history file.` — 12 lines instead of 24. Better readability.

**Verdict:** Improved. Remaining length is appropriate — all 12 lines carry distinct ticker identity.

---

### Section 9 — Follow-Up Questions

**What worked before this sprint:** Watchlist open questions (15 questions across 5 items) and journal follow-up triggers are specific and useful.

**Pre-improvement problem:** Per-ticker generic questions emitted 24 identical-format lines (`[TICKER] What local facts would help...`) — no new information per ticker beyond what Section 8 already surfaced.

**Post-improvement (Sprint 220):** Two grouped summary lines replace 24 identical lines:
```
Tickers without local company facts (12): ADYEN, COLB, DHR, ...
Tickers without local financial history (12): ADYEN, COLB, DHR, ...
```
Section 9 is now dominated by the specific watchlist questions and journal triggers, which are genuinely useful.

**Verdict:** Improved significantly.

---

### Section 10 — Non-Actions / Reasons to Wait

**Pre-improvement state:** ~40 lines total:
- 2 decision deferred items (useful)
- 1 evidence gap count (useful)
- 24 per-ticker reasons (one per ticker per missing evidence type — repetitive)
- 1 journal aging reason (useful)
- 7 principle reasons (all identical boilerplate — repetitive)
- 5 constraint reasons (all identical boilerplate — repetitive)
- 3 universal reminders (appropriate)

**Post-improvement (Sprint 220):** ~18 lines total:
- 2 decision deferred items (kept)
- 1 evidence gap count (kept)
- 2 consolidated missing evidence summaries (replacing 24 per-ticker lines)
- 1 journal aging reason (kept)
- 1 principle block header + 7 principle lines (replacing 7 identical boilerplate lines)
- 1 constraint block header + 5 constraint lines (replacing 5 identical boilerplate lines)
- 3 universal reminders (kept)

**Verdict:** Significantly improved. Section 10 now reads as a structured discipline summary rather than a repetition dump.

---

## Profile Context Findings

**Are profile principles in Section 6 helpful?** Yes. Listing all 7 principles in one place gives the user a clear reference for their own stated discipline.

**Are profile-derived Section 10 reasons useful?** Yes, with the block format. The block makes clear that the principles apply collectively, not as 7 independent action items.

**Were principles/constraints too repetitive before?** Yes — 7 lines of identical "stated principle X — supports gathering evidence before changing any decision status." The boilerplate overwhelmed the principle content.

**Are constraints grouped now?** Yes — block format applied to both principles and constraints.

---

## Per-Ticker Evidence Findings

**Are Section 8 per-ticker evidence gaps helpful?** Yes. The combined-line-per-ticker format is readable. 12 lines for 12 tickers with missing files is appropriate.

**Are Section 9 grouped tickers helpful?** Yes. Two summary lines (`Tickers without local company facts (12): ...`) communicate the same information far more compactly than 24 identical-format questions.

**Are Section 10 consolidated summaries helpful?** Yes. The two summary lines `Reason to Wait: Local company facts missing for 12 ticker(s) (...)` communicate the portfolio-level gap efficiently.

**Does output become too long when many tickers lack files?** Post-improvement: Section 8 is 12 lines for 12 missing tickers, Section 9 is 2 lines, Section 10 is 2 lines. This is proportionate and readable.

---

## Journal Aging Findings

**Are aging notes useful?** Yes. NESTE at 473 days is a meaningful signal that deserves visibility.

**Is the 90-day threshold reasonable?** Yes. MSFT at 22 days is correctly not flagged. NESTE at 473 days is correctly flagged.

**Does the wording feel calm and non-urgent?** Yes. "Thesis assumptions may need to be rechecked" is calm and appropriate.

**Should aged notes be grouped separately?** No — the single NESTE note reads well in Section 7 in context and in Section 10 as a reason to wait.

---

## Section 10 Findings

**Is Section 10 useful as a discipline tool?** Yes. Post-improvement it is readable in ~18 lines.

**Is it too long?** No longer. The grouped format has resolved the verbosity problem.

**Does it preserve no-action philosophy?** Yes. "No action is a valid and often appropriate outcome of a weekly review" remains the final reminder before the Atlas closing line.

**Does it avoid sounding like advice?** Yes. No recommendation language found.

---

## Small Improvements Made (Trial-Driven)

All four changes were directly motivated by the trial output review.

| Change | Motivation |
|--------|-----------|
| Section 8: combined "both missing" line per ticker | 24 lines for 12 tickers was repetitive; one line per ticker communicates the same information |
| Section 9: grouped ticker lists replace per-ticker identical questions | 24 identical questions added no information beyond Section 8; two grouped lines are sufficient |
| Section 10: consolidated missing evidence summary (2 lines) | 24 per-ticker reasons were repetitive and overwhelmed the more useful content |
| Section 10: block format for principles and constraints | 12 lines of identical boilerplate replaced by 2 block headers + listed items |

---

## Remaining Implementation Gaps

1. Company facts and financial files are presence-checked only — content is not analysed
2. Profile principles and constraints are displayed but not cross-checked against holdings
3. Section 5 suitability evaluation remains deferred (engine wiring not added)
4. Section 6 principle guardrail checking remains deferred
5. No per-ticker local evidence for portfolio holdings that are not on the watchlist — the quality of Section 4 depends on company facts engine wiring (deferred)
6. No ticker appearing in both portfolio and watchlist in the current realistic bundle — this case is covered in unit tests but not the realistic example

---

## Output Quality Assessment (Post-Improvement)

| Criterion | Result |
|-----------|--------|
| Specific | ✓ — per-ticker evidence gaps, per-journal aging, per-holding concentration |
| Readable | ✓ — post-improvement; Section 10 is ~18 lines, not ~40 |
| Not too long | ✓ — improvements resolved the verbosity problem |
| Not too generic | ✓ — watchlist questions and evidence gaps are specific |
| Not too repetitive | ✓ — post-improvement; grouped formats eliminate boilerplate |
| Calm | ✓ — no urgency language anywhere |
| Safe | ✓ — no forbidden terms |
| Deterministic | ✓ — same inputs produce same output |
| Evidence-aware | ✓ — 16 watchlist gaps + 12 file gaps surfaced |
| Profile-aware | ✓ — principles in Section 6, constraints in Section 5, block in Section 10 |
| Decision-aware | ✓ — 4 journal entries with status, follow-ups, aging |
| Portfolio-aware | ✓ — concentration, sector, weights, roles |
| No-action-aware | ✓ — Section 10 preserves no-action philosophy |
| Usable without source-code knowledge | ✓ — output is self-explanatory |

---

## Recommended Sprint 221 Target

**Group or simplify Section 10 output** — with the Sprint 220 improvements applied, the remaining opportunity is to improve the grouping structure within Section 10 so that different reason types (evidence gaps, profile principles, journal aging) are visually separated. This would make Section 10 scannable rather than requiring the user to read sequentially.

Alternatively, if file evidence quality is the priority: **Improve evidence grouping in Sections 8 and 9** by adding group headings that separate watchlist evidence gaps (qualitative) from local file presence gaps (structural).
