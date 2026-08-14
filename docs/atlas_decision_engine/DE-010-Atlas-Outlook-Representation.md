# DE-010 — The Representation of Atlas Outlook

**Working title (as given):** ADR-002 — The Representation of Atlas Outlook
**Sprint:** Atlas Decision Engine — Sprint 1, Session 2 (Outlook track)

**Status:** Ontology investigation only, continuing
`docs/atlas_decision_engine/DE-009-Atlas-Outlook-Ontology.md` ("ADR-001").
Not yet adopted doctrine. This document does not amend `DE-009` — it takes
`DE-009`'s adopted conclusions as its starting point and does not revisit
them except where this session's own testing surfaces a genuine
contradiction, which is called out explicitly wherever it happens (there are
two, both noted as refinements rather than reversals — see §7 and the
Implications section). No implementation, algorithm, UI design, or
pseudocode accompanies this document, by explicit instruction.

---

## 0. The Distinction This Session Investigates

`DE-009` answered *what Atlas Outlook is*. This document answers a
different question: *does Outlook, having exactly one adopted ontological
shape, need to appear to the Investor as exactly one thing — or can the
same underlying concept be shown through several faces without any of those
faces becoming a second, competing ontology?*

This is not a rhetorical setup. `DE-009` §3 and §4 rejected two specific
candidates — a coequal Short-Term Outlook and Expected Return — as
**ontology**: as independently-authored beliefs Atlas would hold. The
question this session tests, rigorously and separately for each rejected
candidate, is whether the same words ("Short-Term Outlook," "Expected
Return") can survive as **representation**: a transformation of
already-adopted content into a different lens or unit, adding no new claim.
Where a candidate genuinely adds no new claim, it survives as
representation even though it was correctly rejected as ontology. Where it
would add one, rejecting it as ontology already settles the matter — a
representation layer cannot smuggle back a claim the ontology forbids by
relabeling it "just a view."

**Primary Question, answered directly, before the supporting investigation:**
Yes — Atlas can have exactly one Outlook ontology while exposing several
representations of it, **provided every representation is a strict,
traceable transformation of already-adopted ontological content, and none
of them independently authors a claim the ontology does not already
support.** That proviso is the actual test applied throughout this
document; it is not asserted as a conclusion, it is what §§1–8 test in
practice, one candidate at a time.

---

## 1. One Outlook, Two Time-Horizon Views: Testing Both Models

**Model A — genuinely two Outlooks, one per horizon.** Already tested and
rejected in `DE-009` §3: a real, independently-reasoned 6–12 month view
either restates a near-term price call (contradicting `Doctrine` §2's
no-market-timing commitment) or says nothing distinguishable from the
long-term case. This document does not re-litigate that rejection — it
holds.

**Model B — one Outlook, with a Short-Term View as a filtered
representation.** Test: does a "Short-Term View" that shows only the
**subset of the single Outlook's own already-adopted Drivers and revision
triggers (`DE-009` §6, §7) that are near-dated** add any claim beyond what
the single Outlook already contains? No — it is a strict filter over
existing content (by date), not a new synthesis. It predicts nothing; it
surfaces which of Atlas's own already-stated, evidence-grounded conditions
happen to be near in time. This passes the test stated in §0.

**Verdict: ADOPTED, asymmetrically, correcting an implicit assumption in
the question as posed.** "6–12 months" and "3–5 years" are not two peer
projections of comparable weight. There is exactly one Outlook, stated over
the Investor's full stated horizon (`Doctrine` §2, commitment 2) — this
*is* what "Long-Term View" would mean, which means Long-Term View is not a
distinct representation at all; it is simply Outlook, unfiltered, under its
own name. **Short-Term View is the only genuinely new representation here**,
and it is a narrow, non-additive filter over Outlook's own Drivers —
never an independent belief about the near term.

---

## 2. Expected Return: Precision Versus Justified Range

`DE-009` §4 rejected Expected Return as *ontology* (an authored belief) and
flagged, without fully testing, that a range might survive as a *derived
secondary display*. This session tests that flag properly.

**Test the doctrine's actual wording, precisely.** `Doctrine` §5.1: *"Atlas
SHALL NOT state a single-number price target, a single-number fair value,
or a single-number expected return."* Every prohibited case is explicitly
qualified "single-number." The user's own example of what's prohibited
("The stock will return 18.37%") is a single number stated as fact — this
is squarely, unambiguously inside the prohibition. The user's second
example ("expected return somewhere between +8% and +15%") is, on its face,
not a single number — it is a range. Read literally, `Doctrine` §5.1 does
not reach it.

**But literal non-prohibition is not the same as adoption — test it
against what the prohibition is actually protecting.** `Doctrine` §5's
governing commitment is *"Ranges, never points... Assumptions are named,
not buried"* — not "numbers are forbidden," but "**unjustified, un-sourced
precision is forbidden.**" A return range that is genuinely derived —
mechanically, transparently, with its assumptions disclosed — from the
already-adopted Valuation range (itself already required to name its
assumptions, `Doctrine` §5.2) is not new precision at all. It is the same
Valuation range, expressed in percentage-of-current-price units instead of
absolute-value units. **This is exactly the form `Doctrine` §5 already
prescribes** ("ranges, never points"), applied to a different unit of the
same content — not an exception carved out for it.

**One further test this session adds, not present in `DE-009`.** A return
range computed against the *live* current price will move every time the
quote moves, even though the Valuation range it is derived from is stable.
Does this reintroduce the near-term-reactivity problem `DE-009` §3 and §7
rejected for Outlook itself? **Test: no, for a reason specific to this
representation.** Outlook's own content (§7 below) is a *forward-looking
synthesis* that should not flicker with routine price movement, because
flickering would falsely imply Atlas's forward belief changes with every
tick. A return range is different in kind: it is a **present-tense fact**
— "how does today's price compare to an already-stated range" — not a
forward belief at all. It is no more suspect for moving with price than the
quote itself is. Distinguishing these two is itself the useful finding:
**a representation's permissible update cadence follows from what kind of
claim it is making, not from a single rule applied to everything Outlook
touches.**

**Verdict: ADOPTED as representation, rejected as ontology (unchanged from
`DE-009`).** The prohibition in `Doctrine` §5.1 targets *unjustified
precision*, not *ranges with disclosed assumptions* — a return range that
is (a) genuinely a range, never a point, (b) mechanically derived from the
already-adopted Valuation range, never independently authored, and (c)
displayed with the same assumptions the Valuation range already discloses,
survives. It is never Outlook's own authored content, and never appears
without the Valuation range's assumptions attached to it.

---

## 3. Bull, Base, Bear: Sharpening `DE-009`'s Answer

`DE-009` §5 already concluded Bull/Base/Bear are explanatory tools, not
probability-weighted futures, and that Base is simply Outlook itself
under no separate label. This session's ontology/representation
distinction lets that conclusion be stated more precisely than `DE-009`
managed to.

**Test: does a Bull or Bear scenario belong *inside* the single Outlook
object (as one of its own fields), or is it something else entirely?**
If Bull/Bear were fields *on* Outlook, a single Outlook instance would be
simultaneously describing three different assumption sets at once — which
directly contradicts `DE-009` §2.6's adopted definition of Outlook as *one*
synthesis under its own currently-best-supported assumptions. Three
assumption sets cannot be one synthesis.

**What Bull and Bear actually are, precisely stated:** each is **a
different instantiation of the identical Outlook ontology** — the same
shape, the same required content (§6 of `DE-009`: Drivers, a range, a
Conviction pairing) — constructed by feeding the same synthesis process a
different, named, plausible assumption set. There is no separate "Bull
ontology" or "Bear ontology." There is one Outlook *kind*, instantiated up
to three times (Base always; Bull and Bear each independently optional,
per `DE-009` §5), and the **Representation Layer** (§5 below) is what
chooses to display two or three instantiations side by side for
explanatory contrast.

**Verdict: REFINED, not contradicted.** Bull/Base/Bear are neither a
separate ontology, nor a component *of* Outlook, nor merely a UI
convenience — they are **multiple instantiations of the single Outlook
ontology, assembled by the Representation Layer.** This is a sharper
answer than `DE-009` gave (which left "Bull and Bear are named
deviations from Outlook" somewhat informal about *where* they live
structurally) and does not change `DE-009`'s substantive conclusion that
Base needs no separate label.

---

## 4. Classifying the Candidate Summaries

Testing each of the user's seven candidates against the same question:
does displaying this add a claim not already present in already-adopted
ontology (Outlook, `DE-009`; Conviction, `DE-004`; Portfolio Context,
`DE-003`), or is it a non-additive transformation of one?

| Candidate | Classification | Reasoning |
|---|---|---|
| Short-Term Outlook | **Derived representation** | A date-filtered view of Outlook's own Drivers/triggers (§1). Adds nothing. |
| Long-Term Outlook | **Not a distinct representation — is Outlook itself** | "Long-term" is simply Outlook stated over the full horizon; labeling it separately beside "Short-Term" implies two peers where there is one whole and one filtered lens on part of it (§1). |
| Expected Return (range) | **Derived representation** | A live, present-tense unit-conversion of the already-adopted Valuation range (§2). Never independently authored. |
| Bull / Base / Bear | **Representation-layer technique, not a candidate in its own right** | Multiple instantiations of the one Outlook ontology, assembled for display (§3). Not itself a "summary" alongside the others — it's how several summaries get shown together. |
| Conviction | **Category error in the candidate list, not a representation of Outlook at all** | Conviction (`DE-004`) is an independently-adopted sibling concept that *accompanies* Outlook (`DE-009` §9, directly extending `DE-004` §6's rule for Recommendation). It is never a "view" derived *from* Outlook's content — collapsing it into "a representation of Outlook" would violate the exact "stated together, never collapsed into one combined signal" rule `DE-009` §9 adopted. It belongs beside the representation set, not inside it. |
| Case Momentum | **Points to a genuine, currently unadopted ontological gap** | Test in §7 below: this term is only meaningful if Outlook has a persisted sequence of past instances to compare against — which `DE-009` did not establish. Not classifiable as "representation" yet, because there is nothing settled to derive it from. Flagged, not adopted — see §7 and Open Question 1. |
| Key Drivers | **Already-adopted ontology, not a new representation** | This is `DE-009` §6's Drivers, verbatim. Surfacing it for display requires no transformation — it is already the pointer-shaped content `DE-009` defined. |

**Grep confirmation performed for this document:** none of "Decision
Delta," "Attention Engine," or "Case Momentum" appear anywhere in this
repository's governed documents outside this session's own prompt — all
three are genuinely new terms, not prior art this investigation is
implicitly relying on. Case Momentum is addressed in §7; Decision Delta
and Attention Engine are addressed, and explicitly left unresolved, in §8.

---

## 5. Does Representation Deserve to Be an Architectural Layer?

**Test against already-adopted precedent, rather than reasoning from
scratch.** `Doctrine` §3 already states, for a structurally identical
problem in a different content type: *"consistent with `APS-006`
`PFINV-004` (Single Priority Model), which already bars Portfolio's own
product surface from computing an independent ranking — the reasoning
behind any priority must come from one place."* The problem Single
Priority Model solves — multiple surfaces each independently computing
their own version of the same underlying judgment, risking silent
divergence — is exactly the problem a missing Representation Layer would
create for Outlook: five surfaces (Investment Brief, Portfolio, Watchlist,
Daily Brief, Companion) each writing their own ad hoc summary of the same
Outlook object, with no shared discipline forcing them to agree.

**Verdict: YES, by direct analogy to an already-adopted principle**, not by
new reasoning. Representation SHALL exist as a single, shared
transformation step between the one Outlook ontology and every surface
that displays it — never duplicated per surface.

**One precision this document adds, since the question is easy to
over-answer.** "Representation Layer" being adopted as an architectural
answer does not mean it is a new *ontological* layer — it introduces no new
kind of thing that exists in the world, the way Outlook, Recommendation, or
Conviction each do. It is a **process constraint** ("this transformation
happens once, not five times"), not a new domain concept. Conflating the
two would be a category error in the opposite direction from Conviction's
in §4 — where Conviction is ontology mistakenly treated as if it were a
representation, "Representation Layer" is architecture correctly *not*
elevated to ontology it doesn't need to be.

---

## 6. Product Consistency: Conceptual Integrity, Not UX

**Test, not from a UX preference, but from what divergence would actually
prove.** Suppose Portfolio displayed "Outlook: improving" for a given
Case while Daily Brief simultaneously displayed "Outlook: stable" for the
*same* Case, at the same moment. This is not a cosmetic inconsistency to
be smoothed over by a style guide. It is **direct, observable evidence
that there were never really "one Outlook" in practice** — there were two
(or five) independently-computed things sharing a label, which is exactly
the hidden ontological multiplication `DE-009`'s entire discipline
("prefer the smallest model," reject invented parallel concepts) exists to
prevent. An ontology that claims "there is exactly one Outlook" is only
actually true if every consumer of it is provably reading the same
instance — anything else falsifies the claim regardless of what this or
`DE-009` states on paper.

**Verdict: ADOPTED, for a reason stronger than coherence-as-a-nicety.**
Uniform representation across surfaces is not a design preference — it is
the **only available external test** of whether the one-Outlook ontology
actually holds in the running system. Divergent per-surface summaries
would not just look inconsistent; they would be empirical proof the
ontology had been silently violated somewhere upstream, which makes this
a conceptual-integrity question exactly as the user's framing insists,
not a UX one wearing an ontology costume.

---

## 7. Identity Over Time: Does Outlook Change, or Does Atlas Restate It?

This is the sharpest open question `DE-009` left informal (§7 there used
"Outlook is restated" without settling what "restated" means for the
object's identity), and it is worth treating as a genuine philosophical
question, not a wording choice.

**Model A — Outlook is one persisting, mutable object.** "The Outlook"
names a single continuous thing whose *content* changes over time while
its *identity* (which Outlook this is) stays fixed — like a variable being
reassigned. Under this model, there is no natural way to ask "how has the
Outlook changed over the last six months," because a mutable object has no
memory of its own prior states unless something external separately logs
them.

**Model B — Outlook is a series of immutable, dated instances.** Each time
a named Driver fires (`DE-009` §7), Atlas produces a *new* Outlook
instance; past instances are retained, unedited, as historical record; "the
current Outlook" means "the most recent instance in this Case's Outlook
history."

**Test against already-adopted precedent, again rather than reasoning from
nothing.** `DE-005` §1 already resolves the structurally identical problem
for Investment Thesis: *"a position's thesis is not a separately recorded
object; it is the accumulated set of `reason` statements across that
position's own Decision history"* — each individual statement *"captured...
at the time a Decision was made, never reconstructed after the fact."*
This is Model B, already adopted for a sibling concept. Applying it to
Outlook by the same direct analogy `DE-009` used repeatedly for other
questions: Outlook should be Model B as well — a **type**, not a single
mutable **token** — with each instance immutable once created.

**Verdict: ADOPTED, as a refinement of `DE-009` §7, not a contradiction of
it.** `DE-009` §7 already established Outlook is event-driven, restated
when a named trigger fires, rather than static or continuously
recomputed — that conclusion holds unchanged. What this session adds is
the precise identity semantics `DE-009` left implicit: **the ontology
describes the shape every Outlook instance takes, not a single mutable
object.** "Outlook changes" is loose language for "Atlas produces a new,
dated Outlook instance and retains the old one," exactly paralleling how
`DE-005` already treats Decision and Outcome records.

**This directly resolves Case Momentum (§4).** Under Model A, momentum is
uncomputable — there is nothing to compare against. Under Model B (now
adopted), momentum becomes a well-defined, honestly-derivable
representation: a comparison between the current Outlook instance and one
or more prior instances for the same Case, evaluated the same
non-scored, plainly-stated way `DE-005` §1 already evaluates thesis
strength ("stated as a plain comparison against named claims, never as a
score"). Case Momentum is therefore **provisionally reclassified from
"unresolved gap" (§4) to "a well-founded derived representation, once
Outlook's persisted-history requirement (this section) is itself
adopted."** It remains a genuine open item — see Open Question 1 — because
that persisted-history requirement is new content this document is
introducing, not something `DE-009` already established, and it deserves
its own explicit adoption rather than being smuggled in as a side effect
of answering Case Momentum's classification question.

---

## 8. Should Outlook Become the Central Synthesis Object?

**Test the proposed architecture directly against `DE-009` §8's already-
tested conclusion, using the identical counter-example.** `DE-009` §8
tested — and rejected — a mandatory dependency between Outlook and
Recommendation in either direction, using a concrete case: a Trim
recommendation justified purely by portfolio concentration (`DE-001` §2's
own stated evidence pattern), where the business's forward trajectory is
completely unchanged. The proposed architecture in this session's Question
8 — `Business Evaluation, Valuation, Evidence, Reasoning → Outlook →
Recommendation → ...` — makes Outlook a **mandatory upstream stage**
Recommendation must pass through. Applying the same counter-example: a
pure-sizing Trim would have to pass through an Outlook step that has
nothing relevant to say about it (Outlook is about business trajectory,
`DE-009` §2.6, not position sizing, which is Portfolio Context's domain,
`DE-002` §2.4). Forcing it through anyway means either Outlook silently
absorbs portfolio-sizing content it does not ontologically own — violating
`DE-009`'s own "smallest model" discipline by conflating two things `DE-002`
already keeps separate — or the pipeline produces an empty, vacuous
Outlook step for a fully valid Recommendation, which misrepresents that
Recommendation as though it always carries a business-trajectory story.

**Verdict: REJECTED as a mandatory pipeline**, on the same grounds, using
the same counter-example, that already settled `DE-009` §8. This is not a
new finding — it is the existing finding, re-confirmed by direct
application to the newly-proposed architecture, exactly as the user's own
instruction (*"reject candidates through contradiction"*) requires when a
new proposal collides with an already-tested conclusion.

**Testing whether a weaker version survives.** Setting aside strict
causal ordering, is there value in Outlook and Recommendation being
jointly exposed as **the** canonical pair every downstream surface reads,
without either being computed *from* the other? Test: this is not a new
claim — it is §5 and §6's already-adopted Representation Layer conclusion,
restated with two objects (Outlook, Recommendation) instead of one. It
survives for the same reason: it prevents silent per-surface divergence,
without requiring either object to depend on the other's existence.
**Verdict: this weaker form is consistent with everything already
adopted** — Outlook and Recommendation are siblings that are *jointly*,
not *sequentially*, the canonical synthesis pair.

**Decision Delta and Attention Engine.** Both terms are introduced for the
first time in this session's prompt and do not appear anywhere in this
repository's governed corpus (confirmed by direct search, §4). Testing an
undefined term against adopted doctrine is not possible — there is nothing
stated about what either concept claims to be, so no contradiction test
can be run. **This document does not adopt, reject, or define either term.**
Per the investigation's own standing instruction to flag uncertainty rather
than guess, both are recorded as **out of scope**, requiring their own
ontology investigation — the same discipline that produced `DE-009` as its
own document rather than deciding Outlook informally inside the master
Doctrine.

---

## 9. Adopted Representation Model

```
Atlas Outlook (ontology, DE-009 — one kind, immutable dated instances, §7)
  │
  ├── instantiated once under Atlas's currently best-supported
  │   assumptions ("Base" — no separate label, DE-009 §5)
  │
  ├── optionally instantiated again under a named, plausible
  │   alternative assumption set ("Bull") — independently optional
  │
  └── optionally instantiated again under a different named,
      plausible alternative assumption set ("Bear") — independently
      optional

        ↓ (shared, single transformation step — §5)

Representation Layer  (architecture, not new ontology)
  │
  ├── Short-Term View          — date-filtered subset of Outlook's own
  │                               Drivers/triggers (§1) — never a new claim
  ├── Expected Return (range)  — live, present-tense unit-conversion of
  │                               the already-adopted Valuation range (§2)
  ├── Bull / Base / Bear       — multiple Outlook instantiations shown
  │                               together for explanatory contrast (§3)
  ├── Key Drivers              — Outlook's own already-adopted pointer
  │                               content (DE-009 §6), displayed as-is
  └── Case Momentum            — comparison across successive Outlook
                                  instances (§7) — provisional, pending
                                  Open Question 1

        ↓ (consumed identically by every surface — §6)

Investment Brief · Portfolio · Watchlist · Daily Brief · Companion
```

**Explicitly not part of this model, and why:**

- **Long-Term View** does not appear as a distinct box — it is Outlook
  itself, unfiltered (§1).
- **Conviction** does not appear inside the Representation Layer — it is a
  sibling ontological concept (`DE-004`) displayed *alongside* Outlook's
  representations, never derived *from* Outlook's own content (§4, §9's
  category-error note).
- **Recommendation** does not appear beneath Outlook in this diagram — the
  two are joint, not sequential (§8); Recommendation has its own,
  separately governed representation, unaffected by this document.

---

## 10. Rejected Alternatives (Summary)

| Candidate | Verdict | Reason |
|---|---|---|
| Genuinely independent Short-Term Outlook (a second belief, not a filtered view) | Rejected (unchanged from `DE-009`) | Either restates a near-term price call or says nothing new (§1) |
| Long-Term Outlook as a distinct representation, peer to Short-Term | Rejected | It is Outlook itself, not a second view; treating it as a peer implies two objects where there is one whole and one filtered lens on part of it (§1) |
| Expected Return as a single-number, independently authored figure | Rejected (unchanged from `DE-009`) | Directly and unambiguously inside `Doctrine` §5.1's prohibition (§2) |
| Expected Return range, un-sourced (no disclosed assumptions) | Rejected | Would reintroduce false precision through the back door — the range must inherit the Valuation range's own disclosed assumptions (§2) |
| Bull/Base/Bear as fields on a single Outlook instance | Rejected | One Outlook instance cannot describe three assumption sets at once without contradicting `DE-009` §2.6's "one synthesis" definition (§3) |
| Bull/Base/Bear as probability-weighted futures | Rejected (unchanged from `DE-009`) | Reintroduces an implied single expected value (§3, citing `DE-009` §5) |
| Conviction classified as a "representation of Outlook" | Rejected | Category error — an independently-adopted sibling concept, not derived from Outlook's content (§4, §9) |
| Representation Layer as a new ontological layer (a new kind of thing) | Rejected | It is a process constraint (share the transformation), not a new domain concept — conflating the two is the mirror-image error of misclassifying Conviction (§5) |
| Outlook as mandatory upstream stage of Recommendation | Rejected | Same counter-example that already settled `DE-009` §8 (a pure portfolio-sizing Trim) applies unchanged to the newly-proposed pipeline (§8) |
| Decision Delta / Attention Engine, defined or adopted in this document | Not resolved — explicitly out of scope | Undefined anywhere in this corpus; no contradiction test is possible against an undefined term (§8) |
| Case Momentum, adopted outright without qualification | Not resolved — provisionally reclassified, pending Open Question 1 | Only well-defined once Outlook's persisted-instance-history requirement (§7) is itself formally adopted, which this document raises but does not finalize (§7) |

---

## 11. Open Questions

1. **Outlook's persisted-history requirement needs its own explicit
   adoption.** §7 adopted Model B (immutable, dated Outlook instances) by
   direct analogy to `DE-005`'s treatment of Decision/Outcome records, and
   §7/§9 built Case Momentum on top of that adoption. This is new content
   relative to `DE-009`, which left "restated" informal. Before Case
   Momentum can be treated as settled, this persisted-history model
   deserves the same explicit, standalone scrutiny `DE-009` gave Outlook's
   core definition — this document raises it in service of a different
   question (representation) and should not be read as having fully
   settled it as ontology in its own right.
2. **Decision Delta and Attention Engine remain completely undefined.**
   §8 declines to guess. If either is intended to sit between Outlook/
   Recommendation and the downstream surfaces (as the user's Question 8
   diagram suggests), that is a third ontology investigation this document
   does not perform.
3. **How many past Outlook instances should Case Momentum compare
   against, and over what standing?** `DE-005` §1 evaluates thesis strength
   as a plain comparison against named claims, never a score — the same
   discipline should presumably govern Case Momentum once adopted, but
   whether it compares against the immediately-prior instance only, or a
   longer window, is untested here.
4. **Does the Representation Layer's "single shared transformation"
   requirement (§5) imply anything about where Bull/Bear instantiations are
   computed versus merely displayed?** §3 and §9 establish that Bull/Bear
   are separate Outlook instantiations, and §5 establishes representation
   must be shared, not per-surface — but whether *instantiating* a
   Bull/Bear scenario counts as part of "Outlook" (upstream of
   representation) or part of "Representation" (a display-time choice to
   compute and show one) was not tested to a clean boundary. This affects
   where the single-source-of-truth discipline of §5/§6 actually needs to
   bind, and is worth resolving explicitly before implementation.
5. **Naming, again.** `DE-009` Open Question 1 already flagged that "Atlas
   Outlook" itself has not been checked against this corpus's naming-
   collision discipline. This session adds "Representation Layer,"
   "Short-Term View," and "Case Momentum" to that same unchecked list.

---

## 12. Implications for the Future Atlas Decision Engine

- **`DE-009` is refined, not amended, in two places**, both already called
  out inline: §3 sharpens where Bull/Bear structurally live (representation-
  layer instantiations of one ontology, not an informal "deviation" from
  it), and §7 gives precise identity semantics (immutable dated instances,
  Model B) to what `DE-009` §7 left as the word "restated." Neither changes
  `DE-009`'s adopted conclusions; both make them more precise.
- **A Representation Layer is now implied as a real architectural
  component**, grounded in the same Single Priority Model precedent
  (`APS-006` `PFINV-004`, cited via `Doctrine` §3) already adopted for a
  different content type. Any future implementation-facing specification
  for Outlook should treat "one shared transformation, consumed by every
  surface" as a requirement, not a nice-to-have, per §5's reasoning and
  §6's stronger conceptual-integrity argument for it.
- **`DE-005` (Decision Memory) supplies a second precedent this session
  relied on directly** — its immutable, dated Decision/Outcome record
  model is the template §7 adopted for Outlook's own identity-over-time
  question. `DE-005`'s own content is unaffected; this is a citation, not
  an amendment.
- **A genuinely new, small ontological commitment is now on the table**
  (Open Question 1): Outlook needs a persisted sequence of past instances,
  not just a current state, for Case Momentum and for `DE-009` §7's
  "restated" language to mean anything precise. This is worth its own
  short, focused adoption before any implementation-facing specification
  is written, the same way this document itself was kept separate from
  `DE-009` rather than folded in as an afterthought.
- **Decision Delta and Attention Engine are flagged, not started.** Any
  future work that wants to place either concept in the architecture
  should treat that as a new ontology investigation in this same family,
  not an extension smuggled into an implementation spec.
