# UX-020 — Investment Case Hero: Voice Redesign

**Status:** Communication-first redesign of the Hero, superseding *how*
`UX-019` presents its content, not *what* `UX-019` decided matters. `UX-019`
established the priority order — Recommendation and Conviction dominant,
Risk elevated and undiluted, Priority as a distinct urgency signal, Expected
Return present but demoted, Case Health and standalone Confidence cut
entirely. Every one of those judgments still holds. What changes here is
the *mode*: those facts stop being four visual rows of labels and become
one paragraph, because a label can be read but a paragraph is the thing
that gets *understood*. This document is written against, and stays
compliant with, `docs/atlas_product_architecture/APP-002-Atlas-Product-Language.md`
— the voice, tone, and sentence-construction rules below are not invented
for this sprint; they already exist as adopted doctrine, and this document
is largely the act of finally applying them to the one screen that has
never used them.

---

## 1. Critique: the current Hero, as a piece of communication

Read the current Hero out loud. It cannot be done — not because the words
are wrong, but because there are no sentences. "STRONG." "HIGH." "8–12%
annualized." "+22% / -15%." These are not things a person says to another
person; they are things a terminal prints. A dashboard's fundamental
communication failure is not that it's ugly or cluttered — it's that it
has no grammar. There is no subject, no verb, no "because," no "though," no
"which means." Six facts sit next to each other with no stated
relationship between any of them, and the investor is left to do the one
job Atlas exists to do on their behalf: reasoning across the facts to reach
a conclusion.

This is the precise failure `APP-002` §2 already names: *"Atlas
communicates the way a trusted long-term investment partner does: someone
who has done the reading, states plainly what they found, distinguishes
what they know from what they are inferring."* A badge cannot distinguish
what is known from what is inferred — a badge can only assert. "Expected
Return: 8–12%" and "Confidence: High" sitting in the same row look like the
same kind of claim, carrying the same weight, when they are not remotely
the same kind of claim — one is a computed estimate with real assumptions
behind it, the other is a judgment about how well those assumptions hold
up. Prose can hold that distinction in a single sentence. A row of badges
cannot hold it at all.

And the deepest problem is not visual, it's psychological: a dashboard
asks the investor to *trust the label*. A conversation asks the investor to
*follow the reasoning*. Those produce entirely different relationships with
the same underlying analysis, and only one of them is the relationship
`APP-000` and `APP-002` were written to build.

---

## 2. The Hero, rewritten

Four scenarios, to show the voice holds up across genuinely different
news — not just the easy case.

**Steady, high-conviction Hold**

> Atlas's analysis indicates this remains one of the strongest businesses
> it follows. Execution has been exceptional, and there's no sign of that
> slowing. Today's price, though, already reflects most of that strength —
> which is why patience, not a change in position, is the right call right
> now. Nothing has changed since your last visit; that would be
> reconsidered if the valuation moved meaningfully or the pace of growth
> showed real signs of slowing.

**Portfolio-driven Trim — business unchanged**

> Atlas's analysis suggests trimming this position is worth considering.
> The business itself hasn't changed — this remains a well-run company with
> a durable position in its market. What's changed is the position's size:
> strong performance has grown it well beyond its original share of the
> portfolio, and that concentration, not the business, is now the bigger
> risk. This is a sizing decision, not a verdict on the company, and it
> would be reconsidered if the position's weight came back in line on its
> own.

**Recommendation Withheld — honest absence of a view**

> Atlas doesn't yet have enough evidence to form a clear view on this
> company. Public disclosure so far is limited, and what's available
> leaves too many open questions about durability to support a confident
> conclusion either way. There's nothing to act on today — this isn't a
> gap Atlas overlooked, it's an honest reflection of what's currently
> knowable. That will change as more evidence becomes available,
> particularly once the company's next full disclosure is out.

**Something changed, doesn't move the conclusion**

> Atlas's view on this company hasn't changed, but something worth a quick
> look has: the latest results showed margins under more pressure than
> expected. It isn't enough on its own to change the recommendation — the
> core business remains strong, and this looks like a single-quarter wobble
> rather than a structural shift. Still, it's worth watching the next
> report to see whether the pressure continues or eases. No action is
> needed today, but this is the one thing worth keeping an eye on.

Every one of these opens with the conclusion, never with data. Every one
names its specific reason in the same breath as its claim. Every one closes
by answering, plainly, whether today requires anything from the investor,
and what would change Atlas's mind. None of them uses a superlative,
raises its register, or asks to be trusted without being checkable.

---

## 3. Atlas's communication style, for the Hero specifically

This section states nothing `APP-002` doesn't already establish — it names
which parts of that already-adopted standard matter most at Hero scale,
where there is no room for drift, because there is only one paragraph to
get right.

**Voice** (unchanged from `APP-002` §3, restated for emphasis): calm,
professional, thoughtful, transparent, respectful, patient, objective,
evidence-driven. Never emotional, sensational, promotional, or absolute
without evidence.

**Hero-specific rules, on top of the general standard:**

- **One paragraph. No headers, no bullets, no labels inside it.** The
  paragraph is the primary content; anything structural breaks the
  sentence-to-sentence reasoning the whole exercise depends on.
- **Sentence one is always the conclusion.** No exceptions — never
  "here's the data" before "here's what it means."
- **Every claim carries its own reason in the same sentence, or the very
  next one.** "The business is strong" alone is a label wearing a
  sentence's clothing; "the business is strong because execution has
  outpaced plan for six straight quarters" is a sentence.
- **Real tension is stated as tension, in one connected thought — "though,"
  "but," "while" — never as two separate, disconnected facts.** This is
  `DE-014`'s already-adopted composition discipline (preserve divergence,
  never collapse it), now expressed as a sentence-construction rule rather
  than a data-modeling one.
- **The closing sentence always answers two things: does today require
  anything, and what would change Atlas's mind.** Where those two answers
  are naturally the same thought (as in the Hold and Trim examples above),
  one sentence carries both. Where they need separating (as in the
  Withheld example), two sentences do.
- **Never write "STRONG," "HIGH," or any capitalized label inside the
  paragraph itself.** Recommendation and Conviction are described in
  sentence form here — a small, quiet confirming badge may still appear
  beneath the paragraph (§5), but it echoes what the prose already said,
  it never introduces something the prose didn't.
- **Target length: 60–90 words, three to five sentences.** At normal
  reading speed this reads in roughly fifteen to twenty-five seconds —
  comfortably inside the thirty-second budget this sprint is built around,
  with room left for the confirming badge strip beneath it.

---

## 4. Why this creates more trust than a dashboard

A number asks to be believed. A reason asks to be checked. `APP-002` §2
states this as a governing principle rather than a preference: *"Persuasive
language, by its nature, is language optimized to be believed rather than
language optimized to be checked — and a product whose entire purpose is to
strengthen Investor Judgment cannot use language that discourages the
Investor from checking it."* A badge is, structurally, the more persuasive
format — it looks authoritative, decisive, terminal-grade — and it is,
for exactly that reason, the format that discourages checking. A sentence
that names its own reason invites the opposite reaction: an investor
reading "patience, not a change in position, is the right call because
today's price already reflects most of that strength" can disagree with
the *reasoning*, weigh it against what they know, and reach their own
judgment — which is the entire point of a decision-support product, not a
side effect of it.

There is also a structural honesty argument, not just a psychological one:
**a badge cannot carry a caveat, and a sentence can.** "Confidence: High"
has no room in it for "though one open question remains." A well-written
sentence does, easily — and because prose makes room for the caveat, it
makes the caveat *harder to quietly drop*. A dashboard's cleanliness is
often achieved by omission; a paragraph's honesty is enforced by its own
grammar. This is why the four rewritten scenarios in §2 all read as
credible even in the Withheld and Trim cases, where the news is
unglamorous — the format itself resists overclaiming in a way badges
never had to resist anything.

Finally: a dashboard, read once, is the same the tenth time. A paragraph
that says "nothing has changed since your last visit," calmly, in the same
voice as everything else, is what actually earns the long-run trust
`APP-002` §4 describes for long-term monitoring — *"Tone treats repetition
of 'nothing has changed' as ordinary and correct... never a state
requiring apology, filler content, or an artificially generated update."*
A badge row has to invent variation to avoid looking broken when nothing
changed. A sentence doesn't — it just says so, and that plainness, repeated
honestly over months, is what makes an investor believe Atlas the tenth
time as much as the first.

---

## 5. Production-ready Hero specification

**Structure, top to bottom:**

1. **Identity strip** (unchanged from `UX-019`): ticker, company name,
   exchange/sector, "as of [date/time]" — smallest type on the page, top
   corner, orientation only.
2. **The paragraph** (this document's primary addition): one paragraph,
   60–90 words, three to five sentences, set in a reading-register
   typeface — larger and more generously leaded than anything else on the
   page, closer to how a well-set pull-quote or a letter reads than how a
   data label reads. This is the single largest block of continuous text
   on the Hero, and it should look like something written for a person to
   read, not like a field with a value in it.
3. **The confirming strip** (quiet, secondary, directly beneath the
   paragraph): small, compact badges that echo — never introduce —
   exactly what the paragraph already said, in the same order the
   paragraph said it:
   - Recommendation + Conviction, fused on one line, small type (e.g.
     "Hold · High Conviction") — a confirmation for a reader scanning back
     up after finishing the paragraph, not a competing headline.
   - Expected Return, smallest type of the strip, one compact line with
     its stated basis ("8–12% annualized (range: −15% to +22%)") —
     present because `UX-019` established investors would miss it if it
     vanished, demoted because it answers "how much," a question the
     paragraph deliberately doesn't lead with.
   No badge for Case Health, standalone Upside/Downside, or Confidence —
   `UX-019`'s cuts stand; the paragraph has already made the case for why
   those never earned a place.
4. **The priority/risk content lives inside the paragraph, not beside
   it.** `UX-019` gave Risk and Priority their own visual rows because the
   Hero was built from fragments that needed separate boxes to be legible
   at all. In a paragraph, they don't need boxes — they need clauses,
   and the four worked examples in §2 show exactly where those clauses
   belong (the "though" and "still" constructions doing the work rows used
   to do).

**States:**

- **Loading.** Prose, not a spinner: *"Atlas is preparing its current view
  of [Company]..."* — per `APP-002` §10's own loading-message rule, stated
  in concrete terms, never a bare "Loading…"
- **Recommendation Withheld.** The third worked example in §2 — a
  complete, honest paragraph, never an empty state, never apologized for.
- **Freshly changed.** The fourth worked example's pattern — the paragraph
  itself carries the "what's new" content; no separate banner competes
  with it for the investor's first fifteen seconds.

**What this explicitly does not change:** the underlying facts available
to the Hero (`UX-017`'s data contract), the honest-gap treatment for
Expected Return and Bull/Base/Bear where they remain backend-unavailable
(the paragraph simply omits a sentence about magnitude rather than stating
one it can't support — the same discipline `APP-002` §7's "Unknown" pattern
already requires), or anything below the Hero. This document changes one
thing: how the Hero speaks. Everything it says was already true before this
sprint. It just wasn't being said like someone meant it.
