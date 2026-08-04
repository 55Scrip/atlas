# UX-016 — Discover Experience Specification

**Status:** Draft, v0.1. This is the third new operational UX specification authored after the completed Product Architecture Reconciliation, `APP-001` v0.4, `APS-006` through `APS-009`, the UX Correspondence Investigation, the UX Governance Resolution Sprint, `UX-014` (Watchlist), and `UX-015` (Daily Brief). It states the complete governing UX contract for Discover: mental model, relationships, the Thread relevance model, information hierarchy, screen architecture, interaction, progression, preview participation, states, navigation, accessibility, and responsive behavior. It does not redefine Discover's own Product semantics, which remain governed exclusively by `APS-009`; it does not specify visual tokens, pixel dimensions, implementation technology, algorithms, or persistence mechanisms.

---

## 1. Governance Metadata

Stated here in full, per `Architecture-Governance.md` §10's own requirement, following the pattern `UX-014` §1 and `UX-015` §1 already established for this authoring lineage.

- **Document identifier:** UX-016.
- **Title:** Discover Experience Specification.
- **Version:** v0.1.
- **Status:** Draft — the smallest truthful status available to a newly authored specification. This document has not undergone Internal Consistency Review, Targeted Consistency Correction, or Final Verification; it is not Release Candidate and not Final.
- **Parent authority:** `UX-000-Atlas-UX-Doctrine.md` (Release Candidate RC v1.0) — the highest governing document within the Atlas UX Architecture; this specification SHALL NOT contradict it, redefine a term it defines, or exceed the authority its own §7 (UX Responsibilities) and §8 (UX Prohibitions) grant.
- **Product authority:** `APP-000` — Atlas Product Doctrine (Draft v0.4); `APP-001` — Atlas Product Concept Taxonomy (Draft v0.4), §4 (Discover's newly-recorded deferral) and §9 item 10; `APS-009` — Discover (Draft v0.1), the primary Product-layer authority this specification translates into a UX contract; `APS-006` — Portfolio (Draft v0.1), for the Atlas Priority Model (§10) and Bounded Preview Governance (§13) this specification adopts by reference; `APS-007` — Watchlist (Draft v0.1), for the Follow/progression discipline Discover reuses; `APS-008` — Daily Brief (Draft v0.1), for the Discover Highlight preview relationship Daily Brief already governs from its own hosting side; `APS-001` — Decision Context (Draft v0.1), for the boundary this specification must never cross.
- **Dependencies:** `UX-014-Watchlist-Experience-Specification.md`, for the Follow interaction's own governing UX contract once a Follow act occurs, and for the authoring style, rigor, and rule-prefix convention this specification follows. `UX-015-Daily-Brief-Experience-Specification.md`, for the Discover Highlight preview's own hosting side, which this specification's own Section 13 fulfills from Discover's side. `UX-004`/`UX-005` — Investment Workspace, for the destination a Candidate's progression opens. `UX-007A`/`UX-007P` — Portfolio Workspace, for the entry point Portfolio surfaces toward Discover. `UX-000-Atlas-UX-Doctrine.md`, for every doctrine-level rule cited throughout. `ADR-002-Critical-UX-Architecture-Resolutions.md` (C-01 information hierarchy, C-06 unavailable-state accessibility) and `ADR-003-Recommendation-Identity-and-Terminology-Resolution.md` (Atlas Recommendation / Proposed Decision Candidate Content boundary), adopted here unchanged.
- **Scope:** Discover's own UX mental model; relationship to Portfolio, Watchlist, Daily Brief, Investment Workspace, Decision Workspace, Investment Case, Decision Context, and the Atlas Priority Model; the Thread relevance model; Themes, AI Opportunities, and Valuation Opportunities as UX-layer presentation; Ignored Noise as an opt-in view; information hierarchy; candidate, priority, connection, evidence, and reasoning presentation; uncertainty visibility; the two progression paths (into Watchlist and directly into Investment Case); Discover's own role as the previewed party within Daily Brief; interaction model; repeat-visit and completion behavior; states; navigation; accessibility; responsive behavior at the architectural level; AI attribution; Investor ownership; explicit UX exclusions.
- **Non-scope:** Any Product semantics `APS-009` already governs (this specification translates, never restates as though it were the authority); visual token values; pixel dimensions; typography; color; animation timing; implementation technology; algorithms; candidate-sourcing, ranking, or relevance-computation methodology; data schemas; persistence mechanisms; Monitoring's, Signals', Themes', or AI's own complete future UX behavior, none yet specified anywhere beyond the bounded principle `APS-009` §8 already states; any amendment to `APP-000`, `APP-001`, any `APS`, `UX-000`, or any existing UX specification.
- **Affected documents:** None requiring amendment. This specification does not modify `UX-014`, `UX-015`, `UX-007A`, `UX-007P`, `UX-012A`, `UX-012B`, `UX-012C`, or any other existing UX document; a future, separately-authorized task may choose to add a literal Discover-entry-point element to `UX-007A`/`UX-007P` or a fuller Discover Highlight card to `UX-015`, but that is not performed or required here.
- **Superseded documents:** None. No dedicated Discover UX specification has ever existed in this repository, and — confirmed by direct corpus-wide search — no existing UX document mentions Discover at all prior to `UX-014` and `UX-015`'s own recent, passing references to it as a neighboring surface.
- **Migration requirements:** None. No existing UX document or implementation is required to change as a consequence of this document's creation. This document completes the three-specification UX expansion (Watchlist, Daily Brief, Discover) mirroring the four-specification Product Architecture expansion `APS-009` itself completed.

## 2. Purpose

Discover requires its own UX specification because `APS-009` states Discover's complete Product-layer behavior but explicitly excludes screens, workflows, navigation, visual design, and interaction design from its own scope (`APS-009` §3). This specification closes that gap: it translates `APS-009`'s normative requirements into a complete, implementable UX contract, following the same method and rigor `UX-014` and `UX-015` already applied to `APS-007` and `APS-008`, so that a future visual design artifact, an implementation, engineering, QA, or any AI agent working on Atlas can build the Discover experience without inventing new UX rules — or new Product rules — of their own.

Discover's own central user question, unchanged from `APS-009` §2, governs every decision in this document: **"What should I investigate next?"** — distinct from Portfolio's "where do I stand" (`UX-007A`/`UX-007P`), Watchlist's "what should I continue following" (`UX-014`), and Daily Brief's "what has changed since I last looked" (`UX-015`). Discover is the only one of the four surfaces whose content is not bounded to what the Investor already owns, follows, or has reasoned about, per `DS-R-013`.

## 3. Scope and Non-Scope

Restated from Section 1 for direct reference: in scope is everything a human perceives or does when using Discover — mental model, relationships, the Thread relevance model, hierarchy, screens, interaction, progression, preview participation, states, navigation, accessibility, responsive behavior — tested against `UX-000` `UXD-R-008`'s own scope discipline: a statement belongs here only if it concerns perception or action, would remain true regardless of the specific screen, framework, or visual design used to express it, and would change if `APS-009`'s own normative behavior changed.

Out of scope, per `UX-000` §3 and `APS-009` §3: any Product semantics, visual tokens, pixel dimensions, implementation technology, algorithms, candidate-sourcing or ranking computation, data schemas, or persistence mechanisms. Also out of scope: Monitoring's, Signals', Themes', and AI's own complete future behavior, none yet specified beyond `APS-009` §8's own bounded principle; any change to `UX-014`, `UX-015`, `UX-007A`, `UX-007P`, `UX-012A`, `UX-012B`, or `UX-012C`.

## 4. Governing References

- **`ATLAS_CONSTITUTION.md`.** Normative, superior to every document in the Atlas Product and UX Architecture. The Product Philosophy's own rejection of "urgency as a product mechanic" and the Non-Negotiable Principle "Atlas never encourages unnecessary trading" ground this specification's own insistence that Discover remain calm, opinionated-but-honest, and never manufacture urgency (Section 5).
- **`Architecture-Governance.md`.** Normative, governs this document's own governance-metadata discipline (§10) and document-status discipline.
- **`APP-000` — Atlas Product Doctrine, Draft v0.4.** Normative Product. PP-001 (Attention Before Information), PP-003 (AI Supports, Never Replaces, Investor Judgment), PP-004 (Progressive Disclosure), PP-005 (Human Ownership), PP-007 (Uncertainty Disclosed, Not Concealed), PP-008 (Provenance) ground this specification throughout, cited by identifier at each point of use.
- **`APP-001` — Atlas Product Concept Taxonomy, Draft v0.4.** Normative Product. §4 governs Discover's own status as newly-recorded deferred territory, not an independent Product Concept; §3.13 (Investment Case) governs the destination Discover routes into.
- **`APS-009` — Discover, Draft v0.1.** Normative Product, the primary authority this specification translates. Every `DS-R-`, `DSINV-`, `DS-F-`, and `DS-AC-` identifier cited below refers to this document.
- **`APS-006` — Portfolio, Draft v0.1.** Normative Product, for the Atlas Priority Model (§10, `PF-R-031`–`035`) this specification adopts by reference, and for the entry point Portfolio already surfaces toward Discover, per `PF-R-020`.
- **`APS-007` — Watchlist, Draft v0.1.** Normative Product, for the Follow act's own governing mechanics once triggered from Discover, per `WL-R-007`, `WL-R-022`.
- **`APS-008` — Daily Brief, Draft v0.1.** Normative Product, for the Discover Highlight preview Daily Brief hosts, per `DB-R-016`, `DB-R-059`–`064`.
- **`APS-001` — Decision Context, Draft v0.1.** Normative Product, for the boundary (`DC-R-017`, `DC-R-021`) this specification's own progression discipline (Section 12) must not cross.
- **`UX-000-Atlas-UX-Doctrine.md`, Release Candidate RC v1.0.** Normative UX, the immediate parent authority for every UX-layer rule in this document.
- **`ADR-002-Critical-UX-Architecture-Resolutions.md`, Accepted.** Normative UX within its own stated scope; C-01 (information hierarchy) and C-06 (`aria-disabled`, never native `disabled`) are cited where Discover's own states require them (Section 14).
- **`ADR-003-Recommendation-Identity-and-Terminology-Resolution.md`, Accepted.** Normative UX within its own stated scope; governs how any Atlas-originated rationale attached to a Candidate must be presented (Section 8, Section 18).
- **`UX-014-Watchlist-Experience-Specification.md`.** Cited for the Follow interaction's own governing contract once a Watchlist Entry is created from Discover, and for the "no [Surface] Conclusion" precedent Section 5 applies here by the identical reasoning.
- **`UX-015-Daily-Brief-Experience-Specification.md`.** Cited for its own Section 11 "Discover Highlight" preview-hosting contract, which this specification's own Section 13 fulfills from Discover's side.
- **`UX-007A-Portfolio-Workspace-Wireframe-Specification.md`, `UX-007P-Portfolio-Workspace-Final-Polish.md`.** Checked directly and confirmed to contain no existing reference to Discover; Section 6 states this specification's own contract for the anticipated Portfolio-hosted entry point without asserting one currently exists.
- **`UX-012A`, `UX-012B`, `UX-012C` — Atlas Design System.** Cited for reusable component, interaction, and accessibility patterns this specification builds on rather than reinvents (Section 15, Section 16).

## 5. UX Definition

Discover is the bounded experience responsible for expanding the Investor's opportunity set beyond what is already owned or intentionally followed. It is not a company profile, not a portfolio snapshot, not a change digest, not a research terminal, and not a general-purpose search or chat surface.

The Discover experience must feel:

- **opinionated but honest** — every Candidate carries a real, statable reason for appearing, per `DS-R-030`; Discover never presents a neutral, exhaustive catalog the way a database or screener would;
- **exploratory, never comprehensive** — content spans from tightly anchored (Portfolio Fit) to genuinely exploratory (Emerging Industries), per Section 8, but every point on that spectrum still requires a real Thread, per Section 7;
- **calm** — no manufactured urgency, no red for red's sake, consistent with `ATLAS_CONSTITUTION.md`'s own rejection of urgency as a product mechanic and `DS-R-067`;
- **non-committal by default** — viewing, dwelling on, or repeatedly encountering a Candidate never itself creates anything, per `DS-R-051`;
- **structured, never conversational** — Candidates are surfaced as categorized, Thread-explained content, never through an open-ended chat interface, per `DS-R-074`.

It must not feel like:

- Portfolio (it operates entirely outside the owned-position set, per `DSINV-002` and `DS-R-070`);
- Watchlist (it is the generative process upstream of Watchlist, never the static storage itself, per `DSINV-003` and `DS-R-071`);
- Daily Brief (it is atemporal and continuously evaluated, never a bounded temporal delta, per `DSINV-004` and `DS-R-072`);
- a news feed (candidates surface via Thread connection, never for general newsworthiness, per `DS-R-075`);
- a stock screener (Discover proactively generates Candidates; it never requires the Investor to specify filter criteria first, per `DS-R-076`);
- an AI chat (it presents structured, categorized Candidates, never an open-ended conversational surface, per `DS-R-074`).

**Deliberate non-decision — no "Discover Conclusion."** `UX-000` `UXD-R-071` recognizes exactly five governed Conclusion variants, each grounded in specific underlying Product-layer content. High Conviction Ideas, Discover's own top-line category, is explicitly *"a scoped view of the Atlas Priority Model... applied to Candidates outside the owned and followed set, never an independently computed ranking"* (`DS-R-045`) — it carries no Reasoning, no Premise, and no Learning Result of its own. This specification therefore deliberately does not introduce a "Discover Conclusion," for the identical reason `UX-014` §5 and `UX-015` §5 already established for Watchlist and Daily Brief: doing so would be a new Conclusion variant `UXD-R-071` does not authorize, and would risk implying Discover has formed a judgment it has not, contrary to `DS-R-048` and `DSINV-005`. Section 9's own "High Conviction Ideas" presentation is a scoped, factual view of Priority Model output, never a Conclusion in the doctrine's governed sense.

## 6. Relationship to Neighboring Surfaces and Concepts

Each relationship below translates `APS-009` §8's own classification into its UX consequence; none is redefined here.

- **Portfolio.** Existing and product-level (`DS-R-014`). Discover may read Portfolio's own owned-position data to compute Portfolio Fit relevance, but never writes to Portfolio. Portfolio surfaces an entry point toward Discover without embedding it — Discover remains the destination, never a preview hosted within Portfolio.
- **Watchlist.** Existing and product-level (`DS-R-016`). Discover may read Watchlist's own state to compute Watchlist Candidates relevance; it is Watchlist's own most common upstream source, but every resulting Entry still requires its own explicit Follow act, governed by `UX-014`. Section 12 governs this from Discover's own side.
- **Daily Brief.** Existing and product-level (`DS-R-015`). Daily Brief hosts a bounded Discover Highlight preview, reading state Discover exposes for exactly this purpose. Discover is the previewed party in this relationship — the only one of the three surfaces that is never itself a host. Section 13 governs this from Discover's own side.
- **Investment Workspace / Investment Case.** Existing and product-level (`DS-R-017`). A Candidate may progress into an Investment Case, directly or via an intermediate Watchlist Entry, but never automatically. Section 12 governs the routing path.
- **Decision Workspace / Decision Context.** Not applicable (`DS-R-018`). Discover never creates, holds, or references a Decision Context; that relationship begins only once a Candidate has progressed into an Investment Case and genuine Reasoning has begun within it.
- **Atlas Priority Model.** Derived and product-level (`DS-R-022`). High Conviction Ideas is a scoped view of this one shared model, applied to Candidates outside the owned and followed set, identical in kind to Portfolio's own Requires Attention and Watchlist's and Daily Brief's own priority signals. Section 9 governs its presentation.

## 7. Thread Relevance Model

`APS-009` §9 (`DS-R-027`–`032`) states what qualifies a Candidate for inclusion; this section states how that qualification is communicated, never how it is computed.

- Every Candidate presented traces visibly to a Thread — a thematic, sectoral, or strategic connection to something already owned, followed, or reasoned about — per `DS-R-027`. Where the UI shows a Candidate, it also shows, or makes reachable, the specific Thread that qualifies it.
- Discover's own relevance is deliberately broader than Daily Brief's, per `DS-R-028`: a Candidate may connect to something never owned or followed before, provided the connection is real and statable. The UI never uses this breadth as license to surface a Candidate on novelty or popularity alone, per `DS-R-029`.
- Discover never claims comprehensiveness; a genuinely interesting Candidate with no current Thread simply does not appear, and this is not communicated as a defect or a gap to be filled, per `DS-R-031`.
- A Candidate with no traceable, statable Thread explanation is never presented, per `DS-R-030` and `DSINV-011`; this is this specification's own single most consequential failure-mode boundary (Section 24).

## 8. Information Hierarchy — Anchored to Exploratory

`APS-009` §10 states these categories as responsibility, explicitly not layout (`DS-R-043`); this section states the UX translation of each without asserting a required visual order beyond what Section 10 itself proposes as one reasonable realization (`DS-R-044`). Categories are organized along a spectrum from tightly anchored to genuinely exploratory — every point on the spectrum still requires Section 7's own Thread.

1. **Portfolio Fit.** Candidates evaluated against a gap or concentration in current owned positions, per `DS-R-033`. The most directly anchored category.
2. **Recently Strengthened Investment Cases.** Investment Cases where new Evidence or Reasoning has reinforced existing conviction, framed as opportunity — Discover looking inward at the Investor's own reasoning history, the mirror image of Daily Brief's Thesis-Impacting Change, per `DS-R-034`.
3. **Watchlist Candidates.** Unfollowed subjects resembling existing Watchlist Entries, per `DS-R-035`.
4. **Themes & Trends.** Candidates grouped under a theme already reflected in owned positions, Watchlist, or Investment Case history — the clearest embodiment of Section 7's own Thread requirement, per `DS-R-036`.
5. **Sector Rotation.** Sectors gaining relative strength, filtered to sectors the Investor already has exposure or stated interest in — never an unfiltered sector overview, per `DS-R-037`.
6. **High Conviction Ideas.** The small set of candidates ranked highest by the Atlas Priority Model — Discover's own verdict-equivalent tier, per `DS-R-038` and Section 9.
7. **Emerging Industries.** Nascent categories not requiring an already-owned or already-followed adjacent position — Discover's own most exploratory category, still Thread-bound, per `DS-R-039`.

**AI Opportunities is not an independent category.** It is presented as one named instance within Themes & Trends, per `DS-R-040`; no UI SHALL give it its own top-level card, section, or sourcing mechanism distinct from item 4 above.

**Valuation Opportunities is not an independent category.** It is presented as a cross-cutting timing lens — a badge or annotation applied to a Candidate that already qualified under another category, explaining why it has newly become worth surfacing — per `DS-R-041`; no UI SHALL give it its own top-level card or sourcing mechanism.

**Ignored Noise is never part of the default presentation.** Where offered at all, it is an explicit, opt-in transparency view of Candidates the relevance filter excluded, reached only through a deliberate Investor action — never surfaced automatically alongside the categories above, per `DS-R-042`.

## 9. Priority Model Integration — High Conviction Ideas

**Presentation.** High Conviction Ideas states plainly which unowned, unfollowed candidates currently rank highest by the Atlas Priority Model, sourced exclusively from that one shared model, never independently computed, per `DS-R-045`–`046`. Where the same underlying fact also appears in Portfolio's own Requires Attention or Daily Brief's own Verdict, the three presentations SHALL NOT disagree about it; they may differ only in scope — owned-and-open versus not-yet-owned-or-followed — per `DS-R-047`. High Conviction Ideas never itself constitutes a Decision, a Judgment, or an act of Investor Judgment; it surfaces candidates for the Investor's own attention and nothing more, per `DS-R-048`.

Identical in kind to `UX-014` §12's and `UX-015` §8's own treatment: text-legible, never color-only, never independently ranked, always traceable to the one shared Atlas Priority Model.

## 10. Screen Architecture

Addressed without visual mockups, consistent with `APS-009` §3's own exclusion of screens from the Product layer.

- **Page purpose and orientation.** The governing question — "What should I investigate next?" — is stated at the top of the Discover surface, the same governing-question-in-header pattern `UX-007A`, `UX-014`, and `UX-015` already establish.
- **High Conviction Ideas block.** The most prominent element, per Section 9, though never framed as a Verdict or Conclusion, per Section 5.
- **Category sections.** Portfolio Fit through Emerging Industries (Section 8, items 1–7), each carrying its own Thread explanation per Candidate.
- **Valuation Opportunities.** Rendered as an annotation on qualifying Candidates within their own category, never as a separate section.
- **Ignored Noise.** Reached only through an explicit, opt-in control; never rendered inline with the default categories.
- **Empty state.** States plainly that no Thread-connected Candidates currently exist, per `DS-R-061` and `DS-F-002`; never framed as broken or missing content.
- **First-visit state.** For a new Investor with little or no owned/followed/reasoned-about state, Discover may present a small set of broadly orienting candidates, explicitly framed as introductory and visually less confident than Thread-connected content elsewhere, per `DS-R-062`; this fallback is optional, never required, and never fabricated to avoid appearing empty, per `DS-R-064`.
- **Partial-data state.** Where one category's own content is temporarily unavailable, the surface states what is unavailable and why, and continues to show what remains current.
- **Error and recovery state.** A failure affecting one category or Candidate SHALL NOT block the entire Discover surface; the surface states the failure, offers retry, and leaves unaffected content usable.
- **Completion state.** Section 11's Done affordance; browsing Discover and finding nothing worth following today is itself a complete, successful session.

## 11. Interaction Model

- **Open.** Expands a Candidate's own summary — identity, Thread explanation, category — in place, or in a lightweight panel. Open is inspection only; it creates no Watchlist Entry, no Investment Case, and carries no Product-layer consequence.
- **Investigate.** The explicit control that progresses a Candidate directly into an Investment Case, without requiring an intermediate Watchlist Entry, per `DS-R-053`. Distinct from Open, and distinct from Follow: Investigate is the deliberate, further act of choosing to seriously evaluate a Candidate, never triggered by Open or by any passive interaction, per `DS-R-051`.
- **Follow.** Creates exactly one Watchlist Entry, governed entirely by `UX-014` once the act occurs, per `DS-R-050`. Distinct from Investigate: Follow adds the Candidate to the Investor's own intentional review queue without itself opening an Investment Case.
- **Ignore.** A bounded, session-scoped acknowledgment that a specific Candidate has been seen and is not currently of interest. `APS-009` defines no Product-layer "ignored" state for an individual Candidate; Ignore is pure UX-layer presentation, per `UXD-R-022`, carrying no persistence obligation and no penalty or consequence, mirroring `DS-R-052`'s own consequence-free treatment of leaving a Candidate un-Followed.
- **Dismiss.** Identical in kind to Ignore for a category-level or transient item (for example, a first-visit orienting candidate); session-scoped, no persistence obligation.
- **Return.** Closing a deeper context (Investment Workspace, Watchlist, Portfolio) and arriving back at Discover restores the exact prior scroll position and any Ignore/Dismiss state from the same visit, per Section 15.
- **View evidence.** Routes the Investor into the relevant Investment Workspace's own Evidence & Assumptions presentation once a Candidate has progressed; Discover never renders full Evidence content inline, mirroring `UX-015` §8's identical treatment for Daily Brief.
- **View reasoning.** Routes the Investor into the relevant Decision Context's own Investor Reasoning presentation, where one already exists (item 2 of Section 8, Recently Strengthened Investment Cases); Discover never renders full Reasoning content inline.
- **View related holdings.** Reveals the specific owned position, Watchlist Entry, or Investment Case a Candidate's own Thread connects to — the concrete answer to "why am I seeing this," per Section 7. Read-only; it alters nothing.
- **Done.** A calm, non-blocking acknowledgment that the current visit is finished, available at any point, with no gating condition — finding nothing worth Following or Investigating today is itself a complete, successful session.

**Explicit distinctions**, restated for clarity because conflating them is this specification's single most consequential failure mode class (Section 24):

- Opening a Candidate (Open) never itself creates a Watchlist Entry, begins investigation, or creates an Investment Case.
- Follow and Investigate are two separate progression paths, per Section 12 below — one is never a substitute UX label for the other.
- Viewing evidence, reasoning, or related holdings are read-only routing or disclosure actions; none of the three edits, creates, or resolves anything on Discover's own behalf.
- Recording a Decision occurs only within the Decision Workspace, per `APS-001` and the existing Decision Workspace specifications — never from within Discover itself, per `DS-R-073`.

## 12. Progression — Two Paths

`APS-009` uniquely authorizes two distinct progression paths, unlike `APS-007`'s single Watchlist-to-Investment-Case path; this section states the UX contract for each.

**Path A — Discover → Watchlist (Follow).** Selecting Follow (Section 11) creates exactly one Watchlist Entry, per `DS-R-049`; this act is then governed entirely by `UX-014`'s own interaction model, states, and removal behavior — this specification does not restate them. No UI mechanism SHALL infer a Follow from viewing, dwelling on, or repeatedly encountering a Candidate, per `DS-R-051` and `DSINV-008`.

**Path B — Discover → Investment Case directly (Investigate).** Selecting Investigate (Section 11) progresses a Candidate directly into an Investment Case, without requiring an intermediate Watchlist Entry, per `DS-R-053`. The UX transition asks nothing administrative of the Investor: Atlas creates the required Investment Case silently, the moment the genuine act occurs, per `DS-R-054` and `DSINV-010` — mirroring the identical silent-creation discipline `UX-014` §10 already establishes for Watchlist's own progression. The Investor lands directly inside the newly available Investment Workspace, already oriented to the Candidate, with no intermediate "Case created" ceremony required. No standalone "create a Case" affordance independent of a genuine reasoning act is ever presented, per `DS-R-056`.

**Where a Candidate has already progressed into a Watchlist Entry**, its further progression into an Investment Case is governed entirely by `UX-014`'s own progression contract (`WL-R-025`–`027`), not restated here, per `DS-R-055`.

Neither path is ever triggered automatically; both require an identifiable, deliberate Investor act, per `DSINV-009`.

## 13. Discover as the Previewed Party

Discover is the only one of the three surfaces this UX expansion covers that is never itself a host of a bounded preview of another area — it is only ever the previewed party, per `APS-009` §14.

- Discover exposes a small, curated summary of its own current High Conviction Ideas and Emerging Industries content sufficient for `UX-015`'s own Discover Highlight preview, without requiring Daily Brief to re-implement Discover's own relevance filtering, per `DS-R-057`.
- Discover never requires or assumes that Daily Brief's own preview reproduces its content in full; a small, curated subset is sufficient and expected, per `DS-R-058`.
- No fact material to understanding a Discover Highlight exists only within Daily Brief's own bounded preview of it; the full, current Discover always remains available in Discover's own area, per `DS-R-059`.
- The Discover Highlight preview stays small and deliberately curated; it never grows to resemble Discover's own full category set, per `DS-R-060` and `DSU-F-010` (Section 24).
- `UX-007A` and `UX-007P` were checked directly and confirmed to contain no existing Discover entry point today. This specification states only what Discover itself must expose; extending `UX-007A`/`UX-007P` to add an entry point is explicitly out of this specification's own scope (Section 1), the identical posture `UX-014` and `UX-015` already took toward their own analogous Portfolio-integration gaps.

## 14. States

Each state below states what the Investor understands, what action is available, how Atlas avoids asserting uncertainty it does not have, and how the Investor recovers or exits.

- **Loading.** Understands the surface is evaluating the current universe; no action is offered prematurely; skeleton structure resembles the eventual category layout, not a generic spinner.
- **Empty.** Understands no Thread-connected Candidates currently exist across any category; a calm, complete state, per `DS-R-061` and `DS-F-002`.
- **No Suitable Opportunities.** The category-level analog of Empty — a specific category (for example, Sector Rotation) has no qualifying Candidate this visit; distinct from whole-surface Empty in scope.
- **Candidate Available.** Understands a specific Candidate exists, its category, and its Thread explanation.
- **Previously Viewed.** A Candidate was Opened in a prior visit; its Thread may have changed since, and if so is presented as updated, not as newly discovered.
- **Previously Ignored.** A Candidate was Ignored in a prior session-scoped visit; per Section 11, this carries no Product-layer persistence, so a materially unchanged Candidate MAY or MAY NOT reappear depending on implementation choice, but its reappearance is never presented as new when nothing about its own Thread changed.
- **Followed.** A Candidate has become a Watchlist Entry; the Discover-side UI reflects this (for example, offering "Open in Watchlist" rather than Follow again), governed onward by `UX-014`.
- **Investigated.** A Candidate has progressed into an Investment Case; the Discover-side UI reflects this (offering "Open Investment Case" rather than Investigate again), per Section 12.
- **Partial Data.** Understands specifically which category or Candidate's own signal is unavailable and why; unaffected content remains fully usable.
- **Unavailable Data.** A specific fact (for example, a single Candidate's own supporting detail) cannot currently be retrieved; stated honestly rather than omitted silently.
- **API/Data Error.** Understands a specific, scoped failure with a retry option; the rest of Discover remains usable.
- **Repeated Visit.** Discover is evaluated fresh against the current universe on every visit, per `DS-R-009` and `DS-R-065`; a Candidate may legitimately reappear across visits where its own Thread remains current — this is correct behavior, not a repeat-visit defect, unlike Daily Brief's own discipline.
- **First Visit.** Little or no owned/followed/reasoned-about state exists yet to connect a Thread against; Section 10's own optional introductory fallback may apply, per `DS-R-062`.
- **Established Investor.** Many owned positions, Watchlist Entries, and Investment Cases; scaled by the anchored-to-exploratory hierarchy (Section 8) and the Atlas Priority Model (Section 9) alone, never by presenting every possible Candidate with equal prominence, per `DS-R-066`.
- **Multi-Portfolio Future Compatibility.** This specification assumes exactly one Portfolio and one Watchlist per Investor, per `DS-R-068`; a future multi-portfolio-scoped Discover relevance model is not asserted unsupportable, only undefined here, per `DS-R-069`. No state in this section presumes multi-portfolio scoping exists today.

## 15. Navigation

- Discover sits as a primary destination alongside Portfolio, Watchlist, and Daily Brief, consistent with `UX-012A` §1's own list of Atlas surfaces and `UX-014` §15's and `UX-015` §14's identical treatment.
- Contextual return paths: closing an Investment Workspace or the full Watchlist, reached via Section 11's Investigate, Follow, or routing links, returns the Investor to the exact prior Discover scroll position and Ignore/Dismiss state, per Section 11's own Return definition.
- Transition to the Investment Workspace occurs via Investigate, or via View evidence/reasoning routing where a Recently Strengthened Investment Case is already open (Section 11).
- Transition to the full Watchlist occurs via Follow, then onward navigation governed by `UX-014`.
- Transition to the Decision Workspace occurs only from within an Investment Workspace or Decision Context that already exists — never directly from Discover itself, per `DS-R-073`.
- No dead ends: every state in Section 14 offers at least one way forward (an action, a Return path, or Done).

## 16. Accessibility

Governed directly by `UX-000` §19 (`UXD-R-091`–`092`); this specification states Discover's own application of that standing requirement.

- Reading order follows Section 8's own anchored-to-exploratory hierarchy — High Conviction Ideas first, then each category in turn — predictably for assistive technology.
- Every interaction verb in Section 11 (Open, Investigate, Follow, Ignore, Dismiss, Return, View evidence, View reasoning, View related holdings, Done) is reachable and operable by keyboard alone.
- Priority and category (Section 9, Section 8) are never communicated by color alone; each carries a text label.
- Action labels are explicit and verb-first ("Investigate," "Follow," "Ignore"), never ambiguous icons alone.
- An empty Discover state or a category with no suitable opportunities is announced clearly to assistive technology, not conveyed by visual absence alone, per `DS-R-061`.
- Every Atlas-originated Thread rationale carries explicit, programmatically associated attribution, per `UXD-R-054`.
- Focus returns to a predictable, stable location after Ignore/Dismiss or after returning from a deeper context, mirroring `UX-005` §23's, `UX-014` §16's, and `UX-015` §15's identical requirement.

## 17. Responsive Behavior

Stated architecturally, without pixel values, per Section 3's own non-scope.

- What remains immediately visible at any viewport: the High Conviction Ideas block (Section 9) — the minimum needed to answer "what should I investigate next" without opening anything.
- What may collapse under narrower viewports: the more exploratory categories (Emerging Industries, Sector Rotation) behind an expansion control, consistent with `UX-007A` §27's, `UX-014` §17's, and `UX-015` §16's own narrow-layout discipline.
- What must never disappear: each Candidate's own Thread explanation and next action (Follow, Investigate) — collapsing either would silently violate `UXD-R-092`.
- Primary actions (Follow, Investigate) remain reachable by touch or keyboard at every viewport, never demoted behind a hover-only affordance.
- Thread explanations and attribution remain understandable at narrow widths through the same text-label discipline Section 16 requires generally.

## 18. AI Attribution and Investor Ownership

- Where AI drafts or improves a Candidate's own "why this" Thread rationale, per `DS-R-026`, that content carries visible, third-person attribution, per `UXD-R-054`, `UXD-R-057`, and PP-008 — never first-person belief framing.
- AI never originates a Candidate's own inclusion and never computes a ranking independent of the Atlas Priority Model, per `DS-R-026` and `DSINV-007`; no UI implies otherwise.
- The Investor remains responsible for deciding whether a Candidate warrants Follow or further investigation; Discover surfaces the Candidate, never the decision, per `DS-R-087` and PP-003.
- The Investor owns every Follow act and every progression act originating from Discover, and the Watchlist Entry or Investment Case each produces, per `DS-R-086`.
- The Investor remains accountable for any Decision later reached after progressing a Discover Candidate into an Investment Case, per `DS-R-088` and `APP-000` §8.2.

## 19. Explicit UX Exclusions

Each boundary below states the UX consequence of a distinction `APS-009` already draws at the Product layer.

- **Not Portfolio.** Discover's screen architecture (Section 10) never includes owned-position state or any Portfolio-owned category; Discover operates entirely outside the owned set, per `DS-R-070` and `DSINV-002`.
- **Not Watchlist.** Discover never lets the Investor browse or edit the full Watchlist directly; it is the generative process upstream of it, per `DS-R-071` and `DSINV-003`.
- **Not Daily Brief.** Discover never presents itself as a bounded temporal delta; it is continuous and atemporal, evaluated fresh on each visit, per `DS-R-072` and `DSINV-004`.
- **Not Decision Workspace.** Discover never offers a Record Decision action, a Proposed Decision field, or any Decision Workspace content directly, per `DS-R-073`.
- **Not a chat interface.** Discover never presents an open-ended conversational surface for arbitrary Investor questions; every Candidate is structured and categorized, per `DS-R-074`.
- **Not a news feed.** A Candidate surfaces only via Thread connection, never for general newsworthiness, per `DS-R-075`.
- **Not a stock screener.** Discover never requires the Investor to specify filter criteria before content appears; it proactively generates Candidates, per `DS-R-076`.
- **Not a stock database.** Discover is opinionated and selective, never an exhaustive, neutral lookup surface presenting everything with equal weight, per `DS-R-077`.
- **Not an unexplained recommendation engine.** Every Candidate carries a traceable Thread-based explanation for its own inclusion; a Candidate with none is never presented, per `DS-R-078` and `DSINV-011`.

## 20. Atlas Responsibilities

- Atlas SHALL evaluate the current universe of candidates against owned positions, Watchlist Entries, and Investment Case history to identify Thread connections, per `DS-R-079`.
- Atlas SHALL filter every candidate against the Thread requirement before presenting it, per `DS-R-080`.
- Atlas SHALL populate High Conviction Ideas from the Atlas Priority Model, never from an independently computed ranking, per `DS-R-081`.
- Atlas SHALL NOT create a Watchlist Entry or progress a Candidate into an Investment Case without an explicit, identifiable Investor act, per `DS-R-082`.
- Atlas SHALL disclose an empty Discover state explicitly, per `DS-R-083`.
- Atlas SHALL preserve the read-only boundary Section 6 states in every computation Discover performs; no interaction defined in Section 11 SHALL alter a Core Domain Object or an already-accepted Product record, per `DS-R-010` and `DS-R-084`.
- Atlas SHALL attribute the origin of any Atlas-originated content Discover presents, including any AI-drafted rationale, per `DS-R-085`.

## 21. Investor Responsibilities

- The Investor is responsible for engaging with the Candidates and Thread explanations Discover presents, rather than treating any of them as a decision already made on their behalf, per PP-003.
- The Investor decides whether, and when, to Follow or Investigate a Candidate; Discover never requires this within the current visit.
- The Investor remains accountable for any Decision reached after leaving Discover for a Decision Context, in the same manner every other Atlas surface already establishes, per `DS-R-088`.

## 22. Requirements

Normative UX requirements for Discover, using the `DSU-R-` prefix — chosen to avoid colliding with `APS-009`'s own `DS-R-` (Product) prefix and `UX-000`'s own `UXD-R-` (Doctrine) prefix, following the identical disambiguation discipline `UX-014` and `UX-015` already established with `WLU-R-` and `DBU-R-`, per `UXD-R-096`.

**Purpose comprehension**

**DSU-R-001.** The Discover surface SHALL communicate its own governing question — "What should I investigate next?" — before any Candidate-level detail, per Section 10 and `UXP-001`.

**DSU-R-002.** No screen state SHALL imply that Discover is a destination for owned-position review, a change digest, or an open-ended search/chat surface, per Section 5 and Section 19.

**Thread relevance**

**DSU-R-003.** Every Candidate presented SHALL display, or make reachable, the specific Thread that qualifies it for inclusion, per `DS-R-027` and `DS-R-030`.

**DSU-R-004.** No UI element SHALL surface a Candidate on the basis of general popularity or trending status alone, per `DS-R-029`.

**Information hierarchy**

**DSU-R-005.** High Conviction Ideas SHALL be presented first and SHALL remain visible without scrolling on first view, per `DS-R-038` and `UXP-001`.

**DSU-R-006.** AI Opportunities SHALL NOT be rendered as an independent top-level category; it SHALL appear only as a named instance within Themes & Trends, per `DS-R-040`.

**DSU-R-007.** Valuation Opportunities SHALL NOT be rendered as an independent top-level category; it SHALL appear only as a cross-cutting annotation on Candidates already qualified elsewhere, per `DS-R-041`.

**DSU-R-008.** Ignored Noise SHALL NOT appear in the default presentation; it SHALL be reachable only through an explicit, opt-in control, per `DS-R-042`.

**Priority**

**DSU-R-009.** No independent ranking mechanism SHALL be introduced anywhere in Discover's own governed UI; every priority signal within High Conviction Ideas SHALL be traceable to the Atlas Priority Model, per `DS-R-046` and `DSINV-007`.

**DSU-R-010.** Where High Conviction Ideas and Portfolio's own Requires Attention or Daily Brief's own Verdict present the same underlying item, the UI SHALL NOT present them as disagreeing about the fact itself, per `DS-R-047`.

**Candidate, evidence, and reasoning presentation**

**DSU-R-011.** No full Evidence or Investor Reasoning content SHALL be rendered inline within Discover; View evidence and View reasoning (Section 11) SHALL route to the Investment Workspace or Decision Context instead.

**DSU-R-012.** Any Atlas-originated Thread rationale SHALL carry visible, third-person attribution, per `UXD-R-054`, `UXD-R-057`, and PP-008.

**DSU-R-013.** View related holdings SHALL reveal only already-known, read-only connection information; it SHALL alter nothing.

**Interaction**

**DSU-R-014.** Open SHALL produce no Product-layer effect; it SHALL only reveal already-known Candidate-level information, per Section 11.

**DSU-R-015.** Follow and Investigate SHALL each be controls visually and semantically distinct from Open and from each other, reachable only through deliberate selection.

**DSU-R-016.** No UI path SHALL infer a Follow or an Investigate act from viewing, dwelling on, or repeatedly encountering a Candidate, per `DS-R-051`.

**DSU-R-017.** Ignore and Dismiss SHALL persist no data beyond the current session/view and SHALL NOT be presented, coded, or described as deletion or resolution of the underlying Candidate.

**Progression**

**DSU-R-018.** Selecting Investigate on a Candidate with no existing Investment Case SHALL transition the Investor directly into a newly available Investment Workspace, with no intermediate configuration step, per `DS-R-054` and `DSINV-010`.

**DSU-R-019.** No standalone "create a Case" affordance independent of a genuine Investigate act SHALL be presented, per `DS-R-056`.

**DSU-R-020.** Where a Candidate has already progressed into a Watchlist Entry or Investment Case, the UI SHALL offer to open the existing record rather than creating a duplicate, per `DS-R-055` and `WLU-R-015`.

**DSU-R-021.** No UI path SHALL offer direct entry into a Decision Context or Decision Workspace from Discover; that transition SHALL be available only from within an Investment Workspace or existing Decision Context, per `DS-R-073`.

**Preview participation**

**DSU-R-022.** The state Discover exposes for Daily Brief's own Discover Highlight preview SHALL remain a small, curated summary; Discover itself SHALL NOT expand that preview beyond what `UX-015` §11 governs, per `DS-R-057` and `DS-R-060`.

**DSU-R-023.** No fact required to understand a Discover Highlight SHALL be presented only within Daily Brief's own bounded preview and nowhere within Discover's own area, per `DS-R-059`.

**Repeat visits and boundedness**

**DSU-R-024.** A Candidate reappearing across visits because its own Thread remains current SHALL NOT be treated as a defect or suppressed; this is correct behavior, per `DS-R-065`, distinct from Daily Brief's own repeat-visit discipline.

**DSU-R-025.** No UI mechanism SHALL manufacture urgency, novelty, or engagement pressure to encourage a return visit, per `DS-R-067`.

**State behavior**

**DSU-R-026.** Every state named in Section 14 SHALL be implemented; no unnamed or ambiguous intermediate state SHALL be presented to the Investor without explanation.

**DSU-R-027.** A failure affecting one category or Candidate's own data SHALL NOT block or degrade the rest of the Discover surface, per Section 10's error-and-recovery treatment.

**DSU-R-028.** An empty Discover state or first-visit state SHALL be stated explicitly, never presented as a silent or ambiguous blank surface, per `DS-R-061`–`062` and `DS-F-002`.

**DSU-R-029.** No UI mechanism SHALL fabricate a Thread-connected Candidate to avoid appearing empty, per `DS-R-064`.

**Navigation**

**DSU-R-030.** Returning from a deeper context (Investment Workspace, Watchlist) SHALL restore the Investor's own prior Discover scroll position and Ignore/Dismiss state, per Section 15.

**DSU-R-031.** No state defined in Section 14 SHALL leave the Investor without at least one available forward action, return path, or Done affordance.

**Accessibility**

**DSU-R-032.** Every interaction verb in Section 11 SHALL be operable by keyboard alone, per `UXD-R-092`.

**DSU-R-033.** No category, priority signal, or state SHALL be communicated by color alone; a text label SHALL always accompany it, per `UXD-R-092`.

**DSU-R-034.** Focus SHALL return to a predictable location after Ignore/Dismiss or after returning from a deeper context, per Section 16.

**Responsive preservation**

**DSU-R-035.** At every viewport, High Conviction Ideas SHALL remain immediately visible, per Section 17.

**DSU-R-036.** No primary action (Follow, Investigate) SHALL be demoted to a hover-only affordance at any viewport, per Section 17.

**Error prevention**

**DSU-R-037.** No UI mechanism SHALL allow Discover to compute or display a ranking independent of the Atlas Priority Model, per `DS-R-046` and `DSU-R-009`.

**DSU-R-038.** No UI mechanism SHALL allow a Watchlist Entry or Investment Case to be created from Discover without an identifiable, deliberate Investor act, per `DSINV-008` and `DSINV-009`.

**Completion behavior**

**DSU-R-039.** A Done affordance SHALL be available at any time the Investor is viewing Discover, with no gating condition.

**DSU-R-040.** No completion action SHALL require the Investor to Follow or Investigate a specific number of Candidates before Done becomes available.

**Product and UX traceability**

**DSU-R-041.** Every requirement in this section SHALL be traceable, by citation, to at least one of: `ATLAS_CONSTITUTION.md`, an `APP-000` Product Principle, an `APS-009` provision, an `APS-006` provision, an `APS-007` provision, an `APS-008` provision, or a `UX-000` `UXD-R-` rule, per Section 26.

## 23. Invariants

**DSU-INV-001 — Discover always represents genuine, Thread-connected opportunity.** No Candidate presented by this specification's own UI SHALL originate from anything other than a real, statable Thread connection or the Atlas Priority Model's own already-governed computation, per `DSINV-011`.

**DSU-INV-002 — Discover never performs Reasoning.** No UI element SHALL invite the Investor to construct or record Reasoning within the Discover surface itself, per `DSINV-005`.

**DSU-INV-003 — Discover never records a Decision.** No UI element within Discover SHALL present a Record Decision, Proposed Decision, or equivalent control, per `DSINV-006`.

**DSU-INV-004 — Discover never becomes Portfolio, Watchlist, or Daily Brief.** No screen state SHALL present owned-position content, full Watchlist editing capability, or a bounded temporal delta digest, per `DSINV-002`–`004`.

**DSU-INV-005 — Priority remains one scoped view of the Atlas Priority Model.** No independent ranking mechanism SHALL exist anywhere in this specification's own governed UI, per `DSINV-007`.

**DSU-INV-006 — Every Atlas-originated rationale remains visibly attributable.** No Atlas-originated Thread rationale SHALL be presented without attribution, per `UXD-R-054` and PP-008.

**DSU-INV-007 — No progression occurs without explicit, deliberate Investor action.** Every Follow, Investigate, or resulting Watchlist Entry or Investment Case SHALL be traceable to an identifiable Investor act, per `DSINV-008` and `DSINV-009`.

**DSU-INV-008 — The Discover Highlight preview is never a destination.** The bounded preview Daily Brief hosts of Discover SHALL always lead back to Discover's own full area, per `DSINV-012`.

**DSU-INV-009 — The user can always distinguish opening, following, and investigating.** Open, Follow, and Investigate SHALL remain three visually and behaviorally distinct actions at every point in this specification, per `DSU-R-015`.

**DSU-INV-010 — The user can always leave the screen with a clear completion state.** A Done affordance, per Section 11, SHALL be reachable from every state Section 14 defines.

## 24. Failure Modes

Atlas SHALL fail closed: where continuing would require this specification, `APS-009`, `APS-006`, `APS-007`, `APS-008`, or `UX-000` to be violated, the interface SHALL present an honest, bounded state rather than proceed on a fabricated or inferred basis. No specific error copy is prescribed here.

**DSU-F-001 — Everything is recommended.** Presenting a Candidate that fails the Thread requirement violates `DSINV-011` and `DSU-R-003`, and defeats Discover's own filtered, curated purpose.

**DSU-F-002 — Nothing is recommended.** Failing to state plainly that no Thread-connected Candidates currently exist, and instead presenting a blank or broken-seeming surface, violates `DS-R-061` and `DSU-R-028`.

**DSU-F-003 — Trending replaces relevance.** Surfacing a Candidate on the basis of general popularity or trending status alone violates `DS-R-029` and `DSU-R-004` directly.

**DSU-F-004 — Discover becomes Portfolio.** Presenting owned-position state within Discover itself violates `DSINV-002` and `DS-R-070`.

**DSU-F-005 — Discover becomes Daily Brief.** Presenting Discover's own content as a bounded temporal delta rather than a continuously-evaluated set violates `DSINV-004` and `DS-R-072`.

**DSU-F-006 — Discover becomes an AI chat.** Presenting an open-ended conversational interface in place of Discover's own structured, categorized presentation violates `DS-R-074`.

**DSU-F-007 — No explanation exists.** Presenting a Candidate with no traceable Thread explanation violates `DS-R-030` and `DSU-R-003` directly.

**DSU-F-008 — Manufactured urgency.** Framing a Candidate with urgency not supported by a genuine Valuation Opportunities timing signal or equivalent traceable basis violates `DS-R-067` and `ATLAS_CONSTITUTION.md`'s own Product Philosophy.

**DSU-F-009 — Automatic Watchlist or Investment Case creation.** Creating a Watchlist Entry or progressing a Candidate into an Investment Case absent an explicit, identifiable Investor act violates `DSINV-007`, `DSINV-008`, and `DSINV-009` directly.

**DSU-F-010 — Discover Highlight grows to resemble Discover's own full category set.** Expanding the Daily-Brief-hosted preview beyond a small, curated subset violates `DS-R-060` and `DSU-INV-008`.

**DSU-F-011 — Priority disagreement.** Presenting High Conviction Ideas and Portfolio's own Requires Attention, or Daily Brief's own Verdict, as reaching different conclusions about the same underlying item violates `DS-R-047` and `DSU-R-010`.

**DSU-F-012 — Unclear completion.** Omitting a reachable Done affordance from any state in Section 14, or requiring an artificial threshold before it becomes available, violates `DSU-INV-010` and `DSU-R-039`–`040`.

## 25. Acceptance Criteria

**DSU-AC-001 (Purpose immediately understood).** A new Investor is observed to understand, from the High Conviction Ideas block alone, that Discover answers "what should I investigate next," per Section 5 and `DSU-R-001`.

**DSU-AC-002 (Opportunity relevance visible).** Every Candidate presented is observed accompanied by an identifiable Thread explanation, per `DSU-R-003`.

**DSU-AC-003 (Connection understandable).** Selecting View related holdings is observed to reveal the specific owned position, Watchlist Entry, or Investment Case a Candidate's Thread connects to, per `DSU-R-013`.

**DSU-AC-004 (Priority justified).** No Candidate is ever observed framed with urgency unsupported by a traceable Valuation Opportunities signal, per `DSU-F-008`.

**DSU-AC-005 (No duplication with Portfolio).** No owned-position content is ever observed within Discover, per `DSU-INV-004`.

**DSU-AC-006 (No duplication with Watchlist).** No full Watchlist editing capability is ever observed within Discover; Follow is observed to hand off entirely to `UX-014`, per `DSU-R-015`.

**DSU-AC-007 (No duplication with Daily Brief).** Discover's own content is never observed framed as a bounded temporal delta; a Candidate is observed able to legitimately reappear across visits, per `DSU-R-024`.

**DSU-AC-008 (AI attribution visible).** Every Atlas-originated Thread rationale is observed to carry visible, third-person attribution, per `DSU-R-012` and `DSU-INV-006`.

**DSU-AC-009 (Investor ownership preserved).** No observed interaction implies that Atlas has made a decision on the Investor's own behalf; every progression is observed to require a deliberate Follow or Investigate act, per `DSU-INV-009`.

**DSU-AC-010 (No autonomous progression).** No Watchlist Entry or Investment Case is ever observed created without an identifiable Investor act, per `DSU-R-038` and `DSU-INV-007`.

**DSU-AC-011 (Repeat visits behave correctly).** A Candidate with a still-current Thread is observed able to reappear across visits without this being treated as a defect, per `DSU-R-024`.

**DSU-AC-012 (No Product or Core redesign required).** No acceptance check above is found to require a new Core Domain Object, a new Core invariant, a change to `APS-009`'s own normative behavior, or a change to any other Product Architecture document, per `DS-AC-006`.

## 26. Traceability

| Section | Normative UX basis | Normative Product basis | Core basis |
|---|---|---|---|
| §5 UX Definition | `UX-000` §5, §24 (`UXP-001`); `UXD-R-071` | `APP-000` PP-004; `APS-009` §2, §18 | — |
| §6 Relationships | `UX-000` `UXD-R-008` | `DS-R-014`–`022` | — |
| §7 Thread Relevance | `UX-000` §12 | `DS-R-027`–`032` | — |
| §8 Information Hierarchy | `UX-000` §12–14, §20 | `DS-R-033`–`044` | — |
| §9 Priority Model Integration | `UX-000` `UXD-R-058`–`061` | `DS-R-045`–`048` | — |
| §10 Screen Architecture | `UX-000` `UXD-R-071` (Conclusion boundary) | `DS-R-012`, `DS-R-043`–`044`, `DS-R-061`–`064` | — |
| §11 Interaction Model | `UX-000` §7 (`UXD-R-011`) | `DS-R-049`–`052`, `DS-R-004` | — |
| §12 Progression | `UX-000` `UXD-R-023`, `UXD-R-104` | `DS-R-053`–`056`; `APP-001` §3.13 | `APS-001` §8 (Decision Context creation) |
| §13 Previewed Party | `UX-000`'s own preview governance (adopted, not itself defining it) | `APS-006` §13; `APS-008` §14; `DS-R-057`–`060` | — |
| §14 States | `UX-000` §19 (`UXD-R-091`–`092`) | `DS-R-061`–`069`, `DS-F-001`–`010` | — |
| §15 Navigation | `UX-005` §20–§22; `UX-007A` §25; `UX-014` §15; `UX-015` §14 | — | — |
| §16 Accessibility | `UX-000` §19; `ADR-002` C-06 | — | — |
| §17 Responsive Behavior | `UX-007A` §26–§27; `UX-014` §17; `UX-015` §16 | — | — |
| §18 AI Attribution/Ownership | `UX-000` §10–11 (`UXD-R-048`–`057`) | `DS-R-085`–`088`, PP-003, PP-008 | — |
| §19 Explicit UX Exclusions | `UX-000` §8 (`UXD-R-020`–`039`) | `DS-R-070`–`078`, `DSINV-002`–`004` | — |
| §22–25 Requirements/Invariants/Failure Modes/Acceptance | `UX-000`, throughout, per each citation | `APS-009`, throughout, per each citation | `OE-002` §4 (via `DSINV-001`/`DSINV-015`) |

No temporary report (the UX Correspondence Investigation, the UX Governance Resolution Sprint's own deliverable text, or the UX Architecture Layer Investigation) is cited above as a governing repository authority; each is a completed session finding already absorbed into the committed documents this table cites directly.

## 27. Open Questions and Deferred Work

- **Opportunity ranking methodology.** `APS-009` §9 defines what qualifies, not how ranking within and across categories is computed. Classified: **non-blocking** — any UI presenting genuinely qualified Candidates in a reasonable order satisfies this specification.
- **Personalization.** How Thread-relevance weighting adapts to an individual Investor's own demonstrated preferences is not defined here, mirroring `APS-009` §25's own identical deferral, coupled to Investor Lab's own eventual specification. Classified: **non-blocking**, implementation-level.
- **Theme maturity and depth.** A future, dedicated Themes capability would deepen the existing Themes & Trends mechanism; its exact shape is not defined here. Classified: **non-blocking**.
- **AI-generated opportunities' own eventual UX detail.** `DS-R-026` bounds AI's role in principle — rationale drafting only — but no dedicated future AI-capability specification exists yet. Classified: **out of scope**, pending that future specification.
- **Institutional discovery.** Asset-manager multi-mandate discovery needs, coupled to Portfolio's and Watchlist's own identical open questions. Classified: **requires separate architecture work**, non-blocking for this specification's own completeness.
- **Whether "Candidate" or "Thread" requires later formal Product Concept treatment.** Genuinely open, mirroring `APS-009` §25's own framing and the identical questions `APS-006` §24, `APS-007` §24, and `APS-008` §28 carry for "Holding," "Watchlist Entry," and "Thesis-Impacting Change." Classified: **deferred** — a future Product Architecture decision this specification has no authority to make.
- **Multi-Portfolio-scoped Discover relevance.** Coupled to Portfolio's and Watchlist's own identical open questions (`APS-006` §24, `APS-007` §24, `UX-014` §24). Classified: **requires separate architecture work**.

None of the above is decided by implication anywhere in this document.

---

*This specification does not modify `ATLAS_CONSTITUTION.md`, `Architecture-Governance.md`, `APP-000`, `APP-001`, any `APS` document, `UX-000`, `UX-014`, `UX-015`, or any other existing UX document. It introduces no new Core Domain Object, no new Product Concept, and requires no Core, Product Architecture, or implementation redesign.*
