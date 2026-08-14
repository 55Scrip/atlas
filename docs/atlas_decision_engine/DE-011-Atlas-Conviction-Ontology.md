# DE-011 — The Nature of Atlas Conviction

**Working title (as given):** ADR-011 — The Nature of Atlas Conviction
**Sprint:** Atlas Decision Engine — Sprint 2, Session 1 (Conviction track)

**Status:** Ontology investigation only. Not yet adopted doctrine. This
document does not amend `DE-004-Honest-Uncertainty.md` — the Atlas
Conviction Level's three-value scale (High/Medium/Low), its per-level
evidence patterns, its categorical-not-numeric justification, and its
naming rationale (§2, avoiding a fourth collision with "Confidence") all
stand unchanged. What `DE-004` does not give is a compact, first-principles
statement of *what Conviction fundamentally is* — it defines the scale and
uses the concept operationally (as does `DE-001`, `DE-002` §2.6, `DE-006`
§5, `DE-007`, `DE-008` §15, `DE-009` §9, `DE-010`), but no single document
answers the question this session asks directly. That is this document's
sole job. No implementation, algorithm, UI, or scoring system accompanies
it, per explicit instruction — this is ontology work, and where a scoring
system almost becomes unavoidable (§6, §10) that near-miss is itself
reported rather than resolved into a design.

**Corrective pass note (Alpha Freeze correction sprint, resolving
Principal Engineer Review 2.0 finding M-1).** Every citation below of
"Outlook reuses the Atlas Conviction Level" (§2, §5, §10, §11) restated a
claim this document inherited from `DE-009` §9, which direct inspection of
the real, shipped implementation has since shown to be inaccurate — see
`DE-009` §9's own corrective note for the full evidence. Outlook's real
`conviction` field (`atlas/analysis_engine/outlook.py`) reuses
`AnalysisConvictionLevel` (the five-value, case-wide evidence-quality
signal `DE-007` §11 and §0 below already separately identify as a distinct
concept from the Atlas Conviction Level), not `DE-004` §3's three-value
scale — and does so by returning the case-wide value near-verbatim
(`_outlook_conviction`, floor-capped only by data sufficiency), not by
performing an independent fresh assessment the way §10's "each attachment
point performs its own full assessment" language describes for Direction
and Execution Guidance. This correction is narrow and factual only: it
changes *which* existing signal Outlook is said to reuse, and notes that
Outlook's own reuse is a capped pass-through rather than a fresh
per-conclusion assessment. It does not reopen, and does not change, this
document's own adopted definition of what Conviction fundamentally *is*
(§11's core claim), Conviction's orthogonality to Direction or Expected
Return (§3, §4), or the rejection of a mandatory Conviction chain (§10's
own core verdict, which the corrected Outlook fact does not weaken — a
capped pass-through is still not a chain stage). Every remaining
occurrence of "the Atlas Conviction Level" in connection with Outlook
below should be read as historical framing this document used before the
correction, not as a restated current claim.

---

## 0. What This Session Found Already Exists

Before testing any candidate, the governed corpus was searched in full for
every existing reference to Conviction and Confidence. This surfaced
**three, not two**, structurally distinct "conviction-shaped" concepts
already active in this repository — one more than `DE-004` §2 itself
disambiguates, and load-bearing for several of the questions below:

1. **Investor-authored Confidence** (`DE-004` §2) — two existing fields,
   `Decision.investment_case`'s `Confidence` value object and the
   Investment Case form's `confidence` field — both a 0–100 self-report the
   Investor enters, which "Atlas stores... [and] does not interpret."
2. **The Atlas Conviction Level** (`DE-004` §3) — the three-value,
   categorical, Atlas-computed scale this document investigates.
3. **`AnalysisConvictionLevel`** (`atlas/analysis_engine/conviction.py`,
   identified in `DE-007` §11) — an already-real, already-shipped,
   **five**-level field (`very_high`/`high`/`moderate`/`low`/
   `insufficient_evidence`), Atlas-computed, case-wide, already shown in
   the Evidence section today. `DE-007` §11 already found and flagged this
   as "the one real ambiguity `DE-004` itself leaves open" and ruled that
   the Atlas Conviction Level is genuinely new, not a relabeling of it, and
   is never presented under the same label.

This document treats `DE-007` §11's ruling as settled and does not reopen
it. It matters here because Q1, Q6, and Q10 below each depend on being
precise about *which* of these three concepts is under discussion — the
question "is Conviction actually Confidence" turns out to have a cleaner
answer once it is clear there are three candidates in play, not two, and
that this session's entire scope is the second one only.

**One further load-bearing fact, found by direct search rather than
assumed:** `DE-006` §5 already states that Execution Guidance "carries its
own Atlas Conviction Level... stated independently of, and MAY be lower
than, the Conviction Level attached to the Direction it depends on."
This single sentence is the most consequential piece of prior art in this
investigation — it already proves, as adopted doctrine, that Conviction is
not a single case-level number, months before this session asked the
question directly. Several answers below (Q5, Q8, Q10) are essentially
this fact, generalized and explained rather than newly discovered.

---

## Primary Question, Answered Directly

**What does Atlas Conviction express?**

Not belief in the business, not belief in the investment, not agreement
with the recommendation, not a forecast of outcome, and not confidence in
any single piece of evidence. Stated precisely, and defended candidate by
candidate below:

> **Atlas Conviction is a rating of how well the evidence and
> counter-evidence currently available to Atlas support one specific,
> named conclusion Atlas has just stated — never a rating of the
> business, the investment, or Atlas's confidence in general.**

It is a **reusable evidentiary-sufficiency judgment**, not a property owned
by any single output. `DE-006` §5 already demonstrates this empirically:
the same kind of judgment is computed independently for a Recommendation's
Direction and, separately, for Execution Guidance's range — never passed
from one to the other. This document's job is to explain precisely why
that independence is correct, not incidental.

---

## 1. Is Conviction Actually Confidence?

**Test the user's own example.** Atlas has extremely strong evidence a
company is overvalued. Confidence in that specific evidentiary reading is
high. Should Conviction — attached to the resulting recommendation, say
Exit — also be high?

**Test for agreement first.** If the overvaluation evidence is strong,
consistent, and Counter-Evidence is minor, `DE-004` §3's High-tier pattern
is satisfied directly — Confidence-in-the-observation and
Conviction-in-the-conclusion agree here. This is not yet a contradiction.

**Now test for divergence, which is the real question.** Suppose the same
strong overvaluation evidence exists, but there is also strong,
unresolved Counter-Evidence — say, credible evidence of a
durability-improving strategic shift that could justify the higher price.
Confidence in the overvaluation *observation* is still high — nothing about
that specific evidentiary reading weakened. But `DE-004` §3's own
Medium-tier pattern now applies to the *conclusion*: "genuine
Counter-Evidence exists and is not fully resolved." Conviction in the
resulting Exit recommendation drops to Medium while Confidence in the
underlying observation has not moved at all. **This is a genuine
divergence, not a wording difference** — it proves Conviction is not a
synonym for confidence-in-an-observation; it is a synthesis across
everything that argues both for and against a conclusion, which a single
observation's confidence never captures on its own.

**A second, independent ground for divergence**, already settled and not
reopened here: `DE-004` §2's naming ruling — "Confidence" is reserved for
the Investor's own self-report (Fact 1, §0 above); the Atlas Conviction
Level is "the opposite in kind: an Atlas-computed assessment," never a
subjective self-report. Even where the two happened to produce the same
label, they would be answers to different questions asked by different
parties.

**Verdict: REJECTED.** Conviction is not Confidence, on two independently
sufficient grounds: (a) they can diverge under unresolved Counter-Evidence
even when the underlying observation's confidence is unchanged (§1's
overvaluation example), and (b) they differ in authorship and register —
self-report versus Atlas-computed synthesis (`DE-004` §2, unchanged).

---

## 2. Is Conviction Belief? If So, In What?

Testing each of the user's five candidates against `DE-004` §3's actual
evidence patterns and the wider corpus, in order:

**Belief in the business.** Rejected outright — this is `Doctrine` §4's
Business Evaluation, already governed by its own Durability,
Evidence-Quality, and Knowable-vs-Assumed dimensions. Conviction
duplicating it would violate the Background's own instruction against
duplication.

**Belief in the investment.** Rejected as imprecise rather than as a clean
duplicate — no single existing concept is named "the investment" in this
corpus; the phrase informally bundles Business Evaluation, Valuation, and
Portfolio Context together. Adopting it as Conviction's target would
quietly re-merge three concepts this corpus has gone to considerable
length to keep separate (`Doctrine` §§4–6).

**Belief in the reasoning.** Closer, and worth taking seriously — `DE-002`
§2.6 places Conviction structurally inside the Reasoning section, paired
with Direction. But test precisely: is Conviction a rating of *the
reasoning process's soundness in the abstract*, or a rating of *how well
the evidence supports the specific conclusion that process reached*?
`DE-004` §3's evidence patterns are unambiguous — every tier is defined by
evidence extent and Counter-Evidence resolution *for the conclusion*, never
by a meta-judgment about whether the seven-part structure was followed
correctly. **Rejected as stated, refined into the sharper candidate
below.**

**Belief in the recommendation.** Test against `DE-008` §15's already-
adopted invariant: *"Recommendation Conviction SHALL NOT determine or
restrict Direction — only gate its existence... and qualify it once
chosen."* If Conviction meant "belief that this recommendation is the
right call," a high Conviction would naturally argue for a stronger or
more aggressive direction — but the invariant explicitly forbids Conviction
from shaping which direction gets picked at all, and `DE-004` §6 states a
High-conviction Hold and a Low-conviction Buy are equally coherent. **This
is a direct contradiction**, so "belief in the recommendation" is
rejected: Conviction cannot mean agreement with the recommended action,
because it is deliberately orthogonal to what that action is.

**Belief in the outlook.** Test against `DE-009` §9's already-adopted
finding: Outlook reuses the Atlas Conviction Level, unchanged, rather than
inventing a new "Outlook Confidence." If Conviction were intrinsically
*of* the Outlook, this reuse would be an odd fit — but the reuse works
cleanly precisely because Conviction is not owned by Outlook at all, the
same way it is not owned by Direction. **This candidate is rejected for
the same reason "belief in the recommendation" was** — not because it is
wrong to pair Conviction with Outlook (that pairing is already correctly
adopted), but because "belief in the outlook" implies exclusive ownership
that the evidence (Outlook, Direction, and Execution Guidance all carrying
independent Conviction levels — `DE-006` §5) directly contradicts.

**Verdict, synthesizing all five tests:** Conviction is not belief in any
of the five candidates as stated. The nearest survivor, sharpened past
"belief in the reasoning": **Conviction is a rating of how well the
evidence supports the specific, named conclusion currently being stated —
reusable across whichever conclusion needs it (Direction, Outlook,
Execution Guidance), never a belief about the business, the investment as
a bundle, the reasoning process in the abstract, or exclusive ownership by
any one output.**

---

## 3. Can Conviction Increase While Expected Return Decreases?

**Test the user's example precisely.** A company's price rises. Business
quality (Durability, Evidence-Quality) is unchanged and strong. Valuation
richens, so Expected Return — the derived, live, present-tense range
adopted in `DE-010` §2 — mechanically compresses.

**Test whether this forces Conviction down.** Apply §2's adopted
definition: Conviction rates how well evidence supports *the specific
conclusion currently being stated*. If the new conclusion is "Hold,
because the business case remains excellent and valuation has now caught
up to it" — and that case is clean, well-evidenced, and free of unresolved
Counter-Evidence — `DE-004` §3's High-tier pattern is fully satisfied.
Nothing in Expected Return's mechanical compression touches evidence
extent or Counter-Evidence resolution at all.

**Test the reverse direction too, for completeness.** A thin, ambiguous
case can support a wide, exciting Expected Return range — Low Conviction,
high magnitude. A rock-solid, unambiguous case can support a narrow,
modest range — High Conviction, low magnitude. Both pairings are
internally consistent, which is only possible if the two are genuinely
independent axes.

**Verdict: YES — Conviction and Expected Return are orthogonal, and this
is not a coincidence but a structural requirement.** Expected Return is a
magnitude (`DE-010` §2: "how big is the potential gain"); Conviction is a
quality-of-support rating (how well-evidenced is the conclusion). Treating
either as a function of the other would repeat the exact category error
`DE-010` §9 already flagged when it rejected classifying Conviction as "a
representation of Outlook" — conflating an evidentiary-sufficiency rating
with a magnitude belonging to a different axis entirely. **Conviction
SHALL NOT be computed from, or made to track, Expected Return or any other
magnitude.**

---

## 4. Can Conviction Remain High While Recommendation Changes?

**Test the user's example.** Buy → Hold, driven purely by valuation
expansion; business quality evidence unchanged.

**Apply already-adopted doctrine directly**, rather than reasoning from
nothing: `DE-004` §6 states outright that "a High-conviction Hold and a
Low-conviction Buy are both coherent, complete Atlas Recommendations,"
and `DE-008` §15 confirms Conviction never drives Direction selection.
Nothing in either rule ties a Direction *change* to a Conviction change —
they are stated as fully orthogonal from the start.

**One precision worth adding, not fully explicit in `DE-004` §6 as
written.** "Conviction remains high" is loose phrasing for something more
exact: the *new* conclusion (Hold) receives its *own*, freshly assessed
Conviction level, evaluated against whatever evidence and Counter-Evidence
now support it — not a value carried forward unexamined from the prior
Buy conclusion. It can easily land at the same High label, because the
same well-established Business Evaluation evidence underlies both readings
and the valuation shift itself is equally clear-cut — but this is a fresh
assessment landing at a familiar value, not persistence of one value
across a change. This distinction matters directly for §7 and §8 below.

**Verdict: YES, Conviction can (and often should) remain at the same
level across a Direction change** — provided the new conclusion is itself
well-evidenced — **but this is a fresh, independent assessment of the new
conclusion, never a value inherited from the old one.** This refines
`DE-004` §6 rather than contradicting it.

---

## 5. Dependency Direction: Conviction and Recommendation

**Test whether Conviction can exist without Recommendation.** `DE-009` §9
and `DE-010` §9 already establish Outlook carries its own Conviction Level
independent of Recommendation (Outlook survives Recommendation Withheld
per `DE-009` §8). `DE-006` §5 shows Execution Guidance carries its own,
independently. **Yes — Conviction routinely exists attached to conclusions
other than a Recommendation Direction.**

**Test whether Recommendation can exist without Conviction.** `DE-002`
§2.6's structural requirement: Direction (§2.5) and Conviction (§2.6) "SHALL
always be stated together." `DE-002` §4 confirms the one true exception is
Recommendation Withheld, which does not contain a Direction either — so it
is not a counter-example, it is the absence of both together. **No —
whenever a Direction is actually stated, a Conviction Level is mandatory
alongside it.**

**Test whether Conviction can exist with no conclusion at all attached.**
Nothing in `DE-004` defines a free-standing Conviction Level; every
described use (§2.6's Direction pairing, `DE-009` §9's Outlook pairing,
`DE-006` §5's Execution Guidance pairing) is a rating *of* something.
**No — Conviction is never free-floating; it always answers "how well is
THIS specific conclusion supported."**

**Verdict: the dependency is real but one-directional and narrower than
the user's framing implies.** This is *not* the same "siblings, neither
requires the other" shape `DE-009` §8 found for Outlook and Recommendation
— it is asymmetric:

- Recommendation (specifically, its Direction) **cannot exist without**
  Conviction — mandatory pairing, `DE-002` §2.6.
- Conviction **can exist without Recommendation** — it attaches equally
  well to Outlook or Execution Guidance, `DE-009` §9 / `DE-006` §5.
- Conviction **can never exist without some conclusion to attach to** —
  it is a rating, not an independent entity.

---

## 6. Certainty or Robustness?

Testing the user's five alternatives against `DE-004` §3's actual,
already-adopted evidence patterns, which is the closest thing to ground
truth available for this question.

**Certainty, tested first since it's the more intuitive word.** "Certainty"
implies an estimate of the *likelihood the conclusion is correct* — which
edges toward an implied probability. `DE-004` §5 already rejects exactly
this shape for an independent reason: numeric or implied-probability
framing is false precision ("a number implies a precision... that no
evidence-based judgment of this kind actually supports"). Adopting
"certainty" as Conviction's conceptual core would reintroduce, informally,
the same problem the categorical (not numeric) scale was built to avoid.
**Rejected.**

**Evidence robustness, thesis robustness, reasoning robustness, outlook
robustness, recommendation robustness — tested together, since the
question is really "robustness of what."** `DE-004` §3's High tier: *"Evidence
is extensive, consistent, and directly supports the conclusion;
Counter-Evidence... is minor."* This is a joint test — evidence quality
*and* how well it holds up against what argues against it — evaluated
**for one specific conclusion**, not for evidence in the abstract. That
rules out plain "evidence robustness" (too general — evidence can be
robust in general while still weakly supporting one particular reading of
it) and "reasoning robustness" (too broad — a rating of the whole
seven-part structure's soundness, when Conviction is explicitly one
section's output, §2.6, not a rating of the other six). "Thesis
robustness" is rejected on a structural ground: `DE-005` §1 defines
Investment Thesis as requiring a prior Decision to exist at all
("accumulated... across that position's own Decision history") — Conviction
requires no such history; it applies to a first-ever analysis just as well
as a tenth. "Outlook robustness" and "Recommendation robustness" are
rejected on the same ground §2 and §5 already established: the identical
concept attaches to Direction, Outlook, and Execution Guidance
interchangeably, so it cannot be intrinsically owned by any one of them.

**Verdict: ADOPTED — robustness, not certainty, and specifically the
robustness of one stated conclusion against the counter-evidence and open
questions that exist against it.** This is the precise concept "Atlas
Conviction Level" already names without spelling out: not "how likely is
this true," but **"how well does this specific, stated conclusion survive
contact with everything that argues against it, given the evidence Atlas
actually has today."** No renaming is proposed — `DE-004` §2 already
settled the name "Conviction" specifically to avoid a fourth naming
collision, and the existing name is fully consistent with this refined
definition; this section supplies the definition the name was always
pointing at.

---

## 7. Should Conviction Change Frequently, or Be Stable?

**Test against `DE-004` §3's evidence patterns directly.** Conviction is a
function of the current evidence-versus-counter-evidence landscape for the
current conclusion (§6). It follows directly that Conviction should change
exactly when that landscape changes materially, and not otherwise.

**What should legitimately change it**, tested one at a time:

- New Evidence emerges that strengthens or weakens support for the current
  conclusion.
- Counter-Evidence is resolved (raising Conviction) or newly discovered
  and left unresolved (lowering it) — `DE-004` §3's own tier-defining
  language.
- The conclusion itself is revised — a new Direction, a new Outlook
  instance (`DE-010` §7) — which per §4 above triggers a **fresh**
  assessment, not a carried-forward one.

**What should not**, tested against the same pattern:

- Routine price movement alone. This is the same reasoning `DE-010` §2
  already applied to distinguish Expected Return (legitimately
  price-reactive, a present-tense fact) from Outlook's own content
  (event-driven, not reactive) — Conviction sits on the Outlook/Direction
  side of that line, not the Expected Return side, because price movement
  by itself changes no evidence and resolves no Counter-Evidence.
- Time passing with no new evidence. A scheduled "refresh" that reruns
  Conviction on a calendar rather than in response to a named trigger would
  imply the evidentiary landscape silently degrades on its own, which
  nothing in `DE-004` supports.

**Verdict: ADOPTED — Conviction is stable by default and event-driven,
reusing the same named-trigger mechanism `DE-002` §2.7 ("What Could Change
This View") and `DE-009` §7 already established for Reasoning and Outlook,
rather than inventing a separate Conviction-specific revision schedule.**
Conviction is revised exactly when the conclusion it accompanies is
revised — never on its own independent cadence.

---

## 8. Property of the Investment Case, or of Atlas's Current Understanding?

**Test directly against `DE-004` §3's evidence patterns**, which describe
*evidence extent*, *consistency*, and *Counter-Evidence resolution* — every
one of these is a fact about what Atlas currently has and knows, not a
fact about the company itself.

**A sharper test: can Conviction vary while the underlying business is
unchanged?** Two companies of genuinely identical real-world quality could
receive different Conviction levels purely because more, or better,
public disclosure exists for one than the other — a data-availability
difference, not a difference in the businesses. This is only possible if
Conviction describes **the sufficiency of what Atlas currently has**, not
a fact about the business that Atlas is merely reading off correctly or
incorrectly. If Conviction were a property of the investment case itself,
this scenario would be incoherent — the "true" Conviction would be a fixed
fact both companies either share or don't, and it wouldn't be able to
diverge from data availability, which is manifestly not how `DE-004` §3
is written.

**Verdict: ADOPTED — Conviction is a property of Atlas's current
understanding (the sufficiency of the evidence Atlas currently holds for
one stated conclusion), never a property of the investment case or
business itself.** This directly grounds §7's revision rule (Conviction
changes when Atlas's evidence changes, not when the business changes
independent of new evidence reaching Atlas) and is the same epistemic,
not ontological, framing `DE-009` §2.6 already applied to Outlook itself.

---

## 9. Conviction and Uncertainty: Can They Coexist at "High"?

**First, a precision the question needs before it can be tested.** This
corpus does not define a separate "Uncertainty" scale running alongside
Conviction — `DE-004` §1 states plainly that it exists specifically to
close `UX-000` `UXD-R-064`'s open question about a confidence/uncertainty
scale. The Atlas Conviction Level *is* this corpus's formal answer to
"how does Atlas express uncertainty" — there is no second, independent
uncertainty rating to compare it against. So the question must be read as:
can a *well-evidenced* conclusion (High Conviction) coexist with a
situation that is *itself* genuinely, irreducibly uncertain?

**Test the straightforward reading first.** `DE-004`'s Low tier is defined
partly by resting "more on Estimated or Possible content... than on Known
fact" (`APP-002` §7). By construction, High Conviction leans toward
Known-heavy evidence. A conclusion about an inherently unresolved
situation — one that rests mostly on Estimated or Possible content because
the facts genuinely aren't settled yet — structurally tends toward Low or
Medium, not High. In this direct sense, "High Conviction" and "high
situational uncertainty" pull against each other by construction, not by
accident.

**Now test the case that actually survives.** Conviction is never a rating
of *how certain the future is* (§8: it rates evidentiary sufficiency for a
stated conclusion, not the world's own unpredictability). So the question
becomes: can the conclusion itself be a well-evidenced, honest statement
*of* uncertainty? Example: "This business's near-term trajectory depends
on a binary regulatory decision, and no currently available evidence
favors either outcome" — this is a specific, checkable claim, and if the
evidence for *that characterization being accurate* is extensive,
consistent, and free of meaningful Counter-Evidence, `DE-004` §3's own
High-tier test is satisfied by the claim, even though the claim's content
is itself an assertion of deep uncertainty about the business.

**Verdict: YES, but only for this narrower, correct reading — High
Conviction and high situational uncertainty coexist exactly when
Conviction is attached to a conclusion that itself honestly states the
uncertainty (a wide range, a named unresolved binary, a Recommendation
Withheld's own stated reasoning), never when Conviction is attached to a
specific, narrow, confident-sounding claim about an inherently unsettled
outcome.** The two are not in contradiction once it is clear Conviction
rates the *statement*, not the *world* the statement describes.
Recommendation Withheld itself is a useful boundary case here: `DE-004` §4
deliberately places it **before** the Conviction scale rather than at any
point on it — Atlas does not say "High Conviction that I don't know," it
uses a structurally distinct outcome instead, which is consistent with,
not a counter-example to, this section's finding.

---

## 10. Should Conviction Become a Permanent Chain Object?

**Test the proposed architecture directly against two already-adopted
invariants — stronger evidence than a single analogy, since both are
directly on-point about Conviction specifically.**

**First counter-example: `DE-006` §5.** Execution Guidance's Conviction
Level is stated *"independently of, and MAY be lower than, the Conviction
Level attached to the Direction it depends on."* If Conviction flowed
through a single mandatory chain (`... → Outlook → Conviction →
Recommendation → ...`), Execution Guidance — which sits downstream of
Recommendation — would inherit or derive its Conviction from
Recommendation's own value, not compute an independent one. `DE-006`
explicitly forbids exactly that. This is a direct, adopted contradiction
of the proposed chain, not an analogy to one.

**Second counter-example: `DE-008` §15.** *"Recommendation Conviction
SHALL NOT determine or restrict Direction — only gate its existence... and
qualify it once chosen."* A chain position between Outlook and
Recommendation implies Conviction is computed once and then feeds forward
into what Recommendation becomes. The existence-gate role this invariant
actually grants Conviction is much narrower — Direction requires *a*
successfully assessed Conviction to exist at all (the "restated safeguard"
in `DE-008` §19: "HOLD and NO ACTION both require a successfully-assessed
Conviction level... If Conviction assessment fails... only
RecommendationWithheld") — but the assessed *level*, once it exists, never
shapes which Direction is chosen. Gating existence is not the same
relationship as sitting as a computed stage inside a pipeline.

**Verdict: REJECTED as a mandatory chain object — on stronger grounds than
`DE-010` §8 had available for the analogous Outlook question.** Conviction
is not a node that content flows through once; it is **a reusable pattern,
computed independently at each point in the Decision Engine that states a
conclusion needing one** — Direction, Outlook, Execution Guidance, and
potentially others in the future, each assessed fresh against that
conclusion's own evidentiary landscape. This is the same shape `DE-010` §5
already adopted for the Representation Layer (a shared *process*, not a
new domain object) — but here the finding is sharper still: Conviction
isn't even a shared single-computation step: each attachment point
performs its *own* full assessment, deliberately allowed to diverge from
every other attachment point's result (`DE-006` §5's "MAY be lower").

Whether Conviction should be **governed** as a permanent, first-class
concept of the Decision Engine is a separate question from whether it
belongs in a linear chain, and it is already settled: `DE-004` exists,
and is cited by name across seven other companion specifications (§0).
This document does not unsettle that. It only rejects the specific
proposed architecture, which conflates "permanently governed concept" with
"single-computation pipeline stage" — two different claims.

---

## 11. Adopted Ontology of Atlas Conviction

> **Atlas Conviction is a categorical (High / Medium / Low) rating of how
> robustly one specific, currently-stated Atlas conclusion is supported by
> the evidence and counter-evidence Atlas currently holds — evaluated
> fresh for whatever conclusion it accompanies (a Recommendation's
> Direction, an Outlook instance, an Execution Guidance range), never
> derived from, or propagated between, those conclusions.**
>
> It is a property of **Atlas's current understanding**, not of the
> business or investment case itself (§8); it changes only when the
> evidentiary landscape for its specific conclusion changes, reusing the
> same named-trigger mechanism (`DE-002` §2.7) already governing Reasoning
> and Outlook revision, never on a routine or price-reactive schedule
> (§7); it is independent of the conclusion's direction or magnitude —
> orthogonal to Recommendation Direction (`DE-004` §6, unchanged) and to
> Expected Return (§3) alike; it requires some specific conclusion to
> attach to and is never free-standing, but that conclusion need not be a
> Recommendation (§5); and it can coexist with high situational
> uncertainty exactly when it is attached to a conclusion that itself
> honestly states that uncertainty, never when attached to a narrow,
> confident-sounding claim about an inherently unsettled outcome (§9).

This adopts, refines, and gives a compact definition to the existing
`DE-004` scale — it changes nothing about the three levels, their
evidence patterns, their categorical framing, or the existing name.

---

## 12. Rejected Alternatives (Summary)

| Candidate | Verdict | Reason |
|---|---|---|
| Conviction = Confidence (renamed only) | Rejected | Diverges under unresolved Counter-Evidence even when observational confidence is unchanged; differs in authorship/register from investor self-report (§1) |
| Conviction = belief in the business | Rejected | Duplicates Business Evaluation (`Doctrine` §4) (§2) |
| Conviction = belief in the investment | Rejected | Imprecisely re-bundles three already-separated concepts (§2) |
| Conviction = belief in the reasoning (process soundness) | Rejected, refined | `DE-004` §3's patterns rate the conclusion, not the process (§2) |
| Conviction = belief in the recommendation (agreement with the action) | Rejected | Contradicts `DE-008` §15 and `DE-004` §6's orthogonality (§2) |
| Conviction = belief exclusively owned by Outlook | Rejected | Contradicts `DE-006` §5's independent, divergent Execution Guidance value (§2, §5) |
| Conviction driven by / tracking Expected Return | Rejected | Category error — magnitude vs. evidentiary-quality rating; both pairings (thin+wide, solid+narrow) are independently coherent (§3) |
| Conviction persisting unexamined across a Direction change | Rejected, refined | Each new conclusion gets a fresh assessment; landing at the same label is not the same as carrying the old value forward (§4) |
| Conviction and Recommendation as full mutual siblings (symmetric, like Outlook/Recommendation) | Rejected, refined | Asymmetric: Recommendation cannot exist without Conviction, but Conviction can exist without Recommendation (§5) |
| Certainty (implied probability) | Rejected | Reintroduces the false-precision problem `DE-004` §5 already rejected for numeric scales (§6) |
| Evidence / thesis / reasoning / outlook / recommendation robustness (as stated) | Rejected, refined into "conclusion robustness" | Each either too broad, too narrow, or structurally mismatched (requires prior Decision history; owned by one output only) (§6) |
| Conviction on a routine or price-reactive revision schedule | Rejected | No evidentiary change occurs on a calendar or with a quote tick; must be event-driven like Outlook (§7) |
| Conviction as a property of the investment case/business itself | Rejected | Can diverge between identically-good businesses purely on data availability — proves it tracks Atlas's evidence, not the business (§8) |
| High Conviction stated for a narrow, confident claim about an inherently unsettled outcome | Rejected | Structurally the opposite of what High requires (Known-leaning evidence) (§9) |
| Conviction as a mandatory single-computation pipeline stage (`Outlook → Conviction → Recommendation`) | Rejected | Directly contradicted by `DE-006` §5 (independent, divergent Execution Guidance Conviction) and `DE-008` §15 (existence-gate only, never a selector) (§10) |

---

## 13. Dependency Relationships

Consolidating §5 and §10 into one explicit statement, since the
deliverables ask for this separately from the narrative testing:

- **Recommendation Direction → requires → Conviction.** Mandatory,
  `DE-002` §2.6. A Direction is never stated without an accompanying
  Conviction Level.
- **Conviction → does not require → Recommendation.** Conviction attaches
  equally validly to Outlook (`DE-009` §9) or Execution Guidance (`DE-006`
  §5).
- **Conviction → does not determine → Direction.** Existence-gate only
  (`DE-008` §15, §19's "restated safeguard") — Conviction being
  *assessable* is a precondition for HOLD/NO ACTION; the assessed *level*
  never selects or restricts which Direction is chosen.
- **Conviction at one attachment point → does not derive from, and is not
  propagated to → Conviction at another attachment point.** Direction's,
  Outlook's, and Execution Guidance's Conviction Levels are each computed
  independently and MAY disagree (`DE-006` §5's "MAY be lower").
- **Conviction ↔ Expected Return: no dependency in either direction**
  (§3) — orthogonal axes, magnitude versus evidentiary quality.
- **Conviction's revision → depends on → the same named-trigger mechanism
  as the conclusion it accompanies** (`DE-002` §2.7, reused per §7) — not
  an independent schedule.

---

## 14. Open Questions

1. **A fourth conviction-shaped concept may exist beyond the three found
   in §0.** This document searched exhaustively for existing references
   but did not audit every evaluator module under `atlas/analysis_engine/`
   for additional undocumented confidence-shaped fields the way `DE-007`
   §11 specifically found `AnalysisConvictionLevel`. A brief targeted
   sweep of that kind may be worth doing before any future
   implementation-facing companion to this document is written.
2. **How many independent Conviction attachment points should the
   Decision Engine ultimately support?** §10 establishes Direction,
   Outlook, and Execution Guidance as three that already exist or are
   already adopted. Whether every future synthesis object (a hypothetical
   fourth or fifth) automatically gets its own independent Conviction, or
   whether some future object should be exempt, is not tested here.
3. **What, precisely, counts as "the same conclusion" for §4's
   fresh-assessment rule?** A Direction changing from Buy to Hold clearly
   triggers a fresh assessment. Whether a *sub-revision* of an existing
   Direction (e.g., the same Hold, restated with an updated Portfolio
   Context) requires a full fresh Conviction assessment or may reuse the
   prior one is not resolved here.
4. **§9's "honest statement of uncertainty" claims still need their own
   evidentiary bar.** This document establishes that such claims *can*
   carry High Conviction, but does not define what would make Atlas's
   characterization of "genuine, irreducible uncertainty" itself
   well-evidenced versus a disguised evasion. This risks being a gap a
   future specification should close explicitly, since it is the one
   place in this document closest to needing a rule rather than a
   principle.
5. **Naming audit, again.** Following the same pattern `DE-009` Open
   Question 1 and `DE-010` Open Question 5 already flagged for their own
   new terms: this document's own new phrase, "conclusion robustness"
   (§6, adopted only as a definition of the existing name, not a
   replacement for it), has not itself been checked against the corpus's
   naming-collision discipline, though it is not proposed as a
   user-facing or field-level term.

---

## 15. Implications for the Remaining Decision Engine

- **`DE-004` is unchanged.** Its scale, evidence patterns, and naming
  rationale all stand. This document supplies the compact ontological
  definition `DE-004` itself never stated outright, and resolves, as
  refinements rather than reversals, two places `DE-004` §6 left informal:
  the "remains high" language across a Direction change (§4, now
  precisely a fresh assessment landing at a familiar value) and the
  implicit scope of "the recommendation direction" independence claim
  (§5, now stated as an asymmetric dependency rather than full siblinghood).
- **`DE-006` §5 and `DE-008` §15 turn out to be this investigation's
  strongest evidence, not just supporting citations.** Both were written
  before this session and already encode, as binding invariants, the
  central finding this document arrives at independently: Conviction is a
  reusable, independently-computed pattern, not a case-level value or a
  chain stage. Any future Decision Engine specification introducing a new
  synthesis object that needs its own evidentiary-sufficiency rating
  should look to `DE-006` §5 as the precedent for how to attach Conviction
  to it — independently computed, allowed to diverge, never inherited.
- **`DE-009` and `DE-010` are unaffected**, and in one place strengthened:
  `DE-010` §9's flagging of "Conviction classified as a representation of
  Outlook" as a category error is now backed by this document's full,
  independent derivation (§2, §5) rather than resting on citation alone.
- **A future companion specification is implied, not started here**, for
  Open Question 2 above — a governing rule for how many, and which, future
  synthesis objects are entitled to their own independent Conviction
  attachment point, the same way `DE-006` and `DE-009` each had to settle
  this question individually for Execution Guidance and Outlook. This
  document establishes the pattern those decisions should follow; it does
  not enumerate every future case.
