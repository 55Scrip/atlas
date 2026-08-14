# DE-013 — Architecture Review: Can the Decision Engine Be Broken?

**Session type:** Adversarial architecture review, not an ontology investigation.
**Scope:** The four provisionally-adopted ADRs — `DE-009` (Outlook Ontology),
`DE-010` (Outlook Representation), `DE-011` (Conviction Ontology), `DE-012`
(Recommendation Ontology) — read against the full existing corpus they build
on (`ATLAS_DECISION_ENGINE_DOCTRINE.md`, `DE-001` through `DE-008`).

**Method.** Every finding below was tested against the actual text of the
cited document — quoted or paraphrased precisely, not from memory of what it
"probably says." Where a candidate contradiction was found, it was pushed
until it either broke (reported as a genuine finding) or resolved under
closer reading (reported as a resolved tension, with the resolution shown —
per the instruction to reject nothing without proof, a tension that survives
scrutiny is reported as surviving, not quietly dropped). No new ontology is
proposed anywhere below; every "missing concept" in Part 4 is named, not
designed.

---

## Part 1 — Dependency Graph

### The graph

**Root concepts** (depend on nothing else in this system, only on raw data
or Investor authorship):

- **Business Evaluation** (`Doctrine` §4) — built from raw company facts.
- **Valuation** (`Doctrine` §5) — built from raw market/financial data.
- **Investor Decision / Implementation Intent** (`DE-006` §4) — Investor-
  authored, computed by nobody.
- **Portfolio holding state** (`HoldingLinkage`, allocation, concentration) —
  raw portfolio data.

**Derived concepts:**

- **Evidence / Counter-Evidence** (`DE-002` §2.2/§2.3) — see the finding
  below; not as root as the Doctrine's own dependency table claims.
- **Decision Memory / Investment Thesis** (`DE-005`) — explicitly *"not a
  separately recorded object; it is the accumulated set of `reason`
  statements across... Decision history"* — a view over Decision, not a
  store of its own.
- **Portfolio Intelligence / Portfolio Context** (`DE-003`/`DE-002` §2.4) —
  derived from raw holding data (Allocation, Concentration) plus Decision
  Memory (Existing Thesis, Previous Decisions factors).
- **Outlook** (`DE-009`) — derived from Business Evaluation + Valuation only.
- **Conviction** (`DE-004`/`DE-011`) — derived per-attachment-point from
  Evidence/Counter-Evidence robustness for whichever conclusion it accompanies.
- **Reasoning** (`DE-002`, the seven-part structure as a whole) — see the
  split finding below.
- **Recommendation / Direction** (`DE-001`/`DE-008`/`DE-012`) — derived from
  Business Evaluation, Valuation Evidence, Portfolio Intelligence, Reasoning
  content, Financial/Valuation Risk, a narrow Decision Memory slice, and
  holding-state; gated (never shaped) by Conviction.
- **Execution Guidance** (`DE-006`) — derived from Recommendation's Direction
  (Buy/Add/Trim/Exit only), with its own independently-computed Conviction.
- **Representation** (`DE-010`) — a shared computation/distribution step over
  Outlook (and, by `DE-012` §10, Recommendation); not a new domain object.

**Terminal concepts** (nothing in this system depends on them):

- **Execution Guidance** — `DE-007` §4 confirms the dependency is one-way;
  nothing reads Execution Guidance back into Recommendation, Outlook, or
  Conviction.
- **Representation**, once it reaches a product surface.

**Cross-cutting concepts** (attach to more than one "layer," deliberately):

- **Conviction** — attaches independently to Direction, Outlook, and
  Execution Guidance (`DE-011` §5, §10; `DE-006` §5).
- **`DE-002` §2.7's revision-trigger mechanism** ("What Could Change This
  View") — reused verbatim by Recommendation (its original owner), Outlook
  (`DE-009` §7), and Conviction (`DE-011` §7). Genuinely the single most
  reused primitive in the whole corpus.
- **Decision Memory** — feeds Recommendation directly (`DE-005` §6) and
  Portfolio Context indirectly (two of `DE-003`'s seven factors), while
  being deliberately excluded from Outlook (`DE-009` §2.6, §4).

### Finding 1.1 — The Doctrine's own dependency table is wrong about `DE-002`

`Doctrine` §13 states plainly: *"`DE-002` (Reasoning Structure) is canonical
and structural... it does not depend on"* anything ("*(canonical
structure — depends on nothing below it)*" in its own dependency table).
This is false on the text of `DE-007` §2, which requires a Recommendation's
Evidence and Counter-Evidence to be *"traceable to Business Evaluation,
Valuation, and Reasoning's own already-produced findings — never restated
from scratch."* If Evidence/Counter-Evidence (`DE-002` §2.2/§2.3) must trace
to Business Evaluation and Valuation's *already-produced* findings, Business
Evaluation and Valuation must run **before** `DE-002`'s Evidence section can
be populated. `DE-002` depends on `Doctrine` §4 and §5 — a real,
demonstrable dependency the Doctrine's own table omits. This is not a defect
in the four new ADRs; it is a pre-existing gap in the master dependency
table this review surfaced while building the graph it asked for.

### Finding 1.2 — "Reasoning" and "Recommendation" are not two concepts

Testing the user's own Part 2 list directly, ahead of Part 2: can Reasoning
and Recommendation ever vary independently? No. `Doctrine` §13 itself
concedes this: `DE-002` is *"the one place a future implementation reads to
know the shape of an Atlas Recommendation."* `DE-002` is not a sibling
object that gets attached to a Recommendation — it **is** the
Recommendation's own structure. There is exactly one exception, and it
sharpens rather than undermines this finding: `DE-009` §6 has Outlook point
into `DE-002` §2.2/§2.3 (Evidence/Counter-Evidence) directly, meaning those
two sections specifically are genuinely shared, reusable material — while
§2.5 (Direction) and §2.6 (Conviction) are Recommendation-specific. **`DE-002`
is not one concept; it is two, bundled under one name**: a shared
evidentiary core (Current Situation, Evidence, Counter-Evidence, Portfolio
Context, What Could Change This View) that Outlook already reuses, and a
Recommendation-specific assembly (Direction, Conviction) layered on top.
`DE-009`'s own Open Question 2 ("should Outlook become an eighth `DE-002`
section, or stay outside it") is this exact seam, not yet closed. This
review does not resolve it either — it confirms the seam is real and worth
closing before implementation, because right now two different things share
one name and one document.

### Finding 1.3 — A genuine, unresolved ambiguity that could become a cycle

`DE-008` §4's hard gate requires "Recommendation Conviction assessable" as a
precondition for Direction Selection — checked *before* Direction is
finalized. But Conviction's actual *level* (`DE-002` §2.6, `DE-011`'s whole
ontology) is explicitly a rating of "one specific, currently-stated Atlas
conclusion" — which requires a Direction to already exist to rate. Read as a
two-phase process (case-level assessability checked first, then a specific
level computed against whichever Direction is eventually chosen), this is
not circular — `DE-008` §15 supports this reading ("existence-gate + attached
label, never a selector"). But **no document states explicitly whether
"assessable" is evaluated once, case-wide, independent of which Direction
will be picked, or separately per-candidate-Direction.** If it is ever
implemented as the latter, a genuine cycle exists (Direction Selection needs
Conviction-assessable-for-this-Direction, which needs a candidate Direction
to exist first). This is not a proven contradiction — it is a proven
*ambiguity that a straightforward, good-faith implementation could resolve
into a cycle without violating any written rule.*

### Finding 1.4 — The "always fresh, never self-referential" rule is convention, not doctrine

Outlook (`DE-009` §7: "restated," never "updated"), Conviction (`DE-011`
§7), and Recommendation (`DE-007` §5, §9: explicitly stateless pre-
persistence) are all, by consistent pattern and analogy, recomputed fresh
from current evidence — never as a function of their own immediately-prior
value. This pattern holds throughout the corpus. But **it is stated as an
explicit `SHALL NOT` only for Recommendation's persistence timing** (`DE-007`
§9: "Atlas SHALL NOT persist a Directional Recommendation merely because it
was computed"). No document states a general "no hysteresis, no smoothing,
no self-reference" invariant for Outlook or Conviction. A future evaluator
author could implement a smoothing mechanism for Conviction — to avoid
"flapping" between High and Medium on borderline cases — without violating
any *written* rule, only an unstated convention. Given how carefully this
corpus states its other invariants as explicit `SHALL`/`SHALL NOT` language,
this is a real gap, not a pedantic one.

### What should be merged or split

- **Split, not merge**: `DE-002`'s shared evidentiary core from its
  Recommendation-specific Direction/Conviction assembly (Finding 1.2).
- **No merge candidates found** among Outlook/Recommendation/Execution
  Guidance/Conviction — each was independently tested by concrete
  counter-example in its own ADR (Trim's portfolio-only pattern for
  Outlook/Recommendation; `DE-006` §5's independent-and-lower Conviction for
  Execution Guidance) and none of those tests broke under this review's own
  re-testing.
- **A flagged, not resolved, merge/split question**: Atlas Conviction Level
  (`DE-004`, 3-level, conclusion-specific) versus the already-shipped,
  case-wide `AnalysisConvictionLevel` (`atlas/analysis_engine/conviction.py`,
  5-level). `DE-007` §11 states these "MAY draw on similar underlying
  evidence... but [is] not derived from it by a fixed formula" — this is
  not a resolution, it is a documented non-answer. Compare this to `DE-005`
  §1's crisp treatment of the structurally similar Investment-Thesis-as-a-
  view-over-Decision question: one relationship in this corpus is precisely
  specified; the other, admittedly, is not. Carried forward to Part 7 as a
  concept deserving its own ADR.

### On the one deliberate feedback loop

`Recommendation → (Investor decides) → Decision → Decision Memory → future
Recommendation` is a real loop in the diagram, but it is not a computational
cycle: it is mediated by an external actor (the Investor) and separated in
time — no single computation depends on its own not-yet-produced output.
This is the system working as designed, not a flaw, and is worth stating
explicitly since a naive reading of the graph would flag it as circular.

---

## Part 2 — Orthogonality

Testing every pair the user listed that carries genuine risk of collapse
(pairs with no plausible confusion — e.g., Evidence vs. Portfolio Context —
are omitted rather than padded):

| Pair | Can they vary independently? | Verdict |
|---|---|---|
| Business Evaluation ↔ Valuation | Yes — `DE-008` §10.2 tests this directly: an undervalued security can still be NO ACTION on weak business quality. | Genuinely orthogonal. |
| Outlook ↔ Conviction | Yes — `DE-009` §9: a well-evidenced bad Outlook and a poorly-evidenced good Outlook are both coherent. | Genuinely orthogonal. |
| Outlook ↔ Recommendation | Yes — `DE-012` §5, §9: shared ancestors, no dependency, concentration-only divergence is a named, adopted case. | Genuinely orthogonal. |
| Conviction ↔ Recommendation (Direction) | Yes — `DE-004` §6: a High-conviction Hold and Low-conviction Buy are both coherent. | Genuinely orthogonal. |
| Recommendation ↔ Execution Guidance | Asymmetric — Recommendation exists without EG constantly (Hold/No Action/Withheld); EG never exists without Recommendation. | Distinct questions (what vs. how), not redundant — asymmetric dependency, correctly documented as such. |
| Reasoning ↔ Recommendation | **No** — see Finding 1.2. `DE-002` is Recommendation's own structure, not a co-existing sibling. | Not orthogonal — same concept under two names, except for the shared evidentiary core Outlook also reuses. |
| Investment Thesis ↔ Decision | **No, by design** — `DE-005` §1 states Thesis is a view over Decision's own `reason` history, with zero independent storage. | Correctly documented as non-orthogonal (a derivation, disclosed as such). |
| Investment Thesis ↔ Outlook | Yes, by design — `DE-009` §2.6, §4: Outlook explicitly never built from Thesis, specifically so it survives before any Decision exists. | Genuinely orthogonal — but see Part 3's disagreement scenario. |
| Atlas Conviction Level ↔ `AnalysisConvictionLevel` | **Unknown — genuinely untested.** `DE-007` §11's own words: "MAY draw on similar underlying evidence... not derived from it by a fixed formula." | Neither proven independent nor proven redundant — a live gap, not a settled orthogonality. |
| Portfolio Intelligence (the toolkit) ↔ Portfolio Context (the application) | Yes — the seven-factor toolkit is fixed; which factors bear on a given Recommendation varies per-case (`DE-003` §4). | Genuinely orthogonal (correctly modeled as principle/mechanism/application already, `DE-003` §1). |
| Representation ↔ Outlook/Recommendation content | Partially — which representation is *shown* (Short-Term View, Bull/Bear, Expected Return) can vary independently of the underlying content; the content itself cannot vary independently of its own inputs. | Legitimate partial independence — a real transformation layer, not a duplicate. |

**Summary finding for Part 2:** one clean, unambiguous non-orthogonality
(Reasoning/Recommendation, Finding 1.2 — a naming/documentation issue, not a
computed-value duplication) and one genuinely unresolved case
(`AnalysisConvictionLevel` vs. Atlas Conviction Level) where the corpus
itself admits it does not know the answer. Every other tested pair survives
scrutiny as either genuinely independent or correctly documented as a
non-independent derivation (Thesis-from-Decision).

---

## Part 3 — Contradiction Testing

### 1. Outstanding company, terrible valuation

Business Evaluation strong; Valuation `EXPENSIVE`. `DE-008` §10.2 resolves
Recommendation cleanly (TRIM if held — "EXPENSIVE... resolves to TRIM, a
self-sufficient direction"; BUY unreachable if not held, per Finding 3-Buy
below). **But Outlook exposes a real gap**: `DE-009` §2.6 defines Outlook as
synthesizing *three* dimensions (durability, evidence quality, valuation
attractiveness) into *one* "direction of travel." When durability trends
positive and valuation attractiveness trends negative, **no document
specifies how these compose into one statement.** The likely-correct answer
— state both named components explicitly rather than forcing one label,
consistent with "never collapse into one combined signal" (`DE-004` §6,
extended by `DE-009` §9's analogy) — is never actually adopted anywhere. An
implementer forcing a single "improving" or "declining" label onto Outlook
in this scenario would produce something the ontology never sanctioned.
**Genuine, open gap — recurs in scenarios 5 and 8 below.**

### 2. Concentrated portfolio

Directly, repeatedly tested (`DE-012` §5). Coherent — TRIM fires on
Portfolio Intelligence alone, independent of Outlook. No new issue.

### 3. Binary FDA approval

Tests Bull/Bear (`DE-009` §5) against Conviction-under-uncertainty (`DE-011`
§9). Bull = approval granted, Bear = denied — both plausible, Known-fact-
consistent deviations, fits `DE-009` §5's shape naturally. The harder case:
`DE-009` §5's "Base" is defined as "the scenario built from Atlas's
currently best-supported assumptions" — but a genuinely symmetric,
unresolvable binary has no single best-supported assumption set. **This
resolves coherently only by combining two separate ADRs the corpus never
explicitly joins**: Outlook's Base states the honest characterization
itself ("trajectory hinges on an unresolved binary regulatory event; no
assumption set is more supported than its opposite"), and Conviction can be
**High** on that characterization even though the underlying event is
unknowable (`DE-011` §9's exact finding). **Verdict: coherent, but only via
a synthesis neither `DE-009` nor `DE-011` states explicitly on its own** —
worth naming as a valuable cross-reference this stress test surfaces, not a
contradiction.

### 4. Fraud discovered

A clean, discrete, checkable event — exactly the shape `DE-002` §2.7 and
`Doctrine` §4's "conclusion reverses" language are built for. Business
Evaluation reverses; Outlook restates (a named Driver contradicted); EXIT
fires (thesis invalidated, `DE-001` §2); Conviction can be High (fraud
evidence, once confirmed, is often unambiguous). **No contradiction — the
architecture handles abrupt, discrete shocks well**, arguably better than
gradual drift, since "named, checkable condition" language fits sudden
events more naturally than continuous ones. Reported as a strength, not
merely an absence of a flaw.

### 5. Rapid multiple expansion (price runs up, no news)

Tests an apparent contradiction directly: `DE-009` §2.6 builds Outlook
*from* Valuation, and Valuation is a price-denominated signal that
mechanically moves with price — yet `DE-009` §7 separately forbids Outlook
from reacting to "routine price movement." **Pushed to a hard test, this
resolves, but not trivially.** `DE-009` §7's actual prohibition is on
*unnamed, tick-by-tick* reactivity; `DE-002` §2.7 explicitly names "a
valuation range moving outside its stated bounds" as a legitimate trigger
type. So a valuation-threshold breach is a permitted Outlook-revision
Driver, **provided Outlook's own Drivers name that threshold explicitly in
advance** — a mechanism the two documents only connect if read together;
neither states the resolution on its own. **Verdict: resolves, but the
resolution requires cross-referencing `DE-009` §7 against `DE-002` §2.7's
example list — a documentation-clarity gap, not a logical one.** The
underlying durability-vs-valuation composition gap from scenario 1 recurs
here identically.

### 6. Major macro shock

Fully absorbable through existing named factors (Durability-threatening
liquidity stress, a Valuation-range breach, a Concentration shift from other
holdings moving) — **provided it is channeled through one of those already-
named factors.** But `Doctrine` §6 explicitly disclaims elaborating
"Market and economic context" (the Constitution's own Decision Framework
step 3): *"Steps 1–3, 8, and 9 remain governed exactly as the Constitution
states them; this Doctrine adds no new content to those steps."* **No
document defines where macro/market-wide context is supposed to enter
Business Evaluation, Valuation, or Recommendation as its own category** —
it only works today by being silently absorbed into other factors. Elevated
to Part 4 as a missing concept, not just a scenario note.

### 7. Strong business, no liquidity

**No existing factor names this.** Durability (`Doctrine` §4.1) covers the
company's own balance-sheet survival, not the *position's* tradability in
the market. None of `DE-003`'s seven Portfolio Intelligence factors ask "can
this position actually be exited, in size, without moving the price."
Execution Guidance (`DE-006` §3) explicitly excludes any execution
algorithm and never addresses market-impact feasibility. **Genuine, clean
gap — liquidity has no home anywhere in the adopted ontology.**

### 8. Excellent company, tiny expected return

Business strong; Valuation `FAIRLY_VALUED` or mildly `EXPENSIVE`; if held,
resolves cleanly to HOLD or TRIM (`DE-008` §10.2); Conviction can be High
(clean evidence, clean methodology) while Expected Return is small — this is
`DE-011` §3's orthogonality finding, directly and correctly exercised. **No
contradiction — a validating case.** The same Outlook-composition gap from
scenario 1 is present but not worsened.

### 9. Weak company, high expected return

Business `WEAK` blocks any exposure-increasing direction regardless of
valuation upside (`DE-008` §10.2's AND rule) — resolves to NO ACTION if
unheld, TRIM/EXIT if held and thesis-relevant. Conviction is naturally Low
(thin, speculative evidence — `DE-004` §3's own Low-tier pattern). **This is
`DE-011` §3's orthogonality finding from the other direction, and it also
holds. No contradiction — a second validating case.**

### The pre-existing, self-documented gap this review must still surface

`DE-008` §10.1 and §11 already state, honestly, that Valuation Support for
Capital Deployment "does not exist as a computed concept anywhere in the
codebase today," and that consequently **BUY and ADD are permanently
unreachable, for any company, regardless of quality, until it is built.**
This is not a contradiction the four new ADRs introduced, and `DE-008`
discloses it plainly rather than hiding it — but a hostile review cannot
responsibly omit it, because it directly bears on the final question this
document is asked to answer (Part 7) and on Part 6's product mapping below.

---

## Part 4 — Missing Concepts

Genuine gaps only — nothing here is proposed as a design, each is named and
left exactly that unresolved, per instruction.

1. **Named Condition / Revision Trigger** is used as a mechanism everywhere
   (`DE-002` §2.7, reused by `DE-009` §7 and `DE-011` §7) but never defined
   as its own concept with a stated shape. Every document describes what a
   good trigger looks like in prose ("a metric crossing a stated threshold,"
   "never a vague hedge") without ever naming the general concept those
   descriptions all instantiate.
2. **Statelessness / Freshness** as an explicit invariant (Finding 1.4) —
   assumed by convention for Outlook and Conviction, stated as a rule only
   for Recommendation's persistence timing.
3. **Market/Macro Context** — the Constitution's own Decision Framework step
   3, explicitly disclaimed by `Doctrine` §6, never elaborated by any
   Decision Engine companion (Part 3, scenario 6).
4. **Liquidity / position tradability** — absent everywhere (Part 3,
   scenario 7).
5. **Time / as-of identity for Outlook and Conviction.** `DE-007` §8 defines
   `generatedAt`/`snapshottedAt` carefully for Recommendation. `DE-010` §7
   *requires* Outlook to exist as immutable, dated instances — but never
   names the field that would carry that date. Conviction gets no timestamp
   treatment anywhere.
6. **State/lifecycle model for Outlook.** `DE-007`/`DE-006` are unusually
   careful about computed-vs-historical state for Recommendation and
   Execution Guidance (`active`/`invalidated`/`withdrawn`). `DE-010` §7
   requires an analogous persisted-history model for Outlook and never
   specifies one.
7. **Version / ordering for Outlook's required instance history.** `DE-007`
   §6 deliberately rejects a version field for Recommendation ("recency is
   the version... an explicit integer version field would imply a precision
   this content does not need") — a reasoned decision, correct for that
   use case. But `DE-010` §7/§9's Case Momentum explicitly needs to compare
   the current Outlook instance against **specific prior instances**, which
   needs some addressing scheme beyond "most recent." `DE-007`'s reasoning
   does not automatically transfer to a use case it was never built for.
8. **Identity for Outlook and Conviction.** `DE-007` §6 treats Recommendation
   identity with real care (computed-instance identity vs. persisted
   historical identity, explicitly deferring only the generation mechanism).
   Nothing analogous exists for Outlook or for a specific Conviction
   assessment.
9. **Scope: is Outlook per-company or per-Case?** `DE-009` §2.6 builds
   Outlook only from company-level inputs (Business Evaluation, Valuation —
   deliberately excluding Portfolio Context). This strongly implies Outlook
   should be a **single, shared, per-company object**, computed once and
   referenced by every Investor's Case for that company — a materially
   different architecture from Recommendation (necessarily per-Case-and-
   Investor, `DE-012` §8) or from computing a fresh, duplicated Outlook per
   Case. No document states this either way. `DE-010`'s Representation
   Layer already gestures at "one computation, many readers" for *display*
   — this finding asks whether the same discipline should apply to
   Outlook's own underlying identity, not just its presentation.

---

## Part 5 — Canonical Flow

```
Raw data (company facts, market data, portfolio holdings,
          Investor-authored Decisions)
   │
   ├──► Business Evaluation ──┐
   ├──► Valuation ────────────┤
   │                          ▼
   │                    Outlook  (+ its own Conviction)
   │
   ├──► Evidence / Counter-Evidence
   ├──► Portfolio Intelligence (7 factors)
   ├──► Decision Memory / Investment Thesis
   │        │
   │        ▼
   └──► Reasoning  (DE-002's shared evidentiary core)
             │
             ▼
        Direction  (one of six, or Recommendation Withheld)
             │        (+ its own Conviction — gates, never selects)
             ▼
        Execution Guidance  (optional; Buy/Add/Trim/Exit only;
             │                + its own, independently lower Conviction)
             ▼
      Representation Layer  (one shared computation, not new ontology)
             │
             ▼
  Investment Brief · Portfolio · Watchlist · Daily Brief
  · Companion · Notifications · History
             │
             ▼  (the Investor acts)
   Investor Decision / Implementation Intent
             │
             ▼
      Decision Memory (appended, never rewritten)
             │
             └──────► feeds future Reasoning / Recommendation
                       (the one legitimate feedback loop — mediated
                        by the Investor, separated in time; not a
                        computational cycle)
```

Everything above the Representation Layer is Atlas-authored and stateless-
by-convention (Finding 1.4). Everything below "the Investor acts" is
Investor-authored and the only place anything is written because it
happened, not because Atlas concluded something (`DE-007` §11's own
governing principle, generalized).

---

## Part 6 — Product Mapping

| Surface | Concepts that map naturally | Gap exposed |
|---|---|---|
| Investment Brief | Business Evaluation, Valuation, Outlook, Direction+Conviction, Execution Guidance, Portfolio Context, Decision Memory/Thesis, Evidence/Counter-Evidence | None — this is the "complete" surface; every adopted concept has a natural home here. |
| Portfolio | Direction+Conviction (canonical, one computation per `DE-012` §10), Portfolio Intelligence (its native home), a compact Outlook representation | None structural. |
| Watchlist | Outlook (`DE-009` §8's Recommendation-Withheld-survival case is essentially the Watchlist case), NO ACTION | **Concretely exposes Part 3's BUY-unreachability gap.** Watchlist's entire purpose is plausibly "should I consider buying this," and the current decision procedure (`DE-008` §10.1) is structurally incapable of ever answering BUY, for any company. This is where that pre-existing gap becomes a visible product problem, not just a documentation footnote. |
| Daily Brief | Revision events — Outlook Drivers firing, Direction changes, Execution Guidance invalidation — all instances of the one shared `DE-002` §2.7 mechanism (Finding, cross-cutting concepts) | None structural. |
| Companion | Outlook, Recommendation, Conviction as conversational content, Case-scoped context (per the already-approved Companion architecture) | Indirectly touches Part 4's scope question (#9) — if Outlook is genuinely per-company, a Case-scoped Companion conversation referencing it is fine either way, but the underlying identity question is still open. |
| Notifications | Same revision-trigger content as Daily Brief | None structural. |
| History | Decision Memory (already well-grounded, `DE-005`) | **Concretely exposes Part 4's Outlook-persistence gap (#5–#8).** History is the natural home for Outlook's own instance history once it exists (per `DE-010` §7's own requirement), and there is currently no defined slot for it — History today is built on `AnalyticalSnapshot`/`ChangeIntelligence`, not on anything `DE-010` names. |

Two abstract gaps found earlier (BUY-unreachability, Outlook persistence)
each land on a specific, named product surface here — Watchlist and History,
respectively — which is a useful cross-check: neither gap is merely
theoretical.

---

## Part 7 — Final Assessment

### Strengths

- The define/test/reject-or-adopt discipline is genuinely, not
  cosmetically, maintained across all twelve documents — verified directly
  against the cited text throughout this review, not assumed.
- Non-merger discipline (Recommendation/Execution Guidance/Outlook) is
  enforced with concrete counter-examples every time, and every one of
  those counter-examples survived this review's own re-testing.
- `DE-002` §2.7's revision-trigger mechanism being reused verbatim by
  Outlook and Conviction, rather than each inventing its own, is a genuinely
  minimal, well-executed design choice.
- `DE-007`'s persistence model (investor-action-triggered only, never
  eager) is unusually rigorous, explicitly self-reviewed against its own
  failure modes (§14), and the strongest single piece of architecture in
  the whole corpus.
- Under every contradiction scenario tested (Part 3), the architecture
  either resolved cleanly or resolved with an identified, honestly-reported
  gap — nothing collapsed outright.

### Weakest assumptions

- Outlook's three-dimension composition (durability, evidence quality,
  valuation attractiveness → one "direction of travel") is asserted, never
  specified (Part 3, scenarios 1/5/8).
- The Atlas Conviction Level / `AnalysisConvictionLevel` relationship is
  explicitly, admittedly unresolved in the corpus's own words (`DE-007`
  §11) — not a finding of this review, but a live wound this review
  confirms is still open.
- Outlook's identity, timestamp, state, and versioning model is a
  requirement (`DE-010` §7) with no mechanism — the least mature part of
  the four newly-adopted documents, by a clear margin.

### Remaining risks

- The unstated "always fresh, never self-referential" convention (Finding
  1.4) could be silently violated by a well-intentioned implementation
  seeking to reduce Conviction "flapping."
- Liquidity and macro blind spots are more likely to surface first as
  product complaints than as recognized ontology gaps.
- Watchlist's structural inability to ever produce BUY is a live product-
  credibility risk that exists independent of, and unaffected by, the four
  ADRs this review was scoped to.

### Concepts that deserve their own ADR

1. Outlook Persistence, Identity, and Scope — closing `DE-010` §7's Open
   Question 1 with the same care `DE-007` gave the analogous Recommendation
   questions.
2. The Atlas Conviction Level / `AnalysisConvictionLevel` relationship —
   `DE-007` §11's flagged, unresolved ambiguity.
3. Market/Macro Context — the Constitution's own Decision Framework step 3,
   never elaborated anywhere in this corpus.
4. Liquidity — entirely absent from the current ontology.
5. Valuation Support for Capital Deployment — not new to this review
   (`DE-008` already names it as its own top priority), but the single most
   consequential gap in the entire engine: until it exists, BUY and ADD
   cannot be produced at all.

### Overall maturity

The ontology layer this review was scoped to (`DE-009`–`DE-012`) is
intellectually rigorous and internally consistent under stress — every
candidate contradiction tested either resolved cleanly or resolved into a
named, bounded, closeable gap, never into a structural collapse. The
surrounding structural layer (`DE-001`–`DE-008`) is unusually mature about
persistence, identity, and non-merger discipline. **The weakest link in the
whole system is not the ontology — it is that the decision procedure
(`DE-008`) currently cannot produce roughly half of its own defined action
space (BUY/ADD)**, a gap that predates and sits outside this review's
four-ADR scope but materially limits what the architecture can actually do
if implemented as specified today.

### "If Atlas were implemented exactly from these four ADRs, would the architecture remain coherent for the next five years?"

**Qualified yes — conditional on two specific, closeable pre-conditions,
not an unconditional yes.**

Nothing found in this review is a hard, structural contradiction inside
`DE-009`–`DE-012` themselves. The closest candidate (Outlook reacting to
Valuation, which is itself price-reactive) resolves cleanly once `DE-009`
§7 is read together with `DE-002` §2.7's own trigger examples — it survives
scrutiny. The four ADRs would not need to be re-architected due to anything
found here.

But "coherent for five years" is a stronger claim than "internally
consistent as written," and two gaps found in this review are the kind that
compound with time rather than staying static:

1. **Outlook's composition and identity gaps (Parts 3 and 4) will not stay
   theoretical.** The moment two implementers build Outlook independently —
   or the same implementer builds it twice, a year apart — without an
   adopted answer for "how do diverging sub-signals become one direction of
   travel" or "what makes two Outlook instances the same Outlook over
   time," the result is silently divergent Outlooks under one shared name.
   This is precisely the failure mode `DE-010`'s entire Representation
   Layer argument (§6: divergent per-surface computation is not a display
   bug, it is proof the "one Outlook" claim was never true) was built to
   prevent — except here the divergence risk sits one layer upstream, in
   Outlook's own construction, not its display.
2. **The BUY-unreachability gap (`DE-008` §10.1) will become a visible
   product failure before it becomes a recognized architecture failure**,
   concretely on Watchlist (Part 6) — and while it is outside the four
   ADRs' own scope, it is not outside the five-year horizon the question
   asks about, since these ADRs' own Recommendation/Outlook content will be
   judged, in practice, against a decision procedure that currently cannot
   reach half its own defined outcomes.

Close both — a short, focused Outlook-persistence ADR (item 1 in the list
above) and continued priority on Valuation Support for Capital Deployment
(already `DE-008`'s own stated priority, not a new one) — and the answer is
an unqualified yes. Implemented exactly as these four ADRs stand today,
without those two closed, the architecture is coherent on day one and
accumulates exactly the kind of silent, undocumented divergence its own
methodology exists to prevent by year two or three.
