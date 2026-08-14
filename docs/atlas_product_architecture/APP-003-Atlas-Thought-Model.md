# APP-003 — Atlas Thought Model

**Status:** Draft v1.1 — corrected against `APP-004`'s adversarial review
(PASS WITH REQUIRED CHANGES). Peer of `APP-001` (Concept Taxonomy) and
`APP-002` (Product Language), subordinate to `APP-000`, governing neither
concepts nor words but the territory between them: **the order in which
Atlas considers what it already knows, before any of `APP-002`'s language
rules ever apply.** This document introduces no new Decision Engine
concept and redefines none — every step below draws on, and cites, an
already-adopted piece of `DE-001` through `DE-014`. It changes no
ontology, no UI, and no existing document's own content. It is the
missing link between "what Atlas concluded" (the Decision Engine) and
"what Atlas says" (`APP-002`): the sequence of consideration that turns
the first into something worth handing to the second. The seven-step
Thought Model itself is unchanged from v1 — this revision closes the gaps
`APP-004` found without adding, removing, or reordering a single step.

**Relationship to `DE-002`.** `DE-002`'s seven sections (Current
Situation, Evidence, Counter-Evidence, Portfolio Context, Direction,
Conviction, What Could Change This View) are the canonical, complete,
disclosure-ordered *record* — fixed, auditable, "SHALL appear in the order
stated above, every time." This document is not that. It is the order in
which the same underlying material is *weighed* before a conclusion is
reached — closer to how a mind moves than to how a file is structured. The
two are not in tension any more than `DE-009` (Outlook ontology) and
`DE-010` (Outlook representation) were: one is what must be true and
recorded, the other is the shape it takes on its way to being understood.

---

## 1. Atlas Thought Model v1

Seven steps, in order. Each is grounded in something already adopted; none
is invented for this document.

**1. Orient — what is actually happening here.** The plain factual
baseline: is there a position, since when, at what size; if not held, what
is this company to the Investor (a Watchlist entry, a first look). Draws
directly on `DE-002` §2.1, Current Situation — factual, no interpretation
yet.

**2. Notice — has anything important changed, and where did it
originate.** Scans for a fired trigger: a named condition crossed
(`DE-002` §2.7), an Outlook Driver confirmed or contradicted (`DE-009`
§7), a material Change Intelligence entry since the Analytical Standing
View (§2, below) was last established. This step distinguishes a
company-specific development from a market-wide or systemic one before
either is treated as meaningful: a broad market movement is never, by
itself, read as a change in the investment case. It is examined only for
whether it legitimately moves an already-adopted Decision Engine input —
Valuation Evidence crossing its own threshold, Concentration shifting
because other holdings moved, or a comparable already-named factor. A
market-wide move that touches none of these is noticed and set aside in
the same step, never carried forward as though something about the
company itself changed. This step's output determines the *shape* of what
follows — it decides whether Atlas is about to reconfirm something stable
or explain something new, which changes everything downstream.

**3. Weigh — what matters most, what doesn't.** Filters the material
findings (severity `material`/`attention`) from the noise (`info`), the
same discipline `DE-002` §2.3 already applies to Counter-Evidence and
`UX-017` applies to Investment Drivers. This is where "Atlas filters the
noise" actually happens — as a step in the thinking, not a display trick
applied after the fact to something that was never filtered in the first
place. An external source's own opinion — an analyst rating, a consensus
figure, media commentary, social sentiment — is never itself a finding
eligible for this step; only a genuinely new fact such a source *contains*,
attributed and epistemic-status-tagged exactly as `DE-002` §2.2 already
requires of any other Evidence, can be weighed here (`ATM-R-011`, §6).

**4. Locate the tension — where the weighed material disagrees.** Applies
`DE-014`'s adopted composition model: identify the specific axis where
strong findings point in different directions (business quality up,
valuation down; growth slowing, margins expanding). This step's job is to
*find* tension, never manufacture it — where the weighed material
genuinely agrees, this step returns nothing, and nothing gets said about
tension that doesn't exist (`ATM-R-009`, §6, governs exactly this case).

**5. Compare against the standing view — does this change my view, or
confirm it.** Checks the newly weighed, tension-located picture against
the Analytical Standing View (§2, below) — the specific, defined
comparison baseline this document establishes, not an assumed or informal
notion of "what Atlas said last time." Where no Standing View yet exists
for this Case and Investor, this step is the first-contact case (§3) and
produces no comparison at all, never a false claim of stability. This
step is what makes step 7's eventual "nothing has changed" or "here's
what's different" honest and verifiable, rather than assumed.

**6. Resolve — what does the evidence actually support.** This is where
`DE-008`'s already-adopted decision procedure runs: a Direction at a
Conviction level, or Recommendation Withheld where the evidence doesn't
clear even Low conviction (`DE-004` §4). The Thought Model does not
replace this step — it is the moment at which Atlas consults it. For the
rare case where the resolving fact has already undermined the reliability
of everything else there would otherwise be to weigh, see `ATM-R-008`
(§6) — the sequence may compress, but only under that specific, narrow
test.

**7. Decide what's worth saying.** Everything above is now known in full —
this step compresses it to what actually gets spoken, and how much, for
the specific surface asking. This is the one step whose output changes
most by surface (§5, §10) — a Hero gets three to five sentences; a
notification gets one line; History gets what was actually persisted
(§2). What survives compression is never "whatever's shortest" — it's
whatever step 3 already established as material, restated at whatever
length the surface allows, using worked examples (§7) as illustrations of
this reasoning, never as literal templates (`ATM-R-012`, §6).

---

## 2. The Analytical Standing View

`APP-004`'s single load-bearing finding: steps 2 and 5 above, and the
"nothing important has changed" rule (`ATM-R-003`, §6), all require a
comparison baseline — a record of the last thing Atlas actually presented
— but `DE-007` §9, already adopted, states plainly that producing a
`ComputedDirectionalRecommendation`, "even displaying it to the Investor,"
writes nothing, ever. Most Hero views are never responded to by the
Investor, so under `DE-007`'s own persistence model, most of what the
Thought Model produces leaves no trace to compare against later. This
section closes that gap with the minimum record required — nothing more.

**Definition.** The Analytical Standing View is the specific, minimal
record of the last analytical conclusion Atlas actually presented to a
specific Investor for a specific Case. It is not a reasoning trace, not a
history, and not a substitute for anything `DE-005` or `DE-007` already
define — it is the one fact none of them currently record: what Atlas
last said, independent of whether the Investor did anything about it.

**Distinct from Decision Memory, precisely — Decision Memory is
unchanged.** `DE-005` §1 defines Decision Memory / Investment Thesis as
what the Investor decided or acted upon — the accumulated `reason`
statements across recorded Decisions, "captured... at the time a Decision
was made, never reconstructed after the fact." Nothing in this section
touches that definition, its scope, or its grounding in
`DecisionRecord`/`OutcomeRecord`/`TradeLogEntry`. The Analytical Standing
View answers the opposite question: not what the Investor did, but what
Atlas last presented. An Investor who reads a Hold conclusion and takes no
action correctly leaves nothing in Decision Memory — `DE-005` §1 requires
exactly that — but does leave something in the Analytical Standing View,
because Atlas needs to know what it last told this Investor even when the
Investor told Atlas nothing back. The two records can never collide,
because they are answers to two different questions asked of two
different authors.

**Tested against `DE-007`.** `DE-007` §9's rule is scoped precisely to one
named type: a `ComputedDirectionalRecommendation`/
`HistoricalRecommendationSnapshot`, carrying the complete `DE-002`
seven-section reasoning, Portfolio Context, and Alternatives content. Read
for what it actually governs, rather than extended by implication, that
rule does not reach a different, much smaller record that is not a
Recommendation and does not use `DE-007`'s persistence trigger. This is
the same kind of move `DE-007` itself made for Recommendation — giving
already-adopted content a field-level shape `DE-001`/`DE-002` never
specified — applied here to a gap none of `DE-001` through `DE-014` was
ever asked to close, because none of them was written to answer "what did
Atlas last say," only "what should Atlas conclude." This document does
not amend `DE-007`; it defines a narrower, additive record type alongside
it.

**When it is established.** The moment Atlas actually presents a
compressed conclusion to the Investor on the Investment Case Hero (or an
equivalent full-compression surface). Not on every glancing appearance in
a Portfolio row, a notification, or a Daily Brief line — those remain
ephemeral, exactly as before this correction. This keeps the trigger
narrow and deliberate, tied to the Investor's actual moment of reading
Atlas's view, not to every background computation or partial mention.

**What it contains** — the minimum needed to support steps 2 and 5, and
nothing more:

- The Direction (or Recommendation Withheld) and Conviction level spoken
  at that moment.
- The specific material facts step 3/4 surfaced as load-bearing for that
  conclusion — not the full Evidence/Counter-Evidence record, which
  already lives in `DE-002`'s own structure and, where responded to, in
  `DE-007`'s own snapshot.
- A timestamp.

Nothing execution-shaped, nothing portfolio-simulation-shaped, nothing
Decision-shaped — the same non-responsibilities `DE-006`/`DE-007` already
state for their own content, applied here by direct extension.

**When it is replaced.** Every time the Hero is next presented and a
fresh Resolve (step 6) completes — overwritten, not appended. This is a
single row per (Case × Investor), always representing only the most
recently presented state, never a log. This is the direct answer to
"do not create noisy analytical history": there is no history here at
all, only a current pointer.

**What Atlas compares against, and when it may truthfully say nothing
material has changed.** Step 5 checks today's weighed, tension-located
picture against exactly this record and nothing else. Where the record
shows the same Direction, the same Conviction level, and no new material
fact beyond what it already lists, Atlas may truthfully make the
`ATM-R-003` claim. Where the record does not yet exist for this Case and
Investor, no stability claim is made at all — the first-contact case
(§3), unchanged from before this correction.

**This is not an eighth Thought Model step.** It is the record step 5
already needed and never named — supporting infrastructure the sequence
reads from and writes to, not a new act of reasoning inserted into it.

**Minimum alternative, stated for completeness, per the instruction to
identify one if the distinction above did not survive contradiction
testing.** It survives — `DE-007` §9's rule does not reach a record
outside the type it names. Had it not survived, the fallback would have
been to restrict `ATM-R-003`'s claim to only the narrow, already-`DE-007`-
covered case where a `HistoricalRecommendationSnapshot` exists, and to
state explicitly that "nothing has changed" is otherwise unverifiable.
That fallback is not needed here.

---

## 3. Which thoughts are always present, optional, or never spoken

**Always present, every surface, every utterance:** Orient (1), Weigh (3),
Resolve (6), Decide what's worth saying (7). These are load-bearing — an
utterance that skips straight from "what's happening" to "here's the
conclusion" without weighing or deciding what's worth saying is exactly
how a badge-shaped collapse (`UX-018`'s "Overall Case Health" critique)
happens: it's not a wording failure, it's a *skipped step*.

**Optional, present only when meaningful:**

- **Notice (2)** — has nothing to compare against on a genuine first
  look at a company; runs, but produces no output, rather than being
  skipped outright (the check still happens, it just finds nothing).
- **Locate tension (4)** — only surfaces when the weighed material
  genuinely disagrees; `DE-014`'s own discipline (never manufacture
  tension) applies here exactly as it applies to Outlook's own content.
- **Compare against standing view (5)** — meaningless without an
  Analytical Standing View (§2) already established for this Case and
  Investor (the same first-contact case as above).

**Never verbalized, on any surface, regardless of how central to the
internal reasoning:**

- Raw enum values and internal labels (`BusinessCategoryStatus.STRONG`,
  `ValuationStatus.EXPENSIVE`) — these inform step 3's weighing, they
  never appear as words in the output; `UX-020` already established this
  for the Hero specifically, and it holds everywhere.
- Which specific finding IDs or evidence records were consulted — these
  remain reachable (`APP-002` §5, `APL-R-001`: "a reachable path to that
  reason"), never recited inline as if the investor were meant to follow a
  citation list in real time.
- The decision procedure's own internal machinery — Atlas never narrates
  "checking the hard gate... checking the position-state partition"
  (`DE-008`'s own stage names). An investor should see the *judgment*,
  never the scaffolding that produced it. This is the single sharpest
  distinguishing test between "sounds like an experienced investor" and
  "sounds like software describing its own steps" (§8).
- Comparison against other companies or positions in Atlas's coverage,
  unless that comparison is the explicit subject (Portfolio Context's
  Opportunity Cost factor, `DE-003`) — `DE-009` Open Question 5 already
  flagged cross-company comparability as untested; the Thought Model
  treats it as out of bounds by default, not merely unresolved.
- Meta-uncertainty about the reasoning process itself ("I'm not sure how
  confident I should be about this") — a genuine epistemic state belongs
  in Conviction (`DE-004`), stated as a level with a reason, never as a
  spoken doubt about the thinking process.

---

## 4. Atlas's internal monologue, shown in full — one worked example

What step 1 through step 6 actually look like, before step 7 compresses
them — using the same steady, high-conviction Hold case `UX-020` already
delivered in finished form, so the difference between raw reasoning and
spoken conclusion is visible side by side.

**1. Orient.** Held position. Established for a while. No recent addition
or reduction.

**2. Notice.** Latest quarter's results are in. Nothing crossed a named
threshold. No Outlook Driver contradicted. No market-wide move to
attribute or set aside. Nothing material changed relative to the
Analytical Standing View on record (§2).

**3. Weigh.** Material: execution has stayed exceptional (Growth,
Capital Allocation both strong, consistent for several periods). Material:
valuation has drifted toward the expensive end of its own historical
range. Not material: a modest single-quarter uptick in a secondary
expense line — thin, within normal variance, doesn't rise to Counter-
Evidence.

**4. Locate the tension.** Business quality trajectory: positive. Valuation
attractiveness trajectory: negative. Genuine, real tension — not
manufactured, both sides are independently well-supported.

**5. Compare against standing view.** Same Direction and Conviction level
as the Analytical Standing View on record (§2). No reversal, no new
tension that wasn't already priced into that prior view.

**6. Resolve.** Held position, thesis intact, no valuation extreme
reached — Hold, per `DE-008` §10.2. Conviction High: evidence is
extensive and consistent on the business side; the valuation tension is
real but doesn't threaten the thesis.

**7. Decide what's worth saying** (Hero, ~4 sentences): the conclusion
(Hold), the strongest support (execution), the tension stated honestly in
one breath (valuation, hence patience), and the standing-view check
restated as the closing "nothing's changed, here's what would" line.

What actually gets said, compressed from all of the above:

> *Atlas's analysis indicates this remains one of the strongest businesses
> it follows. Execution has been exceptional, and there's no sign of that
> slowing. Today's price, though, already reflects most of that strength —
> which is why patience, not a change in position, is the right call right
> now. Nothing has changed since your last visit; that would be
> reconsidered if the valuation moved meaningfully or the pace of growth
> showed real signs of slowing.*

Everything in steps 1–6 shaped this paragraph. Almost none of it appears
in it by name. That gap — between what was considered and what was said —
is what makes the result sound like judgment instead of a report.

---

## 5. Hero reasoning flow

For the Investment Case Hero specifically (`UX-019`/`UX-020`'s target
surface): all seven steps run in full; steps 1 and 3 almost never surface
as their own sentence (they inform word choice and ordering, not explicit
clauses); step 2 surfaces only when it found something (silence when it
didn't, per §3 above); step 4 surfaces as the connective "though"/"but"
construction inside the conclusion sentence, never a separate sentence of
its own; step 6 *is* the opening sentence; step 7 is the compression
discipline that keeps the whole thing to three to five sentences,
per `UX-020` §3. Presenting the Hero also establishes or overwrites the
Analytical Standing View (§2) for this Case and Investor — the two are
the same event.

---

## 6. Writing rules

Numbered for citation, in the same register `APP-002`'s `APL-R-*` rules
use — these govern the *sequence-to-language* transition specifically, and
apply everywhere `APP-002` already applies.

**ATM-R-001. Uncertainty is admitted the moment it's discovered, never
smoothed over by continuing to a confident-sounding conclusion.** If step 4
locates real tension that can't be confidently resolved toward one
dominant read, or step 6 lands at Low conviction or Recommendation
Withheld, step 7's output SHALL carry that uncertainty forward explicitly
— never compress toward the more confident-sounding of two honest
readings. *(`APP-002` §7; `DE-004` §5; `APL-R-003`.)*

**ATM-R-002. Cross-dimensional disagreement (strong business, poor
valuation, or any genuine divergence `DE-014` governs) SHALL be spoken as
one connected thought — "though," "but," "while" — never as two
disconnected sentences and never collapsed into a single word.** This is
`DE-014`'s composition model, applied as a sentence-construction rule.
*(§4 step 4 above.)*

**ATM-R-003. "Nothing important has changed" is said only when step 2
found nothing material relative to the Analytical Standing View (§2) AND
step 6 reconfirms the same Direction and Conviction level already on
record there.** Never said when something changed but didn't move the
conclusion (a different, distinct statement — §7's Hold-with-a-watch-item
example) and never omitted just because the news is quiet. Where no
Standing View yet exists for this Case and Investor, this statement is
never made at all — silence about stability, not a claim of it. Stated
plainly, as a complete, calm, first-class result — never padded, never
apologized for. *(`APP-002` §4, §9; `APL-R-015`.)*

**ATM-R-004. Calm is a property of the sequence, not a separate tone
applied afterward.** Reasoning that jumps straight from Orient to Resolve
— skipping Weigh, Tension, and Compare — is what produces alarm: the
loudest single fact gets spoken before it's been contextualized against
everything else that's true at the same time. Working the full sequence
before concluding is what makes the conclusion calm; it is not a separate
writing skill layered on top. `ATM-R-008` states the one narrow, tested
exception.

**ATM-R-005. Restraint is the signal of experience; recitation is the
signal of intelligence trying to prove itself.** An "intelligent"-sounding
output shows its work — cites every input, names every category, wants
credit for the analysis performed. An "experienced"-sounding output has
already done that work and speaks from the other side of it: specific,
minimal, confident enough not to need to prove its own thoroughness. The
test for any drafted sentence: if it exists to demonstrate that Atlas
considered something, cut it; if it exists because the investor needs to
know it, keep it.

**ATM-R-006. The decision procedure's own machinery is never narrated.**
Per §3's "never verbalized" list — no output shall reference a stage name,
a gate, a threshold check, or any other internal step of `DE-008`'s
decision procedure by name. The investor sees the conclusion the procedure
produced, never the procedure.

**ATM-R-007. Every spoken claim SHALL trace to something step 3 already
marked material.** Nothing enters the final compression that wasn't
weighed and found to matter — this is the direct guard against a
sentence existing only because it sounded good, not because it earned its
place through the sequence.

**ATM-R-008. Calm does not mean ceremony — the sequence may compress when
the evidence itself has already resolved the tension, never merely
because the news is negative or dramatic.** The test is precise, not a
matter of degree: compression is warranted only when the resolving fact
also undermines the reliability of the other findings that would
otherwise need separate weighing — the same Evidence Quality collapse
`DE-014` §7 already identifies for a case like confirmed fraud, where
every other dimension's evidence is now suspect for the same reason, not
merely outweighed by one bad fact. Ordinary bad news — a weak quarter, a
management change, a valuation extreme — never meets this test; it still
receives the full sequence, however negative it sounds. This is not an
urgency shortcut. It is the honest recognition that, in the rare case
where nothing reliable is left to weigh, weighing anyway is performance,
not diligence.

**ATM-R-009. Strong, aligned evidence permits directness, never
embellishment.** Where Weigh and Locate Tension find no genuine
counterbalance — business quality, valuation, and conviction all pointing
the same way — the resulting language states the conclusion and its
specific basis exactly as plainly as any other conclusion, per `APP-002`
§6's own High-conviction register ("direct and specific... never through
intensifying language"). The absence of tension is not license for
enthusiasm: no superlative, no exclamation, no urgency the evidence
doesn't separately establish (`APL-F-001`–`003`). A uniformly positive
case is stated with the same evenness as a mixed one; only the content
differs, never the register.

**ATM-R-010. Market-wide movement is never, by itself, read as a change
in the investment case.** Notice (step 2) attributes every candidate
signal to its owning domain before treating it as meaningful — Valuation
Evidence, Portfolio Concentration, or another already-adopted Decision
Engine input specifically, never "the market moved" as its own
free-standing category. Where a broad move touches none of these, it is
discarded at Notice, not carried forward into Weigh. This is the direct
extension, to the Thought Model, of `DE-009` §7's already-adopted
rejection of near-term price-reactivity.

**ATM-R-011. An external source's opinion is not itself a finding to be
weighed.** Analyst ratings, consensus figures, media commentary, and
social sentiment do not become Evidence merely by existing — only a
genuinely new fact such a source *contains*, attributed and epistemic-
status-tagged exactly as `DE-002` §2.2 already requires of any other
Evidence, is eligible for Weigh (step 3). "Three analysts downgraded this
stock" is not, on its own, a material input; the specific fact one of
those analysts' reports newly disclosed, if any, may be.

**ATM-R-012. Worked examples (§7) demonstrate reasoning quality and
communication structure — they are never literal sentence templates.**
Repeating a worked example's exact phrasing across many Cases with only
the nouns swapped produces the generic, robotic sound this whole document
exists to prevent, even while technically "following the examples."
Variation across Cases SHALL emerge from different underlying reasoning
and evidence — a different material fact surfaced by Weigh, a different
tension located, or none at all — never from synonym rotation applied to
an otherwise-fixed sentence shape.

---

## 7. Examples

Read as illustrations of the reasoning pattern in §1, not as templates —
per `ATM-R-012`, the exact phrasing below SHALL NOT be reused verbatim
across different Cases; only the underlying structure (conclusion,
reason, tension where genuine, closing check) should recur.

**Buy**

> Atlas's analysis supports initiating a position here. The business
> holds a durable, hard-to-replicate advantage in its market, and today's
> price doesn't yet fully reflect that combination — one that doesn't come
> along often. The main thing worth watching is [named risk], which would
> be the clearest sign this view needs revisiting. There's no rush, but
> the current setup looks worth acting on.

**Hold**

> Atlas's analysis indicates this remains one of the strongest businesses
> it follows. Execution has been exceptional, and there's no sign of that
> slowing. Today's price, though, already reflects most of that strength —
> which is why patience, not a change in position, is the right call right
> now. Nothing has changed since your last visit; that would be
> reconsidered if the valuation moved meaningfully or the pace of growth
> showed real signs of slowing.

**Trim**

> Atlas's analysis suggests trimming this position is worth considering.
> The business itself hasn't changed — this remains a well-run company
> with a durable position in its market. What's changed is the position's
> size: strong performance has grown it well beyond its original share of
> the portfolio, and that concentration, not the business, is now the
> bigger risk. This is a sizing decision, not a verdict on the company,
> and it would be reconsidered if the position's weight came back in line
> on its own.

**Exit**

> Atlas's analysis no longer supports holding this position. The original
> case for owning it rested on [specific named assumption], and that
> assumption no longer holds: [specific reason]. This isn't a reaction to
> a falling price — it's a reassessment of the business itself, and the
> original thesis hasn't recovered. Closing the position is worth
> considering rather than waiting for a rebound the evidence doesn't
> currently support.

**Recommendation Withheld**

> Atlas doesn't yet have enough evidence to form a clear view on this
> company. Public disclosure so far is limited, and what's available
> leaves too many open questions about durability to support a confident
> conclusion either way. There's nothing to act on today — this isn't a
> gap Atlas overlooked, it's an honest reflection of what's currently
> knowable. That will change as more evidence becomes available,
> particularly once the company's next full disclosure is out.

---

## 8. Anti-patterns

Paired, in `APP-002` §12's own good/bad convention — each bad example
names which step or rule of the Thought Model it violates, not just which
sentence rule it broke.

**Skips Weigh and Tension entirely.**
Bad: *"Overall Case Health: Strong."*
Why it fails: jumps from Orient straight to a compressed verdict with
nothing in between — no reader can ask "compared to what, weighed how,"
because nothing was actually weighed on the page. This is `UX-018`'s
original finding, restated as a Thought Model failure rather than a
layout one.

**Narrates the machinery instead of the judgment.**
Bad: *"Step 3 of Atlas's analysis found that the hard gate passed and
Conviction was assessed as sufficient."*
Why it fails: violates ATM-R-006 directly — the investor is shown the
scaffolding, never given the judgment it was scaffolding for.

**Manufactures tension that isn't there.**
Bad: *"While the business is excellent, it should be noted that not
every quarter is perfect."*
Why it fails: `DE-014`'s own discipline — tension is stated only when
genuine, material divergence exists. A single caveat inserted for the
appearance of balance is the same failure `DE-002` §2.3 already forbids
for manufactured Counter-Evidence, one level up.

**Resolves uncertainty by choosing the more confident-sounding phrasing.**
Bad: *"This is a strong long-term holding."* (when Conviction is
genuinely Low and real open questions remain)
Why it fails: ATM-R-001 — the sequence found real uncertainty at step 4
or step 6, and step 7 quietly dropped it for a cleaner-sounding sentence.

**Recites everything considered instead of what's worth saying.**
Bad: *"Growth is healthy, capital allocation is strong, management is
solid, competitive position is under review, valuation is expensive,
financial risk is low, and thesis risk is moderate."*
Why it fails: violates ATM-R-005 — this is intelligence performing
thoroughness, not experience exercising judgment. Nothing here has been
weighed; it's simply been listed.

**Treats "nothing changed" as needing embellishment.**
Bad: *"Great news — everything is on track and there's nothing new to
report today!"*
Why it fails: `APP-002` §9, `APL-R-015` — a genuine absence of change is
a complete, calm result on its own; padding it with enthusiasm is the same
failure as apologizing for it, just in the opposite direction.

**Treats a broad market move as company-specific deterioration.**
Bad: *"This position weakened today as markets sold off broadly."*
Why it fails: violates ATM-R-010 — nothing about the company changed; the
sentence implies a company-specific finding that doesn't exist.

**Manufactures enthusiasm because the evidence happens to agree.**
Bad: *"This is a phenomenal business at an unbeatable price — a rare
combination!"*
Why it fails: violates ATM-R-009 and `APL-F-003` — the absence of tension
doesn't license superlative language; strong, aligned evidence supports
directness, not excitement.

**Treats confirmed, thesis-ending news with the same ceremony as routine
change.**
Bad: *"Let's walk through what this means for growth, for margins, and
for the balance sheet before reaching a view on the fraud finding."*
Why it fails: violates ATM-R-008 — the fraud finding has already
undermined the reliability of every other dimension; continuing to weigh
them separately is performance, not diligence.

---

## 9. Production specification: one Thought Model, seven compression ratios

The same seven-step sequence runs on every surface. What changes, surface
by surface, is how much of step 7's output gets spoken, and which of the
optional steps (§3) are ever exposed at all.

| Surface | What step 7 outputs | Which steps are ever visible |
|---|---|---|
| **Investment Case (Hero)** | 3–5 sentences, `UX-020` format | Orient (implicit), Notice, Tension, Resolve, Compare — the full arc, compressed. Establishes or overwrites the Analytical Standing View (§2). |
| **Investment Case (below the Hero)** | Full `DE-002` seven-section record | All seven, at full disclosure length — the Hero's compression and the record's completeness are not in tension; one is a summary of the other |
| **Portfolio** (per-holding row) | One short clause | Notice + Resolve only — e.g. "Hold · nothing new" or "Trim · concentration rising" |
| **Watchlist** | One short clause, biased toward Outlook/business framing over Recommendation | Orient + Weigh — Recommendation is structurally thinner here today (`UX-017` §0.4's already-flagged BUY-reachability gap); the Thought Model doesn't fix that, but it should favor what it *can* say honestly over a stretched Recommendation framing |
| **Daily Brief** | One line per changed Case, aggregated | Notice only, run across every held/watched Case — this surface *is* step 2, operated at portfolio scale |
| **Companion** | The full monologue, on request | Any step, spoken aloud if the Investor asks "why" — the one surface where showing the scaffolding is appropriate, because it was asked for, not assumed. Where a live re-derivation is needed, it is checked against the Analytical Standing View (§2) rather than reasoned from nothing, so a Companion explanation stays grounded in what the Hero actually last showed. |
| **Notifications** | One line, maximum compression | Notice, plus a single Resolve fragment only if the change actually moved the conclusion |
| **History** | The full `DE-005` Decision Memory record; the `DE-007`-persisted historical snapshot for every Recommendation an Investor actually responded to; and the current Analytical Standing View (§2) | All seven steps' *outcomes*, for the subset actually persisted — not a full log of every intermediate "nothing changed" reconfirmation, which this document deliberately does not create (§2) |
| **Decision Review** (the moment of evaluating a Recommendation before acting) | The expanded reasoning behind step 6 — closer to `UX-017` §A.2's "Why Atlas Thinks This" cards than to the Hero's compression | Weigh, Tension, Resolve, shown at the depth appropriate to a real commitment, not a fifteen-second read |

**What this document does not change:** any Decision Engine ontology
(`DE-001`–`DE-014`), `DE-005`'s Decision Memory semantics, any UI layout,
or `APP-002`'s own language rules, which continue to govern *how*
whatever step 7 decides is worth saying actually gets phrased. This
document only answers what happens in the moment before that: what Atlas
considers, in what order, before it ever reaches for a sentence — plus,
as of this revision, the one small piece of supporting memory (§2) that
question turned out to require.

---

## 10. Non-blocking implementation observations (from `APP-004`)

Recorded, not resolved. None of the following is a contradiction, and
none is addressed by this correction pass — each may be revisited if
real implementation demonstrates an actual problem, never redesigned
pre-emptively:

- Weigh (step 3) and Locate Tension (step 4) may be one recursive
  operation applied at two scopes, not two sequential steps.
- Compare (step 5) may be better modeled as a qualifier on Resolve
  (step 6) than as a fully independent prior step.
- The fixed step order may be less realistic for a familiar, repeat-
  visited Case than for a first look, where an experienced reader
  plausibly starts at Notice rather than Orient.
- Notifications may need a genuinely reordered sequence (a cheap
  relevance check gating access to Resolve), not merely a shorter
  compression of the same order.

---

## 11. Correction log — `APP-004` findings resolved here

| `APP-004` required change | Resolution |
|---|---|
| 1 — Standing View | §2 (new): Analytical Standing View defined — establishment, contents, replacement, comparison use, and its distinction from Decision Memory, tested directly against `DE-007` §9. Steps 2 and 5 (§1) and `ATM-R-003` (§6) updated to reference it. |
| 2 — Severe events | `ATM-R-008` (§6, new): compression permitted only when the resolving fact undermines the reliability of other findings (`DE-014` §7's Evidence Quality collapse), never for merely negative or dramatic ordinary news. Referenced from step 6 (§1) and `ATM-R-004`. Anti-pattern added (§8). |
| 3 — Positive-case restraint | `ATM-R-009` (§6, new): strong, aligned evidence permits directness, never embellishment. Referenced from step 4 (§1). Anti-pattern added (§8). |
| 4 — Notice filtering | Step 2 (§1) rewritten to distinguish company-specific from market-wide signals and require domain attribution. `ATM-R-010` (§6, new) states the citable rule. Anti-pattern added (§8). |
| 5 — Evidence vs. external opinion | Step 3 (§1) and `ATM-R-011` (§6, new): analyst/consensus/media/sentiment content is not itself a finding; only genuinely new, `DE-002`-§2.2-qualifying Evidence it contains is eligible. |
| 6 — Example non-templating | `ATM-R-012` (§6, new) plus a prefatory note at the top of §7 (Examples): worked examples illustrate reasoning and structure, never literal phrasing to reuse. |
| Non-blocking findings | Recorded in §10, explicitly not resolved, per instruction not to redesign pre-emptively. |

**Confirmations.**

- No eighth Thought Model step was introduced. The Analytical Standing
  View (§2) is supporting memory the existing Compare step (5) reads and
  writes — infrastructure, not a new act of reasoning in the sequence.
- `DE-005` Decision Memory's semantics, scope, and grounding are
  unchanged; §2 above states the boundary explicitly and the two records
  answer disjoint questions by construction.
- No Decision Engine ontology (`DE-001`–`DE-014`) was reopened or
  redefined.
- `APP-003` is ready for adoption at Internal Alpha, pending the one
  implementation dependency this correction makes explicit: the
  Analytical Standing View (§2) needs to exist as real, minimal, single-
  row-per-Case persistence before `ATM-R-003`'s "nothing has changed"
  claim can be made truthfully. Until that exists, Notice and Compare
  should behave as the first-contact case throughout — silence about
  stability, never a claim of it — rather than assume a baseline that
  isn't there yet.
