# DE-006 — Atlas Execution Guidance

**Status:** Draft v0.2. Companion specification to
`docs/ATLAS_DECISION_ENGINE_DOCTRINE.md` §8 (Recommendation Framework), by
extension. Governed by, and subordinate to, that Doctrine and to `APP-000`.
Documentation only — no code, no frontend, no backend accompanies this
specification. Discovered as a gap during the design of the Investment Case
Recommendation Workspace (frontend design, not yet implemented): that design
needed a "Suggested Execution" block with no domain concept behind it. This
specification exists to name that concept, precisely, before anything is
built against it.

**Amendment pass note (v0.2, "DE-006 Amendment Draft" sprint).** This
revision closes a narrow, investigated gap: an external design exploration
("Actionable Recommendation Engine") proposed capability this document did
not yet name — multiple qualitative ways to carry out one direction,
explicit-constraint filtering, and bounded post-action arithmetic — and,
separately, surfaced two wording ambiguities in the v0.1 text. Both were
independently investigated and found to require only narrow, additive
changes, never a redesign: no new bounded context was created, the external
exploration's own terminology and its general-purpose "portfolio impact"
and "entry range" computation ideas were rejected as out of scope or
unsupported by any implemented capability, and every invariant this
document already stated — one Guidance object per Recommendation, no
ranking, no optimization, the two-stage lifecycle, the unidirectional
dependency on Recommendation — is unchanged. Each amended section below
carries its own inline note marking exactly what changed and why; §12 is
this revision's self-review, in the same form `DE-007` §14 already
established for exactly this purpose.

**Consistency-review addendum (same v0.2, pre-merge).** A final review,
performed before this draft's own "ready to merge" status could stand,
tested the amendment against itself and found three further corrections
required — not a redesign, but gaps the three-amendment structure itself
did not yet close: (1) `targetAllocationRange`, inherited unchanged from
v0.1, had never been tested against the same "is there a real normative
source" standard Amendment 3's own investigation applied to "recommended
quantity" — it fails that test identically, and is now marked unavailable,
with the same marking cascaded into Post-Action Impact, which depends on
it; (2) a user-facing `label` was found insufficient as the stable
reference a future Decision Capture integration would need, so a
non-localized `approachKey` was added — a plain field, not a new Aggregate
or Entity; (3) explicit constraints (§2.1) were found to have no canonical
source anywhere in this repository today, now stated directly as an
external dependency rather than left implied. §12.1 records this pass in
full, in the same self-review form as §12.

## 1. Definition

**Execution Guidance is Atlas's advisory input on how an already-stated
Recommendation direction could reasonably be carried out.** It answers
exactly one question — *"If this direction is followed, how might it
reasonably be carried out?"* — and no other. It does not answer *"what
should I do"* (that is Recommendation, `DE-001`) and it does not answer
*"what do I intend to do"* or *"what actually happened"* (that is,
respectively, the Investor's own Decision/Implementation Intent and the
distinct, unspecified concept of Actual Execution — see §4).

Execution Guidance does **not** require that the Investor has accepted the
underlying Recommendation. It may accompany a Recommendation that is still
pending (`UX-012` §28's own pending/accepted/dismissed/acted-upon states) —
one of its purposes is precisely to help the Investor evaluate the
Recommendation itself, before any acceptance, dismissal, or action has
occurred. Acceptance belongs to the Investor's own decision lifecycle, not
to Execution Guidance's own definition — see §7 for the full relationship,
and §6 for how this splits Execution Guidance's own lifecycle into a
computed stage (before any response) and a historical stage (only after
one), mirroring the identical split `DE-007` establishes for Recommendation
itself.

Execution Guidance is guidance: a small set of ranges, qualitative
framings, and named assumptions, held to the same evidence-attributed,
uncertainty-disclosed discipline `APP-002` and `DE-004` already require of a
Recommendation itself. It is never an instruction, never a mechanism, and
never a number precise enough to hand to a broker.

It exists because Recommendation, on its own, leaves a real gap: a Buy
direction with no execution content tells the Investor Atlas believes
initiating a position is supported, but nothing about whether that means
today, in ten equal steps over six months, or opportunistically on
weakness — and an Investor filling that gap with their own guess, believing
it came from Atlas's own reasoning, is a worse outcome than Atlas stating
the gap and addressing it honestly, at the same evidentiary standard as
everything else Atlas states.

## 2. Responsibilities

**Amendment note (v0.2).** This section's content is unchanged in kind —
every element the v0.1 text required an Investor be able to see is still
required. What changes is shape only: four elements that describe *how* a
direction could be carried out (target allocation range, execution range,
accumulation approach, urgency) move from single scalar fields into an
**Execution Approach** — one qualitative way to carry the direction out —
because a single direction can legitimately be carried out more than one
reasonable way (immediately, gradually, or via a smaller initial position
held for reassessment, among others), and forcing all of them into one
scalar field either silently picked one or fabricated a false single
answer. This does **not** create multiple Execution Guidance objects, does
not rank the approaches it lists, and does not recommend one over another
— see the invariants stated immediately below and reconfirmed in §7.

Where a Recommendation's direction is Buy, Add, Trim, or Exit (§7 states why
Hold and No Action are excluded), Execution Guidance SHALL, when present,
carry one or more **Execution Approaches**, and, at the Guidance level (not
per-approach — these describe the underlying Recommendation's own
conditions, which every approach shares), the valuation-sensitivity,
assumptions, validity-conditions, and Atlas Conviction Level content the
v0.1 text already required:

**Per Execution Approach** (`approaches`, §9 — an ordered list whose order
carries no meaning; see the invariant below):

- A short **label** identifying the approach (e.g., "immediate," "staged
  over time," "smaller initial position, reassess later") — naming only,
  never a ranking signal, and never itself a stable reference — see the new
  **`approachKey`** field below.
- A **rationale**: why this is a reasonable way to carry out the direction,
  in the same evidence-attributed register as everything else this
  specification requires.
- An **`approachKey`** (new, v0.2 consistency-review correction) — a short,
  stable, non-localized identifier for this approach entry, distinct from
  `label`. See the note at the end of this list for why this is required.
- A **target allocation range** — a minimum and maximum share of the
  portfolio the position might reasonably move toward or away from under
  this approach — never a single target weight. **Consistency-review
  correction (v0.2):** this field is inherited unchanged from v0.1, and
  this revision's own audit found it had never been tested against the
  same standard Amendment 3's investigation applied to "recommended" or
  "optimal" quantity (that investigation's Part 7). Applying that same
  test here: describing a position's *current* allocation (`DE-003`
  Allocation/Concentration — real, computed) and prescribing a *target*
  allocation are different semantic claims, and no doctrine anywhere in
  this repository — not `DE-003`'s seven factors, not `DE-001`, not
  `DE-008` — defines a normative basis for what a position's allocation
  *should* become. This field therefore has the same status as
  "recommended quantity" already found to require a missing normative
  sizing model: it is not computable today from any existing doctrine or
  implemented Core capability. It is **not removed** from this
  specification — a future, separately-justified sizing doctrine may yet
  define one — but until such doctrine exists, this field SHALL be treated
  as unavailable and SHALL NOT be populated with an approximated or
  heuristic range. Where unavailable, it is simply absent (`null`), the
  same honest-absence discipline already applied to `executionRange`'s
  `valuation_relative` basis above. **This has a direct downstream
  consequence for Post-Action Impact (§2.2): because that capability
  brackets its arithmetic by this field's own endpoints, Post-Action
  Impact is, for the same reason, currently unavailable wherever this
  field is unavailable — see §2.2's own updated note.**
- An **execution range** — a price range or a range relative to the
  Valuation section's own stated fair-value range (`Doctrine` §5) — never a
  single-point price, carrying forward `docs/ValueScenarioReview.md`'s
  already-absorbed principle (`Doctrine` §12) that Atlas does not issue
  single-point price targets, applied here to execution content
  specifically, not only to valuation content. **Amendment note (v0.2):**
  the `"valuation_relative"` basis for this range currently has **no
  implemented Valuation capability producing a fair-value range to be
  relative to** — neither `DE-015`'s Valuation Support (a categorical
  `SUPPORTED`/`NOT_SUPPORTED`/`INSUFFICIENT_INPUT` status, never a numeric
  range) nor Outlook (`DE-014`, a percentage expected-return range over
  time, explicitly never a price target) produces one. This basis therefore
  currently has no data source. It is not removed from this specification
  — the master Doctrine's own Valuation Philosophy (§5) still commits Atlas
  to expressing value as a range, and a future Valuation capability may yet
  produce one — but until such a capability exists, this basis SHALL NOT be
  populated with a fabricated or approximated figure. Where no such
  capability exists, this field is simply absent (`null`), the same honest-
  absence discipline every other field in this specification already
  follows.
- An **accumulation approach category** (staged versus lump-sum) — never a
  schedule, never specific dates. A "smaller initial position, reassess
  later" approach is modeled as `staged` with its distinguishing content
  carried in `rationale`, not as a third enum value — this keeps the
  category small while still letting the approach be named and explained
  precisely.
- An **urgency** framing as a qualitative category (time-sensitive versus no
  particular urgency) with its reason — never a deadline.
- **Post-Action Impact** (Amendment 3, v0.2) — see the new subsection below.

**Why `approachKey` is required (v0.2 consistency-review correction).** A
future Decision Capture integration (§9B) needs a stable way to record
"which approach, if any, the Investor selected." A user-facing `label`
cannot serve this purpose: it is translated per `UX-012`'s existing
localization system (the same approach reads differently in English and
Swedish), it may be reworded in a future copy pass without the underlying
approach changing, nothing prevents two approaches from generating similar
or identical label text, and a persisted historical record must not depend
on matching mutable presentation strings to reconstruct what was actually
shown. `approachKey` is not a new Aggregate or independent Entity — it
carries no lifecycle, no repository, and no meaning outside the one
Guidance object it appears in (scoped by that object's own
`recommendationId`/`recommendationInstanceId`, exactly as `recommendationInstanceId`
itself is "stable for the lifetime of one computed instance," `DE-007` §6,
not a globally-durable identifier). It is the smallest addition that makes
historical replay and guidance-versus-execution comparison (§9B) possible
without relying on presentation text.

**At the Guidance level, shared across every approach it lists** (unchanged
from v0.1 except in name — these were never approach-specific, since they
describe the Recommendation's own conditions, not any one way of acting on
it):

- The **valuation sensitivity** of the guidance: which specific Valuation
  assumptions (`Doctrine` §5, `DE-002` §2.2) it depends on, so the Investor
  can see exactly what would make it stale.
- Its **assumptions** explicitly ("this guidance assumes…") and its
  **validity conditions** explicitly ("valid while…"), per §5 below.
- Its own **Atlas Conviction Level** (`DE-004`), stated independently of the
  Recommendation's own Conviction Level — see §5.
- **Explicit constraints** (Amendment 2, v0.2) — see the new subsection
  below.

**Invariant (unchanged by this amendment, restated for emphasis): exactly
one Execution Guidance object exists per directional Recommendation.**
`approaches` is an internal list on that one object — never a set of
separate Execution Guidance objects, each with its own identity, its own
lifecycle, or its own `recommendationId`. See §7.

**The order of `approaches` SHALL NOT be read, presented, or treated as a
ranking, a preference, or a recommendation of one approach over another.**
Where a canonical order is needed for stable rendering, it SHALL be a
neutral one (e.g., generation order or alphabetical by `label`) — never an
order implying "Atlas's first choice."

### 2.1 Explicit Constraints (Amendment 2, v0.2)

Execution Guidance MAY be generated against a small set of **explicit
constraints** — investor-stated or system-stated limits already known at
generation time (for example, an investor-stated cap on exposure to a
sector, or a stated no-margin rule). Where a constraint is present:

- Any candidate approach that would violate a stated constraint SHALL NOT
  appear in `approaches` at all. Constraints are a **feasibility filter
  applied before generation completes**, not a note attached after the
  fact and not a reason to mark an approach as inferior.
- Constraints SHALL NOT be used to rank, score, or order the approaches
  that remain feasible — their only effect is inclusion or exclusion.
- Constraints SHALL NOT be inferred, estimated, or derived by any
  computation this specification defines — only an explicitly stated
  constraint (from the Investor or from an already-adopted system rule)
  may exclude an approach. Introducing an inferred constraint would be
  exactly the kind of undisclosed decision logic §3 already prohibits for
  everything else this document governs.
- Where a stated constraint excludes every candidate approach, Execution
  Guidance is simply absent for that Recommendation (§6, §10) — the same
  honest-absence outcome as when no approach clears even Low conviction
  (§5).

**No canonical source for an explicit constraint currently exists
(consistency-review correction, v0.2).** This subsection specifies a
legitimate *mechanism* (a feasibility filter with a stated, exclusion-only
effect) — it does not, on its own, supply anything to filter with. Checked
directly against the real repository: no domain object, API, or adopted
doctrine anywhere (`DE-003`'s seven factors, the real `DecisionRecord`/
`OutcomeRecord`/`TradeLogEntry` types, or elsewhere) lets an Investor record
a hard constraint (a sector cap, a no-margin rule, or similar), and no
system-stated regulatory or platform constraint source exists either.
`DE-003`'s Allocation/Concentration data are current-state **facts**, not
investor-settable **limits**, and SHALL NOT be treated as constraints under
this section. Until a canonical constraint source is separately adopted,
this subsection describes an **external dependency this specification does
not itself satisfy**: `constraints` (§9) is always the empty list, and this
section's exclusion mechanism, while correctly specified, has nothing to
act on. This is not a defect in the mechanism — it is the same honest-
absence discipline applied everywhere else in this document — and it is
not resolved here; inventing a constraint-capture mechanism is explicitly
out of scope for this correction.

### 2.2 Post-Action Impact (Amendment 3, v0.2)

Each Execution Approach MAY carry a **Post-Action Impact**: a small,
strictly arithmetic statement of what the position's current-state facts
(`DE-003` — Allocation, Concentration, and, where already available
elsewhere in the Investment Case, current price and cash) would mechanically
become **at the two endpoints of that approach's own already-disclosed
`targetAllocationRange`** — never for any other quantity, and never for a
single named exact quantity (`§3` already prohibits stating an exact share
or dollar quantity; this amendment does not relax that).

**Currently unavailable in practice (consistency-review correction, v0.2).**
Because this capability's only legitimate bracket is the accompanying
approach's own `targetAllocationRange`, and §2 now states that field has no
implemented or doctrinal source today, Post-Action Impact is, for the same
reason, **currently unavailable** wherever `targetAllocationRange` is
unavailable — which, as of this revision, is everywhere. This section is
not removed: its specification remains correct and becomes usable the
moment a real `targetAllocationRange` source exists, exactly as designed.
Until then, `postActionImpact` is simply absent (`null`) on every approach,
per the same honest-absence discipline as every other unsourced field in
this document — it SHALL NOT be approximated from any other figure (e.g.,
current weight alone, with no target endpoint) as a workaround.

Where computable, Post-Action Impact states, as ranges bracketed by the
approach's own `targetAllocationRange` endpoints:

- **Resulting position weight.**
- **Resulting cash**, where the Investment Case's already-fetched cash
  figure is available.
- **Resulting concentration**, using `DE-003`'s existing
  `Concentration`/`ConcentrationLevel` data.
- **Resulting exposure**, where an already-computed exposure figure exists
  elsewhere in the Investment Case.

**This is arithmetic over already-known facts, never a new computation
about the facts' meaning.** See §3 for the explicit boundary this
capability SHALL NOT cross.

## 3. Explicit Non-Responsibilities

**Amendment note (v0.2).** Three bullets below are new (marked), narrowly
scoped to the two capabilities §2.1/§2.2 add. Every bullet already present
in v0.1 is unchanged.

Execution Guidance SHALL NOT, under any circumstance:

- Compute, promise, or imply a guaranteed price, outcome, or result.
- Prepare, place, route, or transmit a broker order, or reference order
  mechanics (order type, limit/market, time-in-force).
- State an exact price target, an exact share or dollar quantity, or an
  exact execution date or time. **(Unchanged by Amendment 3, v0.2): Post-
  Action Impact (§2.2) computes only at the two endpoints of an approach's
  own already-disclosed range — it does not, and this rule does not permit
  it to, introduce a single named quantity by another route.**
- Read, assume, or reference brokerage account state, tax lots, available
  cash beyond the portfolio weight and cash figures already surfaced
  elsewhere in the Investment Case, or any other account-specific mechanics.
- Apply a portfolio-optimization algorithm (mean-variance, efficient
  frontier, or similar) or an execution algorithm (TWAP, VWAP, smart order
  routing, or similar) to derive any of its content. Every range and
  category above is a qualitative product of the same evaluators already
  producing Business/Valuation/Risk/Portfolio Intelligence content
  (`Doctrine` §§4–6), never a new computational model.
- Compute or project a resulting portfolio state after the guidance is
  followed, **except** for the narrowly-scoped Post-Action Impact arithmetic
  §2.2 defines. That narrow exception SHALL NOT be read as authorizing
  anything broader: Post-Action Impact SHALL NOT state or imply whether a
  resulting state is more or less desirable; SHALL NOT compute or reference
  expected return, risk-adjusted return, or any change in diversification;
  SHALL NOT be computed for any quantity beyond the accompanying approach's
  own already-disclosed range endpoints; and SHALL NOT be presented as a
  recommendation of the approach it accompanies over any other. Anything
  beyond this narrow arithmetic remains Portfolio Simulation's domain, still
  undefined — see §8. **(New, v0.2 — Amendment 3.)**
- Rank, score, or otherwise recommend one Execution Approach (§2, `approaches`)
  over another, or present their listed order as a preference — see §2's own
  invariant. **(New, v0.2 — Amendment 1.)**
- Infer, estimate, or derive an explicit constraint (§2.1) computationally;
  only a constraint the Investor or an already-adopted system rule actually
  states may exclude an approach, and its exclusion effect SHALL NOT extend
  to ranking or scoring the approaches that remain. **(New, v0.2 —
  Amendment 2.)**
- Be presented, recorded, or treated as a Decision. Per `APP-000` §5 and
  `DE-001` §1, only the Investor decides; Execution Guidance is advice about
  an already-advisory Recommendation, one further step removed from
  authorship, not closer to it.

## 4. Domain Boundaries — Five Concepts, Not One

This specification's single most important structural claim is that five
concepts, easily collapsed into one another in casual language, are
distinct and SHALL NOT be merged. In particular, correcting an imprecision
in this document's own first draft: the Investor's own recorded intent and
the factual market event that intent may or may not lead to are **two
different concepts**, not one "Order Execution" bucket — conflating them
would silently claim the existing `BUY/SELL/HOLD/WATCH/PASS` field and
Implementation Summary record a completed trade, when they record only what
the Investor intends or has decided.

| Concept | Answers | Authored by | Status in this repository |
|---|---|---|---|
| **Recommendation** (`DE-001`) | What should I do? | Atlas | Specified in full; not yet implementable — `kind` is always `recommendation_withheld` today (`atlas/decision_engine/stages/recommendation.py:61`) |
| **Execution Guidance** (this document) | If that action is taken, how might it reasonably be carried out? | Atlas | Specified here for the first time; not implemented |
| **Decision / Implementation Intent** | What do I intend or decide to do? | The Investor | **Already exists.** The live `BUY \| SELL \| HOLD \| WATCH \| PASS` field (`frontend/src/routes/InvestmentCasePage.tsx:301`) — `DE-001` §1's "Investor's own recorded decision type" — and `UX-012B`'s Implementation Summary component (Implementation type: Reduce/Add/Initiate Position, No Action, Monitor; target allocation or quantity; states Pending, Partially Executed, Complete, Not Required) — `DE-001` §1's "Investor's own stated implementation intent." Both record intent or decision, never a completed market event. |
| **Actual Execution** | What factual market action actually occurred, if any? | The market, as a fact of what the Investor's brokerage did | **Not defined anywhere in this repository.** Named here only to draw a boundary against Decision/Implementation Intent — not specified, not scoped, not designed here |
| **Portfolio Simulation** | What would my portfolio look like if I did this? | Atlas (computational, hypothetical) | **Not defined anywhere in this repository.** Named in §8 only to draw a boundary against it — not specified, not scoped, not designed here |

Decision/Implementation Intent is the Investor's own record of what they
intend or have decided to do — it is not superseded, renamed, or altered by
this specification, exactly as `DE-001` §1 already establishes for the
Investor's `BUY/SELL/HOLD/WATCH/PASS` field and Implementation Summary
relative to Recommendation.

Actual Execution — the factual market action that actually occurred, if
any (an order that was placed and filled) — is distinct from
Decision/Implementation Intent, which records what the Investor intends or
decided, not what factually happened in the market: an intent can be
recorded and later never carried out, only partially carried out, or
carried out differently than intended. This specification does not design
an Actual Execution object or claim it exists; it states only that Decision/
Implementation Intent and Actual Execution SHALL NOT be conflated, and that
any future wording describing the existing `BUY/SELL/HOLD/WATCH/PASS` field
or Implementation Summary SHALL NOT describe them as recording a completed
trade.

A future implementation MAY choose to let Execution Guidance for an
accepted Recommendation pre-populate fields of the Investor's own
Implementation Summary — that is a genuine design question for the
implementation phase, not decided here, mirroring exactly the same
deferral `DE-001` §1 already states for Recommendation's own relationship
to the Investor's recorded decision type.

## 5. Uncertainty

Execution Guidance SHALL be phrased exclusively in the assumption-
conditional register its own name implies — "This guidance assumes…",
"Valid while…", "May change if…" — extending `APP-002` §6's
evidence-attributed register and §7's Known/Estimated/Possible conventions
to execution content specifically. It SHALL NOT be phrased as a bare
statement of fact ("buy at $142") under any circumstance; every figure
SHALL appear inside a stated range, attached to a stated assumption.

Execution Guidance's Atlas Conviction Level (`DE-004`) is stated
**independently** of, and MAY be lower than, the Conviction Level attached
to the Direction it depends on. A Recommendation can hold High conviction
that Buy is the right direction while the specific execution range carries
only Medium conviction — direction and execution-range confidence are
different epistemic claims about different questions, and stating one
figure for both would silently overstate whichever one is actually weaker.
Where Execution Guidance's own evidence does not support even Low
conviction in any range, no Execution Guidance is issued at all — the
Recommendation stands with its own Direction and Conviction (`DE-002`
§2.5–2.6) and no execution content is shown, rather than a range being
stated at an unsupported confidence.

No action call accompanies a range as a bare fact — the same discipline
`docs/ValueScenarioReview.md` (absorbed at `Doctrine` §12) already states
for scenario-based value ranges applies here without modification: a range
is a structured way to communicate uncertainty, not a prediction, and is
never presented as though a range alone justifies acting.

**The execution range specifically is not a market-timing signal.** Where
an execution range (§2) is present, it SHALL NOT be presented, or read, as
"Atlas predicts the stock will trade in this range." It states, instead,
that "under the valuation and scenario assumptions already disclosed
(`Doctrine` §5, this guidance's own `valuationSensitivity` and
`assumptions`, §2), this range is consistent with the Recommendation." The
difference is not cosmetic: the first is a forecast of future price
behavior Atlas has no basis to make; the second is a conditional statement
about consistency with assumptions that are already named and already
visible to the Investor, and that stops being true the moment those named
assumptions stop holding (§6, Invalidated). An execution range presented
without its governing assumptions attached is incomplete and SHALL NOT be
shown on its own.

### 5.1 Generation Legitimacy Versus Historical Validity (Editorial clarification, v0.2)

This document has always kept these two questions separate in effect,
through §§2–3 (Responsibilities and Non-Responsibilities) on one side and
§6 (Lifecycle) on the other, without ever naming the separation directly.
This subsection names it, changing no behavior:

- **Generation legitimacy** — whether an Execution Approach (or an entire
  Execution Guidance) was permitted to be produced at all, given §§2–3's
  Responsibilities/Non-Responsibilities and §2.1's explicit constraints.
  This is checked exactly once, at the moment of computation. It is never
  re-checked later, and a computed instance that was legitimate when
  generated does not later become "illegitimate" — if the environment
  moves, what happens instead is the separate question below.
- **Historical validity** — whether Execution Guidance content the Investor
  was already shown remains applicable **now**. This question can only be
  asked of a persisted `HistoricalExecutionGuidanceSnapshot` (§6, §9B); it
  has no meaning for a merely Computed Execution Guidance, which has
  nothing persisted to compare later analysis against (§6 already states
  this for the `Invalidated` state specifically — this subsection states it
  as the general rule the `Invalidated` state is one instance of).

**A single generic "validate" operation SHALL NOT be used for both
questions** — doing so would obscure exactly the distinction this
subsection exists to preserve: legitimacy is a one-time gate at generation;
validity is a recurring check against a persisted historical fact. Any
future implementation surface (API, service, or otherwise) that needs both
capabilities SHALL name them distinctly.

## 6. Lifecycle

**Corrective pass note.** This section previously described a single
lifecycle without stating when its "retained and visibly marked, not
deleted" language actually applies — an ambiguity `DE-007`'s own review
surfaced and explicitly deferred back here. This revision resolves it by
stating, directly, that Execution Guidance's lifecycle divides into two
stages, exactly mirroring the split the approved Recommendation Ontology
Decision already establishes for Recommendation itself (`DE-007` §1, §5,
§8): a *computed* stage, ephemeral and recomputed fresh, and a
*historical* stage, persisted, that exists only once an Investor has
responded. No new state is introduced by this clarification — the same
three states this document has always named (`active`/`invalidated`/
`withdrawn`) are unchanged; only the precondition for the latter two —
that a persisted historical record exists at all — is now stated
explicitly rather than assumed.

### Computed Execution Guidance (pre-response — ephemeral, no persisted status)

While a Recommendation exists only as a `ComputedDirectionalRecommendation`
(`DE-007` §8A) — that is, before the Investor has responded to it —
Execution Guidance exists in exactly the same form: recomputed fresh
alongside the Recommendation on every analysis run, for as long as the
Direction remains Buy, Add, Trim, or Exit (Hold, No Action, and
Recommendation Withheld never produce it — unchanged from before, and
still true at this stage). It carries **no persisted status field, no
`createdAt`, no `updatedAt`** — it simply is, or is not, present in the
current computation, the same way `ComputedDirectionalRecommendation`
itself carries no lifecycle-state field of its own (`DE-007` §5, §8A).

**There is nothing at this stage that can meaningfully become
"Invalidated," and nothing that can meaningfully be "Withdrawn."**
Invalidation is a statement that current analysis no longer supports
content that was previously *recorded* — and before an Investor response,
nothing has been recorded. A Computed Execution Guidance that no longer
clears its own validity conditions on a later request is not
"invalidated" — it is simply absent from that later request's fresh
computation, exactly as a Computed Directional Recommendation that no
longer clears its gate is simply absent, not "withdrawn," from a later
request (the identical point `DE-007` §4 already makes about
Recommendation Withheld replacing, not superseding, an unresponded-to
computation). Nothing is retained at this stage, because nothing was ever
stored.

### Historical Execution Guidance Snapshot (post-response — persisted, immutable)

- **Created** — only in the same event that creates a
  `HistoricalRecommendationSnapshot` (`DE-007` §5, §8B): when the Investor
  responds (accepts or dismisses) to a Recommendation whose Direction is
  Buy, Add, Trim, or Exit, and a Computed Execution Guidance exists at
  that moment, its content is captured, verbatim, alongside the
  Recommendation's own snapshot. If no Computed Execution Guidance existed
  at response time (§5's own "no Execution Guidance issued" case), none is
  snapshotted — there is nothing to capture.
- **Active** — the snapshot as captured, not yet contradicted by any later
  analysis.
- **Invalidated** — when a *later* analysis run's fresh computation no
  longer supports the specific validity conditions the snapshot recorded
  (§2, §5) — for example, price or valuation has since moved outside the
  range the snapshot assumed. The snapshot itself is retained and visibly
  marked, not deleted, per the same immutability discipline `UX-012B`'s
  Historical Section already establishes for locked content — language
  that is now fully coherent, since a real persisted record exists to
  retain and mark. **This state is reachable only for a Historical
  Execution Guidance Snapshot** — it cannot be triggered for a merely
  Computed Execution Guidance (above), which has nothing to be invalidated
  relative to.
- **Withdrawn** — when the Recommendation snapshot it depends on is itself
  superseded (`DE-007` §5, §6: a later Investor response produces a new
  `HistoricalRecommendationSnapshot` for the same Case). **The underlying
  Recommendation no longer stands** — a Historical Execution Guidance
  Snapshot cannot outlive the Recommendation snapshot it was captured
  alongside.

Invalidated and Withdrawn remain two distinct states, not one, precisely
as before: a validity condition can be breached (Invalidated) while the
Recommendation snapshot the Investor actually responded to is still fully
intact — **the historical Execution Guidance still exists; current
analysis simply no longer supports it.** Withdrawn is different in kind:
the underlying Recommendation snapshot itself no longer stands, so nothing
remains for the execution content to describe how to carry out.

## 7. Relationship to Recommendation

**Amendment note (v0.2): this section is unchanged by Amendments 1–3.**
§2's `approaches` list does not alter the relationship described below in
any way — it is a list internal to the one Execution Guidance object this
section already establishes exists per directional Recommendation, not a
mechanism for producing more than one such object. Every statement below
("always a 1:1-or-nothing dependent... never freestanding") continues to
mean exactly what it meant in v0.1, applied now to an object that may
internally list more than one way of carrying its one Recommendation out.

Recommendation answers *what*; Execution Guidance answers *how, if you do
it*. The relationship is asymmetric, and the asymmetry is load-bearing:

**Can a Recommendation exist without Execution Guidance? Yes.** `DE-001`
and `DE-002` already fully specify a complete, self-contained Recommendation
with zero execution content. Hold and No Action have no execution content
by definition — there is nothing to carry out. Recommendation Withheld
(`DE-002` §4) likewise has none. Even a directional Buy/Add/Trim/Exit
Recommendation is complete and meaningful under `DE-001` §3's four required
elements (why, evidence, uncertainty, what could change it) without any
execution content at all. This is why Execution Guidance MUST be modeled as
a separate, optional, dependent object rather than a mandatory field on
Recommendation itself: making it mandatory would force Hold, No Action, and
Recommendation Withheld to either fabricate meaningless empty execution
fields or be special-cased around a field that should not exist for them —
exactly the kind of state-inappropriate field this codebase's own domain
modeling already avoids (`RecommendationStateView`'s own kind-gated shape,
where withheld and directional states carry structurally different content
rather than one shape with irrelevant nulls).

**Can Execution Guidance exist without a Recommendation? No.** Execution
Guidance has no meaning except relative to a specific, already-stated
direction. Issuing execution content with no Recommendation behind it would
be an ungrounded advisory statement of exactly the kind `DE-002` §2.5
already prohibits for Direction itself (a conclusion not traceable to the
sections above it) — and would risk reading as an unprompted trade
suggestion, the single outcome this whole specification exists to prevent.
Execution Guidance is therefore always a 1:1-or-nothing dependent of one
specific directional Recommendation, referenced by `recommendationId`,
never freestanding.

**Execution Guidance does not require Investor acceptance of that
Recommendation.** It may be present while the Recommendation is still
`pending` (`UX-012` §28) — the two are evaluated by the Investor together,
and seeing a concrete, honestly-bounded account of how a direction could be
carried out is part of what informs the decision to accept it, not
something that only becomes relevant afterward. Acceptance, dismissal, and
acted-upon are states of the Investor's own decision lifecycle; they are
not preconditions written into Execution Guidance's own definition (§1) or
its own lifecycle (§6, which gates creation solely on the Recommendation's
Direction, never on the Investor's response to it).

The full chain, stated end to end, with the boundary this section and §4
draw made explicit:

```
Directional Recommendation (Buy / Add / Trim / Exit)      — Atlas, DE-001
        │  optional (§7)
        ▼
Execution Guidance                                          — Atlas, this document
        │  the Investor evaluates both together, regardless
        │  of the Recommendation's pending/accepted state
        │  (accept / dismiss, `UX-012` §28 states)
        ▼
Investor Decision / Implementation Intent                   — the Investor
  (BUY/SELL/HOLD/WATCH/PASS, Implementation Summary)          (§4)
        │  if actually carried out in the market
        ▼
Actual Execution                                              — a market fact,
  (not designed by this document — boundary only, §4)          out of scope
```

Portfolio Simulation (§8) is not part of this chain at any point — it is a
separate, hypothetical "what if" concept, usable independently of whether a
Recommendation exists at all, not a downstream step of one.

Execution Guidance moves through this chain's first box in lockstep with
the Recommendation it depends on: both exist only as current, computed
analysis until the Investor responds, and both gain a persisted historical
form in the same event, at the same moment, never separately (§6's full
two-stage lifecycle).

Hold, No Action, and Recommendation Withheld remain entirely outside this
chain — they never produce Execution Guidance (§6, above), and none of the
downstream steps changes that.

## 8. Relationship to Portfolio Simulation

Portfolio Simulation is not defined anywhere in this repository, and this
specification does not define it — it is named here only so its absence is
disclosed rather than silently assumed, and so Execution Guidance is not
mistaken for it. The distinguishing test, to the extent it can be stated
without specifying Portfolio Simulation itself: Execution Guidance is
**scoped to one already-stated direction** and produces **qualitative
ranges and assumptions** about carrying that direction out. A hypothetical
future Portfolio Simulation would instead be a **computational, "what if"
projection tool**, potentially usable against any hypothetical action
regardless of whether Atlas has recommended it (an Investor exploring "what
would happen if I sold my LVMH position," entirely unprompted by any
Recommendation), and would produce a **projected portfolio state**
(resulting weight, concentration, cash position) as its output. Execution
Guidance never computes or states a resulting portfolio state — the moment
"how might I carry this out" content starts projecting "and here is what
your portfolio would then look like," it has crossed into Portfolio
Simulation's territory, which remains fully unscoped and unspecified by
this document.

## 9. Domain Model (Fields Only — No Implementation)

**Corrective pass note.** Split into two shapes below, matching §6's
two-stage lifecycle exactly — the same split `DE-007` §8 applies to
Recommendation itself, applied here for consistency. This is a
clarification of when each field is meaningful, not a redesign: every
field named in the prior single-shape version below still exists; none is
removed, renamed, or given new semantics.

**Amendment note (v0.2).** Both shapes below are restructured to hold
`approaches` (Amendment 1, §2) and `constraints` (Amendment 2, §2.1) in
place of the four scalar execution-content fields the v0.1 shapes carried.
No field is deleted: `targetAllocationRange`, `executionRange`,
`accumulationApproach`, and `urgency` all still exist, now as members of
each entry in `approaches` rather than as top-level scalars. `postActionImpact`
(Amendment 3, §2.2) is new, nested inside each approach entry. Every other
field — `recommendationInstanceId`/`recommendationId`, `valuationSensitivity`,
`assumptions`, `validityConditions`, `atlasConvictionLevel`,
`snapshottedAt`, `status`, `invalidatedReason`, `withdrawnReason` — is
unchanged in name, meaning, and level (still Guidance-level, not
per-approach, per §2's own reasoning for why they stay shared).

### A. `ComputedExecutionGuidance` — ephemeral, not persisted

```
ComputedExecutionGuidance
├── recommendationInstanceId      — correlates to the ComputedDirectionalRecommendation
│                                    instance it depends on (DE-007 §6) — a computed
│                                    correlation for the duration of one request, not
│                                    a persisted foreign key
├── approaches                    — ExecutionApproach[]   (§2 — one or more; order
│                                    carries no meaning, §2's own invariant; the same
│                                    one ComputedExecutionGuidance object continues to
│                                    exist per Recommendation, §7 — this is a list
│                                    inside it, never a set of sibling objects)
│   each ExecutionApproach:
│   ├── approachKey                 — string   (v0.2 correction — stable, non-localized,
│   │                                    scoped to this Guidance object only; the only
│   │                                    legitimate reference target for a future
│   │                                    Decision Capture integration, §2, §9B — never
│   │                                    `label`)
│   ├── label                       — string   (presentation only, translatable, may be
│   │                                    reworded; naming only, never a ranking signal
│   │                                    and never a stable reference, §2)
│   ├── rationale                   — string
│   ├── targetAllocationRange       — { minPercent, maxPercent } | null   (v0.2
│   │                                    correction, §2 — no implemented or doctrinal
│   │                                    source exists today for a normative target
│   │                                    allocation; same status as "recommended
│   │                                    quantity," which the prior investigation
│   │                                    already found requires a missing sizing model
│   │                                    — always null today)
│   ├── executionRange              — { basis: "price" | "valuation_relative",
│   │                                    min, max } | null   (never single-point, §2/§5;
│   │                                    "valuation_relative" currently has no
│   │                                    implemented data source, §2 — always null today)
│   ├── accumulationApproach        — { kind: "staged" | "lump_sum",
│   │                                    rationale: string } | null
│   ├── urgency                     — { kind: "time_sensitive" |
│   │                                    "no_particular_urgency",
│   │                                    reason: string } | null
│   └── postActionImpact            — { resultingWeightRange: { minPercent, maxPercent },
│                                        resultingCashRange: { min, max } | null,
│                                        resultingConcentrationRange: { min, max } | null,
│                                        resultingExposureRange: { min, max } | null
│                                      } | null   (§2.2 — bracketed only by this
│                                        approach's own targetAllocationRange endpoints;
│                                        null wherever the underlying DE-003 current-state
│                                        fact is unavailable, never fabricated; currently
│                                        always null, v0.2 correction, since its own
│                                        bracket (targetAllocationRange, above) is
│                                        currently always null)
├── constraints                   — { source: "investor_stated" | "system_stated",
│                                      description: string }[]   (§2.1 — explicit only,
│                                      never inferred; already applied as an exclusion
│                                      filter to `approaches` above by the time this
│                                      object exists — this list discloses what was
│                                      applied, it does not itself filter anything;
│                                      v0.2 correction, §2.1 — no canonical source for
│                                      an explicit constraint exists anywhere in this
│                                      repository today, so this list is always empty
│                                      until one is separately adopted)
├── valuationSensitivity          — string[]   (named Valuation assumptions this
│                                    guidance depends on)
├── assumptions                   — string[]   ("this guidance assumes…")
├── validityConditions            — { condition: string }[]   ("valid while…",
│                                    DE-002 §2.7-style, scoped to execution)
└── atlasConvictionLevel          — "high" | "medium" | "low"   (DE-004; stated
                                     independently of the Recommendation's own
                                     Conviction Level, §5)
```

**No `status`, `id`, `createdAt`, `updatedAt`, `invalidatedReason`, or
`withdrawnReason` field** — none of these are meaningful before a
persisted historical record exists (§6). **No per-approach `id` either** —
an `ExecutionApproach` has no identity or lifecycle of its own at the
computed stage; it is a value nested inside the one Guidance object's own
identity (see (B) below, whose `label` field is what a future Decision
Capture integration would reference for "which approach was chosen," never
a minted per-approach identifier).

### B. `HistoricalExecutionGuidanceSnapshot` — persisted, created only alongside a Historical Recommendation Snapshot

```
HistoricalExecutionGuidanceSnapshot
├── recommendationId              — references the paired HistoricalRecommendationSnapshot
│                                    (DE-007 §8B); both are created in the same event (§6)
├── snapshottedAt                 — when this record was written (== the paired
│                                    HistoricalRecommendationSnapshot's own snapshot time)
├── approaches / constraints / valuationSensitivity / assumptions /
│   validityConditions / atlasConvictionLevel
│                                  — frozen copy of the ComputedExecutionGuidance
│                                    content at the moment of capture (§6), identical
│                                    shape to (A) above, including each approach's own
│                                    `approachKey` (v0.2 correction, §2) — the stable,
│                                    non-localized reference a future Decision Capture
│                                    integration (not designed by this document) would
│                                    need to record which approach, if any, the
│                                    Investor selected. `label` is also frozen here,
│                                    for display, but is never the reference used for
│                                    that purpose — presentation text is not stable
│                                    identity (§2)
├── status                        — "active" | "invalidated" | "withdrawn"   (§6 —
│                                    the same three values this document has always
│                                    named; only reachable here, on this type; unchanged
│                                    granularity — status applies to the Guidance object
│                                    as a whole, not per approach, since all approaches
│                                    share one lifecycle, §2)
├── invalidatedReason             — string | null
└── withdrawnReason               — string | null
```

Every field above, on both shapes, is advisory content only. Neither is a
persistence schema, an API contract, or an implementation commitment — per
the same restraint `ADR-003` R-07 and `DE-001` §1 already apply to
Recommendation itself, this specification defines Execution Guidance's
content and reasoning, not its adoption as a Domain Object with an
identifier or persistence guarantee. That is implementation work,
explicitly out of scope here, exactly as before this revision.

## 10. Future Frontend Architecture (No React Code — Architecture Only)

The Investment Case Recommendation Workspace design (frontend design,
already produced, not yet implemented) specified a "Suggested Execution"
block with no domain concept behind it, and flagged that gap explicitly.
This specification closes that gap for that design without requiring any
change to it. **Corrective pass note**: §9's two-stage split does not
change any rendering rule below — the block's actual behavior is
unaffected. The reconciliation is this: while a Recommendation is only
computed (§6, pre-response), a present `ComputedExecutionGuidance` is
rendered exactly as an "active" `HistoricalExecutionGuidanceSnapshot`
would be — same content, same treatment — because `invalidated` and
`withdrawn` are, by definition, unreachable before a persisted snapshot
exists to be invalidated or withdrawn (§6). The frontend does not need a
separate branch for "computed" versus "active": the only real branches are
present/absent (unchanged, last bullet below) and, once a historical
snapshot exists, the two additional post-response states:

- The **Suggested Execution** block renders only when its Recommendation is
  directional, the direction is one of Buy/Add/Trim/Exit (§7 — never
  Hold/No Action, which never have Execution Guidance), and Execution
  Guidance is present — either a `ComputedExecutionGuidance` (pre-response)
  or a `HistoricalExecutionGuidanceSnapshot` with `status: "active"`
  (post-response, §9).
- If a `HistoricalExecutionGuidanceSnapshot` exists with `status:
  "invalidated"`, the block SHALL still render, with a visible "this
  guidance may be stale" treatment — reusing `UX-012B`'s existing
  Monitoring Condition "triggered" visual pattern rather than inventing a
  new one — never disappearing silently, per §6's own disclosure
  requirement. **Unreachable pre-response** (§6, §9A) — a merely computed
  Execution Guidance has no `status` to be `invalidated`.
- If a `HistoricalExecutionGuidanceSnapshot` exists with `status:
  "withdrawn"`, the block does not render — its parent Recommendation
  snapshot no longer stands either, per §7. **Equally unreachable
  pre-response** — for the same reason as above.
- If no Execution Guidance exists at all for a directional, actionable
  Recommendation (the Direction is stated but execution content could not
  be supported even at Low conviction, per §5), the block SHALL NOT be
  silently omitted without explanation — it renders a short, explicit
  statement that execution guidance is not currently available, mirroring
  the same "state the gap, don't hide it" discipline Recommendation
  Withheld itself already follows (`DE-002` §4).
- No new data fetch beyond the Investment Case's existing per-case analysis
  endpoint is assumed necessary at this design stage; whether Execution
  Guidance is embedded in that same payload or fetched separately is an
  implementation-phase decision, not resolved here.
- This gating depends only on whether Execution Guidance is present (and,
  once a historical snapshot exists, its `status`, §6/§9) and the
  Recommendation's own Direction — never on whether the Investor has
  accepted, dismissed, or acted on the Recommendation (§7). The block is
  expected to be visible while the Recommendation is still `pending`
  (`UX-012` §28) — showing a `ComputedExecutionGuidance` — since it exists
  partly to help the Investor decide.
- **(New, v0.2.)** Where `approaches` (§9) contains more than one entry,
  the block renders all of them, in a neutral, non-ranked presentation
  (§2's own invariant) — never a single featured approach with the rest
  demoted or hidden, and never a default selection pre-chosen on the
  Investor's behalf. This specification does not design that layout; it
  states only the one constraint that layout SHALL respect.

## 11. Rationale

This concept earns a specification of its own, rather than folding into
`DE-001`, for one reason: without it, "how should I carry this out" had no
honest home. Folding it into Recommendation itself would force Hold, No
Action, and Recommendation Withheld — the majority of real outcomes this
system will ever produce — to carry meaningless empty execution fields, or
force implementation-time special-casing around a field that structurally
shouldn't exist for them (§7). Leaving it unspecified and inventing it
ad hoc at implementation time was the other real alternative, and the more
dangerous one: exactly the point in the whole Recommendation Workspace
where content gets closest to naming prices and quantities is exactly the
point where an unreviewed, undisciplined design would most easily drift
into looking like a brokerage order ticket — the one outcome the
Recommendation Workspace's own design principles explicitly forbid.
Naming Execution Guidance as its own bounded concept, with its own
independently-stated (and typically lower) Conviction Level, its own
lifecycle distinct from its Recommendation's, and an explicit, named
boundary against Portfolio Simulation, Decision/Implementation Intent, and
Actual Execution, keeps the
"explain itself, expose its assumptions, expose its uncertainty" discipline
intact all the way down to the most execution-adjacent content this product
will ever show the Investor — which is exactly where that discipline is
hardest to hold onto, and therefore where it matters most.

---

## 12. Amendment Log (v0.2, "DE-006 Amendment Draft" Sprint)

Performed against the sprint's own explicit requirement lists for
Amendments 1–3, in the same self-review form `DE-007` §14 established.

**Amendment 1 — multiple Execution Approaches.**
- Exactly one Execution Guidance object per Recommendation: **preserved** —
  §7 restates this unchanged; `approaches` is a list inside the one object,
  confirmed by §9A's own note that an `ExecutionApproach` has no identity
  of its own.
- No sibling Guidance objects: **preserved** — no second identified type
  was introduced; §9A/§9B remain exactly two shapes, matching §6's
  pre-existing two-stage split.
- No ranking: **preserved** — stated as an invariant in §2, restated as a
  Non-Responsibility in §3, and applied to frontend rendering in §10.
- No optimization: **preserved** — no scoring, weighting, or selection
  algorithm was introduced anywhere in §2 or §9.
- No recommendation of one approach over another: **preserved** — same
  evidence as above; `label` is explicitly scoped to naming only.
- Same lifecycle for all approaches: **preserved** — `status`,
  `invalidatedReason`, `withdrawnReason` remain single fields on
  `HistoricalExecutionGuidanceSnapshot`, applying to the object as a whole.
- Same Recommendation for all approaches: **preserved** — `recommendationInstanceId`/
  `recommendationId` remain single fields at the Guidance level; no
  per-approach Recommendation reference exists.
- Dependency direction preserved: **confirmed** — §4's five-concept table
  and §7's unidirectional-reference rule are untouched by this amendment.

**Amendment 2 — explicit constraint filtering.**
- Constraints only remove infeasible approaches: **confirmed** — §2.1
  states exclusion as the sole effect.
- Constraints never rank: **confirmed** — §2.1 and §3 both state this
  explicitly.
- Constraints never optimize: **confirmed** — same.
- Constraints never introduce hidden decision logic: **confirmed** — §2.1
  restricts constraints to explicitly-stated ones only, never inferred or
  derived, and §3 adds the matching Non-Responsibility.

**Amendment 3 — mechanical post-action portfolio arithmetic.**
- No optimization: **confirmed** — §2.2/§3 state Post-Action Impact is
  arithmetic only.
- No expected return: **confirmed** — explicitly excluded in §3.
- No portfolio quality judgment: **confirmed** — §3's "SHALL NOT state or
  imply whether a resulting state is more or less desirable."
- No portfolio simulation: **confirmed** — §2.2/§3 scope this as a narrow,
  named exception to the existing Portfolio Simulation boundary (§8,
  unchanged), not an expansion of it.
- No recommendation: **confirmed** — §3's explicit prohibition against
  presenting it as a recommendation of the approach it accompanies.
- Arithmetic only: **confirmed** — every figure is bracketed by the
  accompanying approach's own already-disclosed `targetAllocationRange`
  endpoints, sourced only from `DE-003`'s existing current-state facts;
  never a new exact quantity (§3's existing prohibition, reconfirmed as
  unrelaxed).

**Editorial clarifications 1–2.** §5.1 (new) names the generation-legitimacy/
historical-validity distinction directly; §2's `executionRange` discussion
and §9A's field comment both now state plainly that the `valuation_relative`
basis has no implemented data source today. Neither changes any prior
behavior — both restate, in direct language, distinctions and gaps the
v0.1 text already implied or left silent.

**What this amendment does not do, confirmed against the sprint's own
scope boundary:** no new bounded context was created; no sibling
terminology for anything DE-006 already owns was introduced (§11's
Terminology resolution, carried in from the prior investigation, is
reflected throughout — "Execution Approach," never "Execution
Alternative"); §4's five-concept non-merger rule, §7's Recommendation
relationship, §8's Portfolio Simulation boundary, and DE-007's own domain
model are all untouched by this revision.

### 12.1 Consistency-Review Correction Pass (Same v0.2, Pre-Merge)

Four checks, run against this draft before its own "ready to merge" status
could stand — testing the amendment against itself, not reopening the
accepted three-amendment structure.

**Check 1 — `targetAllocationRange` audit.** Tested from first principles
against the real repository, exactly as Amendment 3's own investigation
already tested "recommended"/"optimal" quantity: does any existing
doctrine or implemented Core capability produce a normative *target*
allocation, as distinct from a *descriptive* current allocation? `DE-003`
§3's Allocation and Concentration factors are real and computed
(`atlas/domains/portfolio/models.py`), but both describe what a position
*is*, never what it *should become* — no field, factor, or rule anywhere
in `DE-003`, `DE-001`, or `DE-008` states a target range. **Classification:
REQUIRES A NEW NORMATIVE SIZING MODEL** — the identical classification the
prior investigation already gave "recommended quantity," since a target
allocation *range* is the same claim expressed in percentage terms rather
than share terms. **Correction applied:** §2 and §9A now mark
`targetAllocationRange` unavailable today, with the same honest-absence
treatment already used for `executionRange`'s `valuation_relative` basis;
§2.2/§9A/§3 now state the cascading consequence for Post-Action Impact,
which brackets its own arithmetic by this field's endpoints and is
therefore likewise currently unavailable. This is a genuine, necessary
correction, not a redesign: the field, and Post-Action Impact's dependency
on it, remain exactly as specified — only their current computability
changes, from assumed to explicitly absent.

**Check 2 — approach identity for historical traceability.** Tested
`label` against localization (translated per `UX-012`'s existing i18n
system — the same approach reads differently per language), copy changes
(future rewording would silently break any reference), duplicate labels
(nothing prevents two approaches sharing a label), and the needs of
historical replay and guidance-versus-execution comparison (§9B). **Finding:
presentation text cannot legitimately serve as historical identity.**
**Correction applied:** a new `approachKey` field — stable, non-localized,
scoped only within its own Guidance object (no global uniqueness, no
independent repository) — added to `ExecutionApproach` in both §9A and
§9B, explicitly **not** a new Aggregate or Entity, matching the same
lightweight scoped-identity pattern `DE-007` §6 already establishes for
`recommendationInstanceId`. `label` remains presentation-only and is now
explicitly marked as never a stable reference.

**Check 3 — explicit-constraint ownership audit.** Checked directly
against the repository (no `Constraint`/`InvestorPreference`/limit domain
object anywhere in `atlas/` or `frontend/src/`; no doctrine text naming an
investor-settable rule outside `DE-006` itself). Separated hard
user-stated constraints (no source), portfolio facts (real, but
descriptive, not exclusionary — `DE-003`), portfolio doctrine factors
(evaluative inputs, not hard gates), regulatory constraints (unaddressed
anywhere), inferred preferences (already correctly excluded by §2.1's own
"never inferred" rule), and optimization targets (already correctly
excluded). **Finding: no canonical source exists today.** **Correction
applied:** §2.1 now states this directly as an external dependency this
specification does not itself satisfy — `constraints` is always empty
until a source is separately adopted; no constraint-capture mechanism was
invented, per the review's own explicit instruction not to.

**Check 4 — fabricated realism in examples.** The `DE-006.md` file itself
contains, and has always contained, no worked company example — confirmed
by direct inspection; this is consistent with the document's own
established "Fields Only — No Implementation" convention (§9's own
heading). The MSFT example given in the prior turn's chat deliverable
(specific share counts, cash figures, and business-assumption sentences,
none backed by a real cited Core field or fixture) was a violation of this
document's own no-fabricated-precision discipline, committed in
illustrative chat text, not in this document. **No correction to this file
was required or made**, since the file was never the source of the
violation; the corrected, symbolic-values-only example is provided
separately, in the response accompanying this pass, not written into
`DE-006.md` itself, consistent with the document's own convention.

**Outcome:** three corrections applied (Checks 1–3), one confirmed clean
with no file change needed (Check 4). None reopens the accepted
three-amendment structure — each correction narrows an existing field's
stated availability or adds a single scoped identifier; none removes,
redesigns, or contradicts Amendments 1–3 as accepted.
