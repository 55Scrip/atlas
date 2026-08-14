# DE-009 — The Nature of Atlas Outlook

**Working title (as given):** ADR-001 — The Nature of Atlas Outlook
**Sprint:** Atlas Decision Engine — Sprint 1 (Outlook track)

**Status:** Ontology investigation only. Not yet adopted doctrine, not yet a
companion specification with normative authority. This document does not
amend `docs/ATLAS_DECISION_ENGINE_DOCTRINE.md` or any `DE-00X` companion —
it investigates whether a genuinely new concept, "Atlas Outlook," belongs in
that family at all, and if so, what it is. No code, pseudocode, UI, or
formula accompanies this document, by explicit instruction. Where a formula
is unavoidable to state a structural relationship precisely, it is flagged
as such and kept to the smallest form that states the relationship, never a
computation.

**Method note.** This investigation follows the same discipline
`ATLAS_DECISION_ENGINE_DOCTRINE.md` §4 (Business Evaluation) used for its
own new territory: no existing document in this repository or in
conventional investment software is treated as authoritative. Every
candidate is stated, tested against a concrete scenario or an already-
adopted principle, and rejected or adopted with the specific contradiction
or consistency that decided it. Several conclusions below reject the
premise of the question that produced them — this is a feature of the
method, not a failure to answer the question as posed.

---

## 1. The Starting Question, Made Precise

*Atlas has analyzed everything available about a company. It must now
summarize its current understanding. What is that summary?*

Before answering, it is necessary to state what is **already spoken for** by
existing doctrine, so that Outlook is not invented to duplicate something
that already has a name and a home:

| Existing concept | What it already answers | Governing document |
|---|---|---|
| Business Evaluation | Is the business durable? How good is the evidence? What is knowable versus assumed? — a present-tense judgment, never scored | `Doctrine` §4 |
| Valuation Philosophy | Is the current price attractive relative to a range, under stated assumptions? — a present-tense comparison | `Doctrine` §5 |
| Portfolio Intelligence | How does this specific position interact with this specific portfolio? | `DE-003` |
| Atlas Recommendation | What should the Investor consider doing — one of six directions, or Recommendation Withheld? | `DE-001` |
| Atlas Conviction Level | How well does the evidence support whatever conclusion was just reached? | `DE-004` |
| Investment Thesis / Decision Memory | Why does a position exist, and has its specific claims strengthened or weakened since it was made? — retrospective, and requires a Decision to already exist | `DE-005` §1 |

None of these six answers the starting question as asked. Business
Evaluation and Valuation are both **present-tense** ("is," not "will
become"). Recommendation is **prescriptive** ("what to do"), not
descriptive of expected trajectory. Investment Thesis is **retrospective**
and, critically, **requires a prior Decision to exist** — it cannot describe
a company Atlas has never been asked to act on, which is exactly the
Discovery/candidate-evaluation case where a forward view is most valuable.

There is a genuine gap: nothing existing states, in the present, what Atlas
currently expects to become more or less true **going forward**. That gap is
what "Outlook" is a candidate name for. The rest of this document tests
whether the candidate concepts on offer actually fill it without
contradicting anything already adopted.

---

## 2. What Is an Outlook? Testing the Candidates

### 2.1 A prediction

**Definition tested.** A forecast that a specific future state will occur.

**Test.** `Doctrine` §2, commitment 3: *"No market-timing claims. Atlas does
not predict near-term price direction... This is a direct application of
`APP-000` §4's 'Atlas fundamentally is not... a performance-prediction
system whose value is measured by forecast accuracy.'"*

**Verdict: REJECTED.** A prediction, by definition, claims to know a future
state. This is not a close call — it contradicts an already-adopted,
first-order commitment directly, not by implication.

### 2.2 An expectation

**Definition tested.** A softer prediction: "what Atlas currently believes
is most likely," without a claim of certainty.

**Test.** Mathematically, a single "most likely" future state is a point
estimate with a softer name. `Doctrine` §5.1 already rejects this exact
pattern for valuation: *"Atlas SHALL NOT state a single-number price
target, a single-number fair value, or a single-number expected return."*
`APP-000` PP-007 ("SHALL NOT present a conclusion with greater confidence
than its underlying Evidence and Reasoning support") applies with equal
force to a single point about the future as to a single point about value
today — the underlying evidence problem (many unstated assumptions
compressed into one number) is identical.

**Verdict: REJECTED as a single point.** The word "expectation" survives
only if it is explicitly re-scoped to mean "the direction of travel Atlas
currently sees, under stated conditions" rather than "the one thing Atlas
thinks will happen" — which is no longer really an expectation in the
ordinary sense. See §2.4.

### 2.3 A probability distribution

**Definition tested.** A full distribution over possible future outcomes
(e.g., a return distribution with percentiles).

**Test.** This is not merely a point estimate with error bars — it is a
*more* precise-looking artifact than a single number, since it implies
Atlas can quantify not just an outcome but the relative likelihood of every
alternative outcome. Constructing this honestly requires numeric weights on
macro conditions, competitive responses, and management decisions that
`Doctrine` §5 and `UX-000` `UXD-R-064` already treat as beyond what a
categorical, evidence-bound judgment can honestly claim (`UXD-R-064`: *"This
Doctrine SHALL NOT define a numeric or categorical confidence scale"* —
adopted for Conviction in `DE-004`, and the identical false-precision
concern applies with even greater force to a full probability distribution
over outcomes).

**Verdict: REJECTED, and the worst-fitting candidate tested.** It manufactures
a false sense of quantified certainty around fundamentally unquantifiable
judgment — the opposite direction from where every other adopted principle
in this corpus already points.

### 2.4 A scenario analysis

**Definition tested.** A small number of named, discrete, internally
coherent future states (e.g., Bull/Base/Bear), each described with its own
assumptions, without formal probabilities attached.

**Test.** This is structurally identical to the already-adopted Valuation
range: *"Every valuation range Atlas states SHALL name the assumptions that
produce it"* (`Doctrine` §5.2), generalized from a single range to a small,
discrete set of named alternative condition-sets. No new principle is
required to justify it — it is the existing Valuation discipline applied to
more than one assumption set at once.

**Verdict: PROVISIONALLY ADOPTED as Outlook's shape**, pending the separate
treatment of Bull/Base/Bear specifically in §5, where the same test is
applied to the *number* and *naming* of scenarios, not just the principle.

### 2.5 A decision support object

**Definition tested.** Something whose entire purpose is to inform the
Investor's own judgment, not to independently describe or predict reality.

**Test.** Consistent with `APP-000`'s whole framing of Atlas — but tested
against **every other Atlas output already adopted** (Business Evaluation,
Valuation, Recommendation, Portfolio Context), every one of which is
equally "a decision support object" by this definition. A definition that
fits everything distinguishes nothing.

**Verdict: TRUE BUT INSUFFICIENT.** "Decision support object" correctly
describes Outlook's *purpose* (it exists to inform, never to replace,
Investor Judgment — `APP-000` §5, PP-003, PP-005) but says nothing about its
*content*, which is what §2.1–§2.4 were actually testing. Purpose and
content are answered separately below.

### 2.6 Adopted definition

> **Atlas Outlook** is Atlas's current, explicitly conditional synthesis of
> the direction of travel it sees in a business's durability, evidence
> quality, and valuation attractiveness — expressed as a small number of
> named, internally coherent conditions (never a single point, never a
> probability-weighted average), each traceable to specific, named Drivers
> (§6), and existing to inform, never replace, the Investor's own judgment.

This rejects §2.1 (prediction), §2.3 (probability distribution), and the
naive form of §2.2 (a single expected point); adopts §2.4's shape
(scenario-structured, assumptions named); and treats §2.5 as Outlook's
*purpose*, not its definition.

**What Outlook is explicitly not a synthesis of, and why this matters for
§8:** Outlook is built directly from Business Evaluation and Valuation —
the same present-tense conclusions Atlas already reaches independent of any
Decision. It is deliberately **not** built from Investment Thesis (`DE-005`
§1), because Investment Thesis "is not a separately recorded object; it is
the accumulated set of `reason` statements across that position's own
Decision history" — it structurally cannot exist before a first Decision is
made. If Outlook depended on Investment Thesis, it would be unavailable
exactly where a forward view is most valuable: before the Investor has
decided anything at all. This is tested formally in §8.

---

## 3. Short-Term Outlook and Long-Term Outlook: A False Dichotomy

The question as posed assumes Atlas should have both. Testing that
assumption directly, rather than answering "what's the difference," is more
productive.

**Test.** What would a "Short-Term Outlook" (say, the next one to four
quarters) actually have to claim to be distinct from the long-term case?
In ordinary financial usage, "short-term outlook" means a view on near-term
price action, sentiment, or the next earnings print. `Doctrine` §2,
commitment 3 already forbids exactly this: *"Atlas does not predict
near-term price direction."* A genuine, coequal "Short-Term Outlook"
sibling to "Long-Term Outlook" would either (a) violate that commitment
directly, by being a near-term price call in a different name, or (b) be
so hedged as to say nothing distinguishable from the long-term case, which
fails "smallest model capable of expressing reality" by adding a concept
that carries no content of its own.

**What legitimately survives.** A company can have a specific, *named*,
near-term-dated event that would resolve a specific open question — an
earnings release, a regulatory ruling, a guidance update. This is not a
second Outlook. It is exactly what `DE-002` §2.7 (What Could Change This
View) already exists to state: *"Specific, named conditions — a metric
crossing a stated threshold, a named assumption failing... never a generic
disclaimer."* A near-term catalyst is simply a §2.7 trigger with a near
date attached, not an independent forward-looking belief about what will
happen.

**Verdict: REJECTED as a coequal sibling.** There is exactly **one**
Outlook, always evaluated over the Investor's own stated time horizon per
`Doctrine` §2, commitment 2 ("Time horizon is stated, not assumed"). What
colloquially gets called "short-term outlook" is not a second Outlook
wearing a shorter time window — it is the near-term subset of Outlook's own
revision triggers (§7), already covered by the existing §2.7 mechanism.
Inventing a second Outlook object to hold this content would duplicate
`DE-002` §2.7 under a new name while also reopening the market-timing
contradiction §2.1 already closed.

---

## 4. Is Expected Return the Correct Primary Output?

**Test against existing doctrine, directly, before testing alternatives.**
`Doctrine` §5.1 states, unconditionally: *"Atlas SHALL NOT state a
single-number price target, a single-number fair value, or a single-number
expected return."* This is not a new rejection this document is
discovering — Expected Return, as a scalar, is **already, explicitly
prohibited**. Any Outlook that produces "Expected Return: +14%" as its
primary output would contradict existing, adopted doctrine on its face.

**Could it survive as a range instead of a point?** A return range under
stated assumptions is arithmetically just the Valuation range (`Doctrine`
§5) re-expressed as a percentage delta from the current price instead of an
absolute value. It adds no new information Valuation does not already
carry, and doubling the same content under two names violates "smallest
model capable of expressing reality." **Verdict: a return range is at best
a *derived, secondary display*, computed from the already-adopted Valuation
range and the current price — never authored independently, and never
Outlook's defining content.**

**Testing the user's offered alternatives:**

- *Expected outcome* — too vague to test; doesn't name what dimension
  ("outcome" of the thesis? the trade? the business?). Not adopted as
  stated.
- *Expected investment quality* — risks duplicating Durability (`Doctrine`
  §4.1), which already asks a present-tense quality question. Only survives
  if explicitly reframed as the *trajectory* of quality (improving/eroding),
  not quality itself — folded into the adopted definition (§2.6) rather
  than kept as a separate concept.
- *Expected value creation* — closer to something real: whether the
  business, going forward, is likely to compound value (growth + capital
  allocation working together) or erode it. This maps onto Durability and
  the existing Capital Allocation evaluator, reframed forward. A genuine
  partial contributor to Outlook's content, not a full definition on its
  own.
- *Expected thesis evolution* — the most doctrinally tempting candidate,
  since Investment Thesis is already a well-specified primitive (`DE-005`
  §1) and reusing it avoids inventing new machinery. **Tested and rejected
  as the *primary* definition** for the reason stated in §2.6: Investment
  Thesis requires a prior Decision to exist, and Outlook must be available
  before one does. Thesis-evolution is instead adopted as an *optional,
  additional* layer of Outlook, present only once a position exists — see
  §8.

**Verdict.** Expected Return is rejected outright (§5.1 already forbids
it). None of the offered alternatives alone is sufficient; Outlook's
adopted content (§2.6) is closer to "expected value creation," generalized
beyond capital allocation to include the full Business Evaluation and
Valuation trajectory, with thesis-evolution folded in as an optional
extension once a Decision exists.

---

## 5. Bull, Base, and Bear: What They Actually Are

**Test each candidate relationship in turn.**

- **Probability-weighted futures.** Rejected for the identical reason §2.3
  was rejected: assigning "60% Base / 25% Bull / 15% Bear" implies a
  quantified likelihood judgment the evidence cannot honestly support, and
  multiplying through produces an implied single expected value —
  reintroducing the already-forbidden Expected Return (§4) through a side
  door.
- **Stress tests.** A stress test asks "what happens if a specific adverse
  condition occurs" — this is functionally identical to a detailed,
  downside-only instance of `DE-002` §2.7's revision-trigger content. Useful,
  but not a new object; a Bear scenario that is *only* a stress test would
  just be one §2.7 trigger elaborated, not a full alternative Outlook.
- **Explanatory tools.** The strongest fit. Bull/Base/Bear, read this way,
  are not three competing forecasts Atlas is hedging across — they are a
  presentation device that makes Outlook's *sensitivity to its own
  assumptions* visible: "under assumption set A, the outlook looks like
  this; under the more supportive plausible assumption set B, it looks like
  this." This directly serves an already-adopted principle
  (`Doctrine` §5.3, change triggers are stated) rather than adding a new
  one.

**Verdict, and one correction to ordinary usage.** "Base" is not "the most
probable outcome" (a probability claim) — it is **the scenario built from
Atlas's currently best-supported assumptions**, an evidentiary claim, not a
probabilistic one. Given that, **Base and Outlook are the same thing** —
there is no need for a separate "Base Case" label distinct from Outlook
itself. Bull and Bear are explicitly-named **deviations** from Outlook,
each built from a plausible alternative assumption set that remains
consistent with Known facts (`APP-002` §7) — not arbitrary extremes, and
not required to exist symmetrically (a company may have a credible Bear
case and no credible Bull case, or vice versa).

**Mandatory or optional?** Constructing two full alternative scenarios
requires *more* assumptions than stating one Outlook, and `DE-002` §2.3
already establishes the precedent that manufacturing content for the
appearance of completeness is prohibited: *"Counter-Evidence SHALL be
genuine and specific, or the section SHALL state plainly that no material
counter-evidence was found — never populated for the appearance of
completeness."* **Verdict: Bull and Bear are each independently optional**,
stated only where the evidence supports naming a genuinely distinct,
plausible alternative assumption set. Where it does not, Outlook states
only itself (the Base case, unlabeled as such), exactly as thin evidence
already causes Recommendation Withheld rather than a manufactured
direction (`DE-004` §4).

---

## 6. Should Outlook Include Its Own Reasons?

**Test the proposed layering — Outlook → Drivers → Evidence → Raw Data —
against what already exists.** `DE-002` §2.2 (Evidence) and §2.3
(Counter-Evidence) are already first-class, canonical sections every
Recommendation conclusion must trace back to explicitly: *"[Direction,
stated] with an explicit link back to the specific Evidence,
Counter-Evidence, and Portfolio Context items that produced it"* (`DE-002`
§2.5). The proposed Outlook → Drivers → Evidence → Raw Data chain is
*structurally the same discipline*, already adopted for Recommendation.

**The real question is not whether Outlook needs traceability — it already
must, by the same principle that governs every other Atlas conclusion —
but whether Outlook should own a *second, separate* Evidence/
Counter-Evidence store, or point into the existing one.**

**Test.** If Outlook maintained its own copy of "why," the same underlying
fact (say, a specific margin trend) could end up cited with different
wording or drift out of sync between Outlook's version and Recommendation's
version — the same evidence base, forked. This violates "smallest model
capable of expressing reality" and creates exactly the kind of
inconsistency `Doctrine` §6's fixed Reasoning Structure exists to prevent
("consistency of structure... is what makes step-skipping detectable").

**Verdict: ADOPTED, with one refinement.** Outlook does **not** own a
separate Evidence/Counter-Evidence section. It has **Drivers** — a short,
named *pointer* into the existing `DE-002` §2.2/§2.3 Evidence and
Counter-Evidence content and the existing Business Evaluation/Valuation
conclusions that specifically produced this Outlook — never a duplicate
copy of their content. The ontology is:

```
Outlook
  ↓ (named pointer, not a copy)
Drivers  — which existing Evidence/Counter-Evidence items and
            Business Evaluation/Valuation conclusions produced this Outlook
  ↓ (already canonical, unchanged)
Evidence / Counter-Evidence  (DE-002 §2.2 / §2.3)
  ↓ (already existing)
Raw Data  (Business Evaluation §4 / Valuation §5 / underlying facts)
```

This is the proposed ontology from the starting question, adopted, with the
correction that "Drivers" is explicitly thin (a selection, not a store).

---

## 7. How Should Outlook Evolve Over Time?

**Test the static/continuous dichotomy directly, the same way §3 tested
Short-Term/Long-Term.**

**Static** fails immediately: the Constitution's own principle, already
cited repeatedly in this corpus, is *"Atlas changes its mind when evidence
changes"* (`DE-002` §2.7). A frozen Outlook that never updates as new
Evidence arrives would contradict this directly.

**Continuously updated** (recomputed on every price tick or every data
refresh) fails differently: it risks manufacturing noise — an Outlook that
visibly flickers with routine market movement looks unstable rather than
considered, and smuggles back the near-term price-reactivity §3 already
rejected. Recomputing on a schedule (daily, weekly) is no better — it
couples Outlook's honesty to a clock rather than to evidence, which is
exactly backwards.

**What already exists to resolve this.** `Doctrine` §4's own treatment of
Business Evaluation reversal is the precedent: a conclusion changes *"when
the specific Durability judgment... no longer holds against current
Evidence"* — a named, specific claim failing, not a scheduled recompute.

**Verdict: ADOPTED — event-driven by Outlook's own named triggers, not
static and not continuously fluid.** Every Outlook SHALL state its own
revision conditions, reusing the exact mechanism `DE-002` §2.7 already
specifies for Recommendation ("What Could Change This View") rather than
inventing a parallel one. Outlook is restated exactly when one of its own
named Drivers (§6) is confirmed, contradicted, or newly available — a
deterministic, explainable event, not a timer and not a permanent freeze.
This resolves the static/continuous question as a third false dichotomy,
matching the pattern already found in §3: the honest answer is neither pole
of the question as posed.

---

## 8. Outlook and Recommendation: The Dependency Direction

**Test both directions independently, by concrete scenario, rather than
asserting a hierarchy.**

**Can Outlook exist without Recommendation?** Given §2.6's adopted
definition (Outlook is built from Business Evaluation and Valuation alone,
not from Investment Thesis), and given the existing precedent that Current
Situation and Portfolio Context *"MAY still be stated"* under Recommendation
Withheld (`DE-002` §4) — **yes.** In fact this is one of Outlook's most
valuable cases: evidence may be too thin to clear even Low conviction for
any of the six directions (triggering Recommendation Withheld, `DE-004`
§4), while Outlook can still honestly state the direction of travel Atlas
currently sees, exactly as Current Situation and Portfolio Context already
survive that same state. **Verdict: Outlook joins Current Situation and
Portfolio Context as content statable under Recommendation Withheld.**

**Can Recommendation exist without Outlook?** Tested by concrete
counter-example: `DE-001` §2's Trim evidence pattern is *"the position's
weight has grown... to a concentration Portfolio Intelligence flags as
exceeding what continues to be supported"* — a pure portfolio-sizing
rationale. The business's forward trajectory may be completely unchanged;
only its weight relative to the rest of the portfolio changed. A Trim
recommendation is fully justified here without any reference to Outlook at
all. Buy's evidence pattern ("current price is attractive relative to
[the valuation] range") and Exit's ("the original thesis... has been
invalidated") are both **present-tense comparisons**, not inherently
Outlook-dependent either — Exit in particular is Investment Thesis's own
domain (`DE-005`), tested directly, not via a fresh Outlook restatement.
**Verdict: yes — Recommendation's evidence pattern (`DE-001` §2) does not
strictly require Outlook.**

**Conclusion.** Neither direction holds as a mandatory dependency. Outlook
and Recommendation are **siblings, not a chain** — both are separate,
parallel syntheses of the same upstream material (Business Evaluation,
Valuation, Evidence, Counter-Evidence, Portfolio Context), each answering a
different question the starting question itself already distinguished:
Recommendation answers *"what should the Investor consider doing"*
(action-oriented); Outlook answers *"what does Atlas currently expect,
going forward, and why"* (understanding-oriented). This is not a
compromise between two possible hierarchies — both tested directions
independently produced "no," which is itself the finding.

**One qualification, not a re-introduction of dependency.** Because both
draw from the same Evidence/Counter-Evidence/Drivers material (§6), a
Recommendation's Direction section (`DE-002` §2.5) **MAY** cite the current
Outlook as one of the things that informed it, exactly as it may already
cite Portfolio Context — but Outlook is never a *required* citation, and a
Direction is never invalid for omitting it. Sibling, not upstream input.

---

## 9. Confidence and Outlook

**Test with a concrete scenario before consulting existing precedent.**
Imagine Atlas has extensive, high-quality, mutually consistent evidence
that a company faces a structural, well-documented margin decline. The
evidence *quality* here is high — Atlas is not guessing — while the
*content* of the Outlook is negative. This demonstrates the two are
logically independent axes: a well-evidenced bad Outlook and a
poorly-evidenced good Outlook are both coherent, and neither collapses into
the other.

**This is not a new discovery — it is the same relationship already
adopted between Conviction and Direction** (`DE-004` §6: *"The Atlas
Conviction Level is independent of the recommendation direction... a
High-conviction Hold and a Low-conviction Buy are both coherent, complete
Atlas Recommendations."*). By direct structural analogy, a High-conviction
declining Outlook and a Low-conviction improving Outlook must both be
coherent.

**Should Outlook get its own, new confidence concept, or reuse the
existing one?** `DE-004` §2 already warns explicitly against inventing a
fourth confidence-shaped concept in this corpus, having already had to
resolve one naming collision (`ADR-003`, for "Recommendation"): *"Naming it
'Conviction' rather than 'Confidence' avoids a fourth accidental
collision."* Given Outlook draws from the identical evidence base as
Recommendation (§2.6, §6), there is no principled reason the evidence-
quality judgment should differ in kind between the two.

**Verdict: ADOPTED — Outlook reuses an existing, already-computed
evidence-quality signal rather than defining a new "Outlook Confidence."**
Outlook and its Conviction Level SHALL be stated together, per the same
rule `DE-004` §6 already states for Recommendation, and SHALL NOT be
collapsed into one combined signal.

**Corrective pass note (Alpha Freeze correction sprint, resolving
Principal Engineer Review 2.0 finding M-1).** This section's original text
named the specific signal reused as "the existing Atlas Conviction Level
(`DE-004`)" — `DE-004` §3's three-value (High/Medium/Low) scale. Direct
inspection of the real, shipped implementation (`atlas/analysis_engine/outlook.py`,
`_outlook_conviction`, which returns the case-wide `conviction.level`
verbatim, floor-capped only by data sufficiency) shows this was inaccurate:
the signal Outlook actually reuses is `AnalysisConvictionLevel`
(`atlas/analysis_engine/conviction.py`'s five-value
`very_high`/`high`/`moderate`/`low`/`insufficient_evidence` scale,
identified and named as a separate concept from the Atlas Conviction Level
by `DE-007` §11 and `DE-011` §0) — not `DE-004`'s three-value scale. This
correction changes only which existing signal this document says Outlook
reuses; it does not change Outlook's implementation, does not introduce a
new signal, and does not reopen this section's own settled reasoning for
*why* reuse rather than invention is correct (the analogy to
Conviction/Direction orthogonality above still holds identically for
Outlook and `AnalysisConvictionLevel`). `DE-011` §5/§10, which cited this
section's original claim, is corrected in the same pass — see that
document's own corrective note.

---

## 10. Adopted Definition of Atlas Outlook

> **Atlas Outlook** is Atlas's current synthesis of the direction of travel
> it sees in a business's durability, evidence quality, and valuation
> attractiveness, built directly from Business Evaluation (`Doctrine` §4)
> and Valuation Philosophy (`Doctrine` §5) — never from Investment Thesis,
> which it does not require to exist. It is expressed as one central view
> (never called "Base" separately — the central view *is* Outlook) plus,
> optionally, a Bull and/or Bear deviation, each a named, plausible
> alternative assumption set consistent with Known facts, never
> probability-weighted and never averaged into a single figure. Every
> Outlook names its own Drivers — a pointer into existing Evidence,
> Counter-Evidence, and Business Evaluation/Valuation content, never a
> duplicate of it — and its own revision triggers, reusing `DE-002` §2.7's
> existing mechanism. Outlook is accompanied by the existing Atlas
> Conviction Level (`DE-004`), independent of Outlook's content exactly as
> Conviction is independent of Recommendation's Direction. Outlook and
> Recommendation are siblings: neither requires the other to exist, and
> Outlook specifically survives Recommendation Withheld, alongside Current
> Situation and Portfolio Context. Outlook is never a single number, never
> a price target, and never a return figure — where a return figure is
> useful at all, it is a secondary, derived display computed from the
> already-adopted Valuation range, never Outlook's own authored content.

---

## 11. Rejected Alternatives (Summary)

| Candidate | Verdict | Reason |
|---|---|---|
| Outlook as prediction | Rejected | Contradicts `Doctrine` §2's no-market-timing commitment directly |
| Outlook as single expectation/point | Rejected | Same false-precision failure `Doctrine` §5.1 already rejected for valuation |
| Outlook as probability distribution | Rejected | Manufactures quantified certainty the evidence cannot support; worst-fitting candidate tested |
| Outlook as pure "decision support object" | Insufficient alone | True of every Atlas output; describes purpose, not content |
| Coequal Short-Term Outlook alongside Long-Term Outlook | Rejected | Either reintroduces market-timing or duplicates `DE-002` §2.7 under a new name |
| Expected Return as primary output | Rejected | Already, explicitly forbidden by `Doctrine` §5.1 |
| "Expected thesis evolution" as primary definition | Rejected (adopted as optional extension) | Investment Thesis (`DE-005` §1) requires a prior Decision; Outlook must survive before one exists |
| Bull/Base/Bear as probability-weighted futures | Rejected | Reintroduces a single expected value through implied weighting |
| Bull/Base/Bear as pure stress tests | Rejected as sole framing | Collapses into a single `DE-002` §2.7 trigger, not a distinct scenario |
| Outlook owning its own Evidence/Counter-Evidence store | Rejected | Duplicates `DE-002` §2.2/§2.3; risks the same fact being cited inconsistently in two places |
| Outlook as static, fixed-at-creation | Rejected | Contradicts "Atlas changes its mind when evidence changes" |
| Outlook as continuously/scheduled recomputed | Rejected | Couples honesty to a clock; risks near-term noise reintroducing market-timing |
| New "Outlook Confidence" concept | Rejected | `DE-004` §2 already warns against a fourth confidence-shaped naming collision; no principled reason to differ from Conviction |
| Recommendation as a required upstream input to Outlook, or vice versa | Rejected (both directions tested) | Each is independently constructible from the same upstream material; genuine counter-examples exist in both directions |

---

## 12. Open Questions

These are not resolved by this document and are flagged, not guessed at,
per the investigation's own instruction.

1. **Naming.** "Atlas Outlook" itself has not been tested against the same
   naming-collision discipline `ADR-003` and `DE-004` §2 already applied to
   "Recommendation" and "Confidence." A search for an existing, differently-
   scoped use of "Outlook" elsewhere in this repository's product or UX
   documents has not been performed as part of this investigation and
   should precede formal adoption.
2. **Where Outlook attaches structurally.** §6 established that Outlook
   points into `DE-002`'s existing Evidence/Counter-Evidence rather than
   owning a copy, and §8 established Outlook is a sibling to Recommendation
   rather than a `DE-002` section itself. Whether Outlook should nonetheless
   become an eighth `DE-002` section (alongside Direction and Conviction) or
   remain permanently outside that structure as a separate, referenced
   artifact is not decided here — §8's sibling finding argues against
   folding it in, but this deserves its own explicit governance decision
   before implementation, the same way `DE-006`'s relationship to `DE-001`
   was explicitly decided rather than assumed.
3. **What happens when Outlook and the existing Investment Thesis
   disagree** — e.g., Outlook (built from current Business Evaluation and
   Valuation) turns negative while the recorded Investment Thesis (`DE-005`)
   has not yet been marked as weakened. §2.6 and §8 establish that Outlook
   does not require Thesis to exist, but do not establish what Atlas should
   say when both exist and point in different directions. This is a
   genuine, not-yet-tested case.
4. **Minimum evidence bar for issuing any Outlook at all.** `DE-004` §4
   already establishes Recommendation Withheld as the honest outcome when
   evidence cannot support even Low conviction for a direction. Whether an
   analogous "Outlook Withheld" exists, or whether Outlook can always be
   stated (even if only as "Atlas does not yet see a clear direction of
   travel") the way Current Situation can always be stated, is not resolved
   here.
5. **Multiple Investment Cases / comparison.** This investigation reasoned
   about a single company's Outlook throughout. Whether Outlook is
   comparable across companies (e.g., for ranking or screening) was not
   tested and should not be assumed — `Doctrine` §4 deliberately rejects a
   single business-quality score for the same reason a cross-company
   Outlook ranking might be tempting but unsound.

---

## 13. Implications for the Rest of the Decision Engine

- **`DE-001` (Recommendation Framework) is unaffected.** §8 establishes
  Outlook does not sit upstream of Recommendation's evidence patterns. No
  change to the six directions or Recommendation Withheld is implied.
- **`DE-002` (Reasoning Structure) is unaffected as canonical structure**,
  pending Open Question 2. If a future governance decision folds Outlook in
  as an eighth section, `DE-002` §3's "seven sections, every time" would
  need to be revised to eight — this document does not make that change.
- **`DE-004` (Honest Uncertainty) gains a second consumer of its existing
  scale**, not a new scale. §9 extends "stated together, never collapsed"
  from Recommendation Direction to Outlook, by direct analogy — `DE-004`
  §6's wording would need a cross-reference added, not new content.
- **`DE-005` (Decision Memory) gains a defined relationship, not a change
  to its own content.** §2.6 and §4 establish that Investment Thesis is
  explicitly *not* Outlook's foundation, and §Open-Question-3 flags the
  unresolved case of disagreement between the two. `DE-005`'s own
  definition of Investment Thesis is untouched.
- **`Doctrine` §5 (Valuation Philosophy) supplies half of Outlook's
  foundation** (the other half being Business Evaluation, `Doctrine` §4).
  Neither section requires amendment — Outlook is built *from* them, not a
  restatement of either.
- **A genuinely new companion specification is implied**, not an amendment
  to an existing one, should this ontology be adopted: a `DE-0XX` defining
  Outlook's structure in the same register `DE-001`/`DE-002`/`DE-004`
  already use (required content, prohibited content, relationship to
  Recommendation), grounded in this document's §10 adopted definition. That
  specification is out of scope for this investigation, per the explicit
  instruction that this session concludes with ontology, not doctrine text
  ready for citation.
