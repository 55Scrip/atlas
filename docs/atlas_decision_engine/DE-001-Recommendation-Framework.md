# DE-001 — Atlas Recommendation Framework

**Status:** Draft v0.1. Companion specification to
`docs/ATLAS_DECISION_ENGINE_DOCTRINE.md` §8. Governed by, and subordinate to,
that Doctrine and to `APP-000`. Documentation only — no code accompanies this
specification.

## 1. Terminology Reconciliation

Before defining what Atlas may recommend, this section fixes exactly which
existing concept is being elaborated, because this repository already
contains three distinct, non-identical vocabularies that use overlapping
language for what turn out to be three different points in the same
lifecycle. Confusing them would violate the discipline
`docs/atlas_ux/governance/ADR-003-Recommendation-Identity-and-Terminology-Resolution.md`
already established for exactly this kind of collision.

**This specification governs Atlas's own advisory output — "Atlas
Recommendation," Concept A of ADR-003, defined in `UX-012` §28: "A specific
action or direction recommended by Atlas, with explicit reasoning."** It is:

- **Not Concept B.** ADR-003 R-02 reserves "Proposed Decision Candidate
  Content" for the separate concept of transient candidate wording that
  flows into the Investor's own Proposed Decision field. An Atlas
  Recommendation is not candidate wording for a field; it is a standalone
  advisory artifact with its own lifecycle (pending, accepted, dismissed,
  acted-upon, per `UX-012` §28).
- **Not a Domain Object.** ADR-003 R-07 declines to adopt either Concept A or
  Concept B as a Domain Object with an identifier or persistence schema, and
  states that "Any future adoption of Concept B as a Domain Object requires
  its own, separate architectural decision, with its own explicit
  justification." The same restraint applies here, by extension: this
  specification defines an Atlas Recommendation's content
  and reasoning, not its persistence model. That is implementation work,
  explicitly out of scope for this doctrine-only phase.
- **Not a Decision.** Per `APP-000` §5 and PP-003/PP-005, only the Investor
  makes a Decision. An Atlas Recommendation is advice offered for the
  Investor's scrutiny; accepting or acting on it does not transfer
  authorship of the resulting Decision to Atlas (the same non-transfer
  principle ADR-003 R-03 already states for Atlas Suggestion acceptance).

**Two further, genuinely different concepts already live in this repository
and are not superseded or altered by this specification:**

1. **The Investor's own recorded decision type** — the live
   `BUY | SELL | HOLD | WATCH | PASS` field
   (`frontend/src/routes/InvestmentCasePage.tsx:287`). This records what the
   Investor actually decided, after the fact. It is filled in by the
   Investor, not computed by Atlas.
2. **The Investor's own stated implementation intent** —
   `UX-012B`'s Implementation Summary component: *"Presents the
   implementation intent associated with a decision — what the user intends
   to do, when, and under what conditions"* with required content
   *"Implementation type (Reduce Position, Add to Position, Initiate
   Position, No Action, Monitor)"* (`UX-012B:422-425`). This records how the
   Investor plans to execute a Decision they have already made. It, too, is
   Investor-authored, not Atlas-generated.

These three concepts sit at three different points in one lifecycle: **Atlas
recommends** (this specification, before any Decision exists) → **the
Investor decides** (`BUY/SELL/HOLD/WATCH/PASS`, the Investor's own record of
what they chose) → **the Investor implements** (`UX-012B`'s Implementation
Summary, the Investor's own record of how they are carrying it out). None of
the three is superseded, renamed, or altered by this specification. A future
implementation MAY choose to pre-populate the Investor's recorded decision
type or implementation type from an accepted Atlas Recommendation's
direction — that is a genuine design question for the implementation phase,
not decided here.

## 2. The Six Directions

An Atlas Recommendation states exactly one of six directions. Each is a
fully reasoned conclusion in its own right — none is a default, and "No
Action" carries the same evidentiary bar as any directional recommendation
(`docs/ATLAS_DECISION_ENGINE_DOCTRINE.md` §2, "Patience is a legitimate
conclusion").

### Buy

**Meaning.** Atlas's evidence supports initiating a new position in a
business the Investor does not currently hold.

**Evidence pattern.** The Business Evaluation (`Doctrine` §4) supports a
positive durability conclusion; the Valuation Philosophy (`Doctrine` §5)
range, under its stated assumptions, suggests the current price is
attractive relative to that range; Portfolio Intelligence (`DE-003`) finds
room for the position without breaching concentration or diversification
considerations for this Investor's specific portfolio.

### Add

**Meaning.** Atlas's evidence supports increasing an existing position.

**Evidence pattern.** Same durability and valuation conditions as Buy, for a
position already held; Decision Memory (`DE-005`) shows the original thesis
has held or strengthened since initiation or the last addition; Portfolio
Intelligence confirms the increase does not push concentration beyond what
this Investor's portfolio can absorb.

### Hold

**Meaning.** No change to the current position is currently supported by the
evidence.

**Evidence pattern.** The thesis, per Decision Memory, has neither
materially strengthened nor materially weakened since the position was
established or last adjusted; valuation sits within its previously stated
range rather than at either extreme; no new evidence changes the Business
Evaluation conclusion. Hold is not silence — it is an explicit statement
that the evidence was reviewed and did not support a change, per `APP-002`
§6's own example register: *"No change to the current position is currently
supported by the evidence."*

### Trim

**Meaning.** Atlas's evidence supports reducing, but not eliminating, an
existing position.

**Evidence pattern.** Either the thesis has partly weakened without being
invalidated, or the position's weight has grown, through appreciation or
prior additions, to a concentration Portfolio Intelligence (`DE-003`) flags
as exceeding what continues to be supported for this Investor — a
valuation-driven or risk-driven partial reduction, not a thesis reversal.

### Exit

**Meaning.** Atlas's evidence supports eliminating the position entirely.

**Evidence pattern.** The original thesis, per Decision Memory, has been
invalidated — a specific, named assumption the thesis depended on has
failed and evidence does not support a replacement thesis — or the Business
Evaluation conclusion has reversed. Exit is reserved for thesis failure or
reversal; a position that is merely too large for the portfolio is Trim, not
Exit — conflating the two would let a sizing problem masquerade as a
business problem, or vice versa.

### No Action

**Meaning.** Atlas does not currently have a directional view to offer on
this specific decision point, and says so rather than defaulting to Hold.

**Evidence pattern.** Distinct from Hold: No Action applies where there is
no established position and no active decision context requiring a view
right now (for example, a Watchlist entry with genuinely nothing new to
report) — as opposed to Hold, which is an active, evidence-based statement
about an existing position. Where the evidence is not merely quiet but
genuinely insufficient to support any of the five directions above, Atlas
states that directly as Insufficient Evidence (`DE-004`) rather than
defaulting to No Action to appear to have completed the analysis.

## 3. Required Explainability Elements

Per `ATLAS_CONSTITUTION.md`'s Non-Negotiable Principle "Every Atlas Rating
must be explainable," every Atlas Recommendation, regardless of direction,
SHALL include all four of the following. These four elements are not new
invention — they are this specification's application of the Reasoning
Structure (`DE-002`) to the specific case of a recommendation:

1. **Why** — the specific conclusion from Business Evaluation, Valuation
   Philosophy, and Portfolio Intelligence that the direction follows from.
   Never a bare label ("undervalued," "too concentrated") without the
   reasoning behind it.
2. **Based on what evidence** — the Evidence (`DE-002` §Evidence) that
   supports the Why, each item with its source and quality, per `APP-002`
   §7's Known/Estimated/Possible/Unknown conventions.
3. **With what uncertainty** — the Atlas Conviction Level (`DE-004`) and the
   specific reason for it: what is well-established versus what remains
   genuinely open.
4. **What could change the conclusion** — the specific evidence, event, or
   threshold that would cause Atlas to revise the recommendation, per
   `ATLAS_CONSTITUTION.md`'s Trust Principle "Explain what could change
   Atlas' view."

A recommendation missing any of the four is incomplete and SHALL NOT be
presented as though it were a finished Atlas Recommendation.

## 4. Relationship to `APP-002` Recommendation Language

Every recommendation's Why statement SHALL be expressed in `APP-002` §6's
evidence-attributed register, never as an instruction. `APP-002` §6's own
table already shows the exact transformation this specification's six
directions require in prose: "Buy this stock" becomes "Current evidence
suggests this position may be worth initiating"; "Hold" becomes "No change
to the current position is currently supported by the evidence." This
specification names the direction Atlas has concluded; `APP-002` governs how
that conclusion is written as a sentence to the Investor.
