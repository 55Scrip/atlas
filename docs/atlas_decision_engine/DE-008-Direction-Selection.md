# DE-008 — Atlas Direction Selection

**Status:** Draft v0.2 (incorporates the approved valuation-semantics
corrective pass). Companion specification to
`docs/ATLAS_DECISION_ENGINE_DOCTRINE.md` §8 (Recommendation Framework) and
`DE-001` §2 (the six directions), which it implements the decision rule
for — it does not redefine either. Governed by, and subordinate to, that
Doctrine and to `DE-001` through `DE-007`. Documentation only — no code,
no frontend, no backend accompanies this specification.

**This document does not redesign `DE-001` through `DE-007`.** Every
direction's meaning, every reasoning-section requirement, every Portfolio
Intelligence factor, every Conviction level, every Decision Memory rule,
every Execution Guidance boundary, and every Recommendation domain-model
field defined in those seven documents is treated as fixed. DE-008
answers exactly one question those documents leave open: given
already-evaluated analysis, *which* of `DE-001` §2's six directions — or
`RecommendationWithheld` — does the evidence support, and why.

**v0.2 note.** v0.1 of this document contained one unproven claim,
identified and corrected during doctrine review before this version was
finalized: it treated `ValuationStatus.UNDERVALUED` as sufficient, by
itself, to satisfy `DE-001` §2's BUY/ADD valuation criterion. That claim
did not survive scrutiny against the actual implementation and is
corrected throughout this version — see §10 and §21 in particular. No
other part of v0.1 changed.

---

## 1. Definition

**Recommendation Direction is the terminal categorical conclusion of
`DE-002`'s seven-part reasoning structure** — specifically the output of
`DE-002` §2.5: "the specific conclusion the preceding sections [Current
Situation, Evidence, Counter-Evidence, Portfolio Context] support,"
expressed as exactly one of six mutually exclusive values, with "an
explicit link back to the specific Evidence, Counter-Evidence, and
Portfolio Context items that produced it."

Precisely: given the current, evaluated state of Business Evaluation,
Valuation, Portfolio Intelligence, and Reasoning for one Case (and, where
one exists, the one portfolio holding tied to it), Direction answers
exactly one question — **which of six orientations toward this position
does the evidence currently support: initiate new exposure, increase
existing exposure, maintain existing exposure unchanged, partially reduce
existing exposure, fully remove existing exposure, or take no
exposure-changing view at all.**

**Direction is not:**

- **An order** — no order type, quantity, or routing information.
- **Execution Guidance** — `DE-006` §1 answers *how* a direction could be
  carried out; Direction answers *what* the direction is.
- **Investor intent** — the Investor's own `BUY/SELL/HOLD/WATCH/PASS` and
  Implementation Summary record what the Investor decided; Direction is
  Atlas's advisory conclusion (`DE-006` §4's boundary, unchanged here).
- **Actual execution** — undefined, out of scope, `DE-006` §4.
- **A price target** — `DE-002` §2.5 carries no price; that is `DE-006`'s
  `executionRange`.
- **A conviction level** — `DE-004` §6: "The two SHALL always be stated
  together... and SHALL NOT be collapsed into a single combined signal."
  Resolved fully in §15.
- **A valuation status** — `ValuationStatus.EXPENSIVE` is one *input* to
  Direction, not a synonym for it; Business Evaluation and Valuation are
  structurally independent questions (`analysis_engine/__init__.py`'s own
  ownership statement), and neither one alone is Direction.

---

## 2. The six directions — ontology

| Direction | Asserts | Must already be true | Does NOT assert | Confusable with |
|---|---|---|---|---|
| **BUY** | Evidence supports initiating new exposure | No existing position; Business and Valuation both positive | Size, price, timing, urgency | ADD |
| **ADD** | Evidence supports increasing existing exposure | Position exists; thesis intact; same Business+Valuation support as BUY | How much, at what price | BUY, HOLD |
| **HOLD** | Evidence, actively reviewed, does not support any change | Position exists | That the position is flawless, or facts couldn't change | NO ACTION |
| **TRIM** | Evidence supports reducing, not eliminating, exposure | Position exists; thesis partly weakened *or* sizing/concentration excessive | That the business/thesis is broken | EXIT |
| **EXIT** | Evidence supports eliminating exposure entirely | Position exists; a *specific, named* thesis dependency has failed, or Business Evaluation has reversed | That the business is universally bad | TRIM |
| **NO ACTION** | Atlas has no directional view to offer, and evidence was sufficient to reach that conclusion honestly | No existing position; Conviction was successfully assessed | Uncertainty or missing evidence (that is RecommendationWithheld) | RecommendationWithheld |

---

## 3. Position-state dependency

Tested directly against `DE-001` §2's own per-direction text:

- **BUY requires NOT held** ("a business the Investor does not currently
  hold").
- **ADD requires held** ("increasing an existing position").
- **HOLD requires held.** Not an explicit `SHALL` in `DE-001`, but
  structurally necessary — "no change to the *current position*"
  presupposes one exists. There is nothing to maintain without a
  position.
- **TRIM requires held**, **EXIT requires held** — both definitionally
  require exposure to reduce or remove.
- **NO ACTION requires NOT held.** `DE-001` §2 draws this contrast
  directly: "as opposed to Hold, which is an active, evidence-based
  statement about an existing position."

**Invariant:** `{BUY, NO_ACTION}` apply exclusively to unheld securities;
`{ADD, HOLD, TRIM, EXIT}` apply exclusively to held securities. This
bifurcation is the first, structural partition of the entire decision
space (§18).

---

## 4. Required analytical prerequisites

**Hard gates** (already implemented, reused verbatim — `atlas.analysis_engine.recommendation`/`recommendation_conviction`):

- Business Evaluation, Valuation, Portfolio Intelligence, Reasoning all
  `EVALUATED` — exactly `RequiredBeforeRecommendation`'s four existing
  members.
- Recommendation Conviction assessable — `calculate_recommendation_conviction(...)`
  returns a real assessment, not `None`.

Any failure here → RecommendationWithheld, unconditionally, before
anything else is considered.

**A second, distinct prerequisite — new in v0.2, exists only for
exposure-increasing directions:**

- **Valuation Support for Capital Deployment** — the conclusion `DE-001`
  §2 requires for BUY/ADD specifically: whether current price is
  attractive relative to the Valuation Philosophy's assumption-based
  scenario range (`DE-004` §5; `ValuationMethodKind.SCENARIO_BEAR/BASE/BULL`).
  **This prerequisite does not exist as a computed concept anywhere in
  the codebase today** (see §10). Its absence does not fail the hard gate
  above — Business/Valuation/Portfolio Intelligence/Reasoning can all be
  fully `EVALUATED`, and Conviction can be fully assessable, while this
  second prerequisite remains unmet. It blocks BUY/ADD specifically, not
  Direction Selection generally.

**Soft factors:** the specific categorical findings within Business/
Valuation/Portfolio Intelligence/Reasoning (Growth status, Capital
Allocation status, Valuation Evidence, Risk categories, open questions,
contradicting evidence) — shape *which* direction is selected once the
hard gate is cleared.

**Irrelevant to Direction:** execution-shaped content; Decision Memory's
prior execution price; reconciliation status; Catalysts/Scenario Analysis
(`UnavailableCapability`).

---

## 5. Allowed Direction inputs

| Input | Included? | Justification |
|---|---|---|
| Business Evaluation (`BusinessCategoryStatus` — Growth, Capital Allocation) | **Yes** | Determines thesis integrity; central to every direction |
| Valuation Evidence (`ValuationStatus`, FCF-Yield-relative — §10) | **Yes, scoped precisely** | Real signal, but not equivalent to Valuation Support for Capital Deployment |
| Portfolio Intelligence (Allocation, Concentration) | **Yes, narrowly** | Dampening-only adjustment (§12) |
| Reasoning (Evidence/Counter-Evidence/Open Questions) | **Yes** | Where Counter-Evidence and Open Questions live |
| Recommendation Conviction | **Yes, as qualifier only** | Existence-gate + attached label, never a selector (§15) |
| Risk — `THESIS_RISK`, `BUSINESS_RISK` | **No** | Already reflected via Reasoning/Business; double-counting |
| Risk — `FINANCIAL_RISK`, `VALUATION_RISK` | **Yes** | Genuinely independent signal |
| Decision Memory — Thesis Synthesis | **Yes, narrowly** | Distinguishes ADD/TRIM-worthy states |
| Decision Memory — prior execution price, investor Confidence | **No** | Anchoring risk; different concept |
| `HistoricalRecommendationSnapshot` / `RecommendationResponse` | **No** | Layering violation (§16) |
| Current holding — `HoldingLinkage` | **Yes** | The §3 partition itself |
| Current holding — weight/value | **Yes, via Portfolio Intelligence** | Not read raw |
| Current holding — reconciliation status | **No** | Workflow fact, not analytical |

---

## 6. Separation of concerns

| Concept | Answers |
|---|---|
| **Direction** | What action direction does the current analysis support? |
| **Recommendation Conviction** | How strongly does the evidence support *that* conclusion? |
| **Execution Guidance** | If that direction is followed, how might it be carried out? |
| **Portfolio Simulation** | What would my portfolio look like if I did something (undefined)? |
| **Investor Decision/Implementation Intent** | What did the Investor decide/intend? |
| **Actual Execution** | What happened in the market (undefined)? |

---

## 7. BUY vs ADD

The only dimension that survives testing by contradiction (size doesn't
distinguish them; thesis status doesn't) is position existence.

**BUY means:** `HoldingLinkage.ABSENT`, and Business + Valuation jointly
support initiating exposure (§10 — currently unsatisfiable).
**ADD means:** `HoldingLinkage.PRESENT`, thesis intact, and the same
standard BUY requires (`DE-001` §2: "Same durability and valuation
conditions as Buy").

---

## 8. HOLD vs NO ACTION

**Invariants:**
- **HOLD SHALL mean:** an existing position, fully evaluated, for which
  the evidence does not currently support a change — an affirmative,
  evidenced conclusion, never silence.
- **NO ACTION SHALL mean:** no existing position, a Recommendation
  Conviction level was successfully assessed, and the evaluated evidence
  does not support initiating one.
- **NO ACTION SHALL NOT be produced when Recommendation Conviction could
  not be assessed** — that is RecommendationWithheld, unconditionally.

---

## 9. TRIM vs EXIT

**Invariants:**
- **TRIM SHALL NOT** be produced where the thesis has been fully
  invalidated.
- **EXIT SHALL NOT** be produced for a sizing/concentration problem
  alone, or for generalized risk elevation without a specific, nameable
  failed assumption.
- **No accumulation of TRIM-triggering factors composes into EXIT.** EXIT
  is reached only through thesis invalidation.

---

## 10. Valuation role (revised, v0.2)

### 10.1 Valuation Evidence vs Valuation Support for Capital Deployment

Verified directly against the real implementation
(`atlas/analysis_engine/valuation/cash_flow.py`'s own rule table),
not assumed:

> 3. Current yield exceeds every historical yield → `UNDERVALUED`.
> 4. Current yield is below every historical yield → `EXPENSIVE`.
> 5. Otherwise (within the historical range) → `FAIRLY_VALUED`.

*"'Cheap' and 'expensive' are always relative to the same company's own
recorded history — never a fixed yield percentage, never a P/E cutoff."*
(module docstring, verbatim).

**`ValuationStatus` is Valuation Evidence — a real, honest, but purely
self-referential signal:**

- **`UNDERVALUED`** = positive historical-relative valuation evidence:
  current FCF yield exceeds every yield this company has recorded in its
  own history. **Does not prove intrinsic undervaluation.**
- **`FAIRLY_VALUED`** = neutral historical-relative valuation evidence:
  current yield sits within the company's own historical range. **Does
  not prove the price equals intrinsic fair value.**
- **`EXPENSIVE`** = negative historical-relative valuation evidence:
  current yield is below every recorded historical yield. **Does not,
  alone, prove intrinsic overvaluation under a full assumption-based
  model.**

None of the three, alone, constitute **Valuation Support for Capital
Deployment** — the conclusion `DE-001` §2 actually requires for BUY/ADD:
*"the Valuation Philosophy range, under its stated assumptions, suggests
the current price is attractive relative to that range."* "Under its
stated assumptions" is the tell: this is `DE-004` §5's scenario-based
value-estimate range (`ValuationMethodKind.SCENARIO_BEAR/BASE/BULL`),
confirmed by the same source file to be **permanently `INSUFFICIENT_INPUT`
today** (`ValuationDataGapKind.MISSING_SCENARIO_ASSUMPTIONS`: "no forward
assumption was explicitly supplied for this scenario — always true this
sprint"). `FCF_YIELD_RELATIVE` was deliberately chosen instead because it
*"needs the fewest unsupported assumptions"* — an honest, narrower proxy,
never presented in its own doctrine as equivalent to the assumption-based
range `DE-001` describes. "The range" in `DE-001` §2 and "the range" in
`cash_flow.py`'s rule table are two different objects that share a word.

### 10.2 What follows

- **Can a great business still be EXIT on valuation alone?** No — EXIT
  requires thesis invalidation or Business reversal (§9); valuation
  extremity with an intact thesis is TRIM's territory.
- **Can an expensive holding still be HOLD?** No — `EXPENSIVE` is, by its
  own definition, an *extreme*, which HOLD's own criterion ("not at
  either extreme," `DE-001` §2) excludes. It resolves to TRIM, a
  self-sufficient direction.
- **Can an undervalued security be NO ACTION because business quality is
  weak?** Yes — Business and Valuation are independent; positive
  Valuation Evidence alone cannot overpower a `WEAK` Business conclusion.
- **Can Valuation Evidence alone produce BUY or ADD?** No, at any of its
  three values — see §10.1.
- **Can Valuation Evidence alone produce HOLD, for a held position?**
  Only `FAIRLY_VALUED` — its own definition ("within the historical
  range, not at either extreme") is, word for word, the same shape of
  claim as HOLD's own doctrinal criterion. `UNDERVALUED`, being the
  *favorable* extreme, does **not** satisfy HOLD's criterion either — see
  §17's held/`UNDERVALUED` finding.

**Structural rule, unchanged from v0.1, still governing the AND/OR
asymmetry:** initiating or adding exposure requires Business AND
Valuation Support for Capital Deployment both positive; reducing exposure
can be triggered by Business OR Valuation Evidence OR Portfolio Context
alone.

---

## 11. Business role

Unchanged from v0.1. Weak business quality blocks BUY/ADD regardless of
price (§10's AND rule). Strong business quality alone does not support
BUY/ADD (needs Valuation Support for Capital Deployment too, which does
not exist — so today, no business quality, however strong, makes BUY/ADD
reachable). Business Evaluation reversal alone is sufficient for EXIT
(`DE-001` §2's explicit "or the Business Evaluation conclusion has
reversed" branch).

---

## 12. Portfolio Intelligence role

Unchanged from v0.1. **Invariant: Portfolio Intelligence is
dampening-only.** Can push toward more conservative exposure (block
BUY/ADD, downgrade toward TRIM) but never manufactures a positive
direction and never reaches EXIT.

---

## 13. Risk role

Unchanged from v0.1. `FINANCIAL_RISK`/`VALUATION_RISK` are Direction
inputs only (not Conviction, not Execution Guidance); `THESIS_RISK`/
`BUSINESS_RISK` excluded (double-counting). **Risk (Financial/Valuation)
SHALL NOT independently produce EXIT.**

---

## 14. Evidence and Counter-Evidence

Unchanged from v0.1. Unresolved Counter-Evidence lowers Conviction but
leaves Direction unchanged unless it invalidates a named thesis
assumption (→ EXIT) or is severe enough to collapse Evidence Coverage
itself (→ RecommendationWithheld, via the pre-existing floor).

---

## 15. Recommendation Conviction role

Unchanged from v0.1. Tested against `DE-004` §6: *"a High-conviction Hold
and a Low-conviction Buy are both coherent, complete Atlas
Recommendations... The two SHALL always be stated together... and SHALL
NOT be collapsed into a single combined signal."*

**Invariant: Recommendation Conviction SHALL NOT determine or restrict
Direction** — only gate its existence (the pre-existing floor, §4) and
qualify it once chosen.

---

## 16. Decision Memory role

Unchanged from v0.1. Prior Decisions/Outcomes provide context (Thesis
Synthesis, first-purchase-vs-continuation), never a default or anchor.

**Invariant: Direction Selection SHALL NOT read `RecommendationResponse`
or `HistoricalRecommendationSnapshot` records.** Both are
investor-response-triggered, persisted, downstream artifacts (the locked
Ontology Decision); reading them here would reintroduce exactly the
staleness/anchoring that decision was designed to prevent.

---

## 17. Current holding-state role

Unchanged from v0.1. `HoldingLinkage` (§3's partition), weight/value (via
Portfolio Intelligence). Reconciliation status excluded — a workflow
fact, not analytical (mirrors `risk/contracts.py`'s own `EXECUTION_RISK`
distinction).

---

## 18. Conflict-resolution protocol

Unchanged in ordering from v0.1; stage 4's content is updated to reflect
§10's corrected valuation semantics.

1. **Hard gate** (§4). Failure → RecommendationWithheld, stop.
2. **Position-state partition** (§3).
3. **Thesis/Business integrity check** (held only). Thesis Invalidated →
   EXIT, unconditional, before any positive-case reasoning.
4. **Standalone attractiveness** (Business × Valuation). For
   exposure-increasing directions specifically, this stage now also
   checks Valuation Support for Capital Deployment (§10) — currently
   never satisfiable, so this stage can never conclude BUY/ADD today; it
   can still conclude the Business leg has failed independently (§11).
5. **Risk overlay** (§13).
6. **Portfolio-context adjustment** (§12).
7. **Contradiction residue check** (§14).
8. **Recommendation Conviction** (§15) — attached, never consulted by
   stages 2–7.
9. **Direction finalized**, or RecommendationWithheld if no stage above
   reached a supportable conclusion (§19).

---

## 19. RecommendationWithheld conditions (revised, v0.2)

**Original five classes (v0.1, unchanged):**

1. Any of the four stages not `EVALUATED`.
2. Evidence Coverage `NOT_APPLICABLE`/`NONE`.
3. Contradiction severe enough to collapse Evidence Coverage itself.
4. Position-state genuinely indeterminate (theoretical today).
5. An irreducible tie the §18 ordering doesn't resolve.

**Sixth class, new in v0.2:**

6. **Evidence is otherwise complete (Business, Portfolio, Reasoning,
   Conviction all assessed), but the specific conclusion required for the
   direction under consideration — Valuation Support for Capital
   Deployment — does not exist as a computable concept, and no
   independently-sufficient real evidence exists to ground an alternative
   direction honestly instead.**

This sixth class is a distinct triggering path for the same, unmodified
DE-004 §4 mechanism — not a new mechanism, and structurally later-stage
than classes 1–3 (it can only be reached after the hard gate, position
partition, and thesis-integrity check have all already passed).

**The governing test, applied throughout this document to distinguish
class 6 from a genuine NO ACTION/HOLD conclusion:** *would this outcome be
forced identically for every case sharing this evidence pattern, purely
because of a missing systemic capability, regardless of case-specific
facts?* If yes — RecommendationWithheld; the alternative would silently
disguise a capability gap as a case-specific conclusion. If the outcome
genuinely varies with real, case-specific evidence — a genuine Direction.

**Restated safeguard (unchanged):** HOLD and NO ACTION both require a
successfully-assessed Conviction level. If Conviction assessment fails,
neither is available — only RecommendationWithheld.

---

## 20. Deterministic Direction Matrix (revised, v0.2)

All dimensions use real, existing enum values. **Pre-condition for every
row: Conviction assessable (not `None`).** If not — RecommendationWithheld
before the matrix applies.

### Not held

| Business | Valuation Evidence | Dampening | Direction |
|---|---|---|---|
| WEAK | any | any | NO ACTION |
| MODERATE/STRONG | `UNDERVALUED` or `FAIRLY_VALUED` | None | **RecommendationWithheld** |
| MODERATE/STRONG | `UNDERVALUED` or `FAIRLY_VALUED` | Present | NO ACTION |
| MODERATE/STRONG | `EXPENSIVE` | any | NO ACTION |

`UNDERVALUED` and `FAIRLY_VALUED` are treated identically throughout —
deliberately: neither constitutes Valuation Support for Capital
Deployment, so ranking one above the other would silently reintroduce
exactly the error this revision corrects. Dampening (real, case-specific
negative evidence — Risk or Portfolio pressure) is what distinguishes
NO ACTION from RecommendationWithheld here, per §19's governing test, not
the Valuation Evidence value itself.

### Held, thesis Intact

(Thesis Invalidated → EXIT, unconditional, checked at stage 3.)

| Business | Valuation Evidence | Dampening | Direction |
|---|---|---|---|
| WEAK (partly weakened) | any | any | TRIM |
| MODERATE/STRONG | `UNDERVALUED` | None | **RecommendationWithheld** |
| MODERATE/STRONG | `UNDERVALUED` | Present | TRIM |
| MODERATE/STRONG | `FAIRLY_VALUED` | None | HOLD |
| MODERATE/STRONG | `FAIRLY_VALUED` | Present | TRIM |
| MODERATE/STRONG | `EXPENSIVE` | any | TRIM |

**`UNDERVALUED` + held + no dampening does not fall back to HOLD.** HOLD's
own criterion — *"valuation sits within its previously stated range
rather than at either extreme"* (`DE-001` §2) — excludes `UNDERVALUED` on
the same textual basis it excludes `EXPENSIVE`: both are, by their own
code-level definitions, extremes. `EXPENSIVE` has a self-sufficient
fallback (TRIM, whose triggers never depended on Valuation Support for
Capital Deployment). `UNDERVALUED`'s natural direction is ADD — exactly
the one this document blocks — leaving no honest landing spot but
RecommendationWithheld. This asymmetry is structural, not an
inconsistency.

---

## 21. Hard invariants (revised, v0.2)

1. **BUY SHALL NOT** be produced for a held position, when Business is
   not positive, or **when Valuation Support for Capital Deployment
   cannot be established** — which is always, today.
2. **ADD SHALL require** `HoldingLinkage.PRESENT`, an intact thesis, and
   the same standard as BUY, including Valuation Support for Capital
   Deployment — unsatisfiable today.
3. **HOLD SHALL** mean an actively-reviewed, evidenced "no change"
   conclusion for a held position, valid only when its own valuation
   criterion (`FAIRLY_VALUED`, or equivalent "not at either extreme"
   evidence) is independently satisfied.
4. **NO ACTION SHALL NOT** be produced for a held position, when
   Conviction is unassessable, or **merely to conceal that Valuation
   Support for Capital Deployment is unavailable** — it SHALL require
   real, case-specific evidence (e.g., `EXPENSIVE` Valuation Evidence, or
   dampening) independent of that missing prerequisite.
5. **TRIM SHALL NOT** be produced where thesis is invalidated; SHALL
   require partial weakening or portfolio/risk dampening on an intact
   thesis, or `EXPENSIVE` Valuation Evidence.
6. **EXIT SHALL** require a specific, named failed assumption or a
   reversed Business conclusion — **SHALL NOT** be produced from
   Valuation Evidence alone, at any value, however extreme.
7. **RecommendationWithheld SHALL** be the outcome whenever Conviction is
   unassessable, **or** whenever Valuation Support for Capital Deployment
   is required and unavailable with no independently-sufficient
   alternative evidence — never silently rounded to NO ACTION or HOLD in
   either case.
8. **Recommendation Conviction SHALL NOT** determine or restrict
   Direction.
9. **Portfolio Intelligence and Risk (Financial/Valuation) SHALL NOT**
   independently produce EXIT or independently produce BUY/ADD.
10. **Direction Selection SHALL NOT** read `RecommendationResponse`,
    `HistoricalRecommendationSnapshot`, prior execution price, or
    Execution Guidance content.
11. **`ValuationStatus.UNDERVALUED` SHALL NOT, alone or in combination
    with any other currently-computed signal, be treated as equivalent to
    Valuation Support for Capital Deployment.**

---

## 22. Falsification scenarios (revised, v0.2)

| # | Scenario | Result |
|---|---|---|
| A | No holding, strong business, `UNDERVALUED`, no constraints, high conviction | **RecommendationWithheld** — Business positive, but Valuation Support for Capital Deployment unavailable |
| B | Existing holding, strong business, `UNDERVALUED`, no constraints | **RecommendationWithheld** — same prerequisite blocks ADD; HOLD unavailable too (`UNDERVALUED` is an extreme) |
| C | Existing holding, strong business, `FAIRLY_VALUED`, no negative pressure | **HOLD** — supports exactly *"current FCF yield sits within this company's own historical range,"* no intrinsic claim |
| D | Existing holding, strong business, `EXPENSIVE` | **TRIM** — *"current yield is below this company's own historical range"* is real, sufficient evidence; no intrinsic-overvaluation claim needed |
| E | Thesis broken, `UNDERVALUED` | **EXIT** — thesis invalidation (stage 3) precedes all valuation reasoning; `UNDERVALUED` is irrelevant to a thesis that has already failed |
| F | Strong business, `UNDERVALUED`, existing oversized position (dampening) | **TRIM** — dampening is self-sufficient, independent of the missing prerequisite |
| G | No position, ordinary (`WEAK`) business, `UNDERVALUED` valuation | **NO ACTION** — Business leg fails independently; the valuation question never becomes relevant |
| J | Low Recommendation Conviction, `FAIRLY_VALUED`, no holding | **RecommendationWithheld** — Conviction level is attached, never a gate here; the same Valuation Support for Capital Deployment absence governs regardless of Conviction level (§15) |

---

## 23. Rejected alternatives

Unchanged from v0.1, plus:

- **Treating `UNDERVALUED` as sufficient, or more sufficient than
  `FAIRLY_VALUED`, for BUY/ADD** — rejected; both are Valuation Evidence,
  neither is Valuation Support for Capital Deployment (§10.1).
- **Falling back to NO ACTION for the blocked BUY/ADD cells merely
  because no Direction "feels" available** — rejected explicitly; this
  would fail the §19 governing test (forced identically regardless of
  case specifics = disguised capability gap, not a genuine conclusion).
- **Inventing an interim numeric proxy or threshold to make `UNDERVALUED`
  "count enough" for BUY/ADD** — rejected; not derivable from doctrine or
  the real implementation, and explicitly out of this document's scope to
  invent (Valuation Philosophy's domain, not Direction Selection's).

---

## 24. Open questions

Unchanged from v0.1, plus:

- Whether Valuation Support for Capital Deployment should eventually be
  satisfied by real scenario-valuation implementation, or by a deliberate
  Valuation Philosophy doctrine decision permitting a scoped-down
  interim proxy — belongs to `DE-004`'s domain, not this document.
- Whether a second, graduated tier of Valuation Evidence severity (beyond
  the three-way `UNDERVALUED`/`FAIRLY_VALUED`/`EXPENSIVE` split) would
  ever be useful once Capital Deployment Support exists — not decided
  here, and not needed for the current, fully-specified TRIM/HOLD/EXIT/
  NO ACTION logic.

---

## 25. Implementation implications (revised, v0.2)

A future Direction Selector should be a **pure function**, living in
`atlas/analysis_engine/` (same boundary reasoning as
`recommendation_conviction.py`).

**Explicit implementation note:**

> **The Direction Selector MAY be implemented today for: HOLD, TRIM,
> EXIT, NO ACTION, and RecommendationWithheld** — every one of their
> triggering conditions is fully specified in this document and depends
> only on signals that exist and are computed today.
>
> **BUY and ADD remain reserved-but-unreachable** until Valuation Support
> for Capital Deployment exists as a computed concept — mirroring exactly
> the precedent already established for `RecommendationOutcomeKind.DIRECTIONAL`
> (`atlas/decision_engine/contracts.py`), a reserved discriminant with no
> code path that constructs it. `RecommendationDirection.BUY`/`.ADD`
> (`atlas/analysis_engine/recommendation.py`, already shipped) remain
> valid, doctrine-correct enum members; the Selector's own logic SHALL
> never construct either.

---

## 26. Critical self-review (revised, v0.2)

| Check | Result |
|---|---|
| Any residual `UNDERVALUED` → BUY mapping | None — checked explicitly against every section; `UNDERVALUED` and `FAIRLY_VALUED` are treated identically wherever the missing prerequisite is relevant (§20), which is the strongest available proof no ranking survived |
| Any `FAIRLY_VALUED` → intrinsic fair value claim | None — §10.1, §22 Scenario C state only the literal historical-relative claim |
| Any `EXPENSIVE` → intrinsic overvaluation claim | None — §10.1, §22 Scenario D state only the literal historical-relative claim |
| Fake HOLD/NO ACTION fallback caused by missing BUY/ADD capability | Excluded by the §19 governing test, applied consistently in §20's matrix |
| Valuation evidence leaking into EXIT | Excluded — §9, §21 invariant 6, confirmed by Scenario E |
| BUY/ADD becoming accidentally reachable through another branch | Checked — no matrix row, invariant, or protocol stage produces either; §25 states this explicitly as an implementation-level guarantee |
| Portfolio overriding broken thesis | Still blocked (§12, §18 stage 3 before stage 6) — unaffected by this revision |
| Conviction selecting Direction | Still rejected (§15) — unaffected |
| Status-quo bias | Named honestly, not denied (v0.1's own finding, unaffected: HOLD's bar is genuinely more lenient than BUY's would be, justified by real switching-cost asymmetry, not disguised) |
| Previous Recommendation anchoring | Still forbidden (§16, invariant 10) — unaffected |

---

## 27. Recommended next step

Not implementation of BUY/ADD — that remains blocked on Valuation Support
for Capital Deployment, a Valuation Philosophy question (`DE-004`'s
domain), not a Direction Selection question. The actionable next step is
implementation of the Direction Selector for the five currently-reachable
outcomes (§25), followed by tracking Valuation Support for Capital
Deployment as its own explicit, named dependency — a candidate future
companion specification, not invented or resolved here.
