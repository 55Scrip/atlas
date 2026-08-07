# DE-005 — Atlas Decision Memory

**Status:** Draft v0.1. Companion specification to
`docs/ATLAS_DECISION_ENGINE_DOCTRINE.md` §9. Governed by, and subordinate to,
that Doctrine and to `APP-000`. Documentation only — no code accompanies this
specification.

## 1. Scope: Distinct from `UX-008` §15

`UX-008` §15, also titled "Decision Memory," already covers a different
subject: the Investor's own behavioral patterns *across* decisions — *"Over
time, Atlas should be able to identify patterns such as: Repeated
overreaction to short-term price movement... Reluctance to exit positions
whose theses have clearly weakened... Excessive confidence in a specific
sector."* That memory is about how the Investor decides, in general, across
their whole history.

**This specification is about a different memory: a single position's own
thesis over time** — why it was initiated, why it was subsequently added to
or reduced, what was reported against each of those decisions, and whether
the thesis has strengthened or weakened since. `UX-008` §15's investor-
behavioral-pattern memory and this specification's per-position thesis
memory are complementary, not competing: the former is computed across many
positions' worth of this specification's own content, not a substitute for
it. This specification does not restate `UX-008` §15 and does not duplicate
its content.

## 2. Grounding in What Is Already Implemented

This specification is written to be genuinely implementation-ready, so it is
grounded in the actual Decision, Outcome, and Trade records already shipped
(Sprint 4, "Decision Continuity & History") rather than a hypothetical data
model:

- **`DecisionRecord`** (`frontend/src/activity/deriveActivity.ts`) — `id`,
  `caseId`, `decisionType` (the live `BUY | SELL | HOLD | WATCH | PASS`),
  `subject`, `reason`, `confidence` (the Investor's own self-reported
  conviction — see `DE-004` §2's explicit disambiguation from Atlas
  Conviction Level), `decidedAt`, `recordedAt`.
- **`OutcomeRecord`** — `id`, `caseId`, `decisionId`, `statement`, `note`,
  `occurredAt`, `recordedAt` — the reported outcome against a specific,
  named prior Decision.
- **`TradeLogEntry`** — `outcomeId`, `decisionId`, `security`,
  `transactionType`, `quantity`, `executionPrice`, `fees`, `executedAt` —
  what was actually executed against a Decision and Outcome.
- **`deriveActivity()` / `sortActivity()`** — the existing pure function
  that already cross-references these three record types plus current
  holdings into one chronological feed, shared today by `HistoryPage.tsx`,
  `DashboardPage.tsx`, and `InvestmentCasePage.tsx`'s own Decision Timeline.

This specification does not propose a new data model. It states the
doctrine that governs how this already-shipped history SHALL be used by a
future Atlas Recommendation, and what a future implementation phase would
still need to add (Section 4) to fully realize it.

## 3. What Atlas SHALL Remember, Per Position

For a given position (a given Investment Case with an associated portfolio
holding), Atlas's reasoning SHALL be able to state, drawing on the records
in Section 2:

1. **Why the position was initiated** — the `reason` recorded on the
   earliest `BUY`-type Decision for the Case, together with the Evidence
   available at that time.
2. **Why it was subsequently increased** — the `reason` on each later
   `BUY`/Add-type Decision for the same Case, in order.
3. **Why it was reduced** — the `reason` on each `SELL`/Trim-type Decision
   for the same Case that did not fully close the position.
4. **Reported outcomes** — every `OutcomeRecord` linked, via `decisionId`,
   to each of the Decisions above, in the order they occurred.
5. **Whether the original thesis has strengthened or weakened** — a
   synthesis, not a new recorded field: comparing the `reason` stated at
   initiation against the Evidence and Outcomes recorded since, per
   `DE-002`'s Evidence/Counter-Evidence structure. This synthesis is
   produced fresh each time it is needed from the underlying records — it is
   never itself stored as a separate, possibly-stale verdict.

## 4. What This Specification Does Not Yet Resolve

Consistent with `docs/atlas_ux/governance/ADR-003-Recommendation-Identity-and-Terminology-Resolution.md`
R-10's own practice of stating non-decisions explicitly rather than
resolving them by implication, this specification leaves open, for a future
implementation phase: the exact algorithm for judging "strengthened" versus
"weakened" (a qualitative synthesis per Section 3.5, not a scored formula,
per `DE-004` §4's same reasoning against false precision); whether thesis-
strength synthesis is computed on demand or cached; and how far back in a
position's history a single Atlas Recommendation SHALL draw before older
history is summarized rather than restated in full. None of these is
decided by implication anywhere above.

## 5. Application Rule

A future Atlas Recommendation (`DE-001`) for a position with prior recorded
history SHALL reference that history when it is relevant to the direction
being reasoned toward, per `docs/ATLAS_DECISION_ENGINE_DOCTRINE.md` §9. A
Trim recommendation on a position added eighteen months ago, on a thesis
Section 3's synthesis shows has partly played out, is a different
recommendation — reasoned differently, and stated differently under
`APP-002` §6 — than the same direction on a position added last month with
no reported Outcomes yet. A recommendation for a position with no prior
history simply has less of Section 3 to draw on; this specification does
not require history where none yet exists.
