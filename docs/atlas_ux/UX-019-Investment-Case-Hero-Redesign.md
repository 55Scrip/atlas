# UX-019 — Investment Case Hero Redesign

**Status:** Focused redesign of one screen. Nothing below the Hero is in
scope. Written for the target-state product, not constrained by today's
backend — where a proposed element needs backend capability that doesn't
exist yet, that's noted in-line, briefly, without changing the design.

---

## The 15-second test

An investor opens this page for fifteen seconds before work. What must
they walk away knowing? Everything else can wait for the forty-five
seconds after that, or the five minutes after that. Four questions, and
only four, define what belongs in this zone:

**What should I think? Why? Do I need to act? Can I trust this?**

Every element below is judged against these four questions and nothing
else. Visual polish is not a criterion. Completeness is not a criterion.
Decision speed is the only criterion.

---

## 1. Element-by-element verdict

| Element | Verdict | Why |
|---|---|---|
| **Recommendation** | **Keep. Dominant.** | The direct answer to "what should I think." Everything else in the Hero exists to support or qualify this one fact. |
| **Conviction** | **Keep. Fused with Recommendation, never separate.** | A Recommendation without its Conviction is an incomplete sentence — "Hold" alone doesn't tell you whether Atlas is confident or barely clearing the bar. It answers "why should I trust this" as much as it qualifies "what should I think." It must sit on the same line as the Recommendation, not float as an independent badge elsewhere in the row. |
| **Overall Case Health** | **Cut entirely.** | This is a composite of things the Hero already states individually (Recommendation, Conviction, Risk). It cannot be explained on its own — an investor cannot ask "why STRONG?" and get an answer, because nothing produced that specific word; it's a vibe sitting next to three real judgments. It is also the least actionable word on the page: it changes nothing about what the investor does next. Removing it costs nothing an investor would notice missing, because Recommendation + Conviction + Risk already tell the same story with attribution. |
| **Expected Return** | **Keep. Demoted — smallest tier, bottom of the Hero.** | "How much" is a real, legitimate question, but it is a second-order one. Answering "what should I think" first and "how much" second is the correct order for decision quality: an investor who anchors on a return number before understanding the underlying conclusion is more likely to make a worse decision, not a faster one. Demote, don't delete — an investor would miss this if it vanished entirely. |
| **Upside / Downside** | **Cut as a separate element; merge into Expected Return.** | This is the same question as Expected Return, asked a second time in a different shape. Two numbers both claiming to answer "how much could this move" is not two facts, it's one fact shown twice with no stated relationship between them — which is confusing, not thorough. One compact range, one place. |
| **Confidence** | **Cut entirely from the Hero.** | Either this duplicates Conviction (in which case it's redundant), or it's the investor's own self-reported figure (in which case it does not belong styled identically to Atlas's own judgments — showing them side by side implies they're the same kind of claim, and they aren't). Neither reading earns it a place in the fifteen-second zone. |
| **Biggest Opportunity** | **Cut as a standalone, separately-labeled element; fold into Recommendation's own reasoning clause.** | In practice, "the biggest reason to like this business" and "the reason behind the Recommendation" are almost always the same fact. Keeping both is asking the investor to read the same idea twice under two different headings. The full strengths story still exists one section down the page — nothing is lost, only deferred to where an investor who wants the fuller case can find it. |
| **Biggest Risk** | **Keep. Elevated — its own full-width line, not paired 50/50 with Opportunity.** | This is the one element this redesign gives *more* room than the current design does. A rushed investor's most important question after "what should I do" is "what could make that wrong" — and a risk squeezed into half a column, at equal visual weight to an opportunity, does not communicate "pay attention to this." Risk earns undiluted space, closer to the Recommendation than anything else on the page except Conviction. |
| **Current Priority** | **Keep. Repositioned as an urgency/change signal, distinct from Risk.** | Risk is a standing fact about the case; Priority is about what's *new* — whether anything has changed since the investor last looked. These are different questions ("what worries Atlas, generally" versus "did anything happen that needs me specifically, right now") and collapsing them into one line would blur "do I need to act" into "what's the ongoing risk," which are genuinely different psychological questions the brief itself names separately. |

---

## 2. The redesigned Hero, row by row

**Row 0 — Identity strip.** Ticker, company name, exchange/sector, and a
small "as of [date/time]" marker, in the smallest type on the page, top
corner. Its only job is orientation and freshness — the freshness marker
is new; nothing in the current design tells an investor how current the
analysis is, and that omission is a real trust cost in fifteen seconds
("is this today's picture, or three weeks old?").

**Row 1 — Recommendation + Conviction (dominant, largest type on the
page).** *"Hold — Thesis Intact"* in the largest, boldest type on the
screen, immediately followed on the same line by a smaller, clearly
distinct Conviction badge ("High Conviction"). Directly beneath, one
evidence-attributed sentence — the compressed "why," carrying both the
strongest support for the conclusion and, where a genuine tension exists,
the countervailing fact in the same breath: *"Business quality remains
exceptional; current valuation offers little margin of safety."* This
sentence is written to include tension only when real tension exists —
never manufactured for balance, per the same discipline that governs
every other Atlas output in this product.

**Row 2 — Biggest Risk (its own full-width line, second-largest visual
weight).** *"What worries Atlas most: [specific, named risk], because
[the specific reason]."* Full width, not sharing a column with anything.
This is the row that most directly answers "why," beyond the compressed
clause in Row 1, and it is positioned immediately after Recommendation
deliberately — before Priority — so that a maximally rushed reader who
stops after two rows still sees the risk, not just the freshness signal.

**Row 3 — Current Priority (medium weight, visually distinct treatment —
e.g. a small marker that's present only when something changed).**
Either *"Nothing requires your attention right now"* (calm, quiet
styling) or *"New since your last visit: [specific change] — review
recommended"* (a visually distinct marker, not alarming, but clearly
different from the steady-state copy). This is deliberately **not**
readable as "nothing to worry about" — Row 2's risk is always shown
regardless of what this row says, precisely to prevent a "nothing new"
Priority line from being misread as "nothing risky."

**Row 4 — Expected Return (smallest tier, quiet/secondary color,
bottom of the Hero).** One compact line: *"Expected return: 8–12%
annualized (range: −15% to +22%)"* — basis always stated, never a bare
number. This is the last thing an investor's eye reaches in the Hero, by
design.

**Cut, with no trace in the Hero:** Overall Case Health, a standalone
Upside/Downside badge, Confidence, a separately-labeled Biggest
Opportunity element.

---

## 3. Reading order and the four questions

| Question | Answered by |
|---|---|
| **What should I think?** | Row 1 — Recommendation, largest element on the page, read first by construction (position and size). |
| **Why?** | Row 1's own sentence (compressed), then Row 2 (Risk, the strongest countervailing or supporting fact given real weight). |
| **Do I need to act?** | Row 3 — Priority, answered as a distinct, separately-styled signal so it can't be confused with the standing Risk in Row 2. |
| **Can I trust this?** | The freshness marker (Row 0), Conviction stated honestly next to the Recommendation rather than implied (Row 1), and Expected Return always carrying its stated basis rather than a bare, falsely-precise number (Row 4). Trust here comes from calibration and transparency, not from confident-sounding language. |

Four rows, four questions, one answer per question, no question answered
twice under a different name.

---

## 4. Why this is faster and better for decisions

**Faster, because the page now has exactly one reading path instead of
six competing entry points.** The current Hero asks the eye to choose
among six co-equal badges with no signal about which to read first. This
redesign removes that choice entirely — there is one largest element,
one clear next row, one clear row after that. An investor doesn't have to
decide what to look at; the hierarchy decides for them, which is what
"fifteen seconds" actually requires.

**Better, because nothing is stated twice under a different name.**
Overall Case Health, standalone Upside/Downside, Confidence, and a
separate Biggest Opportunity box were each either a duplicate of
something else in the Hero or an unexplainable composite of it. Removing
duplication doesn't just save space — it removes the small, corrosive
uncertainty of "wait, is this the same thing as that other number?",
which is itself a tax on trust and reading speed even when the investor
doesn't consciously notice paying it.

**Better, because Risk is no longer diluted.** Giving Risk its own
full-width line, positioned ahead of the freshness/priority signal,
means an investor cannot walk away from a fifteen-second read without
having seen the one fact most likely to change their mind — which is a
direct, concrete improvement in decision quality, not just page tidiness.

**Better, because honesty is now structurally part of the hierarchy, not
an afterthought.** Conviction is fused to the Recommendation instead of
floating as a separate badge; Expected Return always carries its basis;
freshness is stated for the first time. None of this makes the Hero look
more impressive — all of it makes the Hero more truthful about exactly
how much weight each number deserves, which is what actually earns an
investor's trust over repeated use, not confident styling on a first
visit.
