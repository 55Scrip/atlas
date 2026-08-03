# UX-014 — Watchlist Experience Specification

**Status:** Draft, v0.1. This is the first new operational UX specification authored after the completed Product Architecture Reconciliation, `APP-001` v0.4, `APS-006` through `APS-009`, the UX Correspondence Investigation, and the UX Governance Resolution Sprint (commit `4bd4856`). It states the complete governing UX contract for Watchlist: mental model, entry points, information hierarchy, screen architecture, interaction flow, states, progression, removal, navigation, accessibility, and responsive behavior. It does not redefine Watchlist's own Product semantics, which remain governed exclusively by `APS-007`; it does not specify visual tokens, pixel dimensions, implementation technology, API contracts, database structure, or AI ranking methodology.

---

## 1. Governance Metadata

Stated here in full, per `Architecture-Governance.md` §10's own requirement, adapted to the UX layer following the pattern every `APS` document already established and consistent with `UX-000`'s own governance discipline (§21).

- **Document identifier:** UX-014.
- **Title:** Watchlist Experience Specification.
- **Version:** v0.1.
- **Status:** Draft — the smallest truthful status available to a newly authored specification. This document has not undergone Internal Consistency Review, Targeted Consistency Correction, or Final Verification; it is not Release Candidate and not Final.
- **Parent authority:** `UX-000-Atlas-UX-Doctrine.md` (Release Candidate RC v1.0) — the highest governing document within the Atlas UX Architecture; this specification SHALL NOT contradict it, redefine a term it defines, or exceed the authority its own §7 (UX Responsibilities) and §8 (UX Prohibitions) grant.
- **Product authority:** `APP-000` — Atlas Product Doctrine (Draft v0.4); `APP-001` — Atlas Product Concept Taxonomy (Draft v0.4), §4 (Watchlist's reaffirmed deferral) and §9 item 8; `APS-007` — Watchlist (Draft v0.1), the primary Product-layer authority this specification translates into a UX contract; `APS-006` — Portfolio (Draft v0.1), for the Atlas Priority Model (§10) and Bounded Preview Governance (§13) this specification adopts by reference; `APS-001` — Decision Context (Draft v0.1), for the boundary this specification must never cross. `APS-008` (Daily Brief) and `APS-009` (Discover) are cited only for the deferred, future-facing relationships `APS-007` itself already names (WL-R-013, WL-R-014); their own complete UX behavior is explicitly out of scope, per the authorizing task's own constraint.
- **Dependencies:** `UX-004` — Investment Workspace Philosophy and `UX-005` — Investment Workspace Screen Specification, for the destination an Entry progresses into. `UX-007A` — Portfolio Workspace Wireframe Specification and `UX-007P` — Portfolio Workspace Final Polish, for the existing Watchlist-count reference in the Portfolio Workspace header this specification must remain compatible with. `UX-012A`, `UX-012B`, `UX-012C` — Atlas Design System, for reusable component, interaction, and accessibility patterns this specification builds on rather than reinvents. `ADR-002-Critical-UX-Architecture-Resolutions.md` (C-01 information hierarchy, C-06 unavailable-state accessibility), `ADR-003-Recommendation-Identity-and-Terminology-Resolution.md` (Atlas Recommendation / Proposed Decision Candidate Content boundary), adopted here unchanged.
- **Scope:** Watchlist's own UX mental model; entry points; per-Entry information hierarchy; screen architecture; interaction model (Follow, Open, Review, Investigate, Remove, Ignore for now, Return, Done); the UX progression path into Investment Case; removal and non-permanence behavior; the scoped presentation of the Atlas Priority Model; preview relationships with Portfolio and Daily Brief; states; navigation; accessibility; responsive behavior at the architectural level; explicit UX exclusions.
- **Non-scope:** Any Product semantics `APS-007` already governs (this specification translates, never restates as though it were the authority); visual token values; pixel dimensions; typography; color; animation timing; implementation technology; API contracts; database or persistence structure; AI recommendation or ranking logic; Daily Brief's or Discover's own complete UX behavior (each reserved for its own future specification); any amendment to `APP-000`, `APP-001`, any `APS`, `UX-000`, or any existing UX specification.
- **Affected documents:** None requiring amendment. This specification does not modify `UX-007A`, `UX-007P`, `UX-012A`, `UX-012B`, `UX-012C`, or any other existing UX document; a future, separately-authorized task may choose to add a Watchlist-preview card to `UX-007A`/`UX-007P` or a cross-reference from `UX-012A`'s surface list, but that is not performed or required here.
- **Superseded documents:** None. No dedicated Watchlist UX specification has ever existed in this repository; the Phase II "Entry Flows," "Portfolio Control Center," and "Discover" material `APS-007` itself cites as non-normative source material was never committed here and holds no authority this document could supersede.
- **Migration requirements:** None. No existing UX document or implementation is required to change as a consequence of this document's creation.

## 2. Purpose

Watchlist requires its own UX specification because `APS-007` states Watchlist's complete Product-layer behavior but explicitly excludes screens, workflows, navigation, visual design, and interaction design from its own scope (`APS-007` §3). This specification closes that gap: it translates `APS-007`'s normative requirements into a complete, implementable UX contract, so that a future visual design artifact, an implementation, engineering, QA, or any AI agent working on Atlas can build the Watchlist experience without inventing new UX rules — or new Product rules — of their own.

Watchlist's own central user question, unchanged from `APS-007` §2, governs every decision in this document: **"What should I continue following?"** — distinct from Portfolio's "where do I stand" (`APS-006` §2, realized in `UX-007A`/`UX-007P`) and Investment Workspace's "what should I conclude and decide" (`UX-004` §2).

## 3. Scope and Non-Scope

Restated from Section 1 for direct reference: in scope is everything a human perceives or does when using Watchlist — mental model, entry points, hierarchy, screens, interaction, states, navigation, accessibility, responsive behavior — tested against `UX-000` `UXD-R-008`'s own scope discipline: a statement belongs here only if it concerns perception or action, would remain true regardless of the specific screen, framework, or visual design used to express it, and would change if `APS-007`'s own normative behavior changed.

Out of scope, per `UX-000` §3 and `APS-007` §3: any Product semantics, visual tokens, pixel dimensions, implementation technology, API contracts, database structure, AI recommendation logic, or ranking methodology. Also out of scope: Daily Brief's and Discover's own complete UX behavior, each reserved for its own future specification; any change to `UX-007A`, `UX-007P`, `UX-012A`, `UX-012B`, or `UX-012C`.

## 4. Governing References

- **`ATLAS_CONSTITUTION.md`.** Normative, superior to every document in the Atlas Product and UX Architecture. "Calm before clever," "Portfolio before position," and the Non-Negotiable Principle that Atlas "never encourages unnecessary trading" ground this specification's own insistence that Watchlist remain bounded, calm, and never manufacture urgency (Section 5, Section 12).
- **`Architecture-Governance.md`.** Normative, governs this document's own governance-metadata discipline (§10) and document-status discipline.
- **`APP-000` — Atlas Product Doctrine, Draft v0.4.** Normative Product. PP-001 (Attention Before Information), PP-003 (AI Supports, Never Replaces, Investor Judgment), PP-004 (Progressive Disclosure), PP-005 (Human Ownership), PP-008 (Provenance) ground this specification throughout, cited by identifier at each point of use.
- **`APP-001` — Atlas Product Concept Taxonomy, Draft v0.4.** Normative Product. §3.13 (Investment Case) governs the destination of progression (Section 10); §4 governs Watchlist's own status as reaffirmed deferred territory, not an independent Product Concept.
- **`APS-007` — Watchlist, Draft v0.1.** Normative Product, the primary authority this specification translates. Every `WL-R-`, `WLINV-`, `WL-F-`, and `WL-AC-` identifier cited below refers to this document.
- **`APS-006` — Portfolio, Draft v0.1.** Normative Product, for the Atlas Priority Model (§10, `PF-R-031`–`035`) and Bounded Preview Governance (§13, `PF-R-051`–`055`) this specification adopts by reference rather than restating.
- **`APS-001` — Decision Context, Draft v0.1.** Normative Product, for the boundary (`DC-R-017`, `DC-R-021`) this specification's own progression discipline (Section 10) must not cross prematurely.
- **`UX-000-Atlas-UX-Doctrine.md`, Release Candidate RC v1.0.** Normative UX, the immediate parent authority for every UX-layer rule in this document.
- **`ADR-002-Critical-UX-Architecture-Resolutions.md`, Accepted.** Normative UX within its own stated scope; C-01 (information hierarchy) and C-06 (`aria-disabled`, never native `disabled`) are cited where Watchlist's own states require them (Section 14).
- **`ADR-003-Recommendation-Identity-and-Terminology-Resolution.md`, Accepted.** Normative UX within its own stated scope; governs how any Atlas-originated framing within a Watchlist Entry must be presented (Section 7, Section 16).
- **`UX-005-Investment-Workspace-Screen-Specification.md`.** Cited for its own Watchlist Case / Watchlist Entry disambiguation note (added per `UXD-R-096` and the UX Governance Resolution Sprint), which this specification adopts without restating: a "Watchlist Case" in `UX-005` is a Case Type on an already-open Investment Case; a Watchlist Entry, as this specification governs it, is a lighter-weight, pre-Investment-Case record that has not yet progressed. The two SHALL NOT be conflated anywhere in this document (Section 10).
- **`UX-007A-Portfolio-Workspace-Wireframe-Specification.md`, `UX-007P-Portfolio-Workspace-Final-Polish.md`.** Cited for the existing Portfolio Workspace header metadata ("5 watchlist") this specification's own Portfolio-preview entry point must remain compatible with (Section 6).
- **`UX-012A`, `UX-012B`, `UX-012C` — Atlas Design System.** Cited for reusable component, interaction-token, and accessibility patterns (Section 15, Section 17).

## 5. UX Definition

Watchlist is the Investor's intentional review queue — the bounded set of subjects the Investor has explicitly chosen to keep following, and nothing more. It is not a company profile, not a research terminal, not a feed, and not a second Portfolio.

The Watchlist experience must feel:

- **bounded** — a finite, comprehensible set the Investor can see the edges of, never an endlessly scrolling stream;
- **calm** — no manufactured urgency, no red for red's sake, consistent with `ATLAS_CONSTITUTION.md`'s own "calm before clever" and `UX-004` §10's own "reduce anxiety" discipline;
- **intentional** — every Entry visibly traces to a deliberate act, never to something Atlas added on the Investor's behalf;
- **easy to review** — the Investor can understand the state of the entire Watchlist without opening every Entry, per `UXP-001` (Meaning Before Volume);
- **easy to reduce** — removing an Entry is as legitimate, and as low-friction, as adding one;
- **clearly upstream of deeper investigation** — Watchlist is where following begins, not where reasoning happens.

It must not feel like:

- a feed (it never ingests or surfaces content on its own initiative, per `WL-R-051`);
- a second Portfolio (it holds no owned-position state, per `WL-R-047`);
- a task backlog (no Entry carries a due date or completion-tracking semantics, per `WL-R-054`);
- a notes database (no Entry carries citation, Source, or Provenance Category of its own, per `WL-R-050`);
- an infinite research queue (Section 12's priority-reflecting ordering, never unbounded accumulation, is the only scaling mechanism `APS-007` authorizes, per `WL-R-043`–`044`).

**Deliberate non-decision — no "Watchlist Conclusion."** `UX-000` `UXD-R-071` recognizes exactly five governed Conclusion variants (Initial and Investor-engaged Current Conclusion, Historical Conclusion, Review Conclusion, Primary/Portfolio Conclusion), each grounded in specific underlying Product-layer content (pre-Reasoning material, a Premise, a Learning Result, or an Investment Case/Portfolio state). A Watchlist Entry carries none of that: no Reasoning, no thesis, no Decision Context (`WL-R-004`, `WL-R-023`). This specification therefore deliberately does not introduce a "Watchlist Conclusion" — doing so would be a new Conclusion variant `UXD-R-071` does not authorize, and would risk implying Watchlist has formed a judgment it has not, contrary to `WLINV-003`. Section 8's "primary summary" is a plain factual status summary, never a Conclusion in the doctrine's governed sense.

## 6. Entry Points

Every entry point below is truthful to what currently exists or is explicitly anticipated by `APS-007`; none invents an automatic entry-creation path, per `WL-R-008` and `WL-R-022`.

- **Primary navigation.** Watchlist is reachable as its own primary destination, a peer of Portfolio, Discover, and Daily Brief, consistent with `UX-012A` §1's own list of Atlas surfaces (Section 15).
- **Discover → Follow.** The most common real-world origin, per `WL-R-014` and `WL-R-024`. Selecting Follow on a Discover candidate creates exactly one Watchlist Entry through an explicit Investor act; it does not open Watchlist itself, and does not require the Investor to leave Discover unless they choose to.
- **Daily Brief → Watchlist Update.** `APS-007` §8 (`WL-R-013`) names this relationship as deferred and future-facing: Daily Brief's own complete UX behavior has no governing specification yet. This specification records only that, once one exists, arriving at Watchlist from a Daily Brief item must land the Investor on the specific Entry the item concerned, using the same context-preservation discipline Section 15 states generally. It does not define Daily Brief's own content, screen, or "Watchlist Update" category — that remains Daily Brief UX's own future responsibility.
- **Portfolio preview → full Watchlist.** `UX-007A`'s and `UX-007P`'s own existing Portfolio Workspace header already states a bare Watchlist count ("Reviewed today · 8 holdings · 5 watchlist"). This specification's own entry point contract is what Watchlist itself must do when arrived at this way: land the Investor on Watchlist's full, current state, per `WL-R-039` and `PF-R-054` — no fact material to Watchlist may exist only within that count reference. A richer, card-level Portfolio-hosted preview of Watchlist, per `PF-R-051`–`054`, is anticipated but not yet specified in `UX-007A`/`UX-007P`; extending those documents to add one is explicitly out of this specification's own scope (Section 1).
- **Direct return to an existing Watchlist.** Reopening Watchlist from primary navigation after a prior visit restores the Investor's own last-used ordering, filter, and scroll position, per Section 15.
- **Onboarding when no Entries exist.** Section 8's Empty state governs; it is a valid, honest destination in its own right, never a forced setup flow, per `WL-R-040`–`042`.

## 7. Information Hierarchy

For each Watchlist Entry, presented in this order of priority — meaning before volume, per `UXP-001`:

1. **Identity of the followed opportunity.** The company, security, or theme name, presented plainly, the same identity pattern `UX-005` §4 already establishes for the Investment Workspace header. No new Product field is invented; identity is the ordinary-language subject `APS-007` §5 already describes.
2. **Why it is being followed — truthful absence by default.** `WL-R-023` is explicit: a Follow act requires no justification, thesis, or reasoning. This specification therefore distinguishes two different things that could occupy this position, and requires only the first: (a) the **origin of the Follow act** — a factual provenance note such as "Followed from Discover" or "Followed directly" — which Atlas may honestly record about the act itself without fabricating reasoning; and (b) a **substantive rationale**, which `APS-007` does not require and which this specification SHALL NOT present as though it were expected, complete, or missing when absent. Where no origin is known, the UI states this plainly rather than presenting an empty field as a defect.
3. **Current relevance or state.** Sourced exclusively from the scoped Atlas Priority Model view Section 12 governs; Watchlist itself computes nothing independently, per `WL-R-035`–`036`.
4. **What changed since the last review, when available.** This signal, where it exists, is sourced from the Atlas Priority Model and/or a future Daily Brief "Watchlist Update" category (`WL-R-013`), never independently computed by Watchlist itself. Because Daily Brief's own UX does not yet exist, this specification requires truthful absence — an Entry with no available change signal states plainly that nothing new is known, rather than presenting a fabricated "no change" verdict Watchlist itself is not authorized to compute.
5. **The appropriate next action.** One of Section 9's interaction verbs, determined by the Entry's own current state (Section 14) — most commonly Investigate, or Open Investment Case where progression has already occurred.
6. **Provenance or explanation for Atlas-originated content.** Wherever Atlas surfaces any system-originated note about an Entry (for example, the origin note in item 2, or a Priority Model signal), it is visibly attributed as Atlas-originated, per `UXD-R-054`–`057` and `PP-008`, using clearly attributed third-person framing, never first-person belief language.
7. **Whether deeper investigation has already begun.** Whether an Investment Case already exists for this Entry, per `WL-R-015` and `WL-R-027`. This is the signal that determines whether Section 9's Investigate action or Open Investment Case action is offered.

## 8. Screen Architecture

Addressed without visual mockups, consistent with `APS-007` §3's own exclusion of screens from the Product layer and `UX-000` §3's identical exclusion at the doctrine layer.

- **Page purpose and orientation.** The governing question — "What should I continue following?" — is stated at the top of the Watchlist surface, the same governing-question-in-header pattern `UX-007A` §6 already establishes for Portfolio.
- **Primary summary.** A plain factual status line (Entry count, count currently warranting Attention per the scoped Priority Model view) — never a Conclusion, per Section 5's own deliberate non-decision.
- **Watchlist Entry collection.** The bounded list or grid of Entries, ordered per Section 12.
- **Prioritization as a scoped view.** Any visual distinction between Entries (ordering, an "Attention" indicator) is drawn from the Atlas Priority Model's own scoped view (Section 12), never an independent Watchlist computation, per `WL-R-035` and `WLINV-005`.
- **Empty state.** States plainly that no Entries exist yet; offers Follow as the sole next step, without implying anything is broken or missing, per `WL-R-040`.
- **First-use state.** The Investor's first Entry or first few Entries; no administrative setup step is required beyond the Follow act itself, per `WL-R-041`.
- **Established-use state.** Many Entries, scaled by Section 12's ordering discipline alone — never by requiring manual triage before the surface delivers value, per `WL-R-043`.
- **No-change state.** Where the Priority Model view and any available change signal indicate nothing new, this is presented as a calm, successful state — consistent with `UX-004` §26's own "Silence Is a Valid Outcome" — never as missing content.
- **Partial-data state.** Where an Entry's own Priority Model signal or change signal is temporarily unavailable, the surface states what is unavailable and why, and continues to show what remains current — the same partial-data discipline `UX-007A` §30 already establishes for Portfolio, adapted here.
- **Error and recovery state.** A failure in one Entry's own data SHALL NOT block the entire Watchlist; the surface states the failure, offers retry, and leaves unaffected Entries usable, mirroring `UX-007A` §31.
- **Completion state.** Section 9's Done affordance; a calm acknowledgment that the current visit is finished, never a ceremonial "review complete" record, per Section 9's own distinction from Portfolio's heavier completion pattern.
- **Contextual transition into deeper investigation.** Selecting Investigate or Open Investment Case opens the Investment Workspace (`UX-004`/`UX-005`) as a focused layer above Watchlist, using the identical overlay-and-context-preservation pattern `UX-005` §20–§22 already establishes for opening an Investment Case from the Dashboard — Watchlist plays the role the Dashboard plays there.

The screen must answer "what should I continue following" from the collection view alone, without requiring every Entry to be opened, per `UXP-001` and `WL-R-011`.

## 9. Interaction Model

- **Follow.** Adds exactly one Watchlist Entry through an explicit, unambiguous control (never a passive side-effect of viewing content), per `WL-R-022`. Requires no justification field, per `WL-R-023`.
- **Open.** Expands an Entry's own summary (Section 7's information hierarchy) in place, or in a lightweight panel. Open is inspection only — it creates no Investment Case, begins no investigation, and carries no Product-layer consequence. This is the deliberate boundary this specification draws between glancing at an Entry and acting on it.
- **Review.** Ordinary-language description of the Investor's own visit to the Watchlist surface as a whole; it names no formal act and creates no Product-layer record of its own, consistent with `UXD-R-095`'s own treatment of Workspace-level session language.
- **Investigate.** The explicit, deliberate control, visually and semantically distinct from Open, that constitutes the "genuine, further Investor act" `WL-R-025` requires before progression into an Investment Case occurs. Selecting Investigate is never triggered by Open, by hovering, or by any passive interaction, per `WL-R-025` and `WLINV-007`.
- **Remove.** The Release act, per `WL-R-028`. Immediate, frictionless, and carries no justification requirement, per `WL-R-029` and `WL-R-032`; see Section 11 for the recovery behavior that accompanies it.
- **Ignore for now.** A bounded, session-scoped de-emphasis of an Entry within the current view only. `APS-007` defines no "ignored" Product-layer state; this specification treats Ignore for now as pure UX-layer presentation, per `UXD-R-022`, carrying no persistence obligation and no effect on the underlying Entry, its ordering data, or its eligibility for Follow/Release. It SHALL NOT be implemented as, or confused with, Release.
- **Return.** Closing a deeper context (Investment Workspace, Discover, Daily Brief) and arriving back at Watchlist restores the exact prior scroll position, ordering, and any Ignore-for-now state from the same visit, per Section 15.
- **Done.** A calm, non-blocking acknowledgment that the current visit is finished. Unlike Portfolio's own explicit "Record Portfolio Review Complete" action (`UX-007A` §21.1), Watchlist requires no recorded completion act, because `APS-007` imposes no review-cycle requirement on Watchlist the way `APS-006`'s Portfolio does; Done is available whenever the Investor is ready to leave, not gated on any condition.

**Explicit distinctions**, restated for clarity because conflating them is this specification's single most consequential failure mode (Section 21):

- Following an opportunity (Follow) never itself opens, creates, or implies an Investment Case.
- Opening an Entry (Open) never itself begins investigation or creates an Investment Case.
- Beginning genuine investigation (Investigate) is the one act that may trigger progression, per Section 10.
- Opening an existing Investment Case (where progression has already occurred) is inspection of already-created structure, not a new progression act.
- Opening a Decision Context, and the Decision Workspace built on it, occurs only once a real decision objective exists within that Investment Case — never directly from Watchlist, per `WL-R-016`.
- Recording a Decision occurs only within the Decision Workspace, per `APS-001` and the existing Decision Workspace specifications (`UX-008`–`UX-011`).

Watchlist never implies that Following something is itself an investment judgment or a Decision, per `WLINV-003`, `WLINV-004`, and `PP-003`.

## 10. Progression to Investment Case

The complete, accepted path, per `APS-007` §9 and `APP-001` §3.13:

```
Discover
  → explicit Follow                          (Section 9: Follow)
  → Watchlist Entry                           (WL-R-007)
  → genuine Investor investigation act        (Section 9: Investigate — WL-R-025)
  → system-created Investment Case, if none exists    (WL-R-026, WLINV-006)
  → later Decision Context, when a specific decision objective exists   (WL-R-016, APS-001 §8)
```

The UX transition at each arrow is deliberate and asks nothing administrative of the Investor:

- Selecting Investigate never asks the Investor to name a Case, choose ownership metadata, or configure any technical relationship. Atlas creates the required Investment Case silently, the moment the genuine act occurs, per `WL-R-026` and `WLINV-006` — mirroring exactly the same silent-creation discipline `UX-004`/`UX-005` already assume for an Investment Case's own origin.
- The Investor lands directly inside the newly available Investment Workspace (`UX-005`), already oriented to the followed subject, with no intermediate "Case created" ceremony required.
- Where an Investment Case already exists for an Entry (because a prior Investigate act already created one), selecting the Entry's own next action opens that existing Investment Case rather than creating a second one, per `WL-R-015` and `WL-AC-008`'s own no-duplication discipline.
- Opening a Decision Context, and by extension the Decision Workspace, is never offered directly from Watchlist. It becomes available only from within the Investment Workspace, once a real decision objective exists, per `WL-R-016` and the existing Decision Workspace entry-point discipline (`UX-009` §3).

**Watchlist Case / Watchlist Entry — non-conflation, restated.** Per `UX-005`'s own disambiguation note (Section 4): a "Watchlist Case" is a Case Type describing an already-open Investment Case whose current Decision Context concerns initiation. It is not this specification's own Watchlist Entry, which is the pre-Investment-Case record Sections 6–10 govern. This specification's own screens and copy SHALL NOT use "Watchlist Case" to refer to a Watchlist Entry, and SHALL NOT use "Watchlist Entry" to refer to a Case Type inside the Investment Workspace.

Per `WL-R-027`, whether a progressed Entry remains in Watchlist, is removed, or is marked as progressed is the Investor's own discretion; this specification does not mandate any one outcome, and its own "Existing Investment Case Available" state (Section 14) supports all three without forcing a choice.

## 11. Removal and Non-Permanence

`APS-007` permits Release without historical-integrity consequence (`WL-R-009`, `WL-R-030`, `WLINV-008`, `WLINV-009`); this section states the UX behavior that keeps that Product-layer permission truthful in the interface.

- Removal (Section 9: Remove) completes immediately upon selection — no confirmation dialog, no required justification field, per `WL-R-032` and `WLINV-008`. A confirmation-dialog pattern, however brief, would itself be the friction `WL-R-032` prohibits.
- Removal never implies deletion of an Investment Case, Reasoning, a Decision, or an Outcome. Where an Entry has already progressed, its copy and iconography make clear that removal affects only the Watchlist Entry, never the Investment Case it produced, per `WL-R-031` and `WLINV-011`.
- Immediately after removal, a brief, non-blocking recovery affordance ("Removed. Undo.") is available for a bounded window. This is not friction on the removal act itself — the act already completed — it is a safety net consistent with `UX-000`'s own accessibility and error-prevention discipline (`UXD-R-092`), and it does not reintroduce the confirmation burden `WL-R-032` forbids, because it appears after the fact rather than gating the act.
- Removal language avoids irreversible-action framing ("permanently delete," "cannot be undone") inappropriate to a lightweight Entry with no Reasoning or Decision attached, per `WLINV-008`'s own "no penalty, no required justification" standard — this is a materially lighter act than Abandoning a Decision Context (`APS-001` §12), and its copy must not borrow that heavier register, per `WL-R-010` and `WLINV-010`.
- Where an implementation chooses to retain a released Entry's own record for its own purposes, that retention carries no Product-layer significance and is never presented to the Investor as an active, restorable Watchlist state beyond the bounded Undo window above, per `WL-R-030`.

## 12. Atlas Priority Model

Watchlist presents exactly one scoped view of the single Atlas Priority Model `APS-006` §10 defines (`PF-R-031`–`035`), adopted here by reference per `WL-R-020` and `WL-R-035`–`036`. This specification does not define, and does not need to define, the Model's own calculation; it defines only how the Model's output is communicated within Watchlist:

- Any ordering or "requires attention" signal Watchlist shows is filtered to Entries connected to it, never independently computed, per `WLINV-005`.
- No Entry is ever presented as more "correct" or more worth pursuing than another on Watchlist's own authority; ordering reflects the Investor's own expressed priorities (recency of Follow, proximity to progression, or an explicit Investor-set preference), per `WL-R-033`–`034`.
- Priority is communicated through calibrated, text-legible states (for example, a plain label such as "Requires attention" or "No change"), never through color alone, per `UXD-R-092` and Section 16.
- Watchlist never presents every Entry as equally urgent; where the Priority Model surfaces nothing for an Entry, that Entry is shown calmly, without a manufactured signal, consistent with Section 5's own "calm" requirement and `ATLAS_CONSTITUTION.md`'s own rejection of urgency as a product mechanic.

## 13. Preview Relationships

Watchlist appears, in bounded form, within Portfolio and (once specified) Daily Brief. `UX-000` governs the general preview discipline this specification applies here without redefining it; `APS-006` §13 (`PF-R-051`–`055`) and `APS-007` §13 (`WL-R-037`–`039`) state the Product-layer version of the same rule from each side.

- **Within Portfolio.** The existing header count (`UX-007A`/`UX-007P`, "5 watchlist") is a bounded preview: it must never claim to be the destination, must never independently re-order Watchlist's own Entries, and must never resolve or dismiss an Entry on Watchlist's behalf, per `PF-R-051`–`053`. It always leads to the full Watchlist (Section 6). This specification does not add a richer preview card to `UX-007A`/`UX-007P`; see Section 6's own scope note.
- **Within Daily Brief.** Deferred and future-facing, per `WL-R-013`; Daily Brief's own "Watchlist Update" category, once specified, must observe the identical bounded-preview discipline: never a substitute destination, never an independent re-ranking, never a full resolution, always leading back to Watchlist or the correct contextual destination.
- No fact material to understanding a Watchlist Entry exists only within a hosted preview and nowhere within Watchlist's own area, per `WL-R-039` and `PF-R-054`.

## 14. States

Each state below states what the Investor understands, what action is available, how Atlas avoids asserting uncertainty it does not have, and how the Investor recovers or exits.

- **Loading.** Understands the surface is retrieving current state; no action is offered prematurely; skeleton structure resembles the eventual layout, not a generic spinner, consistent with `UX-007A` §28.
- **Empty.** Understands no Entries exist yet; Follow (via Discover or direct entry) is the sole, calmly presented next step; not framed as an error or a missing feature, per `WL-R-040`.
- **First Follow.** Understands their first Entry now exists; no further setup is requested, per `WL-R-041`.
- **Populated.** Understands the current, bounded set of Entries and their relative priority (Section 12); the next action for each is visible without opening it.
- **Updating.** Understands new information may be arriving; existing Entries remain visible and interactive throughout, never blocked by a full-surface loading state.
- **No Meaningful Change.** Understands calmly that nothing new is known since the last review; presented as a successful, complete state, per Section 8's own no-change treatment.
- **Partial Data.** Understands specifically which Entry's signal is unavailable and why; unaffected Entries remain fully usable, per Section 8.
- **API/Data Error.** Understands a specific, scoped failure with a retry option; the rest of Watchlist remains usable, per Section 8's error-and-recovery treatment.
- **Removal Pending.** Understands an Entry was just removed; sees the bounded Undo affordance, per Section 11.
- **Removal Success.** Understands the Entry is gone from Watchlist and that no investment history was affected, per Section 11.
- **Undo Available.** Understands a time-bounded opportunity to reverse the immediately preceding removal exists; selecting Undo restores the Entry to its exact prior position; the window's own expiry is a quiet, non-alarming transition to Removal Success, consistent with `UX-000`'s own rejection of artificial countdowns as a pressure mechanic (`UX-004` §10).
- **Entry Already Under Investigation.** Understands this Entry already has an open Investment Case; the offered action is Open Investment Case, not Investigate, per Section 10.
- **Existing Investment Case Available.** The same underlying fact as above, stated at the point of decision (for example, in the next-action control itself) rather than only as a passive label.
- **No Action Required.** Understands the current Watchlist requires no further attention right now; distinct from Empty (Entries exist) and from No Meaningful Change (a specific Entry-level state); this is the whole-surface analog.
- **Completion / Done.** Understands the current visit is finished; may leave via Section 9's Done affordance or ordinary navigation at any time, with no gating condition.

## 15. Navigation

- Watchlist sits as a primary destination alongside Portfolio, Discover, and Daily Brief, consistent with `UX-012A` §1's own naming of Atlas's surfaces.
- Contextual return paths: closing the Investment Workspace opened from an Investigate or Open Investment Case action returns the Investor to the exact prior Watchlist scroll position, ordering, and any Ignore-for-now state, per the same state-preservation discipline `UX-005` §21–§22 and `UX-007A` §25 already establish for their own respective Workspaces.
- Return to Discover, where Watchlist was reached via a Discover → Follow act and the Investor chooses to go back, restores Discover's own prior state; Watchlist does not own or alter Discover's own state.
- Transition to the Investment Workspace occurs only via Section 9's Investigate or Open Investment Case actions.
- Transition to the Decision Workspace occurs only from within an Investment Workspace that already contains an open Decision Context — never directly from Watchlist, per `WL-R-016` and Section 10.
- Filters, sort order, and scroll position persist across a visit and across a Return from a deeper context, per Section 9's own Return definition.
- No dead ends: every state in Section 14 offers at least one way forward (an action, a Return path, or Done).

## 16. Accessibility

Governed directly by `UX-000` §19 (`UXD-R-091`–`092`); this specification states Watchlist's own application of that standing requirement.

- Reading order follows Section 7's information hierarchy — identity, then origin/state, then relevance, then change, then next action — predictably for assistive technology.
- Every interaction verb in Section 9 (Follow, Open, Investigate, Remove, Ignore for now, Return, Done) is reachable and operable by keyboard alone.
- Priority and state (Section 12, Section 14) are never communicated by color alone; each carries a text label.
- Action labels are explicit and verb-first ("Investigate," "Remove," "Undo"), never ambiguous icons alone.
- Removal remains recoverable via the Undo affordance (Section 11), itself keyboard-reachable and announced to assistive technology when it appears.
- Priority semantics are stated in plain language ("Requires attention," "No change"), never as an unexplained numeric score, consistent with `UXD-R-063`–`065`.
- Every Atlas-originated note (Section 7 item 6) carries explicit, programmatically associated attribution, per `UXD-R-054`.
- Empty and error states (Section 8, Section 14) are announced clearly to assistive technology, not conveyed by visual absence alone.
- Focus returns to a predictable, stable location after the Undo affordance expires or after returning from a deeper context, mirroring `UX-005` §23's own "Focus restored after closing" requirement.

## 17. Responsive Behavior

Stated architecturally, without pixel values, per Section 3's own non-scope.

- What remains immediately visible at any viewport: an Entry's identity, its next action, and its priority signal (Section 12) — the minimum needed to answer "what should I continue following" without opening anything.
- What may collapse under narrower viewports: secondary metadata (origin note, detailed change description) behind an expansion control, consistent with `UX-007A` §27's own narrow-layout discipline for Portfolio.
- What must never disappear: the primary next action for each Entry, and its priority/attention signal — collapsing either would silently violate `UXD-R-092`.
- Primary actions (Investigate, Remove) remain reachable by touch or keyboard at every viewport, never demoted behind a hover-only affordance, per `UX-007A` §26's own "no essential interaction may depend on pointer hover" rule.
- Priority and provenance remain understandable at narrow widths through the same text-label discipline Section 16 requires generally — never reduced to a color chip alone.
- Entry context (which Entry an expanded panel or Undo affordance belongs to) is preserved and unambiguous regardless of viewport, avoiding the narrow-layout failure mode Section 21 names.

## 18. Explicit UX Exclusions

Each boundary below states the UX consequence of a distinction `APS-007` already draws at the Product layer.

- **Not Discover.** Watchlist has no candidate-sourcing, criteria-matching, or thread-relevance UI of its own, per `WL-R-052`/`WL-R-048`; its collection view never offers a "browse" or "search the universe" affordance — that belongs exclusively to Discover.
- **Not Portfolio.** Watchlist's screen architecture (Section 8) never includes a Health grid, Diversification breakdown, Scenario Analysis, or Capital Allocation section — presenting any of these would visually imply owned-position analysis Watchlist does not have, per `WL-R-047` and `WLINV-002`.
- **Not Daily Brief.** Watchlist never independently computes or displays a cross-surface "what changed today" digest beyond its own Entries' own change signal (Section 7 item 4); that broader digest belongs to Daily Brief once specified.
- **Not Investment Workspace.** Watchlist never inlines Investment Workspace content (thesis, valuation, key drivers) directly within an Entry row; Open (Section 9) shows only Section 7's bounded hierarchy, and deeper content is reached only by transitioning into the Investment Workspace itself.
- **Not Decision Workspace.** Watchlist never offers a Record Decision action, a Proposed Decision field, or any Decision Workspace content directly, per `WL-R-016` and `WLINV-004`.
- **Not a research notebook.** No Entry row offers a citation, Source, or note-taking field of its own, per `WL-R-050`; anything resembling Evidence belongs to Investor Reasoning within a real Investment Case.
- **Not a task manager.** No Entry carries a due date, assignment, or completion checkbox; Ignore for now (Section 9) is the only session-level de-emphasis this specification authorizes, and it persists no task-like state.
- **Not a permanent archive.** The collection view (Section 8) never presents a "previously followed" or "history" tab as a required feature; per `WLINV-009`, Watchlist's own responsibility is the current, live set, not an archive of everything ever followed.
- **Not a broker or trade-execution surface.** No action in Section 9 executes, prepares, or references a trade; the furthest any Watchlist action reaches is opening an Investment Workspace, per `UXD-R-035` and `PP-003`.
- **Not an autonomous recommendation surface.** Any Atlas-originated framing (Section 7 item 6) is attributed, qualified, and non-directive, per `UXD-R-036` and `ADR-003`; Watchlist never presents "Atlas recommends following X" as though Watchlist itself generated that judgment — any such content, where it exists, is Discover's or another surface's own attributed output, merely visible in context.

## 19. Requirements

Normative UX requirements for Watchlist, using the `WLU-R-` prefix — chosen to avoid colliding with `APS-007`'s own `WL-R-` (Product) prefix and `UX-000`'s own `UXD-R-` (Doctrine) prefix, per `UXD-R-096`'s own disambiguation discipline.

**Purpose comprehension**

**WLU-R-001.** The Watchlist surface SHALL communicate its own governing question — "What should I continue following?" — before any Entry-level detail, per Section 8 and `UXP-001`.

**WLU-R-002.** No screen state SHALL imply that Watchlist is a destination for owned-position review, a research archive, or a task list, per Section 5 and Section 18.

**Intentional Follow**

**WLU-R-003.** Every UI path that results in a new Watchlist Entry SHALL require one unambiguous, explicit Investor action; no passive interaction (view, hover, scroll, dwell time) SHALL create an Entry, per `WL-R-022` and `WLINV-007`.

**WLU-R-004.** The Follow control SHALL NOT present a required justification, thesis, or rationale field, per `WL-R-023`.

**WLU-R-005.** No onboarding, tutorial, or suggestion mechanism SHALL pre-populate a Watchlist Entry on the Investor's behalf, per `WL-R-008` and `WLU-F-001`.

**Information hierarchy**

**WLU-R-006.** Each Entry SHALL present, at minimum, its identity, its origin note or its truthful absence, its current Priority Model signal, its available change signal or its truthful absence, and its next action, in the order Section 7 states.

**WLU-R-007.** No UI SHALL fabricate a rationale, change signal, or Priority Model output where none is available; absence SHALL be stated plainly, per Section 7 item 2 and item 4.

**WLU-R-008.** Any Atlas-originated note attached to an Entry SHALL carry visible, third-person attribution, per `UXD-R-054`, `UXD-R-057`, and `PP-008`.

**Priority-model consistency**

**WLU-R-009.** Any ordering, grouping, or "requires attention" treatment applied to Entries SHALL be sourced from the scoped Atlas Priority Model view Section 12 defines; no alternate ranking mechanism SHALL be introduced.

**WLU-R-010.** No visual treatment SHALL imply that all Entries are equally important, nor that any specific Entry is more "correct" than another, per `WL-R-034`.

**Entry review and interaction**

**WLU-R-011.** Open SHALL produce no Product-layer effect; it SHALL only reveal already-known Entry-level information, per Section 9.

**WLU-R-012.** Investigate SHALL be a control visually and semantically distinct from Open, reachable only through deliberate selection, per `WL-R-025`.

**WLU-R-013.** Ignore for now SHALL persist no data beyond the current session/view and SHALL NOT be presented, coded, or described using Release's own language or iconography.

**Progression**

**WLU-R-014.** Selecting Investigate on an Entry with no existing Investment Case SHALL transition the Investor directly into a newly available Investment Workspace, with no intermediate configuration step, per `WL-R-026` and `WLINV-006`.

**WLU-R-015.** Selecting the next action on an Entry with an existing Investment Case SHALL open that existing Investment Case; it SHALL NOT create a second one, per `WL-R-015` and `WL-AC-008`.

**WLU-R-016.** No UI path SHALL offer direct entry into a Decision Context or Decision Workspace from Watchlist; that transition SHALL be available only from within an Investment Workspace that already contains one, per `WL-R-016`.

**WLU-R-017.** "Watchlist Case" and "Watchlist Entry" SHALL be used according to `UX-005`'s own disambiguation note and SHALL NOT be used interchangeably anywhere in this specification's own governed UI.

**Removal**

**WLU-R-018.** Removal SHALL complete immediately upon selection, without an intervening confirmation dialog, per `WL-R-032`.

**WLU-R-019.** Removal copy SHALL NOT use irreversible-action or data-loss language; it SHALL make clear that only the Watchlist Entry is affected, per Section 11 and `WLINV-011`.

**WLU-R-020.** A bounded, non-blocking Undo affordance SHALL follow every removal, per Section 11 and Section 14.

**State behavior**

**WLU-R-021.** Every state named in Section 14 SHALL be implemented; no unnamed or ambiguous intermediate state SHALL be presented to the Investor without explanation.

**WLU-R-022.** A failure affecting one Entry's own data SHALL NOT block or degrade the rest of the Watchlist surface, per Section 8's error-and-recovery treatment.

**Navigation**

**WLU-R-023.** Returning from a deeper context (Investment Workspace, Discover) SHALL restore the Investor's own prior Watchlist scroll position, ordering, and Ignore-for-now state, per Section 15.

**WLU-R-024.** No state defined in Section 14 SHALL leave the Investor without at least one available forward action, return path, or Done affordance.

**Previews**

**WLU-R-025.** Any Watchlist content hosted within Portfolio SHALL remain bounded, SHALL NOT independently re-rank Watchlist's own Entries, and SHALL always lead to the full Watchlist, per `PF-R-051`–`054` and `WL-R-037`–`039`.

**WLU-R-026.** No fact required to understand a Watchlist Entry SHALL be presented only within a hosted preview and nowhere within Watchlist's own area.

**Accessibility**

**WLU-R-027.** Every interaction verb in Section 9 SHALL be operable by keyboard alone, per `UXD-R-092`.

**WLU-R-028.** No state or priority signal SHALL be communicated by color alone; a text label SHALL always accompany it, per `UXD-R-092`.

**WLU-R-029.** Focus SHALL return to a predictable location after the Undo affordance expires or after returning from a deeper context, per Section 16.

**Responsive preservation**

**WLU-R-030.** At every viewport, an Entry's identity, next action, and priority signal SHALL remain immediately visible, per Section 17.

**WLU-R-031.** No primary action SHALL be demoted to a hover-only affordance at any viewport, per Section 17.

**Error prevention**

**WLU-R-032.** No UI mechanism SHALL allow a Follow, Investigate, or Release act to be triggered without an identifiable, deliberate Investor action, per `WL-R-008`, `WL-R-022`, `WL-R-025`, and `WL-R-028`.

**WLU-R-033.** No UI mechanism SHALL allow Watchlist to compute or display a ranking independent of the Atlas Priority Model, per `WL-R-035` and `WLU-R-009`.

**Completion behavior**

**WLU-R-034.** A Done affordance SHALL be available at any time the Investor is viewing Watchlist, with no gating condition, per Section 9.

**WLU-R-035.** No completion action SHALL require the Investor to reach a specific Entry count, a "zero attention items" state, or any other artificial threshold before Done becomes available.

**Product and UX traceability**

**WLU-R-036.** Every requirement in this section SHALL be traceable, by citation, to at least one of: `ATLAS_CONSTITUTION.md`, an `APP-000` Product Principle, an `APS-007` provision, an `APS-006` provision, or a `UX-000` `UXD-R-` rule, per Section 23.

## 20. Invariants

**WLU-INV-001 — Watchlist always represents explicit Investor intent.** No Entry, ordering signal, or state presented by this specification's own UI SHALL originate from anything other than a deliberate Investor act or the Atlas Priority Model's own already-governed computation, per `WLINV-007`.

**WLU-INV-002 — Watchlist never performs Reasoning.** No UI element SHALL invite the Investor to construct or record Reasoning within the Watchlist surface itself, per `WLINV-003`.

**WLU-INV-003 — Watchlist never records a Decision.** No UI element within Watchlist SHALL present a Record Decision, Proposed Decision, or equivalent control, per `WLINV-004`.

**WLU-INV-004 — Watchlist never automatically creates an Entry.** No feature, onboarding flow, or Atlas-originated suggestion SHALL create a Watchlist Entry without an explicit Follow act, per `WLINV-007` and `WLU-R-003`.

**WLU-INV-005 — Watchlist never becomes Portfolio or Discover.** No screen state SHALL present owned-position content, candidate-sourcing, or criteria-matching functionality, per `WLINV-002` and Section 18.

**WLU-INV-006 — Removing an Entry never removes durable investment history.** No removal path SHALL affect an Investment Case, Reasoning, a Decision, or an Outcome, per `WLINV-011`.

**WLU-INV-007 — Priority remains one scoped view of the Atlas Priority Model.** No independent ranking mechanism SHALL exist anywhere in this specification's own governed UI, per `WLINV-005`.

**WLU-INV-008 — Every Atlas-originated rationale remains visibly attributable.** No Atlas-originated note SHALL be presented without attribution, per `UXD-R-054` and `PP-008`.

**WLU-INV-009 — The user can always distinguish following from investigating.** Follow, Open, and Investigate SHALL remain three visually and behaviorally distinct actions at every point in this specification.

**WLU-INV-010 — The user can always leave the screen with a clear completion state.** A Done affordance, per Section 9, SHALL be reachable from every state Section 14 defines.

## 21. Failure Modes

Atlas SHALL fail closed: where continuing would require this specification, `APS-007`, `APS-006`, or `UX-000` to be violated, the interface SHALL present an honest, bounded state rather than proceed on a fabricated or inferred basis. No specific error copy is prescribed here.

**WLU-F-001 — Everything looks urgent.** Presenting every Entry with equal visual weight, or manufacturing an attention signal the Priority Model did not produce, violates Section 12, `WL-R-034`, and `WLU-R-010`, and directly contradicts `ATLAS_CONSTITUTION.md`'s own rejection of urgency as a product mechanic.

**WLU-F-002 — Entries lack a clear reason for being followed.** Where an Entry's origin note is silently omitted rather than shown as truthful absence (Section 7 item 2), the Investor cannot distinguish a data gap from Atlas withholding information — this violates `WLU-R-007`.

**WLU-F-003 — Discover content is auto-added.** Any mechanism that creates an Entry from Discover output without an explicit Follow act violates `WL-R-014`, `WLINV-007`, and `WLU-R-003`.

**WLU-F-004 — Removal appears to delete investment history.** Removal copy or iconography implying an Investment Case, Reasoning, or Decision is affected violates `WLU-INV-006` and `WL-R-031`.

**WLU-F-005 — Watchlist becomes a task backlog.** Introducing due dates, assignment, or completion-tracking on an Entry violates `WL-R-054` and Section 18.

**WLU-F-006 — Watchlist becomes a research notebook.** Attaching citation, Source, or note fields to an Entry violates `WL-R-050` and Section 18.

**WLU-F-007 — Following is mistaken for investing.** Any copy, iconography, or flow implying that a Follow act constitutes an investment judgment or Decision violates `WLINV-003`, `WLINV-004`, and `PP-003`.

**WLU-F-008 — An Investment Case and Decision Context are conflated.** Offering a Decision Context or Decision Workspace transition directly from Watchlist, or describing an Investment Case using Decision Context language, violates `WL-R-016` and `WLU-R-016`.

**WLU-F-009 — Previews replace the destination.** A Portfolio- or Daily-Brief-hosted Watchlist preview that omits a path back to the full Watchlist, or that presents itself as sufficient on its own, violates `PF-R-051`, `WL-R-039`, and `WLU-R-025`–`026`.

**WLU-F-010 — Narrow layouts hide provenance or primary actions.** Collapsing an Entry's next action or priority signal at narrow viewports violates `WLU-R-030`–`031` and `UXD-R-092`.

**WLU-F-011 — Empty state creates unnecessary setup work.** Requiring categorization, portfolio linkage, or any step beyond a single Follow act before Watchlist delivers value violates `WL-R-041` and `WLU-R-005`.

**WLU-F-012 — The user cannot tell when they are done.** Omitting a reachable Done affordance from any state in Section 14 violates `WLU-INV-010` and `WLU-R-034`.

## 22. Acceptance Criteria

**WLU-AC-001 (Purpose understood without explanation).** A new Investor is observed to understand, from the collection view alone, that Watchlist answers "what should I continue following," per Section 5 and `WLU-R-001`.

**WLU-AC-002 (Every Entry reflects explicit intent).** No Entry is ever observed to exist without a traceable Follow act, per `WLU-INV-001` and `WLU-INV-004`.

**WLU-AC-003 (Discover → Follow → Watchlist → Investigate path is understandable).** The full path from a Discover candidate, through Follow, through Investigate, to an open Investment Workspace, is observed to be traversable by a new Investor without external explanation, per Section 10.

**WLU-AC-004 (Distinct from Portfolio and Discover).** No owned-position content, no candidate-sourcing affordance, and no criteria-matching UI is ever observed within Watchlist, per `WLU-INV-005` and Section 18.

**WLU-AC-005 (Removal is safe and comprehensible).** Every observed removal completes without a confirmation dialog, offers a bounded Undo, and is understood by the Investor to affect only the Watchlist Entry, per Section 11.

**WLU-AC-006 (Durable investment history unaffected).** No observed removal is found to alter an Investment Case, Reasoning, Decision, or Outcome, per `WLU-INV-006`.

**WLU-AC-007 (Priority is consistent with Portfolio and Daily Brief).** No independently computed ranking is ever observed within Watchlist's own content, and any priority signal shown is traceable to the same Atlas Priority Model Portfolio itself uses, per `WLU-R-009` and `WLU-INV-007`.

**WLU-AC-008 (Existing Investment Case reused, not duplicated).** Selecting the next action on an already-progressed Entry is observed to open the existing Investment Case, never to create a second one, per `WLU-R-015`.

**WLU-AC-009 (Decision Workspace entered only through a real Decision Context).** No observed path reaches the Decision Workspace directly from Watchlist; every observed path passes through an Investment Workspace's own open Decision Context, per `WLU-R-016`.

**WLU-AC-010 (States are complete).** Every state named in Section 14 is observed to be reachable and to offer at least one forward action or exit, per `WLU-R-021` and `WLU-R-024`.

**WLU-AC-011 (Accessibility meaning is preserved).** Every interaction verb is observed to be keyboard-operable, and no state or priority signal is observed to depend on color alone, per Section 16.

**WLU-AC-012 (No Product or Core redesign required).** No acceptance check above is found to require a new Core Domain Object, a new Core invariant, a change to `APS-007`'s own normative behavior, or a change to any other Product Architecture document, per `WL-AC-008`.

## 23. Traceability

| Section | Normative UX basis | Normative Product basis | Core basis |
|---|---|---|---|
| §5 UX Definition | `UX-000` §5, §24 (`UXP-001`) | `APP-000` PP-004; `APS-007` §2, §17 | — |
| §6 Entry Points | `UX-000` `UXD-R-008` | `WL-R-013`, `WL-R-014`, `WL-R-024`, `WL-R-040`–`042` | — |
| §7 Information Hierarchy | `UX-000` §12–14, §20 (`UXD-R-054`–`057`, `UXD-R-096`) | `WL-R-023`, `WL-R-035`–`036` | — |
| §8 Screen Architecture | `UX-000` `UXD-R-071` (Conclusion boundary) | `WL-R-011`, `WL-R-040`–`044` | — |
| §9 Interaction Model | `UX-000` §7 (`UXD-R-011`) | `WL-R-022`, `WL-R-025`, `WL-R-028`–`029`, `WL-R-032`, `WLINV-007` | — |
| §10 Progression | `UX-000` `UXD-R-023`, `UXD-R-104` | `WL-R-015`–`016`, `WL-R-025`–`027`, `WLINV-006`; `APP-001` §3.13 | `APS-001` §8 (Decision Context creation) |
| §11 Removal | `UX-000` `UXD-R-092` | `WL-R-009`, `WL-R-028`–`032`, `WLINV-008`–`010` | — |
| §12 Atlas Priority Model | `UX-000` §12 (`UXD-R-058`–`061`) | `APS-006` §10 (`PF-R-031`–`035`); `WL-R-020`, `WL-R-035`–`036` | — |
| §13 Preview Relationships | `UX-000`'s own preview governance (adopted, not itself defining it) | `APS-006` §13 (`PF-R-051`–`055`); `APS-007` §13 (`WL-R-037`–`039`) | — |
| §14 States | `UX-000` §19 (`UXD-R-091`–`092`) | `WL-R-040`, `WL-F-001`–`009` | — |
| §15 Navigation | `UX-005` §20–§22; `UX-007A` §25 | — | — |
| §16 Accessibility | `UX-000` §19; `ADR-002` C-06 | — | — |
| §17 Responsive Behavior | `UX-007A` §26–§27 | — | — |
| §18 Explicit UX Exclusions | `UX-000` §8 (`UXD-R-020`–`039`) | `WL-R-047`–`054`, `WLINV-002` | — |
| §19–22 Requirements/Invariants/Failure Modes/Acceptance | `UX-000`, throughout, per each citation | `APS-007`, throughout, per each citation | `OE-002` §4 (via `WLINV-001`/`WLINV-012`) |

No temporary report (the UX Correspondence Investigation, the UX Governance Resolution Sprint's own deliverable text, or the UX Architecture Layer Investigation) is cited above as a governing repository authority; each is a completed session finding already absorbed into the committed documents this table cites directly.

## 24. Open Questions and Deferred Work

- **Multi-Portfolio Watchlists.** Coupled to `APS-006` §24's and `APS-007` §24's own identical open question. Classified: **requires separate architecture work** — this specification assumes exactly one Watchlist per Investor, per `WL-R-045`, and does not anticipate a UX for a multi-Watchlist model.
- **Whether Watchlist Entry later needs formal Product Concept status.** Genuinely open, mirroring `APS-007` §24's own framing. Classified: **deferred** — a future Product Architecture decision this specification has no authority to make; if it occurs, this specification's own Section 7 and Section 10 would require review, not silent continuation.
- **Whether released Entries may later inform Investor Lab.** Mirrors `APS-007` §24's own open question. Classified: **out of scope** — this specification's own Section 11 governs current removal behavior regardless of what a future Investor Lab specification eventually decides.
- **Monitoring and Signal integration.** `APS-007` §8 (`WL-R-021`) records this as future-facing. Classified: **deferred** — this specification's own Section 12 states only that any future signal would be expressed through the Atlas Priority Model, not through an independent Watchlist mechanism; the UX of an actual Signal has no governing specification yet.
- **Sorting and grouping methodology.** Section 12 (`WL-R-033`) states that ordering reflects Investor-expressed priority, but the exact set of sort/group options (by recency, by priority signal, manually) is not decided here. Classified: **non-blocking** — any reasonable implementation of Section 12's own ordering discipline satisfies this specification; a future, narrower UX addendum may specify exact options without amending this document's own architecture.
- **The exact UX relationship to a future global Search function.** No global Search UX specification exists yet anywhere in the corpus. Classified: **out of scope** — this specification's own entry points (Section 6) do not depend on Search existing, and nothing here would need to change if Search is added later, provided any future Search-to-Watchlist path observes Section 6's own "no automatic entry-creation" discipline.

None of the above is decided by implication anywhere in this document.

---

*This specification does not modify `ATLAS_CONSTITUTION.md`, `Architecture-Governance.md`, `APP-000`, `APP-001`, any `APS` document, `UX-000`, or any other existing UX document. It introduces no new Core Domain Object, no new Product Concept, and requires no Core, Product Architecture, or implementation redesign.*
