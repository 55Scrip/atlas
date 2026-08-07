# DE-004 — Atlas Honest Uncertainty

**Status:** Draft v0.1. Companion specification to
`docs/ATLAS_DECISION_ENGINE_DOCTRINE.md` §7. Governed by, and subordinate to,
that Doctrine and to `APP-000`. Documentation only — no code accompanies this
specification.

## 1. This Specification's Authority

`UX-000` `UXD-R-064` states: *"This Doctrine SHALL NOT define a numeric or
categorical confidence scale. Any future scale requires its own subordinate
specification."* This is that specification.

`APP-002` §7 independently confirms the boundary this specification fills:
its own Known/Estimated/Possible/Unknown language conventions are
*"a language convention, not a numeric or categorical confidence scale...
[and do] not discharge, and SHALL NOT be read as resolving, `UX-000`
`UXD-R-064`'s own still-open question."* This specification is written to
close exactly that still-open question — and no other.

## 2. Naming: Atlas Conviction Level, Not Confidence

The formal scale this specification defines is named the **Atlas Conviction
Level**, deliberately not "Confidence." Two distinct fields already named
"Confidence" exist and remain unchanged and unrenamed by this specification:

- `Decision.investment_case`'s companion `Confidence` value object at
  `atlas/core/domain/decision/value_objects.py` — a 0–100 integer,
  explicitly *"the investor's own conviction level at decision time... Atlas
  stores this. It does not interpret it."*
- The Investment Case form's own `confidence` field
  (`frontend/src/routes/InvestmentCasePage.tsx`) — the same investor
  self-report, entered by the Investor, not computed by Atlas.

Both are Investor-authored self-reports. The Atlas Conviction Level this
specification defines is the opposite in kind: an **Atlas-computed**
assessment of how well Atlas's own evidence supports its own recommendation.
Naming it "Conviction" rather than "Confidence" avoids a fourth accidental
collision in a corpus that has already had to formally resolve one naming
collision of this exact kind (`ADR-003`, for "Recommendation"). The word
"conviction" is not a new coinage either: it is drawn directly from `APP-002`
§6's own existing section title, "By conviction level."

## 3. The Three Levels

The Atlas Conviction Level formalizes, as a structured field, three of the
four levels `APP-002` §6 already uses as prose-register categories (the
fourth, "Insufficient evidence," is not a Conviction Level — see Section 4).
This specification does not introduce new labels — it gives existing labels
a consistent, structured status so a recommendation's conviction can be
represented the same way everywhere it appears (a badge, a filter, a sort
order), not only within a sentence.

### High

**Evidence pattern.** Evidence is extensive, consistent, and directly
supports the conclusion; Counter-Evidence (`DE-002` §2.3), if any, is minor
and does not meaningfully undermine the conclusion.

**Communication.** Per `APP-002` §6: direct and specific language, "still
attributed and still framed as a matter for the Investor's own judgment" —
*"The evidence available strongly supports [specific claim], based on
[specific, named basis]."* Directness comes from naming the specific basis,
never from intensifying words such as "definitely" or "obviously."

### Medium

**Evidence pattern.** Evidence meaningfully supports the conclusion but
leaves real, specific open questions — genuine Counter-Evidence exists and
is not fully resolved.

**Communication.** Per `APP-002` §6: *"Current evidence suggests [claim],
though [specific named uncertainty] has not yet been resolved."* The named
uncertainty SHALL be the actual open question from Counter-Evidence, never a
generic hedge.

### Low

**Evidence pattern.** Evidence is thin, mixed, or largely inferential — the
Business Evaluation (`Doctrine` §4) or Valuation Philosophy (`Doctrine` §5)
conclusion rests more on Estimated or Possible content (`APP-002` §7) than
on Known fact.

**Communication.** Per `APP-002` §6: stated directly rather than softened
while keeping a confident shape — *"The available evidence is limited. What
exists points toward [tentative claim], but this should be treated as a
starting point for further review, not a settled view."*

## 4. Recommendation Withheld

Where the evidence available does not support High, Medium, or Low
conviction for any of `DE-001` §2's six directions — not even a
Low-conviction case — Atlas issues **Recommendation Withheld** instead of a
Conviction Level and a direction. This is not the bottom of the Conviction
scale; it precedes the scale entirely, because there is no conclusion for a
Conviction Level to qualify.

**Required content**, per `Doctrine` §7 and `DE-002` §4:

- No recommendation direction is selected — not Buy, Add, Hold, Trim, Exit,
  or No Action.
- Atlas states, specifically, why the available evidence is insufficient —
  which of `DE-002`'s Evidence (§2.2) or Counter-Evidence (§2.3) content is
  missing, contested, or too thin to support a conclusion.
- Atlas states what evidence or clarification would allow it to form a
  view.
- Atlas MAY still state Current Situation (`DE-002` §2.1) and Portfolio
  Context (`DE-002` §2.4).
- Atlas SHALL NOT default to Hold or No Action.

**Communication.** Per `APP-002` §6: *"There isn't currently enough evidence
for Atlas to form a view here."* This is a complete, valid Atlas
Recommendation outcome in its own right, not an error state and not a
placeholder awaiting more information — per `ATLAS_CONSTITUTION.md`'s Trust
Principle, *"Admit when there is not enough information for a high-confidence
assessment,"* and `APP-002` §6's own explicit instruction: *"Atlas SHALL NOT
manufacture a claim to avoid appearing unhelpful."* Recommendation Withheld
SHALL NOT be silently rounded up to a Low-conviction direction.

## 5. Categorical, Not Numeric — Why

This specification defines a three-value categorical scale, not a numeric
score (a percentage, a 1–10 rating). This is a deliberate choice, not an
omission, for two independently sufficient reasons already stated elsewhere
in this repository's doctrine:

1. **`ATLAS_CONSTITUTION.md` Trust Principles: "Avoid false precision."** A
   number implies a precision — that 73% is meaningfully different from
   71% — that no evidence-based judgment of this kind actually supports. A
   category makes only the claim the evidence can bear.
2. **`APP-000` PP-007: "A subordinate specification SHALL NOT present a
   conclusion with greater confidence than its underlying Evidence and
   Reasoning support."** A bare number invites exactly this — treating the
   number itself as the evidence, rather than as a compressed pointer back
   to it. Each of the three categories above is instead defined by, and
   always accompanied by, the specific evidence pattern that produced it.

## 6. Relationship to Recommendation Direction and Recommendation Withheld

The Atlas Conviction Level is independent of the recommendation direction
(`DE-001` §2) — a High-conviction Hold and a Low-conviction Buy are both
coherent, complete Atlas Recommendations. Conviction states how well the
evidence supports the conclusion reached; direction states what the
conclusion is. The two SHALL always be stated together (`DE-002` §2.6) and
SHALL NOT be collapsed into a single combined signal that obscures which one
a reader is looking at.

Recommendation Withheld (Section 4) is not a point on this relationship —
it replaces both the direction and the Conviction Level together, rather
than pairing with either.
