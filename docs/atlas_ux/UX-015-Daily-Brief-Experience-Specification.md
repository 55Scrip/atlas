# UX-015 — Daily Brief Experience Specification

**Status:** Draft, v0.1. This is the second new operational UX specification authored after the completed Product Architecture Reconciliation, `APP-001` v0.4, `APS-006` through `APS-009`, the UX Correspondence Investigation, the UX Governance Resolution Sprint, and `UX-014` (Watchlist). It states the complete governing UX contract for Daily Brief: mental model, relationships, information hierarchy, screen architecture, interaction, previews, states, navigation, accessibility, and responsive behavior. It does not redefine Daily Brief's own Product semantics, which remain governed exclusively by `APS-008`; it does not specify visual tokens, pixel dimensions, implementation technology, algorithms, or persistence mechanisms.

---

## 1. Governance Metadata

Stated here in full, per `Architecture-Governance.md` §10's own requirement, following the pattern `UX-014` §1 already established for this authoring lineage.

- **Document identifier:** UX-015.
- **Title:** Daily Brief Experience Specification.
- **Version:** v0.1.
- **Status:** Draft — the smallest truthful status available to a newly authored specification. This document has not undergone Internal Consistency Review, Targeted Consistency Correction, or Final Verification; it is not Release Candidate and not Final.
- **Parent authority:** `UX-000-Atlas-UX-Doctrine.md` (Release Candidate RC v1.0) — the highest governing document within the Atlas UX Architecture; this specification SHALL NOT contradict it, redefine a term it defines, or exceed the authority its own §7 (UX Responsibilities) and §8 (UX Prohibitions) grant.
- **Product authority:** `APP-000` — Atlas Product Doctrine (Draft v0.4); `APP-001` — Atlas Product Concept Taxonomy (Draft v0.4), §4 (Daily Brief's newly-recorded deferral) and §9 item 9; `APS-008` — Daily Brief (Draft v0.1), the primary Product-layer authority this specification translates into a UX contract; `APS-006` — Portfolio (Draft v0.1), for the Atlas Priority Model (§10) and Bounded Preview Governance (§13) this specification adopts by reference; `APS-007` — Watchlist (Draft v0.1), for the Watchlist Update preview relationship and its own governing `UX-014`; `APS-001` — Decision Context (Draft v0.1), for the boundary this specification must never cross. `APS-009` (Discover) is cited only for the deferred, future-facing relationship `APS-008` itself already names (`DB-R-016`); Discover's own complete UX behavior is explicitly out of scope, per the authorizing task's own constraint.
- **Dependencies:** `UX-014-Watchlist-Experience-Specification.md`, for the Watchlist Update preview's own upstream side and for the authoring style, rigor, and rule-prefix convention this specification follows. `UX-004`/`UX-005` — Investment Workspace, and `UX-007A`/`UX-007P` — Portfolio Workspace, for the destinations Daily Brief routes into and the preview relationship Portfolio hosts of Daily Brief. `UX-000-Atlas-UX-Doctrine.md`, for every doctrine-level rule cited throughout. `ADR-002-Critical-UX-Architecture-Resolutions.md` (C-01 information hierarchy, C-06 unavailable-state accessibility) and `ADR-003-Recommendation-Identity-and-Terminology-Resolution.md` (Atlas Recommendation / Proposed Decision Candidate Content boundary), adopted here unchanged.
- **Scope:** Daily Brief's own UX mental model; relationship to Portfolio, Watchlist, Discover, Investment Workspace, Decision Workspace, Investment Case, Decision Context, and the Atlas Priority Model; meaningful change presentation; information hierarchy; Verdict, priority, change, evidence, and reasoning presentation; uncertainty visibility; preview architecture in both directions Daily Brief participates in; interaction model; repeat-visit and completion behavior; states; navigation; accessibility; responsive behavior at the architectural level; AI attribution; Investor ownership; explicit UX exclusions.
- **Non-scope:** Any Product semantics `APS-008` already governs (this specification translates, never restates as though it were the authority); visual token values; pixel dimensions; typography; color; animation timing; implementation technology; algorithms; relevance-filtering or ranking computation; data schemas; persistence mechanisms; Discover's own complete UX behavior (reserved for its own future specification); Monitoring's, Signals', or Notifications' own complete UX behavior (none yet specified anywhere); any amendment to `APP-000`, `APP-001`, any `APS`, `UX-000`, or any existing UX specification.
- **Affected documents:** None requiring amendment. This specification does not modify `UX-014`, `UX-007A`, `UX-007P`, `UX-012A`, `UX-012B`, `UX-012C`, or any other existing UX document; a future, separately-authorized task may choose to add a literal Daily-Brief-preview element to `UX-007A`/`UX-007P` or a Watchlist-Update-preview cross-reference to `UX-014`, but that is not performed or required here.
- **Superseded documents:** None. No dedicated Daily Brief UX specification has ever existed in this repository. The scattered "Daily Briefing" references within `UX-008`, `UX-009`, `UX-009A`, `UX-010`, `UX-011`, `UX-012A`, and `UX-012C` — each a passing entry-point or deep-link reference from another surface's own point of view, never a specification of Daily Brief's own behavior, per the completed UX Correspondence Investigation — are not superseded by this document; they remain accurate as far as they go and require no correction as a consequence of this document's creation.
- **Migration requirements:** None. No existing UX document or implementation is required to change as a consequence of this document's creation.

## 2. Purpose

Daily Brief requires its own UX specification because `APS-008` states Daily Brief's complete Product-layer behavior but explicitly excludes screens, workflows, navigation, visual design, and interaction design from its own scope (`APS-008` §3). This specification closes that gap: it translates `APS-008`'s normative requirements into a complete, implementable UX contract, following the same method and rigor `UX-014` already applied to `APS-007`, so that a future visual design artifact, an implementation, engineering, QA, or any AI agent working on Atlas can build the Daily Brief experience without inventing new UX rules — or new Product rules — of their own.

Daily Brief's own central user question, unchanged from `APS-008` §2, governs every decision in this document: **"What has changed since I last looked?"** — a temporal, delta question, distinct from Portfolio's own snapshot question "where do I stand" (`APS-006` §2, realized in `UX-007A`/`UX-007P`) and from Watchlist's own "what should I continue following" (`APS-007` §2, realized in `UX-014`).

## 3. Scope and Non-Scope

Restated from Section 1 for direct reference: in scope is everything a human perceives or does when using Daily Brief — mental model, relationships, hierarchy, screens, interaction, previews, states, navigation, accessibility, responsive behavior — tested against `UX-000` `UXD-R-008`'s own scope discipline: a statement belongs here only if it concerns perception or action, would remain true regardless of the specific screen, framework, or visual design used to express it, and would change if `APS-008`'s own normative behavior changed.

Out of scope, per `UX-000` §3 and `APS-008` §3: any Product semantics, visual tokens, pixel dimensions, implementation technology, algorithms, relevance-filtering computation, data schemas, or persistence mechanisms. Also out of scope: Discover's own complete UX behavior; Monitoring's, Signals', and Notifications' own complete UX behavior, none yet specified anywhere; any change to `UX-014`, `UX-007A`, `UX-007P`, `UX-012A`, `UX-012B`, or `UX-012C`.

## 4. Governing References

- **`ATLAS_CONSTITUTION.md`.** Normative, superior to every document in the Atlas Product and UX Architecture. The Product Philosophy's own rejection of "urgency as a product mechanic" and "confusing activity with progress" grounds this specification's own insistence that Daily Brief remain calm, bounded, and honest about absence (Section 5, Section 12).
- **`Architecture-Governance.md`.** Normative, governs this document's own governance-metadata discipline (§10) and document-status discipline.
- **`APP-000` — Atlas Product Doctrine, Draft v0.4.** Normative Product. PP-001 (Attention Before Information), PP-003 (AI Supports, Never Replaces, Investor Judgment), PP-004 (Progressive Disclosure), PP-005 (Human Ownership), PP-007 (Uncertainty Disclosed, Not Concealed), PP-008 (Provenance) ground this specification throughout, cited by identifier at each point of use.
- **`APP-001` — Atlas Product Concept Taxonomy, Draft v0.4.** Normative Product. §4 governs Daily Brief's own status as newly-recorded deferred territory, not an independent Product Concept; §3.13 (Investment Case) governs the destination Daily Brief routes into.
- **`APS-008` — Daily Brief, Draft v0.1.** Normative Product, the primary authority this specification translates. Every `DB-R-`, `DBINV-`, `DB-F-`, and `DB-AC-` identifier cited below refers to this document.
- **`APS-006` — Portfolio, Draft v0.1.** Normative Product, for the Atlas Priority Model (§10, `PF-R-031`–`035`) and Bounded Preview Governance (§13, `PF-R-051`–`055`) this specification adopts by reference rather than restating.
- **`APS-007` — Watchlist, Draft v0.1.** Normative Product, for the state Watchlist exposes for Daily Brief's own Watchlist Update preview, per `WL-R-037`–`039`.
- **`APS-001` — Decision Context, Draft v0.1.** Normative Product, for the boundary (`DC-R-017`, `DC-R-021`) this specification's own review-routing discipline (Section 10) must not cross.
- **`UX-000-Atlas-UX-Doctrine.md`, Release Candidate RC v1.0.** Normative UX, the immediate parent authority for every UX-layer rule in this document.
- **`ADR-002-Critical-UX-Architecture-Resolutions.md`, Accepted.** Normative UX within its own stated scope; C-01 (information hierarchy) and C-06 (`aria-disabled`, never native `disabled`) are cited where Daily Brief's own states require them (Section 13).
- **`ADR-003-Recommendation-Identity-and-Terminology-Resolution.md`, Accepted.** Normative UX within its own stated scope; governs how any Atlas-originated framing within a Verdict item or Thesis-Impacting Change must be presented (Section 8, Section 17).
- **`UX-014-Watchlist-Experience-Specification.md`.** Cited for its own §13 "Within Daily Brief" note, which anticipated exactly this document; this specification's own Section 11 fulfills that anticipation and SHALL remain consistent with it. Also cited for its own precedent on the "no Watchlist Conclusion" decision, directly analogous to Section 5's "no Daily Brief Conclusion" decision here.
- **`UX-007A-Portfolio-Workspace-Wireframe-Specification.md`, `UX-007P-Portfolio-Workspace-Final-Polish.md`.** Checked directly and confirmed to contain no existing reference to Daily Brief; Section 6 and Section 11 state this specification's own contract for the anticipated Portfolio-hosted preview without asserting one currently exists.
- **`UX-012A`, `UX-012B`, `UX-012C` — Atlas Design System.** Cited for reusable component, interaction, and accessibility patterns this specification builds on rather than reinvents (Section 14, Section 15).

## 5. UX Definition

Daily Brief is the bounded experience that communicates meaningful change — never comprehensive information — since the Investor's own last visit. It is not a company profile, not a portfolio snapshot, not a research terminal, not a monitoring dashboard, and not an inbox.

The Daily Brief experience must feel:

- **immediately answerable** — a reader can state, from the first screen alone, whether anything requires attention, per `UXP-001` (Meaning Before Volume) and `DB-R-012`;
- **calm** — no manufactured urgency, no red for red's sake, consistent with `ATLAS_CONSTITUTION.md`'s own rejection of urgency as a product mechanic and `DB-R-076`;
- **honest about absence** — "nothing new" is a complete, successful answer, per `DBINV-011`, never padded to appear active;
- **bounded and finishable** — a definite end exists; nothing about the experience creates the sensation of "more below," per `DB-R-072` and `DB-R-089`;
- **connected, not comprehensive** — every item traces to something the Investor owns, follows, or has reasoned about, per `DB-R-026`; general market or news significance alone earns no place here.

It must not feel like:

- Portfolio (it answers "what changed," never "where do I stand," per `DBINV-002` and `DB-R-090`);
- Discover (its own Discover content is a small, bounded pointer, never a browse or search surface, per `DBINV-003`);
- Watchlist (its own Watchlist content is a bounded update preview, never the full Entry list or an editing surface, per `DBINV-004`);
- an inbox (it compresses and prioritizes the Delta into meaning; it is never a raw, unranked, chronological log of everything that fired, per `DB-R-095`);
- a monitoring dashboard (Completed Monitoring, once it exists, is quiet confirmation of coverage, never a live telemetry display, per `DB-R-070`).

**Deliberate non-decision — no "Daily Brief Conclusion."** `UX-000` `UXD-R-071` recognizes exactly five governed Conclusion variants, each grounded in specific underlying Product-layer content (pre-Reasoning material, a Premise, a Learning Result, or an Investment Case/Portfolio state). The Verdict `APS-008` §11 defines is explicitly *"a temporally-scoped view of the Atlas Priority Model... never an independently computed signal"* (`DB-R-042`) — it carries no Reasoning, no Premise, and no Learning Result of its own. This specification therefore deliberately does not introduce a "Daily Brief Conclusion," for the identical reason `UX-014` §5 already established for Watchlist: doing so would be a new Conclusion variant `UXD-R-071` does not authorize, and would risk implying Daily Brief has formed a judgment it has not, contrary to `DB-R-045` and `DBINV-005`. Section 9's own "Verdict block" is a scoped, factual presentation of Priority Model output, never a Conclusion in the doctrine's governed sense.

## 6. Relationship to Neighboring Surfaces and Concepts

Each relationship below translates `APS-008` §8's own classification into its UX consequence; none is redefined here.

- **Portfolio.** Existing and product-level, running in both directions (`DB-R-014`). Daily Brief reads the same underlying state Portfolio reads, filtered temporally; and Portfolio hosts a bounded preview of Daily Brief. This specification governs the latter relationship from Daily Brief's own side in Section 11.
- **Watchlist.** Existing and product-level (`DB-R-015`). Daily Brief hosts a bounded Watchlist Update preview, reading the state `UX-014`'s own Watchlist exposes for exactly this purpose, per `WL-R-037`–`039`. Governed here in Section 11.
- **Discover.** Deferred and future-facing (`DB-R-016`); Discover has no governing Product Architecture specification for its complete behavior yet, and no UX specification at all. Daily Brief anticipates hosting a bounded Discover Highlight preview, per Section 11, without this specification defining Discover's own content or ranking.
- **Investment Workspace / Investment Case.** Existing and product-level (`DB-R-017`). Daily Brief reads across Investment Cases the same way Portfolio does, filtered to what changed since last visit. Section 10 governs how Daily Brief routes an Investor into the relevant Investment Workspace.
- **Decision Workspace / Decision Context.** Existing and product-level (`DB-R-018`). Daily Brief's own review-routing content reads Decision Contexts whose state has newly changed; it never creates, closes, or reopens one, per `DB-R-018` and `DBINV-013`. Section 10 governs the routing path; Daily Brief never offers direct entry into the Decision Workspace's own reasoning surfaces.
- **Atlas Priority Model.** Derived and product-level (`DB-R-022`). The Verdict is a temporally-scoped view of this one shared model, identical in kind to Portfolio's own Requires Attention category and Watchlist's own priority signal (`UX-014` §12); Daily Brief computes nothing independently. Section 9 governs its presentation.

## 7. Meaningful Change and the Delta

`APS-008` §9 (`DB-R-026`–`033`) states what qualifies a fact for inclusion; this section states how that qualification is communicated, never how it is computed.

- Every item presented traces visibly to a connection — an owned position, a followed Watchlist Entry, or an open or recently-closed Investment Case — per `DB-R-026`. Where the UI shows an item, it also shows, or makes reachable, what it connects to; an unconnected fact is never observed present, per `DB-AC-005`.
- Daily Brief never claims completeness. Its own framing communicates relevance-over-completeness honestly (for example, "here is what's connected to what you own or follow" rather than implying "here is everything that happened"), consistent with `DB-R-027`.
- A materially adjacent development with no clean connection of its own (`DB-R-033`) is shown only through the lens of the specific owned position or followed Entry it affects — never as an independent item in its own right.
- A fact already shown, unchanged, in a prior visit is not shown again, per `DB-R-032`; Section 12 states the corresponding state behavior.

## 8. Information Hierarchy

`APS-008` §10 states four tiers as responsibility, explicitly not layout (`DB-R-038`); this section states the UX translation of each tier without asserting a required visual order beyond what Section 9 itself proposes as one reasonable realization (`DB-R-039`).

1. **Tier 1 — the Verdict.** The smallest content answering "does anything require my attention, right now," per `DB-R-034`. Presented first, always visible without scrolling on first view, per `UXP-001`.
2. **Tier 2 — the story of what changed.** The Delta translated into meaning connected to specific owned positions or followed Entries, per `DB-R-035` — never a raw event list.
3. **Tier 3 — where to look next.** Review-routing content (Section 10) and the Watchlist Update preview (Section 11) — content that informs a decision to investigate further without itself requiring one, per `DB-R-036`.
4. **Tier 4 — periphery.** Discover Highlight (Section 11) and Completed Monitoring content — safe to skip entirely, per `DB-R-037` and `DB-R-064`.

**Verdict presentation.** The Verdict states plainly whether anything currently requires attention, sourced exclusively from the Atlas Priority Model (Section 6), never independently computed, per `DB-R-042`–`043`. Where the same item also appears in Portfolio's own Requires Attention category, the two presentations SHALL NOT disagree about the underlying fact; they may differ only in framing — current status (Portfolio) versus newly-changed (Daily Brief) — per `DB-R-044`. An empty Verdict is a calm, complete state, never padded to appear active, per `DB-R-046`–`047`.

**Priority presentation.** Identical in kind to `UX-014` §12's own treatment for Watchlist: text-legible, never color-only, never independently ranked, always traceable to the one shared Atlas Priority Model.

**Change presentation (Thesis-Impacting Change).** Where Daily Brief identifies a Thesis-Impacting Change (`APS-008` §13, `DB-R-054`–`058`), the UI discloses the new information's own connection to already-recorded Reasoning and stops there — it never asserts that the original Reasoning was wrong, and never implies a specific response is required, per `DB-R-057`. Where no genuine, traceable Thesis-Impacting Change exists, none is presented; a fabricated or speculative one is a failure mode (Section 23, `DBU-F-008`).

**Evidence presentation.** Daily Brief never displays full Evidence content inline. Where a Tier 2 item's own change is grounded in new Evidence, the UI names the Evidence's own existence and connection, and routes to the Investment Workspace (`UX-004`/`UX-005`) for full inspection — Evidence itself remains governed and presented within Investor Reasoning, never reproduced here, per `WL-R-050`'s own identical discipline for Watchlist, applied here by analogy.

**Reasoning visibility.** Daily Brief never displays full Investor Reasoning inline, and never invites the Investor to construct or edit Reasoning within itself. A Thesis-Impacting Change makes the existence and general shape of a connection to recorded Reasoning visible; the Reasoning's own full content is inspected only by transitioning into the relevant Decision Context, per Section 10.

**Uncertainty visibility.** Where a Verdict item or Thesis-Impacting Change rests on incomplete or contested Evidence, that condition is disclosed rather than smoothed over, per PP-007 and `UXD-R-062`–`065`; Daily Brief never presents a degree of confidence its underlying material does not support.

## 9. Screen Architecture

Addressed without visual mockups, consistent with `APS-008` §3's own exclusion of screens from the Product layer.

- **Page purpose and orientation.** The governing question — "What has changed since I last looked?" — is stated at the top of the Daily Brief surface, the same governing-question-in-header pattern `UX-007A` §6 and `UX-014` §8 already establish.
- **Verdict block.** Tier 1's own content (Section 8), the most prominent element, answering whether anything requires attention before any other content is read.
- **Change story.** Tier 2's own content, organized by connected owned position or followed Entry, never as an undifferentiated event list.
- **Review routing and Watchlist Update.** Tier 3's own content (Section 10, Section 11).
- **Periphery — Discover Highlight and Completed Monitoring.** Discover Highlight's own content (Section 11); both remain visually and positionally de-emphasized relative to Tiers 1–3, per `DB-R-070`.
- **Empty state.** States plainly that nothing has changed since the last visit; a calm, complete state, never framed as missing content, per `DB-R-079` and `DBINV-011`.
- **First-visit state.** States plainly that insufficient prior history exists to compute a meaningful Delta yet, explaining that more will be reported once a prior state exists to compare against, per `DB-R-080`.
- **Partial-data state.** Where one tier's own content is temporarily unavailable, the surface states what is unavailable and why, and continues to show what remains current, mirroring `UX-014` §8's identical treatment for Watchlist.
- **Error and recovery state.** A failure affecting one item or tier SHALL NOT block the entire Brief; the surface states the failure, offers retry, and leaves unaffected content usable.
- **Completion state.** Section 10's Done affordance; reading the full Brief, including a Verdict of "nothing requires attention," is itself a complete, successful session, per `DB-R-078` and `DBINV-011`.

Every tier named above remains subject to Section 12's own boundedness discipline; no tier is exempt from Daily Brief's own finishability requirement, per `DB-R-040`.

## 10. Interaction Model

- **Open.** Expands a Verdict item, change-story item, or routing item's own summary in place, or in a lightweight panel. Open is inspection only — it creates no Investment Case, alters no record, and carries no Product-layer consequence, mirroring `UX-014` §9's identical treatment of Open for Watchlist.
- **Review.** Ordinary-language description of the Investor's own visit to Daily Brief as a whole; it names no formal act and creates no Product-layer record of its own, consistent with `UXD-R-095`'s treatment of Workspace-level session language.
- **Investigate.** The explicit control that transitions the Investor from a Tier 2 or Tier 3 item into the relevant Investment Workspace, per `DB-R-048`. Distinct from Open, exactly as `UX-014` §9 already establishes the same distinction for Watchlist: Investigate is a deliberate further act, never triggered by Open or by any passive interaction.
- **Continue.** Where a Tier 3 item concerns a Decision Context whose state has newly changed, Continue transitions the Investor toward that Decision Context or its Decision Workspace, per `DB-R-049`. Continue never itself performs any part of the underlying reasoning, per `DB-R-004`.
- **Dismiss.** A bounded, session-scoped acknowledgment that a specific Verdict or change-story item has been seen. `APS-008` defines no Product-layer "dismissed" state for an individual item; Dismiss is pure UX-layer presentation, per `UXD-R-022`, carrying no persistence obligation beyond the current view and no effect on the underlying fact, the Delta computation, or the item's own future reappearance if it changes again materially.
- **Done.** A calm, non-blocking acknowledgment that the current visit is finished, available at any point, with no gating condition — reading a Brief that says "nothing new" and selecting Done is itself a complete, successful session, per `DB-R-078`.
- **Return.** Closing a deeper context (Investment Workspace, Decision Workspace, Watchlist, Discover) and arriving back at Daily Brief restores the exact prior scroll position and any Dismiss state from the same visit, per Section 14.
- **View history.** Routes the Investor to the already-governed historical presentation of the relevant record — the Investment Case's own Case History (`UX-005` §17) or a Decision's own Decision Timeline, per `UXD-R-094`'s own disambiguation of historical persistence from "Memory." Daily Brief owns no historical archive of its own past Briefs; `APS-008` `DB-R-073`–`075` explicitly do not require one, and this specification does not introduce one.
- **View evidence.** Routes the Investor into the Investment Workspace's own Evidence & Assumptions presentation (`UX-005` §9); Daily Brief never renders full Evidence content inline, per Section 8's own Evidence presentation rule.
- **View reasoning.** Routes the Investor into the relevant Decision Context's own Investor Reasoning presentation; Daily Brief never renders full Reasoning content inline, per Section 8's own Reasoning visibility rule.

**Explicit distinctions**, restated for clarity because conflating them is this specification's single most consequential failure mode class (Section 23):

- Opening an item (Open) never itself begins investigation, alters a record, or creates an Investment Case.
- Investigating or Continuing are the only acts that transition the Investor toward deeper reasoning surfaces; neither itself performs any Reasoning, records a Judgment, or records a Decision, per `DB-R-052` and `DBINV-005`.
- Viewing history, evidence, or reasoning are read-only routing actions; none of the three edits, creates, or resolves anything on Daily Brief's own behalf.
- Recording a Decision occurs only within the Decision Workspace, per `APS-001` and the existing Decision Workspace specifications (`UX-008`–`UX-011`) — never from within Daily Brief itself, per `DB-R-052` and `DBINV-013`.

## 11. Preview Architecture

Daily Brief participates in bounded previews in both directions, governed here without redefining `APS-006` §13 or `APS-007` §13.

**Daily Brief as host.**

- **Watchlist Update.** A bounded preview of what changed among the Investor's own Watchlist Entries since last visit, reading the state `UX-014`'s own Watchlist exposes for exactly this purpose (`WL-R-037`–`039`). It never replaces the full Watchlist, never independently re-ranks Watchlist's own Entries, and never resolves an Entry on Watchlist's own behalf; it always leads to the full Watchlist (`UX-014`), per `DB-R-059`, `DB-R-061`–`062`, and `WLU-R-025`–`026`. This fulfills, from Daily Brief's own side, exactly the anticipation `UX-014` §13 already recorded.
- **Discover Highlight.** A small, bounded preview of candidates Discover has surfaced, per `DB-R-060`. Because Discover has no UX specification, this section states only Daily Brief's own contract — bounded, non-replacing, leading onward — without defining Discover's own destination screen; authoring that screen is explicitly out of this task's own scope.
- Neither preview is Daily Brief's own sole presentation of the previewed content, per `DB-R-063`; no fact material to understanding either preview's own subject exists only within Daily Brief, per `DB-R-064`.

**Daily Brief as the previewed party.**

- Where Portfolio hosts a bounded preview of Daily Brief, per `DB-R-014` and `DB-R-065`, Daily Brief exposes a summary of its own current Verdict and Delta sufficient for that preview, without requiring Portfolio to re-implement Daily Brief's own filtering, per `DB-R-065`–`066`.
- `UX-007A` and `UX-007P` were checked directly and confirmed to contain no existing Daily-Brief-preview element today. This specification states only what Daily Brief itself must expose for such a preview to exist; extending `UX-007A`/`UX-007P` to add one is explicitly out of this specification's own scope (Section 1), the identical posture `UX-014` §6 already took toward its own Portfolio-hosted preview gap.
- No fact material to understanding Daily Brief's own Verdict exists only within a Portfolio-hosted preview of it; the full, current Daily Brief always remains available in Daily Brief's own area, per `DB-R-067`.

## 12. Repeat Visits, Boundedness, and Completion

- Daily Brief has a definite end on every visit; nothing in its own presentation implies "more below" once the four tiers are exhausted, per `DB-R-072` and `DB-R-089`.
- A fact already presented, unchanged, in a prior visit is not presented again; only a materially new development concerning that same fact warrants re-presentation, per `DB-R-032`, `DB-R-073`, and `DB-R-099`.
- Where nothing has changed since the immediately prior visit, the surface states this plainly; repeated "nothing new" across consecutive visits is accurate, successful reporting, never a defect requiring unrelated content to fill the space, per `DB-R-074` and `DBINV-011`.
- Nothing in Daily Brief's own presentation manufactures urgency, novelty, or engagement pressure to encourage a return visit, per `DB-R-076` and `ATLAS_CONSTITUTION.md`'s own Product Philosophy.
- Completion (Section 10's Done) never requires navigation to any other area first; reading the full Brief and finding nothing further of interest is itself a complete, successful session, per `DB-R-077`–`078`.

## 13. States

Each state below states what the Investor understands, what action is available, how Atlas avoids asserting uncertainty it does not have, and how the Investor recovers or exits.

- **Loading.** Understands the surface is retrieving the current Delta; no action is offered prematurely; skeleton structure resembles the eventual tiered layout, not a generic spinner.
- **Empty.** Understands nothing has changed since the last visit across every tier; a calm, complete state, per `DB-R-079` and `DBINV-011`.
- **No Meaningful Change.** The item-level analog of Empty — a specific tier or item shows no new development; distinct from Empty in scope (whole-Brief versus tier-level), per Section 9.
- **New Meaningful Change.** Understands specifically what changed and why it is connected to something owned, followed, or reasoned about, per Section 7.
- **Previously Reviewed.** Understands an item was already seen in a prior visit and has not materially changed again since; it is not re-presented as though newly significant, per `DB-R-073`.
- **Review Completed.** The whole-session analog of Done (Section 10); understands the current visit is finished.
- **Partial Data.** Understands specifically which tier or item's own signal is unavailable and why; unaffected content remains fully usable, per Section 9.
- **Unavailable Data.** A specific fact (for example, a single Verdict item's own supporting detail) cannot currently be retrieved; stated honestly rather than omitted silently, per `DB-R-047` and `DBF-002`'s own governing principle (absence itself is not the failure; silence about it is).
- **API/Data Error.** Understands a specific, scoped failure with a retry option; the rest of Daily Brief remains usable, per Section 9's error-and-recovery treatment.
- **Repeated Visit.** The Investor has visited before; the Delta reflects only what changed since that specific prior visit, per Section 12.
- **First Visit.** No meaningful prior state exists to compare against yet; stated plainly, per `DB-R-080`, never presented as a broken empty page.
- **Established Investor.** Many owned positions, Watchlist Entries, and open Decision Contexts; scaled by filtering and boundedness alone, never by presenting every changed fact with equal prominence, per `DB-R-083`.
- **Multi-Portfolio Future Compatibility.** This specification assumes exactly one Portfolio, one Watchlist, and therefore one Daily Brief per Investor, per `DB-R-085`; a future multi-portfolio-scoped Daily Brief is not asserted unsupportable, only undefined here, per `DB-R-086`. No state in this section presumes multi-portfolio scoping exists today.

## 14. Navigation

- Daily Brief sits as a primary destination alongside Portfolio, Watchlist, and Discover, consistent with `UX-012A` §1's own list of Atlas surfaces and `UX-014` §15's identical treatment.
- Contextual return paths: closing an Investment Workspace, Decision Workspace, the full Watchlist, or Discover, reached via Section 10's Investigate, Continue, or preview links, returns the Investor to the exact prior Daily Brief scroll position and Dismiss state, per Section 10's own Return definition.
- Transition to the Investment Workspace occurs via Investigate or View evidence/reasoning routing (Section 10).
- Transition to the Decision Workspace occurs only from within an Investment Workspace or Decision Context that already exists — never directly from Daily Brief itself, per `DB-R-052` and `DBINV-013`.
- Transition to the full Watchlist or to Discover occurs via their own respective preview links (Section 11), never bypassed by an inline expansion of their own full content within Daily Brief.
- No dead ends: every state in Section 13 offers at least one way forward (an action, a Return path, or Done).

## 15. Accessibility

Governed directly by `UX-000` §19 (`UXD-R-091`–`092`); this specification states Daily Brief's own application of that standing requirement.

- Reading order follows Section 8's own tiered hierarchy — Verdict, then change story, then routing, then periphery — predictably for assistive technology.
- Every interaction verb in Section 10 (Open, Review, Investigate, Continue, Dismiss, Done, Return, View history, View evidence, View reasoning) is reachable and operable by keyboard alone.
- Priority and state (Section 8, Section 13) are never communicated by color alone; each carries a text label.
- Action labels are explicit and verb-first ("Investigate," "Continue," "Dismiss"), never ambiguous icons alone.
- An empty Verdict or empty Delta is announced clearly to assistive technology, not conveyed by visual absence alone, per `DB-R-079` and `DBINV-011`.
- Every Atlas-originated note (a Verdict item's own framing, a Thesis-Impacting Change's own disclosure) carries explicit, programmatically associated attribution, per `UXD-R-054`.
- Focus returns to a predictable, stable location after Dismiss or after returning from a deeper context, mirroring `UX-005` §23's own "Focus restored after closing" requirement and `UX-014` §16's identical treatment.

## 16. Responsive Behavior

Stated architecturally, without pixel values, per Section 3's own non-scope.

- What remains immediately visible at any viewport: the Verdict block (Section 9) — the minimum needed to answer "what has changed" without opening anything.
- What may collapse under narrower viewports: Tier 3 and Tier 4 content behind an expansion control, consistent with `UX-007A` §27's and `UX-014` §17's own narrow-layout discipline.
- What must never disappear: the Verdict block and each Tier 2 item's own next action — collapsing either would silently violate `UXD-R-092`.
- Primary actions (Investigate, Continue) remain reachable by touch or keyboard at every viewport, never demoted behind a hover-only affordance, per `UX-007A` §26's own "no essential interaction may depend on pointer hover" rule.
- Attribution and connection context (what an item traces to) remain understandable at narrow widths through the same text-label discipline Section 15 requires generally.

## 17. AI Attribution and Investor Ownership

- Every Atlas-originated Verdict item, change-story item, or Thesis-Impacting Change disclosure carries visible, third-person attribution, per `UXD-R-054`, `UXD-R-057`, and PP-008 — never first-person belief framing ("I believe," "I have decided").
- The Investor remains responsible for deciding whether a Verdict item warrants action; Daily Brief surfaces the item, never the decision, per `DB-R-103` and PP-003.
- The Investor remains responsible for interpreting a Thesis-Impacting Change; Daily Brief discloses the connection, never the conclusion, per `DB-R-057` and `DB-R-104`.
- The Investor remains accountable for any Decision reached after navigating from Daily Brief into a Decision Context, in the same manner `APP-000` §8.2 states generally, per `DB-R-105`.
- No UI element within Daily Brief implies that Atlas has exercised Investor Judgment, formed a conclusion, or made a decision on the Investor's own behalf, per `ADR-003` and `UXD-R-036`.

## 18. Explicit UX Exclusions

Each boundary below states the UX consequence of a distinction `APS-008` already draws at the Product layer.

- **Not Portfolio.** Daily Brief's screen architecture (Section 9) never includes a Health grid, Diversification breakdown, or any current-state snapshot content; Portfolio answers "where do I stand," Daily Brief answers "what changed," per `DB-R-090` and `DBINV-002`.
- **Not Discover.** Daily Brief never inlines a browse or search interface; its own Discover content is a small, bounded pointer, per `DB-R-091` and `DBINV-003`.
- **Not Watchlist.** Daily Brief never lets the Investor browse or edit the full Watchlist directly; its own Watchlist content is a bounded update preview, per `DB-R-092` and `DBINV-004`.
- **Not Investment Workspace.** Daily Brief never inlines full thesis, valuation, or key-driver content; Open (Section 10) shows only Section 8's bounded hierarchy, and deeper content is reached only by transitioning into the Investment Workspace itself.
- **Not Decision Workspace.** Daily Brief never offers a Record Decision action, a Proposed Decision field, or any Decision Workspace content directly, per `DB-R-052` and `DBINV-013`.
- **Not a news feed.** A macro or market-level fact enters Daily Brief only through the lens of a specific owned position or followed Entry it affects, per `DB-R-033` and `DB-R-088`/`094`, never as an independent market update.
- **Not a monitoring dashboard.** Completed Monitoring, once it exists, is quiet, Tier-4 confirmation of coverage, never a live telemetry or status display, per `DB-R-070`.
- **Not an inbox.** Daily Brief compresses, prioritizes, and narrates the Delta into meaning; it is never a raw, unranked, chronological log of every event that fired, per `DB-R-095`.
- **Not a notification center.** Daily Brief's own content MAY later be delivered through Notifications, but Daily Brief itself is never merely a log of what Notifications have sent, per `DB-R-095`.

## 19. Atlas Responsibilities

- Atlas SHALL present the Delta computed per `APS-008` §5 without independently altering, expanding, or suppressing it beyond the relevance filtering `APS-008` §9 already governs, per `DB-R-096`–`097`.
- Atlas SHALL populate the Verdict from the Atlas Priority Model, never from an independently computed ranking, per `DB-R-098`.
- Atlas SHALL NOT re-present a materially unchanged fact across visits, per `DB-R-099`.
- Atlas SHALL disclose an empty Delta, an empty Verdict, or an empty Completed Monitoring category explicitly, per `DB-R-100`.
- Atlas SHALL attribute the origin of any Atlas-originated content Daily Brief presents, per `DB-R-102` and PP-008.
- Atlas SHALL preserve the read-only boundary Section 6 states in every presentation choice Daily Brief's own UI makes; no interaction defined in Section 10 SHALL alter a Core Domain Object or an already-accepted Product record, per `DB-R-010` and `DB-R-101`.

## 20. Investor Responsibilities

- The Investor is responsible for engaging with the Verdict and change story Daily Brief presents, rather than treating either as a decision already made on their behalf, per PP-003.
- The Investor decides whether, and when, to Investigate or Continue into deeper reasoning; Daily Brief never requires this within the current visit, per `DB-R-103`.
- The Investor remains accountable for any Decision reached after leaving Daily Brief for a Decision Context, in the same manner every other Atlas surface already establishes, per `DB-R-105`.

## 21. Requirements

Normative UX requirements for Daily Brief, using the `DBU-R-` prefix — chosen to avoid colliding with `APS-008`'s own `DB-R-` (Product) prefix and `UX-000`'s own `UXD-R-` (Doctrine) prefix, following the identical disambiguation discipline `UX-014` already established with `WLU-R-`, per `UXD-R-096`.

**Purpose comprehension**

**DBU-R-001.** The Daily Brief surface SHALL communicate its own governing question — "What has changed since I last looked?" — before any item-level detail, per Section 9 and `UXP-001`.

**DBU-R-002.** No screen state SHALL imply that Daily Brief is a destination for owned-position review, a browse/search surface, or a raw event log, per Section 5 and Section 18.

**Meaningful change and relevance**

**DBU-R-003.** Every item presented SHALL display, or make reachable, the specific connection (owned position, followed Entry, or Investment Case) that qualifies it for inclusion, per `DB-R-026`.

**DBU-R-004.** No UI element SHALL imply completeness; framing SHALL communicate relevance-over-completeness honestly, per `DB-R-027`.

**Information hierarchy**

**DBU-R-005.** The Verdict block SHALL be presented first and SHALL remain visible without scrolling on first view, per `DB-R-034` and `UXP-001`.

**DBU-R-006.** No tier defined in Section 8 SHALL be presented with greater visual weight than its own tier number implies is warranted, per `DB-R-038`.

**DBU-R-007.** Where the Verdict and Portfolio's own Requires Attention category present the same underlying item, the UI SHALL NOT present them as disagreeing about the fact itself, per `DB-R-044`.

**Verdict and priority**

**DBU-R-008.** No independent ranking mechanism SHALL be introduced anywhere in Daily Brief's own governed UI; every priority signal SHALL be traceable to the Atlas Priority Model, per `DB-R-043` and `DBINV-006`.

**DBU-R-009.** An empty Verdict SHALL be presented as a calm, complete state; no UI mechanism SHALL fabricate a Verdict item to avoid appearing empty, per `DB-R-047`.

**Change and evidence presentation**

**DBU-R-010.** A Thesis-Impacting Change SHALL be presented as a disclosed connection only, never as an assertion that prior Reasoning was wrong or that a specific response is required, per `DB-R-057`.

**DBU-R-011.** No UI SHALL present a Thesis-Impacting Change with no traceable derivation from new Evidence or a new Observation, per `DB-R-058`.

**DBU-R-012.** No full Evidence or Investor Reasoning content SHALL be rendered inline within Daily Brief; View evidence and View reasoning (Section 10) SHALL route to the Investment Workspace or Decision Context instead.

**DBU-R-013.** Any Atlas-originated note attached to a Verdict item or change-story item SHALL carry visible, third-person attribution, per `UXD-R-054`, `UXD-R-057`, and PP-008.

**Interaction**

**DBU-R-014.** Open SHALL produce no Product-layer effect; it SHALL only reveal already-known item-level information, per Section 10.

**DBU-R-015.** Investigate and Continue SHALL each be controls visually and semantically distinct from Open, reachable only through deliberate selection.

**DBU-R-016.** Dismiss SHALL persist no data beyond the current session/view and SHALL NOT be presented, coded, or described as deletion or resolution of the underlying fact.

**DBU-R-017.** No UI path SHALL offer direct entry into a Decision Context or Decision Workspace from Daily Brief; that transition SHALL be available only from within an Investment Workspace or existing Decision Context, per `DB-R-052`.

**Previews**

**DBU-R-018.** The Watchlist Update preview SHALL remain bounded, SHALL NOT independently re-rank Watchlist's own Entries, and SHALL always lead to the full Watchlist (`UX-014`), per `DB-R-059`, `DB-R-061`–`062`.

**DBU-R-019.** The Discover Highlight preview SHALL remain bounded and SHALL NOT be expanded into a browse or search interface within Daily Brief, per `DB-R-060` and `DBINV-003`.

**DBU-R-020.** No fact required to understand a previewed item SHALL be presented only within a Daily-Brief-hosted preview and nowhere within the previewed area's own destination, per `DB-R-064`.

**DBU-R-021.** Any Daily Brief content hosted within Portfolio SHALL remain bounded, SHALL NOT independently re-rank Daily Brief's own Verdict or Delta, and SHALL always lead to the full Daily Brief, per `DB-R-065`–`067`.

**Repeat visits and boundedness**

**DBU-R-022.** No fact already presented, unchanged, in a prior visit SHALL be presented again as though newly significant, per `DB-R-073` and `DB-R-099`.

**DBU-R-023.** No UI mechanism SHALL create the sensation of "more below" once Section 8's four tiers are exhausted, per `DB-R-072` and `DB-R-089`.

**DBU-R-024.** No UI mechanism SHALL manufacture urgency, novelty, or engagement pressure to encourage a return visit, per `DB-R-076`.

**State behavior**

**DBU-R-025.** Every state named in Section 13 SHALL be implemented; no unnamed or ambiguous intermediate state SHALL be presented to the Investor without explanation.

**DBU-R-026.** A failure affecting one tier or item's own data SHALL NOT block or degrade the rest of the Daily Brief surface, per Section 9's error-and-recovery treatment.

**DBU-R-027.** An empty Delta, empty Verdict, or first-visit state SHALL be stated explicitly, never presented as a silent or ambiguous blank surface, per `DB-R-079`–`080` and `DBINV-011`.

**Navigation**

**DBU-R-028.** Returning from a deeper context (Investment Workspace, Decision Context, Watchlist, Discover) SHALL restore the Investor's own prior Daily Brief scroll position and Dismiss state, per Section 14.

**DBU-R-029.** No state defined in Section 13 SHALL leave the Investor without at least one available forward action, return path, or Done affordance.

**Accessibility**

**DBU-R-030.** Every interaction verb in Section 10 SHALL be operable by keyboard alone, per `UXD-R-092`.

**DBU-R-031.** No state, priority signal, or tier distinction SHALL be communicated by color alone; a text label SHALL always accompany it, per `UXD-R-092`.

**DBU-R-032.** Focus SHALL return to a predictable location after Dismiss or after returning from a deeper context, per Section 15.

**Responsive preservation**

**DBU-R-033.** At every viewport, the Verdict block SHALL remain immediately visible, per Section 16.

**DBU-R-034.** No primary action (Investigate, Continue) SHALL be demoted to a hover-only affordance at any viewport, per Section 16.

**Error prevention**

**DBU-R-035.** No UI mechanism SHALL allow Daily Brief to compute or display a ranking independent of the Atlas Priority Model, per `DB-R-043` and `DBU-R-008`.

**DBU-R-036.** No UI mechanism SHALL allow a Decision Context to be created, closed, or reopened from within Daily Brief without an identifiable Investor act performed elsewhere, per `DBINV-013`.

**Completion behavior**

**DBU-R-037.** A Done affordance SHALL be available at any time the Investor is viewing Daily Brief, with no gating condition, per `DB-R-078`.

**DBU-R-038.** No completion action SHALL require the Investor to reach a specific item count, a "zero attention items" state, or any other artificial threshold before Done becomes available.

**Product and UX traceability**

**DBU-R-039.** Every requirement in this section SHALL be traceable, by citation, to at least one of: `ATLAS_CONSTITUTION.md`, an `APP-000` Product Principle, an `APS-008` provision, an `APS-006` provision, an `APS-007` provision, or a `UX-000` `UXD-R-` rule, per Section 25.

## 22. Invariants

**DBU-INV-001 — Daily Brief always represents genuine, connected change.** No item presented by this specification's own UI SHALL originate from anything other than the Delta computation filtered per `DB-R-026`, or the Atlas Priority Model's own already-governed computation, per `DBINV-010`.

**DBU-INV-002 — Daily Brief never performs Reasoning.** No UI element SHALL invite the Investor to construct or record Reasoning within the Daily Brief surface itself, per `DBINV-005`.

**DBU-INV-003 — Daily Brief never records a Decision.** No UI element within Daily Brief SHALL present a Record Decision, Proposed Decision, or equivalent control, per `DBINV-013`.

**DBU-INV-004 — Daily Brief never becomes Portfolio, Discover, or Watchlist.** No screen state SHALL present a current-state snapshot, a browse/search interface, or full Watchlist editing capability, per `DBINV-002`–`004`.

**DBU-INV-005 — Priority remains one scoped view of the Atlas Priority Model.** No independent ranking mechanism SHALL exist anywhere in this specification's own governed UI, per `DBINV-006`.

**DBU-INV-006 — Every Atlas-originated rationale remains visibly attributable.** No Atlas-originated note SHALL be presented without attribution, per `UXD-R-054` and PP-008.

**DBU-INV-007 — Previews are never destinations.** Every bounded preview Daily Brief hosts, or is itself hosted within, SHALL always lead to its own full destination, per `DBINV-008`.

**DBU-INV-008 — Daily Brief remains bounded and finishable.** No UI mechanism SHALL authorize unbounded, continuously-scrolling, or engagement-optimized content, per `DBINV-009`.

**DBU-INV-009 — Honest absence is success.** An empty Verdict, an empty Delta, or a repeated "nothing new" across consecutive visits SHALL be presented as accurate, successful reporting, per `DBINV-011`.

**DBU-INV-010 — The user can always distinguish opening from investigating.** Open, Investigate, and Continue SHALL remain three visually and behaviorally distinct actions at every point in this specification, per `DBU-R-015`.

**DBU-INV-011 — The user can always leave the screen with a clear completion state.** A Done affordance, per Section 10, SHALL be reachable from every state Section 13 defines.

## 23. Failure Modes

Atlas SHALL fail closed: where continuing would require this specification, `APS-008`, `APS-006`, `APS-007`, or `UX-000` to be violated, the interface SHALL present an honest, bounded state rather than proceed on a fabricated or inferred basis. No specific error copy is prescribed here.

**DBU-F-001 — Everything looks urgent.** Presenting Tier 2 through Tier 4 content with Tier 1's own urgency violates `DB-R-034`, `DB-R-037`, and `DBU-R-006`, and degrades the Investor's ability to answer "does anything require attention."

**DBU-F-002 — Nothing looks important.** Presenting a genuine Verdict item without adequate visual priority, such that it is indistinguishable from periphery content, violates `DB-R-034` and `DBU-R-005` equally in the opposite direction.

**DBU-F-003 — Daily Brief becomes Portfolio.** Presenting current-state, non-delta content as though it belonged in Daily Brief violates `DBINV-002` and `DB-R-090`.

**DBU-F-004 — Daily Brief becomes Discover.** Expanding the Discover Highlight preview beyond a bounded pointer violates `DBINV-003` and `DB-R-091`.

**DBU-F-005 — Daily Brief becomes a monitoring dashboard.** Presenting Completed Monitoring with live-telemetry framing or Tier-1 urgency violates `DB-R-070` and Section 18.

**DBU-F-006 — Noise overwhelms meaning.** Including an item that fails `DB-R-026`'s own connection requirement, or presenting the full Delta unfiltered, violates `DBINV-010` and `DBU-R-003`.

**DBU-F-007 — Changes repeat forever.** Re-presenting a materially unchanged fact across visits as though newly significant violates `DB-R-073`, `DB-R-099`, and `DBU-R-022`.

**DBU-F-008 — No explanation exists.** Presenting a Verdict item or Thesis-Impacting Change with no traceable connection or derivation violates `DB-R-058` and `DBU-R-011`.

**DBU-F-009 — AI ownership implied.** Any copy, iconography, or flow implying that Atlas has exercised Investor Judgment or reached a conclusion on the Investor's own behalf violates `DBINV-005`, `DB-R-045`, and PP-003.

**DBU-F-010 — Investor ownership hidden.** Omitting attribution from an Atlas-originated Verdict item or Thesis-Impacting Change violates `DBU-INV-006` and `UXD-R-054`.

**DBU-F-011 — Priority disagreement.** Presenting the Verdict and Portfolio's own Requires Attention category as reaching different conclusions about the same underlying item violates `DB-R-044` and `DBU-R-007`.

**DBU-F-012 — Unclear completion.** Omitting a reachable Done affordance from any state in Section 13, or requiring an artificial threshold before it becomes available, violates `DBU-INV-011` and `DBU-R-037`–`038`.

## 24. Acceptance Criteria

**DBU-AC-001 (Purpose immediately understood).** A new Investor is observed to understand, from the Verdict block alone, that Daily Brief answers "what has changed since I last looked," per Section 5 and `DBU-R-001`.

**DBU-AC-002 (Meaningful change visible).** Every item presented is observed traceable to a connection under `DB-R-026`; no unconnected fact is ever observed present, per `DBU-R-003`.

**DBU-AC-003 (Urgency justified).** No tier is ever observed presented with visual weight inconsistent with its own tier number, per `DBU-R-006`, and no genuine Verdict item is ever observed under-emphasized relative to periphery content.

**DBU-AC-004 (No duplication with Portfolio).** No current-state snapshot content is ever observed within Daily Brief, per `DBU-INV-004`.

**DBU-AC-005 (No duplication with Discover).** No browse or search interface is ever observed within Daily Brief; only the bounded Discover Highlight preview is observed, per `DBU-R-019`.

**DBU-AC-006 (No duplication with Watchlist).** No full Watchlist Entry list or editing capability is ever observed within Daily Brief; only the bounded Watchlist Update preview is observed, per `DBU-R-018`.

**DBU-AC-007 (AI attribution visible).** Every Atlas-originated note is observed to carry visible, third-person attribution, per `DBU-R-013` and `DBU-INV-006`.

**DBU-AC-008 (Investor ownership preserved).** No observed interaction implies that Atlas has made a decision on the Investor's own behalf; every transition into deeper reasoning is observed to require a deliberate Investigate or Continue act, per `DBU-INV-010`.

**DBU-AC-009 (Priority consistent).** No independently computed ranking is ever observed within Daily Brief's own content, and the Verdict is never observed disagreeing with Portfolio's own Requires Attention category about the same underlying fact, per `DBU-R-007`–`008`.

**DBU-AC-010 (Repeat visits behave correctly).** No materially unchanged fact is ever observed re-presented across consecutive visits as though newly significant, per `DBU-R-022`.

**DBU-AC-011 (States are complete).** Every state named in Section 13 is observed to be reachable and to offer at least one forward action or exit, per `DBU-R-025` and `DBU-R-029`.

**DBU-AC-012 (No Core or Product redesign required).** No acceptance check above is found to require a new Core Domain Object, a new Core invariant, a change to `APS-008`'s own normative behavior, or a change to any other Product Architecture document, per `DB-AC-006`.

## 25. Traceability

| Section | Normative UX basis | Normative Product basis | Core basis |
|---|---|---|---|
| §5 UX Definition | `UX-000` §5, §24 (`UXP-001`); `UXD-R-071` | `APP-000` PP-004; `APS-008` §2, §21 | — |
| §6 Relationships | `UX-000` `UXD-R-008` | `DB-R-014`–`025` | `OE-002` §3.1 Case (via Investment Case) |
| §7 Meaningful Change | `UX-000` §12 | `DB-R-026`–`033` | — |
| §8 Information Hierarchy | `UX-000` §12–14, §20 | `DB-R-034`–`058` | — |
| §9 Screen Architecture | `UX-000` `UXD-R-071` (Conclusion boundary) | `DB-R-012`, `DB-R-034`–`041`, `DB-R-079`–`080` | — |
| §10 Interaction Model | `UX-000` §7 (`UXD-R-011`) | `DB-R-048`–`053`, `DB-R-004` | — |
| §11 Preview Architecture | `UX-000`'s own preview governance (adopted, not itself defining it) | `APS-006` §13 (`PF-R-051`–`055`); `APS-007` §13 (`WL-R-037`–`039`); `DB-R-059`–`067` | — |
| §12 Repeat Visits/Boundedness | `UX-000` `UXD-R-059`–`060` | `DB-R-072`–`078` | — |
| §13 States | `UX-000` §19 (`UXD-R-091`–`092`) | `DB-R-079`–`086`, `DB-F-001`–`010` | — |
| §14 Navigation | `UX-005` §20–§22; `UX-007A` §25; `UX-014` §15 | — | — |
| §15 Accessibility | `UX-000` §19; `ADR-002` C-06 | — | — |
| §16 Responsive Behavior | `UX-007A` §26–§27; `UX-014` §17 | — | — |
| §17 AI Attribution/Ownership | `UX-000` §10–11 (`UXD-R-048`–`057`) | `DB-R-102`–`105`, PP-003, PP-008 | — |
| §18 Explicit UX Exclusions | `UX-000` §8 (`UXD-R-020`–`039`) | `DB-R-087`–`095`, `DBINV-002`–`004` | — |
| §21–24 Requirements/Invariants/Failure Modes/Acceptance | `UX-000`, throughout, per each citation | `APS-008`, throughout, per each citation | `OE-002` §4 (via `DBINV-001`/`DBINV-014`) |

No temporary report (the UX Correspondence Investigation, the UX Governance Resolution Sprint's own deliverable text, or the UX Architecture Layer Investigation) is cited above as a governing repository authority; each is a completed session finding already absorbed into the committed documents this table cites directly.

## 26. Open Questions and Deferred Work

- **Relevance threshold tuning.** `APS-008` §9 defines what qualifies, not how qualification is computed. Classified: **non-blocking** — any UI presenting a genuinely qualified item correctly satisfies this specification; the computation itself is implementation and calibration work outside this document's own scope.
- **Repeat-visit detection mechanics.** Section 12 states the governing principle; the exact mechanism for detecting "materially unchanged" across visits is not defined here, mirroring `APS-008` §28's own identical deferral. Classified: **non-blocking**, implementation-level.
- **Completed Monitoring's eventual UX detail.** Section 8 and Section 9 state Completed Monitoring's own Tier-4 placement and non-urgent framing, but Monitoring itself has no governing Product Architecture specification yet, per `DB-R-069`. Classified: **out of scope** until Monitoring is specified.
- **Discover Highlight's own destination screen.** Section 11 states only Daily Brief's own hosting contract; Discover's own UX has no governing specification. Classified: **out of scope**, explicitly excluded by this task's own constraint.
- **Multi-Portfolio-scoped Daily Brief.** Coupled to Portfolio's and Watchlist's own identical open questions (`APS-006` §24, `APS-007` §24, `UX-014` §24). Classified: **requires separate architecture work**, non-blocking for this specification's own completeness.
- **Whether "Thesis-Impacting Change" requires later formal Product Concept treatment.** Genuinely open, mirroring `APS-008` §28's own framing and the identical questions `APS-006` §24 and `APS-007` §24 carry for "Holding" and "Watchlist Entry." Classified: **deferred** — a future Product Architecture decision this specification has no authority to make.
- **Notification integration's eventual UX.** `APS-008` §8 records this as future-facing; no Notification UX exists anywhere yet. Classified: **out of scope**.

None of the above is decided by implication anywhere in this document.

---

*This specification does not modify `ATLAS_CONSTITUTION.md`, `Architecture-Governance.md`, `APP-000`, `APP-001`, any `APS` document, `UX-000`, `UX-014`, or any other existing UX document. It introduces no new Core Domain Object, no new Product Concept, and requires no Core, Product Architecture, or implementation redesign.*
