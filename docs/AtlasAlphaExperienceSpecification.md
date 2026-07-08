# Atlas Alpha 0.1 — First Five-Minute Experience Specification

**Created:** 2026-07-08 (Sprint 286)
**Status:** CANONICAL — product experience specification. No runtime implementation.
**Chapter:** 2 — Building the Product
**Answers:** What should a first-time user experience from second 0 until they have received meaningful value — without creating an account?

---

## Purpose

This document is the canonical specification for the Atlas Alpha 0.1 first-time user experience.

It is written for designers and frontend engineers. After reading it, the question "how should the experience work?" should have a clear answer for every step from arrival to first meaningful value.

It does not define implementation. It defines what the user should experience, what they should feel at each step, and why.

---

## Product Principles (Binding)

Every screen, state, and interaction in Atlas Alpha must be consistent with these principles. They are not aspirational. They are constraints.

| Principle | What it means in practice |
|---|---|
| Evidence before conclusions | Atlas never shows a conclusion before the user has provided the evidence it is based on |
| No action is a valid outcome | Atlas never implies the user must do something as a result of what it shows |
| Reduce noise. Increase clarity. | Every screen removes something unnecessary; nothing is added without a reason |
| Trust before accounts | The user receives full value before they are asked to create an account |
| AI supports judgment | Any AI-derived content is labelled and does not override user-authored content |
| User owns the decision | Atlas informs. The user decides. Atlas never decides on their behalf. |
| Structured judgment over predictions | Atlas produces organised, traceable analysis — not forecasts, signals, or predictions |
| Input-first, not dashboard-first | The first action is always to provide input — not to view a dashboard or summary |

---

## Emotional Objectives

Atlas should make the user feel:

- **Calmer** — less noise, more structure, less anxiety about what they might be missing
- **More structured** — their thinking is organised, not just reflected back
- **More informed** — they understand their own evidence and assumptions better than before
- **More confident in their own reasoning** — Atlas supports their judgment, it does not replace it

---

## Anti-Goals

Atlas Alpha must never make the user feel:

- **Rushed** — no countdowns, urgency cues, or "limited time" framing
- **Pressured** — no "create account to continue" gates before value is delivered
- **Manipulated** — no dark patterns, no manufactured scarcity, no social proof pressure
- **Overwhelmed** — no information density that requires orientation before the user can act
- **Dependent on Atlas** — Atlas should increase the user's confidence in their own reasoning, not replace it

Atlas Alpha must never:

- Show a price, return estimate, or valuation figure without stating the evidence and assumptions behind it
- Imply that waiting or doing nothing is the wrong answer
- Use language that implies Atlas knows what the user should do
- Present AI-derived content as if it were user-authored content
- Request an account before the user has seen meaningful value

---

## The Five-Minute Journey

```
Second 0    Arrival
Second 10   Landing page understood
Second 30   First input started
Minute 1    First input submitted
Minute 2    Temporary Workspace appears
Minute 3    Workspace Cards explored
Minute 4    First "aha" moment
Minute 5    Save Workspace prompt — value received before commitment
```

---

## 1. Arrival

**Entry points:** Direct URL, referral link, word of mouth, search.

**What the user knows at arrival:** Nothing, or almost nothing. They may have heard "Atlas helps you think through investments." They have not been told what Atlas is, what it costs, or what they need to provide.

**What Atlas must establish in the first screen:**

1. What Atlas does — in one sentence, without financial jargon
2. What the user does first — one clear action
3. That no account is required — stated explicitly, not implied

**What Atlas must not do at arrival:**

- Show a feature list
- Show a pricing table
- Show testimonials or social proof
- Ask for an email address
- Show charts, graphs, or market data
- Use words like "portfolio", "returns", "alpha", or "outperform"

**Emotional goal at arrival:** The user should feel that this is a calm, thoughtful tool — not a trading platform, not a social network, not a news product. The visual tone, copy, and layout should signal: *this is a place to think, not a place to act.*

---

## 2. Landing Page

### Primary message

One sentence. Plain language. No financial jargon.

> Atlas helps you think more clearly about your investments.

Or equivalent. The sentence should not contain: buy, sell, outperform, returns, alpha, gain, profit, beat the market, track, monitor.

### Sub-message (optional, one sentence)

If a second sentence is used, it should describe the process, not the outcome:

> Paste in your portfolio, a company name, or a research note — Atlas structures what you already know.

### Primary call to action

One button. The label describes what the user does, not what Atlas does.

> Try Atlas — no account needed

Or:

> Start with your portfolio

Or:

> Paste in anything

The button label must not say "Sign up", "Get started", "Create account", "Join", or "Log in".

### Trust signal

One line, below the button, no icon required:

> No account required. Nothing is stored until you choose to save it.

This line is not optional. It must appear before the user takes the first action.

### What is not on the landing page

- Navigation bar with multiple items
- Feature sections ("Evidence Assembly", "Risk Review", etc.)
- Pricing
- Testimonials
- Blog links
- Social media links
- Charts or illustrations of investment performance
- Any number that could be interpreted as a return, price, or target

### Emotional goal at landing page

The user should feel: *I understand what this is and what I need to do. I am not being sold to.*

---

## 3. First Input

### Input surface

A single text area, large, centred, with a calm placeholder.

**Placeholder text:**

> Paste your portfolio, a company name, a research note, or anything you're thinking about.

The placeholder disappears when the user begins typing. It does not reappear while the user is typing.

### What the user can paste

The input surface accepts any of the following without the user needing to know which type:

- A list of tickers and positions (e.g. "AAPL 100 shares, MSFT 50 shares")
- A company name or ticker alone (e.g. "Apple" or "AAPL")
- A research note in plain text
- A price observation (e.g. "Apple is at $180, I bought at $150")
- A news headline or excerpt
- A question (e.g. "I'm thinking about adding more NVIDIA, is that reasonable?")
- A free-form thought (e.g. "I've been holding this for 3 years and I'm not sure if the thesis still holds")

The user does not need to format their input. Atlas classifies it.

### Input constraints

- Minimum: 1 character (Atlas will ask for more if needed)
- Maximum: visible limit indicator only when the user is near it (do not show "0 / 10000" by default)
- No required fields
- No format validation on input — Atlas handles ambiguity downstream

### Submit action

One button below the text area:

> Analyse

Or:

> See what Atlas finds

The button becomes active as soon as the user types anything. It does not require a minimum length.

### What happens if the user submits an empty input

The placeholder pulses once. No error message. No red border. No "required field" text. The input area gently draws focus.

### Emotional goal at first input

The user should feel: *I can just type what I'm thinking. I don't need to prepare anything. Atlas will figure out what I mean.*

---

## 4. Processing Experience

### Duration

Processing is instantaneous in Alpha 0.1 (no AI, no network). The processing screen exists to make the transition feel intentional — not to simulate latency.

### What appears during processing

A single, calm, progress statement. Not a spinner. Not a progress bar. A sentence that describes what Atlas is doing.

Sequence (each line replaces the previous, 400ms intervals):

```
Reading your input…
Finding what you've shared…
Structuring what we know…
```

The sequence completes. The Temporary Workspace appears.

### What does not appear during processing

- Percentage complete
- "Loading…" or "Please wait…"
- Animated charts or graphs
- Advertisements or promotions
- Account prompts

### If processing takes unexpectedly long (> 3 seconds)

A single line appears:

> Still working — this takes a moment.

No retry button unless the user waits more than 10 seconds.

### Emotional goal during processing

The user should feel: *Something careful is happening. This is not instant because it is thoughtless — it is taking a moment to be thorough.*

---

## 5. Temporary Workspace

### What it is

The Temporary Workspace is Atlas's primary output surface. It is a structured, readable document that organises everything Atlas has found and surfaced from the user's input.

It is temporary by default. Nothing in it is saved until the user explicitly chooses to save.

**Defined in:** [docs/TemporaryWorkspaceDataModel.md](TemporaryWorkspaceDataModel.md)

### How it appears

The Temporary Workspace slides in from below or fades in — a calm transition, not a pop or flash. It fills the main content area.

### What it contains (first appearance)

The Temporary Workspace on first appearance shows:

1. **A title** — derived from what the user submitted. If the user submitted a ticker: "AAPL — Temporary Workspace". If the user submitted free text: "Your Input — Temporary Workspace".
2. **A status badge** — "Temporary · Not saved"
3. **Cards** — one or more Workspace Cards representing what Atlas found (see Section 6)
4. **A footer** — "Nothing has been saved. Save this workspace to keep your work." with a Save button.

### What it does not contain on first appearance

- Account prompts
- Upgrade prompts
- Empty sections with "coming soon" labels
- Charts or visualisations that require data not provided by the user
- Any number that could be interpreted as a price target or return estimate

### Navigation within the Temporary Workspace

The user can scroll. Cards expand on click. Nothing requires navigation away from this page to be useful.

### Emotional goal at Temporary Workspace

The user should feel: *This is organised. Atlas has taken what I gave it and made it structured. I can see my own thinking reflected back more clearly.*

---

## 6. Workspace Cards

### What cards are

Each card represents one structured piece of information that Atlas has surfaced from the user's input, or has identified as relevant based on what the user provided.

**Defined in:** [docs/TemporaryWorkspaceCardRenderingContract.md](TemporaryWorkspaceCardRenderingContract.md)

### Card ordering

Cards are ordered as follows, from top to bottom:

1. **Entity cards** — What Atlas identified (ticker, company, portfolio holding). One card per entity.
2. **Evidence cards** — What evidence Atlas found in the user's input. One card per evidence item.
3. **Assumption cards** — Assumptions Atlas surfaced from the user's input. One card per assumption.
4. **Risk cards** — Risks Atlas identified from the assumptions and evidence. One card per risk.
5. **Open question cards** — Questions that the evidence or assumptions leave unanswered.
6. **Uncertainty cards** — Things Atlas cannot determine from the provided input.

### Card anatomy

Each card has:

- **A type label** — "Entity", "Evidence", "Assumption", "Risk", "Open Question", "Uncertainty"
- **A title** — plain language, no jargon
- **A body** — one to three sentences maximum. No bullet points inside cards in the first view.
- **An expand action** — "See more" or a chevron. Expanded state shows linked items.
- **No action buttons** — cards do not have "Act on this", "Buy", "Sell", or similar

### What cards do not show

- Scores
- Ratings
- Probability estimates
- Price targets
- Return estimates
- Urgency indicators
- Traffic light colours (red/amber/green) as quality signals — these imply action

### Cards for uncertain or ambiguous input

If Atlas cannot determine the entity from the user's input (e.g. the user typed "Apple" and there are multiple interpretations), it shows a single card:

> **Disambiguation needed**
> Atlas found "Apple" in your input. Did you mean Apple Inc. (AAPL) or something else?
> [AAPL — Apple Inc.] [Something else]

The user selects. Atlas reprocesses. No error state.

### Emotional goal at Workspace Cards

The user should feel: *Atlas has organised my thinking. I can see the assumptions I was making without realising it. The risks I hadn't named are visible. This is useful.*

This is the first "aha" moment.

---

## 7. Weekly Review Preview

### When it appears

The Weekly Review Preview appears when the user's input contains enough information for Atlas to produce a partial Weekly Review — typically when a portfolio or at least two holdings have been provided.

It does not appear for single-ticker inputs on first submission. It appears after the user has provided more input or expanded a card.

### What it contains

A partial Weekly Review: the sections Atlas can populate from the provided input. Empty sections are not shown. Sections Atlas cannot populate are listed as "Not enough information yet" — without prompting the user to provide more.

**Structure:**

```
Weekly Review — [Date] (Preview)

Entities reviewed: [list]

Evidence available:
  [evidence items from workspace]

Open questions:
  [open question cards from workspace]

Reasons to wait:
  [if any]

Sections not yet available:
  Research notes — not provided
  Value scenarios — requires more information
```

### What the Weekly Review Preview does not contain

- Price targets
- Return estimates
- "Buy" or "sell" language
- Urgency
- Action prompts

### How to access it

A link or button within the Temporary Workspace: "Preview Weekly Review". It opens inline, not in a new tab.

### Emotional goal at Weekly Review Preview

The user should feel: *This is what a structured review looks like. I can see that Atlas isn't guessing — it's only showing me what it actually knows from what I've told it.*

---

## 8. Snapshot Draft Preview

### When it appears

The Snapshot Draft Preview appears when the user's input contains a price, an order, a news reference, or a clear observation that maps to a snapshot type.

Example triggers:
- "I bought 50 shares of AAPL at $180"
- "Apple just reported earnings"
- "I'm thinking about adding MSFT"

### What it contains

A structured draft of the snapshot, following the Snapshot Draft schema. It shows the user what Atlas understood from their input and asks for confirmation before treating it as evidence.

**Structure:**

```
Snapshot Draft (Unconfirmed)

Type: Order
Subject: AAPL
Confidence: High
Understood as: Purchase of 50 shares at $180.00

Is this correct?
[Confirm] [Edit] [Discard]
```

### Confirmation requirement

Atlas never treats a Snapshot Draft as confirmed evidence until the user explicitly confirms it. The `[Confirm]` action moves the draft into the workspace as confirmed evidence. `[Discard]` removes it. `[Edit]` opens an inline editor.

### What the Snapshot Draft Preview does not contain

- Interpretation of whether the order was a good decision
- Price commentary
- Comparison to other prices
- Advice

### Emotional goal at Snapshot Draft Preview

The user should feel: *Atlas understood what I said. It's showing me what it understood before treating it as fact. I am in control of what it uses.*

---

## 9. Save Workspace Prompt

### When it appears

The Save Workspace prompt appears after the user has:

- Seen at least three Workspace Cards, **or**
- Spent at least 60 seconds in the Temporary Workspace, **or**
- Clicked to expand at least one card

It does not appear before these conditions are met. It does not appear as a gate — the user can continue using the Temporary Workspace without saving.

### What it says

> **Your workspace is temporary.**
> Save it to keep your work and return to it later. Nothing leaves your browser until you save.

Two options:

> [Save workspace] [Continue without saving]

"Continue without saving" is equally prominent. It is not greyed out. It is not labelled "Skip" or "Maybe later".

### What saving does (Alpha 0.1)

In Alpha 0.1, saving writes the workspace to local storage in the user's browser. No account is required. The user is told this explicitly:

> Saved to this browser. To access your workspace from another device, create a free account.

### What saving does not do

- Require an account
- Send data to a server
- Charge the user
- Create a profile

### Emotional goal at Save Workspace prompt

The user should feel: *I'm being asked to save because I've done something worth keeping — not because Atlas is trying to lock me in. I can say no.*

---

## 10. Optional Account Creation

### When it is offered

Account creation is offered only after:

1. The user has saved a workspace (local storage), **and**
2. The user returns to Atlas in a subsequent session, **or**
3. The user explicitly asks to access their workspace from another device

It is never offered before the user has received meaningful value.

### What it says

> **Access your workspace anywhere.**
> Create a free account to sync your workspace across devices and keep your work safe.

One action:

> [Create free account]

And a dismissal:

> [Keep using without an account]

"Keep using without an account" must be available. It must not be styled as a less important action.

### What account creation is not

- A requirement to use Atlas
- A gate to any feature in Alpha 0.1
- Triggered by any in-session event before the user has saved a workspace

### Emotional goal at account creation

The user should feel: *I'm creating an account because I want to, not because I have to. Atlas has already given me something valuable.*

---

## 11. Empty States

### Empty state: no entities found

Trigger: The user submits input but Atlas cannot identify any entity.

**What appears:**

> Atlas couldn't identify a company, ticker, or investment in what you shared.
>
> Try:
> - A company name (e.g. "Apple")
> - A ticker (e.g. "AAPL")
> - A description of what you're thinking about

No error indicator. No red. A calm, neutral tone. One or two suggestions.

### Empty state: no evidence found

Trigger: Entity identified but no evidence is available.

**What appears:**

> Atlas found [entity] but doesn't have any evidence to work with yet.
>
> Add a research note, a price you remember, or anything you know about this company.

### Empty state: no workspace saved

Trigger: User returns to Atlas and has no saved workspace.

**What appears:**

The landing page. No "You have no workspaces" message. No empty state dashboard. The user starts fresh as if it is their first visit.

### Empty state: partial input

Trigger: User submits very short input (e.g. a single word that is ambiguous).

**What appears:**

The disambiguation card (see Section 6). Not an error. Not a rejection.

### Emotional goal at empty states

The user should feel: *Atlas is being honest about what it doesn't know. It's not pretending to have information it doesn't have. I know what to do next.*

---

## 12. Error States

### Error state: input too long

Trigger: User pastes input that exceeds the maximum length.

**What appears:**

> Your input is very long. Atlas works best with focused input — try one company, one portfolio, or one research note at a time.
>
> [Trim to limit] [Split into two inputs]

No red border. No "error" label. A calm, solution-focused message.

### Error state: processing failure

Trigger: Processing fails for any reason (in Alpha 0.1, this should be extremely rare).

**What appears:**

> Something went wrong while reading your input. Your input has not been lost.
>
> [Try again] [Start over]

"Your input has not been lost" is essential. The user's typed text must remain visible.

### Error state: save failure

Trigger: Local storage save fails (e.g. storage quota exceeded).

**What appears:**

> Atlas couldn't save your workspace to this browser. Your browser's storage may be full.
>
> You can still use your workspace — it just won't be saved when you leave.

No data loss. No forced account creation.

### Error state: disambiguation failure

Trigger: User selects "Something else" in a disambiguation card and Atlas cannot resolve it.

**What appears:**

> Atlas couldn't identify what you meant. Try typing the ticker symbol directly (e.g. AAPL for Apple Inc.).

### Emotional goal at error states

The user should feel: *Atlas is telling me what happened clearly and without alarm. My work is safe. I know what to do next.*

---

## 13. Success States

### Success state: workspace created

Trigger: Temporary Workspace appears for the first time.

**What appears:**

The Temporary Workspace with a calm header:

> Atlas found [N] things in your input.

No celebration animation. No confetti. No "Great job!" copy. The result speaks for itself.

### Success state: workspace saved

Trigger: User saves workspace to local storage.

**What appears:**

A single line, replacing the "Temporary · Not saved" badge:

> Saved to this browser.

No modal. No full-page confirmation. No sound.

### Success state: snapshot draft confirmed

Trigger: User confirms a Snapshot Draft.

**What appears:**

The draft card updates in place:

> Confirmed. Added as evidence.

The card moves to the Evidence section of the workspace.

### Success state: account created

Trigger: User creates an account (if they choose to).

**What appears:**

A single line, replacing the "Saved to this browser" indicator:

> Saved to your account. Access your workspace from any device.

No welcome tour. No onboarding checklist. The user returns to their workspace.

### Emotional goal at success states

The user should feel: *Something real happened. Atlas is not celebrating — it is simply telling me what is now true. That is appropriate.*

---

## 14. Emotional Goals — Complete Map

| Step | Primary emotional goal | Secondary emotional goal |
|---|---|---|
| Arrival | Calm curiosity | Recognition ("this is different from trading apps") |
| Landing page | Clarity ("I understand what this is") | Low commitment ("I can try without risk") |
| First input | Permission ("I can just type what I'm thinking") | Ease ("no format required") |
| Processing | Patience ("something careful is happening") | Trust ("this is not instant because it is thoughtless") |
| Temporary Workspace | Organisation ("my thinking is structured") | Surprise ("I didn't know I was making those assumptions") |
| Workspace Cards | Insight ("I can see the risks I hadn't named") | Control ("I can expand any card") |
| Weekly Review Preview | Credibility ("Atlas only shows what it knows") | Completeness ("I can see what's missing") |
| Snapshot Draft Preview | Agency ("Atlas is asking, not assuming") | Precision ("it understood what I said") |
| Save Workspace prompt | Readiness ("I've done something worth keeping") | No pressure ("I can say no") |
| Account creation | Choice ("I want to, not have to") | Trust ("Atlas has already given me value") |
| Empty states | Honesty ("Atlas tells me what it doesn't know") | Direction ("I know what to do next") |
| Error states | Safety ("my work is not lost") | Calm ("this is not alarming") |
| Success states | Appropriate acknowledgement ("something real happened") | Continuity ("I return to my work") |

---

## Trust Boundaries

### What Atlas never does without explicit user action

- Store data outside the user's browser
- Send the user's input to a server
- Share data with third parties
- Create a user account
- Use the user's input to train a model
- Show the user's input to other users

### What Atlas always does

- Tells the user when data is temporary ("Temporary · Not saved")
- Tells the user when data has been saved ("Saved to this browser")
- Tells the user what it understood before treating it as evidence (Snapshot Draft confirmation)
- Preserves user-authored content exactly as written
- Labels any AI-derived content as AI-derived

### Privacy expectations

In Alpha 0.1:

- All user data lives in browser local storage
- No server-side persistence until the user explicitly creates an account and syncs
- No analytics on user input content
- No session recording of input content
- The user's investment information never leaves their browser until they choose to sync

---

## First "Aha" Moment Specification

The first "aha" moment occurs when the user reads an Assumption card or a Risk card and thinks: *I didn't know I was making that assumption* or *I hadn't named that risk.*

This moment should occur within the first 90 seconds after the Temporary Workspace appears.

### How to ensure it occurs

1. The Assumption cards and Risk cards appear in the top half of the workspace (not buried below the fold)
2. Assumption cards use plain, direct language: "You are assuming that Apple's revenue growth will continue above 15% annually."
3. Risk cards use calm, non-alarming language: "If that assumption fails, the investment thesis may need revision."
4. The cards do not tell the user what to do as a result

### What the "aha" moment is not

- A chart that shows a loss
- A warning about a stock price
- A notification that implies action is required
- A score that implies the investment is "risky"

---

## Future Extension Notes

The following capabilities are not in Alpha 0.1 and are not specified here. They are noted so that the specification can be extended cleanly.

| Future capability | Where it connects in this specification |
|---|---|
| AI reasoning | Assumption cards and Risk cards may be AI-derived; they will be labelled |
| Market data | Evidence cards may include market data; source and freshness will be shown |
| OCR | First input may accept image uploads; classification step handles the new input type |
| Research note import | First input may accept file uploads; treated as pasted text |
| Broker sync | First input may be replaced by a broker sync flow for portfolio input |
| Collaboration | Workspaces may be shared; trust boundaries extend to shared content |
| Mobile | Input surface and card layout adapt; emotional goals are unchanged |

**Principle:** Future capabilities extend the input surface and the evidence available. They do not change the processing experience, the Temporary Workspace structure, the card ordering, the trust boundaries, or the emotional goals.

---

## Sprint 287 Target

**Prototype the First Temporary Workspace UX Flow (Documentation Only)**

Using this specification as the canonical source, Sprint 287 should define the screen-by-screen UX flow for the Temporary Workspace journey: from first input submitted to Save Workspace prompt. Each screen should be specified as a wireframe-level document (not a visual design, not code) describing: layout zones, content in each zone, interactive elements, transitions, and emotional checkpoint.
