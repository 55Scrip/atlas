# Temporary Workspace UX Flow

**Created:** 2026-07-08 (Sprint 287)
**Status:** CANONICAL — screen-by-screen UX flow. No runtime implementation.
**Source specification:** [docs/AtlasAlphaExperienceSpecification.md](AtlasAlphaExperienceSpecification.md)
**Card rendering contract:** [docs/TemporaryWorkspaceCardRenderingContract.md](TemporaryWorkspaceCardRenderingContract.md)
**Chapter:** 2 — Building the Product

---

## Purpose

This document transforms the Atlas Alpha Experience Specification into a screen-by-screen product flow. It is the primary reference for the first Atlas Alpha prototype.

After reading it, a designer or frontend engineer should be able to build the first prototype without asking: "How should this work?"

It covers six sequential screens:

1. Landing Screen
2. Processing State
3. Temporary Workspace
4. Weekly Review Preview
5. Snapshot Draft Preview
6. Save Workspace Prompt

Each screen is described with: purpose, user goal, Atlas goal, primary content, secondary content, available actions, empty states, error states, success states, and emotional objective.

---

## How to Read This Document

Each screen describes what the user sees, why it exists, and what Atlas is trying to accomplish. Wireframe-level layout notes are included as prose — not as visual designs.

**User question** means: the question the user is holding when this screen appears.
**Emotional objective** means: what the user should feel when they leave this screen.
**Earn the next interaction** means: this screen has done enough that the user wants to continue.

---

---

# Screen 1 — Landing Screen

---

## Purpose

The Landing Screen is the entire first impression. It establishes what Atlas is, what the user should do first, and that no commitment is required. It must accomplish this in under ten seconds.

**User question:** *Is this worth my time? What do I do?*

---

## User Goal

Understand whether Atlas is relevant to them and decide to try it.

---

## Atlas Goal

Establish trust and get out of the way. The Landing Screen is not a sales page. It is an invitation to begin.

---

## Primary Content

### Headline

One sentence. Plain language. No financial jargon. No numbers.

> **Think more clearly about your investments.**

Or:

> **Atlas helps you structure what you already know.**

The headline must not contain: buy, sell, returns, alpha, outperform, gain, beat, track, monitor, signals, portfolio optimisation, or similar.

### Supporting text

One sentence below the headline. Describes what the user does, not what Atlas does.

> Paste in your portfolio, a company name, or anything you're thinking about — Atlas structures it for you.

### Paste box

A large, single-focus text area, centred on the page. The paste box is the primary action surface — not a button.

**Placeholder text (visible before user types):**

> Paste your portfolio, a ticker, a research note, or a question you're sitting with.

The placeholder is not instructional. It is an invitation. It suggests possibilities without requiring a format.

**Minimum visible size:** Large enough that the user can type a paragraph without scrolling.

**Position:** Centre of the viewport. Nothing below the fold is required to begin.

### Examples (below the paste box)

Three short, clickable example inputs. Clicking an example populates the paste box.

> `AAPL 100 shares, MSFT 50 shares, NVDA 25 shares`

> `I've been holding Apple for three years. The thesis was iPhone dominance but I'm not sure the AI angle changes things.`

> `Should I be worried about my Microsoft position given recent AI competition?`

Each example is one line. They are not labelled "Example 1", "Example 2". They appear as clickable chips or plain text links — visually quiet.

**Purpose of examples:** Remove the "what do I type?" anxiety for first-time users. The examples show that Atlas accepts imperfect, natural input.

### Privacy messaging

Below the examples, one line:

> Nothing is stored until you choose to save it.

This is not optional. It appears before the user submits anything.

### No-account messaging

Immediately below the privacy line, one line:

> No account required.

These two lines appear together, in smaller text, without an icon. They are not a checkbox. They are statements of fact.

### Submit button

One button, directly below or adjacent to the paste box:

> Analyse

The button is active as soon as the user types or pastes anything. It is not disabled before then — but clicking it with an empty paste box does nothing alarming (the paste box gently draws focus).

---

## Secondary Content

- No navigation bar beyond a minimal logo
- No feature list
- No pricing table
- No testimonials
- No charts or graphs
- No social proof
- No login link in the header (may be a small "Sign in" link in the far corner for returning users — not prominent)

---

## Available Actions

| Action | Result |
|---|---|
| Type or paste into the paste box | Paste box becomes active; submit button activates |
| Click an example chip | Paste box populated with example text; submit activates |
| Click Analyse | Transitions to Processing State (Screen 2) |
| Press Enter (with content) | Same as clicking Analyse |
| Press Escape | Clears the paste box (with confirmation if content is long) |

---

## Empty States

**Empty paste box, user clicks Analyse:**
The paste box outline pulses once. Focus returns to the paste box. No error message. No red. No "required field" text.

**User arrives with no prior session:**
The Landing Screen is shown as described. No "You have no saved workspaces" message. The user starts fresh.

---

## Error States

There are no error states on the Landing Screen. Validation happens after submission, not before. The Landing Screen never rejects input.

---

## Success State

The user has typed or pasted something and clicked Analyse. The Landing Screen transitions to the Processing State. The transition is a smooth fade — not a flash or a hard cut. The paste box content is not visible during transition (no jarring layout shift).

---

## Emotional Objective

**The user should feel:** *This is calm and clear. I know what to do. I'm not being sold to. I can just try it.*

**Earn the next interaction:** The Landing Screen earns the user's willingness to submit their first input.

---

---

# Screen 2 — Processing State

---

## Purpose

The Processing State is the moment between submission and the Temporary Workspace appearing. It signals that something careful is happening — not that Atlas is slow.

**User question:** *Is this working? What's happening?*

---

## User Goal

Understand that Atlas has received their input and is doing something with it.

---

## Atlas Goal

Make the transition feel intentional. Not instant (which would feel shallow). Not slow (which would feel broken). A brief, purposeful pause.

---

## Primary Content

The Processing State replaces the Landing Screen entirely. The paste box is gone. The layout is clean and centred.

### Progress statement

A single sentence, displayed in the centre of the screen. It changes on a 400ms interval — each line replacing the previous one. No animation between lines; a clean crossfade.

```
Reading your input…

Finding what you've shared…

Structuring what we know…
```

These lines are not "AI thinking" copy. They describe what is actually happening: Atlas is reading, finding entities, and structuring the content. They are neutral, calm, and accurate.

**What these lines must not say:**
- "Our AI is analysing your portfolio…"
- "Running advanced algorithms…"
- "Checking market data…"
- "Processing with machine learning…"

### No progress bar

No percentage. No spinner. No animation beyond the text crossfade. A spinner implies waiting. A calm sentence implies purposeful activity.

---

## Secondary Content

None. The Processing State is intentionally sparse. No navigation. No other content. Nothing to read, click, or dismiss.

---

## Available Actions

None during the processing sequence. The user waits. This is deliberate — the wait is short (under two seconds in Alpha 0.1) and the sparseness creates a moment of calm before the Temporary Workspace appears.

**If processing takes longer than 3 seconds:**

An additional line appears below the sequence, in smaller text:

> Still working — this takes a moment.

**If processing takes longer than 10 seconds:**

A single button appears:

> Try again

Clicking it returns to the Landing Screen with the user's input still in the paste box.

---

## Empty States

Not applicable. The Processing State only appears when the user has submitted input.

---

## Error States

**Processing fails completely:**

The Processing State clears. A single message appears in the centre:

> Something went wrong. Your input has not been lost.
>
> [Try again]

Clicking Try again returns to the Landing Screen with the user's input preserved in the paste box.

---

## Success State

The final progress line ("Structuring what we know…") completes. The Temporary Workspace fades in. The transition is smooth — the Processing State fades out as the Temporary Workspace fades in.

---

## Emotional Objective

**The user should feel:** *Something careful is happening. This is not instant because it is trivial — it is taking a moment to be thorough.*

**Earn the next interaction:** The Processing State earns the user's expectation that the Temporary Workspace will contain something meaningful.

---

---

# Screen 3 — Temporary Workspace

---

## Purpose

The Temporary Workspace is Atlas's primary output surface. It shows everything Atlas has found, surfaced, and structured from the user's input. It is the first moment of real value.

**User question:** *What did Atlas find? Is this useful?*

---

## User Goal

See their input transformed into structured, readable output. Explore what Atlas has surfaced. Have the first "aha" moment.

---

## Atlas Goal

Deliver value immediately. The Temporary Workspace must be useful on first sight — not after the user has read a tutorial or clicked through a setup flow.

The first "aha" moment is the target: the user reads an Assumption card or Risk card and thinks *I didn't know I was making that assumption* or *I hadn't named that risk.* This must happen within the first 90 seconds.

---

## Layout

The Temporary Workspace has three zones:

**Header zone:** Title, status badge, and workspace metadata.
**Card zone:** All Workspace Cards, in the specified order.
**Footer zone:** Save prompt and session status.

The card zone is scrollable. The header zone stays visible while scrolling. The footer zone stays visible while scrolling (sticky footer).

---

## Primary Content

### Header

**Title:** Derived from what Atlas found.
- If the input contained a single ticker: `AAPL — Temporary Workspace`
- If the input contained a portfolio: `Your Portfolio — Temporary Workspace`
- If the input was free text: `Your Input — Temporary Workspace`
- If the input was a question: `Your Question — Temporary Workspace`

**Status badge:** `Temporary · Not saved` — visible in the header at all times until the workspace is saved.

**Summary line:** One line, below the title:

> Atlas found [N] things in your input.

Where N is the total number of cards. This line does not enumerate the card types — it is a simple, calm acknowledgement that something was found.

### Cards — Ordering and Rationale

Cards appear in this fixed order. The order is not random, not alphabetical, not by confidence score. It follows the sequence: what is this → what do we know → what are we assuming → what could go wrong → what we don't know.

---

#### Position 1: Entity Card(s)

**Why it exists:** The user needs to see that Atlas understood what they were writing about before they can trust anything else on the page. Entity cards anchor the workspace.

**Why it appears first:** Everything else in the workspace is about this entity. The user should confirm Atlas got it right before reading evidence, assumptions, or risks about it.

**When it is omitted:** Never. If Atlas cannot identify an entity, the workspace shows a Disambiguation Card in this position instead (see Disambiguation below).

**Content:**
- Entity type label: `Company`, `Holding`, `Portfolio`, `Watchlist Entry`
- Entity name: `Apple Inc.`
- Ticker (if applicable): `AAPL`
- One-line description (from company facts, if available): `iPhone, Mac, and services company. Largest public company by market capitalisation.`

**Expand state:** Shows linked evidence items, linked assumptions, and linked risks.

---

#### Position 2: Evidence Card(s)

**Why it exists:** Evidence is the foundation of everything else in the workspace. The user should see what Atlas is working from before they see the conclusions drawn from it.

**Why it appears second:** Evidence comes before assumptions and risks. Showing conclusions before evidence would undermine trust.

**When it is omitted:** If no evidence is available from the user's input or stored sources, evidence cards are omitted. An uncertainty card may appear in their place (see Position 6).

**Content (one card per evidence item):**
- Evidence type label: `Company Facts`, `Research Note`, `Your Observation`, `Price`, `Portfolio Holding`, `Journal Entry`
- Evidence body: one to two sentences summarising the evidence item
- Source and freshness: `From your input · Today` or `Company facts · Last updated 3 months ago`
- Quality label (from Evidence Quality Review vocabulary): `Strong`, `Adequate`, `Incomplete`, `Weak`, `Outdated`, `Conflicting`

**Expand state:** Full evidence text, source link (if applicable), linked assumptions and risks.

---

#### Position 3: Assumption Card(s)

**Why it exists:** Assumptions are what make the investment thesis work. Most users have never named their assumptions explicitly. Surfacing them is Atlas's most distinctive contribution.

**Why it appears third:** Assumptions are derived from evidence. Seeing the evidence first prepares the user to recognise where their assumptions came from.

**When it is omitted:** If Atlas cannot surface any assumptions from the provided input, assumption cards are omitted. This is rare — even minimal input ("I'm holding Apple") implies assumptions.

**Content (one card per assumption):**
- Assumption type label: `Business`, `Financial`, `Competitive`, `Management`, `Industry`, `Regulatory`, `Macro`, `Valuation`, `Portfolio`, `User`
- Assumption body: written in second person, direct, plain language
  > You are assuming that Apple's revenue growth will remain above 15% annually.
- Evidence link label: `Supported by 1 evidence item` or `No supporting evidence found`
- Assumption state: `Evidence-supported`, `Partially supported`, `Unsupported`, `Contradicted`, `Obsolete`

**Expand state:** Linked evidence items, linked risk cards, open questions about this assumption.

**Why second person:** "You are assuming" is more useful than "The thesis assumes." It makes the assumption personal and recognisable. It does not imply criticism — it implies visibility.

---

#### Position 4: Risk Card(s)

**Why it exists:** Risks are what could cause the investment thesis to fail. They are derived from assumption failures. Showing risks after assumptions makes the causal chain visible: assumption → what happens if it fails → risk.

**Why it appears fourth:** Risks are conclusions drawn from assumptions and evidence. They belong after the inputs they are derived from.

**When it is omitted:** If no assumptions were surfaced, risk cards are omitted. If assumptions were surfaced but Atlas cannot identify risks from them, risk cards are omitted.

**Content (one card per risk):**
- Risk category label: `Business Risk`, `Financial Risk`, `Competitive Risk`, `Management Risk`, `Industry Risk`, `Regulatory Risk`, `Macro Risk`, `Valuation Risk`, `Portfolio Construction Risk`, `Behavioural Risk`
- Risk body: plain language, calm tone, not alarmist
  > If revenue growth slows below 15%, the current valuation may need to be revised.
- Linked assumption: `Linked to: Revenue growth assumption`
- Evidence quality: `Evidence quality: Adequate`
- Monitoring trigger (if available): `Watch for: Next quarterly earnings`

**Expand state:** Full risk description, all linked assumptions, all linked evidence items, open questions, monitoring triggers.

**What risk cards must not contain:**
- Urgency language ("Act now", "Immediate risk")
- Probability estimates ("60% chance of…")
- Scores or ratings ("Risk level: 7/10")
- Action recommendations ("Consider reducing your position")
- Traffic light colours as quality signals

---

#### Position 5: Open Question Card(s)

**Why it exists:** Open questions are what Atlas cannot answer from the provided input. Naming them is more useful than silently ignoring them. The user may not have noticed these gaps.

**Why it appears fifth:** Open questions are what remains after evidence, assumptions, and risks have been surfaced. They represent the edge of what Atlas knows.

**When it is omitted:** If all assumptions are well-supported and no evidence gaps exist, open question cards may be omitted. In practice, they are almost always present.

**Content (one card per open question):**
- Question label: `Open Question`
- The question, written in plain language:
  > What percentage of Apple's revenue comes from its top three customers?
- Why it matters (one sentence):
  > This is relevant to the customer concentration assumption.
- Linked assumption or risk: `Linked to: Business assumption`

**Expand state:** No additional content. Open questions are simple — they do not expand into sub-cards.

---

#### Position 6: Uncertainty Card(s)

**Why it exists:** Uncertainty cards name what Atlas cannot determine — not because the evidence is missing, but because the question itself is inherently unresolvable from the available information.

**Why it appears sixth:** Uncertainty is the lowest-confidence output. It belongs at the end of the card stack, after everything Atlas is more certain about.

**When it is omitted:** If no significant uncertainties exist beyond the open questions already listed, uncertainty cards are omitted.

**Content (one card per uncertainty):**
- Uncertainty label: `Uncertainty`
- Plain language description:
  > Atlas cannot determine whether the competitive landscape will change materially in the next 12 months. This is inherently uncertain and not resolvable from available evidence.

**Expand state:** No additional content.

---

### Disambiguation Card (replaces Entity Card when entity is ambiguous)

When Atlas cannot identify the entity with confidence, the workspace shows a single Disambiguation Card instead of an Entity Card.

**Content:**

> **Disambiguation needed**
>
> Atlas found `Apple` in your input. Did you mean:
>
> [Apple Inc. (AAPL)] [Something else]

Clicking `Apple Inc. (AAPL)` resolves the entity and reloads the card zone with the correct entity.
Clicking `Something else` opens a simple text input:

> What did you mean by "Apple"? (e.g. a ticker, a company name, a country)

Atlas reprocesses based on the user's clarification.

**What the Disambiguation Card must not do:**
- Show multiple possible entities as a list the user must scroll
- Require the user to know a ticker symbol
- Show an error indicator

---

## Secondary Content

**Card count indicator:** `6 items` or `4 items, 2 open questions` — in the header, below the summary line. Updates as cards are added or dismissed.

**Card expand/collapse controls:** Each card has a small expand affordance (chevron or "See more" text). Collapsed by default on first view. The first Assumption card may be pre-expanded if Atlas has high confidence in it — this is the card most likely to produce the "aha" moment.

---

## Available Actions

| Action | Result |
|---|---|
| Click to expand a card | Card expands to show linked items and full content |
| Click to collapse a card | Card returns to summary view |
| Click "See more" on any card | Equivalent to expand |
| Scroll the card zone | Cards scroll; header and footer remain fixed |
| Click "Preview Weekly Review" (if available) | Opens Screen 4 inline |
| Click "Confirm" on Snapshot Draft (if present) | Draft becomes confirmed evidence; card updates in place |
| Click "Save workspace" in footer | Opens Save confirmation; workspace saves to local storage |
| Click "Continue without saving" in footer | Footer minimises; workspace remains usable |

---

## Empty States

**No cards found (input was too ambiguous to process):**

The card zone shows a single card:

> **Atlas couldn't find anything to work with.**
>
> Try a company name (e.g. Apple), a ticker (e.g. AAPL), or describe what you're thinking about.
>
> [Start over]

**Entity found, no evidence:**

Entity card appears. Below it, a single information card:

> **No evidence available yet.**
>
> Atlas found Apple Inc. but doesn't have evidence to work with. Add a research note, a price you remember, or anything you know about this company.

**Entity found, evidence found, no assumptions surfaced:**

Entity and evidence cards appear. No assumption, risk, or open question cards. The workspace is genuinely sparse. No placeholder cards. The footer still offers the Save prompt.

---

## Error States

**A card fails to load:**

The card position shows a minimal error state:

> One item couldn't be loaded. [Try again]

The rest of the workspace is unaffected.

**The entire workspace fails to load:**

The processing state returns briefly, then:

> Something went wrong. Your input has not been lost.
>
> [Try again] [Start over]

"Start over" returns to the Landing Screen with the paste box empty.

---

## Success State

**Workspace loads with at least one Assumption or Risk card:**

The summary line reads:

> Atlas found [N] things in your input.

No celebration. No animation. The cards are the success state — they speak for themselves.

**User expands a card for the first time:**

The card expands smoothly. No animation effect beyond the expansion itself.

**User reads an Assumption card and recognises it:**

This is the first "aha" moment. No Atlas action is required. The content produces the reaction.

---

## Emotional Objective

**The user should feel:** *This is organised. Atlas has taken what I gave it and made it structured. I can see the assumptions I was making without realising it. The risks I hadn't named are visible. This is useful.*

**Earn the next interaction:** The Temporary Workspace earns the user's willingness to explore — to click Weekly Review Preview, confirm a Snapshot Draft, or save the workspace.

---

---

# Screen 4 — Weekly Review Preview

---

## Purpose

The Weekly Review Preview shows the user what a structured weekly review looks like for their input. It appears inline — not in a new tab or modal. It shows only what Atlas can populate from the current workspace.

**User question:** *What does a full Atlas review look like? Can I use this for my regular investment review?*

---

## User Goal

Understand how the Temporary Workspace translates into a recurring, structured review. See that Atlas doesn't invent content — it shows only what it knows.

---

## Atlas Goal

Demonstrate the Weekly Review as a product capability without requiring the user to understand the full pipeline. Show that "more input → more review" is the natural path forward.

---

## When It Appears

The Weekly Review Preview link appears in the Temporary Workspace when:
- The workspace contains at least two Entity cards, **or**
- The workspace contains at least three evidence items, **or**
- The user has been in the workspace for more than 45 seconds

It does not appear for single-ticker inputs on first load — unless the user has also confirmed a Snapshot Draft or the input contained a research note.

The link appears as a quiet affordance in the workspace — not a button, not a banner. One line:

> Preview what your Weekly Review would look like → 

---

## Primary Content

The Weekly Review Preview expands inline below the card zone. It does not replace the workspace.

**Header:**

> Weekly Review — Preview (based on current workspace)

**Sections shown (only if Atlas can populate them):**

```
Entities reviewed
  Apple Inc. (AAPL)

Evidence available
  [list of evidence items from the workspace]

Open questions
  [open question cards from the workspace]

Assumptions under review
  [assumption cards from the workspace]

Risks identified
  [risk cards from the workspace]

Reasons to wait
  [if any monitoring triggers exist]
```

**Sections not shown (listed at the bottom as a quiet note):**

> Sections not yet available from current input:
> Research notes · Value scenarios · Decision journal context

This note is plain text, not a button or a prompt to add more input.

---

## Secondary Content

A one-line note below the preview:

> This preview is based only on what you've shared. Add more and it grows.

This is a statement, not a call to action.

---

## Available Actions

| Action | Result |
|---|---|
| Scroll within the preview | Preview scrolls independently |
| Click "Close preview" | Preview collapses; workspace returns to full view |
| Click "Add research note" (quiet link) | Returns focus to the paste box with a suggestion pre-filled |

---

## Empty States

**Weekly Review Preview opens but no sections can be populated:**

> Atlas doesn't have enough from your current input to show a Weekly Review preview.
>
> Try adding a research note or a second company.

This is rare. If the user has reached the workspace, at least an entity was identified.

---

## Error States

None. The Weekly Review Preview is generated from the current workspace — if the workspace loaded, the preview can always load.

---

## Success State

The user reads the Weekly Review Preview and understands what a full Atlas review contains.

No specific success indicator. The preview exists and contains content.

---

## Emotional Objective

**The user should feel:** *I understand what Atlas is building toward. This is what my weekly investment review could look like. It only shows what it actually knows.*

**Expected user reaction:** *This would be genuinely useful if I added more. I can see why the workspace matters.*

**Earn the next interaction:** The Weekly Review Preview earns the user's interest in saving the workspace and returning with more input.

---

---

# Screen 5 — Snapshot Draft Preview

---

## Purpose

When the user's input contains a price, an order, a news reference, or a clear personal observation, Atlas creates a Snapshot Draft and shows it as a card within the workspace. This screen describes how that card behaves and what it presents.

**User question:** *Did Atlas understand what I said? Is this what I meant?*

---

## User Goal

Confirm (or correct) what Atlas understood before it is treated as evidence.

---

## Atlas Goal

Never treat anything as fact without the user's explicit confirmation. The Snapshot Draft is Atlas asking, not assuming.

---

## When It Appears

The Snapshot Draft card appears within the Temporary Workspace card zone, between Evidence cards and Assumption cards, when the user's input contains:

- A price observation ("Apple is at $180")
- An order ("I bought 50 shares of AAPL at $180")
- A news reference ("Apple just reported earnings")
- A forward-looking intention ("I'm thinking about adding MSFT")
- A personal observation ("I've noticed the store traffic seems lower")

It does not appear for purely analytical input ("What is Apple's competitive position?").

---

## Primary Content

### Snapshot Draft Card (unconfirmed state)

**Card label:** `Snapshot Draft · Unconfirmed`

**Content:**

```
Type:        Order
Subject:     AAPL
Confidence:  High
Understood as: Purchase of 50 shares at $180.00

Is this correct?
[Confirm]  [Edit]  [Discard]
```

The three actions are equally prominent. None is pre-selected. There is no default action.

**What the card must not contain:**
- Commentary on whether the price was good or bad
- Comparison to other prices or historical data
- A recommendation about whether to record this
- An urgency indicator

---

## Snapshot Draft Card States

### Unconfirmed (default)

The card shows the draft content with the three actions. The card is visually distinct from confirmed evidence cards — a lighter border, or a "draft" visual treatment.

### Being edited

Clicking `[Edit]` replaces the card content with an inline editor. Fields:

- Type (dropdown: Order / Price Observation / News Reference / Personal Observation / Other)
- Subject (text field, pre-filled from Atlas's understanding)
- Description (text area, pre-filled with Atlas's interpretation)
- Date (date field, pre-filled with today's date)

Two actions appear below the editor:

> [Save edits and confirm]  [Cancel edit]

"Cancel edit" returns to the unconfirmed card without saving changes.

### Confirmed

Clicking `[Confirm]` updates the card in place:

> ✓ Confirmed — added as evidence.

The card moves from its position between Evidence and Assumption cards into the Evidence section. The card label changes from `Snapshot Draft · Unconfirmed` to `Your Observation · Confirmed`.

The Assumption cards and Risk cards may update quietly to reflect the new evidence — no animation, but the evidence link counts on those cards increment.

### Discarded

Clicking `[Discard]` removes the card from the workspace with a gentle fade. No confirmation dialog. No "Are you sure?" The discard is immediate but the card can be un-discarded within 5 seconds via a single undo link:

> Snapshot draft removed. [Undo]

After 5 seconds, the undo link disappears and the discard is permanent for this session.

---

## Secondary Content

A one-line note below the Snapshot Draft card (unconfirmed state only):

> Atlas won't use this until you confirm it.

This line disappears after confirmation or discard.

---

## Available Actions

| Action | Result |
|---|---|
| Click Confirm | Draft becomes confirmed evidence; card updates in place |
| Click Edit | Inline editor opens |
| Click Discard | Card fades out; undo link appears for 5 seconds |
| Click Undo (within 5 seconds of discard) | Card reappears in unconfirmed state |
| Click Save edits and confirm | Saves edited content; card becomes confirmed |
| Click Cancel edit | Returns to unconfirmed card |

---

## Empty States

Not applicable. The Snapshot Draft card only appears when Atlas has identified draft content.

---

## Error States

**Atlas misunderstood the input completely:**

The card shows low confidence:

```
Type:        Unknown
Subject:     Unknown
Confidence:  Low
Understood as: Atlas wasn't sure what this referred to.

[Edit to clarify]  [Discard]
```

There is no `[Confirm]` action when confidence is Low — the user must edit or discard.

---

## Success State

**Draft confirmed:**

> ✓ Confirmed — added as evidence.

The card is now part of the Evidence section. The workspace is now more complete than when the user arrived.

---

## Emotional Objective

**The user should feel:** *Atlas understood what I said. It's showing me what it understood before treating it as fact. I am in control of what it uses.*

**Expected user reaction:** *This is careful. It's not just assuming. I like that it asked.*

**Earn the next interaction:** The Snapshot Draft Preview earns trust. A user who has confirmed a Snapshot Draft is more likely to save the workspace and return.

---

---

# Screen 6 — Save Workspace Prompt

---

## Purpose

The Save Workspace Prompt is the first moment Atlas asks the user to commit to preserving their work. It appears after the user has received value — not before.

**User question:** *Should I save this? Is this worth keeping?*

---

## User Goal

Decide whether to save the workspace and return to it. Not be pressured into saving.

---

## Atlas Goal

Offer to preserve value at the right moment — after the user has experienced enough to know it is worth keeping. Never pressure. Never gate.

---

## When It Appears

The Save Workspace Prompt appears in the sticky footer when any of the following are true:

- The user has expanded at least one card, **and** more than 60 seconds have passed since the workspace appeared
- The user has confirmed a Snapshot Draft
- The user has clicked "Preview Weekly Review"

It does not appear:
- Before the workspace has been visible for 60 seconds
- Before the user has interacted with the workspace (expanded a card, clicked something)
- As a modal or overlay — it is part of the sticky footer, always visible but never blocking

The trigger conditions ensure that the Save Prompt appears after the user has received something worth saving.

---

## Primary Content

### Footer (before Save Prompt conditions are met)

The footer is minimal:

> `Temporary · Not saved`  ·  [Save workspace]

The "Save workspace" button is present but quiet — secondary colour, not the primary call to action. The user's focus is on the cards, not the footer.

### Footer (after Save Prompt conditions are met)

The footer expands slightly to show the save prompt:

> **Your workspace is temporary.**
> Save it to keep your work and return to it later. Nothing leaves your browser until you save.

Two actions:

> [Save workspace]  [Continue without saving]

Both actions are equally prominent. "Continue without saving" is not greyed out, not labelled "Skip" or "Maybe later", and not smaller than "Save workspace".

---

## What Saving Does (Alpha 0.1)

Saving writes the workspace to browser local storage. No server. No account.

**Immediately after saving, the footer updates to:**

> Saved to this browser.  ·  [Access from another device →]

"Access from another device" is a quiet link. Clicking it opens the account creation offer (see below). It is not a prompt — it is an option.

---

## Account Creation Offer (within this screen)

Account creation is offered after the user saves, not before. It is a one-line link, not a modal:

> **Access from another device →**

Clicking this link expands the footer to show:

> **Save your workspace to your account.**
> Access it from any device, any browser.
>
> [Create free account]  [Keep using without an account]

"Keep using without an account" is available and equally prominent.

**Why this is the first time an account is suggested:**

The user has now:
1. Submitted input and seen the Temporary Workspace
2. Interacted with at least one card
3. Chosen to save their work

They have received clear value. They have expressed a desire to keep that value (by saving). The natural next question is "can I access this elsewhere?" — and that is when an account becomes genuinely useful to the user, not just to Atlas.

Offering an account before this point would be premature. The user would not yet have a reason to want one.

---

## Secondary Content

**Below the "Saved to this browser" confirmation (one line, small text):**

> Your workspace is stored only in this browser. [Learn more]

"Learn more" links to a one-paragraph privacy note (not a full privacy policy). The paragraph explains: what is stored, where, and who can access it (only the user, only in this browser, until they clear browser storage or sync to an account).

---

## Available Actions

| Action | Result |
|---|---|
| Click "Save workspace" (pre-conditions not met) | Workspace saves immediately; footer updates to "Saved to this browser" |
| Click "Save workspace" (full prompt) | Workspace saves; footer updates; account offer appears as quiet link |
| Click "Continue without saving" | Footer minimises back to minimal state; workspace remains usable |
| Click "Access from another device" | Footer expands to show account creation offer |
| Click "Create free account" | Account creation flow begins (outside scope of this document) |
| Click "Keep using without an account" | Footer collapses; workspace remains in "Saved to this browser" state |

---

## Empty States

Not applicable. The Save Workspace Prompt is always attached to a workspace that contains content.

---

## Error States

**Save to local storage fails (e.g. storage quota exceeded):**

The footer shows:

> Atlas couldn't save your workspace to this browser. Your browser's storage may be full.
> You can still use your workspace — it just won't be saved when you leave.

No account creation is suggested as a workaround for a storage error. The user is told what happened and what the consequence is. Nothing more.

---

## Success State

**Workspace saved:**

> Saved to this browser.

The status badge in the header updates from `Temporary · Not saved` to `Saved · This browser`. The workspace is now persistent in local storage.

No modal. No full-page confirmation. No sound. The badge update is the success state.

---

## Emotional Objective

**The user should feel:** *I'm being asked to save because I've done something worth keeping — not because Atlas is trying to lock me in. I can say no. I chose to save because I wanted to.*

**Why "Continue without saving" matters:** If the user can only save, the save is a gate. If the user can save or not, the save is a choice. The distinction is the difference between pressure and trust.

**Earn the next interaction:** The Save Workspace Prompt earns the user's return. A saved workspace is a reason to come back.

---

---

# Full Emotional Journey Map

| Screen | Primary question the user holds | Emotional objective | What earns the next interaction |
|---|---|---|---|
| Landing Screen | Is this worth my time? | Calm curiosity; no pressure | The simplicity earns the first submission |
| Processing State | Is this working? | Patience; trust that something careful is happening | The thoroughness earns the expectation of value |
| Temporary Workspace | What did Atlas find? Is this useful? | Organisation; surprise at named assumptions and risks | The "aha" moment earns exploration |
| Weekly Review Preview | What does a full review look like? | Credibility; Atlas only shows what it knows | The coherence earns interest in returning |
| Snapshot Draft Preview | Did Atlas understand what I said? | Agency; Atlas asked before assuming | The confirmation earns deeper trust |
| Save Workspace Prompt | Should I save this? | Readiness; no pressure; genuine choice | The non-pressured ask earns the return visit |

---

# Anti-Goals — Applied to Every Screen

| Anti-goal | How it manifests in this flow |
|---|---|
| No dashboards | No screen shows an overview or summary before the user has provided input |
| No information overload | Cards are collapsed by default; the user expands what they want |
| No gamification | No streaks, badges, scores, ratings, or completion indicators |
| No urgency | No countdowns, "act now" copy, or time-limited offers |
| No prediction language | No "Apple will…", no price targets, no forecasts |
| No recommendations | No card ever suggests what the user should do |
| No unnecessary charts | No charts appear unless derived from user-provided data |
| No account walls | The workspace is fully usable without saving; saving is fully usable without an account |

---

# Sprint 288 Target

**Prototype the First Visual Wireframes**

Using this UX flow as the canonical source, Sprint 288 should produce wireframe-level visual specifications for each of the six screens. Each wireframe should define: layout zones with dimensions, typographic hierarchy, spacing system, colour roles (not values), interactive states, and responsive behaviour notes. The wireframes are not visual designs — they are spatial and structural specifications from which a visual designer can begin.
