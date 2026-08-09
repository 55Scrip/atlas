# DE-006 — Atlas Execution Guidance

**Status:** Draft v0.1. Companion specification to
`docs/ATLAS_DECISION_ENGINE_DOCTRINE.md` §8 (Recommendation Framework), by
extension. Governed by, and subordinate to, that Doctrine and to `APP-000`.
Documentation only — no code, no frontend, no backend accompanies this
specification. Discovered as a gap during the design of the Investment Case
Recommendation Workspace (frontend design, not yet implemented): that design
needed a "Suggested Execution" block with no domain concept behind it. This
specification exists to name that concept, precisely, before anything is
built against it.

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
to Execution Guidance's own definition — see §7 for the full relationship.

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

Where a Recommendation's direction is Buy, Add, Trim, or Exit (§7 states why
Hold and No Action are excluded), Execution Guidance SHALL, when present:

- State a **target allocation range** — a minimum and maximum share of the
  portfolio the position might reasonably move toward or away from — never a
  single target weight.
- State an **execution range** — a price range or a range relative to the
  Valuation section's own stated fair-value range (`Doctrine` §5) — never a
  single-point price, carrying forward `docs/ValueScenarioReview.md`'s
  already-absorbed principle (`Doctrine` §12) that Atlas does not issue
  single-point price targets, applied here to execution content
  specifically, not only to valuation content.
- State an **accumulation approach** as a qualitative category (staged
  versus lump-sum) with its rationale — never a schedule, never specific
  dates.
- State an **urgency** framing as a qualitative category (time-sensitive
  versus no particular urgency) with its reason — never a deadline.
- State the **valuation sensitivity** of the guidance: which specific
  Valuation assumptions (`Doctrine` §5, `DE-002` §2.2) it depends on, so the
  Investor can see exactly what would make the range stale.
- State its **assumptions** explicitly ("this guidance assumes…") and its
  **validity conditions** explicitly ("valid while…"), per §5 below.
- Carry its own **Atlas Conviction Level** (`DE-004`), stated independently
  of the Recommendation's own Conviction Level — see §5.

## 3. Explicit Non-Responsibilities

Execution Guidance SHALL NOT, under any circumstance:

- Compute, promise, or imply a guaranteed price, outcome, or result.
- Prepare, place, route, or transmit a broker order, or reference order
  mechanics (order type, limit/market, time-in-force).
- State an exact price target, an exact share or dollar quantity, or an
  exact execution date or time.
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
  followed. That is Portfolio Simulation's domain, not this one — see §8.
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

## 6. Lifecycle

Execution Guidance's lifecycle reuses the state vocabulary `UX-012B`'s
existing Monitoring Condition and Review Condition components already
establish (Active/Triggered/Resolved/Expired; Pending/Triggered/Completed),
rather than inventing new terms for a structurally similar situation:

- **Created** — only when a Recommendation's Direction is stated as Buy,
  Add, Trim, or Exit (§7). Hold, No Action, and Recommendation Withheld
  never produce Execution Guidance, because there is nothing for it to
  guide.
- **Updated** — when the Recommendation it depends on is re-evaluated and
  its Direction or Conviction changes materially, or when new Valuation
  evidence shifts the range this guidance's own valuation-sensitivity
  statement (§2) names. Execution Guidance is re-derived, not left silently
  stale beside an updated Recommendation.
- **Invalidated** — when a stated validity condition (§2) is actually met —
  for example, the current price or valuation moves outside the range the
  guidance assumed. Invalidated guidance is retained and visibly marked,
  not deleted, per the same immutability discipline `UX-012B`'s Historical
  Section already establishes for locked content: an invalidated Execution
  Guidance is itself information (it tells the Investor exactly what
  changed), not nothing.
- **Withdrawn** — when the Recommendation it depends on is itself withdrawn
  or superseded (moves to Recommendation Withheld, or is superseded by a
  later analysis run). Execution Guidance cannot outlive its Recommendation
  (§7) — Recommendation withdrawal always withdraws its linked Execution
  Guidance.

Invalidated and Withdrawn are kept as two distinct states, not one, because
they are triggered differently and mean different things: a validity
condition can be breached (Invalidated) while the underlying Direction is
still fully intact (a Buy recommendation whose specific execution range
needs refreshing is not a Buy recommendation that has stopped being true).

## 7. Relationship to Recommendation

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

```
ExecutionGuidance
├── id
├── recommendationId              — required; 1:1-or-nothing with a
│                                    directional, actionable Recommendation (§7)
├── status                        — "active" | "invalidated" | "withdrawn"  (§6)
├── createdAt
├── updatedAt
├── targetAllocationRange         — { minPercent, maxPercent } | null
├── executionRange                — { basis: "price" | "valuation_relative",
│                                      min, max } | null   (never single-point, §2/§5)
├── accumulationApproach          — { kind: "staged" | "lump_sum",
│                                      rationale: string } | null
├── urgency                       — { kind: "time_sensitive" |
│                                      "no_particular_urgency",
│                                      reason: string } | null
├── valuationSensitivity          — string[]   (named Valuation assumptions this
│                                    guidance depends on)
├── assumptions                   — string[]   ("this guidance assumes…")
├── validityConditions            — { condition: string }[]   ("valid while…",
│                                    DE-002 §2.7-style, scoped to execution)
├── atlasConvictionLevel          — "high" | "medium" | "low"   (DE-004; stated
│                                    independently of the Recommendation's own
│                                    Conviction Level, §5)
├── invalidatedReason             — string | null
└── withdrawnReason               — string | null
```

Every field above is advisory content only. None is a persistence schema,
an API contract, or an implementation commitment — per the same restraint
`ADR-003` R-07 and `DE-001` §1 already apply to Recommendation itself, this
specification defines Execution Guidance's content and reasoning, not its
adoption as a Domain Object with an identifier or persistence guarantee.
That is implementation work, explicitly out of scope here.

## 10. Future Frontend Architecture (No React Code — Architecture Only)

The Investment Case Recommendation Workspace design (frontend design,
already produced, not yet implemented) specified a "Suggested Execution"
block with no domain concept behind it, and flagged that gap explicitly.
This specification closes that gap for that design without requiring any
change to it:

- The **Suggested Execution** block renders only when its Recommendation is
  directional, the direction is one of Buy/Add/Trim/Exit (§7 — never
  Hold/No Action, which never have Execution Guidance), and a linked
  `ExecutionGuidance` with `status: "active"` exists.
- If `status: "invalidated"`, the block SHALL still render, with a visible
  "this guidance may be stale" treatment — reusing `UX-012B`'s existing
  Monitoring Condition "triggered" visual pattern rather than inventing a
  new one — never disappearing silently, per §6's own disclosure
  requirement.
- If `status: "withdrawn"`, the block does not render — its parent
  Recommendation no longer stands either, per §7.
- If no `ExecutionGuidance` exists for a directional, actionable
  Recommendation at all (the Direction is stated but execution content
  could not be supported even at Low conviction, per §5), the block SHALL
  NOT be silently omitted without explanation — it renders a short,
  explicit statement that execution guidance is not currently available,
  mirroring the same "state the gap, don't hide it" discipline
  Recommendation Withheld itself already follows (`DE-002` §4).
- No new data fetch beyond the Investment Case's existing per-case analysis
  endpoint is assumed necessary at this design stage; whether
  `ExecutionGuidance` is embedded in that same payload or fetched
  separately is an implementation-phase decision, not resolved here.
- This gating depends only on `ExecutionGuidance.status` (§6) and the
  Recommendation's own Direction — never on whether the Investor has
  accepted, dismissed, or acted on the Recommendation (§7). The block is
  expected to be visible while the Recommendation is still `pending`
  (`UX-012` §28), since it exists partly to help the Investor decide.

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
