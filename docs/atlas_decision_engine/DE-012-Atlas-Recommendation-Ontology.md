# DE-012 — The Nature of Atlas Recommendation

**Working title (as given):** ADR-012 — The Nature of Recommendation
**Sprint:** Atlas Decision Engine — Sprint 3, Session 1 (Recommendation track)

**Status:** Ontology investigation only. Not yet adopted doctrine. This
document does not amend `DE-001-Recommendation-Framework.md` or
`DE-008-Direction-Selection.md` — the six directions, their evidence
patterns, the position-state bifurcation, the AND/OR asymmetry between
exposure-increasing and exposure-reducing directions, and every already-
adopted invariant in `DE-008` (§15's existence-gate-only Conviction role,
§16's layering rule, the conflict-resolution protocol) all stand
unchanged. What no existing document states outright is a compact,
first-principles account of *what a Recommendation fundamentally is* —
`DE-008` §1 comes closest ("the terminal categorical conclusion of `DE-002`'s
seven-part reasoning structure") but that is a structural definition
written to scope an implementation question, not an ontological one. This
document supplies that account, and re-tests the Outlook and Conviction
dependency questions now that both are independently settled (`DE-009`/
`DE-010`, `DE-011`). No implementation, UI, or algorithm accompanies it.

---

## 0. What This Session Confirmed Before Testing Anything

Two searches were run against the full governed corpus before any
candidate below was tested, since several of this session's questions
turn on whether a specific dependency exists anywhere in already-adopted
doctrine rather than on new reasoning:

1. **`DE-008` — the single most detailed specification of what actually
   determines Direction — never once cites Outlook.** A direct search
   confirms zero occurrences of the word "Outlook" in `DE-008`, `DE-001`,
   or `DE-003`. `DE-008` §5's own "Allowed Direction inputs" table is
   explicit and exhaustive about every input Direction is permitted to
   read; Outlook is not a candidate row that was excluded — it is simply
   never mentioned, in a document whose entire purpose is to enumerate
   inputs precisely. This is stronger evidence for Q9 than a single
   counter-example would be.
2. **`DE-006` §4 already enumerates Recommendation as one of five
   deliberately un-merged concepts** (Recommendation, Execution Guidance,
   Decision/Implementation Intent, Actual Execution, Portfolio
   Simulation), and `DE-007` §11 already ruled that Execution Guidance
   *references* Recommendation (`ExecutionGuidance.recommendationId`)
   rather than containing or being contained by it, specifically to avoid
   coupling. This is direct, already-adopted precedent this document
   relies on for Q10.

---

## Primary Question, Answered Directly

**What does Atlas Recommendation express?**

> **An Atlas Recommendation is Atlas's own terminal conclusion about
> which of six mutually exclusive orientations — toward one specific
> position, for one specific Investor's current portfolio situation —
> the currently available evidence supports. It is a conclusion, never an
> action and never a Decision; it is scoped to a specific Investor's
> holding state and Portfolio Context, never to the company in the
> abstract; and it is one of several independently-derived synthesis
> objects that share Business Evaluation and Valuation as common
> ancestors, never a link in a mandatory causal chain running through
> Outlook.**

Each clause is defended, not asserted, in §§1–10 below.

---

## 1. Is Recommendation an Action, a Conclusion, or a Decision?

**Test "action."** `DE-001` §1 states Recommendation is "not a Decision"
and is explicitly not any of the Investor's own recorded action-shaped
fields; `DE-008` §1 states Direction "is not... An order — no order type,
quantity, or routing information," and is not Execution Guidance ("`DE-006`
§1 answers *how* a direction could be carried out; Direction answers
*what* the direction is"). Even Execution Guidance, one layer further
toward action than Recommendation, is itself barred from action content
(`DE-006` §3: no broker orders, no exact prices, no exact dates). If the
layer explicitly closer to action still carries no action content,
Recommendation — one layer further from it — certainly does not.
**Rejected.**

**Test "decision."** `DE-001` §1, citing `APP-000` §5 and PP-003/PP-005
directly: "only the Investor makes a Decision. An Atlas Recommendation is
advice offered for the Investor's scrutiny; accepting or acting on it does
not transfer authorship of the resulting Decision to Atlas." This is not a
close call — it is a direct, named prohibition against exactly this
conflation. **Rejected.**

**Test "conclusion."** `DE-008` §1's own definition: "the terminal
categorical conclusion of `DE-002`'s seven-part reasoning structure" —
"terminal" meaning it is what Reasoning (`DE-002` §2.5) arrives at, not an
input to further reasoning; "categorical" meaning one of six discrete,
named values, never a continuous score. This survives every test above
without contradiction and is the concept every other adopted document
already uses when it needs to refer to what Recommendation actually is.

**Verdict: ADOPTED — Recommendation is a conclusion, not an action and not
a Decision.** This is not a new finding so much as a confirmation, by
direct citation, of what `DE-001` §1 and `DE-008` §1 already establish
independently — but stating it as the answer to "what kind of thing is
this" rather than as a boundary rule is itself useful: it is the premise
Q6 below builds on.

---

## 2. Company or Investor? Independence from Portfolio Context?

**Test whether Recommendation could, even in principle, be computed from
company facts alone.** `DE-001` §2's own evidence patterns settle this
directly, per direction: BUY requires "Portfolio Intelligence... finds
room for the position without breaching concentration or diversification
considerations for **this Investor's specific portfolio**." ADD requires
the increase "does not push concentration beyond what **this Investor's
portfolio** can absorb." Most decisively, **TRIM's evidence pattern can be
satisfied by portfolio sizing alone**: "the position's weight has grown...
to a concentration Portfolio Intelligence flags as exceeding what
continues to be supported for this Investor — a valuation-driven or
risk-driven partial reduction, not a thesis reversal." A company whose
Business Evaluation and Valuation are entirely unchanged can still
legitimately receive TRIM, purely because one particular Investor's
position in it has grown too large. This is not a hypothetical — it is a
named, adopted evidence pattern, and it is sufficient by itself to
disprove "Recommendation belongs to the company."

**Test the reverse — could it be computed from investor situation alone,
with no company-specific evidence?** No direction's evidence pattern
supports this: BUY and ADD both require Business Evaluation and Valuation
conclusions that are entirely about the company; even TRIM's
portfolio-driven case is TRIM only because a company that is otherwise
still fine has grown oversized in this portfolio — remove the company
entirely and there is no position to trim.

**Verdict: REJECTED, both as stated.** Recommendation belongs to neither
the company alone nor the Investor alone — it is a joint function of
company-level evidence (Business Evaluation, Valuation — the same content
Outlook is built from) and Investor-specific Portfolio Context (`DE-003`'s
seven factors, applied through `DE-002` §2.4). **Recommendation can never
exist independently of Portfolio Context being evaluated** — `DE-002` §3's
structural discipline already requires this ("SHALL NOT... omit a
section's content entirely without disclosing the omission"), and `DE-003`
§4 confirms the requirement is that Portfolio Context be *evaluated and
stated* (even as an explicit null result — "no factor changed this
direction") rather than exhaustively recited. A Recommendation computed
without ever evaluating Portfolio Context is not a Recommendation with a
gap in it; it is an incomplete, unfinished one, per `DE-001` §3's
explainability checklist.

---

## 3. Can Two Investors Diverge While Outlook Is Identical?

This is §2's TRIM finding, restated as its own direct test, and the
answer follows immediately: **yes.** Take two Investors holding the same
company, whose Business Evaluation and Valuation — and therefore whose
Outlook (`DE-009` §2.6: built only from Business Evaluation and Valuation
Philosophy, never from Investment Thesis) — are identical. If Investor A
holds a small, well-sized position and Investor B holds a concentrated
one, Investor A may receive HOLD while Investor B receives TRIM, purely on
`DE-003`'s Concentration factor.

**What causes the divergence, precisely:** not the company, not Outlook
(which is identical for both by construction) — the divergence is
entirely attributable to Portfolio Context (`DE-002` §2.4, `DE-003`'s seven
factors) and/or position-state (`DE-008` §3's held/not-held bifurcation),
the two categories of input Recommendation consumes that Outlook
structurally does not. This is the cleanest possible demonstration that
Recommendation's input set is strictly wider than Outlook's — not a
different selection from the same set, but a genuinely larger set with
extra members.

---

## 4. Dependency Direction: What Is Recommendation Actually Derived From?

Testing the user's candidate list against `DE-008`'s own "Allowed
Direction inputs" table (§5) rather than reasoning abstractly:

| Candidate | Included? | Basis |
|---|---|---|
| Business Evaluation | **Yes** | `DE-008` §5: "Determines thesis integrity; central to every direction" |
| Valuation | **Yes, scoped** | Valuation *Evidence* (`ValuationStatus`), not the not-yet-computable Valuation Support for Capital Deployment (`DE-008` §10.1) |
| Outlook | **No** | Never cited anywhere in `DE-008`'s exhaustive input enumeration (§0 above) |
| Conviction | **Yes, narrowly** | "Existence-gate + attached label, never a selector" (`DE-008` §5, §15) |
| Portfolio Context / Portfolio Intelligence | **Yes, narrowly** | Allocation and Concentration, dampening-only (`DE-008` §12) |
| Reasoning (Evidence/Counter-Evidence/Open Questions) | **Yes** | `DE-008` §5 |
| Risk (Financial/Valuation only) | **Yes** | Thesis/Business Risk excluded as double-counting (`DE-008` §13) |
| Decision Memory (Thesis Synthesis, narrowly) | **Yes** | Distinguishes ADD/TRIM-worthy states; prior execution price and investor Confidence excluded (anchoring risk) |
| Current holding-state (`HoldingLinkage`) | **Yes** | The position-state partition itself (`DE-008` §3) |

**Verdict: ADOPTED — Recommendation is derived from Business Evaluation,
Valuation Evidence, Portfolio Intelligence (dampening-only), Reasoning
content, Financial/Valuation Risk, a narrow slice of Decision Memory, and
current holding-state — gated, not shaped, by Conviction's assessability
— and is explicitly NOT derived from Outlook.** This is not a new
conclusion; it is `DE-008`'s already-adopted input list, read for what it
omits as much as what it includes, and confirms rather than merely repeats
`DE-009` §8's finding.

---

## 5. Can Recommendation Change While Outlook Stays Fixed?

**Test the user's example directly.** Concentration increases; the
company remains equally attractive (Business Evaluation and Valuation, and
therefore Outlook, unchanged). `DE-008` §10.2 states the governing
asymmetry outright: *"reducing exposure can be triggered by Business OR
Valuation Evidence OR Portfolio Context alone."* Portfolio Context alone
is sufficient — this is not an edge case the existing doctrine leaves
ambiguous, it is a named, adopted rule, and it is the same TRIM pattern
§2 and §3 already relied on.

**Verdict: YES, decisively — and this is not a defect to reconcile, it is
the direct, expected consequence of §2's finding that Portfolio Context is
a mandatory Recommendation input Outlook does not share.** A model in
which Recommendation could *not* change under this scenario would
contradict `DE-003` §1's own foundational principle, "Portfolio before
position" — Atlas would be evaluating the company in isolation from the
portfolio it belongs to, the exact failure mode `DE-003` exists to
prevent.

---

## 6. Should Recommendation Always Exist? Recommendation Withheld, From First Principles

**Derive the necessity, rather than citing the existing rule as given.**
§1 adopted Recommendation as a *conclusion* — specifically, an honest
report of which of six orientations the currently available evidence
supports. A conclusion, by the nature of what a conclusion is, can only be
validly stated when the premises actually support it. If Atlas were
required to always select one of the six directions regardless of
evidentiary sufficiency, "conclusion" would stop meaning what §1 just
established it means — it would become a forced categorical output,
indistinguishable in kind from an action or a guess dressed as a
conclusion. `APP-000` PP-007 — "SHALL NOT present a conclusion with
greater confidence than its underlying Evidence and Reasoning support" —
is the direct, already-adopted statement of exactly this requirement.

**Test whether any of the six directions could silently absorb the
insufficient-evidence case instead of requiring a seventh path.** No — NO
ACTION already carries its own positive evidentiary requirement ("evidence
was sufficient to reach that conclusion honestly," `DE-008` §2); it is not
a null or default value, and using it to paper over insufficient evidence
would misrepresent an absence of conclusion as a reached one. The same
applies to HOLD (`DE-001` §2: "Hold is not silence — it is an explicit
statement that the evidence was reviewed"). Forcing either to stand in for
insufficiency would violate the same PP-007 principle this section
already invoked.

**Verdict: ADOPTED — Recommendation Withheld is not a workaround feature,
it is the logically necessary complement of defining Recommendation as an
honest conclusion (§1).** Any concept that claims to report what the
evidence supports must have a valid non-answer available for when the
evidence supports nothing — otherwise it is not reporting the evidence, it
is reporting a forced output that merely resembles one. This is a
first-principles derivation of what `DE-004` §4 and `DE-001` §2 already
specify operationally (why it is "not an error state and not a
placeholder," why it "SHALL NOT default to Hold or No Action"); this
document does not alter any of `DE-008` §19's six specific triggering
classes, which remain the authoritative operational account.

---

## 7. Recommendation Stability: What Should Legitimately Cause Revision?

**Apply the same discipline already adopted for Outlook (`DE-009` §7,
`DE-010` §7) and Conviction (`DE-011` §7): revision should be event-driven,
tied to named, checkable conditions (`DE-002` §2.7), never routine or
reactive to every minor fluctuation.** Since §1 establishes Recommendation
as the terminal conclusion of Reasoning, it should change exactly when the
reasoning supporting it changes — never on a fixed schedule.

**One genuine addition this section makes, not present in the Outlook or
Conviction versions of this question.** Because §2 and §4 establish
Portfolio Context as a Recommendation-specific input that Outlook does not
share, Recommendation has a **second, independent category of legitimate
revision trigger that Outlook structurally cannot have**: a portfolio-state
condition — most concretely, Concentration crossing a stated threshold —
can itself be exactly the kind of "specific, named condition" `DE-002`
§2.7 requires ("a metric crossing a stated threshold... never a vague
hedge"), even where the metric is sourced from portfolio state rather
than company evidence. A position's weight drifting upward purely because
its price rose, with zero new evidence about the company, is a legitimate
trigger for re-evaluating Recommendation (§5's TRIM case) even though it
is not a legitimate trigger for revising Outlook at all (`DE-009` §7:
company-evidence only).

**What should not trigger revision**, tested against `DE-008`'s own
explicit exclusions: routine time passing with no named condition met;
raw price movement that crosses no stated Concentration or Valuation
Evidence threshold; anything `DE-008` §16 already excludes as a layering
violation (`HistoricalRecommendationSnapshot`/`RecommendationResponse`);
execution-shaped content or reconciliation status (`DE-008` §17, "a
workflow fact, not analytical").

**Verdict: ADOPTED — Recommendation is event-driven like Outlook and
Conviction, but its set of legitimate triggers is strictly wider, because
it inherits company-evidence triggers from the same shared ancestors
Outlook has (Business Evaluation, Valuation) and additionally has
portfolio-state triggers Outlook cannot have.** This mirrors, structurally,
the same asymmetry §2–§5 already established for inputs — a wider input
set produces a wider trigger set, not a coincidence but a direct
consequence.

---

## 8. Ownership: Investment Opportunity, or Investor's Situation?

**Test by holding one side fixed at a time**, the same method §3 already
used. Hold the Investor's portfolio situation fixed and vary only company
facts: Recommendation changes (a Business Evaluation reversal moves BUY
toward EXIT territory, `DE-001` §2). Hold company facts fixed and vary
only the Investor's portfolio situation: Recommendation changes (§5's
concentration case). **Neither side, held fixed, makes Recommendation
constant** — which is only possible if Recommendation is not reducible to
either side alone.

**A sharper framing than "which side wins."** A property that genuinely
requires two independent inputs to compute, and cannot be correctly
computed from either one alone, is not a property *of* either input taken
individually — it is a property of the **relationship** between them.
`DE-001` §2 already writes every direction this way without stating the
principle explicitly: "a business the Investor does not currently hold"
(BUY), "increasing an existing position" (ADD) — every definition is
phrased relative to a specific Investor's specific holding state, never in
terms of the company considered in the abstract.

**Verdict: REJECTED, both as stated — ADOPTED instead: Recommendation is a
property of the relationship between one investment opportunity and one
specific Investor's current portfolio situation** (concretely: the Case,
scoped to that Investor's holding state and Portfolio Context) **— never
reducible to the company alone or the Investor's situation alone.** This
is consistent with, and gives the general principle behind, `DE-005`'s
already-adopted scoping of Investment Thesis to "a position," not to a
company considered abstractly.

---

## 9. Re-Testing the Outlook/Recommendation Dependency

`DE-009` §8 already tested and rejected a mandatory dependency in either
direction, using the Trim counter-example. This session re-tests the same
question with the benefit of `DE-008`'s full, subsequently-written
specification, which provides stronger evidence than was available when
`DE-009` was written.

**Can Recommendation exist without Outlook?** Yes — `DE-008` fully
specifies Direction Selection's decision rule, across twenty sections and
an exhaustive input table, without citing Outlook once (§0 above). This is
not merely "no counter-example was found" — it is a complete, independently
governing specification that had every opportunity to require Outlook and
never did.

**Can Outlook exist without Recommendation?** Yes, unchanged from `DE-009`
§8 — Outlook survives Recommendation Withheld, continuing to state
Business Evaluation and Valuation content even when no Direction is
selected at all.

**A sharper structural account than "siblings," now that both sides are
independently confirmed.** Outlook and Recommendation are not merely
uncorrelated concepts that happen to coexist — they are both independently
derived from the same upstream content, **Business Evaluation and
Valuation Philosophy** (`DE-009` §2.6 for Outlook; §4 above for
Recommendation). This shared ancestry is *why* they usually move together
in practice — a Business Evaluation reversal will typically shift both at
once — without either one structurally requiring or computing the other.
Recommendation additionally depends on Portfolio Intelligence, which
Outlook structurally excludes (`DE-009` §7 restricts Outlook to
company-evidence triggers only) — this is precisely the extra parent that
makes §5's divergence case possible: two objects with mostly-shared
ancestry will usually agree, but will diverge exactly where one of them
has an input the other does not.

**Verdict: RE-CONFIRMED, and sharpened.** Not "siblings" in the weak sense
of "unrelated but coexisting" — **shared-ancestor, independently-computed
objects**, correlated through common inputs (Business Evaluation,
Valuation) but never dependent on one another, and predictably divergent
exactly at Recommendation's one extra input, Portfolio Intelligence.

---

## 10. Should Recommendation Become the Canonical Object?

**The question conflates two different claims, and they test differently.**

**Claim A: Recommendation's Direction+Conviction pairing should be
computed once and read identically by every consuming surface** (Portfolio,
Watchlist, Daily Brief, Companion, Notifications), rather than each surface
independently recomputing or restating it. **Test against precedent:**
`DE-003` §1 already states this exact requirement, generalized: *"Portfolio
SHALL NOT create an independent priority or ranking model separate from
the Atlas Priority Model"* — a direct application of `APS-006` `PFINV-004`
(Single Priority Model). This is the identical precedent `DE-010` §5 and
§6 already used to adopt a shared Representation Layer for Outlook, for
the identical reason: divergent per-surface computation of the same
underlying judgment is not a display inconsistency, it is proof the
"one Recommendation" claim was never actually true in the running system
(the same conceptual-integrity argument `DE-010` §6 made for Outlook
applies here without modification). **Verdict: ADOPTED.**

**Claim B: Recommendation should become a mandatory upstream stage that
Execution Guidance, Outlook, and other objects derive their own content
from, folding what are currently separate objects into one canonical
pipeline node.** **Test directly against already-adopted doctrine, not
analogy:** `DE-006` §4 explicitly enumerates Recommendation as one of five
concepts that "SHALL NOT be merged" into one another. `DE-007` §11 already
ruled, and justified, that Execution Guidance *references*
`ExecutionGuidance.recommendationId` rather than containing or being
contained by Recommendation, specifically "to avoid coupling two documents
your instructions explicitly require to stay separated." Folding Execution
Guidance's content into a canonical Recommendation object directly
contradicts this already-adopted, deliberately justified separation. And
§9 just re-confirmed Outlook has no dependency on Recommendation at all —
there is nothing for it to derive. **Verdict: REJECTED.**

**Synthesis.** These two verdicts are not in tension — they answer
different questions, the same way `DE-010` §5 distinguished "a shared
transformation step" (adopted) from "a new ontological layer" (rejected),
and `DE-011` §10 distinguished "a permanently governed concept" (already
settled) from "a single-computation chain stage" (rejected). Here:
**Recommendation SHALL be canonical at the distribution level** — one
computed Direction+Conviction pairing, read identically everywhere it
appears — **while remaining one of several independently-derived,
never-merged synthesis objects at the ontological level** — Outlook,
Recommendation, and Execution Guidance stay three distinct things, related
by shared ancestry (§9) and explicit reference (`DE-006` §4) rather than
by containment or a mandatory pipeline.

---

## 11. Adopted Ontology of Atlas Recommendation

> **An Atlas Recommendation is Atlas's terminal, categorical conclusion —
> one of six mutually exclusive directions, or Recommendation Withheld in
> their place — about which orientation toward a specific position the
> currently available evidence supports, for one specific Investor's
> current portfolio situation. It is a conclusion, never an action and
> never a Decision (§1); it is a property of the relationship between the
> investment opportunity and the Investor's holding state, never of
> either alone (§2, §8), and cannot exist without Portfolio Context having
> been evaluated (§2); it is derived from Business Evaluation, Valuation
> Evidence, Portfolio Intelligence, Reasoning, Financial/Valuation Risk,
> a narrow slice of Decision Memory, and current holding-state — gated,
> never shaped, by Conviction — and explicitly not derived from Outlook
> (§4); it changes exactly when a named, checkable condition changes,
> drawing on both company-evidence triggers and portfolio-state triggers,
> the latter being a category of revision Outlook structurally cannot
> have (§5, §7); it is one of several independently-computed objects that
> share Business Evaluation and Valuation as common ancestors with
> Outlook, correlated through that shared ancestry without either
> depending on the other (§9); and it is canonical at the distribution
> level — one shared computation every surface reads identically — while
> remaining ontologically distinct from, and never merged with, Outlook
> or Execution Guidance (§10).**

This adopts and gives a first-principles account of what `DE-001` and
`DE-008` already specify operationally; it changes none of their content.

---

## 12. Rejected Alternatives (Summary)

| Candidate | Verdict | Reason |
|---|---|---|
| Recommendation as an action | Rejected | No execution content at any layer; even Execution Guidance, closer to action, carries none (§1) |
| Recommendation as a Decision | Rejected | `DE-001` §1, `APP-000` §5/PP-003/PP-005: authorship never transfers to Atlas (§1) |
| Recommendation as a property of the company alone | Rejected | TRIM's evidence pattern is satisfiable by portfolio sizing alone, no company change required (§2, §3) |
| Recommendation as a property of the Investor's situation alone | Rejected | No direction's evidence pattern is satisfiable without company-level Business/Valuation content (§2) |
| Recommendation computable without evaluating Portfolio Context | Rejected | `DE-002` §3's structural discipline; an unevaluated Portfolio Context makes the Recommendation incomplete, not merely minimal (§2) |
| Recommendation strictly derived from/through Outlook | Rejected | `DE-008`'s full, exhaustive input specification never cites Outlook (§4, §9) |
| Recommendation immune to portfolio-only changes when the company is unchanged | Rejected | `DE-008` §10.2: reducing exposure can be triggered by Portfolio Context alone (§5) |
| A seventh direction absorbing the insufficient-evidence case (no Recommendation Withheld) | Rejected | Violates `APP-000` PP-007 and undermines "conclusion" as adopted in §1 (§6) |
| Recommendation revision on a routine or fixed schedule | Rejected | No evidentiary or portfolio-state change occurs on a calendar (§7) |
| Recommendation as a property of the investment opportunity or the Investor's situation, taken singly | Rejected | Neither, held fixed, makes Recommendation constant (§8) |
| Outlook and Recommendation as merely "unrelated siblings" | Rejected, refined | Shared-ancestor, independently-computed objects — correlated through Business Evaluation/Valuation, not merely coincidentally coexisting (§9) |
| Recommendation as a mandatory pipeline stage feeding Execution Guidance or Outlook | Rejected | Directly contradicts `DE-006` §4's five-concept non-merger rule and `DE-007` §11's referenced-never-contained ruling (§10) |
| Recommendation as one of several *independently computed* per-surface objects | Rejected | Contradicts the Single Priority Model precedent (`DE-003` §1, `APS-006` `PFINV-004`) (§10) |

---

## 13. Dependency Relationships

- **Recommendation → requires → Portfolio Context having been evaluated.**
  Mandatory, `DE-002` §2.4/§3; may be a stated null result, never silently
  absent (§2).
- **Recommendation → requires → Conviction being assessable (existence
  gate only).** Never shaped by Conviction's level, only gated by its
  successful assessment (`DE-008` §15, §19; `DE-011` §10, unchanged here).
- **Recommendation ↔ Outlook: no dependency in either direction.** Both
  independently derived from the same Business Evaluation + Valuation
  ancestry; correlated, not coupled (§9).
- **Recommendation → referenced by, never containing or contained by →
  Execution Guidance.** `ExecutionGuidance.recommendationId` (`DE-006` §4,
  `DE-007` §11) — a genuine, adopted dependency, but a reference, not a
  merger (§10).
- **Recommendation's Direction → does not depend on → Investor Decision or
  Implementation Intent.** `DE-008` §16: reading those back into Direction
  Selection would be a layering violation (staleness/anchoring).
- **Recommendation's distribution (the single computed value) → governs →
  every consuming surface.** Portfolio, Watchlist, Daily Brief, Companion,
  and Notifications read one canonical computation; none computes its own
  (§10, by direct extension of `DE-003` §1's Single Priority Model
  citation).

---

## 14. Open Questions

1. **Does Companion's tool-triggered Case creation (per the separately
   adopted Atlas Companion architecture) ever need to read a Recommendation
   before a Case exists at all?** This document assumes a Recommendation
   is scoped to an existing Case/holding-state pairing (§8); the bootstrap
   case — first contact with a brand-new company, no Case yet — was not
   tested here and may need its own short treatment.
2. **§7 adopts portfolio-state triggers (e.g., a Concentration threshold)
   as legitimate Recommendation-revision events, alongside company-evidence
   triggers — but does not define how the two interact when both change at
   once** (e.g., Business Evaluation weakens in the same window
   Concentration crosses a threshold). Whether these compose, or whether
   one should be evaluated first, is left to `DE-008`'s existing
   conflict-resolution protocol (§18) to answer, since this document does
   not revisit that ordering.
3. **§10's "canonical at the distribution level" finding was derived here
   by direct extension of `DE-003` §1's Single Priority Model citation to
   Recommendation specifically — but `DE-003` §1 was written about
   priority/ranking, not about Direction+Conviction content itself.**
   Whether this extension needs its own explicit doctrinal statement
   (rather than resting on this document's own reasoning) is worth a
   follow-up if a future implementation-facing specification needs firmer
   footing than an ADR provides.
4. **Naming audit, again**, following the same pattern flagged in every
   prior ADR in this series: this document introduces no new user-facing
   term, but "shared-ancestor objects" (§9) has not been checked against
   the corpus's naming-collision discipline, though it is offered only as
   descriptive framing, not as a term intended for reuse elsewhere.

---

## 15. Implications for the Remaining Atlas Decision Engine

- **`DE-001` and `DE-008` are unchanged.** This document supplies the
  compact ontological account neither fully states, and resolves two
  places their language was closer to implicit than explicit: the
  company/Investor ownership question (§2, §8, now stated as relationship-
  scoped rather than left to be inferred from each direction's individual
  wording) and the precise shape of the Outlook/Recommendation relationship
  (§9, now "shared-ancestor" rather than bare "siblings").
- **`DE-008`'s own silence on Outlook turns out to be this document's
  strongest single piece of evidence** (§0, §4, §9) — a fully-specified,
  independently-governing document that never needed a concept is stronger
  proof of non-dependency than any single counter-example, the same way
  `DE-006` §5 and `DE-008` §15 together were the strongest evidence in
  `DE-011`'s Conviction investigation.
- **`DE-006` and `DE-007` are unaffected, and one finding is strengthened**:
  `DE-007` §11's "referenced, never contained" ruling for Execution
  Guidance is now backed by this document's independent derivation (§10)
  of why Recommendation cannot become a merged canonical pipeline stage,
  not merely by the original coupling-avoidance rationale.
- **`DE-003` §1's Single Priority Model citation is now doing double duty**
  — originally scoped to priority/ranking, it has been directly extended
  here (§10, flagged as Open Question 3) to license Recommendation's own
  canonical-distribution requirement, the same way `DE-010` §5 already
  extended it once for Outlook's Representation Layer. A future
  specification collecting all three extensions (Outlook, Conviction by
  implication, Recommendation) under one explicit "single-computation,
  many-readers" rule may be worth writing, rather than leaving the
  precedent to be independently re-derived by each ADR in this series.
- **A future companion specification is implied for Q1's open item**
  (bootstrap Case creation) and for formalizing the distribution-layer
  rule this document and `DE-010` have now both independently arrived at
  — neither is started here.
