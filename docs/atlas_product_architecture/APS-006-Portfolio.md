# APS-006 — Portfolio

**Status:** Draft, v0.1. This is the sixth Atlas Product Specification, subordinate to APP-000 — Atlas Product Doctrine and APP-001 — Atlas Product Concept Taxonomy (v0.4), and depending on APS-001 — Decision Context. It states the complete normative product behavior of Portfolio: the product surface responsible for presenting the Investor's owned-position state and portfolio-level awareness. It does not describe screens, workflows, visual design, interaction design, algorithms, data schemas, persistence mechanisms, or any other implementation technique, and it does not redefine Core ontology.

---

## 1. Governance Metadata

Stated here in full, per `Architecture-Governance.md` §10's own requirement that every future Atlas document declare this at its own outset.

- **Document identifier:** APS-006.
- **Title:** Portfolio.
- **Version:** v0.1.
- **Status:** Draft — not yet reviewed, not yet binding on any implementation. The smallest truthful status available to a newly authored specification, matching the status every one of APS-001 through APS-005 carried at its own first publication.
- **Parent authority:** APP-000 — Atlas Product Doctrine (Draft v0.4); APP-001 — Atlas Product Concept Taxonomy (Draft v0.4), specifically §3.13 (Investment Case), §4 (Portfolio's own reaffirmed deferral), and §9 item 7 (Portfolio reserved for this specification).
- **Dependencies:** APS-001 — Decision Context (Draft v0.1), for Decision Context's own lifecycle and its enclosure within Investment Case. `OE-002` — Domain Object Model (Final), for Case, Decision, and Outcome. `OE-004` — Domain Invariants (Final), for same-Case reference rules this specification's own read-only relationships must respect.
- **Scope:** Portfolio's own identity, ownership, responsibilities, information hierarchy, relationship to the Atlas Priority Model, relationship to Investment Case and Decision Context, relationship to future Daily Brief, Discover, Watchlist, and Investor Lab, exclusions, and the Atlas/Investor responsibility split.
- **Non-scope:** Screens, workflows, navigation, visual design, interaction design, implementation, algorithms, data schemas, persistence mechanisms; the complete product behavior of Daily Brief, Discover, or Watchlist (each reserved for its own future specification); any amendment to APP-000, APP-001, APS-001 through APS-005, Atlas Core, or `docs/atlas_ux/`.
- **Affected documents:** None requiring amendment. `APP-001` already reserved this territory in its own v0.4 amendment (§3.13, §4, §9) and requires no further change. `Architecture-Governance.md` §8.2's own description of the Product Architecture track as "APP-000, APP-001, APS-001–005" becomes incomplete the moment this document is added, but its own text states it "will drift... and should be refreshed by a future governance pass rather than assumed current indefinitely" — that refresh is future work, not performed here.
- **Superseded documents:** None, in the formal sense `Architecture-Governance.md` §7 defines. The Phase II "Portfolio Control Center" product specification is this document's own primary source material, but it was never committed to this repository; §7's Supersession Notice mechanism applies to a document that exists in the repository and receives a notice added to itself. No such document exists here to notice. Portfolio Control Center is cited throughout this specification as source material only, never as a document this specification formally supersedes.
- **Migration requirements:** None. No existing repository document, and no implementation, is required to change as a consequence of this document's creation.

## 2. Purpose

Portfolio requires its own specification because APP-001 §3.13 names it as approved deferred territory but does not itself state Portfolio's product behavior, and because `ATLAS_CONSTITUTION.md`'s own Non-Negotiable Principles name "Portfolio before position" directly, without operationalizing what that principle requires of a dedicated Portfolio surface. This specification closes that gap: it states Portfolio's own identity as a product-level surface — not a Core Domain Object, not a replacement for Investment Case or Decision Context — its responsibilities, its information hierarchy, its relationship to the single Atlas Priority Model this specification adopts as accepted architecture, and its boundary against Daily Brief, Discover, Watchlist, Investor Lab, and Decision Workspace — so that a future UX specification, an implementation design, engineering, QA, and any AI agent working on Atlas can build from it without inventing new Portfolio product rules of their own.

This specification is re-derived from, and supersedes as normative authority, the accepted Phase II "Portfolio Control Center" product specification, the Product Architecture Review, and the Architecture Resolutions — three source documents that were never committed to this repository and hold no independent authority of their own. Their valid product decisions are translated here into normative requirements, invariants, and acceptance criteria consistent with the real APP/APS lineage; their content is not copied verbatim, and no determination they made is treated as binding until restated and justified here.

## 3. Scope

In scope: Portfolio's identity as a product-level surface; its ownership and responsibility boundary; its relationship to Investor, owned position, Investment Case, Decision Context, Decision, and Outcome; its relationship to the Atlas Priority Model; its relationship to future Daily Brief, Discover, Watchlist, Investor Lab, Monitoring, and Notifications; its information hierarchy, stated as responsibility, not layout; its governance of bounded previews of other product areas; its explicit exclusions; and the Atlas/Investor responsibility split.

Out of scope, per APP-000 §1 and §10: screens, workflows, navigation, visual design, interaction design, algorithms, data schemas, persistence mechanisms, or any other implementation technique. Also out of scope: Daily Brief's, Discover's, and Watchlist's own complete product behavior (each reserved for APS-008, APS-009, and APS-007 respectively); the exact computation method behind portfolio health or risk (Section 24); multi-portfolio and asset-manager multi-mandate support (Section 24); formal Product Concept treatment of "Holding" or "owned position," which this specification does not attempt and does not require (Section 6, Section 24); the global Preview Pattern's own presentation-layer rules, which remain UX governance territory per the accepted Product Architecture Reconciliation Design, not restated here beyond the minimum needed to state Portfolio's own product responsibility (Section 13); and any resolution of the Core-track discrepancy between Evidence's documented, Product-layer-only status and its current implementation, which this specification does not reopen.

## 4. Governing References

- **`ATLAS_CONSTITUTION.md`.** Normative, superior to every document in the Atlas Product Architecture track. "Portfolio before position" is cited directly as this specification's own constitutional grounding (Section 2).
- **APP-000 — Atlas Product Doctrine, Draft v0.4.** Normative, superior to this specification.
- **APP-001 — Atlas Product Concept Taxonomy, Draft v0.4.** Normative, superior to this specification; §3.13 accepts Investment Case; §4 reaffirms Portfolio's own deferral and names this specification as its subject; §9 item 7 reserves this specification's own sequencing position.
- **APS-001 — Decision Context, Draft v0.1.** Normative, superior to this specification; governs the lifecycle this specification's own "Open Review" content reads from, without restating it.
- **`OE-002` — Domain Object Model, Final.** Normative for Atlas Core; defines Case (§3.1), Decision (§5.5), and Outcome (§5.6), each read only by this specification.
- **`OE-004` — Domain Invariants, Final.** Normative for Atlas Core; INV-002 and INV-004 bound any same-Case reference this specification's own read-only relationships touch.
- **`Architecture-Governance.md`.** Accepted; governs this document's own required governance metadata (Section 1) and the authority chain this specification sits within.
- **The Product Architecture Reconciliation Design** (accepted, this repository's own prior governance work). Non-normative in the sense that it is not itself a Product Architecture document — it is the accepted design this specification executes. Cited as the source of the Core Case → Investment Case → Decision Context → Decision mapping (Section 6, Section 8), the ruling that the Atlas Priority Model and the Preview Pattern are not independent Product Concepts (Sections 10, 13), and the Evidence-correction guidance this specification follows without reopening (Section 20).
- **The Phase II "Portfolio Control Center" product specification.** Non-normative source material only, never committed to this repository, holding no authority of its own. Its valid product decisions are translated, not copied, into this specification's own requirements.
- **The Phase II "Product Architecture Review" and "Architecture Resolutions."** Non-normative source material only, for the same reason. The Atlas Priority Model (Section 10) and the bounded-preview discipline (Section 13) originate in Architecture Resolutions' own analysis, adopted here as accepted architecture, restated in this specification's own normative language rather than cited as an independent authority.

## 5. Definitions

Only concepts not already defined by APP-000, APP-001, or APS-001 are defined here.

**Owned position.** Ordinary-language description of a specific capital commitment the Investor currently holds. Not a formal Product Concept; no independent identity, ownership, lifecycle, or responsibility is asserted for it by this specification. See Section 6 and Section 24.

**Atlas Priority Model.** A single, product-level computation of which items, across everything the Investor owns or has reasoned about, currently warrant the Investor's Attention, per PP-001. Defined in full in Section 10 of this specification and adopted by reference by any future specification that needs it; not itself a Product Concept requiring APP-001 acceptance, per the accepted Product Architecture Reconciliation Design.

**Open Review.** An open Decision Context (APS-001), within any Investment Case, that has not yet closed by Commitment or Abandonment. Corrects the imprecise Phase II source term "Investment Cases with no recorded Decision," which described the wrong grain — an entire Investment Case may enclose several Decision Contexts, only some of which are open at a given time (APP-001 §3.13 Cardinality).

**Bounded preview.** A compact, capped presentation, hosted by Portfolio, of content whose own product responsibility belongs to a different area (Daily Brief, Discover, Watchlist). Governed by Section 13; never a substitute for its own destination.

## 6. Architectural Position

**PF-R-001.** Portfolio SHALL be subordinate to APP-000, APP-001, and APS-001; it SHALL NOT contradict any of the three or redefine a term any of them defines.

**PF-R-002.** Portfolio SHALL NOT be treated as a Core Domain Object, and SHALL NOT be, or be treated as, reference-eligible within Atlas Core.

**PF-R-003.** Portfolio SHALL NOT be treated as identical to, or a replacement for, Case, Investment Case, or Decision Context.

**PF-R-004.** Portfolio SHALL NOT be treated as a Decision Engine concept. It does not perform Reasoning, does not record a Decision, does not exercise Investor Judgment, and does not evaluate Decision Quality.

**PF-R-005.** Portfolio SHALL NOT be treated as a pure UX artifact carrying no Product responsibility. It owns real product responsibility, stated in Section 8 through Section 13.

**PF-R-006.** Portfolio SHALL NOT introduce a new Core Domain Object, including for the purpose of representing an owned position. Where Core has no adopted primitive for a fact Portfolio needs to present, that gap is recorded as an open question (Section 24), never silently resolved by this specification.

## 7. Core Properties and Ownership

**PF-R-007.** Portfolio SHALL be owned by the Investor, in the same sense Investment Case and Decision Context are Investor-owned (APP-001 §3.10, §3.13).

**PF-R-008.** Portfolio SHALL derive its own content entirely by reading already-accepted Product Concepts and Core Domain Objects. It SHALL NOT originate a Decision, a Judgment, an Outcome, an Observation, or any other Core Domain Object.

**PF-R-009.** Portfolio SHALL present, in aggregate, the state of every Investment Case (APP-001 §3.13) the Investor holds, per Investment Case's own Relationships clause: *"A future Portfolio subordinate specification reads across many Investment Cases, in aggregate, to state what the Investor currently holds."*

**PF-R-010.** Portfolio SHALL NOT alter, mutate, or supersede any Investment Case, Decision Context, Decision, or Outcome it reads. Every relationship Portfolio holds to these concepts is read-only.

**PF-R-011.** Portfolio SHALL NOT require the existence of a Core Domain Object type beyond the six `OE-002` §4 already adopts, or of a Decision Context, to have some content to present; an Investor with no open Decision Context and no recorded Decision remains a valid, presentable Portfolio state (Section 14, empty and early states).

**PF-R-012.** Portfolio's own central user question — *"Where do I stand?"* — SHALL govern every category of content this specification defines. A category that does not serve this question does not belong in Portfolio, regardless of its own informational value.

## 8. Concept Relationships

Each relationship below is classified as existing, derived, product-level, deferred, future-facing, or not yet represented in Core, per this specification's own required precision.

**PF-R-013.** Portfolio's relationship to **Investor** is existing and product-level: Portfolio is owned by, and exists to serve, the Investor, per Section 7.

**PF-R-014.** Portfolio's relationship to **owned position** is not yet represented in Core. No adopted Core Domain Object, and no accepted Product Concept, formally represents "an owned position" as its own primitive. Portfolio's presentation of owned-position state relies on ordinary-language description of this fact, most plausibly derived from Observation and Decision records within an Investment Case; this specification does not assert that mapping as confirmed, per Section 24.

**PF-R-015.** Portfolio's relationship to **Investment Case** is existing and product-level, per PF-R-009: Portfolio reads across many Investment Cases, in aggregate.

**PF-R-016.** Portfolio's relationship to **Decision Context** is existing and product-level: Portfolio's own Open Review content (Section 5, Section 11) reads the open/closed state of Decision Contexts held within the Investment Cases it aggregates, per APS-001 §9 through §13.

**PF-R-017.** Portfolio's relationship to **Decision** is existing and derived: Portfolio MAY read `Decision.confidence` and other already-recorded Decision fields to compose aggregate, derived content (for example, a distribution of conviction across owned positions); Portfolio never originates or alters a Decision, per PF-R-008.

**PF-R-018.** Portfolio's relationship to **Outcome** is existing and derived: Portfolio MAY read Outcome records to inform aggregate context; per `ORINV-016`, Portfolio SHALL NOT characterize Decision Quality by reference to Outcome, whether alone or in aggregate.

**PF-R-019.** Portfolio's relationship to **Daily Brief** is deferred and future-facing: Daily Brief's complete product behavior is reserved for APS-008, not yet written. Portfolio hosts a bounded preview of Daily Brief's own content today, governed by Section 13, and does not itself perform Daily Brief's responsibility.

**PF-R-020.** Portfolio's relationship to **Discover** is deferred and future-facing: Discover's complete product behavior is reserved for APS-009, not yet written. Portfolio surfaces an entry point toward Discover (for example, in connection with unallocated capital) without embedding Discover's own content, ranking, or logic.

**PF-R-021.** Portfolio's relationship to **Watchlist** is deferred and future-facing: Watchlist's complete product behavior is reserved for APS-007, not yet written. Portfolio hosts a bounded, passive summary of Watchlist's own state today, governed by Section 13.

**PF-R-022.** Portfolio's relationship to **Investor Lab** is future-facing and, at present, indirect: no specification has yet been reserved for Investor Lab anywhere in the accepted sequencing. Portfolio holds no direct relationship to it today and does not anticipate one beyond the general possibility that a future Investor Lab specification may read Portfolio's own historical state, exactly as Learning (APS-004) already reads closed Decision Contexts generally.

**PF-R-023.** Portfolio's relationship to the **Atlas Priority Model** is derived and product-level, defined in full in Section 10: Portfolio's own Requires Attention category is a scoped view of this one shared model, never an independently computed ranking.

**PF-R-024.** Portfolio's relationship to future **Monitoring** and **Notifications** is future-facing and out of current scope. This specification records only that, when Monitoring is eventually specified, a monitored condition firing is the natural kind of fact the Atlas Priority Model would incorporate, and that Notifications would be a delivery channel for content Portfolio already has a canonical home for — neither claim commits this specification to any design decision for either future system.

## 9. Information Hierarchy

Stated as responsibility, not layout, per this specification's own required discipline. Four tiers, ordered by directness of resolution into *act* or *don't act* — not by screen position, which this specification does not define.

**PF-R-025.** Tier 1, **immediately action-relevant**, SHALL consist of exactly the Requires Attention category (Section 10) and the Daily Brief bounded preview (Section 13) — the smallest set of content answering *"do I need to do anything, and what has changed."*

**PF-R-026.** Tier 2, **explanatory portfolio state**, SHALL consist of the categories answering *"how is my portfolio doing"* in the aggregate — portfolio health, performance, allocation, diversification, cash, and risk context — each read from already-accepted data, none independently scored beyond what Section 16 permits.

**PF-R-027.** Tier 3, **directional or contextual**, SHALL consist of Open Review content (Section 5, Section 11) and Portfolio Conviction Distribution-style content derived from Decision confidence (PF-R-017) — content that informs a decision to investigate further without itself requiring one.

**PF-R-028.** Tier 4, **peripheral but useful**, SHALL consist of the Watchlist bounded summary (Section 13) and upcoming relevant events — content safe to skip entirely without missing anything that exists only there, per PF-R-054.

**PF-R-029.** This hierarchy SHALL NOT be read to assert a required visual order, layout, or screen position; it states which category resolves most directly into action, not where any category appears.

**PF-R-030.** A future UX specification MAY order these tiers differently in presentation, provided the underlying responsibility boundary each tier states is preserved.

## 10. The Atlas Priority Model

**PF-R-031.** The Atlas Priority Model SHALL be exactly one, shared, product-level computation of which items currently warrant the Investor's Attention, per PP-001. It SHALL be computed from already-accepted data: Decision Context state, Decision, Outcome, and, once specified, Monitoring conditions.

**PF-R-032.** Portfolio's own Requires Attention category SHALL be a scoped view of the Atlas Priority Model — specifically, the Model's output filtered to items connected to owned positions or open Decision Contexts within the Investor's own Investment Cases.

**PF-R-033.** Portfolio SHALL NOT compute an independent ranking of importance separate from the Atlas Priority Model. Any future category in Portfolio, or in any other future specification, claiming to state "what matters most" SHALL be expressed as a scoped view of this same Model, per the accepted Product Architecture Reconciliation Design.

**PF-R-034.** The Atlas Priority Model itself SHALL NOT be treated as a Product Concept requiring APP-001 acceptance. It owns no independent identity, ownership, or lifecycle beyond the computation it performs over already-accepted data; this specification defines its behavior once so that a future Watchlist, Daily Brief, or Discover specification may adopt it by reference rather than re-defining it.

**PF-R-035.** The Atlas Priority Model SHALL NOT itself constitute a Decision, a Judgment, or an act of Investor Judgment; it surfaces candidates for the Investor's own attention and nothing more, per PP-003.

## 11. Portfolio-State Presentation, Actionability, and Navigation

**PF-R-036.** Portfolio SHALL present current owned-position state, per PF-R-014's own honest limits on what "owned position" formally rests on today.

**PF-R-037.** Portfolio SHALL present aggregate portfolio state — a composed, honest read of overall status — never a gamified score presented without derivation, per PFINV-006.

**PF-R-038.** Portfolio SHALL surface portfolio health and concentration as explanatory context (Tier 2), never as an unexplained numeric score standing alone, per PF-F-007.

**PF-R-039.** Portfolio SHALL surface risk and diversification context as explanatory content, distinguishing spread (diversification) from consequence (risk) as two related but distinct categories.

**PF-R-040.** Portfolio SHALL present cash or unallocated capital when this fact is available to it, and SHALL disclose plainly when it is not, per PF-R-058.

**PF-R-041.** Portfolio SHALL surface Open Review content (Section 5) as its own direct, honest link between Portfolio and the open reasoning the Investor has not yet resolved — never silently letting an open Decision Context go unreflected in Portfolio's own aggregate state.

**PF-R-042.** Portfolio SHALL present a bounded Daily Brief preview, governed entirely by Section 13.

**PF-R-043.** Portfolio SHALL present upcoming relevant events connected to owned positions, filtered to what is genuinely relevant to those positions.

**PF-R-044.** Portfolio SHALL provide a natural navigational path from any owned position or Open Review into its own Investment Case.

**PF-R-045.** Portfolio SHALL provide a natural navigational path from an Investment Case into Decision Context and, where a Decision Context is already open, into the Decision Workspace destination that operationalizes it — without itself performing any part of that reasoning.

**PF-R-046.** Where an owned position has no associated Investment Case yet, Portfolio's own navigation into it SHALL be the same act that creates one, per PF-R-047 — never a separate, additional administrative step.

## 12. System-Created Investment Cases and No Manual Case Administration

**PF-R-047.** An Investment Case SHALL be created only upon a genuine, Investor-originated act of choosing to reason about a specific owned position or idea, consistent with the same creation discipline APS-001 already establishes for Decision Context (DC-R-017, DC-R-021).

**PF-R-048.** Portfolio SHALL NOT require the Investor to name, configure, or administratively set up an Investment Case. Its creation SHALL be a silent consequence of the Investor's own act of choosing to reason, never a separate, bureaucratic step Portfolio interposes.

**PF-R-049.** Portfolio SHALL NOT present any interface implying an Investment Case is a thing to be created independent of a genuine reasoning act — no standalone "create a Case" affordance is authorized by this specification.

**PF-R-050.** Portfolio SHALL NOT itself create, close, or reopen a Decision Context; that lifecycle remains exclusively governed by APS-001, read only by Portfolio.

## 13. Bounded Preview Governance

This specification does not define the global Preview Pattern as Product Architecture; per the accepted Product Architecture Reconciliation Design, that pattern is presentation-layer governance reserved for a future UX Doctrine authority, not this track. The requirements below state only the minimum product responsibility Portfolio itself owns when it hosts a preview of another area's content.

**PF-R-051.** Any preview Portfolio hosts of Daily Brief, Discover, or Watchlist content SHALL NOT replace that content's own destination area.

**PF-R-052.** Any preview Portfolio hosts SHALL NOT independently re-rank the content it previews; where the previewed content is priority-bearing, the preview SHALL draw its ordering from the Atlas Priority Model (Section 10), never compute its own.

**PF-R-053.** Any preview Portfolio hosts SHALL NOT fully resolve, dismiss, or otherwise complete the item it previews on the item's own destination area's behalf.

**PF-R-054.** Any preview Portfolio hosts SHALL be safe to skip entirely: no fact SHALL exist only within a Portfolio-hosted preview and nowhere in the previewed content's own destination area.

**PF-R-055.** The exact bound, ranking-integration mechanics, and presentational treatment of any preview beyond PF-R-051 through PF-R-054 remain governed by future UX authority, not by this specification.

## 14. Empty States, Incomplete Data, and User Maturity

**PF-R-056.** Portfolio SHALL present a valid, honest state for an Investor with no owned positions and no Investment Cases, stating this fact plainly rather than presenting an empty or broken-seeming surface.

**PF-R-057.** Portfolio SHALL present a valid, honest state for an Investor whose imported or entered data is incomplete, disclosing which fact is missing rather than presenting a default, inferred, or silently omitted value in its place.

**PF-R-058.** Portfolio SHALL NOT create false certainty from incomplete data; any aggregate figure computed from partial data SHALL disclose that partiality rather than presenting the figure as complete.

**PF-R-059.** Portfolio's own value to a first-time Investor SHALL NOT depend on any administrative setup step beyond the entry flow (import or build) that establishes owned positions in the first place; per APP-000 §10, Portfolio does not itself define that entry flow, and treats it as a temporary flow, not a permanent product area, per PF-R-060.
**PF-R-060.** Portfolio SHALL NOT treat "Import Portfolio" or "Build Portfolio" as permanent product areas of its own; these remain entry flows outside this specification's own scope, producing the owned-position state Portfolio then presents.

**PF-R-061.** Portfolio's own behavior for an established Investor with many owned positions and many Investment Cases SHALL scale by aggregation and prioritization (Section 9, Section 10), never by presenting every individual fact with equal prominence.

**PF-R-062.** Portfolio SHALL NOT require re-entry of any fact already captured through an entry flow or an existing record; where a fact already exists, Portfolio reads it rather than re-requesting it.

## 15. Future Multi-Portfolio Compatibility

**PF-R-063.** This specification assumes exactly one Portfolio per Investor, consistent with Atlas Alpha's current baseline scope.

**PF-R-064.** This specification SHALL NOT be read to assert that multi-portfolio support is unsupportable; it states only that this specification does not define it, per Section 24.

**PF-R-065.** No requirement in this specification SHALL be interpreted in a way that would require rework, rather than extension, should multi-portfolio support later be specified; where a requirement's own wording assumes single-portfolio scope, a future specification extending it governs that extension, not this one.

## 16. Accessibility of Meaning and Traceability

**PF-R-066.** Every aggregate or derived figure Portfolio presents SHALL be traceable to the already-accepted data it was derived from; Portfolio SHALL NOT assert a portfolio-level conclusion with no identifiable source.

**PF-R-067.** Portfolio SHALL disclose Atlas-originated content's own origin, per PP-008, wherever it presents content it did not merely read verbatim from an existing record.

**PF-R-068.** Portfolio's own presentation of meaning SHALL NOT depend on any single visual treatment, color, or layout; the underlying informational meaning of every category this specification defines SHALL remain expressible through any accessible presentation a future UX specification defines.

## 17. Explicit Exclusions

**PF-R-069.** Portfolio SHALL NOT become a stock screener. Screening finds candidates across a universe the Investor does not own; that responsibility belongs to Discover (APS-009, deferred). Portfolio only ever presents what is already owned or already reasoned about.

**PF-R-070.** Portfolio SHALL NOT become a market-news feed. News is externally sourced and high-volume; Portfolio's own obligation is synthesized, low-volume, high-signal content connected to owned positions, per PF-R-025.

**PF-R-071.** Portfolio SHALL NOT become Discover. Discover's own responsibility — sourcing opportunity outside the owned set — belongs exclusively to APS-009; Portfolio only surfaces an entry point toward it, per PF-R-020.

**PF-R-072.** Portfolio SHALL NOT become Watchlist. Watchlist's own responsibility — zero-commitment staging of tracked-but-unowned items — belongs exclusively to APS-007; Portfolio only hosts a bounded, passive summary of it, per PF-R-021.

**PF-R-073.** Portfolio SHALL NOT become Daily Brief. Daily Brief's own responsibility — a temporal delta narrative since the Investor's last visit — belongs exclusively to APS-008; Portfolio only hosts a bounded preview of it, per PF-R-019.

**PF-R-074.** Portfolio SHALL NOT become Decision Workspace. Reasoning is performed, structured, and permanently recorded through Decision Context and its own governing specification (APS-001, APS-002); Portfolio never lets the Investor record an Observation, a Judgment, or a Decision directly, per PF-R-004.

**PF-R-075.** Portfolio SHALL NOT become Investor Lab. Investor Lab looks backward across the Investor's own decision-making patterns over time; Portfolio looks at the present state of owned positions. These are different cognitive modes and remain separate areas, per PF-R-022.

**PF-R-076.** Portfolio SHALL NOT become a research terminal. Deep, open-ended investigation of a specific security belongs to Decision Workspace, entered deliberately with a real Investment Case behind it, never to Portfolio's own ambient presentation.

**PF-R-077.** Portfolio SHALL NOT become a broker or trade-execution interface. The presence of an owned position or a recorded Decision in Portfolio SHALL NOT be conflated with the capacity, or the intent, to execute a trade, per `ATLAS_CONSTITUTION.md`'s own Non-Negotiable Principles.

**PF-R-078.** Portfolio SHALL NOT become a tax product in the current scope. Tax-relevant computation and presentation is out of scope for this specification and for the current Alpha baseline generally; this specification does not name an eventual attachment point, since doing so is future architectural work this specification does not perform.

## 18. Atlas Responsibilities

**PF-R-079.** Atlas SHALL compute Portfolio's own aggregate categories (Section 9, Section 11) from already-accepted data, without originating any new Core Domain Object or Product record in the process, per PF-R-008.

**PF-R-080.** Atlas SHALL populate Requires Attention from the Atlas Priority Model, per Section 10, never from an independently computed ranking.

**PF-R-081.** Atlas SHALL create an Investment Case silently, at the moment the Investor's own act of choosing to reason occurs, per PF-R-047 through PF-R-049.

**PF-R-082.** Atlas SHALL disclose incomplete or unavailable data explicitly, per PF-R-057 and PF-R-058, rather than presenting a default value or silently omitting the gap.

**PF-R-083.** Atlas SHALL preserve the read-only boundary stated in PF-R-010 in every computation Portfolio performs; no Portfolio-level computation SHALL alter a Core Domain Object or an already-accepted Product record.

**PF-R-084.** Atlas SHALL attribute the origin of any Atlas-originated content Portfolio presents, per PP-008 and PF-R-067.

## 19. Investor Responsibilities

**PF-R-085.** The Investor owns every Investment Case Portfolio's own act of navigation creates, per APP-001 §3.13's own ownership statement.

**PF-R-086.** The Investor remains responsible for deciding whether a Requires Attention item warrants action; Portfolio surfaces the item, never the decision, per PP-003.

**PF-R-087.** The Investor remains accountable for any Decision reached after navigating from Portfolio into a Decision Context, in the same manner APP-000 §8.2 already states generally.

## 20. Invariants

**PFINV-001 — No Core Object Status.** Portfolio SHALL NOT be treated as a Core Domain Object or as Core-reference-eligible.

**PFINV-002 — Distinctness from Investment Case and Decision Context.** Portfolio SHALL NOT be treated as identical to, or a replacement for, Investment Case or Decision Context.

**PFINV-003 — No Deep Reasoning Ownership.** Portfolio SHALL NOT own or perform Reasoning, Investor Judgment, Decision recording, or Decision Quality evaluation.

**PFINV-004 — Single Priority Model.** Portfolio SHALL NOT create an independent priority or ranking model separate from the Atlas Priority Model (Section 10).

**PFINV-005 — No Manual Case Administration.** Portfolio SHALL NOT require the Investor to manually create, name, or configure an Investment Case.

**PFINV-006 — Previews Are Not Destinations.** A bounded preview Portfolio hosts SHALL NOT be treated as the complete destination for the content it previews.

**PFINV-007 — Traceable Conclusions.** Portfolio SHALL NOT assert a portfolio-level conclusion without an identifiable source or derivation from already-accepted data.

**PFINV-008 — Honest Incompleteness.** Portfolio SHALL NOT obscure, silently omit, or default-fill incomplete or unavailable data.

**PFINV-009 — Distinct from Daily Brief.** Portfolio's own state presentation SHALL remain distinct from Daily Brief's own delta-since-last-visit responsibility; Portfolio answers "where do I stand," never "what changed."

**PFINV-010 — Distinct from Discover.** Portfolio's own content SHALL remain scoped to owned positions and existing Investment Cases; it SHALL NOT include candidates from outside that owned set, which remains Discover's own responsibility.

**PFINV-011 — Read-Only Relationship to Core and Product Records.** Portfolio SHALL NOT mutate any Investment Case, Decision Context, Decision, Outcome, or Core Domain Object it reads.

**PFINV-012 — No Autonomous Commitment.** Portfolio SHALL NOT cause a Decision Context to close by Commitment, and SHALL NOT present any Portfolio-level action as though it had done so, per APS-001 DCINV-006.

**PFINV-013 — No New Core Relationship.** This specification, and Portfolio as it governs, SHALL NOT introduce or rely upon a Core relationship, Core Domain Object, or Core invariant beyond those already adopted in `OE-002` and `OE-004`.

**PFINV-014 — Evidence Remains Product-Layer Only.** This specification SHALL NOT describe Evidence as a Core Domain Object anywhere it is mentioned, per APS-003 EV-R-002 and `OE-002` §4's own closed Domain Object Set.

## 21. Failure and Refusal Behavior

Atlas SHALL fail closed: where continuing would violate this specification, APP-000, APP-001, APS-001, or a Core invariant, Atlas SHALL refuse or halt the action rather than proceed on an assumed or inferred basis. No UI error message is prescribed by this section or by this specification.

**PF-F-001 — Portfolio would present owned positions with no prioritization.** Atlas SHALL NOT ship a Portfolio surface that presents every owned position with equal, unranked prominence; this violates PF-R-025 and Tier 1's own purpose of resolving directly into action.

**PF-F-002 — Portfolio would become a dashboard crowded with unrelated metrics.** Atlas SHALL refuse to add a category to Portfolio that does not serve the central question "where do I stand," per PF-R-012; an unrelated metric degrades the Investor's Attention, per PP-001.

**PF-F-003 — A Portfolio-hosted preview would duplicate Daily Brief's own full content.** Atlas SHALL refuse to expand a Daily Brief preview beyond a bounded preview, per PF-R-051 through PF-R-055; duplicating the destination's own content violates PFINV-006 and the exclusion in PF-R-073.

**PF-F-004 — A Portfolio-hosted preview would duplicate Discover's own full content.** Atlas SHALL refuse, for the same reason as PF-F-003, applied to the exclusion in PF-R-071.

**PF-F-005 — Portfolio would present conflicting priority signals.** Atlas SHALL refuse to compute or display a ranking independent of the Atlas Priority Model; this violates PFINV-004 directly.

**PF-F-006 — Portfolio would create false certainty from incomplete data.** Atlas SHALL disclose the incompleteness rather than present a computed aggregate as though it were complete, per PFINV-008.

**PF-F-007 — Portfolio would require manual administrative setup before delivering value.** Atlas SHALL refuse to interpose a setup step beyond the entry flow that establishes owned positions, per PF-R-059 and PF-R-062.

**PF-F-008 — Portfolio would treat portfolio health as an unexplained score.** Atlas SHALL refuse to present portfolio health, or any aggregate figure, without the traceable derivation PFINV-007 requires.

**PF-F-009 — Portfolio would make every item look urgent.** Atlas SHALL refuse to present Tier 2 through Tier 4 content with Tier 1's own visual or narrative urgency; conflating urgency levels degrades the Investor's ability to answer "do I need to do anything," per PF-R-025.

**PF-F-010 — Portfolio would hide the absence of meaningful change.** Atlas SHALL state plainly when nothing requires attention, per PF-R-056's own honest-empty-state discipline extended to the ordinary, non-empty case; a quiet, accurate "nothing needs you" is a successful state, not a state to be filled with unrelated content.

**PF-F-011 — An Investment Case would be conflated with a single Decision Context.** Atlas SHALL NOT present an Investment Case's own Open Review content as though the Investment Case itself were the reasoning episode; the Investment Case may enclose several Decision Contexts over its lifetime, per APP-001 §3.13 Cardinality, and PFINV-002 requires the distinction be preserved.

**PF-F-012 — Portfolio would autonomously close a Decision Context.** Atlas SHALL refuse any action that would cause a Decision Context to close by Commitment without an identifiable Investor act, per PFINV-012 and APS-001 DCINV-006.

## 22. Acceptance Criteria

**PF-AC-001 (Central question).** Portfolio's own content is observed to resolve, for a returning Investor, the question "where do I stand," without requiring navigation to another area first, per PF-R-012.

**PF-AC-002 (Fast orientation).** A returning Investor can state whether action is required from Portfolio's own Tier 1 content alone, per PF-R-025.

**PF-AC-003 (Attention resolution).** Every item Portfolio presents in Requires Attention traces to the Atlas Priority Model's own output, per PF-R-032 and PFINV-004; no item is ever observed with an independently computed priority.

**PF-AC-004 (Distinct from Daily Brief).** No content unique to Daily Brief's own full responsibility (a complete delta narrative since last visit) is ever observed presented in full within Portfolio; only a bounded preview is observed, per PFINV-009 and PF-R-051 through PF-R-055.

**PF-AC-005 (Distinct from Discover).** No candidate from outside the Investor's own owned positions and existing Investment Cases is ever observed presented as Portfolio content, per PFINV-010.

**PF-AC-006 (System-created Investment Cases).** Every Investment Case observed to exist as a consequence of Portfolio navigation is traceable to a genuine Investor act of choosing to reason, per PF-R-047 and PF-R-081; no Investment Case is ever observed created by mere navigation or product-opening alone.

**PF-AC-007 (Open work terminology).** Every reference to unfinished reasoning within Portfolio is observed expressed in terms of an open Decision Context, never as an ambiguous restatement of Investment Case status, per PF-R-011's own definition and PF-F-011.

**PF-AC-008 (Previews are not destinations).** Every bounded preview Portfolio hosts is observed to link to its own destination area and is never observed as the sole presentation of the content it previews, per PFINV-006.

**PF-AC-009 (Single priority model).** No second, independently computed ranking of importance is ever observed anywhere within Portfolio's own content, per PFINV-004.

**PF-AC-010 (Honest incompleteness).** Every aggregate figure computed from incomplete data is observed accompanied by an explicit disclosure of that incompleteness, per PFINV-008.

**PF-AC-011 (No Core or Decision Engine redesign).** No requirement in this specification is observed to require a new Core Domain Object, a new Core invariant, or a change to the Decision Engine's own existing behavior, per PFINV-001, PFINV-003, and PFINV-013.

**PF-AC-012 (Traceability).** Every requirement in Sections 6 through 19 is traceable, by citation, to at least one of: `ATLAS_CONSTITUTION.md`, an APP-000 Product Principle, an APP-001 provision, an APS-001 provision, or a Core same-Case requirement, per Section 23.

## 23. Traceability

This section distinguishes normative basis from non-normative source material for every requirement and invariant group, per this specification's own required discipline against citing a standalone artifact as though it already held repository authority.

| Requirement / Invariant | Normative basis | Source material (non-normative) | Core basis | Core basis status |
|---|---|---|---|---|
| PF-R-001–006, PFINV-001, PFINV-013 | APP-000 §2, §9; APP-001 §1 | — | `OE-002` §4 (closed Domain Object Set excludes Portfolio) | Normative (Core) |
| PF-R-007–012 | APP-001 §3.13 (Investment Case, Relationships clause); `ATLAS_CONSTITUTION.md` ("Portfolio before position") | Portfolio Control Center §1 (Purpose) | — | — |
| PF-R-013–024, PFINV-002, PFINV-009, PFINV-010 | APP-001 §3.13, §4 | Portfolio Control Center §6 (Navigation role); Entry Flows §2, §4 (area relationships, adopted as reconciled) | `OE-002` §3.1 Case, via Investment Case | Normative (Core), cited not redefined |
| PF-R-025–030 | PP-001, PP-004 | Portfolio Control Center §4 (Information hierarchy) | — | Reconciliation Design source material, restated normatively |
| PF-R-031–035, PFINV-004 | PP-001, PP-003 | Architecture Resolutions, Decision 2 (Atlas Priority Model) | — | Accepted reconciliation input, restated normatively here for the first time in the real lineage |
| PF-R-036–046 | PP-001, PP-002, PP-006 | Portfolio Control Center §4, §7 (User flows) | `OE-002` §5.5 Decision, §5.6 Outcome | Normative (Core), cited not redefined |
| PF-R-047–050, PFINV-005, PFINV-012 | PP-002, PP-003, PP-005 | Entry Flows §3 (system-created Case rule), adopted as reconciled | APS-001 DC-R-017, DC-R-021, DCINV-006 | Normative (Product), cited not redefined |
| PF-R-051–055, PFINV-006 | — | Architecture Resolutions, Decision 3 (Preview Pattern) — presentation-layer authority explicitly not claimed here | — | Accepted reconciliation input; product responsibility only, per Reconciliation Design ruling |
| PF-R-056–062 | PP-004; APP-000 §10 | Portfolio Control Center §7, §9 (flows, success criteria) | — | — |
| PF-R-063–065 | — | Product Architecture Review, Section 7 (Scalability); Reconciliation Design Open Questions | — | This specification's own product decision |
| PF-R-066–068 | PP-007, PP-008 | — | — | — |
| PF-R-069–078, PFINV-014 | APP-000 §10; `ATLAS_CONSTITUTION.md` Non-Negotiable Principles | Portfolio Control Center §5 (Must not become) | `OE-002` §4 (Evidence excluded); APS-003 EV-R-002 | Normative (Core) for Evidence's own status |
| PF-R-079–087 | PP-001 through PP-009, as cited per line; APP-000 §8.2 | Portfolio Control Center §8 (Responsibilities) | — | — |
| PFINV-003, PFINV-007, PFINV-008, PFINV-011 | PP-006, PP-007, PP-009 | Portfolio Control Center §9 (Success criteria); Product Architecture Review Weaknesses | — | This specification's own product decision |

## 24. Open Questions and Deferred Work

- **Portfolio health and risk computation method.** Not defined here; this specification states what question each category answers and why it belongs, never how the underlying figure is computed. Classified: **non-blocking for APS-006** — implementation and calibration work for a future, dedicated task.
- **Multi-portfolio compatibility.** Named repeatedly across the Phase II source material as deferred; this specification assumes single-portfolio scope throughout (Section 15). Classified: **requires separate architecture work** — a dedicated future Product Architecture task, not this specification's own authority to resolve.
- **Asset-manager multi-mandate requirements.** Coupled to multi-portfolio compatibility; same classification: **requires separate architecture work**, non-blocking for this specification's own completeness.
- **Whether "Holding" or "owned position" requires later formal Product Concept treatment.** Genuinely open. This specification describes Portfolio's owned-position responsibility without promoting the term into a Product Concept, per PF-R-014. Classified: **deferred** — a candidate for a future, dedicated APP-001 amendment, which this specification has no authority to propose or enact.
- **Concurrent Decision Contexts within one Investment Case.** APS-001 does not state whether two Decision Contexts may be concurrently open within the same enclosing Case. This specification's own Open Review requirements (PF-R-041, PF-F-011) are written to remain valid under either resolution — a single Investment Case's Open Review content may show one or several entries without any requirement in this document changing. Classified: **non-blocking for APS-006**, but genuinely relevant to Portfolio's own eventual presentation depth; resolution remains APS-001's own authority, not this specification's.

---

*This specification does not modify `ATLAS_CONSTITUTION.md`, `Architecture-Governance.md`, `Atlas-Alpha-Baseline-v1.0.md`, APP-000, APP-001, APS-001 through APS-005, any `docs/atlas_ux/` document, or any source code. It introduces no new Core Domain Object and requires no Atlas Core or Decision Engine redesign.*
