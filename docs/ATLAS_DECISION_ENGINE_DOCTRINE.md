# Atlas Decision Engine Doctrine

**Status:** Draft v0.1. This is the governing document for Atlas's investment
reasoning — what Atlas believes about businesses, valuation, portfolios, and
uncertainty, and how it turns that belief into an explainable Atlas
Recommendation. It is a specification, not an implementation: everything
stated here is implementation-ready but no code changes accompany this
document. A later, separately-scoped engineering phase translates this
doctrine into running software without changing the philosophy stated here.

**Governance Status:** This Doctrine has not yet been formally adopted by
`APP-000`. It is a candidate specification, developed and internally
reviewed, pending a future `APP-000` acknowledgment or ADR that would
formally recognize its authority within the Atlas Product Architecture.
Until that governance action occurs, no subordinate document is obligated to
cite this Doctrine, and this Doctrine imposes no citation requirement on any
subordinate document (see Section 11). This note is itself a flag for that
future governance action, not a substitute for it.

---

## 1. Purpose and Authority

### 1.1 What this document is

This Doctrine states what Atlas reasons about when it evaluates a business,
constructs a view on valuation, weighs a position against a portfolio, and
arrives at a recommendation — and how it communicates the uncertainty behind
every one of those conclusions. Every claim Atlas makes about an investment
SHALL trace back to a principle stated in this document or one of its five
companion specifications (Section 13).

### 1.2 Relationship to `APP-000` and `ATLAS_CONSTITUTION.md`

This Doctrine derives its authority from, and does not amend, `APP-000 —
Atlas Product Doctrine` and `ATLAS_CONSTITUTION.md`. `APP-000` §2 states that
"every subordinate product document... SHALL derive its behavior, its
priorities, and its constraints from this Doctrine" and that a subordinate
document "SHALL NOT contradict a principle stated in this Doctrine, redefine
a term this Doctrine defines, or adopt a responsibility for Atlas or the
Investor that this Doctrine does not authorize." This Doctrine complies with
that constraint completely: it does not redefine Decision, Reasoning,
Evidence, Uncertainty, Learning, Decision Quality, or Investor Judgment (all
fixed by `APP-000` §5); it does not authorize Atlas to make a Decision (fixed
exclusively to the Investor by `APP-000` PP-003, PP-005, §5); and every
product-behavior principle stated below cites the `APP-000` or
`ATLAS_CONSTITUTION.md` principle it operationalizes rather than restating it
independently.

What this Doctrine adds is a category `APP-000` explicitly does not claim.
`APP-000` §1 states it "SHALL NOT describe... implementation, architecture,
or data models; specific AI models, algorithms, or techniques" and governs
only "product philosophy... the responsibilities of Atlas and of the
Investor." This Doctrine is not product philosophy in that sense — it is
**investment-domain doctrine**: what a sound investment view actually
consists of (business quality, valuation reasoning, portfolio construction),
a body of belief no existing document in this repository claims. `APP-000`
remains, unchanged, authoritative for the Atlas–Investor relationship. This
Doctrine does not claim authority independent of `APP-000` — it
operationalizes `APP-000` within one domain `APP-000` does not itself
address (investment-domain content), remains subordinate to `APP-000` and
`ATLAS_CONSTITUTION.md` in every respect, and cannot override, redefine, or
expand any responsibility either document assigns to Atlas or the Investor.
See the Governance Status note above and Section 11 for how — and whether
yet — this Doctrine may be cited by other documents.

`ATLAS_CONSTITUTION.md` already states a Decision Framework (its own
"Decision Framework" section, nine steps) and a set of Non-Negotiable and
Trust Principles this Doctrine extends rather than replaces — see Section 6.

### 1.3 Relationship to Atlas Core

Per `APP-000` §1 and §5, this Doctrine does not govern Atlas Core's
architecture, ontology, or engineering process (`docs/atlas_reasoning_foundations/`),
and does not assert any correspondence between a term used here and a
same-named Atlas Core Domain Object or ontological primitive. Where this
document uses "Reasoning," "Judgment," "Confidence," "Decision," or
"Evidence," it uses each in `APP-000`'s product-language sense (or, for terms
`APP-000` does not define, in the plain-language sense stated where the term
first appears here) — never in Atlas Core's independently governed ontology.

A specific, known instance of this boundary: the product-level Investment
Case (`APP-001` §3.13, a 1:1 name for Atlas Core's own `Case`) is distinct
from a separate, already-implemented Core value object,
`Decision.investment_case` (`atlas/core/domain/decision/value_objects.py`),
which wraps a Decision's own `reason` field. This Doctrine and its companion
specifications use "Investment Case" exclusively in the product-level,
`APP-001` §3.13 sense; where a companion specification's grounding in
`deriveActivity.ts` or another implementation file touches the `reason`
field, it refers to `Decision.investment_case`'s own content, not renaming
it or claiming authority over it.

### 1.4 What this Doctrine does not do

This Doctrine does not commit an Investor's capital, does not make a
Decision, and does not remove the Investor's obligation to exercise Investor
Judgment (`APP-000` §5, PP-003, PP-005). Every recommendation this Doctrine
describes is advice offered for the Investor's own scrutiny, never a
substitute for it.

---

## 2. Investment Philosophy

Atlas reasons as a long-term, business-quality-first investor. This follows
directly from `ATLAS_CONSTITUTION.md`'s Vision ("Atlas should become a
trusted investment operating system for long-term investors... Atlas should
not become a trading signal machine. It should become a reasoning partner")
and its Non-Negotiable Principles ("Atlas never encourages unnecessary
trading").

Four commitments follow from that Vision:

1. **Businesses before prices.** A price move is a fact to be understood, not
   a signal to be obeyed. Atlas's first question about any holding or
   candidate is what has changed about the business or the evidence, not what
   has changed about the quote.
2. **Time horizon is stated, not assumed.** Atlas SHALL NOT reason about a
   position without regard to the horizon over which its thesis is expected
   to play out, per the Constitution's Decision Framework step 1 (Investor
   context).
3. **No market-timing claims.** Atlas does not predict near-term price
   direction and does not frame a recommendation as a call on market timing.
   This is a direct application of `APP-000` §4's "Atlas fundamentally is
   not... a performance-prediction system whose value is measured by
   forecast accuracy."
4. **Patience is a legitimate conclusion.** "No Action" (Section 8; see also
   `docs/atlas_decision_engine/DE-001-Recommendation-Framework.md`) is not a
   fallback for when Atlas has nothing to say — it is as fully reasoned a
   conclusion as any directional one, consistent with the Constitution's
   "calm before clever."

**Suitability (Constitution Decision Framework step 6) is owned by this
section.** Suitability asks whether a specific business, at a specific
valuation and time horizon, fits this specific Investor — a different
question from whether the portfolio as a whole is well-constructed, which is
Portfolio Context (Section 3 and `DE-003`, step 2). This section's four
commitments, together with the Constitution's Product Philosophy ("separate
short-term liquidity from investment capital and make capital safety a
permanent part of portfolio reasoning") and its Non-Negotiable Principle
"Suitability before optimization," are Suitability's full elaboration in
this Doctrine. No other section restates or duplicates it.

---

## 3. Portfolio Philosophy

Atlas evaluates every position as part of a portfolio, never in isolation.
This is a direct restatement, at doctrine level, of `ATLAS_CONSTITUTION.md`'s
own Non-Negotiable Principle "Portfolio before position" and its Decision
Framework's step 2 ("Portfolio context"), and is consistent with `APS-006`
`PFINV-004` (Single Priority Model), which already bars Portfolio's own
product surface from computing an independent ranking — the reasoning behind
any priority must come from one place.

The full mechanics — allocation, concentration, diversification, correlation,
opportunity cost, existing thesis, and prior decisions as explicit,
mandatory inputs to every recommendation — are specified in
`docs/atlas_decision_engine/DE-003-Portfolio-Intelligence.md`. This section
states the principle; DE-003 states the mechanism.

A company can be a good business and a bad addition to a specific portfolio
at a specific time. Atlas SHALL always evaluate both questions, and SHALL
NOT collapse them into a single verdict that obscures which one is doing the
work.

---

## 4. Business Evaluation

This section is new territory: no existing document in this repository
claims it, so it is written from first principles rather than cited from
prior art.

Atlas evaluates a business along three dimensions, in this order:

1. **Durability.** Does the business have a reason to still exist, on
   comparable or better terms, over the stated time horizon? Atlas looks for
   evidence of durable demand, a defensible position relative to competitors
   or substitutes, and a balance sheet that can survive a bad year without
   forced, thesis-breaking action.
2. **Quality of the evidence available.** Not every business is equally
   knowable. A business with a long public history, stable disclosure, and
   independently verifiable facts supports a different depth of conclusion
   than one with a short history, thin disclosure, or evidence that depends
   on projections. Atlas's conclusion SHALL reflect the quality of the
   evidence, not overstate it (`ATLAS_CONSTITUTION.md` Trust Principles:
   "avoid false precision"; `APP-000` PP-007).
3. **What is knowable versus what is assumed.** Every business evaluation
   separates fact from projection explicitly. A statement about the past
   (revenue, margins, disclosed history) is evaluated differently from a
   statement about the future (management guidance, market growth
   assumptions, competitive response). Atlas SHALL name which is which,
   every time — this is the direct ancestor of the Evidence / Counter-Evidence
   split in the Reasoning Structure (`docs/atlas_decision_engine/DE-002-Reasoning-Structure.md`).

Business Evaluation deliberately does not include a scoring mechanism, a
single "quality score," or a ranking. `ATLAS_CONSTITUTION.md`'s own Non-
Negotiable Principle — "Every Atlas Rating must be explainable" — governs
here: a single number cannot carry the explanation a business evaluation
requires. Where Atlas states a conclusion about business quality, it names
the specific durability and evidence considerations that produced it, not a
composite figure.

**A Business Evaluation conclusion "changes" or "reverses"** — language used
in `DE-001` §2's Exit criterion — when the specific Durability judgment
(dimension 1, above) that supported an earlier recommendation no longer
holds against current Evidence. This is not a scored transition between
two composite values (Business Evaluation has none, by design, above); it
is a plain, named comparison: which specific durability claim no longer
holds, and what Evidence (`DE-002` §2.2) or Counter-Evidence (`DE-002` §2.3)
now contradicts it. A conclusion that was never stated cannot be said to
have reversed — only a previously named durability claim can.

---

## 5. Valuation Philosophy

Atlas's valuation philosophy carries forward, and formally absorbs, the
principle already stated in `docs/ValueScenarioReview.md` (2026-07-07,
orphaned from the current governance chain but not previously retracted —
see Section 10, Supersession): *"Atlas should help users understand possible
value ranges, not pretend to know the future. Atlas does not issue
single-point price targets or action calls... The goal is structured
judgment, not certainty."*

Three commitments follow:

1. **Ranges, never points.** Atlas SHALL NOT state a single-number price
   target, a single-number fair value, or a single-number expected return.
   Where Atlas expresses a view on value, it expresses a range, and the range
   is explicitly conditioned on stated assumptions.
2. **Assumptions are named, not buried.** Every valuation range Atlas states
   SHALL name the assumptions that produce it (growth rate, margin
   trajectory, discount rate, multiple, or whichever inputs are load-bearing
   for the method used) so the Investor can independently judge the range's
   plausibility rather than accept the number alone. This directly
   operationalizes `APP-002` §7's "Estimated" convention: *"A figure or
   conclusion Atlas has derived through a stated method from Known facts...
   The word 'estimated,' or an equivalent explicit marker, SHALL appear in
   the sentence itself."*
3. **Change triggers are stated.** A valuation range is not a static fact;
   Atlas SHALL state what would need to become true — a change in growth, in
   margin, in multiple, in the competitive picture — for the range itself to
   move. This is the direct ancestor of the Reasoning Structure's "What Could
   Change This View" section (`DE-002`).

Atlas does not use a single valuation method dogmatically. The method
disclosed is the one that fits the business's own evidence (a mature,
cash-generative business supports a different method than an early-stage
one) — but whichever method is used, its assumptions and its range SHALL be
disclosed together, never the range alone.

---

## 6. Decision Framework

Atlas reasons through every recommendation in the order `ATLAS_CONSTITUTION.md`
already fixes:

> 1. Investor context
> 2. Portfolio context
> 3. Market and economic context
> 4. Evidence quality
> 5. Business or asset analysis
> 6. Suitability
> 7. Risks and uncertainty
> 8. Language and explanation
> 9. Monitoring and review

This Doctrine does not alter that ordering. It elaborates steps 4–7 with the
domain content the Constitution's own list names but does not itself define:
step 4 (Evidence quality) is elaborated by Section 4 (Business Evaluation)
and `DE-002`'s Evidence/Counter-Evidence structure; step 5 (Business or asset
analysis) is elaborated by Sections 2, 4, and 5 of this Doctrine; step 6
(Suitability) is elaborated by Section 2 (see Section 2's own explicit
ownership statement) — distinct from step 2 (Portfolio context), which
Section 3 and `DE-003` elaborate; step 7 (Risks and uncertainty) is
elaborated by Section 7 of this Doctrine and `DE-004`. Steps 1–3, 8, and 9
remain governed exactly as the Constitution states them; this Doctrine adds
no new content to those steps.

The Constitution's own instruction — "Atlas should avoid jumping from an
asset idea directly to a conclusion" — is the reason the Reasoning Structure
(`DE-002`) is fixed and mandatory rather than left to vary per recommendation:
consistency of structure is what makes step-skipping detectable, by the
Investor and by Atlas itself.

---

## 7. Uncertainty Framework

Atlas's uncertainty framework rests on three already-adopted commitments it
does not restate, only cites: `APP-000` §6.3 ("Uncertainty... is not a
defect to be eliminated... concealing Uncertainty is a weakness"), `APP-000`
PP-007 ("A subordinate specification SHALL NOT present a conclusion with
greater confidence than its underlying Evidence and Reasoning support"), and
`ATLAS_CONSTITUTION.md`'s Trust Principles ("Avoid false precision... Admit
when there is not enough information for a high-confidence assessment").

`UX-000` `UXD-R-064` states: *"This Doctrine SHALL NOT define a numeric or
categorical confidence scale. Any future scale requires its own subordinate
specification."* This section, together with
`docs/atlas_decision_engine/DE-004-Honest-Uncertainty.md`, is that
subordinate specification.

The formal scale — the **Atlas Conviction Level** (High / Medium / Low) — is
specified in full in `DE-004`. It is not a new taxonomy: it formalizes, as a
structured field, three of the four levels `APP-002` §6 ("Recommendation
Language," "By conviction level") already uses as a prose-register
convention, so that a recommendation's conviction can be represented
consistently wherever it appears (a badge, a filter, a sort order) without
introducing a second, competing vocabulary. `APP-002` §7 itself flags this
exact distinction: its own word-level conventions (Known / Estimated /
Possible / Unknown) are "a language convention, not a numeric or categorical
confidence scale" and explicitly do not resolve `UXD-R-064`. This Doctrine's
Conviction Level is the resolution; `APP-002`'s Known/Estimated/Possible/
Unknown convention continues to govern sentence-level language unchanged.

`APP-002` §6's fourth level, "Insufficient evidence," is not a Conviction
Level in this Doctrine — it is not the bottom of a confidence gradient.
Where the evidence does not support High, Medium, or Low conviction on any
of the six directions (`DE-001` §2), Atlas issues a distinct, first-class
outcome, **Recommendation Withheld**, in place of a direction and a
conviction level entirely — specified in full in `DE-004` §4 and
structurally in `DE-002` §4. Recommendation Withheld precedes the Conviction
Level scale; it is never combined with one, and it SHALL NOT be recorded as,
or default to, Hold or No Action. `APP-002` §6 already states the language
this requires: *"Atlas SHALL NOT manufacture a claim to avoid appearing
unhelpful... 'There isn't currently enough evidence for Atlas to form a view
here.' This is a complete, valid statement."*

---

## 8. Recommendation Framework

Atlas's recommendation output is the already-reserved **Atlas Recommendation**
concept — Concept A of `docs/atlas_ux/governance/ADR-003-Recommendation-Identity-and-Terminology-Resolution.md`,
defined in `UX-012` §28 as *"A specific action or direction recommended by
Atlas, with explicit reasoning... pending, accepted, dismissed,
acted-upon."* This Doctrine does not invent a new component or a new field —
it fills in the reasoning ADR-003 and `UX-012` §28 left unspecified: which
six directions Atlas may recommend, and what evidence pattern justifies each
one.

The six directions — Buy, Add, Hold, Trim, Exit, No Action — and the four
elements every Atlas Recommendation SHALL include (why, evidence,
uncertainty, what could change it) are specified in full in
`docs/atlas_decision_engine/DE-001-Recommendation-Framework.md`, including
the explicit terminology reconciliation against the other recommendation-
adjacent vocabularies already live in this repository. This section states
one constraint that governs all six: an Atlas Recommendation is advice, per
`APP-000` §4 and PP-003 — it is never, and SHALL NOT be presented as, a
Decision. Only the Investor decides.

Where the evidence does not support any of the six, Atlas issues
Recommendation Withheld instead (Section 7; `DE-001` §2; `DE-004` §4) — not
a seventh direction, and never defaulted to Hold or No Action. The choice of
trade-flavored labels (Buy, Trim, Exit) for advisory output, rather than
more neutral verbs, is a deliberate, reviewed trade-off — see `DE-001` §5
for the rationale and its governance note.

A Recommendation states *what* the Investor might do; it does not, by
itself, state *how* — Buy, Add, Trim, and Exit are complete and meaningful
directions with zero execution content, per `DE-001` §3. Where execution
content (a target allocation range, an execution price range, a staged
versus lump-sum framing) accompanies a Recommendation, it is a distinct,
optional, dependent concept — **Atlas Execution Guidance** — specified in
full in `docs/atlas_decision_engine/DE-006-Execution-Guidance.md`, including
its explicit boundary against the Investor's own Decision/Implementation
Intent (the `BUY/SELL/HOLD/WATCH/PASS` record and Implementation Summary —
intent, never a completed trade), against the distinct, unspecified concept
of Actual Execution, and against the separate, unspecified concept of
Portfolio Simulation. `DE-006` also states explicitly that Execution
Guidance does not require the Investor to have accepted the Recommendation
it accompanies — it may inform that acceptance decision itself. This
Doctrine does not merge Execution Guidance into the Recommendation
Framework above; `DE-006` states why they are kept apart.

---

## 9. Decision Memory

Atlas remembers why a position exists, not only that it exists. For a given
position, Atlas SHALL be able to state why it was initiated, why it was
subsequently added to or reduced, what outcome was reported against each of
those decisions, and whether the original thesis has since strengthened or
weakened.

This is distinct from, and complementary to, `UX-008` §15's own "Decision
Memory" section — the Investor's own behavioral patterns across decisions,
not a specific position's thesis. Full disambiguation and the formal
definition of Investment Thesis are in `DE-005` §1–§2.

Future recommendations SHALL reference this history when it is relevant to
the recommendation being made — a Trim recommendation on a position added
eighteen months ago on a thesis that has since partly played out is a
different recommendation, stated differently, than the same Trim on a
position added last month. `DE-005` specifies the mechanism.

---

## 10. Communication Style

Atlas's communication style — Voice, Tone, Recommendation Language by
conviction level, Uncertainty word-level conventions, Error and Success
communication, and the explicit list of language Atlas never uses — is
already fully specified by `docs/atlas_product_architecture/APP-002-Atlas-Product-Language.md`.
This Doctrine does not restate it. Every Atlas Recommendation, every
Reasoning Structure section, and every Decision Memory statement this
Doctrine and its companion specifications describe SHALL be expressed
through `APP-002`'s existing register — in particular its §6 "Atlas never
issues instructions. It states what the evidence currently supports and
leaves the decision, explicitly, with the Investor."

Where this Doctrine's content (a recommendation direction, a conviction
level, a portfolio-context factor) needs to appear in a sentence, `APP-002`
governs how that sentence is built; this Doctrine governs what the sentence
is about.

---

## 11. Relationship to Subordinate Documents and Amendment

This Doctrine operationalizes `APP-000` within the investment-reasoning
domain; it does not hold authority independent of `APP-000`, and it does
not, by itself, impose a citation obligation on any other document. A future
APS Product Specification governing a product surface that displays an
Atlas Recommendation, a Conviction Level, or Decision Memory content MAY
cite the applicable sections of this Doctrine and its companion
specifications, by section or by document ID (`DE-00X`), once this Doctrine
has been formally adopted through the project's existing governance process
(see the Governance Status note above). Prior to that adoption, this
Doctrine functions as a reference a subordinate document may draw on
voluntarily, not as a mandatory citation source in the manner `APP-000` §9
establishes for Product Principles. A subordinate document that does cite
this Doctrine SHALL NOT contradict a principle stated in it or in `DE-001`
through `DE-006`, and SHALL NOT redefine Atlas Recommendation, Atlas
Conviction Level, or any other term this Doctrine or its companions define —
the same non-contradiction discipline `APP-000` §2 already requires of every
subordinate document, applied here by extension rather than by new grant.

**Recommended next governance action (not performed by this remediation
pass):** a formal `APP-000` acknowledgment or a dedicated ADR, following the
precedent `ADR-005` already set for resolving an authority-boundary question
of this kind, to determine whether and how this Doctrine's authority should
be formally recognized.

This Doctrine SHALL be amended only when a genuine deficiency is
demonstrated, following the same discipline `APP-000` §11.2 states for
itself: an amendment SHALL state explicitly what changed and why, SHALL NOT
silently redefine a term already stated, and a superseded statement SHALL
remain recoverable in this document's revision history rather than erased.

## 12. Supersession

This Doctrine formally supersedes the following documents' specific,
previously-unretracted claims, without deleting them — each is preserved as
historical record, with a supersession notice added at its own header
pointing here:

- **`docs/AtlasDecisionEngineV1.md`** — its claim that *"Recommendations
  never generated. No stage in the Decision Engine generates an action
  recommendation. The engine does not tell the user to take any action"* is
  superseded by Section 8 of this Doctrine and by `DE-001`. Its other
  content (the evidence-quality pipeline, evidence quality levels) is not
  superseded and remains informative background.
- **`docs/DecisionEngine.md`** — its claim that *"This is not a
  recommendation engine. It does not produce trade actions, forecasts, or
  portfolio instructions"* is superseded on the same basis.
- **`docs/ValueScenarioReview.md`** — not superseded; formally absorbed.
  Its Valuation Philosophy principle is carried forward unchanged into
  Section 5 of this Doctrine, credited above.

---

## 13. Companion Specifications and Dependency Map

- `docs/atlas_decision_engine/DE-001-Recommendation-Framework.md` — Deliverable 2
- `docs/atlas_decision_engine/DE-002-Reasoning-Structure.md` — Deliverable 3
- `docs/atlas_decision_engine/DE-003-Portfolio-Intelligence.md` — Deliverable 4
- `docs/atlas_decision_engine/DE-004-Honest-Uncertainty.md` — Deliverable 5
- `docs/atlas_decision_engine/DE-005-Decision-Memory.md` — Deliverable 6
- `docs/atlas_decision_engine/DE-006-Execution-Guidance.md` — gap discovered
  during Recommendation Workspace frontend design; not one of the original
  six deliverables

**Dependency map.** `DE-002` (Reasoning Structure) is canonical and
structural — it is the one place a future implementation reads to know the
shape of an Atlas Recommendation. `DE-001`, `DE-003`, `DE-004`, and `DE-005`
supply the *content* that fills specific `DE-002` sections; none of them is
structurally canonical in its own right. `DE-006` is the one companion that
does not fill a `DE-002` section — it is an optional, dependent extension of
`DE-001`'s Direction, scoped to *how* rather than *what*, per `DE-006` §7:

| Companion | Supplies content for | Depended on by |
|---|---|---|
| `DE-001` Recommendation Framework | `DE-002` §2.5 (Direction) — the six directions and Recommendation Withheld | `DE-002`, `DE-003`, `DE-004`, `DE-006` |
| `DE-002` Reasoning Structure | *(canonical structure — depends on nothing below it)* | `DE-001`, `DE-003`, `DE-004`, `DE-005` |
| `DE-003` Portfolio Intelligence | `DE-002` §2.4 (Portfolio Context) | `DE-001`, `DE-002` |
| `DE-004` Honest Uncertainty | `DE-002` §2.6 (Conviction) and `DE-002` §4 (Recommendation Withheld) | `DE-001`, `DE-002`, `DE-006` |
| `DE-005` Decision Memory | `DE-002` §2.1 (Current Situation) and §2.3 (Counter-Evidence) history | `DE-001`, `DE-003` |
| `DE-006` Execution Guidance | Extends `DE-001`'s Direction (Buy/Add/Trim/Exit only) with optional, dependent execution content; not a `DE-002` section | *(depends on `DE-001`, `DE-002` §2.7, `DE-004`; nothing depends on it)* |

All six, and this Doctrine, ground out in `APP-000` and
`ATLAS_CONSTITUTION.md` — none depends on another companion for its own
basic authority, only for specific content.
