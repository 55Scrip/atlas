# APS-007 — Watchlist

**Status:** Draft, v0.1. This is the seventh Atlas Product Specification, subordinate to APP-000 — Atlas Product Doctrine and APP-001 — Atlas Product Concept Taxonomy (v0.4), and depending on APS-001 — Decision Context and APS-006 — Portfolio. It states the complete normative product behavior of Watchlist: the product surface responsible for the Investor's intentional review queue. It does not describe screens, workflows, visual design, interaction design, algorithms, data schemas, persistence mechanisms, or any other implementation technique, and it does not redefine Core ontology.

---

## 1. Governance Metadata

Stated here in full, per `Architecture-Governance.md` §10's own requirement, matching the pattern APS-006 §1 already established.

- **Document identifier:** APS-007.
- **Title:** Watchlist.
- **Version:** v0.1.
- **Status:** Draft — the smallest truthful status available to a newly authored specification, matching APS-001 through APS-006 at their own first publication.
- **Parent authority:** APP-000 — Atlas Product Doctrine (Draft v0.4); APP-001 — Atlas Product Concept Taxonomy (Draft v0.4), specifically §4 (Watchlist's own reaffirmed deferral) and §9 item 8 (Watchlist reserved for this specification).
- **Dependencies:** APS-001 — Decision Context (Draft v0.1), for the lifecycle Watchlist explicitly does not touch but must not be confused with. APS-006 — Portfolio (Draft v0.1), for the Atlas Priority Model it adopts by reference and the bounded-preview discipline it operates under from the previewed side.
- **Scope:** Watchlist's own identity, ownership, responsibilities, relationships to Portfolio, Daily Brief, Discover, Investment Case, Decision Context, Decision, Outcome, Investor Lab, the Atlas Priority Model, and future Monitoring and Signals; its exclusions; and the Atlas/Investor responsibility split.
- **Non-scope:** Screens, workflows, navigation, visual design, interaction design, implementation, algorithms, data schemas, persistence mechanisms; Discover's and Daily Brief's own complete product behavior (each reserved for APS-009 and APS-008 respectively); any amendment to APP-000, APP-001, APS-001 through APS-006, Atlas Core, or `docs/atlas_ux/`.
- **Affected documents:** None requiring amendment. `APP-001` already reserved this territory in its own v0.4 amendment (§4, §9) and requires no further change.
- **Superseded documents:** None, in the formal sense `Architecture-Governance.md` §7 defines. No dedicated Phase II "Watchlist Product Specification" was ever produced or committed to this repository — Watchlist appears only as scattered descriptions within the Phase II Entry Flows, Portfolio Control Center, and Discover material. §7's Supersession Notice mechanism does not apply to source material that was never itself a repository document.
- **Migration requirements:** None. No existing repository document, and no implementation, is required to change as a consequence of this document's creation.

## 2. Purpose

Watchlist requires its own specification because APP-001 §4 names it as approved deferred territory but does not itself state Watchlist's product behavior. This specification closes that gap: it states Watchlist's own identity as the Investor's intentional review queue — a store of Investor intent, not a reasoning process, not a Portfolio, and not Discover — its responsibilities, its relationships, and its boundary against every neighboring area, so that a future UX specification, an implementation design, engineering, QA, and any AI agent working on Atlas can build from it without inventing new Watchlist product rules of their own.

Watchlist's own central user question is *"what should I continue following?"* — distinct from Portfolio's "where do I stand" (APS-006 §2) and, once specified, from Discover's "what should I investigate next" and Daily Brief's "what changed."

This specification is re-derived from the scattered Watchlist material within the Phase II Entry Flows, Portfolio Control Center, and Discover documents, the Product Architecture Review, and Architecture Resolutions — none of which were committed to this repository and none of which hold independent authority here. Their valid product decisions are translated, not copied, into this specification's own requirements.

## 3. Scope

In scope: Watchlist's identity as a product-level surface; its ownership and responsibility boundary; its relationship to Portfolio, Daily Brief, Discover, Investment Case, Decision Context, Decision, Outcome, Investor Lab, the Atlas Priority Model, and future Monitoring and Signals; intentional inclusion and removal; progression into Investment Case; preview behavior as the previewed party; empty state and onboarding; established-Investor behavior; and the Atlas/Investor responsibility split.

Out of scope, per APP-000 §1 and §10: screens, workflows, navigation, visual design, interaction design, algorithms, data schemas, persistence mechanisms, or any other implementation technique. Also out of scope: Discover's and Daily Brief's own complete product behavior (each reserved for APS-009 and APS-008, neither yet written); formal Product Concept treatment of "Watchlist Entry," which this specification does not attempt and does not require (Section 5, Section 24); multi-portfolio compatibility (Section 16, Section 24); and any resolution of the Core-track Evidence discrepancy, which this specification does not reopen.

## 4. Governing References

- **`ATLAS_CONSTITUTION.md`.** Normative, superior to every document in the Atlas Product Architecture track.
- **APP-000 — Atlas Product Doctrine, Draft v0.4.** Normative, superior to this specification.
- **APP-001 — Atlas Product Concept Taxonomy, Draft v0.4.** Normative, superior to this specification; §4 reaffirms Watchlist's own deferral and names this specification as its subject; §9 item 8 reserves this specification's own sequencing position.
- **APS-001 — Decision Context, Draft v0.1.** Normative, superior to this specification; governs the lifecycle Watchlist explicitly does not touch (Section 8).
- **APS-006 — Portfolio, Draft v0.1.** Normative, superior to this specification; defines the Atlas Priority Model (§10) this specification adopts by reference (Section 12), and states, from Portfolio's own side, the bounded-preview discipline (§13) Watchlist operates under here as the previewed party (Section 13).
- **`OE-002` — Domain Object Model, Final.** Normative for Atlas Core; confirms Watchlist introduces no new Domain Object (Section 6).
- **The Product Architecture Reconciliation Design** (accepted, this repository's own prior governance work). Non-normative in the sense that it is not itself a Product Architecture document — cited as the source of the migration sequencing that places this specification after APS-006 and before APS-008.
- **The Phase II "Entry Flows," "Portfolio Control Center," and "Discover" material.** Non-normative source material only, never committed to this repository, holding no authority of its own. No dedicated Phase II Watchlist specification exists; the material used here is Entry Flows' own Watchlist area description, Portfolio Control Center's own Watchlist Summary preview treatment, and Discover's own Watchlist Candidates and Discover → Watchlist flow. Translated, not copied, into this specification's own requirements.
- **The Phase II "Product Architecture Review" and "Architecture Resolutions."** Non-normative source material only, for the same reason.

## 5. Definitions

Only concepts not already defined by APP-000, APP-001, APS-001, or APS-006 are defined here.

**Watchlist Entry.** Ordinary-language description of one subject — a specific security, theme, or idea — the Investor has intentionally chosen to keep following. Not a formal Product Concept; no independent identity, ownership, lifecycle, or responsibility is asserted for it by this specification, mirroring APS-006's own treatment of "owned position" (APS-006 §5, §6).

**Follow.** The explicit, Investor-originated act of adding a Watchlist Entry.

**Release.** The explicit, Investor-originated act of removing a Watchlist Entry. Unlike Decision Context's own Abandonment (APS-001 §12), Release carries no requirement of permanent historical preservation; see Section 10.

## 6. Architectural Position

**WL-R-001.** Watchlist SHALL be subordinate to APP-000, APP-001, APS-001, and APS-006; it SHALL NOT contradict any of the four or redefine a term any of them defines.

**WL-R-002.** Watchlist SHALL NOT be treated as a Core Domain Object, and SHALL NOT be, or be treated as, reference-eligible within Atlas Core.

**WL-R-003.** Watchlist SHALL NOT be treated as identical to, or a replacement for, Portfolio, Discover, Investment Case, or Decision Context.

**WL-R-004.** Watchlist SHALL NOT be treated as a Decision Engine concept. It does not perform Reasoning, does not exercise Investor Judgment, does not record a Decision, and does not evaluate Decision Quality.

**WL-R-005.** This specification does not promote Watchlist Entry to a formal Product Concept; it remains ordinary-language description throughout, per Section 5.

## 7. Core Properties and Ownership

**WL-R-006.** Watchlist SHALL be owned by the Investor.

**WL-R-007.** Watchlist SHALL consist of zero or more Watchlist Entries, each created only by an explicit Follow act and removed only by an explicit Release act.

**WL-R-008.** Watchlist SHALL NOT infer, automate, or default a Follow or a Release on the Investor's own behalf.

**WL-R-009.** A Watchlist Entry SHALL NOT be required to persist permanently. Release is a legitimate, consequence-free act — an explicit and deliberate departure from the permanence discipline APS-001 through APS-006 establish for the records each of them governs, because a Watchlist Entry carries no Reasoning, no Commitment, and no epistemic weight of its own; there is nothing in it that Learning (APS-004) or any other future specification would need to revisit once released.

**WL-R-010.** A Watchlist Entry's own removal SHALL NOT be treated as, described as, or confused with an Abandonment of a Decision Context; the two are unrelated acts governed by unrelated specifications (Section 5; APS-001 §12).

**WL-R-011.** Watchlist's own central user question — *"What should I continue following?"* — SHALL govern every responsibility this specification defines.

## 8. Concept Relationships

Each relationship below is classified as existing, derived, product-level, deferred, future-facing, or not applicable, per this specification's own required precision.

**WL-R-012.** Watchlist's relationship to **Portfolio** is existing and product-level: Portfolio hosts a bounded, passive summary of Watchlist's own state (APS-006 §8 PF-R-021, §9 PF-R-028), read from Watchlist, never the reverse. Watchlist SHALL NOT read or embed Portfolio's own owned-position content.

**WL-R-013.** Watchlist's relationship to **Daily Brief** is deferred and future-facing: Daily Brief's complete product behavior is reserved for APS-008, not yet written. Watchlist anticipates hosting, or being previewed by, a future bounded "Watchlist Updates" category, governed by the same bounded-preview discipline this specification adopts (Section 13) — this specification does not itself define that category's content.

**WL-R-014.** Watchlist's relationship to **Discover** is deferred and future-facing: Discover's complete product behavior is reserved for APS-009, not yet written. Discover is Watchlist's own most common upstream source in practice, but Watchlist SHALL NOT automatically populate an Entry from Discover output; every Entry requires its own explicit Follow act, per WL-R-007, regardless of where the underlying idea originated.

**WL-R-015.** Watchlist's relationship to **Investment Case** is existing and product-level: a Watchlist Entry MAY progress into an Investment Case, per Section 9, but never does so automatically; the Entry itself is never an Investment Case and is never treated as one prior to that progression.

**WL-R-016.** Watchlist's relationship to **Decision Context** is not applicable: Watchlist SHALL NOT create, hold, or reference a Decision Context. That relationship begins only once a Watchlist Entry has progressed into an Investment Case and genuine Reasoning has begun within it, per APS-001 §8.

**WL-R-017.** Watchlist's relationship to **Decision** is not applicable: no Decision is ever recorded against a Watchlist Entry as such.

**WL-R-018.** Watchlist's relationship to **Outcome** is not applicable, for the same reason as WL-R-017: an Outcome presupposes a Decision, and a Watchlist Entry, by definition, has none.

**WL-R-019.** Watchlist's relationship to **Investor Lab** is future-facing and, at present, indirect, mirroring APS-006 §8 PF-R-022: no specification has yet been reserved for Investor Lab. A future Investor Lab specification MAY read Watchlist's own historical Follow/Release pattern once one exists; this specification does not anticipate the mechanism.

**WL-R-020.** Watchlist's relationship to the **Atlas Priority Model** (APS-006 §10) is derived and product-level: Watchlist SHALL NOT compute an independent ranking of its own Entries; any future prioritization of Watchlist content SHALL be expressed as a scoped view of the one Atlas Priority Model, adopted by reference exactly as APS-006 §10 PF-R-034 invites.

**WL-R-021.** Watchlist's relationship to future **Monitoring** and **Signals** is future-facing and out of current scope. This specification records only that a monitored condition on a Watchlist Entry, once Monitoring is specified, is the natural kind of fact the Atlas Priority Model would incorporate, and that a Signal, once specified, would prompt the Investor toward a new Follow act or flag an existing Entry — never autonomously create or remove one, per PP-003 and WL-R-008.

## 9. Intentional Inclusion and Progression into Investment Case

**WL-R-022.** A Follow act SHALL be explicit and Investor-originated; Watchlist SHALL NOT create an Entry merely because the Investor viewed, encountered, or was shown a candidate.

**WL-R-023.** A Follow act SHALL NOT require the Investor to provide any justification, thesis, or reasoning; Watchlist entry carries no evidentiary or reasoning weight, per WL-R-004 and Section 17.

**WL-R-024.** A Follow act MAY originate from any context — Discover, a Daily Brief highlight, or a source entirely outside Atlas — without altering Watchlist's own treatment of the resulting Entry, per WL-R-014.

**WL-R-025.** Watchlist SHALL support progression of an Entry into an Investment Case, triggered only by a genuine, further Investor act of choosing to seriously evaluate that Entry — the same creation discipline APS-001 already establishes for Decision Context (DC-R-017, DC-R-021) and APS-006 already establishes for Investment Case (PF-R-047).

**WL-R-026.** Progression into an Investment Case SHALL create that Investment Case silently, per WL-R-025; Watchlist SHALL NOT require the Investor to name, configure, or administratively set up the resulting Investment Case.

**WL-R-027.** An Entry that progresses into an Investment Case MAY remain in Watchlist, be removed from it, or be marked as progressed, at the Investor's own discretion; this specification does not mandate any one of these three outcomes.

## 10. Intentional Removal

**WL-R-028.** A Release act SHALL be explicit and Investor-originated; Watchlist SHALL NOT remove an Entry through inference, staleness, or any automated process.

**WL-R-029.** Release SHALL carry no negative framing, penalty, or required justification; ceasing to follow something is as legitimate an outcome as following it in the first place.

**WL-R-030.** Following WL-R-009, Release SHALL NOT be required to preserve the released Entry as a historical record; where an implementation chooses to retain one anyway, that retention is not required by this specification and confers no Product-layer significance.

**WL-R-031.** Release of a Watchlist Entry SHALL NOT alter, close, or otherwise affect any Investment Case that Entry may have already progressed into, per WL-R-027; the two remain independent once progression has occurred.

**WL-R-032.** Watchlist SHALL NOT prevent or discourage Release through friction, confirmation burden, or any mechanism inconsistent with Release's own consequence-free status, per WL-R-029.

## 11. Reflecting Investor Priorities

**WL-R-033.** Watchlist's own ordering or emphasis of its Entries, where any exists, SHALL reflect the Investor's own expressed priorities — including recency of Follow, proximity to progression, or an explicit Investor-set preference — never an Atlas-originated ranking asserted as though it were the Investor's own.

**WL-R-034.** Watchlist SHALL NOT present one Entry as more "correct" or more worth pursuing than another; per WL-R-023, no Entry carries evidentiary or reasoning weight for Watchlist to rank by.

## 12. Interaction with the Atlas Priority Model

**WL-R-035.** Watchlist SHALL NOT independently compute which Entries deserve the Investor's Attention; where such a signal exists, it SHALL be expressed as a scoped view of the Atlas Priority Model (APS-006 §10), per WL-R-020.

**WL-R-036.** Where a Watchlist Entry's underlying subject changes in a way that would otherwise warrant Requires-Attention-style treatment, that treatment SHALL be sourced from the Atlas Priority Model, never independently asserted by Watchlist.

## 13. Preview Behavior — Watchlist as the Previewed Party

APS-006 §13 states Portfolio's own responsibilities as a host of bounded previews. This section states the corresponding, narrower responsibility Watchlist itself carries as the content being previewed; it does not restate or redefine the presentation-layer rules that section already governs.

**WL-R-037.** Watchlist SHALL expose a summary of its own current state sufficient for Portfolio, and eventually Daily Brief, to host a bounded preview of it, per APS-006 PF-R-051 through PF-R-054.

**WL-R-038.** Watchlist SHALL NOT require or assume that any previewing area re-implements Watchlist's own content in full; a preview reading a subset of Watchlist's own state is sufficient and expected.

**WL-R-039.** No fact material to understanding a Watchlist Entry SHALL exist only within a previewing area's own bounded preview; the full, current state of Watchlist SHALL always be available in Watchlist's own area, per APS-006 PFINV-006.

## 14. Empty State and Onboarding

**WL-R-040.** Watchlist SHALL present a valid, honest state for an Investor with zero Entries, stating this fact plainly rather than presenting an empty or broken-seeming surface.

**WL-R-041.** Watchlist's own value to a first-time Investor SHALL NOT depend on any administrative setup step beyond a single Follow act; an Investor MAY use Watchlist meaningfully before ever importing or building a Portfolio, per its own independence from owned-position state (WL-R-003).

**WL-R-042.** Watchlist SHALL NOT require the Investor to categorize, tag, or classify an Entry at the moment of Follow; any such refinement, where it exists, remains optional and separate from the act of Following itself.

## 15. Established-Investor Behavior

**WL-R-043.** Watchlist's own behavior for an Investor with many Entries SHALL scale by the ordering discipline in Section 11, never by requiring manual triage before the surface delivers value.

**WL-R-044.** Watchlist SHALL NOT accumulate unbounded, undifferentiated content without regard to the Investor's own current priorities; where volume grows large, Section 11's own priority-reflecting ordering remains the sole mechanism this specification authorizes for managing it — never an independent Atlas-computed filter.

## 16. Future Multi-Portfolio Compatibility

**WL-R-045.** This specification assumes exactly one Watchlist per Investor, consistent with Atlas Alpha's current baseline scope and with APS-006 §15's own identical assumption for Portfolio.

**WL-R-046.** This specification SHALL NOT be read to assert that multi-portfolio-scoped Watchlists are unsupportable; it states only that this specification does not define them, per Section 24.

## 17. Explicit Exclusions

**WL-R-047.** Watchlist SHALL NOT become Portfolio. Portfolio presents owned-position state; Watchlist tracks unowned subjects the Investor has chosen to keep following. Different universes, per WL-R-003 and APS-006 PFINV-010.

**WL-R-048.** Watchlist SHALL NOT become Discover. Discover is the generative process that sources candidates from outside the owned and followed set; Watchlist is static storage of decisions already made about what is worth tracking. A list and the engine that feeds it are not the same responsibility.

**WL-R-049.** Watchlist SHALL NOT become the Decision Engine. Watchlist never lets the Investor record an Observation, a Judgment, or a Decision directly; every path from an Entry into real reasoning passes through a system-created Investment Case, per WL-R-025 and WL-R-026, never around one.

**WL-R-050.** Watchlist SHALL NOT become a research database. An Entry carries no citation, no Source, no Provenance Category, and no Descriptive Reliability of its own; those properties belong exclusively to Evidence (APS-003), governed within a real Investor Reasoning, not to a mere Watchlist Entry.

**WL-R-051.** Watchlist SHALL NOT become a news feed. It does not ingest or surface external events on its own initiative; it only ever reflects what the Investor has deliberately chosen to Follow, per WL-R-022.

**WL-R-052.** Watchlist SHALL NOT become a market screener. It has no criteria-matching, filtering, or candidate-generation mechanism of its own; every Entry begins from an already-identified subject the Investor names through Follow, never from a query Watchlist itself evaluates against a universe.

**WL-R-053.** Watchlist SHALL NOT become a permanent archive. Per WL-R-009 and WL-R-030, an Entry is not required to persist after Release; Watchlist's own responsibility is a live, current reflection of what the Investor is now choosing to follow, not a historical record of everything ever followed.

**WL-R-054.** Watchlist SHALL NOT become a task manager. An Entry carries no due date, no assignment, and no completion-tracking semantics; Section 11's own priority-reflecting ordering is the only organizing mechanism this specification authorizes, and it is not a task list.

## 18. Atlas Responsibilities

**WL-R-055.** Atlas SHALL record a Watchlist Entry only upon an explicit Follow act, per WL-R-022.

**WL-R-056.** Atlas SHALL remove a Watchlist Entry only upon an explicit Release act, per WL-R-028, and SHALL NOT preserve a Product-layer historical record of it as a requirement of this specification, per WL-R-009 and WL-R-030.

**WL-R-057.** Atlas SHALL create an Investment Case silently upon genuine progression from a Watchlist Entry, per WL-R-025 and WL-R-026, mirroring APS-006 PF-R-081.

**WL-R-058.** Atlas SHALL expose Watchlist's own current state for Portfolio's, and eventually Daily Brief's, own bounded previews, per Section 13.

**WL-R-059.** Atlas SHALL NOT compute an independent ranking of Watchlist Entries separate from the Atlas Priority Model, per WL-R-035 and Section 12.

**WL-R-060.** Atlas SHALL NOT infer a Follow or a Release on the Investor's own behalf, per WL-R-008, PP-003, and PP-005.

## 19. Investor Responsibilities

**WL-R-061.** The Investor owns every Follow and every Release act, and the Watchlist Entry each produces or removes.

**WL-R-062.** The Investor is responsible for deciding when a Watchlist Entry warrants progression into an Investment Case; Watchlist surfaces the opportunity, never the decision, per PP-003.

**WL-R-063.** The Investor remains accountable for any Decision later reached after progressing a Watchlist Entry into an Investment Case, in the same manner APP-000 §8.2 already states generally.

## 20. Invariants

**WLINV-001 — No Core Object Status.** Watchlist SHALL NOT be treated as a Core Domain Object or as Core-reference-eligible.

**WLINV-002 — Distinctness from Portfolio and Discover.** Watchlist SHALL NOT be treated as identical to, or a replacement for, Portfolio or Discover.

**WLINV-003 — No Reasoning.** Watchlist SHALL NOT perform Reasoning, exercise Investor Judgment, or evaluate Decision Quality.

**WLINV-004 — No Decision Creation.** Watchlist SHALL NOT create, record, or imply a Decision for any Entry it holds.

**WLINV-005 — No Independent Ranking.** Watchlist SHALL NOT compute a ranking or priority signal independent of the Atlas Priority Model.

**WLINV-006 — No Manual Case Administration.** Watchlist SHALL NOT require the Investor to manually create, name, or configure the Investment Case a progressed Entry produces.

**WLINV-007 — Intentionality of Inclusion.** Every Watchlist Entry SHALL be traceable to an explicit Follow act; no Entry SHALL be observed created by inference, default, or automation.

**WLINV-008 — Consequence-Free Removal.** Release SHALL NOT be required to preserve a permanent historical record of the released Entry, and SHALL carry no penalty, friction, or required justification.

**WLINV-009 — Not Historical Storage.** Watchlist SHALL NOT be treated as, or required to function as, a permanent archive of everything ever followed.

**WLINV-010 — Distinctness from Decision Context Lifecycle.** Release SHALL NOT be treated as, described as, or confused with Abandonment of a Decision Context.

**WLINV-011 — Read-Only Relationship to Portfolio, Investment Case, Decision, and Outcome.** Watchlist SHALL NOT mutate, and SHALL NOT be mutated by, Portfolio's own content, any Investment Case, any Decision, or any Outcome.

**WLINV-012 — No New Core Relationship.** This specification, and Watchlist as it governs, SHALL NOT introduce or rely upon a Core relationship, Core Domain Object, or Core invariant beyond those already adopted in `OE-002` and `OE-004`.

## 21. Failure and Refusal Behavior

Atlas SHALL fail closed: where continuing would violate this specification, APP-000, APP-001, APS-001, APS-006, or a Core invariant, Atlas SHALL refuse or halt the action rather than proceed on an assumed or inferred basis. No UI error message is prescribed by this section or by this specification.

**WL-F-001 — Everything becomes Watchlisted.** Atlas SHALL NOT auto-populate Watchlist from Discover output, Daily Brief content, or any other source without an explicit Follow act; this violates WL-R-022 and WLINV-007, and defeats the intentionality that gives Watchlist its own meaning.

**WL-F-002 — Nothing leaves Watchlist.** Atlas SHALL NOT interpose friction, confirmation burden, or justification requirements on Release; this violates WL-R-032 and WLINV-008, and turns a consequence-free act into an administrative one.

**WL-F-003 — Watchlist becomes Discover.** Atlas SHALL NOT add candidate-sourcing, criteria-matching, or thread-relevance computation to Watchlist itself; this violates WL-R-052 and WLINV-002 — that responsibility belongs exclusively to Discover.

**WL-F-004 — Watchlist becomes Portfolio.** Atlas SHALL NOT present owned-position state, or any Portfolio-owned category, within Watchlist itself; this violates WL-R-047 and WLINV-002.

**WL-F-005 — Watchlist becomes a research notebook.** Atlas SHALL NOT attach citations, Source, Provenance Category, or Descriptive Reliability to a Watchlist Entry; this violates WL-R-050 — those properties belong to Evidence, governed within a real Investor Reasoning, never to a mere Entry.

**WL-F-006 — Watchlist loses intentionality.** Atlas SHALL refuse any mechanism that creates, modifies, or removes an Entry without an identifiable Investor act; this violates WLINV-007 and PP-003/PP-005 directly.

**WL-F-007 — Watchlist would preserve a released Entry as though it were historically required.** Atlas SHALL NOT represent Release as though it carried the same permanent-preservation obligation as Decision Context closure or Evidence capture; this violates WLINV-008 and WLINV-009, and misapplies a discipline that governs different, heavier records.

**WL-F-008 — Watchlist would compute its own priority ranking.** Atlas SHALL refuse to rank Entries by any mechanism independent of the Atlas Priority Model; this violates WLINV-005 directly.

**WL-F-009 — Watchlist would autonomously create an Investment Case.** Atlas SHALL NOT progress an Entry into an Investment Case absent a genuine, further Investor act distinct from the original Follow; this violates WL-R-025 and mirrors APS-001 DCINV-006's own discipline against autonomous Commitment.

## 22. Acceptance Criteria

**WL-AC-001 (Purpose understood).** Watchlist's own content is observed to answer "what should I continue following," distinctly from Portfolio's "where do I stand" and Discover's own eventual "what should I investigate next," per WL-R-011 and WLINV-002.

**WL-AC-002 (Discover → Watchlist → Investment Case).** A candidate is observed to move from Discover-originated interest, through an explicit Follow act, to an explicit progression act, to a system-created Investment Case, with every step attributable to a genuine Investor act, per WL-R-014, WL-R-022, and WL-R-025.

**WL-AC-003 (Distinct from Portfolio).** No owned-position content is ever observed presented within Watchlist itself, per WLINV-002 and WL-R-047.

**WL-AC-004 (Investor intent reflected).** Every Watchlist Entry observed to exist is traceable to an explicit Follow act; no Entry is ever observed with no identifiable originating act, per WLINV-007.

**WL-AC-005 (Removal is consequence-free).** Every observed Release is completed without a required justification, penalty, or preserved historical record, per WLINV-008.

**WL-AC-006 (Single priority model).** No independently computed ranking is ever observed within Watchlist's own content, per WLINV-005.

**WL-AC-007 (Previews are not destinations).** Every bounded preview of Watchlist hosted elsewhere is observed to draw from, never replace, Watchlist's own full current state, per WL-R-037 through WL-R-039.

**WL-AC-008 (No Core or Decision Engine redesign).** No requirement in this specification is observed to require a new Core Domain Object, a new Core invariant, or a change to the Decision Engine's own existing behavior, per WLINV-001, WLINV-003, and WLINV-012.

**WL-AC-009 (Traceability).** Every requirement in Sections 6 through 19 is traceable, by citation, to at least one of: `ATLAS_CONSTITUTION.md`, an APP-000 Product Principle, an APP-001 provision, an APS-001 provision, an APS-006 provision, or a Core same-Case requirement, per Section 23.

## 23. Traceability

| Requirement / Invariant | Normative basis | Source material (non-normative) | Core basis | Core basis status |
|---|---|---|---|---|
| WL-R-001–005, WLINV-001 | APP-000 §2, §9; APP-001 §1 | — | `OE-002` §4 (closed Domain Object Set excludes Watchlist) | Normative (Core) |
| WL-R-006–011 | APP-001 §4 | Entry Flows §2 (Watchlist area description) | — | — |
| WL-R-012, WLINV-002 | APS-006 §8 (Portfolio's own Watchlist relationship, PF-R-021, PF-R-028) | Portfolio Control Center §4, §6 (Watchlist Summary) | — | Normative (Product), cited not redefined |
| WL-R-013 | — | Portfolio Control Center §10 (Daily Brief future expansion, adopted as reconciled) | — | This specification's own product decision |
| WL-R-014, WL-F-001, WL-F-003, WLINV-002 | — | Discover §6, §7 (Watchlist relationship, Discover → Watchlist flow) | — | This specification's own product decision |
| WL-R-015–018 | APP-001 §3.13 (Investment Case); APS-001 §8 (Decision Context creation) | Entry Flows §3 (system-created Case rule) | `OE-002` §5.5 Decision, §5.6 Outcome | Normative (Core), cited not redefined |
| WL-R-019 | — | Entry Flows §2 (Investor Lab, future) | — | This specification's own product decision |
| WL-R-020, WL-R-035, WL-R-036, WLINV-005 | PP-001 | Architecture Resolutions, Decision 2 (Atlas Priority Model) | — | Normative (Product), per APS-006 §10 |
| WL-R-021 | — | Entry Flows §7 (Signals, Monitoring future-compatibility table) | — | This specification's own product decision |
| WL-R-022–027, WLINV-006, WLINV-007 | PP-002, PP-003, PP-005 | Entry Flows §3 (system-created Case rule, adopted) | APS-001 DC-R-017, DC-R-021, DCINV-006 | Normative (Product), cited not redefined |
| WL-R-028–032, WLINV-008, WLINV-009, WLINV-010 | PP-006 boundary reasoned against, not applied | — | — | This specification's own product decision — the deliberate departure from APS-001–006's own permanence discipline |
| WL-R-033–034 | PP-001 | Portfolio Control Center §4 (priority-reflecting pattern, adapted) | — | — |
| WL-R-037–039 | — | APS-006 §13 (Preview Governance, from the previewing side) | — | Normative (Product), cited not redefined |
| WL-R-040–044 | PP-004; APP-000 §10 | Portfolio Control Center §7, §9 (empty/established-user pattern, adapted) | — | — |
| WL-R-045–046 | — | Product Architecture Review §7 (Scalability); Reconciliation Design Open Questions | — | This specification's own product decision |
| WL-R-047–054 | APP-000 §10 | Discover §5 (Must not become, adapted) | APS-003 EV-R-002 (Evidence's own Product-layer-only status, cited for WL-R-050) | Normative (Core) for Evidence's own status |
| WL-R-055–063 | PP-001 through PP-009, as cited per line; APP-000 §8.2 | Portfolio Control Center §8 pattern, adapted | — | — |
| WLINV-003, WLINV-004, WLINV-011, WLINV-012 | PP-003, PP-005, PP-006 | Product Architecture Review Weaknesses (verdict-triplication finding, adapted as a caution against Watchlist inventing its own signals) | `OE-002` §4; `OE-004` | Normative (Core) |

## 24. Open Questions and Deferred Work

- **Whether "Watchlist Entry" requires later formal Product Concept treatment.** Genuinely open, mirroring the identical, still-open question APS-006 §24 carries for "Holding." Classified: **deferred** — a candidate for a future, dedicated APP-001 amendment this specification has no authority to propose or enact.
- **Multi-portfolio-scoped Watchlists.** Coupled to Portfolio's own identical open question (APS-006 §24). Classified: **requires separate architecture work**, non-blocking for this specification's own completeness.
- **The exact future shape of "Watchlist Updates" within Daily Brief.** Cannot be resolved before APS-008 exists. Classified: **non-blocking for APS-007** — this specification states only that Watchlist exposes state sufficient for such a preview to exist, per Section 13, not the preview's own content.
- **Whether released Entries should, in some future specification, be retained for Investor Lab's own pattern analysis** (per WL-R-019's own forward possibility). Not resolved here, and not silently assumed either way; WLINV-008 and WLINV-009 govern this specification's own behavior regardless of what a future specification eventually decides. Classified: **out of current scope**.

---

*This specification does not modify `ATLAS_CONSTITUTION.md`, `Architecture-Governance.md`, `Atlas-Alpha-Baseline-v1.0.md`, APP-000, APP-001, APS-001 through APS-006, any `docs/atlas_ux/` document, or any source code. It introduces no new Core Domain Object and requires no Atlas Core or Decision Engine redesign.*
