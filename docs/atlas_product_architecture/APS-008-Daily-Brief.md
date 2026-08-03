# APS-008 — Daily Brief

**Status:** Draft, v0.1. This is the eighth Atlas Product Specification, subordinate to APP-000 — Atlas Product Doctrine and APP-001 — Atlas Product Concept Taxonomy (v0.4), and depending on APS-001 — Decision Context, APS-006 — Portfolio, and APS-007 — Watchlist. It states the complete normative product behavior of Daily Brief: the product surface responsible for communicating meaningful change since the Investor last reviewed Atlas. It does not describe screens, workflows, visual design, interaction design, algorithms, data schemas, persistence mechanisms, or any other implementation technique, and it does not redefine Core ontology.

---

## 1. Governance Metadata

Stated here in full, per `Architecture-Governance.md` §10's own requirement, matching the pattern APS-006 §1 and APS-007 §1 already established.

- **Document identifier:** APS-008.
- **Title:** Daily Brief.
- **Version:** v0.1.
- **Status:** Draft — the smallest truthful status available to a newly authored specification, matching APS-001 through APS-007 at their own first publication.
- **Parent authority:** APP-000 — Atlas Product Doctrine (Draft v0.4); APP-001 — Atlas Product Concept Taxonomy (Draft v0.4), specifically §4 (Daily Brief's own newly-recorded deferral) and §9 item 9 (Daily Brief reserved for this specification).
- **Dependencies:** APS-001 — Decision Context (Draft v0.1), for the lifecycle Daily Brief reads but never alters. APS-006 — Portfolio (Draft v0.1), for the Atlas Priority Model it adopts by reference and for the relationship in which Portfolio hosts a bounded preview of Daily Brief. APS-007 — Watchlist (Draft v0.1), for the relationship in which Daily Brief hosts a bounded preview of Watchlist.
- **Scope:** Daily Brief's own identity, ownership, responsibilities, relationships to Portfolio, Watchlist, Discover, Investment Case, Decision Context, Decision, Outcome, Investor Lab, the Atlas Priority Model, and future Monitoring, Signals, and Notifications; its exclusions; and the Atlas/Investor responsibility split.
- **Non-scope:** Screens, workflows, navigation, visual design, interaction design, implementation, algorithms, data schemas, persistence mechanisms; Discover's own complete product behavior (reserved for APS-009, not yet written); any amendment to APP-000, APP-001, APS-001 through APS-007, Atlas Core, or `docs/atlas_ux/`.
- **Affected documents:** None requiring amendment. `APP-001` already reserved this territory in its own v0.4 amendment (§4, §9) and requires no further change.
- **Superseded documents:** None, in the formal sense `Architecture-Governance.md` §7 defines. The Phase II "Daily Brief" product specification is this document's own primary source material, but it was never committed to this repository; §7's Supersession Notice mechanism does not apply to a document that was never itself a repository document.
- **Migration requirements:** None. No existing repository document, and no implementation, is required to change as a consequence of this document's creation.

## 2. Purpose

Daily Brief requires its own specification because APP-001 §4 names it as newly-recorded deferred territory but does not itself state Daily Brief's product behavior. This specification closes that gap: it states Daily Brief's own identity as the product surface responsible for communicating meaningful change — never comprehensive information — since the Investor last reviewed Atlas, its responsibilities, its relationships, and its boundary against every neighboring area, so that a future UX specification, an implementation design, engineering, QA, and any AI agent working on Atlas can build from it without inventing new Daily Brief product rules of their own.

Daily Brief's own central user question is *"what has changed since I last looked?"* — a temporal, delta question, distinct from Portfolio's own snapshot question "where do I stand" (APS-006 §2) and from Watchlist's own "what should I continue following" (APS-007 §2).

This specification is re-derived from the Phase II "Daily Brief" product specification, the Product Architecture Review, and Architecture Resolutions — three source documents that were never committed to this repository and hold no independent authority of their own. Their valid product decisions are translated, not copied, into this specification's own requirements.

## 3. Scope

In scope: Daily Brief's identity as a product-level surface; its ownership and responsibility boundary; its relationship to Portfolio, Watchlist, Discover, Investment Case, Decision Context, Decision, Outcome, Investor Lab, the Atlas Priority Model, and future Monitoring, Signals, and Notifications; meaningful change and relevance filtering; delta presentation; review routing; thesis-impacting change; bounded previews in both directions Daily Brief participates in; completed monitoring communication; boundedness and repeat-visit behavior; empty brief and user-maturity behavior; and the Atlas/Investor responsibility split.

Out of scope, per APP-000 §1 and §10: screens, workflows, navigation, visual design, interaction design, algorithms, data schemas, persistence mechanisms, or any other implementation technique. Also out of scope: Discover's own complete product behavior (reserved for APS-009, not yet written); the exact relevance-filtering algorithm or threshold (Section 28); multi-portfolio compatibility (Section 20, Section 28); Monitoring's and Notifications' own complete product behavior, neither yet specified anywhere; and any resolution of the Core-track Evidence discrepancy, which this specification does not reopen.

## 4. Governing References

- **`ATLAS_CONSTITUTION.md`.** Normative, superior to every document in the Atlas Product Architecture track.
- **APP-000 — Atlas Product Doctrine, Draft v0.4.** Normative, superior to this specification.
- **APP-001 — Atlas Product Concept Taxonomy, Draft v0.4.** Normative, superior to this specification; §4 reaffirms Daily Brief's own deferral and names this specification as its subject; §9 item 9 reserves this specification's own sequencing position.
- **APS-001 — Decision Context, Draft v0.1.** Normative, superior to this specification; governs the lifecycle Daily Brief reads from but never alters (Section 7, Section 8).
- **APS-006 — Portfolio, Draft v0.1.** Normative, superior to this specification; defines the Atlas Priority Model (§10) this specification adopts by reference (Section 11); its own §13 states, from the hosting side, the bounded-preview relationship in which Portfolio previews Daily Brief (Section 15).
- **APS-007 — Watchlist, Draft v0.1.** Normative, superior to this specification; its own §13 anticipates, and its WL-R-037 through WL-R-039 state, exactly the content Watchlist exposes for Daily Brief's own bounded preview of it (Section 14).
- **`OE-002` — Domain Object Model, Final.** Normative for Atlas Core; confirms Daily Brief introduces no new Domain Object (Section 6).
- **The Product Architecture Reconciliation Design** (accepted, this repository's own prior governance work). Non-normative in the sense that it is not itself a Product Architecture document — cited as the source of the migration sequencing that places this specification after APS-007 and before APS-009.
- **The Phase II "Daily Brief" product specification.** Non-normative source material only, never committed to this repository, holding no authority of its own. Its ten information categories, six user flows, and success criteria are translated, not copied, into this specification's own requirements.
- **The Phase II "Product Architecture Review" and "Architecture Resolutions."** Non-normative source material only, for the same reason. The Atlas Priority Model and the bounded-preview discipline originate in Architecture Resolutions' own analysis, already adopted as accepted architecture in APS-006 §10 and §13, and reused here by reference rather than restated as independent authority.

## 5. Definitions

Only concepts not already defined by APP-000, APP-001, APS-001, APS-006, or APS-007 are defined here.

**Delta.** The set of facts that are new or materially changed, concerning owned positions, followed Watchlist Entries, or open Investment Cases, since the Investor's own last visit to Daily Brief. The organizing temporal frame of this entire specification.

**Verdict.** Daily Brief's own top-line answer to "does anything require attention" — a temporally-filtered, scoped view of the Atlas Priority Model (APS-006 §10), never an independently computed signal. Defined in full in Section 11.

**Thesis-Impacting Change.** Ordinary-language description of new information — typically a new Evidence Instance (APS-003) or Observation — that appears to qualify, support, or contradict the Investor Reasoning (APS-002) or Decision already recorded within an open or closed Decision Context. Not a formal Product Concept; no independent identity, ownership, lifecycle, or responsibility is asserted for it by this specification, mirroring APS-006's own treatment of "owned position" and APS-007's own treatment of "Watchlist Entry." Defined in full in Section 13.

**Discover Highlight.** A bounded preview, hosted by Daily Brief, of a small number of candidates Discover has surfaced. Governed by Section 14; deferred and future-facing, since Discover's own complete product behavior is reserved for APS-009, not yet written.

**Watchlist Update.** A bounded preview, hosted by Daily Brief, of what has changed among the Investor's own Watchlist Entries since last visit. Governed by Section 14; reads Watchlist's own exposed state, per APS-007 WL-R-037 through WL-R-039.

**Completed Monitoring.** An entry confirming that a monitored condition was checked and found nothing requiring attention. Governed by Section 16; deferred and future-facing, since Monitoring's own complete product behavior is not yet specified anywhere.

## 6. Architectural Position

**DB-R-001.** Daily Brief SHALL be subordinate to APP-000, APP-001, APS-001, APS-006, and APS-007; it SHALL NOT contradict any of the five or redefine a term any of them defines.

**DB-R-002.** Daily Brief SHALL NOT be treated as a Core Domain Object, and SHALL NOT be, or be treated as, reference-eligible within Atlas Core.

**DB-R-003.** Daily Brief SHALL NOT be treated as identical to, or a replacement for, Portfolio, Discover, Watchlist, Investment Case, or Decision Context.

**DB-R-004.** Daily Brief SHALL NOT be treated as a Decision Engine concept. It does not perform Reasoning, does not exercise Investor Judgment, does not record a Decision, and does not evaluate Decision Quality.

**DB-R-005.** Daily Brief SHALL NOT be treated as a pure UX artifact carrying no Product responsibility. It owns real product responsibility, stated in Section 8 through Section 16.

**DB-R-006.** Daily Brief SHALL NOT introduce a new Core Domain Object. Where Core has no adopted primitive for a fact Daily Brief needs to present, that gap is recorded as an open question (Section 28), never silently resolved by this specification.

## 7. Core Properties and Ownership

**DB-R-007.** Daily Brief SHALL be owned by the Investor, in the same sense Portfolio and Watchlist are Investor-owned (APS-006 §7, APS-007 §7).

**DB-R-008.** Daily Brief SHALL derive its own content entirely by reading already-accepted Product Concepts and Core Domain Objects, filtered by the Delta (Section 5). It SHALL NOT originate a Decision, a Judgment, an Outcome, an Observation, or any other Core Domain Object.

**DB-R-009.** Daily Brief SHALL answer a temporal question — what changed since the Investor's own last visit — never a snapshot question; this is Daily Brief's own defining distinction from Portfolio (APS-006 §2), stated here as this specification's own architectural position, not merely as a philosophical preference.

**DB-R-010.** Daily Brief SHALL NOT alter, mutate, or supersede any Investment Case, Decision Context, Decision, Outcome, or Watchlist Entry it reads. Every relationship Daily Brief holds to these concepts is read-only.

**DB-R-011.** Daily Brief SHALL NOT require the existence of a Decision Context, an owned position, or a Watchlist Entry to have some content to present; an Investor with none of these remains a valid, presentable Daily Brief state (Section 18, empty and early states).

**DB-R-012.** Daily Brief's own central user question — *"What has changed since I last looked?"* — SHALL govern every category of content this specification defines. A category that does not serve this question does not belong in Daily Brief, regardless of its own informational value.

**DB-R-013.** Daily Brief SHALL remain bounded and finishable; no requirement in this specification SHALL be read to authorize unbounded, continuously-scrolling, or engagement-optimized content, per Section 17.

## 8. Concept Relationships

Each relationship below is classified as existing, derived, product-level, deferred, future-facing, or not applicable, per this specification's own required precision.

**DB-R-014.** Daily Brief's relationship to **Portfolio** is existing and product-level, and runs in both directions: Daily Brief reads the same underlying state Portfolio reads (Investment Cases, Decision Contexts, Decisions, Outcomes), filtered temporally by the Delta; and Portfolio hosts a bounded preview of Daily Brief's own content, per APS-006 PF-R-019, PF-R-025, and PF-R-042 — Daily Brief is the previewed party in that one relationship, governed from this side in Section 15.

**DB-R-015.** Daily Brief's relationship to **Watchlist** is existing and product-level: Daily Brief hosts a bounded Watchlist Update preview, reading the state Watchlist exposes for exactly this purpose, per APS-007 WL-R-013 and WL-R-037 through WL-R-039. Daily Brief is the hosting party in this relationship, governed from this side in Section 14.

**DB-R-016.** Daily Brief's relationship to **Discover** is deferred and future-facing: Discover's complete product behavior is reserved for APS-009, not yet written. Daily Brief anticipates hosting a bounded Discover Highlight preview, governed by the same bounded-preview discipline this specification establishes (Section 14); this specification does not itself define Discover's own content or ranking.

**DB-R-017.** Daily Brief's relationship to **Investment Case** is existing and product-level: Daily Brief reads across Investment Cases the same way Portfolio does, filtered to what has changed since last visit, per APP-001 §3.13's own Relationships clause extended to a temporal reading.

**DB-R-018.** Daily Brief's relationship to **Decision Context** is existing and product-level: Daily Brief's own review-routing content (Section 12) reads Decision Contexts whose state has newly changed — newly opened, or newly the subject of a Thesis-Impacting Change (Section 13) — since last visit, per APS-001 §9 through §13. Daily Brief SHALL NOT itself create, close, or reopen a Decision Context.

**DB-R-019.** Daily Brief's relationship to **Decision** is existing and derived: Daily Brief MAY reflect a Decision recorded since last visit as part of the Delta; it never originates or alters a Decision, per DB-R-008.

**DB-R-020.** Daily Brief's relationship to **Outcome** is existing and derived: Daily Brief MAY reflect an Outcome recorded since last visit; per `ORINV-016`, Daily Brief SHALL NOT characterize Decision Quality by reference to Outcome, whether alone or in aggregate.

**DB-R-021.** Daily Brief's relationship to **Investor Lab** is future-facing and, at present, indirect, mirroring APS-006 PF-R-022 and APS-007 WL-R-019: no specification has yet been reserved for Investor Lab. Daily Brief holds no direct relationship to it today.

**DB-R-022.** Daily Brief's relationship to the **Atlas Priority Model** (APS-006 §10) is derived and product-level: Daily Brief's own Verdict (Section 11) is a temporally-scoped view of this one shared model, never an independently computed ranking, per PF-R-034's own explicit invitation for future specifications to adopt it by reference.

**DB-R-023.** Daily Brief's relationship to future **Monitoring** is future-facing and out of current scope. This specification records only that a monitored condition firing, once Monitoring is specified, is the natural kind of fact the Atlas Priority Model would incorporate, and that a monitored condition checked with nothing to report is the natural content of Completed Monitoring (Section 16) — neither claim commits this specification to any design decision for Monitoring itself.

**DB-R-024.** Daily Brief's relationship to future **Signals** is future-facing and out of current scope, mirroring APS-007 WL-R-021: a Signal, once specified, would be a prompt toward a candidate the Atlas Priority Model might incorporate — never an autonomous act on Daily Brief's own behalf.

**DB-R-025.** Daily Brief's relationship to future **Notifications** is future-facing and out of current scope, mirroring APS-006 PF-R-024: a Notification would be a delivery channel for Daily Brief's own already-canonical content, never a parallel or independent content system. Daily Brief SHALL NOT be treated as, or reduced to, a notification inbox, per Section 21.

## 9. Meaningful Change and Relevance Filtering

**DB-R-026.** Daily Brief SHALL report a fact only because of its connection to an owned position, a followed Watchlist Entry, or an open or recently-closed Investment Case; a fact with no such connection SHALL NOT appear in Daily Brief regardless of its own general significance.

**DB-R-027.** Daily Brief SHALL prefer relevance over completeness; this specification explicitly accepts that a genuinely significant fact with no connection under DB-R-026 will not appear, in exchange for never burying a connected fact under volume that isn't.

**DB-R-028.** Daily Brief SHALL NOT justify including a fact solely on the grounds that the underlying information exists or is available, per PP-001.

**DB-R-029.** Daily Brief SHALL filter every candidate fact before presentation; unfiltered, unranked presentation of everything that changed is a failure mode, per Section 25.

**DB-R-030.** The exact computational method by which relevance is determined is not defined by this specification; Section 9's own requirements state what qualifies, not how qualification is computed. See Section 28.

**DB-R-031.** Daily Brief SHALL NOT report a fact merely because it is new; the Delta (Section 5) is a necessary, not sufficient, condition for inclusion — the connection required by DB-R-026 remains independently required.

**DB-R-032.** Daily Brief SHALL NOT report a fact already reported in a prior visit's own Brief unless that fact has itself materially changed again since it was last reported; see Section 17 for the full repeat-visit discipline.

**DB-R-033.** Where a genuinely new development has no clean connection under DB-R-026 but is closely adjacent to one (for example, a macro event affecting a sector the Investor holds), Daily Brief MAY report it, but only through the lens of the specific owned position or followed Entry it affects — never as an independent market update.

## 10. Delta Presentation and Information Hierarchy

Stated as responsibility, not layout, mirroring APS-006 §9's own discipline. Four tiers, ordered by directness of resolution into *act* or *don't act*.

**DB-R-034.** Tier 1, **the Verdict**, SHALL consist of exactly the content defined in Section 11 — the smallest set of content answering *"does anything require my attention, right now."*

**DB-R-035.** Tier 2, **the story of what changed**, SHALL consist of the categories translating the Delta into meaning connected to the Investor's own exposure — never a raw list of events, always run through the lens of what it means for a specific owned position or followed Entry, per DB-R-033.

**DB-R-036.** Tier 3, **where to look next**, SHALL consist of review-routing content (Section 12) and Watchlist Update content (Section 14) — content that informs a decision to investigate further without itself requiring one.

**DB-R-037.** Tier 4, **periphery**, SHALL consist of Discover Highlight content (Section 14) and Completed Monitoring content (Section 16) — content safe to skip entirely without missing anything that exists only there, per DB-R-064.

**DB-R-038.** This hierarchy SHALL NOT be read to assert a required visual order, layout, or screen position; it states which category resolves most directly into action, not where any category appears.

**DB-R-039.** A future UX specification MAY order these tiers differently in presentation, provided the underlying responsibility boundary each tier states is preserved.

**DB-R-040.** Every tier SHALL remain subject to the boundedness discipline of Section 17; no tier is exempt from Daily Brief's own finishability requirement.

**DB-R-041.** Where a tier has no content on a given visit, Daily Brief SHALL state this plainly rather than omitting the tier silently or presenting an ambiguous absence, per DB-F-002 and Section 26.

## 11. Priority Model Integration — The Verdict

**DB-R-042.** The Verdict SHALL be a temporally-scoped view of the Atlas Priority Model (APS-006 §10): the Model's own output, filtered to items that are new or newly relevant since the Investor's own last visit.

**DB-R-043.** Daily Brief SHALL NOT compute an independent ranking of importance separate from the Atlas Priority Model. Any category in Daily Brief claiming to state "what matters most right now" SHALL be expressed as a scoped view of the same Model Portfolio's own Requires Attention already reads from, per APS-006 PF-R-032 through PF-R-034.

**DB-R-044.** Where the Verdict and Portfolio's own Requires Attention category present the same underlying item, they SHALL NOT be permitted to disagree about the fact itself; they MAY differ only in framing — current status (Portfolio) versus newly-changed (Daily Brief) — per APS-006 PFINV-009.

**DB-R-045.** The Verdict SHALL NOT itself constitute a Decision, a Judgment, or an act of Investor Judgment; it surfaces candidates for the Investor's own attention and nothing more, per PP-003.

**DB-R-046.** An empty Verdict — nothing currently requires attention — SHALL be treated as a legitimate, successful state, per Section 18 and `DBINV-011`.

**DB-R-047.** Daily Brief SHALL NOT fabricate a Verdict item to avoid appearing empty, per PP-007 and DB-F-002.

## 12. Review Routing

**DB-R-048.** Daily Brief SHALL provide a natural navigational path from any Delta-connected owned position into its own Investment Case.

**DB-R-049.** Daily Brief SHALL provide a natural navigational path from a Decision Context whose state has newly changed into that Decision Context itself, or into the Decision Workspace destination that operationalizes it — without itself performing any part of that reasoning, per DB-R-004.

**DB-R-050.** Every reference within Daily Brief to unfinished reasoning SHALL be expressed in terms of a Decision Context — open, newly opened, or newly the subject of a Thesis-Impacting Change — never as an ambiguous restatement of Investment Case status, mirroring APS-006 PF-F-011's own discipline against conflating the two.

**DB-R-051.** Where a Watchlist Entry's own progression into an Investment Case (APS-007 §9) occurred since last visit, Daily Brief MAY reflect that progression as part of the Delta; Daily Brief itself never performs or triggers the progression.

**DB-R-052.** Daily Brief SHALL NOT let the Investor record an Observation, a Judgment, or a Decision directly from within Daily Brief; every path from Daily Brief into real reasoning routes through the Investment Case or Decision Context it names, per DB-R-004 and Section 21.

**DB-R-053.** Where routing from Daily Brief would require creating a new Investment Case (for example, from a Thesis-Impacting Change concerning a position with no open Investment Case), that creation SHALL follow the same silent, genuine-intent creation discipline APS-006 PF-R-047 already establishes; Daily Brief SHALL NOT interpose an additional administrative step.

## 13. Thesis-Impacting Change

**DB-R-054.** Daily Brief MAY identify a Thesis-Impacting Change by comparing new Evidence or a new Observation, connected to an owned position or followed Entry, against the Investor Reasoning or Decision already recorded within an existing Decision Context concerning that same subject.

**DB-R-055.** Identifying a Thesis-Impacting Change SHALL NOT itself constitute an act of Investor Judgment, a revision of the underlying Investor Reasoning, or a new Decision; it is a surfaced comparison only, per PP-003 and APS-002 IRINV-007.

**DB-R-056.** A Thesis-Impacting Change SHALL route the Investor toward the specific Decision Context it concerns, per Section 12, never resolve the comparison on the Investor's own behalf.

**DB-R-057.** Daily Brief SHALL NOT assert that a Thesis-Impacting Change proves the original Reasoning wrong, or that it requires a specific response; it discloses the new information's own connection to existing Reasoning and stops there, per PP-007.

**DB-R-058.** Where Daily Brief cannot identify a genuine Thesis-Impacting Change with a traceable derivation, it SHALL NOT present one; a fabricated or speculative thesis-impact claim is a failure mode, per DB-F-006.

## 14. Bounded Previews — Daily Brief as Host

APS-006 §13 established the governing discipline for any bounded preview in this lineage; this section applies it to the two previews Daily Brief itself hosts.

**DB-R-059.** A Watchlist Update preview Daily Brief hosts SHALL NOT replace Watchlist's own destination area, per APS-006 PF-R-051 applied here.

**DB-R-060.** A Discover Highlight preview Daily Brief hosts SHALL NOT replace Discover's own destination area, per the same discipline.

**DB-R-061.** Neither preview SHALL independently re-rank the content it previews; where the previewed content is priority-bearing, the preview SHALL draw its ordering from the Atlas Priority Model, never compute its own, per APS-006 PF-R-052.

**DB-R-062.** Neither preview SHALL fully resolve, dismiss, or otherwise complete the item it previews on the item's own destination area's behalf, per APS-006 PF-R-053.

**DB-R-063.** Neither preview SHALL be Daily Brief's own sole presentation of the previewed content; the full, current state SHALL always remain available in the previewed area's own destination, per APS-006 PFINV-006 applied here.

**DB-R-064.** Each preview SHALL be safe to skip entirely: no fact SHALL exist only within a Daily-Brief-hosted preview and nowhere in the previewed area's own destination.

## 15. Bounded Preview — Daily Brief as the Previewed Party

**DB-R-065.** Where Portfolio hosts a bounded preview of Daily Brief, per APS-006 PF-R-042, Daily Brief SHALL expose a summary of its own current Verdict and Delta sufficient for that preview, without requiring Portfolio to re-implement Daily Brief's own filtering logic.

**DB-R-066.** Daily Brief SHALL NOT require or assume that Portfolio's own preview of it reproduces Daily Brief's own content in full; a preview reading a bounded subset is sufficient and expected, per APS-006 PF-R-055.

**DB-R-067.** No fact material to understanding Daily Brief's own Verdict SHALL exist only within Portfolio's own bounded preview of it; the full, current Daily Brief SHALL always be available in Daily Brief's own area.

## 16. Completed Monitoring

**DB-R-068.** Daily Brief SHALL provide a Completed Monitoring category, distinct from the Verdict, confirming that monitored conditions were checked and found nothing requiring attention, once Monitoring exists to supply this content.

**DB-R-069.** Prior to Monitoring's own specification, Daily Brief's Completed Monitoring category MAY remain empty or absent; this specification does not require its premature population.

**DB-R-070.** Completed Monitoring content SHALL NOT be presented with Tier 1's own urgency; it belongs to Tier 4, per DB-R-037, as confirmation of coverage rather than a call to action.

**DB-R-071.** Once Monitoring exists, Atlas SHALL NOT duplicate its own output between the Verdict and Completed Monitoring; a condition that fired belongs to the Verdict (Section 11), and a condition checked with nothing to report belongs to Completed Monitoring — the same fact SHALL NOT be represented in both.

## 17. Boundedness, Finishability, and Repeat Visits

**DB-R-072.** Daily Brief SHALL have a definite end; no requirement in this specification SHALL be read to authorize infinite scroll, pagination presented as inexhaustible, or any mechanism designed to keep the Investor engaged beyond what the Delta itself warrants.

**DB-R-073.** A fact already presented in a prior visit's own Brief SHALL NOT be presented again in an unchanged form on a subsequent visit; only a materially new development concerning that same fact warrants re-presentation, per DB-R-032.

**DB-R-074.** Where nothing has changed since the immediately prior visit, Daily Brief SHALL state this plainly; repeated confirmation of "nothing new" across consecutive visits is itself accurate reporting, not a product failure, per `DBINV-011`.

**DB-R-075.** Daily Brief SHALL NOT be required to track every individual prior visit's own exact content; it is sufficient that a materially unchanged fact is not re-presented as though newly significant.

**DB-R-076.** Daily Brief SHALL NOT manufacture urgency, novelty, or engagement pressure to encourage a return visit; per `ATLAS_CONSTITUTION.md`'s own Product Philosophy, Atlas does not use urgency as a product mechanic.

**DB-R-077.** The Investor SHALL be able to leave Daily Brief having read its full content in a short, bounded session; no requirement in this specification depends on an unbounded amount of Investor time or attention.

**DB-R-078.** Daily Brief's own completion SHALL NOT require navigation to any other area; an Investor who reads the full Brief and finds nothing further of interest has completed a valid, successful session, per `DBINV-011`.

## 18. Empty Brief and New-Investor Behavior

**DB-R-079.** Daily Brief SHALL present a valid, honest state for an Investor with no Delta at all — no owned-position change, no Watchlist change, no Thesis-Impacting Change, and no Completed Monitoring content — stating this fact plainly rather than presenting an empty or broken-seeming surface.

**DB-R-080.** Daily Brief SHALL present a valid, honest state for a first-time Investor with insufficient prior visit history to compute a meaningful Delta, explaining that more will be reported once a prior state exists to compare against, rather than presenting a broken-feeling empty page.

**DB-R-081.** Daily Brief's own value to a first-time Investor SHALL NOT depend on any administrative setup step beyond whatever entry flow already established owned positions or Watchlist Entries elsewhere, per APS-006 PF-R-059 and APS-007 WL-R-041.

**DB-R-082.** Daily Brief SHALL NOT require re-entry of any fact already captured through an entry flow or an existing record; where a fact already exists, Daily Brief reads it rather than re-requesting it.

## 19. Established-Investor Behavior

**DB-R-083.** Daily Brief's own behavior for an established Investor with many owned positions, many Watchlist Entries, and many open Decision Contexts SHALL scale by filtering and boundedness (Section 9, Section 17), never by presenting every individual changed fact with equal prominence.

**DB-R-084.** Daily Brief SHALL treat genuinely new information as the primary signal of value to an established Investor; per DB-R-073, an established Investor who has already internalized yesterday's Brief SHALL NOT be shown the same content again as though it were new.

## 20. Future Multi-Portfolio Compatibility

**DB-R-085.** This specification assumes exactly one Portfolio and one Watchlist per Investor, consistent with APS-006 §15 and APS-007 §16's own identical assumptions, and therefore exactly one Daily Brief per Investor.

**DB-R-086.** This specification SHALL NOT be read to assert that a multi-portfolio-scoped Daily Brief is unsupportable; it states only that this specification does not define one, per Section 28.

## 21. Explicit Exclusions

**DB-R-087.** Daily Brief SHALL NOT become Bloomberg. Bloomberg's value is comprehensive, real-time data across everything, for professionals who need the full firehose; Daily Brief's value is the opposite — filtered, personal, and finite. Chasing Bloomberg's completeness would violate Section 17's own boundedness requirement.

**DB-R-088.** Daily Brief SHALL NOT become Reuters. Reuters reports the world's events for their own newsworthiness; Daily Brief reports an event only because of its connection to something the Investor owns, watches, or has reasoned about, per DB-R-026. An event with zero such connection has no place in Daily Brief, however globally significant.

**DB-R-089.** Daily Brief SHALL NOT become Twitter. Twitter is unranked, unverified, infinite-scroll, and optimized for engagement; Daily Brief has a hard end, per Section 17, and nothing about it SHALL create the sensation of "more below."

**DB-R-090.** Daily Brief SHALL NOT become Portfolio. Portfolio answers "where do I stand" — a snapshot, valid at any instant; Daily Brief answers "what's different since I looked last" — a delta, valid only for the gap since the prior visit, per DB-R-009 and APS-006 PFINV-009.

**DB-R-091.** Daily Brief SHALL NOT become Discover. Discover is a full search-and-browse experience across an outside universe; Daily Brief only ever shows a small, pre-filtered Discover Highlight pointer into what Discover has already found, per Section 14, never a search interface of its own.

**DB-R-092.** Daily Brief SHALL NOT become Watchlist. Watchlist is static storage of decisions already made about what to track; Daily Brief only shows a bounded Watchlist Update preview of it, per Section 14, never letting the Investor browse or edit Watchlist directly.

**DB-R-093.** Daily Brief SHALL NOT become Decision Workspace. Reasoning is performed and permanently recorded through Decision Context and Investor Reasoning, governed by APS-001 and APS-002; Daily Brief never lets the Investor record an Observation, a Judgment, or a Decision directly, per DB-R-052.

**DB-R-094.** Daily Brief SHALL NOT become market news. This restates DB-R-088's own reasoning under the specific "market news" framing: a macro or market-level fact only enters Daily Brief through the lens of a specific owned position or followed Entry it affects, per DB-R-033, never as an independent update about the market itself.

**DB-R-095.** Daily Brief SHALL NOT become a notification inbox. A notification inbox is a raw, unranked, chronological log of every event that fired; Daily Brief compresses, prioritizes, and narrates the Delta into meaning, per Section 9 and Section 10 — the opposite operation. Daily Brief's own content MAY later be delivered through Notifications (Section 8, future-facing), but Daily Brief itself is never merely a log of what Notifications have sent.

## 22. Atlas Responsibilities

**DB-R-096.** Atlas SHALL compute the Delta (Section 5) by comparing the Investor's own current state against the state as of the Investor's own last visit.

**DB-R-097.** Atlas SHALL filter every candidate fact against DB-R-026 before including it in Daily Brief, per Section 9.

**DB-R-098.** Atlas SHALL populate the Verdict from the Atlas Priority Model, per Section 11, never from an independently computed ranking.

**DB-R-099.** Atlas SHALL NOT re-present a materially unchanged fact across visits, per Section 17.

**DB-R-100.** Atlas SHALL disclose an empty Delta, an empty Verdict, or an empty Completed Monitoring category explicitly, per DB-R-079 and DB-R-046, rather than presenting an ambiguous or silently omitted state.

**DB-R-101.** Atlas SHALL preserve the read-only boundary stated in DB-R-010 in every computation Daily Brief performs; no Daily-Brief-level computation SHALL alter a Core Domain Object or an already-accepted Product record.

**DB-R-102.** Atlas SHALL attribute the origin of any Atlas-originated content Daily Brief presents, per PP-008.

## 23. Investor Responsibilities

**DB-R-103.** The Investor remains responsible for deciding whether a Verdict item warrants action; Daily Brief surfaces the item, never the decision, per PP-003.

**DB-R-104.** The Investor remains responsible for interpreting a Thesis-Impacting Change; Daily Brief discloses the connection, never the conclusion, per DB-R-057.

**DB-R-105.** The Investor remains accountable for any Decision reached after navigating from Daily Brief into a Decision Context, in the same manner APP-000 §8.2 already states generally.

## 24. Invariants

**DBINV-001 — No Core Object Status.** Daily Brief SHALL NOT be treated as a Core Domain Object or as Core-reference-eligible.

**DBINV-002 — Distinctness from Portfolio.** Daily Brief SHALL NOT be treated as identical to, or a replacement for, Portfolio; Daily Brief answers "what changed," Portfolio answers "where do I stand."

**DBINV-003 — Distinctness from Discover.** Daily Brief's own content SHALL remain limited to a bounded Discover Highlight preview; it SHALL NOT include Discover's own full candidate set or ranking logic.

**DBINV-004 — Distinctness from Watchlist.** Daily Brief's own content SHALL remain limited to a bounded Watchlist Update preview; it SHALL NOT include Watchlist's own full Entry list or editing capability.

**DBINV-005 — No Deep Reasoning Ownership.** Daily Brief SHALL NOT own or perform Reasoning, Investor Judgment, Decision recording, or Decision Quality evaluation.

**DBINV-006 — Single Priority Model.** Daily Brief SHALL NOT create an independent priority or ranking model separate from the Atlas Priority Model.

**DBINV-007 — No Manual Case Administration.** Where Daily Brief routes into a new Investment Case, it SHALL NOT require the Investor to manually create, name, or configure it.

**DBINV-008 — Previews Are Not Destinations.** A bounded preview Daily Brief hosts, or is itself hosted within, SHALL NOT be treated as the complete destination for the content it previews.

**DBINV-009 — Bounded and Finishable.** Daily Brief SHALL always remain bounded; no requirement in this specification SHALL be read to authorize unbounded or continuously-scrolling content.

**DBINV-010 — Represents Change, Not Everything.** Daily Brief SHALL NOT report every change that occurred; it reports only what is both new and connected, per Section 9.

**DBINV-011 — Honest Absence Is Success.** An empty Verdict, an empty Delta, or a repeated "nothing new" across consecutive visits SHALL be treated as accurate, successful reporting, never as a defect to be filled with unrelated content.

**DBINV-012 — Read-Only Relationship to Core and Product Records.** Daily Brief SHALL NOT mutate any Investment Case, Decision Context, Decision, Outcome, or Watchlist Entry it reads.

**DBINV-013 — No Autonomous Commitment.** Daily Brief SHALL NOT cause a Decision Context to close by Commitment, and SHALL NOT present any Daily-Brief-level action as though it had done so, per APS-001 DCINV-006.

**DBINV-014 — No New Core Relationship.** This specification, and Daily Brief as it governs, SHALL NOT introduce or rely upon a Core relationship, Core Domain Object, or Core invariant beyond those already adopted in `OE-002` and `OE-004`.

**DBINV-015 — Evidence Remains Product-Layer Only.** This specification SHALL NOT describe Evidence as a Core Domain Object anywhere it is mentioned, per APS-003 EV-R-002 and `OE-002` §4's own closed Domain Object Set.

## 25. Failure and Refusal Behavior

Atlas SHALL fail closed: where continuing would violate this specification, APP-000, APP-001, APS-001, APS-006, APS-007, or a Core invariant, Atlas SHALL refuse or halt the action rather than proceed on an assumed or inferred basis. No UI error message is prescribed by this section or by this specification.

**DB-F-001 — Everything appears.** Atlas SHALL NOT present every changed fact without the relevance filtering DB-R-026 through DB-R-029 require; this violates `DBINV-010` and defeats Daily Brief's own purpose.

**DB-F-002 — Nothing appears, and Daily Brief fails to say so.** Where the Delta, Verdict, and Completed Monitoring categories are all genuinely empty, Atlas SHALL state this plainly rather than presenting a blank or broken-seeming surface; failing to disclose a genuine absence violates DB-R-079 and `DBINV-011` — the absence itself is not the failure, the silence about it is.

**DB-F-003 — Daily Brief becomes Portfolio.** Atlas SHALL refuse to present current-state, non-delta content as though it belonged in Daily Brief; this violates `DBINV-002` and DB-R-090.

**DB-F-004 — Daily Brief becomes Discover.** Atlas SHALL refuse to expand the Discover Highlight preview beyond a bounded preview, per Section 14; this violates `DBINV-003` and DB-R-091.

**DB-F-005 — Noise overwhelms relevance.** Atlas SHALL refuse to include a candidate fact that fails DB-R-026's own connection requirement; this violates `DBINV-010` directly.

**DB-F-006 — Every change looks critical.** Atlas SHALL refuse to present Tier 2 through Tier 4 content with Tier 1's own urgency; conflating urgency levels degrades the Investor's ability to answer "does anything require attention," per DB-R-034 and DB-R-037.

**DB-F-007 — The same change appears forever.** Atlas SHALL refuse to re-present a materially unchanged fact across visits as though it were newly significant; this violates DB-R-073 and DB-R-099 directly.

**DB-F-008 — Monitoring duplicates the Brief.** Atlas SHALL refuse to represent the same monitored-condition fact in both the Verdict and Completed Monitoring; this violates DB-R-071.

**DB-F-009 — A Thesis-Impacting Change is fabricated or unsupported.** Atlas SHALL refuse to present a Thesis-Impacting Change with no traceable derivation from new Evidence or a new Observation; this violates DB-R-058 and PP-007.

**DB-F-010 — Daily Brief would autonomously create or close a Decision Context.** Atlas SHALL refuse any action that would create, close, or reopen a Decision Context without an identifiable Investor act, per `DBINV-013` and APS-001 DCINV-006.

## 26. Acceptance Criteria

**DB-AC-001 (Immediate understanding).** An Investor reading Daily Brief's own Tier 1 content alone is observed able to state what changed and whether anything requires attention, per DB-R-012 and DB-R-034.

**DB-AC-002 (Natural transition).** Every routed reference within Daily Brief is observed to lead into Portfolio, Watchlist, Discover, an Investment Case, or a Decision Context — never a dead end — per Section 12 and Section 14.

**DB-AC-003 (Single priority system).** No item in the Verdict is ever observed with an independently computed priority separate from the Atlas Priority Model, per DB-R-043 and `DBINV-006`.

**DB-AC-004 (Concise and bounded).** Every observed Daily Brief session is observed to reach a definite end within a short, bounded read, per Section 17.

**DB-AC-005 (Relevance distinguishable from noise).** Every item presented in Daily Brief is observed traceable to a connection under DB-R-026; no unconnected fact is ever observed present.

**DB-AC-006 (No Core or Decision Engine redesign).** No requirement in this specification is observed to require a new Core Domain Object, a new Core invariant, or a change to the Decision Engine's own existing behavior, per `DBINV-001`, `DBINV-005`, and `DBINV-014`.

**DB-AC-007 (Distinct from Portfolio, Discover, Watchlist).** No full destination-area content from Portfolio, Discover, or Watchlist is ever observed presented in full within Daily Brief; only bounded previews are observed, per `DBINV-002` through `DBINV-004`.

**DB-AC-008 (Previews are not destinations).** Every bounded preview Daily Brief hosts, or is itself hosted within, is observed to link to its own full destination and is never observed as the sole presentation of the content it previews, per `DBINV-008`.

**DB-AC-009 (Repeat-visit correctness).** No materially unchanged fact is ever observed re-presented across consecutive visits as though newly significant, per DB-R-073 and DB-R-099.

**DB-AC-010 (Honest absence).** Every observed empty Verdict or empty Delta is accompanied by an explicit statement of that absence, never a silent or ambiguous blank state, per `DBINV-011`.

**DB-AC-011 (Traceability).** Every requirement in Sections 6 through 23 is traceable, by citation, to at least one of: `ATLAS_CONSTITUTION.md`, an APP-000 Product Principle, an APP-001 provision, an APS-001 provision, an APS-006 provision, an APS-007 provision, or a Core same-Case requirement, per Section 27.

## 27. Traceability

| Requirement / Invariant | Normative basis | Source material (non-normative) | Core basis | Core basis status |
|---|---|---|---|---|
| DB-R-001–006, `DBINV-001` | APP-000 §2, §9; APP-001 §1 | — | `OE-002` §4 (closed Domain Object Set excludes Daily Brief) | Normative (Core) |
| DB-R-007–013, `DBINV-002` | APP-001 §4 | Daily Brief §1 (Purpose) | — | This specification's own product decision, mirroring APS-006 §7 |
| DB-R-014, `DBINV-002` | APS-006 §8 PF-R-019, PF-R-025, PF-R-042 | Daily Brief §6 (Relationship to Portfolio) | `OE-002` §3.1 Case, via Investment Case | Normative (Product), cited not redefined |
| DB-R-015, `DBINV-004` | APS-007 §8 WL-R-013, §13 WL-R-037–039 | Daily Brief §6 (Relationship to Watchlist) | — | Normative (Product), cited not redefined |
| DB-R-016, `DBINV-003` | — | Daily Brief §6 (Relationship to Discover) | — | This specification's own product decision, anticipating APS-009 |
| DB-R-017–020 | APP-001 §3.13 (Investment Case); APS-001 §9–13 | Daily Brief §4 (Information hierarchy, adapted) | `OE-002` §5.5 Decision, §5.6 Outcome | Normative (Core), cited not redefined |
| DB-R-021 | — | Entry Flows §2 (Investor Lab, future) | — | This specification's own product decision |
| DB-R-022, `DBINV-006` | PP-001 | Architecture Resolutions, Decision 2 (Atlas Priority Model) | — | Normative (Product), per APS-006 §10 |
| DB-R-023–025 | — | Daily Brief §6, §8 (Monitoring, Signals, Notifications, future) | — | This specification's own product decision |
| DB-R-026–033, `DBINV-010` | PP-001; APP-000 §6.4 | Daily Brief §2 (Philosophy) | — | This specification's own product decision |
| DB-R-034–041 | PP-001, PP-004 | Daily Brief §4 (Information hierarchy) | — | Reconciliation Design source material, restated normatively |
| DB-R-042–047, `DBINV-006` | PP-001, PP-003, PP-007 | Daily Brief §4 (Requires Attention / Verdict) | — | Normative (Product), per APS-006 §10 |
| DB-R-048–053 | PP-002, PP-003, PP-005 | Daily Brief §7 (User flows) | APS-001 DC-R-017, DC-R-021, DCINV-006 | Normative (Product), cited not redefined |
| DB-R-054–058 | PP-003, PP-007 | Daily Brief §4 (Investment Thesis Changes) | APS-002 IR-R-030–032, IRINV-007 | Normative (Product), cited not redefined |
| DB-R-059–067, `DBINV-008` | — | APS-006 §13 (Preview Governance); APS-007 §13 (Preview Behavior) | — | Normative (Product), cited not redefined |
| DB-R-068–071 | — | Daily Brief §4 (Completed Monitoring) | — | This specification's own product decision |
| DB-R-072–078, `DBINV-009` | PP-004; `ATLAS_CONSTITUTION.md` Product Philosophy | Daily Brief §7, §9 (flows, success criteria) | — | This specification's own product decision |
| DB-R-079–082 | PP-004; APP-000 §10 | Daily Brief §3 (User intent, new investor) | — | — |
| DB-R-083–084 | PP-001 | Daily Brief §3 (User intent, experienced investor) | — | — |
| DB-R-085–086 | — | Product Architecture Review §7 (Scalability); Reconciliation Design Open Questions | — | This specification's own product decision |
| DB-R-087–095, `DBINV-015` | APP-000 §10; `ATLAS_CONSTITUTION.md` Non-Negotiable Principles | Daily Brief §5 (Must not become) | `OE-002` §4 (Evidence excluded); APS-003 EV-R-002 | Normative (Core) for Evidence's own status |
| DB-R-096–105 | PP-001 through PP-009, as cited per line; APP-000 §8.2 | Daily Brief §8 (Atlas responsibilities) | — | — |
| `DBINV-003`, `DBINV-005`, `DBINV-007`, `DBINV-011`, `DBINV-012`, `DBINV-013`, `DBINV-014` | PP-003, PP-005, PP-006, PP-007 | Product Architecture Review Weaknesses (verdict-triplication finding, adapted) | `OE-002`; `OE-004`; APS-001 DCINV-006 | Normative (Core), cited not redefined |

## 28. Open Questions and Deferred Work

- **Relevance threshold tuning.** This specification defines what qualifies a fact for inclusion (Section 9) and what does not, but the precise computational method for determining relevance is implementation and calibration work, not defined here. Classified: **non-blocking for APS-008**.
- **Repeat-visit behavior in full detail.** DB-R-073 through DB-R-075 state the governing principle — a materially unchanged fact is not re-presented — but the exact mechanism for detecting "materially unchanged" across visits is not defined here. Classified: **non-blocking for APS-008**, implementation-level.
- **Notification integration.** Named in Section 8 as future-facing and out of current scope; no design commitment is made here for how or when Daily Brief content would be delivered via Notifications. Classified: **out of current scope**.
- **Monitoring cadence and mechanics.** Completed Monitoring (Section 16) assumes Monitoring exists to supply content but does not define how often, or by what mechanism, monitored conditions are checked. Classified: **out of current scope** — Monitoring itself has no governing specification anywhere yet.
- **Multi-portfolio-scoped Daily Brief.** Coupled to Portfolio's and Watchlist's own identical open questions (APS-006 §24, APS-007 §24). Classified: **requires separate architecture work**, non-blocking for this specification's own completeness.
- **Whether "Thesis-Impacting Change" requires later formal Product Concept treatment.** Genuinely open, mirroring the identical, still-open questions APS-006 §24 and APS-007 §24 carry for "Holding" and "Watchlist Entry." Classified: **deferred** — a candidate for a future, dedicated APP-001 amendment this specification has no authority to propose or enact.

---

*This specification does not modify `ATLAS_CONSTITUTION.md`, `Architecture-Governance.md`, `Atlas-Alpha-Baseline-v1.0.md`, APP-000, APP-001, APS-001 through APS-007, any `docs/atlas_ux/` document, or any source code. It introduces no new Core Domain Object and requires no Atlas Core or Decision Engine redesign.*
