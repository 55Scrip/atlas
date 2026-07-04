# No-Account First-Value Onboarding

**Created:** 2026-07-04 (Sprint 266)  
**Status:** DEFINED — product principle established. No implementation in this sprint.

---

## Purpose

This document defines Atlas's no-account first-value onboarding principle.
It specifies what first-time users should be able to do before creating an
account, when account creation should be introduced, and how this principle
aligns with Atlas's local-first, deterministic, provider-free identity.

This is a product specification. No UI, authentication, backend service,
database schema, analytics, or cloud persistence is implemented here.

---

## Product Principle

**Atlas should be useful before it asks for trust.**

A user should be able to try Atlas, provide a portfolio snapshot or investment
notes, run a structured review, and see meaningful output — without creating
an account, providing an email address, or connecting a broker.

Account creation should be introduced only after the user has seen meaningful
value, or when the user explicitly wants persistence, saved workspaces,
history, collaboration, or cross-device access.

This principle is not a UX preference. It is a trust contract between Atlas
and the people who try it.

---

## Non-Goals

This sprint does not:

- implement accounts, authentication, signup, or login
- implement user sessions, local storage, cloud storage, or persistence
- implement database schema or backend services
- implement web UI, guest sessions, or account prompts
- implement payment flows, analytics, or telemetry
- implement broker integrations or live data connections
- change CLI behaviour
- change runtime behaviour
- add new commands or API endpoints

---

## First-Value Definition

First value is the point at which a user receives structured, useful output
from Atlas without having created an account.

For Atlas, first value is:

> A first-time user provides a portfolio snapshot, watchlist, research notes,
> or investment-process question and receives a structured Atlas review that
> surfaces evidence gaps, follow-up questions, missing inputs, and reasons to
> wait — without logging in.

The review may include:

- portfolio context (holdings by weight, sector exposure, concentration notes)
- watchlist review (status, evidence gaps, open questions per item)
- company reviews needing attention
- portfolio fit and suitability notes (structural, not personalised)
- risk and principle guardrail context
- open decisions summary
- missing evidence (per ticker, per directory)
- follow-up questions
- non-actions / reasons to wait

It does not include investment recommendations, price targets, broker signals,
or personalised advice. Atlas's safe-language guardrails apply in all output
regardless of account status.

---

## Guest / No-Account Mode

Guest mode is a future Atlas operating mode in which:

- no account, email, or credential is required
- the user provides input (portfolio text, watchlist, notes, snapshot)
- Atlas generates a temporary structured review
- output is shown in-session only — no persistence by default
- the user may export or copy the result
- Atlas does not silently retain sensitive investment data in guest mode
- Atlas does not require broker connection, live data, or external APIs
- any data provided in guest mode is handled locally or discarded at
  session end unless the user explicitly saves it

Guest mode does not imply any current web UI implementation. It is the
intended future state for first-time user onboarding.

---

## Example First Session

The following describes the intended future first-time user flow. This is
future product direction, not current implementation.

```
1. User opens Atlas (web or desktop).
2. Atlas shows an input-first surface — not a dashboard or account wall.
3. User pastes portfolio holdings, a watchlist, research notes, or an
   investment-process question.
4. Atlas generates a local, temporary structured review.
5. Atlas displays 10-section output with evidence gaps, follow-up questions,
   and reasons to wait — all derived from the user's input.
6. After the review is shown, Atlas offers — without pressure:

   "Save this workspace?"
   "Create an account to keep your history and continue later."

7. The user may accept, decline, or export the result without creating an
   account.
```

The account prompt appears after value is delivered. Not before.

---

## What Users Can Do Before Account Creation

The following capabilities are intended to be available without an account
in future Atlas web and desktop implementations:

- paste portfolio text (positions, holdings, market values)
- paste watchlist text (companies, statuses, evidence gaps, open questions)
- paste research notes
- paste a draft order idea or investment hypothesis
- upload or provide a snapshot file when future UI supports it
- run a temporary structured review
- inspect evidence gaps and follow-up questions
- inspect reasons to wait and non-actions
- export or copy the result if output export is supported
- adjust inputs and re-run

These are input-and-review capabilities. They do not require identity.

---

## What Requires an Account

The following capabilities are intended to be account-gated:

- saving workspaces (named, persistent review bundles)
- saving portfolio history across sessions
- cross-device access (continue on another device)
- collaboration (shared workspaces, team accounts)
- long-term decision journal history
- persistent watchlist state between sessions
- cloud backup of review bundles
- team or shared account features
- billing, if applicable to future paid tiers

Account creation unlocks continuity and collaboration. It does not unlock
the first review.

---

## Account Prompt Timing

Atlas should follow this account-prompt sequence:

| Event | Account prompt? |
|-------|----------------|
| User opens Atlas for the first time | No |
| User enters input (portfolio, notes) | No |
| Atlas generates first review | No |
| User reads output | No |
| User clicks Save or wants history | **Yes — prompt here** |
| User wants to continue later | **Yes — prompt here** |
| User wants cross-device or collaboration | **Yes — prompt here** |

**Never prompt for account creation before first meaningful output.**

Dark patterns to avoid:

- account wall before any output
- email capture before review generation
- forced signup to see results
- modal interruptions during first review
- countdown timers or artificial urgency
- "unlock full results" with partial output as bait

---

## Data Handling and Privacy Boundary

In guest / no-account mode:

- minimise data collection before account creation
- make temporary-session data behaviour explicit to the user
- do not require personal identity (email, name, phone) to try Atlas
- do not silently retain portfolio data, watchlist data, or research notes
  beyond the session unless the user explicitly saves
- do not imply broker connection is required or active
- do not transmit investment data to third parties without explicit consent
- if future cloud processing is introduced, require explicit opt-in before
  any user data leaves the local device
- apply safe-language guardrails to all output regardless of account status

These principles apply to both web and desktop implementations.

---

## Local-First Alignment

No-account first value aligns naturally with Atlas's existing identity:

- Atlas is deterministic — the same input always produces the same output.
  No account is needed to reproduce a result.
- Atlas is local-first — the CLI operates entirely on user-provided local
  files. No external data, no broker connection, no provider dependency.
- Atlas does not use AI or LLMs — output is derived from structure and rules,
  not from black-box inference that requires account-bound API keys.
- Atlas produces informational reviews, not personalised financial advice —
  no personalisation layer requires account identity to function.

The no-account principle extends Atlas's existing values into future
onboarding: the user retains control; Atlas earns trust by producing value.

---

## Future UI Implications

The first screen in any Atlas web or desktop implementation should be
**input-first**, not dashboard-first.

**Preferred first screen direction:**

```
[ Paste your portfolio ]
[ Paste your watchlist ]
[ Paste research notes ]
[ Ask a process question ]

[ Run Review ]     [ Load example ]
```

**Not preferred:**

```
[ Sign up ]  [ Log in ]
[ Dashboard (empty until signed in) ]
```

Account creation UI should exist, but it should not be the entry point.
The entry point is input and review.

Implications for future UI sprints:

- The home route should be an input surface, not an auth screen.
- Example inputs should be available without login (to reduce cold-start friction).
- The "Save" or "Continue later" action is where account creation is introduced.
- The account creation flow should clearly state what the account adds
  (persistence, history, cross-device) — not what the user is missing.

---

## Trust-Building Copy Principles

Atlas copy should be:

- **Clear** — say exactly what is temporary, what is saved, and what an
  account adds.
- **Non-salesy** — no growth-hacking copy, no artificial FOMO, no upsell
  pressure.
- **Non-urgent** — no countdown timers, no "your session expires soon" pressure.
- **Honest about limits** — if output is informational only, say so.
- **Respectful of sensitive data** — investment data is private; do not
  make the user feel surveilled.

**Safe example copy:**

> Try Atlas without an account.  
> Paste a portfolio snapshot or notes and get a structured review.  
> Create an account only if you want to save your workspace.

**Safe account-prompt copy (shown after first review):**

> Your review is ready.  
> To save this workspace and continue later, create a free account.  
> Your review will not be stored unless you save it.

**Copy to avoid:**

> Unlock your full portfolio review — sign up now.  
> ⚠ Your session expires in 5 minutes.  
> Join thousands of investors already using Atlas.  
> Get personalised recommendations — create an account.

---

## Risks and Mitigations

| Risk | Mitigation |
|------|-----------|
| Users expect saved history without account | Explicit temporary-session messaging before and after review |
| Users paste sensitive data without understanding retention | Clear data-handling notice in guest mode before input |
| Abuse or spam if public web entry is open | Rate limits if/when public web entry is implemented; no auth required for rate-limit check |
| User confusion between temporary and saved work | Persistent "not saved" indicator during guest session |
| Legal/safety risk if output feels like advice | Safe-language guardrails enforced in all output; disclaimer always present |
| Users abandon before seeing value if onboarding is complex | No-account entry point removes the primary friction point |
| Users provide real portfolio data and then close without saving | Prompt to save or acknowledge discard at session end |

---

## Implementation Phases

These phases describe future product development. No phase beyond Phase 0
is implemented in this sprint.

| Phase | Description | Status |
|-------|-------------|--------|
| 0 | No-account first-value principle documented | **Complete — Sprint 266** |
| 1 | CLI/local prototype remains fully account-free | **Complete — existing CLI** |
| 2 | Web prototype supports temporary guest review without account | Future |
| 3 | Optional account prompt shown after first review is generated | Future |
| 4 | Saved workspace and history unlocked behind account | Future |
| 5 | Collaboration, cross-device, and team features behind account | Future |

Phase 1 is already complete: the Atlas CLI operates entirely without accounts,
authentication, or network services. The CLI is the reference implementation
of no-account first value.

---

## Open Questions

1. **Session duration in guest mode:** How long should a temporary review
   session persist before expiry? (Suggested: in-session only, with opt-in
   to extend via account.)

2. **Data residency in guest mode:** If future web hosting is introduced,
   where is temporary session data stored, and is it processed server-side
   or client-side? (Preferred: client-side / local processing where possible.)

3. **Example input quality:** What pre-loaded example portfolio should ship
   with the web guest mode to reduce cold-start friction for users with no
   immediate input ready?

4. **Output export in guest mode:** Should guest users be able to export
   a Markdown or PDF copy of their review without creating an account?
   (Preferred: yes — export without account; save to workspace requires account.)

5. **Account type differentiation:** Is there a free persistent tier, or does
   all persistence require a paid account? (Out of scope for this sprint;
   deferred to billing architecture sprint.)

---

## Related Documents

- [docs/AtlasV1OperatingMode.md](AtlasV1OperatingMode.md) — v1 product boundary definition
- [docs/AtlasWeeklyReviewUsageGuide.md](AtlasWeeklyReviewUsageGuide.md) — Weekly Review user-facing guide
- [docs/AtlasLocalizationBoundary.md](AtlasLocalizationBoundary.md) — localization boundary
- [docs/SwedishSafeLanguageGuardrails.md](SwedishSafeLanguageGuardrails.md) — safe-language guardrails
- [docs/Architecture.md](Architecture.md) — system architecture overview

---

## Recommended Next Sprint

**Sprint 267 — Define Input-First Workspace Onboarding**

After establishing the no-account first-value principle, the next product
specification step is to define the input-first first screen: how pasted
portfolio text, watchlist text, research notes, or investment questions
become a temporary Atlas workspace, what the workspace surface looks like,
and how it transitions to a saved account workspace.

This is the UX specification that gives Sprint 266's principle a concrete
first-screen form.
