# DE-015 — Atlas Valuation Support Doctrine

**Status:** ADOPTED — Alpha. Companion specification to `DE-008`
(Direction Selection), which names "Valuation Support for Capital
Deployment" as the missing prerequisite for BUY/ADD (`DE-008` §21
invariant 1/2, §24) without ever specifying it as a constructible domain
capability. This document closes that specification gap. It does not
redesign `DE-008`, `DE-012` (Recommendation Ontology), or `DE-014`
(Outlook Composition) — every boundary those documents already adopted is
treated as fixed here. Documentation only — no code, frontend, or backend
accompanies this specification, and none is implied to exist yet. The
`ValuationSupport` domain object built in the preceding Alpha
implementation sprint remains a valid, honest stub — permanently
`INSUFFICIENT_INPUT` — until a future sprint implements the capability
this document specifies.

---

## 1. Title

**Atlas Valuation Support Doctrine** — what Atlas may legitimately assume
about future value when determining whether today's market valuation
provides Valuation Support for Capital Deployment.

---

## 2. Status

**ADOPTED — Alpha.**

The decision is: **adopt a narrower revised doctrine.** The original,
broader "Candidate 5" proposal (bounded historical persistence, unmodified)
is not adopted verbatim — several of its open questions resolve into real
constraints below, narrower than first proposed. **Candidate A** (no
forward assumptions at all) is not rejected — it remains independently
adopted as a valid, separate, sufficient proof path for narrow
current-state cases (§15), coexisting with the doctrine below rather than
being superseded by it.

---

## 3. Context

`DE-008` §21 invariant 11 forbids treating `ValuationStatus.UNDERVALUED`
as equivalent to Valuation Support for Capital Deployment, and §24 leaves
open whether the missing capability should come from "real
scenario-valuation implementation" or "a deliberate Valuation Philosophy
doctrine decision" — naming that decision as belonging to `DE-004`'s
domain, not `DE-008`'s. Three prior sessions in this track established the
factual and architectural groundwork this document formalizes: an audit
confirming `ValuationMethodKind.FCF_YIELD_RELATIVE` is the only real
valuation conclusion this codebase produces and `SCENARIO_BEAR/BASE/BULL`
are permanently-unimplemented placeholders; a capability investigation
establishing that Outlook's own Long-Term Expected Return mechanism
(revenue-corroborated rolling-CAGR growth extrapolation plus terminal-yield
reversion) is the only real, non-fabricated forward-looking computation
anywhere in the codebase, and that it is mathematically distinct from — not
a renamed version of — `FCF_YIELD_RELATIVE`; and a philosophy investigation
that stress-tested every surviving candidate against real AAPL/MSFT/TSLA
data and a wide range of company archetypes. This document is the
formal record of what survived that scrutiny.

---

## 4. Domain Question

`ValuationSupport` owns exactly one question:

> **Does today's valuation imply a positive or negative prospective return
> under defensible, historically-grounded valuation scenarios?**

It does **not** own, and must never be extended to answer:

> "Is this return economically sufficient to justify deploying capital,
> relative to risk and opportunity cost?"

**Known naming issue, recorded and not resolved here.** The Domain
Object's existing name — "Valuation Support for Capital Deployment" — and
its existing public-facing framing ("does today's market valuation provide
support for deploying new capital?") read most naturally as the second,
stronger question. The doctrine adopted below can only ever honestly
answer the first. **This document does not rename the Domain Object or
rephrase the domain question.** The mismatch is recorded as a known
naming issue and is a named reopening trigger (§22 item 8) for a future
product-ownership decision, not something this ADR resolves by fiat.

---

## 5. Decision

Atlas valuation **may** derive a bounded, disclosed forward-return range
from realized, multi-period, revenue-corroborated historical Free Cash
Flow growth and from a historically-observed valuation range, over an
adopted fixed horizon — subject to every constraint in §9–§16 below.
Atlas valuation **may not** fabricate a discount rate, a terminal multiple
not grounded in real historical observation, a probability weighting, or
any required-return threshold. Where the doctrine below cannot legitimately
reach a conclusion, `ValuationSupport.status` **SHALL** remain
`INSUFFICIENT_INPUT` — this is accepted as a common, ordinary outcome, not
a defect to be engineered away.

---

## 6. Meaning of SUPPORTED

**`SUPPORTED` means:** under the adverse end of a bounded,
historically-grounded, raw-fact-derived valuation scenario, today's
valuation does not imply a nominal loss over the modeled horizon.

This claim is:
- **downside-aware** — it is tested against the pessimistic end of the
  range, never the base case alone (§11 rejects base-case-positive as
  sufficient);
- **nominal** — no inflation adjustment;
- **non-risk-adjusted** — the same magnitude means the same status
  regardless of the business's own risk character (§14);
- **non-opportunity-cost-adjusted** — no comparison against cash, bonds,
  or any alternative (§13).

**`SUPPORTED` does not mean:** attractive relative to cash or any other
alternative; sufficient relative to a hurdle rate; risk-adjusted
attractive; equivalent to a BUY/ADD Recommendation; or "economically
compelling" in any general sense. Any presentation of a `SUPPORTED`
conclusion **SHALL** disclose this narrower meaning explicitly, never imply
the broader one.

---

## 7. Meaning of NOT_SUPPORTED

**`NOT_SUPPORTED` means:** a real, defensible, full prospective valuation
envelope was computed, and even its optimistic end remains negative —
under no combination of the historically-grounded scenarios this
company's own real evidence supports does today's price recover.

**Absence of `SUPPORTED` is never, by itself, `NOT_SUPPORTED`.**
`NOT_SUPPORTED` requires the same positive act of evidence `SUPPORTED`
requires, pointed the opposite direction — never a default fallback for
"nothing proved otherwise."

---

## 8. Meaning of INSUFFICIENT_INPUT

`INSUFFICIENT_INPUT` is returned whenever:
- no legitimate envelope can be computed at all (missing data, ineligible
  history, no positive current Free Cash Flow to build a yield from);
- the computed envelope straddles zero (the adverse end is negative, the
  optimistic end is positive — genuinely mixed evidence, not resolved by
  picking a side);
- multiple independently-sufficient valuation proofs (§15) conflict with
  one another.

`INSUFFICIENT_INPUT` is the expected, common, honest outcome under this
doctrine — never a state to be minimized by loosening any other section
of this document.

---

## 9. Historical Persistence Doctrine

Atlas valuation may derive a bounded forward scenario from realized
historical evidence only when **all three** conditions hold:

1. **At least two real historical observations exist sufficient to form a
   range.** Not a threshold — a range cannot exist from fewer than two
   points, by definition.
2. **Historical Free Cash Flow growth is corroborated by real Revenue
   facts over the same relevant periods.** A data-integrity requirement —
   does independent evidence support that this reflects real business
   activity — never a forecasting judgment.
3. **The valuation domain itself, reading raw facts only, rejects cases
   where full-history evidence shows no legitimate growth basis** (e.g.
   a company that has never once demonstrated real growth on either
   metric across its full recorded history).

Condition 3 **SHALL** be computed entirely within the valuation domain,
from raw `BusinessFact`s. It **SHALL NOT** consume Business Analysis's own
`BusinessCategoryStatus` conclusion, or any other domain's interpreted
conclusion (Risk, Outlook, Recommendation, Portfolio Intelligence). No
other condition is adopted — stability/dispersion, business maturity, and
structural-continuity checks were each tested and found either redundant
with the zero-boundary mechanism (§12) or currently unbuildable without
inventing a new detector (§19).

---

## 10. Shared-Facts Doctrine

Legitimate shared inputs are **raw facts**: Revenue, Free Cash Flow,
Operating Income, Cash, Debt, Shares Outstanding, and historical valuation
observations. Reading these directly, and interpreting them independently,
is not cross-domain coupling — it is the same "shared-ancestor,
independently-computed" principle `DE-012`/`DE-014` already established
for Outlook and Recommendation, applied here to Valuation.

**Consuming another domain's already-interpreted conclusion** —
`BusinessCategoryStatus`, `RiskStatus`, `OutlookMomentumKind`,
`RecommendationDirection`, any `PortfolioDoctrineFactor` conclusion — **is**
cross-domain coupling, and is prohibited unless a future ADR explicitly
establishes that specific dependency as domain-necessary, not merely
convenient.

---

## 11. Scenario Doctrine

**Growth assumptions:**
- **SHALL** be derived from realized historical evidence (§9);
- **SHALL** be expressed as a bounded range, never a fabricated point
  estimate;
- **SHALL NOT** rely on probability weighting of any kind.

**Terminal valuation:**
- **SHALL** be represented as a historically-observed range, never a
  single frozen historical median presented as if it were certain.

**Growth and terminal valuation SHALL be treated as separately uncertain
dimensions.** They **SHALL NOT** be paired through an invented narrative
about which combinations of growth extremity and valuation extremity
"belong together" — no default assumption that strong historical growth
co-occurred with rich historical valuation, or the reverse, for this
specific company, absent evidence establishing it. **When no principled
dependency between the two dimensions is established, Atlas SHALL use the
full conservative envelope (the independent combination of each
dimension's own extremes) rather than a narrower, coherence-preserving but
fabricated pairing.** This SHALL widen the resulting range relative to any
matched-extreme construction, and correspondingly SHALL make
`INSUFFICIENT_INPUT` more common — accepted deliberately as the honest
consequence, not corrected for.

---

## 12. Zero-Boundary Doctrine

**Zero is the only permitted boundary in this doctrine**, used only to
distinguish a nominal gain from a nominal loss. It is adopted specifically
*because* it is not a chosen number — it is the sole mathematically
necessary line between a range implying a gain and one implying a loss.

**SHALL NOT be introduced under this doctrine:** a required-return
threshold, a margin-of-safety *percentage* (the categorical
downside-tested structure of §6/§7 already provides margin-of-safety in
kind — testing the adverse end of the range — without needing a numeric
buffer beyond zero), a hurdle rate, a risk-free spread, or an inflation
spread. Each would require a legitimate input this domain does not
currently have (§13).

---

## 13. Required Return / Opportunity Cost

**True economic capital-deployment sufficiency logically requires a
required-return or opportunity-cost relation.** No source of one is
currently a valid `ValuationSupport` input:

| Source | Status |
|---|---|
| Risk-free rate | Not currently available (no macro data ingestion exists) |
| Inflation | Not currently available (no macro data ingestion exists) |
| Investor hurdle rate | Not currently available (no user-input surface for this exists, and building one is out of scope — §19 rejected alternative 10) |
| Portfolio opportunity cost | Belongs downstream — `DE-003`'s own `OPPORTUNITY_COST` factor, already adopted, not yet computable |
| Company-specific risk adjustment | Belongs downstream, in Recommendation (§14) |

Because none are available, `ValuationSupport` **SHALL** remain narrower
than full economic sufficiency, permanently, until one of these becomes
real (§22).

---

## 14. Risk Independence

`ValuationSupport` **SHALL remain risk-blind** in the sense of never
reading Business Risk, Financial Risk, or Valuation Risk's own interpreted
conclusions. The computed range's own *width* is an acceptable, already
non-invented proxy for one kind of risk (historical growth-rate
volatility) — a volatile history naturally produces a wider range, more
likely to straddle zero and resolve to `INSUFFICIENT_INPUT` — but this is
a structural side effect of §11's own construction, not a separate risk
input. Full risk-awareness (financial leverage, competitive position, and
other risk dimensions Business/Financial/Valuation Risk track) **SHALL
remain owned downstream, in Recommendation**, where independently-computed
Return (`ValuationSupport`) and independently-computed Risk sit side by
side as correlated context — mirroring the sibling-conclusion pattern
`DE-012`/`DE-014` already adopted for Outlook and Recommendation. Neither
is imported into the other's own computation.

---

## 15. Net-Cash Proof Path

A separate current-state valuation capability **may** establish
`SUPPORTED` without any forward extrapolation, when the current-state
evidence is itself sufficient — for example, market value below
demonstrable net cash (real `CASH`/`TOTAL_DEBT`/`SHARES_OUTSTANDING`
facts already exist in this codebase). **This is not an exception to the
forward doctrine in §9–§12 — it is an independent, sufficient proof path**,
fully compliant with Candidate A's own "never extrapolate" principle. It
answers the identical domain question (§4) through entirely different
evidence.

---

## 16. Proof Standard

`ValuationSupport` synthesis across any number of independently-sufficient
valuation capabilities **is proof-like, never vote-like.** Conceptually
(no new public Domain Object is created for this — it is a synthesis rule,
not a type), a given valuation capability may, for a given case:
establish support, establish non-support, or establish nothing.

**Synthesis rule:**
- one sufficient support proof, with no contradicting sufficient proof →
  `SUPPORTED`;
- one sufficient non-support proof, with no contradicting sufficient
  proof → `NOT_SUPPORTED`;
- conflicting sufficient proofs → `INSUFFICIENT_INPUT`;
- no sufficient proof from any capability → `INSUFFICIENT_INPUT`.

**SHALL NOT** be used: majority vote, weighted average, score aggregation,
or any "N of M models agree" rule. A single genuine proof outweighs any
number of non-proofs; two genuine, conflicting proofs resolve to honest
uncertainty, never to a count-based tie-break.

---

## 17. Outlook Relationship

Outlook and `ValuationSupport` **remain sibling conclusions**, per
`DE-012`/`DE-014`. **Neither may consume the other's conclusion.** Where
both domains require the identical descriptive calculation (e.g. rolling
multi-period CAGR, Revenue/Free-Cash-Flow corroboration, historical
valuation-range derivation), the correct architecture is:

```
Raw Facts
    |
    v
shared, opinion-free analytical primitive
    |         |
    v         v
Valuation   Outlook
```

**The shared primitive SHALL contain no valuation doctrine and no Outlook
doctrine** — it computes facts about facts (e.g. "here is the set of
revenue-corroborated rolling growth-rate observations"), nothing more.
Eligibility (§9), scenario construction (§11), and proof synthesis (§16)
**SHALL each be owned and implemented separately** by Valuation and by
Outlook, and may legitimately diverge between the two domains, as this
document's own resolution of the growth/terminal-valuation pairing
question (§11) already does independently of whatever Outlook's own,
separately-owned implementation currently does.

---

## 18. Recommendation Relationship

`ValuationSupport` **SHALL NOT** answer "should the investor buy?" — that
remains exclusively Recommendation's question, per `DE-001`/`DE-008`.
Recommendation may consume only `ValuationSupport`'s public `status`
field, and only according to Recommendation doctrine already adopted
elsewhere (`DE-008`) — this document makes no change to Direction
Selection, gating logic, or Recommendation Conviction. Risk, opportunity
cost, portfolio state, holding state, and every other decision input
named throughout this document as "downstream" remain Recommendation's
(or Portfolio Intelligence's) domain, not `ValuationSupport`'s, and not
addressed further here.

**Amendment (§22.7 — genuine expressive contradiction).** Recommendation
MAY additionally consume `ValuationSupport`'s public `gap` field, solely
for explanatory projection into canonical reasoning. `gap` **SHALL NOT**
influence Direction Selection, recommendation gating, Recommendation
Conviction, DecisionSupport, recommendation drivers, what-would-change,
or any other recommendation-semantic determination, and **SHALL NOT** be
treated as an additional `ValuationSupport` status. `status` remains the
sole `ValuationSupport` field that may affect recommendation semantics.

The contradiction this resolves: `INSUFFICIENT_INPUT` deliberately
collapses causes that are not alike (§6/§7). A
`SCENARIO_ENVELOPE_INCONCLUSIVE` gap means a real, historically-grounded
forward-return range was built and genuinely straddles zero — a complete
analysis whose answer is mixed. Restricted to `status`, canonical
reasoning could only describe that as a missing analytical input, which
is false. The distinction already exists in `gap`, already a public
field of this contract and already consumed outside Valuation by
`decision_readiness`, `coverage`, and the Investment Case API; this
amendment removes an inconsistency in which Recommendation alone was
forbidden to read what the API already publishes.

This is not reopened for naming, convenience, DRY, or test convenience
(§22's own exclusions). The doctrine's decision logic, status
vocabulary, Scenario Envelope construction and Direction Selection are
unchanged.

---

## 19. Known Limitations

The adopted doctrine does not, and under its own constraints cannot,
detect:

- cyclical peak/trough distortion (a trough or peak year's Free Cash Flow
  can distort the rolling-CAGR observations it participates in, in either
  direction);
- turnaround mean-reversion off a depressed base;
- acquisition-driven step changes (Revenue corroboration does not
  distinguish organic growth from an M&A-driven joint move in both
  Revenue and Free Cash Flow);
- permanent margin resets;
- structural business-regime change generally;
- historical valuation regimes that are no longer comparable to the
  present (partially, not fully, mitigated by §11's ranged rather than
  frozen terminal-yield treatment).

These are accepted, permanent, disclosed epistemic limitations — not
special cases requiring exception logic, and not evidence the doctrine
requires per-case patches to remain internally consistent. Its own honest
failure mode for these cases is `INSUFFICIENT_INPUT` or, less often, a
confidently-stated conclusion that carries this named residual risk;
either way, no detector for any of these is invented by this document, and
none should be invented merely to close this section.

---

## 20. Rejected Alternatives

1. `ValuationStatus.UNDERVALUED` as `ValuationSupport.SUPPORTED` —
   already forbidden by `DE-008` §21 invariant 11; reaffirmed here.
2. The Short-Term historical re-rating range as a new capital-deployment
   signal — rejected because it is mathematically equivalent to
   `UNDERVALUED`/`EXPENSIVE` (a re-rating of currently-held Free Cash Flow
   toward any historical yield is guaranteed the same sign as
   `FCF_YIELD_RELATIVE`'s own status, for every company, by construction)
   — it is item 1 wearing a percentage instead of a label.
3. Base-case-positive as sufficient for `SUPPORTED` — rejected; only the
   adverse end of the range may establish `SUPPORTED` (§6).
4. Any hidden required-return threshold — rejected; no legitimate source
   exists (§13).
5. A frozen historical-median terminal valuation presented as certainty
   — rejected; terminal valuation must be a range (§11).
6. Matched Bull/Bear pairing of growth and valuation extremes, justified
   by an unverified narrative that they co-occur for this company —
   rejected; the independent envelope is adopted instead (§11).
7. Business-Analysis-certified valuation eligibility — rejected; eligibility
   is computed from raw facts only, within the valuation domain (§9, §10).
8. Outlook as a computational input to `ValuationSupport` (or the
   reverse) — rejected; sibling conclusions only (§17).
9. Majority voting or model counting as a synthesis rule — rejected;
   proof-standard synthesis only (§16).
10. User-supplied assumptions as part of the minimum Alpha doctrine —
    rejected as the wrong product shape for this Domain Object; not ruled
    out as a future, separate capability.
11. Candidate A (no forward assumptions) as the **sole** general doctrine
    — rejected; it remains valid only as the narrow, independent
    current-state proof path of §15, not as a replacement for §9–§16.

---

## 21. Consequences

Recorded for a future implementation sprint; **none of the following is
built by this document**:

1. A shared, opinion-free primitive may be needed for rolling
   multi-period CAGR, Revenue/Free-Cash-Flow corroboration, and
   historical valuation-range derivation (§17).
2. `ValuationSupport` must implement its own eligibility (§9), scenario
   construction (§11), and proof synthesis (§16) — none inherited from
   Outlook or Business Analysis.
3. It must never import Outlook's conclusion or Business Analysis's
   conclusion, structurally (§10, §17).
4. Net-cash-floor valuation (§15) may become an independent, additional
   sufficient proof path, combined with the forward-scenario path only
   via §16's proof standard, never by voting.
5. The existing `ValuationSupport` implementation — permanently
   `INSUFFICIENT_INPUT`, per the prior Alpha implementation sprint —
   remains valid and correct until a future sprint implements the
   capability this document specifies.

---

## 22. Reopening Criteria

Reopen this ADR only if one of the following becomes real:

1. A real risk-free-rate or macro valuation input exists.
2. Portfolio Intelligence's `OPPORTUNITY_COST` factor becomes computable.
3. A real cyclicality detector exists.
4. A real M&A organic/inorganic decomposition exists.
5. A real structural-regime-change capability exists.
6. A real margin-reset detector exists.
7. Implementation discovers a genuine expressive contradiction in the
   adopted doctrine.
8. Product ownership formally decides that the current `ValuationSupport`
   name or domain question must be narrowed to match its adopted §6/§7
   semantics.

**Do not reopen for:** naming preferences, code convenience, DRY
concerns, test convenience, a desire to make BUY/ADD reachable, or a
desire to make `SUPPORTED` more common. None of these are evidence the
doctrine is wrong.
