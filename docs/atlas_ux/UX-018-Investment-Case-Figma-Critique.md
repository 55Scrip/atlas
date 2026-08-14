# UX-018 — Investment Case Figma Critique (Target-State Design Review)

**Status:** Design critique, not an implementation spec. This document
takes the attached Figma as the primary UX reference and the current
product direction, per explicit instruction — it does not defer to
`UX-017`'s implementation-constrained posture, and it does not treat
backend data availability as a reason to reject a design decision. Where a
critique below depends on backend capability that doesn't exist today, that
dependency is named and collected in §5, separately from the design
judgment itself — the two are kept apart deliberately, because they are
different kinds of problem with different owners.

---

## 0. What's working — said first, because it's true

- The four-card "Atlas Reasoning" row and the "Supports the Case / Challenges
  the Case" split are the right instinct: attributed, evidence-shaped,
  non-imperative. Keep this pattern.
- The "Evidence Supporting This View" metric table (arrow + value +
  one-sentence interpretation) is genuinely good — it's interpretation-
  first, not a raw number dump, and it's the clearest single execution of
  "Atlas interprets, never just displays" anywhere in this design.
- "Detailed Financials, Sources & Methodology" as a collapsed footer link
  is the right home for raw depth — don't lose this in the next pass.
- The overall instinct to separate "the argument" (Supports/Challenges)
  from "the reasoning" (Atlas Reasoning cards) from "the evidence"
  (metric table) is sound information architecture in principle. The
  problems below are mostly about execution and duplication within that
  structure, not about the structure itself.

---

## 1. What is still too complex?

**The header row tries to say six things at once, at equal visual weight.**
Overall Case Health, Conviction, Recommendation, Expected Return,
Upside/Downside, and Confidence sit in one horizontal strip with no
typographic hierarchy distinguishing "the one thing to read first" from
supporting detail. Six co-equal metrics in one row is a small dashboard,
not a hero — and it directly works against the stated goal of an
investor understanding the page in five minutes, because the first thing
they see asks them to parse six numbers before they've read a single
sentence.

**The Outlook box doubles the reading burden by presenting two full,
symmetric panels.** Short-term and Long-term each carry their own Expected
Return, Bull/Base/Bear triplet, Confidence badge, Momentum badge, and Key
Drivers list — twelve data points before the investor has reached
"Investment Argument." Two fully-worked scenarios is roughly twice the
cognitive load of one, and the design gives no visual signal that one of
them (long-term) is primary and the other is a supporting lens on it —
they read as two equally-important, independently-authored forecasts the
investor has to hold in their head and reconcile simultaneously.

---

## 2. What is still missing?

- **No unit or basis clarity on the return figures.** The hero states
  "8-12% annualized" for Expected Return, but neither Outlook panel
  repeats "annualized" for its own Expected Return, and it's not stated
  whether the long-term Bull/Base/Bear figures (+220% / +110% / -20%) are
  cumulative over the full 3–5 year window or also annualized. A number
  without a stated basis is worse than no number for a product whose
  entire premise is honest precision — this is a real gap, not a
  nice-to-have.
- **No freshness indicator anywhere in these screens.** Nothing states
  when this analysis was generated or how current the underlying data is.
  For a live investment tool, "how current is this" is one of the first
  questions an investor asks, and it's currently answerable nowhere on
  the page.
- **Growth has no full card in Company Health Assessment.** It appears
  only as a one-sentence summary in "Atlas Reasoning" ("Revenue, EPS, and
  cash flow continue expanding...") and never gets the same expandable
  treatment Business Quality, Financial Strength, Management & Governance,
  Capital Allocation, and Competitive Position each receive. Growth is a
  first-order dimension everywhere else in this product's own analysis —
  its absence from the full assessment grid reads as an oversight, not a
  deliberate omission.
- **No explicit link between the compressed and expanded versions of the
  same judgment.** Nothing in the visual design tells the investor "this
  one-word badge, this one-sentence card, and this full metric row are the
  same fact at three levels of zoom" (§4 below) — each currently reads as
  an independent finding.

---

## 3. What creates cognitive load?

Ranked by severity:

1. **The symmetric Short-Term/Long-Term Outlook panels** (§1) — the single
   biggest source of load on the page, both in raw data-point count and in
   the reconciliation work it silently asks of the investor.
2. **Four visually-similar "positive judgment" badges appear before the
   investor reaches any real content**: Overall Case Health (STRONG),
   Conviction (HIGH), Confidence (HIGH), and the implicit positive framing
   of the Recommendation itself. All four are green, all four are
   short capitalized words, and nothing distinguishes what kind of
   judgment each one actually represents — an investor skimming has no
   way to tell these apart on a first pass, only on close reading.
3. **The Financial Health/Financial Strength and Business Quality/Business
   Quality Assessment duplication** (§4) — the same underlying judgment
   shown twice, under two different names, close enough together on the
   page that a careful reader will notice the overlap and start to wonder
   what else on the page might be quietly duplicated — a real, if subtle,
   trust cost.

---

## 4. What information hierarchy is wrong?

**"Confidence" sitting alongside Atlas-authored badges is a category
mix, not a hierarchy problem in the usual sense — it's worse.** If this
figure is the investor's own self-reported confidence, it does not belong
in the same visual row as Atlas's own Case Health/Conviction/Recommendation
judgments — mixing investor-authored and Atlas-authored content with
identical styling actively misleads about who is making which claim. If it
is instead meant to be an Atlas-authored figure, it needs a name that
doesn't read as the same concept as Conviction sitting two badges away —
right now the design invites the reader to assume Conviction and
Confidence are either the same thing said twice, or two independent Atlas
judgments with no stated relationship. Either reading is a problem; this
needs to be resolved before the next pass, not carried forward as-is.

**Recommendation and Conviction should be visually bound together; they
currently aren't.** These two are meant to always be read as a pair (what
Atlas concluded, and how well-supported that specific conclusion is) — but
in the current layout, "Overall Case Health" sits between them, breaking
the pairing. A reader's eye should never have to jump over an unrelated
metric to connect a conclusion to its own confidence qualifier.

**"Financial Health" and "Financial Strength," "Business Quality" and
"Business Quality Assessment" are the same finding, shown twice, under two
different names, in two different sections.** Compare the two Financial
cards' own text: *"The balance sheet is exceptionally strong with cash
generation comfortably covering all obligations and reinvestment
needs"* versus *"Unmatched cash reserves and generation with minimal
financial risk."* These are two sentences describing the same underlying
conclusion. This isn't a hierarchy nuance, it's a duplicate — and it
directly costs the "five minute understanding" goal, since a careful
investor will spend part of their five minutes trying to figure out
whether these are actually two different things before concluding they
aren't.

**Evidence table naming collides with a term this product already uses
precisely.** "Evidence" elsewhere in this product means attributed,
sourced, citable fact. This table is really an interpreted financial-
metrics summary — closer in kind to the Atlas Reasoning cards than to a
raw evidence/citation list. Naming it "Evidence" sets an expectation
(sourcing, citations) the table doesn't actually deliver, which is a
trust risk worth taking seriously in a product whose whole premise is
honest, checkable claims.

---

## 5. What should move / disappear / become more prominent

**Should move:**

- "Confidence" out of the Atlas-authored badge row — either into wherever
  investor-entered fields live, or removed from the hero entirely if it's
  meant to be Atlas-authored (see §4).
- Recommendation and Conviction — reposition adjacent to each other,
  nothing else between them.
- Growth — out of a one-line Reasoning card only, into a full card in
  Company Health Assessment, matching every other Business Evaluation
  dimension's treatment.
- The two "Changed since last review" one-liners (currently split, one
  per Outlook panel, saying different and disconnected things) —
  consolidate into one clear "what changed since you last looked at this
  Case" element, not two separate micro-changelogs an investor has to
  read independently and reconcile.

**Should disappear:**

- The label-repeated-in-body pattern on Biggest Strength / Biggest
  Concern / Current Priority — each currently restates its own eyebrow
  label as the first two words of its own sentence ("Biggest Strength:
  Exceptional business quality..."). Free, easy cleanup — cut the repeated
  words, keep the sentence.
- One of the two Financial cards (§4) — merge into a single card, in a
  single location, and let the metric table (§0) be its natural "expand
  for detail" destination rather than a third, separately-titled
  rendering of the same fact.
- One of the two Business Quality cards (§4) — same treatment.
- The hero's standalone "Upside/Downside +22% / -15%" figure, unless and
  until it can be explicitly bound to one specific horizon and shown to be
  arithmetically consistent with that horizon's own Bull/Bear figures. As
  currently shown, it's a third, unexplained return figure sitting beside
  two others that don't obviously agree with it (§2).

**Should become more prominent:**

- The Recommendation itself, with its one strongest supporting reason,
  should be the single largest, most visually dominant element in the
  hero — right now it competes on equal footing with five other badges.
  If an investor reads exactly one thing on this page, it should
  unambiguously be this.
- Biggest Concern deserves more visual weight than Biggest Strength and
  Current Priority currently give it — a risk-forward product should make
  "what deserves attention" easier to spot at a glance than "what's going
  well," not present the two as neutral, equal-weight columns.

---

## 6. One structural issue that isn't a data-availability problem

Worth separating explicitly from everything in §5's backend appendix,
because it needs a design decision, not backend work: **Short-Term and
Long-Term Outlook should not be two symmetric, independently-reasoned
panels, regardless of how much data eventually backs each one.** Even in a
fully-built future state, presenting near-term and multi-year views as two
coequal forecasts risks reading as two separate calls Atlas is making —
one of them inevitably closer to a near-term price call than a business
view — and asks the investor to reconcile two full scenario sets rather
than read one coherent view with a near-term lens on it. The stronger
target-state pattern: **one primary Outlook (the long-term, business-
grounded view), with the short-term content presented as a filtered,
clearly-subordinate lens on the same underlying drivers** — same Key
Drivers list, filtered to what's near-dated, not a second complete panel
with its own independent Bull/Base/Bear/Confidence/Momentum stack. This
also directly resolves the Bull-case-scale inconsistency in §1 (+25% vs.
+220%) and the counter-intuitive confidence inversion (Medium confidence
short-term, High confidence long-term, with no stated reason a 3–5 year
call is more certain than a 6–12 month one) — both of those read as
artifacts of forcing two independent panels to exist, not as real,
defensible product facts.

---

## 7. Backend capability required (separated per instruction — not a reason to change the design)

None of the following should shrink the target-state design. Each is named
so it can be scoped and built separately:

- **A computed, scenario-based Expected Return** (short-term and
  long-term), with an explicit, stated basis (annualized vs. cumulative)
  carried on the wire, not just in the label text.
- **A real Bull/Base/Bear scenario valuation**, requiring a forward
  assumption set this codebase does not compute today.
- **A single, coherent Outlook object** whose "Key Drivers" can be
  filtered by date to produce the short-term lens described in §6, rather
  than two independently-authored driver lists.
- **A "Momentum" signal**, distinct from Conviction and from the Bull/Bear
  deltas, with a stated definition — currently nothing in the backend
  computes anything named or shaped like this.
- **A full write-up for the Growth dimension** at the same depth Business
  Quality, Financial Strength, Management & Governance, Capital
  Allocation, and Competitive Position already receive.
- **A visible generation/freshness timestamp** on the analysis payload.
- **On-the-wire clarity between case-wide Conviction and Recommendation-
  specific Conviction** (two different existing scales in this codebase) —
  needed before the hero's Recommendation+Conviction pairing (§4) can be
  built honestly, since the design implies one paired judgment and the
  backend currently has two different conviction concepts that could each
  plausibly fill that slot.

---

## 8. Priorities for the next iteration

1. Resolve the Confidence/Conviction/Case-Health badge cluster (§3, §4) —
   the single highest-leverage fix, since it touches almost every other
   finding above.
2. Replace the symmetric Outlook panels with one primary view + a filtered
   short-term lens (§6).
3. Merge the two Financial cards and the two Business Quality cards into
   one each (§4).
4. Give Growth a full Company Health card (§2).
5. Add a freshness timestamp and explicit return-figure basis labeling
   (§2) — small, cheap, high-trust fixes.
