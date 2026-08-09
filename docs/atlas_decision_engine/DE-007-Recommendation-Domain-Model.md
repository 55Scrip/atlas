# DE-007 — Atlas Recommendation Domain Model

**Status:** Draft v0.1. Companion specification to
`docs/ATLAS_DECISION_ENGINE_DOCTRINE.md` §8 (Recommendation Framework).
Governed by, and subordinate to, that Doctrine, to `DE-001` and `DE-002`
(which it implements the shape of, never redefines), and to `APP-000`.
Documentation only — no code, no frontend, no backend accompanies this
specification. This is the "separate architectural decision, with its own
explicit justification" `docs/atlas_ux/governance/ADR-003-Recommendation-Identity-and-Terminology-Resolution.md`
R-07 explicitly deferred when it declined to adopt Atlas Recommendation as a
Domain Object. It is also the gap the Recommendation Workspace
implementation design surfaced as blocking: DE-001/DE-002 specify
Recommendation's *structure and behavior* in full; neither specifies its
*field-level shape*. This document closes that gap, and only that gap.

**This document does not redesign `DE-001` through `DE-006`.** Every
direction, every reasoning-section requirement, every Portfolio
Intelligence factor, every Conviction level, every Decision Memory rule,
and every Execution Guidance field defined in those six documents is
treated as fixed. Where their combination exposes a genuine ambiguity, this
document identifies it, explains it, and resolves it — without changing
what any of them already states.

## 1. Definition

**Ontology corrective pass note.** This document has been revised to
reflect the approved Recommendation Ontology Decision: Recommendation is
derived analysis by default; only an Investor's actual response to a
specific computed instance gives rise to a persisted historical record.
Every section below reflects that decision. The locked principle, restated
once, governs the whole document and is not re-argued section by section:
**Recommendation is NEVER persisted merely because Atlas computed it.**

**A Recommendation is Atlas's own conclusion about a single decision point
for a single position, at a single moment in time — the completed output
of the seven-part reasoning structure `DE-002` requires, stating one of the
six directions `DE-001` §2 defines, or, where the evidence does not support
any of them, Recommendation Withheld (`DE-002` §4, `DE-004` §4).** That
single definition now names three distinct things, precisely, per the
approved ontology:

- **Computed Directional Recommendation.** Derived, current-state analysis
  — the live output of one analysis run, exactly like Business Evaluation,
  Valuation, Risk, Portfolio Intelligence, and Reasoning already are. It
  exists for the duration of the request that produced it. It is **not
  persisted merely because it exists** — computing it, and even displaying
  it to the Investor, creates no database row.
- **Historical Recommendation Snapshot.** Created **only** when the
  Investor responds to a specific Computed Directional Recommendation
  instance (§5). Immutable once created. Preserves exactly what Atlas
  recommended, and why, at that moment — the one and only place this
  document departs from "everything here is recomputed fresh," and it
  departs only because an Investor action, not a machine computation,
  triggered it.
- **Recommendation Withheld.** Remains purely derived — no persistence, no
  historical identity requirement, unaffected by any of the above. See §4
  and §9 for why it stays entirely outside this document's one
  persistence exception.

It is not the reasoning *process* (that is `atlas.decision_engine`'s
pipeline, and `atlas.analysis_engine`'s composition of it — code, not this
document's concern) and it is not the evidence *inputs* to that process
(Business Evaluation, Valuation, Portfolio Intelligence, Reasoning — each
already has its own contract). A Recommendation is the **conclusion**:
the one thing those inputs were assembled to produce, held to `DE-001` §3's
four required explainability elements and `DE-002`'s seven-section
structure, together.

This repository's own code has been anticipating this exact type by name
for several sprints without ever defining it: `atlas.decision_engine.contracts.RecommendationOutcomeKind.DIRECTIONAL`
is a reserved enum member with no corresponding type
(`atlas/analysis_engine/recommendation.py:7-9`, `atlas/analysis_engine/__init__.py:37`,
`atlas/analysis_engine/provenance.py:30`, each independently noting "no
`DirectionalRecommendation` type is defined... anywhere in this codebase").
**This specification names and defines that type: `ComputedDirectionalRecommendation`,**
and its historical counterpart, `HistoricalRecommendationSnapshot` (§8).
`RecommendationWithheld` (`atlas/decision_engine/contracts.py:877-914`),
which already exists, already implemented, and already correct per `DE-002`
§4 and `DE-004` §4, is untouched by this document — it is the other member
of the same `RecommendationOutcomeKind` union, and this document does not
redesign it.

## 2. Responsibilities

A Recommendation's directional content — whether currently a
`ComputedDirectionalRecommendation` or, once responded to, a
`HistoricalRecommendationSnapshot` (§8) — SHALL:

- State exactly one Direction (`DE-001` §2), in `APP-002` §6's
  evidence-attributed register.
- Carry the Why (`DE-001` §3.1–3.2): Evidence and Counter-Evidence, each
  attributed and epistemic-status-tagged (`APP-002` §7), traceable to
  Business Evaluation, Valuation, and Reasoning's own already-produced
  findings — never restated from scratch.
- Carry an Atlas Conviction Level (`DE-004` §3: High, Medium, or Low) and
  the specific evidentiary basis for it.
- Carry Portfolio Context (`DE-002` §2.4): whichever of `DE-003` §3's seven
  factors actually bear on this Direction — never all seven restated by
  rote (`DE-003` §4).
- Carry Alternatives content, grounded specifically in `DE-003`'s
  Opportunity Cost factor (qualitative, no scores or rankings — `UX-012B`
  Comparison precedent, already cited by `DE-003`).
- Carry What Could Change This View (`DE-002` §2.7): specific, named,
  checkable conditions for the *Direction* — distinct from any conditions
  Execution Guidance separately states about *how* the Direction is
  carried out (`DE-006` §2, §7 — see §4 below).
- Where the position has prior history, reference Decision Memory
  (`DE-005` §4: why initiated, why since added to or reduced, reported
  Outcomes, thesis synthesis) — per `DE-005` §6, a recommendation for a
  position with history SHALL draw on it when relevant.
- Carry a stable identity for the lifetime of one computed instance (§6) —
  the one genuinely new responsibility this document adds, because `DE-006`
  §9 already requires `ExecutionGuidance.recommendationId` to reference
  something. This identity is **not** a lifecycle state: `UX-012` §28's
  pending/accepted/dismissed/acted-upon states belong to the Investor's
  response to a Recommendation, never to the Recommendation itself (§5,
  §9) — a Computed Directional Recommendation carries no state field of
  its own.

## 3. Non-Responsibilities

A Recommendation's directional content, in either form (§2), SHALL NOT,
under any circumstance:

- State a target allocation, an execution price range, an accumulation
  approach, or an urgency — that is Execution Guidance's exclusive content
  (`DE-006` §2). **This document does not absorb `DE-006`.** Not one
  execution-shaped field appears anywhere in §8's domain model.
- State or imply a projected resulting portfolio state (weight,
  concentration, cash position, after acting) — that is Portfolio
  Simulation's undefined, out-of-scope territory (`DE-006` §8, unchanged
  here).
- Record what the Investor actually intends or decided to do — that is
  Investor Decision/Implementation Intent (the existing
  `BUY/SELL/HOLD/WATCH/PASS` field and Implementation Summary, `DE-006`
  §4), authored by the Investor, never by Atlas.
- Record what actually happened in the market — Actual Execution, `DE-006`
  §4, undefined and out of scope here exactly as it is there.
- Be presented, recorded, or treated as a Decision (`APP-000` §5, `DE-001`
  §1) — only the Investor decides.
- Carry a numeric confidence score of any kind — `DE-004` §5's
  categorical-not-numeric reasoning applies identically here.
- Duplicate content that already has a canonical home elsewhere on the
  page: Current Situation (`DE-002` §2.1) is satisfied by the Investment
  Case's existing Executive Summary and is not restated as its own field
  here (this is a presentation decision, made at the Recommendation
  Workspace design layer, not a domain-model field — the underlying
  `ReasoningSummary` content, §8, still exists and is available; it is
  simply not duplicated into a second top-level field).

## 4. Relationships

Per your explicit instruction, `DE-001` through `DE-006` are not
redesigned here — only related to, precisely:

**Execution Guidance (`DE-006`).** A Computed Directional Recommendation
**does not contain, own, or reference Execution Guidance.** The dependency
is unidirectional and already fully owned by `DE-006` §7/§9:
`ExecutionGuidance.recommendationId` points at a Recommendation instance;
no field on either `ComputedDirectionalRecommendation` or
`HistoricalRecommendationSnapshot` (§8) points back. This is a deliberate
choice, not an oversight — see §11 for the reasoning, and the self-review
at the end for the specific coupling risk it forecloses. Consuming code
determines whether an active `ExecutionGuidance` exists for a given
`recommendationId` by query, not by traversing a field on the
Recommendation itself.

**Remaining `DE-006` ambiguity — noted, not resolved here.** `DE-006` §6
describes an Execution Guidance's Invalidated state as content that is
"retained and visibly marked, not deleted" — language that presumes a
persisted prior state to invalidate *against*. Under the approved
ontology, that presumption holds cleanly once an Investor has responded
(a `HistoricalRecommendationSnapshot` exists to compare fresh computation
against), but is genuinely undefined for a still-*pending* Execution
Guidance, since no Recommendation snapshot exists yet for anything to be
invalid relative to. This is a real gap in `DE-006`'s own wording,
surfaced here because `DE-007` depends on `DE-006`'s identity assumption
and this is the place that dependency shows a seam — but it is a **future
clarification, not a blocker**, and `DE-006` is not modified by this
document.

**Investor Decision / Implementation Intent.** No relationship at the
domain-model level. `DE-006` §4 already states that a future
implementation *may* choose to let Execution Guidance pre-populate the
Investor's own Implementation Summary — that deferral is unchanged. This
document adds nothing to it: neither `ComputedDirectionalRecommendation`
nor `HistoricalRecommendationSnapshot` carries a field referencing the
Investor's `BUY/SELL/HOLD/WATCH/PASS` record, in either direction.

**Actual Execution.** No relationship. Undefined, out of scope, exactly as
`DE-006` §4 already states.

**Portfolio Simulation.** No relationship. Undefined, out of scope,
exactly as `DE-006` §8 already states.

**Recommendation Withheld.** The other member of the same
`RecommendationOutcomeKind` union (`atlas/decision_engine/contracts.py:827-840`),
not a state a Computed Directional Recommendation can be in and not a
state it transitions to or from. A case whose current computation was
directional and is later re-evaluated into insufficiency does not "become"
a `RecommendationWithheld` — the current Computed Directional
Recommendation is simply replaced, on the next request, by a fresh
`RecommendationWithheld` computation, the same discriminated-union shape
`RecommendationOutcomeKind` already enforces at the type level. **No
supersession event occurs** unless a `HistoricalRecommendationSnapshot`
already existed for the prior directional content (§6, §9) — an Investor
who never responded to the earlier directional computation leaves nothing
behind for the new `RecommendationWithheld` to supersede.

**Decision Memory (`DE-005`).** Read-only input, not owned. A
Recommendation's Portfolio Context and Alternatives content may draw on
`DE-005`'s Existing Thesis and Previous Decisions factors, but neither
`ComputedDirectionalRecommendation` nor `HistoricalRecommendationSnapshot`
stores or duplicates Decision history — both reference the same
`DecisionRecord`/`OutcomeRecord` data `DE-005` §3 already grounds itself
in.

**Portfolio Intelligence (`DE-003`).** Mandatory input, reused not
duplicated — see §8: the Portfolio Context field, on both the computed and
persisted forms, is typed as the existing
`PortfolioContextSummary`/`PortfolioFinding` shapes
(`atlas/decision_engine/contracts.py:553-587, 709-717`), not a new,
parallel structure.

## 5. Lifecycle

Three things happen in sequence, and only one of the transitions among
them creates anything persisted:

```
Compute Recommendation                       (ComputedDirectionalRecommendation,
        │                                      §8 — ephemeral, per request)
        ▼
Investor may view / evaluate it                (no state change from viewing alone)
        │
        ├── No response ──────────────► nothing persisted. The next
        │                                request simply recomputes fresh
        │                                (possibly different) content —
        │                                there is nothing to reconcile,
        │                                because nothing was ever recorded.
        │
        └── Investor responds
                │
                ▼
        Recommendation content is snapshotted   (HistoricalRecommendationSnapshot
                │                                 is created, §8 — the one and
                │                                 only persistence trigger this
                │                                 document defines)
                ▼
        Investor response is persisted          (RecommendationResponse, §8 —
                │                                 created in the same event as
                │                                 the snapshot above)
                ▼
        A later Decision / Implementation Intent  (open question — whether this
        record MAY reference this snapshot          reference exists structurally,
                                                       §12)
```

**Computing a Recommendation is not a lifecycle event with states of its
own.** A Computed Directional Recommendation is not "Created" in any sense
that implies persistence or an audit trail — it is simply what the current
analysis run's Reasoning output, combined with a Conviction Level of
Medium or High (`DE-004` §4: Low conviction alone does *not* block a
direction; only the absence of even Low conviction does), produces when it
clears the gate `atlas/analysis_engine/recommendation.py`'s own docstring
already states in full: *"Business Analysis EVALUATED AND Valuation
EVALUATED AND Portfolio Intelligence EVALUATED AND Reasoning EVALUATED AND
Conviction ≥ [threshold] → Directional Recommendation allowed."* No new
gate condition is introduced here — this document only names the type the
existing, already-documented gate has been waiting to produce, and
declines to attach any persistence to producing it.

**Pending is not necessarily a stored state — it is the default.** A
Recommendation is "pending" for exactly as long as no
`RecommendationResponse` exists referencing its instance identity (§6).
This requires no write, no row, and no explicit state transition into
"pending" — it is simply what "no response yet" means by absence.

**The Investor-response lifecycle** (`UX-012` §28's own
pending/accepted/dismissed/acted-upon) governs the *Investor's own
reaction*, and only the Investor's reaction:

- **Pending** — absence of a `RecommendationResponse` (above).
- **Accepted** / **Dismissed** — the `RecommendationResponse.state` value,
  written at the moment of response, together with the
  `HistoricalRecommendationSnapshot` it references (§8) — the single
  persistence-triggering event this whole document defines.
- **Acted upon** — not separately recorded. Derived by checking whether a
  subsequent Investor Decision/Implementation Intent record exists that is
  traceable to this Recommendation's identity (a future implementation-
  phase question, per `DE-006` §4's own deferral of exactly this
  pre-population/traceability mechanism, and per §12's own open question
  on the same point).

**These states belong to the response, never to the Recommendation
content itself, and SHALL NOT be merged into one mutable record.** A
`HistoricalRecommendationSnapshot`, once created, is immutable; a
`RecommendationResponse` is a separate fact that references it, never a
field that gets written onto the snapshot. This single rule is this
document's primary defense against Recommendation becoming a mutable
dumping ground (§9, §14).

**Supersession**, precisely scoped: only a `HistoricalRecommendationSnapshot`
can be superseded, and only by a *later response* to a *differently
computed* Recommendation for the same Case — never by the mere passage of
time or a mere recomputation with no accompanying response. A Computed
Directional Recommendation that is never responded to leaves nothing
behind, and therefore has nothing that could ever need to be superseded
(§9's own falsification check against unnecessary supersession
mechanics).

## 6. Identity

Two distinct identities exist, deliberately kept separate, per the
approved ontology's own explicit clarification:

**Computed-instance identity.** A Computed Directional Recommendation
SHALL carry a stable identity **for the lifetime of that computed
instance** — sufficient for an Execution Guidance (`DE-006` §9) or an
Investor response (§8) to reference *exactly that instance*, and no other.
This is not optional: `DE-006` §9 already declared
`ExecutionGuidance.recommendationId` a *required* field, silently assuming
Recommendation has some identity to reference, without `DE-006` itself
ever defining what that identity is (reasonable at the time — `DE-007`
did not yet exist). This document closes that dangling reference at the
*requirement* level only. **The technical mechanism — a UUID minted at
computation time, a canonical hash of the instance's own content, a
compound key, or another approach entirely — is explicitly an
implementation decision and stays outside this document.** What the
domain requires is only that the identity be stable and reproducible for
the duration one computed instance is in use (one request, one page view,
one moment an Investor might respond to it) — not that it survive forever,
and not that it be assigned by any particular algorithm.

**Persisted historical identity.** When an Investor responds, the
computed instance's own identity is carried forward, unchanged, into the
`HistoricalRecommendationSnapshot` that gets created (§8) — no new
identity-minting step happens at persistence time. The identity that was
merely "stable for one computed instance" a moment earlier now becomes
"stable forever," simply because a real, persisted row now exists under
it. This is the only sense in which identity "upgrades" from ephemeral to
permanent, and it happens automatically, as a consequence of persistence,
not as a separate design decision.

**Versioning**: not required, and not added. Recency is the version for
the *computed* side (the most recent request always reflects current
evidence — there is nothing to version). For the *persisted* side, a Case
may eventually accumulate more than one `HistoricalRecommendationSnapshot`
over time (one per Investor response), ordered by `generatedAt` — an
explicit integer version field would imply a precision (`DE-004` §5) this
content does not need.

**Supersession**: applies only among `HistoricalRecommendationSnapshot`
records for the same Case (§5, §9) — never among merely-computed,
never-responded-to instances, which leave nothing to supersede. Where it
does apply, it is implicit: a later snapshot with a later `generatedAt`
supersedes an earlier one for the same Case; no `supersedes`/
`supersededBy` cross-reference field is required, and none is added.

**Replacement**: a superseded `HistoricalRecommendationSnapshot` is never
mutated in place — a wholly new snapshot is created by a wholly new
response event. This mirrors `DE-005` §1's own Decision-history precedent
exactly (a thesis is never rewritten; new Decisions are appended) and
`UX-012B`'s Historical Section immutability guarantee, already cited by
`DE-006` §6 for the identical reason.

**Historical permanence**: applies only to `HistoricalRecommendationSnapshot`
records — retained, not deleted, once created, the same "retained and
visibly marked, not deleted" principle `DE-006` §6 already states for
Invalidated Execution Guidance. A Computed Directional Recommendation that
was never responded to has no historical permanence to speak of, because
it was never historical in the first place. Whether or how a superseded
snapshot is *surfaced* in the UI (a history view, a diff against the
current one) is a Recommendation Workspace presentation question, not
decided here.

## 7. Aggregate Boundary

**Not every computed Recommendation is a persistent aggregate root.** The
prior draft's central error, corrected here: a `ComputedDirectionalRecommendation`
is a **value object**, exactly like `BusinessEvaluationResult`,
`ValuationResult`, `PortfolioIntelligenceResult`, `ReasoningResult`, and
`RecommendationWithheld` already are — recomputed fresh on every request,
never persisted, carrying only the computed-instance identity §6 requires,
never a database identity. It is not an aggregate root, and this document
no longer describes it as one.

**`HistoricalRecommendationSnapshot` is the aggregate root** — the one and
only persisted, independently-identified entity this document defines.
Its boundary is drawn narrowly, and drawn *because* an Investor action
created it, not because Atlas computed something:

- It reaches into, by **reference at the moment of capture, then by
  frozen copy thereafter**, the reasoning content already produced by the
  existing pipeline stages (§8) — `ReasoningFinding`'s `ReasoningSummary`,
  `SupportingEvidenceSummary`, `ContradictionSummary`, and
  `PortfolioContextSummary` are the exact same types already defined in
  `atlas/decision_engine/contracts.py:649-717`. At the instant of
  snapshotting, their *current* values are copied in; after that instant,
  the snapshot no longer tracks live changes to those types — it is
  frozen, by definition.
- It does **not** reach into Execution Guidance, Investor Decision, Actual
  Execution, or Portfolio Simulation (§4) — unchanged from the prior
  draft's conclusion, still correct here.
- It does **not** reach into or redesign the persistence model for
  Investor Decision / Implementation Intent — `RecommendationResponse`
  (§8) is a small, adjacent record that references a snapshot; it is not
  a restructuring of how Decisions are recorded today.

**`RecommendationResponse`** is a third, even smaller entity, created in
the same event as the snapshot it references (§5, §8) — its own boundary
is exactly the Investor's reaction (accepted/dismissed, and when), nothing
about the Recommendation's content, which lives entirely on the snapshot
it points to.

## 8. Complete Domain Model (Fields Only — No Implementation)

Three types, matching §1's three-way definition exactly. `RecommendationWithheld`
is not repeated here — it is unchanged from its existing implementation
(`atlas/decision_engine/contracts.py:877-914`) and out of this section's
scope entirely.

### A. `ComputedDirectionalRecommendation` — ephemeral, not persisted

```
ComputedDirectionalRecommendation
├── recommendationInstanceId      — stable for the lifetime of this
│                                    computed instance only (§6); the
│                                    generating mechanism is explicitly an
│                                    implementation decision, not specified
│                                    here
├── caseId                        — the Investment Case this instance is for
├── generatedAt                   — when this instance was computed
│
├── direction                     — one of DE-001 §2's six directions
│                                    (Buy / Add / Hold / Trim / Exit / No
│                                    Action) — RecommendationOutcomeKind
│                                    .DIRECTIONAL, finally given a shape
├── directionStatement            — pre-composed, APP-002 §6
│                                    evidence-attributed register
│
├── convictionLevel               — DE-004 §3's Atlas Conviction Level
│                                    (High / Medium / Low) — a field
│                                    distinct from the existing, already-
│                                    implemented AnalysisConvictionLevel
│                                    (analysis_engine/conviction.py; see §11)
├── convictionReason              — specific evidentiary basis (DE-004 §3)
│
├── reasoning                     — embeds, by reference, the EXISTING
│   │                                atlas.decision_engine.contracts types:
│   ├── currentSituation            ReasoningSummary          (DE-002 §2.1)
│   ├── supportingEvidence          SupportingEvidenceSummary (DE-002 §2.2)
│   ├── contradictingEvidence       ContradictionSummary      (DE-002 §2.3)
│   ├── portfolioContext            PortfolioContextSummary   (DE-002 §2.4)
│   └── whatWouldChange             tuple[OpenQuestion, ...]  (DE-002 §2.7 —
│                                    ReasoningFinding already reserves this
│                                    field; it is contractually forced empty
│                                    today "until a prior stage genuinely
│                                    provides one" — a Directional
│                                    Recommendation is that provider; the
│                                    existing __post_init__ guard needs
│                                    loosening for this case specifically,
│                                    not a redesign of ReasoningFinding)
│
├── portfolioFactors              — embeds, by reference, the EXISTING
│                                    PortfolioFinding /
│                                    PortfolioDoctrineFactor enum
│                                    (DE-003 §3's seven factors — already
│                                    implemented, not redefined)
│
├── alternatives                  — { label: string, rationale: string }[]
│                                    — qualitative Opportunity Cost content
│                                    (DE-003 §Opportunity Cost); no existing
│                                    type to reuse, genuinely new, directly
│                                    justified by an already-named factor
│
└── decisionMemoryReference       — reference (not copy) to the position's
                                     existing DecisionRecord/OutcomeRecord
                                     history (DE-005 §3), when one exists
```

**Deliberately absent**: no execution field of any kind (§3); no
projected-portfolio-state field (§3, §4); no field referencing Investor
Decision, Implementation Intent, or Actual Execution (§4); no field
referencing Execution Guidance (§4); **no lifecycle-state field at all**
— `pending`/`accepted`/`dismissed`/`acted-upon` belong exclusively to
`RecommendationResponse` (C, below), never to this type, per §5's explicit
separation.

### B. `HistoricalRecommendationSnapshot` — persisted, created only on response

Identical field shape to `ComputedDirectionalRecommendation` above, with
one rename and one addition, capturing exactly what §9's persistence
model requires be answerable later:

```
HistoricalRecommendationSnapshot
├── recommendationId              — the SAME identity value the computed
│                                    instance carried as recommendationInstanceId
│                                    (§6) — carried forward, not reminted
├── caseId
├── generatedAt                   — copied from the computed instance,
│                                    unchanged, at the moment of response
├── direction / directionStatement
├── convictionLevel / convictionReason
├── reasoning                     — { currentSituation, supportingEvidence,
│                                    contradictingEvidence, portfolioContext,
│                                    whatWouldChange } — frozen copy, not a
│                                    live reference, from the instant of
│                                    capture onward (§7)
├── portfolioFactors
├── alternatives
├── decisionMemoryReference
│
└── snapshottedAt                 — when this record was written (== the
                                     paired RecommendationResponse's
                                     respondedAt, since both are created in
                                     the same event, §5)
```

This is the type that makes §9's "sufficient to answer later" requirement
concrete: every field DE-002's seven-part structure and DE-004's Conviction
Level require is present, frozen, and requires no future recomputation to
read back.

### C. `RecommendationResponse` — persisted, Investor-authored

```
RecommendationResponse
├── recommendationId              — references the HistoricalRecommendationSnapshot
│                                    above (created together, same event, §5)
├── state                         — "accepted" | "dismissed"
│                                    ("pending" = no record exists at all;
│                                    "acted_upon" = derived, never stored
│                                    here, §5)
└── respondedAt
```

Named, not fully designed — as the prior draft already stated and this
revision does not change: whether this is its own minimal table, an
extension of the existing Decision-recording flow, or another shape is a
genuine implementation-phase question (§12), not a domain-model decision.
What this document commits to, unchanged: it is **Investor-authored, not
Atlas-authored**, and it is **never a mutable field on either
`ComputedDirectionalRecommendation` or `HistoricalRecommendationSnapshot`**
(§5, §9).

## 9. Persistence Model

**`RecommendationWithheld` is unchanged: computed fresh on every request,
never persisted, never independently identified** — exactly as it already
works today (`atlas/decision_engine/contracts.py:877-914`). This document
does not touch that.

**Atlas SHALL NOT persist a Directional Recommendation merely because it
was computed.** This is the locked principle, restated here in its most
operational form: producing a `ComputedDirectionalRecommendation` — even
displaying it to the Investor — writes nothing, ever. **Persistence occurs
only when an Investor's response creates historical significance** — the
single trigger this entire document recognizes, no exceptions:

- **Persisted, and only then**: the full `HistoricalRecommendationSnapshot`
  shape (§8B), written once, at the moment an Investor accepts or
  dismisses — never before, never speculatively, never because a
  background computation happened to run.
- **Persisted in the same event**: the paired `RecommendationResponse`
  (§8C).
- **Never persisted merely by computation**: a `ComputedDirectionalRecommendation`
  that nobody responds to leaves no trace after the request that produced
  it ends. This is not a gap — it is the entire point of the approved
  ontology: Atlas's own unengaged opinions are not history.
- **Not persisted, computed at read time**: whether an `ExecutionGuidance`
  is currently `active` for a given `recommendationId` (a query against
  `DE-006`'s own store, not a field here); whether a Recommendation has
  been "acted upon" (derived from Investor Decision/Implementation Intent
  records, §5); which `HistoricalRecommendationSnapshot`, if more than one
  exists for a Case, is the most recent (derived by `generatedAt`
  ordering, §6).
- **Never persisted, under any candidate**: anything execution-shaped,
  anything portfolio-simulation-shaped, anything Actual-Execution-shaped —
  the same non-responsibilities as §3, restated here because a
  persistence model is exactly where scope creep tends to enter through
  the back door.

**The persisted snapshot must be sufficient, on its own, to answer later**
— without relying on any future recomputation, which would silently
substitute *today's* evidence for the evidence that actually existed at
response time (§1's own Historical Recommendation Snapshot definition):
what Atlas recommended (`direction`, `directionStatement`); why
(`reasoning.supportingEvidence`); what counter-evidence existed
(`reasoning.contradictingEvidence`); what the Atlas Conviction Level was
(`convictionLevel`, `convictionReason`); what portfolio context supported
it (`portfolioFactors`, `reasoning.portfolioContext`); and what conditions
could change the view (`reasoning.whatWouldChange`). Every one of these is
a named field in §8B's snapshot shape — this is not an aspiration, it is
checked directly against the field list.

## 10. Frontend Consumption Model

Consistent with, and no redesign of, the Recommendation Workspace
architecture already produced. The frontend does not need to know or care
whether it is reading a `ComputedDirectionalRecommendation` or a
`HistoricalRecommendationSnapshot` — both share the same content shape
(§8) — only whether a `RecommendationResponse` exists changes what is
shown for state:

- `RecommendationHeader` consumes `direction`, `directionStatement`, and
  the derived (not stored on either type, §5) investor-response state.
- `RecommendationReasoning` consumes `reasoning.supportingEvidence` /
  `reasoning.contradictingEvidence` directly — the same objects Business/
  Valuation/Risk already render below it, never a re-derived copy (closing
  the "coupling risk" the Recommendation Workspace design flagged: with a
  real, identified `reasoning` field to point at, the traceability hooks
  that design specified can now resolve to something concrete instead of
  an aspiration).
- `RecommendationConviction` consumes `convictionLevel` /
  `convictionReason` — and SHALL be labeled distinctly in the UI from the
  existing, already-shown `AnalysisConvictionLevel` in the Evidence
  section (§11's resolved ambiguity, carried through to the presentation
  layer, not just the type layer).
- `PortfolioImpactPanel` consumes `portfolioFactors`, filtered to
  relevance exactly as `DE-003` §4 already requires.
- `AlternativesPanel` consumes `alternatives` directly.
- `RecommendationValidityPanel` consumes `reasoning.whatWouldChange`.
- **`ExecutionGuidancePanel` consumes nothing from this document's model
  at all** — it is fetched or queried independently via `recommendationId`,
  per `DE-006` §10's own gating logic, unchanged. This is the concrete
  proof that §4's "no reference field" decision does not block the
  frontend: the query direction (find Execution Guidance for this
  Recommendation) never needed a field on Recommendation to work.

## 11. Design Rationale

**Why persistence is triggered by Investor response, and only by Investor
response.** This is the approved Recommendation Ontology Decision, applied
here rather than re-argued: Atlas's own existing persistence pattern,
observed directly across `DecisionRecord`, `OutcomeRecord`, `TradeLogEntry`,
and Observation/Evidence, persists a fact only when an Investor's own
action creates that fact — never because a computation ran, however
conclusive. The prior draft of this document broke that pattern by
persisting on Creation (i.e., on computation). This revision restores
consistency with it: a `HistoricalRecommendationSnapshot` is written for
exactly the same reason a `DecisionRecord` is written — because the
Investor did something — and for no other reason. `UX-012` §28's
pending/accepted/dismissed/acted-upon states, and `DE-006` §6's "retained,
not deleted" language for Invalidated Execution Guidance, are both
satisfied the moment a real response exists to persist against; neither
requires persisting *every* computation on the chance an Investor might
someday respond to it. `DE-005` §1's Decision-history immutability
precedent is honored exactly as before — once a snapshot exists, it is
never rewritten — but the precedent does not, on inspection, require
*every* computed opinion to become history, only the ones an Investor
actually engaged with.

**Why Execution Guidance is referenced, never contained.** Unchanged from
the prior draft, and still correct: containing it would make every
consumer of a computed or persisted Recommendation also a consumer of
Execution Guidance, coupling two documents your instructions explicitly
require to stay separated. Referencing it — the direction `DE-006` §9
already chose (`ExecutionGuidance.recommendationId`, not the reverse) —
means Recommendation, in either its computed or persisted form, can be
defined and reasoned about with zero knowledge that Execution Guidance
exists at all.

**Why the Atlas Conviction Level (`DE-004` §3) is a genuinely new field,
not a reuse of the existing `AnalysisConvictionLevel`.** This is the one
real ambiguity `DE-004` itself leaves open, identified and resolved here
rather than silently decided by implication. `DE-004` §2 disambiguates
"Atlas Conviction Level" from two *investor self-reported* Confidence
fields — it was written without reference to `atlas/analysis_engine/conviction.py`'s
already-real, already-shipped, 5-level `AnalysisConvictionLevel`
(`very_high`/`high`/`moderate`/`low`/`insufficient_evidence`), which is a
different, Atlas-computed, case-wide field that already exists and is
already shown in the Evidence section today. `DE-004` §3 explicitly
defines a **3-level** scale (High/Medium/Low) specific to a Recommendation's
own Direction — not a relabeling of the existing 5-level field, and not
something `DE-004` asks to be merged with it. Resolving the ambiguity
`DE-004` leaves open: `convictionLevel` (present on both
`ComputedDirectionalRecommendation` and its `HistoricalRecommendationSnapshot`
counterpart) is a **new, independently computed field**, governed by
`DE-004`'s own
3-level definition, that MAY draw on similar underlying evidence as the
existing case-wide `AnalysisConvictionLevel` but is not derived from it by
a fixed formula and is never presented under the same label. This is new
judgment this document introduces, not a restatement of something `DE-004`
already decided — flagged as such rather than presented as settled.

## 12. Open Questions

- Whether a *second* response to a Case whose computed Recommendation has
  changed since an earlier response creates a new
  `HistoricalRecommendationSnapshot` or amends the existing one (§5, §6)
  — narrowed considerably from the prior draft's version of this question
  (which had to consider every computation, not just repeat responses),
  but still genuinely open.
- Whether `RecommendationResponse` (§8C) is its own minimal persistence
  table, an extension of the existing Decision-recording flow, or another
  shape entirely — named, not designed, per §8's own caveat.
- Whether "acted upon" detection (§5) — tracing a later Investor Decision
  record back to a specific `recommendationId` — needs an explicit field
  on that Decision record, or can be inferred structurally; `DE-006` §4
  already flagged the adjacent pre-population question as undecided, and
  this is its sibling question, equally undecided here.
- Whether superseded `HistoricalRecommendationSnapshot` records need their
  own surfaced history view in Recommendation Workspace, or stay
  retrievable but unsurfaced (§6) — a presentation-layer decision, not a
  domain-model one.
- Whether `ReasoningFinding.what_would_change`'s existing `__post_init__`
  guard (`atlas/decision_engine/contracts.py:771-777`) should be loosened
  generally, or whether a Computed Directional Recommendation should carry
  its own, separately-validated copy of that field instead of embedding
  `ReasoningFinding` directly — an implementation-time contract-design
  choice this document flags but does not resolve.
- The `DE-006` pending-Execution-Guidance Invalidated-state ambiguity
  named in §4 — a future clarification for `DE-006` itself, not resolved
  here and not a blocker for this document.

## 13. Recommended Next Step

Backend implementation of `ComputedDirectionalRecommendation` — the actual
`atlas.decision_engine`/`atlas.analysis_engine` evaluator logic that
produces it — is the correct next step now that this domain model exists,
*ahead of* any Recommendation Workspace frontend work, per that design's
own §9 ordering, which named this exact gap as the blocker. The
`HistoricalRecommendationSnapshot`/`RecommendationResponse` persistence
layer (§7–§9) is a smaller, second piece of that same backend work —
smaller than the prior draft implied, since it is now triggered by a
specific Investor action rather than by every qualifying computation.
Execution Guidance (`DE-006`) implementation follows once
`ComputedDirectionalRecommendation` is real, per `DE-006` §7's own
dependency (Execution Guidance cannot exist without a Recommendation).

---

## 14. Self-Review (Ontology Corrective Pass)

Performed against your explicit checklist for this revision — the
document above already reflects every fix this pass produced:

- **Eager machine-opinion persistence.** This was the prior draft's
  central defect: §5's "Created — when [a computation] clears the gate"
  language persisted a `DirectionalRecommendation` on every qualifying
  analysis run, independent of Investor engagement. Corrected throughout
  §5, §7, §9, and §11 — persistence now triggers exclusively on
  `RecommendationResponse` creation. Verified by re-reading §9's bullet
  list: every "persisted" item is now conditioned on a response existing;
  none is conditioned on computation alone.
- **Duplicate truth.** The prior draft's eager-persistence model meant a
  frozen row could sit alongside a live pipeline recomputing the same
  facts before anyone had looked at the frozen copy — two representations
  of "the current state" existing simultaneously. Eliminated: under the
  revised model, no persisted representation exists at all until an
  Investor response creates one, and that one is explicitly historical
  ("what Atlas said then"), never competing with "what Atlas says now."
- **Lifecycle state leaking onto Recommendation itself.** Checked §8A
  (`ComputedDirectionalRecommendation`) and §8B
  (`HistoricalRecommendationSnapshot`) field-by-field: neither carries a
  `state`/`pending`/`accepted`/`dismissed`/`acted-upon` field anywhere.
  That vocabulary exists exclusively on §8C (`RecommendationResponse`).
  This was already correct in the prior draft's field list and remains so
  — confirmed, not newly fixed.
- **Unnecessary identity/version fields.** §6 no longer specifies *how*
  `recommendationInstanceId`/`recommendationId` is generated (UUID, hash,
  compound key) — the prior draft's `(caseId, generatedAt)` compound-key
  suggestion is removed, per your explicit instruction not to canonize an
  algorithm. No version-number field was ever added, and none is added
  now — recency-by-`generatedAt` remains sufficient for both the computed
  and persisted sides.
- **Hidden Execution Guidance ownership.** Re-verified: no field on
  `ComputedDirectionalRecommendation`, `HistoricalRecommendationSnapshot`,
  or `RecommendationResponse` references Execution Guidance in either
  direction. The one-way `ExecutionGuidance.recommendationId` FK (`DE-006`
  §9) remains the sole link, and §4 now explicitly names the one place
  this creates a real (not hidden) seam — pending-state Execution Guidance
  has nothing persisted to be Invalidated against — surfaced rather than
  papered over.
- **Inability to reconstruct historical truth.** Checked against §9's own
  explicit list (what was recommended, why, counter-evidence, Conviction,
  portfolio context, validity conditions) — every item is a named field on
  §8B's snapshot shape, captured verbatim at response time, never relying
  on future recomputation. This is what the ontology decision's own §5
  concluded was required, and only required for content an Investor
  actually engaged with — confirmed consistent here.
- **Accidental persistence of Recommendation Withheld.** Explicitly
  re-checked: §1, §4, and §9 each independently state
  `RecommendationWithheld` is unchanged, unpersisted, and outside this
  document's one persistence exception. No field, table, or lifecycle
  description anywhere in the revised document attaches identity or
  persistence to it.
- **Duplication of `ReasoningFinding` data.** §7 now states precisely when
  duplication is real and unavoidable: at the instant of snapshotting,
  `ReasoningFinding`'s live values are copied into the
  `HistoricalRecommendationSnapshot`, and from that instant on the
  snapshot no longer tracks the live type. This is a deliberate, one-time,
  Investor-triggered copy — not the same failure mode as the prior draft's
  eager, untriggered duplication, and is named as a legitimate exception
  rather than glossed over.
- **Violation of Atlas's persist-investor-history / derive-analysis
  principle.** This is the test the entire revision was performed
  against. §11 restates the principle explicitly (observed directly from
  `DecisionRecord`/`OutcomeRecord`/`TradeLogEntry`, not asserted) and
  checks the revised model against it: persistence triggers exclusively on
  Investor action, matching every other persisted entity in this codebase,
  with no remaining exception.

**Master-doctrine changes inspected, not modified.** `docs/ATLAS_DECISION_ENGINE_DOCTRINE.md`'s
§8 pointer paragraph and §13 dependency-table row for `DE-007` were
re-read against this revision: neither asserts a specific persistence
timing (eager vs. response-triggered) or a specific identity algorithm —
both describe only that `DE-007` "specifies the field-level shape" and
"the separation between Atlas-authored reasoning content and the
Investor's own accept/dismiss response," which remains true under the
corrected ontology without amendment. No change made to the master
doctrine in this pass.

No further changes were made after this review; the document above
already reflects it.
