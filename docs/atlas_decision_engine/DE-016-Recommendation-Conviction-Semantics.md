# DE-016 — Recommendation Conviction Semantics

**Status:** ADOPTED — Alpha. Clarification subordinate to `DE-011` (Atlas
Conviction Ontology), which adopted Conviction's ontology without
resolving three concepts its own definition depends on: what makes
uncertainty *material*, what a *capability gap* is, and which kinds of
open question may bear on Conviction at all. `DE-011` §14 lists five
unresolved open questions and names none of these three — they are
genuine silence, not answered inconsistently. This document closes that
silence as `DE-011`'s sixth open question. It reverses nothing. It
redefines nothing. Every boundary `DE-001`, `DE-002`, `DE-004`, `DE-008`
and `DE-011` already adopted is treated as fixed here. Documentation only
— no code, frontend, or backend accompanies this specification, and none
is implied to exist yet.

---

## 1. Title

**Recommendation Conviction Semantics** — what Atlas Conviction measures,
what it does not measure, and which facts about a company, an investor's
evidence, and Atlas's own analytical capability are entitled to move it.

---

## 2. Status

**ADOPTED — Alpha.**

The decision is: **Conviction is evidentiary and conclusion-relative;
Atlas's own analytical capability is not a Conviction input and belongs
to the readiness layer.**

This formalises what `DE-004` §3, `DE-002` §2.3 and `DE-011` §11 already
imply but never stated as a rule. It is adopted as a clarification
because the governing corpus does not conflict with itself — the concepts
below were left undefined, and an undefined space was filled by default
rather than by decision.

---

## 3. Purpose

### 3.1 What Conviction measures

> **Atlas Conviction measures the evidentiary robustness of one specific,
> currently-stated Atlas conclusion under material uncertainty.**

This restates `DE-011` §11's adopted ontology in the vocabulary this
document defines below. It adds no new scale, no new level, and no new
attachment point.

### 3.2 What Conviction does not measure

Conviction SHALL NOT be read as, or computed from, any of the following:

- **Business quality.** That is Business Evaluation's subject
  (`Doctrine` §4). `DE-011` §12 already rejected "belief in the business."
- **Atlas implementation maturity.** Whether Atlas has built, wired, or
  executed a given analytical capability is a fact about Atlas, not about
  the conclusion. See §8.
- **Analytical completeness.** How much of Atlas's total possible
  analysis has been performed is Coverage's and the readiness layer's
  subject, divided as §9 and §10 specify.
- **Recommendation popularity or agreement.** `DE-011` §12 already
  rejected "belief in the recommendation"; `DE-008` §15 forbids
  Conviction from determining or restricting Direction.
- **Confidence in the reasoning process.** `DE-011` §12 rejected "belief
  in the reasoning (process soundness)" explicitly: `DE-004` §3's
  patterns rate the conclusion, never the process that produced it.
- **Confidence in Atlas itself.** Conviction is attached to one stated
  conclusion and is meaningless as a general self-assessment.

### 3.3 Why the distinction is load-bearing

A rating that moves when Atlas ships an engine, rather than when evidence
about the company changes, is not a rating of the evidence. It also fails
`DE-011` §7's revision rule, which binds Conviction to change *exactly
when the evidentiary landscape for its specific conclusion changes
materially, and not otherwise*.

---

## 4. Governing References

This document clarifies, and does not replace:

- **`DE-001`** — Recommendation Framework. Source of the "materially
  strengthened nor materially weakened" language §5 generalises.
- **`DE-002`** — Reasoning Structure. Source of the Counter-Evidence
  definition (§2.3), the "no material counter-evidence was found"
  formulation, the prohibition on completeness theatre, and §2.4's rule
  that Portfolio Intelligence factors are "not all seven restated by rote
  every time."
- **`DE-004`** — Honest Uncertainty. Source of the three levels and their
  evidence patterns, including High's explicit tolerance of minor
  Counter-Evidence and §4's placement of Withheld *before* the scale.
- **`DE-008`** — Direction Selection. Source of §15's invariant that
  Conviction gates a Direction's existence but never selects or restricts
  it.
- **`DE-011`** — Atlas Conviction Ontology. Source of the adopted
  ontology (§11), the property-of-Atlas's-understanding finding (§8), the
  revision rule (§7), the dependency rules (§13), and the rejected
  interpretations (§12).

Where this document and any of the above appear to differ, the above
governs and this document is in error.

---

## 5. Conviction Ontology

Each definition below is normative. None describes an implementation.

**Conviction.** A categorical (High / Medium / Low) rating of how robustly
one specific, currently-stated Atlas conclusion is supported by the
evidence and counter-evidence Atlas currently holds about the subject of
that conclusion, evaluated fresh for whatever conclusion it accompanies.

**Counter-Evidence.** Facts that cut against the conclusion being reasoned
toward. Counter-Evidence and *Contradicting Evidence* are the same
concept under two names; this document treats them as equivalent and
prefers "Counter-Evidence." Per `DE-002` §2.3, Counter-Evidence SHALL be
genuine, specific and conclusion-relative — never a token counter-point
included to appear balanced.

**Material Counter-Evidence.** Counter-Evidence which, taken at face
value, could reasonably alter or invalidate the current conclusion. See
§6.

**Material Open Question.** An unresolved question whose answer could
reasonably alter, materially weaken, or invalidate the currently stated
conclusion. A question that cannot be shown to bear on the conclusion is
not material, however important it may be in general.

**Evidential Uncertainty.** Uncertainty arising from the evidence and
counter-evidence Atlas currently holds about the subject of the
conclusion under evaluation. It includes missing investor evidence,
contradictory evidence, unresolved evidence, incomplete corroboration,
and analysis that ran to completion and returned a genuinely mixed
result. It excludes Capability Gaps.

**Capability Gap.** An unresolved question caused by Atlas lacking, not
having executed, or not yet integrating an analytical capability, rather
than by evidence currently held about the subject of the conclusion. See
§8.

**Known Unknown.** A structural inventory entry naming something Atlas
has established it does not know. A Known Unknown is a disclosure
obligation, not a Conviction input; whether any particular Known Unknown
also constitutes Evidential Uncertainty is decided by §7's partition, not
by its membership in the inventory.

**Analytical Uncertainty.** The state of an analysis that ran and did not
reach a conclusive result. It divides into two kinds that SHALL NOT be
conflated: *complete but mixed*, where the analysis executed fully and
the answer is genuinely undetermined, which is Evidential Uncertainty;
and *insufficient input*, where the analysis could not run for want of
data, which bears on Coverage.

**Investor Information Gap.** A claim the Investor has recorded but not
corroborated, or a claim the Investor has not recorded at all. This is
Evidential Uncertainty and bears on Conviction through Coverage.

**Workflow State.** A fact about whether a process has been performed —
evaluated, monitored, refreshed, reviewed. Workflow State is never
Evidential Uncertainty and never bears on Conviction.

---

## 6. Materiality

Materiality is already invoked normatively three times in the governing
corpus — `DE-001` ("materially strengthened nor materially weakened"),
`DE-002` §2.3 ("no material counter-evidence was found"), and `DE-011` §7
("changes materially") — and defined in none of them. `DE-004` §3 relies
on the same idea in different words: Counter-Evidence at High must be
"minor" and must not "meaningfully undermine the conclusion." This
section supplies the missing definition.

**Materiality is categorical and conclusion-relative.**

> **Material Counter-Evidence is evidence which, taken at face value,
> could reasonably alter or invalidate the current conclusion.**

Three consequences follow.

**6.1 Conclusion-relative.** The same fact may be material to one
conclusion and immaterial to another. Materiality SHALL always be
assessed against the specific conclusion Conviction accompanies, never
against the company in general, and never once for all conclusions about
a company.

**6.2 Taken at face value.** Materiality SHALL be judged by assuming the
Counter-Evidence is true and asking whether the conclusion survives.
Atlas SHALL NOT discount Counter-Evidence as immaterial on the grounds
that it is probably wrong; that is a judgement about the evidence's
quality, which belongs in the assessment of the evidence itself.

**6.3 No quantification.** Materiality SHALL NOT be expressed as a score,
a percentage, a probability, a weight, or a numeric threshold. `DE-004`
§5 already rejected numeric Conviction scales for the false-precision
problem they reintroduce; a numeric materiality bar would reintroduce it
one level down.

Where materiality genuinely cannot be determined for a specific piece of
Counter-Evidence, that Counter-Evidence SHALL be treated as material.
Understating uncertainty is the more damaging error.

---

## 7. Open Question Partition

"Open Question" is an umbrella term, not a single normative category. Two
structurally different kinds of unresolved question have historically
shared the word. This section partitions every category and assigns each
exactly one canonical owner.

**A question's category is determined by what caused it, never by where
it is stored or what it is called.**

| Category | Canonical owner | Affects Conviction? | Affects Coverage? | Affects Readiness? | In Canonical Reasoning? |
|---|---|---|---|---|---|
| Counter-Evidence | Conviction | **Yes, if material** | No | No | Yes |
| Evidential Uncertainty (unresolved evidence) | Conviction | **Yes, if material** | No | No | Yes |
| Investor Information Gap | Coverage | Yes, through Coverage | **Yes** | No | Yes |
| Analytical Uncertainty — complete but mixed | Conviction | **Yes, if material** | No | No | Yes |
| Analytical Uncertainty — insufficient input | Coverage | Through Coverage only | **Yes** | No | Yes |
| **Capability Gap** | **Readiness layer** | **No** | **No** | **Yes** | **Yes, as disclosure** |
| Workflow State | Readiness layer | No | No | **Yes** | No |
| Monitoring State | Readiness layer | No | No | **Yes** | No |
| Portfolio-context gap | Readiness layer while unimplemented; reclassified per §11 once implemented | No | No | **Yes** | Yes, as disclosure |

Every category has exactly one canonical owner. A single fact MAY be
disclosed in more than one place, but SHALL be *owned* by exactly one.

---

## 8. Capability Gaps

**8.1 Definition.** A Capability Gap is an unresolved question caused by
Atlas lacking, not having executed, or not yet integrating an analytical
capability, rather than by evidence currently held about the subject of
the conclusion.

**8.2 Rules.**

- Capability Gaps **SHALL NOT** reduce Conviction.
- Capability Gaps **SHALL** remain visible. Suppressing them would trade
  one dishonesty for another; Atlas SHALL continue to state plainly what
  it cannot assess.
- Capability Gaps **SHALL** belong to the readiness layer, which is their
  canonical owner.
- Capability Gaps **SHALL NOT** become drivers of a Direction.
- Capability Gaps **SHALL NOT** become part of What Would Change. Atlas
  gaining a new engine is not the investment thesis changing.
- Capability Gaps **SHALL NOT** be interpreted as Counter-Evidence. The
  absence of an analysis is not a fact that cuts against a conclusion.

**8.3 Rationale.** Three independent grounds, each sufficient.

*It carries no conclusion-specific information.* A Capability Gap is
identical for every company and every conclusion Atlas states. `DE-011`
§11 requires Conviction to be "evaluated fresh for whatever conclusion it
accompanies"; a signal that cannot differ between two conclusions cannot
discharge that requirement. This is not a general objection to universal
signals — a universal signal that carried conclusion-specific information
would be admissible. A Capability Gap carries product-state information
only.

*It violates the revision rule.* `DE-011` §7 binds Conviction to change
exactly when the evidentiary landscape for its conclusion changes
materially. If Capability Gaps were Conviction inputs, shipping an engine
would move Conviction for every company at once, with no evidence about
any of them having changed — precisely the untriggered revision §7
forbids.

*It is completeness theatre.* `DE-002` §2.3 forbids populating
Counter-Evidence "for the appearance of completeness," and §2.4 requires
Portfolio Intelligence factors to be "not all seven restated by rote every
time, but whichever ones actually inform the direction." A fixed roster of
not-yet-assessable dimensions recited identically for every company is the
pattern both rules exist to prevent.

**8.4 Distinction from genuine inconclusiveness.** A Capability Gap is
*"Atlas has not analysed this."* A complete-but-mixed analytical result is
*"Atlas analysed this and the answer is genuinely undetermined."* The
second is Evidential Uncertainty and MAY reduce Conviction where material.
Similarity of wording between the two SHALL NOT be treated as evidence
that they are the same category.

---

## 9. Coverage

> **Coverage answers how much of the relevant evidentiary landscape has
> been examined.**

Coverage does **not** answer how complete Atlas itself is. Analytical
capability completeness is not Coverage's subject and SHALL NOT be folded
into it.

Coverage and Conviction are separate and SHALL remain so:

> **Coverage determines how much of the relevant evidentiary landscape has
> been examined; Conviction determines how robustly that examined
> landscape supports the stated conclusion.**

Full Coverage means the Investor's recorded claims bearing on the
conclusion have been examined. It establishes **eligibility** for high
Conviction; it never establishes high Conviction itself. An examined
landscape may still contain material Counter-Evidence.

---

## 10. Decision Support and the Readiness Layer

Two distinct concepts have shared the phrase "Decision Support." This
document keeps them apart.

**Decision Support Level** retains its existing, narrow meaning: *does
current evidence support taking action?* It is not a maturity concept and
SHALL NOT absorb one.

**The readiness layer** owns:

- implementation maturity — what Atlas can and cannot currently assess;
- workflow state — what has and has not yet been performed;
- analytical capability — which engines exist, are wired, and have run.

**Conviction** owns recommendation robustness, and only that.

This assignment introduces no new domain concept. The readiness layer
already expresses facts of exactly this kind; Capability Gaps are the
same kind of fact and belong with them.

---

## 11. Conviction Levels

These definitions are doctrinal restatements of `DE-004` §3 and §4 in this
document's vocabulary. They change no level, no name, and no boundary.

**WITHHELD.** Conviction is not assigned. Either no conclusion exists for
a Conviction to qualify, or the evidence does not support even a
Low-conviction conclusion. Per `DE-004` §4, Withheld precedes the scale
rather than occupying its bottom, and SHALL NOT be described as low
Conviction.

**LOW.** The evidence bearing on the conclusion is thin, mixed, or largely
inferential — resting more on estimated or possible content than on known
fact — or substantial unresolved material Counter-Evidence stands against
it. Incompleteness alone does not make a conclusion Low; insufficiency
does.

**MEDIUM.** The evidence meaningfully supports the conclusion, but at
least one genuine, specific, conclusion-relevant uncertainty remains
unresolved and could reasonably alter or materially weaken it. This
includes material Counter-Evidence and material open questions alike, and
includes an analysis that ran to completion and returned a genuinely
mixed result.

**HIGH.** The evidence bearing on the conclusion is extensive, consistent
and directly supportive; the Investor's recorded claims bearing on it have
been examined; and no material Counter-Evidence and no material open
question remains unresolved.

**HIGH explicitly admits minor Counter-Evidence.** Per `DE-004` §3, "Counter-
Evidence, if any, is minor and does not meaningfully undermine the
conclusion." High SHALL NOT require the absence of all Counter-Evidence,
and SHALL NOT require the absence of all unresolved questions. It requires
the absence of *material* ones.

Capability Gaps bear on none of the four levels.

---

## 12. Future Engines

**Introducing a new analytical engine SHALL NOT change Conviction merely
because the engine now exists.**

Only evidence generated by that engine, and only insofar as it materially
bears on the specific conclusion, may change Conviction.

This rule is symmetric and SHALL be applied in both directions:

- An engine's **absence** SHALL NOT lower Conviction.
- An engine's **arrival** SHALL NOT raise Conviction.
- An engine's **neutral finding** SHALL NOT change Conviction.
- An engine's **material finding** SHALL change Conviction, in whichever
  direction the finding supports.

Without this rule, Conviction degrades whenever Atlas expands: every new
engine would introduce a new not-yet-assessable dimension before it
introduced any answers. A rating that falls as the system improves is
measuring the system, not the evidence.

---

## 13. Future Compatibility

Every future analytical capability follows the same ownership model. No
capability is exempt, and none requires a variant rule.

- **Business Durability.** While unimplemented, its unavailability is a
  Capability Gap owned by the readiness layer. Once implemented, its
  findings are business evidence and bear on Conviction exactly to the
  extent they are material to the stated conclusion.
- **Portfolio Intelligence.** Each of the seven factors is governed
  individually. An unimplemented factor is a Capability Gap. An
  implemented factor bears on Conviction only where its result is
  material to the conclusion — consistent with `DE-002` §2.4's rule
  against reciting all seven by rote.
- **Industry Intelligence**, **Macro Intelligence**. Identical treatment.
  Their arrival SHALL NOT alter Conviction for any existing conclusion
  absent new material findings.
- **Decision Memory.** Prior Decisions and Outcomes bear on Conviction
  only where they constitute evidence or counter-evidence material to the
  current conclusion. Their mere existence, count, or age does not.
- **Investor Lab.** Synthetic or exploratory data SHALL NOT influence
  production Conviction unless and until it is explicitly promoted into
  genuine evidence.

---

## 14. Non-goals

DE-016 does not define, and SHALL NOT be read as defining:

- any implementation, wiring, module, or data structure;
- any algorithm for computing Conviction;
- any threshold, score, weight, percentage, or probability;
- any user interface, label, or presentation rule;
- any benchmark scoring rule;
- confidence percentages of any kind;
- numeric materiality.

Nor does it create a new domain object, a new authority tier, or a new
Conviction attachment point. `DE-011` §14's second open question — how
many attachment points the Decision Engine should ultimately support —
remains open and is not addressed here.

---

## 15. Compatibility

DE-016 changes none of `DE-001`, `DE-002`, `DE-004`, `DE-008` or
`DE-011`. It formalises concepts those documents left intentionally or
inadvertently undefined. Verification against each:

- **`DE-001`** — No conflict. §6 generalises `DE-001`'s own "materially
  strengthened nor materially weakened" language into a definition
  `DE-001` uses but does not supply.
- **`DE-002`** — No conflict. §5's Counter-Evidence definition is
  `DE-002` §2.3's, unmodified. §8.3 relies on `DE-002` §2.3's prohibition
  on completeness theatre and §2.4's rule against reciting all seven
  portfolio factors; both are applied, neither is altered.
- **`DE-004`** — No conflict. §11 restates the three levels and Withheld
  without changing any boundary. §11's admission of minor Counter-Evidence
  at High is `DE-004` §3's own text, not an addition. §6.3 preserves
  `DE-004` §5's rejection of numeric scales.
- **`DE-008`** — No conflict. Nothing here permits Conviction to
  determine or restrict Direction; `DE-008` §15's existence-gate invariant
  is untouched.
- **`DE-011`** — No conflict. §3.1 restates `DE-011` §11's ontology; §8.3
  applies `DE-011` §7's revision rule and §11's fresh-evaluation
  requirement; §3.2 restates `DE-011` §12's rejected interpretations.
  `DE-011` §8's finding that Conviction is a property of Atlas's current
  understanding is preserved and sharpened: the understanding in question
  is of *the evidence Atlas holds about the conclusion's subject*, which
  is what `DE-011` §8's own worked example — two identically-good
  businesses differing on public disclosure — actually varies.

---

## 16. Reopening Criteria

DE-016 remains closed unless one of the following occurs:

1. **A Capability Gap is shown to contain conclusion-specific evidence.**
   If some class of not-yet-assessable dimension can be demonstrated to
   discriminate between two conclusions on evidentiary grounds, §8's
   exclusion must be re-examined for that class.
2. **Materiality cannot be applied consistently.** If §6's categorical,
   conclusion-relative definition proves indeterminate in practice — such
   that comparable cases receive incomparable treatment — the definition
   requires revision, though §6.3's prohibition on quantification would
   need its own separate reversal.
3. **A later doctrine supersedes DE-016**, explicitly and by name.
4. **A governing document DE-016 clarifies is itself revised** in a way
   that changes what this document depends on.

Dissatisfaction with the distribution of Conviction levels a conforming
implementation produces is **not** grounds for reopening. If High proves
rare, that is a finding about the evidence, which is what Conviction
exists to report.

---

## 17. Remaining Unresolved Doctrinal Questions

Stated explicitly rather than left implicit:

1. **Who judges materiality, and against what record?** §6 defines the
   standard but does not say whether materiality is a property Atlas
   determines per conclusion, a property attached to each piece of
   evidence when recorded, or both. This is the most likely subject of a
   successor clarification.
2. **Does Coverage need its own governing doctrine?** Coverage is
   currently governed only at the implementation-documentation tier. §9
   states its contract but does not elevate it; whether Coverage warrants
   a normative document of its own is not settled here.
3. **Does the readiness layer need its own governing doctrine?** §10
   assigns it ownership of implementation maturity without a normative
   document defining the layer itself. The same question applies.
4. **`DE-011` §14's own five open questions remain open.** This document
   closes only the sixth gap it identified, and does not address the
   fourth-conviction-concept sweep, the attachment-point rule, the
   same-conclusion boundary, or the evidentiary bar for honest statements
   of uncertainty.
