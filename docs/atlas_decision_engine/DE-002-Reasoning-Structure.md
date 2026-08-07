# DE-002 — Atlas Reasoning Structure

**Status:** Draft v0.1. Companion specification to
`docs/ATLAS_DECISION_ENGINE_DOCTRINE.md` §6. Governed by, and subordinate to,
that Doctrine and to `APP-000`. Documentation only — no code accompanies this
specification.

## 1. Purpose

Every Atlas Recommendation (`DE-001`) SHALL be presented through the same
seven-part structure, regardless of direction, business, or portfolio.
Consistency of structure, not complexity of content, is the goal — per
`ATLAS_CONSTITUTION.md`'s own instruction: *"Atlas should avoid jumping from
an asset idea directly to a conclusion."* A fixed structure is what makes a
skipped step visible, to the Investor and to Atlas itself.

This structure is not new invention. It is the direct application, at
recommendation level, of the ordering `ATLAS_CONSTITUTION.md`'s Non-
Negotiable Principles already fix: *"Evidence before opinion. Context before
conclusion. Portfolio before position. Risk before return."* Sections 2–7
below name exactly where each of those four principles lands in the
structure.

This structure is canonical: any summary, checklist, or shorter derived view
of recommendation completeness — including `DE-001` §3's four-element
checklist — is a view onto this structure, not an independent or competing
requirement.

## 2. The Seven Sections

### 2.1 Current Situation

**Purpose.** States the position (or absence of one) as it actually stands
today: whether the Investor holds the position, since when, at what
allocation, and what the position's own Decision Memory and Investment
Thesis (`DE-005` §1) show about its history.

**Required content.** A factual summary — no interpretation, no conclusion.
Sourced from the Investment Case's own recorded state (the product-level
Investment Case, `APP-001` §3.13 — a confirmed, 1:1 name for Atlas Core's own
`Case`, and distinct from `Decision.investment_case`; see `Doctrine` §1.3
for the disambiguation) together with current portfolio holding data.

**Prohibited content.** Any forward-looking claim, any conclusion, any
recommendation direction. This section answers "where do things stand,"
never "what should happen."

### 2.2 Evidence

**Purpose.** States the facts that support the recommendation being
reasoned toward. Operationalizes "Evidence before opinion."

**Required content.** Each item of Evidence attributed to its source and
its epistemic status per `APP-002` §7 (Known, Estimated, or Possible — never
presented with a plainness the underlying fact doesn't support). Sourced
from recorded Evidence and Observation content associated with the
Investment Case.

**Prohibited content.** An unattributed claim. A conclusion presented as if
it were itself a fact. Evidence "invented" to fill a gap — where evidence is
genuinely thin, that thinness is itself reported here, not concealed by
restating what little exists more confidently.

### 2.3 Counter-Evidence

**Purpose.** States the facts that cut against the recommendation being
reasoned toward — the single section this structure adds that a
less disciplined recommendation format most often omits.

**Required content.** Genuine counter-evidence, held to the same
attribution and epistemic-status standard as Section 2.2. Where a
recommendation is being made despite a specific, real risk or
counter-indicator, that risk is named here, not folded quietly into the
Evidence section or omitted because it complicates the conclusion.

**Prohibited content.** A token or manufactured counter-point included only
to appear balanced. Counter-Evidence SHALL be genuine and specific, or the
section SHALL state plainly that no material counter-evidence was found —
never populated for the appearance of completeness.

### 2.4 Portfolio Context

**Purpose.** States how this specific position interacts with this specific
Investor's specific portfolio. Operationalizes "Portfolio before position"
and is the direct application point of `DE-003-Portfolio-Intelligence.md`'s
seven factors (allocation, concentration, diversification, correlation,
opportunity cost, existing thesis, previous decisions) — see `DE-003` §1 for
how Portfolio Philosophy, Portfolio Intelligence, and Portfolio Context
relate.

**Required content.** The specific Portfolio Intelligence factors that bear
on this recommendation — not all seven restated by rote every time, but
whichever ones actually inform the direction being reasoned toward, per
`DE-003` §3.

**Prohibited content.** A recommendation reasoned as though the position
existed in isolation from the rest of the portfolio.

### 2.5 Direction

**Purpose.** States the direction — Buy, Add, Hold, Trim, Exit, or No Action
(`DE-001` §2) — and the Why element `DE-001` §3 requires: the specific
conclusion the preceding four sections support. Named "Direction," not
"Recommendation," to avoid reusing the name of the artifact this section is
one part of (the Atlas Recommendation as a whole) or of `DE-001`'s
Recommendation Framework.

**Required content.** Exactly one direction, stated in `APP-002` §6's
evidence-attributed register, with an explicit link back to the specific
Evidence, Counter-Evidence, and Portfolio Context items that produced it.
Where no direction can be supported at all, this section is not populated
with a weak or default direction — see Section 4, Recommendation Withheld.

**Prohibited content.** A direction that does not follow traceably from
Sections 2.2–2.4. This section is not permitted to introduce a
justification that was not already established above it.

### 2.6 Conviction

**Purpose.** States the Atlas Conviction Level (`DE-004`: High, Medium, or
Low) and the specific reason for it — the `DE-001` §3 "with what
uncertainty" element. Where no direction is stated (Section 4,
Recommendation Withheld), this section does not apply — Recommendation
Withheld precedes the Conviction Level scale rather than occupying its
bottom.

**Required content.** The level, and the specific evidentiary basis for
that level (what is well-established, what remains genuinely open), per
`DE-004` §3.

**Prohibited content.** A conviction level unsupported by, or in excess of,
the Evidence and Counter-Evidence actually presented above it — the direct
application of `APP-000` PP-007 at structure level.

### 2.7 What Could Change This View

**Purpose.** States the specific evidence, event, or threshold that would
cause Atlas to revise the recommendation — the `DE-001` §3 fourth element,
and a direct application of `ATLAS_CONSTITUTION.md`'s Trust Principle
"Explain what could change Atlas' view."

**Required content.** Specific, named conditions — a metric crossing a
stated threshold, a named assumption failing, a valuation range moving
outside its stated bounds (`Doctrine` §5) — never a generic disclaimer.

**Prohibited content.** A vague hedge ("market conditions could change")
that names no specific, checkable condition. This section exists so a
recommendation can be revisited honestly when the named condition occurs,
per `ATLAS_CONSTITUTION.md`'s "Atlas changes its mind when evidence
changes."

## 3. Structural Discipline

The seven sections SHALL appear in the order stated above, every time. A
future product surface presenting an Atlas Recommendation MAY collapse,
expand, or visually de-emphasize a section for a specific context (per
`APP-000` PP-004, complexity disclosed progressively), but SHALL NOT reorder
the underlying reasoning or omit a section's content entirely without
disclosing the omission — an empty Counter-Evidence section states plainly
that none was found (Section 2.3); it is never simply absent.

## 4. Recommendation Withheld — Structural Exception

Where Atlas cannot support any of the six directions (`DE-001` §2) at even
Low conviction, Atlas issues Recommendation Withheld (`DE-004` §4) instead
of the structure in Section 2. Recommendation Withheld is not a degraded
version of the seven-part structure — it replaces Sections 2.5 (Direction)
and 2.6 (Conviction) entirely:

- **Current Situation** (§2.1) and **Portfolio Context** (§2.4) MAY still be
  stated, where they help the Investor understand what Atlas does and does
  not yet know.
- **Evidence** (§2.2) and **Counter-Evidence** (§2.3) are replaced by a
  direct statement of why the available evidence is insufficient and what
  would resolve that insufficiency, per `DE-004` §4.
- **Direction** (§2.5) is omitted entirely — no direction is selected, and
  Recommendation Withheld SHALL NOT be recorded as, defaulted to, or
  displayed as Hold or No Action.
- **Conviction** (§2.6) is omitted entirely — Recommendation Withheld is not
  a value of the Conviction scale; it precedes the scale.
- **What Could Change This View** (§2.7) is replaced by the same "what
  would resolve this" statement Recommendation Withheld already requires —
  the two are the same content under Recommendation Withheld and are not
  stated twice.
