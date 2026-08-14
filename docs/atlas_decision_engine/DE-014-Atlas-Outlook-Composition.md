# DE-014 — The Composition of Atlas Outlook

**Working title (as given):** ADR-014 — The Composition of Atlas Outlook
**Sprint:** Atlas Decision Engine — Sprint 3, Session 2 (Outlook Composition track)

**Status:** Ontology investigation only. Not yet adopted doctrine. This
document does not redesign `DE-009` (Outlook Ontology), `DE-010` (Outlook
Representation), or `DE-012` (Recommendation Ontology) — it closes the one
specific gap `DE-013` §Part 3 (scenarios 1, 5, 8) and §Part 7 identified in
all three: `DE-009` §2.6 adopts Outlook as a synthesis of "durability,
evidence quality, and valuation attractiveness" without ever specifying how
those dimensions combine into one statement when they point in different
directions. No implementation, formula, or UI accompanies this document.
Where a scoring mechanism might seem tempting, this document tests it and,
in every case, finds it unnecessary — consistent with the explicit
instruction that scoring is adopted only if it becomes logically
unavoidable, and it never does.

---

## 0. Grounding: This Corpus Has Answered This Exact Question Before

Before testing any candidate, it is worth naming a pattern this document
did not invent: **every prior time this corpus faced "should Atlas collapse
multiple real things into one simpler thing," it said no**, and did so for
reasons that generalize directly to this session's question:

- **Business Evaluation** (`Doctrine` §4): *"deliberately does not include a
  scoring mechanism, a single 'quality score,' or a ranking... a single
  number cannot carry the explanation a business evaluation requires...
  Atlas names the specific durability and evidence considerations that
  produced it, not a composite figure."* This is the single most direct
  precedent available: Business Evaluation is itself already multi-
  dimensional (Durability, Evidence Quality, Knowable-vs-Assumed) and
  already refuses to collapse those dimensions into one score — for the
  same reason, stated in advance, that this session is being asked to
  re-derive for Outlook.
- **Valuation** (`Doctrine` §5.1): *"Ranges, never points"* — a range is
  strictly more information than a point, adopted specifically because the
  point would be false, not because more detail is inherently better.
- **Bull/Base/Bear** (`DE-009` §5): probability-weighted averaging was
  rejected specifically because *"multiplying through produces an implied
  single expected value — reintroducing the already-forbidden Expected
  Return... through a side door."*
- **Conviction and Direction** (`DE-004` §6): *"SHALL always be stated
  together... and SHALL NOT be collapsed into a single combined signal that
  obscures which one a reader is looking at."*

**This session's question is the same question, asked one more time, one
level up.** The default expectation, before testing a single candidate,
should be that the answer generalizes — and the burden of this
investigation is to find a genuine reason Outlook's case is different, not
to assume it is.

---

## Primary Question, Answered Directly

**When the underlying analytical dimensions disagree, what does Atlas
Outlook express?**

> **Outlook expresses the actual, named state of each analytical dimension
> that bears on it, and their individual trajectories — never a single
> collapsed label that resolves disagreement the evidence itself has not
> resolved.** Where dimensions diverge, that divergence is not a failure
> Outlook must smooth over; it is the most important thing Outlook has to
> say, and smoothing it away would misrepresent the actual state of Atlas's
> understanding.

Every clause below is tested, not asserted.

---

## 1. Should Outlook Collapse Into a Single Direction (Positive / Neutral / Negative)?

**Test against `APP-000` PP-007 directly**, since this is the sharpest
available test: *"SHALL NOT present a conclusion with greater confidence
than its underlying Evidence and Reasoning support."* When Durability is
improving and Valuation attractiveness is deteriorating, "Positive" and
"Negative" are both **more resolved** claims than the underlying evidence
actually supports — the truthful state is "mixed," and neither pole is
honest. Note the asymmetry this test produces: a P/N/N label is not
*always* false — where all dimensions genuinely agree, "Positive" is a
truthful compression, not a lie. But a composition model that only behaves
correctly when the dimensions happen to agree is not answering the question
this session was asked, which is specifically about the disagreement case.

**Test whether a P/N/N label is independently explainable**, per
`ATLAS_CONSTITUTION.md`'s Non-Negotiable Principle, "Every Atlas Rating must
be explainable." A P/N/N label attached to genuinely divergent dimensions
cannot be explained by itself — explaining it requires secretly re-deriving
whatever weighting turned "durability up, valuation down" into one word, and
that weighting is exactly the kind of unstated formula `DE-013` Finding 1.4
already flagged as a live risk this corpus has not protected against.

**Verdict: REJECTED as Outlook's primary, authored content.** A P/N/N-style
label may survive only as a narrow, secondary, **representation-layer**
convenience (see §11, Implications for Representation), shown only in the
degenerate case where the named dimensions genuinely agree — never as
something Outlook itself states or that a Representation Layer manufactures
by resolving genuine disagreement on Outlook's behalf.

---

## 2. Should Outlook Preserve Analytical Tension Instead?

**Test against `DE-009` §2.6's own adopted definition**, which already
permits *"a small number of named, internally coherent conditions"* —
plural, named. This session's proposal is not a new shape; it is `DE-009`
§2.6 read completely, rather than only for its Bull/Base/Bear application.

**Test against "smallest model capable of expressing reality,"** the
standard this whole corpus repeatedly applies. Preserving named dimensions
is not a violation of parsimony — it is what parsimony actually requires
here, by the same logic §0's Valuation-range precedent already established:
a range is "more" than a point only in the sense that it is *true*, and the
point would not be. Collapsing real, independently-supported divergence
into one label is not simpler — it is a different, false claim wearing a
simpler shape.

**Verdict: ADOPTED.** Outlook preserves analytical tension by naming each
dimension's own trajectory rather than forcing a composite.

---

## 3. What Should Outlook Represent: Average, Strongest Driver, Dominant Driver, Limiting Factor, or Complete Analytical State?

**Average — tested and rejected.** Averaging "Business Quality improving"
against "Valuation deteriorating" requires an exchange rate between two
things that are not even the same unit — a category error, and a
manufactured one, of exactly the unstated-formula kind `DE-013` warned
about. Worse: an average of a strong positive and a strong negative can
land on "neutral," which describes **neither** underlying dimension
accurately — this is not a compromise, it is a third, new falsehood.

**Strongest driver — tested and rejected.** "Strongest" is ambiguous
between "most confidently evidenced" (highest Conviction) and "largest
magnitude of expected change." Read either way, this candidate silently
discards whichever dimension loses, which directly violates `DE-002` §2.3's
already-adopted Counter-Evidence discipline: *"Counter-Evidence SHALL be
genuine and specific... never omitted because it complicates the
conclusion."* A deteriorating dimension dropped from Outlook because a
different dimension happens to be better-evidenced is exactly this failure
mode, one level up from where `DE-002` §2.3 already forbids it.

**Dominant driver — tested and rejected as a standing rule; see §7 for the
full test.** No dimension earns permanent priority over the others; what
looks like dominance in extreme cases has a different, non-hierarchical
explanation (§7).

**Limiting factor — tested and rejected, but for a different reason than
the above: it already exists, correctly, elsewhere.** "The weakest link
constrains the whole" is a real, legitimate composition rule — but it is
already `DE-008` §10.2's own adopted logic for Direction Selection ("initiating
or adding exposure requires Business AND Valuation Support for Capital
Deployment both positive; reducing exposure can be triggered by Business OR
Valuation Evidence OR Portfolio Context alone"). Adopting limiting-factor
logic for Outlook as well would duplicate Recommendation's own
action-oriented compositional machinery inside an understanding-oriented
object, directly blurring the distinction `DE-012` §9 established at real
cost: Outlook and Recommendation are shared-ancestor, independently-
computed objects, never a chain. Limiting-factor reasoning belongs to
Recommendation because Recommendation is the object that has to resolve
divergence into one of six actions; Outlook does not have to resolve
anything, by §1 and §2's verdicts above.

**Complete analytical state — survives.** This is §2's adopted answer,
formalized as the winning candidate: Outlook represents the actual current
state of each dimension that bears on it, named specifically, using the
already-adopted Drivers pointer mechanism (`DE-009` §6) so that "complete"
never means "an unbounded raw dump" — it means faithful to what the
evidence actually shows, structured the same way `DE-009` §6 already
structures everything else Outlook points to.

---

## 4. Six Scenarios

**A. Outstanding business, terrible valuation.** Outlook states both,
named: business trajectory strong and improving (Durability, Evidence
Quality); valuation trajectory unattractive, with the specific named reason
(e.g., price has moved outside the historically-supported range). No forced
single word. This is `DE-013`'s original gap scenario, now resolved.

**B. Weak business, exceptional valuation.** The mirror image of A, handled
by the identical mechanism: business trajectory weak, with the specific
named durability concern; valuation attractive, with its own named basis.
**Symmetry check, deliberately performed**: a composition model that only
worked for "good business, bad price" and broke or needed a different
mechanism for "bad business, good price" would itself be a hidden,
undocumented bias. It does not — both scenarios use the same two-slot,
named-dimension statement.

**C. Growth slowing, margins expanding.** Unlike A and B, this is tension
**within** Business Evaluation, not across dimensions. Test whether a
different mechanism is needed here: no — Business Evaluation already
refuses internal scoring (§0's own first precedent), so this tension is
already correctly preserved one level down, and Outlook inherits it
unmodified through the existing Drivers pointer (`DE-009` §6). The
composition model adopted here is recursive: the same "name it, do not
collapse it" discipline applies at whatever level tension actually appears,
and requires no special case for "intra-dimension" versus "inter-dimension"
divergence.

**D. Increasing competitive moat, declining capital allocation.** Same
resolution as C — both are Business-Evaluation-internal sub-findings,
already non-collapsed at their source, inherited as-is.

**E. Higher expected return, lower conviction.** Tested carefully, because
this scenario is a category check, not a composition question: Expected
Return is `DE-010` §2's derived, secondary **representation**, never
Outlook's own authored content; Conviction is `DE-011`'s independent rating
that *accompanies* Outlook (`DE-009` §9), never one of the dimensions
composed *into* it. Neither is a dimension this ADR's composition problem
governs. Higher Expected Return with Lower Conviction is already fully
coherent under `DE-011` §3's adopted orthogonality finding (a thin, exciting
case is exactly a wide-range, low-conviction pairing) — nothing new is
required to resolve it. This scenario confirms the composition model
correctly excludes non-dimensions rather than accidentally swallowing them.

**F. Short-term deterioration, long-term strengthening.** Tested against
`DE-009` §3 (no coequal Short-Term Outlook) and `DE-010` §1 (Short-Term View
as a date-filtered subset of Outlook's own Drivers). This is not a new kind
of tension requiring a new mechanism — it is temporal tension among the
same named Drivers this document already governs, expressible as a
near-dated Driver and a structural Driver stated side by side, exactly the
content `DE-010` §1's existing Short-Term View representation already
filters by date. **This scenario is already resolved by composing this
document's model with `DE-010` §1's existing one — a validating case, not a
gap.**

---

## 5. Should Outlook Ever Contain Internal Disagreement — Failure or Purpose?

**A precision worth making before answering**, since the word
"disagreement" risks a category slip: dimensions do not "disagree" in the
sense that two pieces of evidence contradict each other's facts — that
would be an actual data problem, already governed within a single
dimension by `DE-002` §2.2/§2.3's Evidence/Counter-Evidence discipline.
What this document calls "disagreement" is **divergence in direction of
travel across dimensions that are each independently, individually
well-supported** — Durability can be genuinely, honestly improving at the
same moment Valuation is genuinely, honestly deteriorating; nothing about
either claim is in doubt on its own.

**Given §§1–4's findings, the answer follows directly.** Smoothing this
divergence away would violate `APP-000` PP-007 (false resolution) and
`DE-002` §2.3's Counter-Evidence discipline (omitting what complicates the
picture). **Verdict: ADOPTED — internal divergence, properly understood as
cross-dimensional rather than factual contradiction, is not a failure state.
Preserving it honestly is part of Outlook's purpose, not an defect to be
engineered away.**

---

## 6. One Synthesized Statement or Multiple Orthogonal Statements?

**Test the proposed split — Business Outlook, Investment Outlook, Capital
Allocation Outlook, Valuation Outlook — against `DE-009` §3's already-
adopted finding directly.** `DE-009` §3 rejected a coequal Short-Term
Outlook alongside a Long-Term Outlook specifically because multiplying
"Outlook" objects, sliced any way, either duplicates content that already
has a home elsewhere or is so thin it adds nothing beyond a relabeled
restatement. The same test applies here, sliced by dimension instead of by
time: a standalone "Capital Allocation Outlook" either duplicates Business
Evaluation's existing Capital Allocation sub-finding (violating `DE-009`
§6's rejection of Outlook owning a duplicate store) or contributes nothing
beyond an "Outlook" label glued onto content that already exists under its
own name.

**Test against `DE-013` Finding 1.2**, which diagnosed exactly this failure
already happening once, by accident: `DE-002`'s bundling of a shared
evidentiary core with Recommendation-specific content under one name was
found to be a genuine naming/proliferation problem. Splitting Outlook into
four separately-branded objects would manufacture the identical problem
deliberately, one document later.

**Verdict: REJECTED — one Outlook object, not multiple named Outlooks.**
This is not the same conclusion as §1's rejection of collapsing: §2 and §3
already establish that the **single** Outlook object internally names
multiple dimensions without forcing them into one label. The three
positions are now fully distinguished: one collapsed signal (§1, rejected);
many separately-branded Outlook objects (this section, rejected); one
object, multiple named dimensions, no forced label (§2–§3, adopted).

---

## 7. Does Outlook Have a Dominant Dimension?

**Test the strongest available counter-example: fraud discovery**, which
`DE-013` Part 3 scenario 4 already found moves Recommendation decisively to
EXIT "regardless of valuation attractiveness" (`DE-001` §2's Business
Evaluation reversal criterion). Does this prove Business Quality dominates
Valuation as a standing rule inside Outlook itself?

**Tested and rejected, for a precise reason.** `DE-001` §2's Exit criterion
is Recommendation's own decision logic — an action-oriented rule, per
`DE-012` §9's already-adopted finding that Recommendation's compositional
machinery is its own, never inherited by Outlook. It is not evidence that
Outlook itself should silence its Valuation dimension whenever Business
Evaluation reverses.

**A better explanation, using only already-adopted material.** Fraud
discovery is not fundamentally a Business Quality event — it is an
**Evidence Quality** event: the prior evidence base is now known to be
unreliable. Evidence Quality is already one of `DE-009` §2.6's three named
dimensions, and a collapse in evidence reliability degrades confidence in
**every** dimension built on that evidence simultaneously — Valuation's own
inputs are just as compromised as Durability's. What looks like one
dimension overriding the others in an extreme case is better explained as
**a shared cause degrading multiple dimensions at once**, not as one
dimension holding structural priority over the rest. This requires no new
machinery beyond `DE-009`'s existing three dimensions.

**Verdict: REJECTED, with an explanation rather than a bare rejection.** No
dimension has standing priority. Extreme-case "dominance" is Evidence
Quality collapsing broadly, a correlation with a shared cause, never a
hierarchy. Any apparent override at the Recommendation level (EXIT
regardless of valuation) is Recommendation's own machinery, not proof of an
internal Outlook hierarchy.

---

## 8. Should Outlook Be Fundamentally Qualitative?

**Test the two example forms directly against `APP-002` §6**, which already
governs every Atlas output's register: *"Atlas never issues instructions.
It states what the evidence currently supports."* "The long-term investment
thesis continues to strengthen despite short-term valuation pressure" is
specific, attributed, and matches this register exactly. "Overall Outlook:
Positive" is a bare categorical label with no attribution at all — it does
not merely risk violating `APP-002` §6, it structurally cannot satisfy it,
since there is nothing in a two-word label for "attribution" to attach to.

**Verdict: ADOPTED — Outlook's primary form is qualitative: a structured
statement naming its dimensions and their trajectories, each attributed to
the evidence that supports it.** This is not a new requirement invented
here; it is `APP-002` §6's existing register, applied to content this
document is the first to specify precisely.

---

## 9. Should Outlook Preserve Uncertainty Instead of Resolving It?

**A distinction this document must draw precisely, to avoid a category
error of its own.** This session's example — "strong business quality, weak
valuation, improving capital allocation, moderate regulatory risk" — is not
epistemic uncertainty in `DE-011` §9's sense (a single claim honestly
stating that a specific outcome is unknowable, e.g., an unresolved binary
regulatory event). Every one of the four claims in this session's example
is independently well-evidenced; they simply point different directions.
**This is §5's cross-dimensional divergence, not `DE-011`'s within-claim
uncertainty.** The two are siblings in spirit — both refuse to manufacture
false resolution — but they are formally distinct mechanisms, and treating
them as the same concept would blur `DE-011`'s own carefully-drawn
boundary.

**Verdict: ADOPTED, restating §2/§5 precisely rather than introducing a new
mechanism.** Outlook communicates the actual multi-dimensional state
exactly as it stands, never forced into one directional conclusion — and
this is achieved entirely through §2–§4's dimension-preservation model, not
through any new "uncertainty-preservation" apparatus borrowed from
Conviction.

---

## 10. Conclusion or Structured Explanation?

**Test against `DE-012` §1's adopted definition of Recommendation directly**,
since this is the sharpest available contrast: Recommendation is "the
terminal, categorical conclusion... one of six mutually exclusive
directions." It is closed-form — exactly one of a small, fixed enumeration.
Nothing adopted in §§1–9 above gives Outlook an analogous fixed
enumeration; there is no small set of "Outlook values" comparable to
Recommendation's six directions, and §6 explicitly rejected manufacturing
one (via either a P/N/N label or a multiplied set of named sub-Outlooks).

**Verdict: ADOPTED — Outlook is a structured explanation, not a conclusion.**
This is not merely a restatement of "Outlook and Recommendation answer
different questions" (`DE-009` §8's already-adopted finding) — it identifies
that they are different **kinds** of object. Recommendation is closed-form:
a categorical selection among a fixed set. Outlook is open-form: a named
bundle of dimensional statements with no fixed enumeration of possible
outcomes. This retroactively explains why `DE-009` struggled to name
Outlook's "primary output" the way `DE-001` easily enumerated
Recommendation's six directions (§0 of `DE-009` surveyed six existing
concepts precisely because none of them fit) — Outlook was never supposed
to reduce to a small, enumerable set the way Recommendation does, and this
document is the first to state that difference explicitly rather than
leave it implicit in the shape of the difficulty.

---

## 11. Adopted Composition Model

> **Atlas Outlook is composed by preserving, never collapsing, the named
> analytical dimensions that bear on it — durability, evidence quality, and
> valuation attractiveness (`DE-009` §2.6), together with whichever of their
> own sub-findings (growth, capital allocation, competitive position, risk)
> are relevant, inherited through the existing Drivers pointer mechanism
> (`DE-009` §6) exactly as Business Evaluation already refuses to collapse
> them internally (`Doctrine` §4). Where dimensions agree, Outlook may read
> as a single coherent direction of travel; where they diverge, Outlook
> states the divergence honestly, as a structured, qualitative explanation
> (`APP-002` §6's evidence-attributed register), never as a forced single
> label. No dimension holds standing priority over another; apparent
> extreme-case dominance is Evidence Quality degrading broadly, not a
> hierarchy. Outlook remains exactly one object (`DE-009` §3, reaffirmed),
> never multiplied into per-dimension sibling Outlooks, and it is a
> structured explanation, not a categorical conclusion — the defining
> difference between Outlook and Recommendation, not merely a difference in
> what each happens to say.**

This model requires no scoring system, no formula, and no weighting — every
candidate that would have needed one (average, strongest driver, dominant
driver) was tested and rejected in §§1, 3, and 7.

---

## 12. Rejected Alternatives (Summary)

| Candidate | Verdict | Reason |
|---|---|---|
| Collapse to Positive / Neutral / Negative as Outlook's own content | Rejected | Violates `APP-000` PP-007 exactly when dimensions diverge; not independently explainable without a hidden formula (§1) |
| Average across dimensions | Rejected | Category error (no shared unit); can manufacture a false "neutral" describing neither real dimension (§3) |
| Strongest driver (best-evidenced dimension wins, others dropped) | Rejected | Silently discards real Counter-Evidence-shaped content, violating `DE-002` §2.3 one level up (§3) |
| Dominant driver (a standing hierarchy among dimensions) | Rejected | No genuine counter-example survives; extreme cases explained by shared-cause Evidence Quality collapse, not priority (§7) |
| Limiting-factor / weakest-link composition | Rejected for Outlook | Already correctly adopted, but for Recommendation (`DE-008` §10.2) — duplicating it inside Outlook blurs the understanding/action boundary `DE-012` §9 established (§3) |
| Multiple named sub-Outlooks (Business Outlook, Valuation Outlook, etc.) | Rejected | Repeats `DE-009` §3's already-settled rejection of multiplied Outlook objects, sliced by dimension instead of time; also repeats `DE-013` Finding 1.2's naming-proliferation failure deliberately (§6) |
| "Uncertainty preservation" as a new mechanism borrowed from Conviction | Rejected, clarified | Cross-dimensional divergence (this document) and within-claim epistemic uncertainty (`DE-011` §9) are siblings in spirit, not the same mechanism (§9) |
| Outlook as a closed-form conclusion, enumerable like Recommendation | Rejected | No fixed enumeration of "Outlook values" survives §§1–6; Outlook is open-form by nature, not by omission (§10) |

---

## 13. Dependency Relationships

- **Outlook's composed dimensions → inherit, never duplicate → Business
  Evaluation's own sub-findings** (Growth, Capital Allocation, Competitive
  Position within Durability), through the existing Drivers pointer
  (`DE-009` §6). No new store, no new evaluator.
- **Outlook's composition model → recurses → at whatever level tension
  appears**, intra-dimension (§4, scenarios C/D) or inter-dimension (§4,
  scenarios A/B) alike, with no special-casing required.
- **Outlook's composition → does not consume → Conviction or Expected
  Return** (§4, scenario E) — both remain, respectively, an accompanying
  rating (`DE-009` §9, `DE-011`) and a derived representation (`DE-010`
  §2), never inputs to the composition problem this document solves.
- **Outlook's composition → does not consume → Recommendation's
  limiting-factor logic** (§3, §7) — that logic remains `DE-008`'s own,
  never inherited.
- **Short-Term View (`DE-010` §1) → is now precisely explained by →
  Outlook's named-dimension Drivers, filtered by date** (§4, scenario F) —
  this document sharpens, rather than alters, `DE-010` §1's existing
  representation.

---

## 14. Open Questions

1. **How many named dimensions is "a small number" (`DE-009` §2.6)?** This
   document adopts preserving divergence but does not set a ceiling on how
   many simultaneously-named dimensions an Outlook statement may carry
   before it stops being a "small number" and starts becoming an
   undisciplined list. `APP-000` PP-004's progressive-disclosure principle
   is the likely governing constraint, but this document does not test it
   directly.
2. **Does the degenerate "all dimensions agree" case need its own explicit
   naming rule?** §1 permits a P/N/N-style representation-layer convenience
   only when dimensions genuinely agree, but does not specify how
   "agreement" itself is determined precisely enough to gate that
   convenience reliably — a representation-layer question, out of this
   document's ontology-only scope, but worth flagging for `DE-010`'s own
   future extension.
3. **Does Risk deserve status as a fourth named `DE-009` dimension, rather
   than a sub-finding folded into Durability?** This document treated Risk
   as one of the granular dimensions this session's background names,
   inherited through Business Evaluation and the already-adopted
   Financial/Valuation Risk category (`DE-008` §13) — but `DE-009` §2.6's
   own three-dimension definition does not name Risk explicitly. Whether
   Risk is fully subsumed by Durability and Valuation attractiveness, or
   deserves its own named slot in Outlook's composition, is not resolved
   here.
4. **Naming audit, again**, following the same pattern every prior ADR in
   this series has flagged: "structured explanation" (§10) is offered as
   descriptive framing for this document's own argument, not as a
   user-facing term, and has not been checked against the corpus's
   naming-collision discipline.

---

## 15. Implications for Outlook Representation (`DE-010`)

- **`DE-010` §1 (Short-Term View) is sharpened, not altered**: it is now
  precisely explained as a date-filtered slice of this document's own
  named-dimension Drivers, not a separate mechanism (§4, scenario F).
- **`DE-010` §3 (Bull/Base/Bear)** is confirmed compatible: each
  instantiation is itself a structured, multi-dimensional explanation under
  this document's model, never a single collapsed label — consistent with,
  and strengthened by, this document's §10 finding that Outlook is
  open-form.
- **A new, narrow representation is licensed, not designed, by §1**: a
  single collapsed label (Positive/Neutral/Negative or similar) may exist
  as a Representation Layer convenience strictly limited to the degenerate
  case where every named dimension genuinely agrees — flagged here as an
  implication for a future `DE-010` extension, not adopted as part of it,
  and dependent on Open Question 2 above being resolved first.
- **`DE-010` §5's Representation Layer discipline (one shared computation,
  never per-surface divergence) applies with even more force now**: since
  Outlook's own content is explicitly multi-dimensional and never
  pre-collapsed, a Representation Layer that quietly picked its own
  per-surface "overall direction" would be manufacturing exactly the false
  resolution §1 forbids Outlook's own content from containing — the
  discipline `DE-010` §5/§6 already requires for consistency across
  surfaces is now also load-bearing for honesty, not merely for coherence.

---

## 16. Implications for Recommendation (`DE-012`)

- **`DE-012` §4/§9's finding that Recommendation does not consume Outlook
  is reinforced, not merely preserved.** If Outlook had a single collapsed
  directional value, it would be a tempting shorthand input to Direction
  Selection. Since this document confirms Outlook has no such value
  (§1, §10), there is no single "Outlook signal" a Recommendation could
  even consume — structurally reinforcing why `DE-008` never needed one and
  why `DE-012` §4 correctly excluded it.
- **`DE-012` §3's own limiting-factor-style AND/OR logic (`DE-008` §10.2)
  is now explicitly confirmed as Recommendation's exclusive machinery**
  (§3, §7 above) — this document tested and rejected importing it into
  Outlook, closing off what could otherwise have looked like a plausible
  future convergence between the two objects' composition rules.
- **No change to any of the six directions, Recommendation Withheld, or the
  Direction Selection decision procedure.** This document's entire content
  is upstream of, and structurally invisible to, `DE-008`'s existing rules.
