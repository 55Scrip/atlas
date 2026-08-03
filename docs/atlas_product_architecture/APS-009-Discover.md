# APS-009 — Discover

**Status:** Draft, v0.1. This is the ninth Atlas Product Specification, subordinate to APP-000 — Atlas Product Doctrine and APP-001 — Atlas Product Concept Taxonomy (v0.4), and depending on APS-001 — Decision Context, APS-006 — Portfolio, APS-007 — Watchlist, and APS-008 — Daily Brief. It states the complete normative product behavior of Discover: the product surface responsible for expanding the Investor's opportunity set beyond currently owned and intentionally followed positions. It does not describe screens, workflows, visual design, interaction design, algorithms, data schemas, persistence mechanisms, or any other implementation technique, and it does not redefine Core ontology.

---

## 1. Governance Metadata

Stated here in full, per `Architecture-Governance.md` §10's own requirement, matching the pattern APS-006 §1, APS-007 §1, and APS-008 §1 already established.

- **Document identifier:** APS-009.
- **Title:** Discover.
- **Version:** v0.1.
- **Status:** Draft — the smallest truthful status available to a newly authored specification, matching APS-001 through APS-008 at their own first publication.
- **Parent authority:** APP-000 — Atlas Product Doctrine (Draft v0.4); APP-001 — Atlas Product Concept Taxonomy (Draft v0.4), specifically §4 (Discover's own newly-recorded deferral) and §9 item 10 (Discover reserved for this specification).
- **Dependencies:** APS-001 — Decision Context (Draft v0.1), for the lifecycle Discover routes toward but never touches directly. APS-006 — Portfolio (Draft v0.1), for the Atlas Priority Model it adopts by reference and the entry-point relationship Portfolio already established toward it (PF-R-020). APS-007 — Watchlist (Draft v0.1), for the upstream-source relationship Watchlist already established from its own side (WL-R-014) and the Follow/progression discipline this specification reuses. APS-008 — Daily Brief (Draft v0.1), for the Discover Highlight preview relationship Daily Brief already established from its own side (DB-R-016, DB-R-060).
- **Scope:** Discover's own identity, ownership, responsibilities, relevance model, information hierarchy, relationship to Portfolio, Daily Brief, Watchlist, Investment Case, Decision Context, Decision, Outcome, Investor Lab, the Atlas Priority Model, and future Monitoring, Signals, Themes, and AI; its exclusions; and the Atlas/Investor responsibility split.
- **Non-scope:** Screens, workflows, navigation, visual design, interaction design, implementation, algorithms, data schemas, persistence mechanisms; the exact candidate-sourcing or ranking algorithm; any amendment to APP-000, APP-001, APS-001 through APS-008, Atlas Core, or `docs/atlas_ux/`.
- **Affected documents:** None requiring amendment. `APP-001` already reserved this territory in its own v0.4 amendment (§4, §9) and requires no further change.
- **Superseded documents:** None, in the formal sense `Architecture-Governance.md` §7 defines. The Phase II "Discover" product specification is this document's own primary source material, but it was never committed to this repository; §7's Supersession Notice mechanism does not apply to a document that was never itself a repository document.
- **Migration requirements:** None. No existing repository document, and no implementation, is required to change as a consequence of this document's creation. This document completes the four-specification APS expansion (Portfolio, Watchlist, Daily Brief, Discover) the accepted Product Architecture Reconciliation Design set out.

## 2. Purpose

Discover requires its own specification because APP-001 §4 names it as newly-recorded deferred territory but does not itself state Discover's product behavior. This specification closes that gap: it states Discover's own identity as the product surface responsible for expanding the Investor's opportunity set beyond what is already owned or intentionally followed — never portfolio management, never Reasoning, never Decision-making — its responsibilities, its relevance model, its relationships, and its boundary against every neighboring area, so that a future UX specification, an implementation design, engineering, QA, and any AI agent working on Atlas can build from it without inventing new Discover product rules of their own.

Discover's own central user question is *"what should I investigate next?"* — distinct from Portfolio's "where do I stand" (APS-006 §2), Watchlist's "what should I continue following" (APS-007 §2), and Daily Brief's "what has changed since I last looked" (APS-008 §2). Discover is the only one of the four specifications in this expansion whose content is not bounded to what the Investor already owns, follows, or has reasoned about — its entire responsibility is expanding that set.

This specification is re-derived from the Phase II "Discover" product specification, the Product Architecture Review, and Architecture Resolutions — three source documents that were never committed to this repository and hold no independent authority of their own. Their valid product decisions are translated, not copied, into this specification's own requirements.

## 3. Scope

In scope: Discover's identity as a product-level surface; its ownership and responsibility boundary; its relevance model; its information hierarchy; its relationship to Portfolio, Daily Brief, Watchlist, Investment Case, Decision Context, Decision, Outcome, Investor Lab, the Atlas Priority Model, and future Monitoring, Signals, Themes, and AI; explicit Follow and progression behavior; its role as the previewed party within Daily Brief; empty state and user-maturity behavior; and the Atlas/Investor responsibility split.

Out of scope, per APP-000 §1 and §10: screens, workflows, navigation, visual design, interaction design, algorithms, data schemas, persistence mechanisms, or any other implementation technique. Also out of scope: the exact candidate-sourcing, ranking, or relevance-computation algorithm (Section 25); multi-portfolio compatibility (Section 17, Section 25); Monitoring's, Signals', and AI's own complete product behavior, none yet specified anywhere; and any resolution of the Core-track Evidence discrepancy, which this specification does not reopen.

## 4. Governing References

- **`ATLAS_CONSTITUTION.md`.** Normative, superior to every document in the Atlas Product Architecture track.
- **APP-000 — Atlas Product Doctrine, Draft v0.4.** Normative, superior to this specification.
- **APP-001 — Atlas Product Concept Taxonomy, Draft v0.4.** Normative, superior to this specification; §4 reaffirms Discover's own deferral and names this specification as its subject; §9 item 10 reserves this specification's own sequencing position.
- **APS-001 — Decision Context, Draft v0.1.** Normative, superior to this specification; governs the lifecycle Discover routes toward but never touches directly (Section 7, Section 8).
- **APS-006 — Portfolio, Draft v0.1.** Normative, superior to this specification; defines the Atlas Priority Model (§10) this specification adopts by reference (Section 11); already established, from its own side, that Portfolio surfaces an entry point toward Discover without embedding it (PF-R-020).
- **APS-007 — Watchlist, Draft v0.1.** Normative, superior to this specification; already established, from its own side, that Discover is Watchlist's own most common upstream source, and that every resulting Entry still requires its own explicit Follow act (WL-R-014).
- **APS-008 — Daily Brief, Draft v0.1.** Normative, superior to this specification; already established, from its own side, the Discover Highlight bounded preview it hosts (DB-R-016, DB-R-059–064).
- **`OE-002` — Domain Object Model, Final.** Normative for Atlas Core; confirms Discover introduces no new Domain Object (Section 6).
- **The Product Architecture Reconciliation Design** (accepted, this repository's own prior governance work). Non-normative in the sense that it is not itself a Product Architecture document — cited as the source of the migration sequencing that places this specification last among the four, and as this expansion's own final step.
- **The Phase II "Discover" product specification.** Non-normative source material only, never committed to this repository, holding no authority of its own. Its nine information categories, thread-relevance model, six discovery flows, and success criteria are translated, not copied, into this specification's own requirements.
- **The Phase II "Product Architecture Review" and "Architecture Resolutions."** Non-normative source material only, for the same reason. The Atlas Priority Model and the bounded-preview discipline originate in Architecture Resolutions' own analysis, already adopted as accepted architecture in APS-006 §10 and §13, and reused here by reference rather than restated as independent authority.

## 5. Definitions

Only concepts not already defined by APP-000, APP-001, APS-001, APS-006, APS-007, or APS-008 are defined here.

**Thread.** Ordinary-language description of a thematic, sectoral, or strategic connection between a candidate and something the Investor already owns, follows, or has reasoned about. Not a formal Product Concept; the organizing relevance mechanism of this entire specification, defined in full in Section 9.

**Candidate.** Ordinary-language description of a subject Discover surfaces for the Investor's own consideration, not yet the subject of a Follow act. Not a formal Product Concept, mirroring APS-007's own treatment of a Watchlist Entry prior to Follow. A Candidate carries no independent identity, ownership, lifecycle, or responsibility of its own under this specification.

**High Conviction Idea.** Discover's own top-line category — a scoped view of the Atlas Priority Model (APS-006 §10), applied to Candidates outside the Investor's own owned and followed set. Defined in full in Section 11.

**Ignored Noise.** An optional, non-default transparency view of Candidates Discover's own relevance filtering excluded. Governed by Section 10; never part of Discover's own default presentation.

## 6. Architectural Position

**DS-R-001.** Discover SHALL be subordinate to APP-000, APP-001, APS-001, APS-006, APS-007, and APS-008; it SHALL NOT contradict any of the six or redefine a term any of them defines.

**DS-R-002.** Discover SHALL NOT be treated as a Core Domain Object, and SHALL NOT be, or be treated as, reference-eligible within Atlas Core.

**DS-R-003.** Discover SHALL NOT be treated as identical to, or a replacement for, Portfolio, Watchlist, Daily Brief, Investment Case, or Decision Context.

**DS-R-004.** Discover SHALL NOT be treated as a Decision Engine concept. It does not perform Reasoning, does not exercise Investor Judgment, does not record a Decision, and does not evaluate Decision Quality.

**DS-R-005.** Discover SHALL NOT be treated as a pure UX artifact carrying no Product responsibility. It owns real product responsibility, stated in Section 8 through Section 14.

**DS-R-006.** Discover SHALL NOT introduce a new Core Domain Object. Where Core has no adopted primitive for a fact Discover needs to present, that gap is recorded as an open question (Section 25), never silently resolved by this specification.

## 7. Core Properties and Ownership

**DS-R-007.** Discover SHALL be owned by the Investor, in the same sense Portfolio, Watchlist, and Daily Brief are Investor-owned (APS-006 §7, APS-007 §7, APS-008 §7).

**DS-R-008.** Discover SHALL derive its own candidates by evaluating a universe outside the Investor's own owned positions and Watchlist Entries, connected back to that universe only through a Thread, per Section 9. It SHALL NOT originate a Decision, a Judgment, an Outcome, an Observation, or any other Core Domain Object.

**DS-R-009.** Discover SHALL answer an atemporal, continuously-evaluated question — what is worth investigating, evaluated fresh against the current universe — never a temporal delta question; this is Discover's own defining distinction from Daily Brief (APS-008 §2, DBINV-003), stated here as this specification's own architectural position.

**DS-R-010.** Discover SHALL NOT alter, mutate, or supersede any Investment Case, Decision Context, Decision, Outcome, or Watchlist Entry it reads. Every relationship Discover holds to these concepts is read-only.

**DS-R-011.** Discover SHALL NOT require the existence of any owned position, Watchlist Entry, or Investment Case to have some content to present; an Investor with none of these remains a valid, presentable Discover state, per Section 15.

**DS-R-012.** Discover's own central user question — *"What should I investigate next?"* — SHALL govern every category of content this specification defines. A category that does not serve this question does not belong in Discover, regardless of its own informational value.

**DS-R-013.** Discover SHALL remain the only one of the four specifications in this expansion whose content is not bounded to the Investor's own owned, followed, or reasoned-about set; every other requirement in this specification operates within that distinction, not against it.

## 8. Concept Relationships

Each relationship below is classified as existing, derived, product-level, deferred, future-facing, or not applicable, per this specification's own required precision.

**DS-R-014.** Discover's relationship to **Portfolio** is existing and product-level: Discover MAY read Portfolio's own owned-position data to compute thread-relevance for Portfolio-Fit-style candidates (Section 10), but SHALL NOT write to Portfolio; Portfolio, per APS-006 PF-R-020, surfaces an entry point toward Discover without embedding it — Discover remains the destination, never a preview hosted within Portfolio.

**DS-R-015.** Discover's relationship to **Daily Brief** is existing and product-level: Daily Brief hosts a bounded Discover Highlight preview, reading state Discover exposes for exactly this purpose, per APS-008 DB-R-016 and DB-R-059 through DB-R-064. Discover is the previewed party in this relationship, governed from this side in Section 14.

**DS-R-016.** Discover's relationship to **Watchlist** is existing and product-level: Discover MAY read Watchlist's own state to compute Watchlist-Candidates-style relevance (unfollowed subjects resembling existing Entries); Discover is Watchlist's own most common upstream source in practice, per APS-007 WL-R-014, but every resulting Entry still requires its own explicit Follow act, per Section 12.

**DS-R-017.** Discover's relationship to **Investment Case** is existing and product-level: a Candidate MAY progress into an Investment Case, per Section 13, but never does so automatically; the Candidate itself is never an Investment Case and is never treated as one prior to that progression.

**DS-R-018.** Discover's relationship to **Decision Context** is not applicable, mirroring APS-007 WL-R-016: Discover SHALL NOT create, hold, or reference a Decision Context. That relationship begins only once a Candidate has progressed into an Investment Case and genuine Reasoning has begun within it, per APS-001 §8.

**DS-R-019.** Discover's relationship to **Decision** is not applicable: no Decision is ever recorded against a mere Candidate.

**DS-R-020.** Discover's relationship to **Outcome** is not applicable, for the same reason as DS-R-019: an Outcome presupposes a Decision, and a Candidate, by definition, has none.

**DS-R-021.** Discover's relationship to **Investor Lab** is future-facing and, at present, indirect, mirroring APS-006 PF-R-022, APS-007 WL-R-019, and APS-008 DB-R-021: no specification has yet been reserved for Investor Lab. Discover holds no direct relationship to it today.

**DS-R-022.** Discover's relationship to the **Atlas Priority Model** (APS-006 §10) is derived and product-level: Discover's own High Conviction Ideas category (Section 11) is a scoped view of this one shared model, applied to Candidates outside the owned and followed set, never an independently computed ranking, per PF-R-034's own explicit invitation for future specifications to adopt it by reference.

**DS-R-023.** Discover's relationship to future **Monitoring** is future-facing and out of current scope. This specification records only that a monitored condition on a followed or owned subject, once Monitoring is specified, is the natural kind of fact that would sharpen a Candidate's own timing relevance (Section 10, Valuation Opportunities) — this claim commits this specification to no design decision for Monitoring itself.

**DS-R-024.** Discover's relationship to future **Signals** is future-facing and out of current scope, mirroring APS-007 WL-R-021 and APS-008 DB-R-024: a Signal, once specified, is a Candidate fact competing for the same relevance filter every other Candidate passes through, per Section 9 — never a separate content type, and never an autonomous act on Discover's own behalf.

**DS-R-025.** Discover's relationship to **Themes** is existing-and-internal, with a future-facing depth dimension: Discover's own Themes & Trends category (Section 10) already exists as internal content; a future, dedicated Themes capability, if ever specified, would deepen or expand this existing mechanism, never create a new one, mirroring the Phase II source material's own explicit ruling on this point.

**DS-R-026.** Discover's relationship to future **AI** is future-facing and bounded by principle now, per PP-003 and PP-008: AI MAY draft or improve the rationale explaining why a Candidate surfaced (Section 9, "why this" requirement); AI SHALL NOT originate a Candidate's own inclusion, compute its own ranking independent of the Atlas Priority Model, or exercise Investor Judgment on the Investor's behalf.

## 9. The Relevance Model — Thread Connection

**DS-R-027.** A Candidate SHALL surface in Discover only where a Thread connects it to something the Investor already owns, follows, or has reasoned about — a theme, sector, or strategy already reflected in existing state, per Section 5.

**DS-R-028.** Relevance under this specification is deliberately broader than Daily Brief's own relevance model (APS-008 DB-R-026): a Thread MAY connect a Candidate the Investor has never owned or followed, provided the thematic or strategic connection is real and statable — mere novelty or popularity SHALL NOT itself constitute a Thread.

**DS-R-029.** Discover SHALL NOT surface a Candidate with no statable Thread, however popular, notable, or globally significant that Candidate may otherwise be.

**DS-R-030.** Every Candidate Discover presents SHALL carry an identifiable, traceable explanation of its own Thread; a Candidate with no such explanation SHALL NOT be presented, per DS-F-009.

**DS-R-031.** Discover SHALL accept, as an explicit product tradeoff, that a genuinely interesting Candidate with no current Thread will not appear; this specification does not treat that omission as a defect, per DS-R-028's own broader-than-Daily-Brief relevance model still requiring some real connection.

**DS-R-032.** The exact computational method by which a Thread is identified or scored is not defined by this specification; Section 9's own requirements state what qualifies, not how qualification is computed. See Section 25.

## 10. Information Hierarchy — Anchored to Exploratory

Stated as responsibility, not layout, mirroring APS-006 §9 and APS-008 §10's own discipline. Categories are organized along a spectrum from candidates anchored tightly to existing owned or followed state, to candidates that are genuinely exploratory but still Thread-connected.

**DS-R-033.** **Portfolio Fit** SHALL present candidates evaluated specifically against a gap or concentration in the Investor's own current owned positions, read from Portfolio per DS-R-014. The most directly anchored category.

**DS-R-034.** **Recently Strengthened Investment Cases** SHALL present Investment Cases where new Evidence or Reasoning has recently reinforced the existing Investor Reasoning or Decision, prompting reconsideration of conviction or sizing — Discover looking inward at the Investor's own reasoning history, the mirror image of Daily Brief's own Thesis-Impacting Change (APS-008 §13), framed here as opportunity rather than alert.

**DS-R-035.** **Watchlist Candidates** SHALL present unfollowed subjects resembling the Investor's own existing Watchlist Entries, read from Watchlist per DS-R-016.

**DS-R-036.** **Themes & Trends** SHALL group candidates under an explicit theme already reflected in the Investor's own holdings, Watchlist, or Investment Case history — the clearest embodiment of Section 9's own Thread requirement.

**DS-R-037.** **Sector Rotation** SHALL flag sectors gaining relative strength, filtered to sectors in which the Investor already has exposure or stated interest — never an unfiltered sector overview.

**DS-R-038.** **High Conviction Ideas** SHALL present the small set of candidates ranked highest by the Atlas Priority Model, per Section 11 — Discover's own verdict-equivalent tier.

**DS-R-039.** **Emerging Industries** SHALL present nascent categories without requiring an already-owned or already-followed adjacent position, remaining Discover's own most exploratory category; every Candidate within it SHALL still satisfy Section 9's own Thread requirement to avoid becoming an arbitrary trending list, per DS-F-003.

**DS-R-040.** **AI Opportunities** SHALL be presented as one named instance of the Themes & Trends mechanism (DS-R-036), never as a structurally separate category or sourcing mechanism of its own.

**DS-R-041.** **Valuation Opportunities** SHALL be presented as a cross-cutting timing lens applied across other categories — explaining why a Candidate that already qualified under Portfolio Fit, a Theme, or a Sector has newly become worth surfacing — never as an independent sourcing category of its own.

**DS-R-042.** **Ignored Noise** SHALL NOT be part of Discover's own default presentation; where offered, it SHALL be an explicit, opt-in transparency view, per Section 5, never surfaced automatically alongside the categories above.

**DS-R-043.** This hierarchy SHALL NOT be read to assert a required visual order, layout, or screen position; it states which category is more anchored or more exploratory, not where any category appears.

**DS-R-044.** A future UX specification MAY order these categories differently in presentation, provided the underlying anchored-to-exploratory responsibility boundary each category states is preserved.

## 11. Priority Model Integration — High Conviction Ideas

**DS-R-045.** High Conviction Ideas SHALL be a scoped view of the Atlas Priority Model (APS-006 §10), filtered to Candidates outside the Investor's own owned and followed set.

**DS-R-046.** Discover SHALL NOT compute an independent ranking of importance separate from the Atlas Priority Model for any category defined in Section 10.

**DS-R-047.** Where High Conviction Ideas and Portfolio's own Requires Attention, or Daily Brief's own Verdict, present a related but distinct fact, they SHALL NOT be permitted to disagree about any shared underlying fact; they MAY differ in scope — owned-and-open (Portfolio, Daily Brief) versus not-yet-owned-or-followed (Discover) — per APS-006 PFINV-009 and APS-008 DB-R-044, extended here to Discover's own scope.

**DS-R-048.** High Conviction Ideas SHALL NOT itself constitute a Decision, a Judgment, or an act of Investor Judgment; it surfaces candidates for the Investor's own attention and nothing more, per PP-003.

## 12. Explicit Follow and Watchlist Progression

**DS-R-049.** Discover SHALL NOT automatically create a Watchlist Entry from any Candidate; every Entry requires its own explicit Follow act, per APS-007 WL-R-007 and WL-R-022, regardless of how strongly a Candidate is ranked within Discover.

**DS-R-050.** A Follow act originating from Discover SHALL be governed entirely by APS-007's own requirements once the act occurs; this specification does not restate Watchlist's own Follow mechanics.

**DS-R-051.** Discover SHALL NOT infer investor intent to Follow from viewing, dwelling on, or repeatedly encountering a Candidate; only an explicit Investor act SHALL create a Watchlist Entry, per PP-003 and PP-005.

**DS-R-052.** A Candidate MAY be ignored, dismissed, or left un-Followed by the Investor without penalty or consequence, mirroring APS-007's own consequence-free-Release discipline (WLINV-008) applied here to the decision not to Follow in the first place.

## 13. Routing into Investment Case

**DS-R-053.** Discover SHALL support progression of a Candidate directly into an Investment Case, without requiring an intermediate Watchlist Entry, triggered only by a genuine, further Investor act of choosing to seriously evaluate that Candidate.

**DS-R-054.** Progression under DS-R-053 SHALL follow the same silent, genuine-intent creation discipline APS-001 already establishes for Decision Context (DC-R-017, DC-R-021) and APS-006 already establishes for Investment Case (PF-R-047); Discover SHALL NOT require the Investor to name, configure, or administratively set up the resulting Investment Case.

**DS-R-055.** Where a Candidate has already progressed into a Watchlist Entry, its further progression into an Investment Case SHALL be governed by APS-007's own progression requirements (WL-R-025 through WL-R-027), not restated here.

**DS-R-056.** Discover SHALL NOT present any interface implying an Investment Case is a thing to be created independent of a genuine reasoning act — no standalone "create a Case" affordance is authorized by this specification, mirroring APS-006 PF-R-049.

## 14. Discover as the Previewed Party — Discover Highlights

Discover is the only one of the four specifications in this expansion that is never itself a host of a bounded preview of another area; it is only ever the previewed party. This section governs that one relationship from Discover's own side; APS-008 §14 governs it from Daily Brief's own side as host.

**DS-R-057.** Discover SHALL expose a small, curated summary of its own current High Conviction Ideas and Emerging Industries content sufficient for Daily Brief's own bounded Discover Highlight preview, without requiring Daily Brief to re-implement Discover's own relevance filtering.

**DS-R-058.** Discover SHALL NOT require or assume that Daily Brief's own preview of it reproduces Discover's own content in full; a preview reading a small, curated subset is sufficient and expected, per APS-008 DB-R-057.

**DS-R-059.** No fact material to understanding a Discover Highlight SHALL exist only within Daily Brief's own bounded preview of it; the full, current Discover SHALL always be available in Discover's own area.

**DS-R-060.** Discover Highlights SHALL remain small and deliberately curated; a Discover Highlight preview that grows to resemble Discover's own full category set is a failure mode, per DS-F-004.

## 15. Empty Discover and New-Investor Behavior

**DS-R-061.** Discover SHALL present a valid, honest state for an Investor with no owned positions, no Watchlist Entries, and no Investment Case history — the condition under which Section 9's own Thread requirement has the least existing state to connect against.

**DS-R-062.** Where genuinely no Thread-connected Candidate exists for a new Investor, Discover MAY present a small set of broadly orienting candidates explicitly framed as introductory, distinct from and less confidently presented than Thread-connected content elsewhere; this specification does not require such a fallback, and does not authorize presenting it with the same confidence as genuinely connected content.

**DS-R-063.** Discover's own value to a first-time Investor SHALL NOT depend on any administrative setup step beyond whatever entry flow already established owned positions or Watchlist Entries elsewhere, per APS-006 PF-R-059 and APS-007 WL-R-041.

**DS-R-064.** Discover SHALL NOT fabricate a Thread-connected Candidate to avoid appearing empty for a new Investor; an honest, smaller, or introductory-framed result set is preferable to a fabricated one, per PP-007 and DS-F-009.

## 16. Repeat Visits and Established-Investor Behavior

**DS-R-065.** Discover SHALL NOT be required to track every individual prior visit's own exact content, unlike Daily Brief's own repeat-visit discipline (APS-008 §17); Discover is evaluated fresh against the current universe on each visit, per DS-R-009, and a Candidate MAY legitimately reappear across visits where its own Thread remains current.

**DS-R-066.** Discover's own behavior for an established Investor with many owned positions, many Watchlist Entries, and many Investment Cases SHALL scale by the anchored-to-exploratory hierarchy (Section 10) and by the Atlas Priority Model (Section 11), never by presenting every possible Candidate with equal prominence.

**DS-R-067.** Discover SHALL NOT manufacture urgency, novelty, or engagement pressure to encourage a return visit; per `ATLAS_CONSTITUTION.md`'s own Product Philosophy, Atlas does not use urgency as a product mechanic.

## 17. Future Multi-Portfolio Compatibility

**DS-R-068.** This specification assumes exactly one Portfolio and one Watchlist per Investor, consistent with APS-006 §15 and APS-007 §16's own identical assumptions, and computes thread-relevance against that single scope.

**DS-R-069.** This specification SHALL NOT be read to assert that multi-portfolio-scoped Discover relevance is unsupportable; it states only that this specification does not define it, per Section 25.

## 18. Explicit Exclusions

**DS-R-070.** Discover SHALL NOT become Portfolio. Portfolio presents owned-position state; Discover operates entirely outside that owned set, per DS-R-013. Different universes.

**DS-R-071.** Discover SHALL NOT become Watchlist. Watchlist is static storage of decisions already made about what to track; Discover is the generative process upstream of it, per APS-007 WL-R-048's own identical reasoning restated from Discover's own side.

**DS-R-072.** Discover SHALL NOT become Daily Brief. Daily Brief is a bounded, temporal delta digest; Discover is continuous and atemporal, evaluated fresh against the full universe on each visit, per DS-R-009 and APS-008 DBINV-003.

**DS-R-073.** Discover SHALL NOT become Decision Workspace. Reasoning is performed and permanently recorded through Decision Context and Investor Reasoning, governed by APS-001 and APS-002; Discover never lets the Investor record an Observation, a Judgment, or a Decision directly, per DS-R-004.

**DS-R-074.** Discover SHALL NOT become a chat interface. Discover surfaces structured, categorized Candidates, each with an explicit Thread-based reason for surfacing, per Section 9; it is not an open-ended conversational surface for arbitrary Investor questions, which would blur its own filtered, curated responsibility into an unbounded one.

**DS-R-075.** Discover SHALL NOT become a news feed. It surfaces opportunities via Thread connection, per Section 9, never raw events reported for their own newsworthiness.

**DS-R-076.** Discover SHALL NOT become a market screener. Screening requires the Investor to already know which filters to apply; Discover proactively generates Candidates without requiring the Investor to specify criteria first, per DS-R-027.

**DS-R-077.** Discover SHALL NOT become a stock database. A database is exhaustive and neutral, presenting everything with equal weight for lookup; Discover is opinionated and selective, presenting only what it believes, via a real Thread, is worth attention.

**DS-R-078.** Discover SHALL NOT become a recommendation engine without explanation. Every Candidate SHALL carry a traceable Thread-based explanation for its own inclusion, per DS-R-030; a Candidate presented with no such explanation is a failure mode, per DS-F-009.

## 19. Atlas Responsibilities

**DS-R-079.** Atlas SHALL evaluate the current universe of candidates against the Investor's own owned positions, Watchlist Entries, and Investment Case history to identify Thread connections, per Section 9.

**DS-R-080.** Atlas SHALL filter every candidate against DS-R-027 before presenting it as a Candidate within Discover.

**DS-R-081.** Atlas SHALL populate High Conviction Ideas from the Atlas Priority Model, per Section 11, never from an independently computed ranking.

**DS-R-082.** Atlas SHALL NOT create a Watchlist Entry or progress a Candidate into an Investment Case without an explicit, identifiable Investor act, per Section 12 and Section 13.

**DS-R-083.** Atlas SHALL disclose an empty Discover state explicitly, per DS-R-061, rather than presenting an ambiguous or silently omitted state.

**DS-R-084.** Atlas SHALL preserve the read-only boundary stated in DS-R-010 in every computation Discover performs; no Discover-level computation SHALL alter a Core Domain Object or an already-accepted Product record.

**DS-R-085.** Atlas SHALL attribute the origin of any Atlas-originated content Discover presents, per PP-008, including any AI-drafted rationale under DS-R-026.

## 20. Investor Responsibilities

**DS-R-086.** The Investor owns every Follow act and every progression act originating from Discover, and the Watchlist Entry or Investment Case each produces.

**DS-R-087.** The Investor remains responsible for deciding whether a Candidate warrants Follow or further investigation; Discover surfaces the Candidate, never the decision, per PP-003.

**DS-R-088.** The Investor remains accountable for any Decision later reached after progressing a Discover Candidate into an Investment Case, in the same manner APP-000 §8.2 already states generally.

## 21. Invariants

**DSINV-001 — No Core Object Status.** Discover SHALL NOT be treated as a Core Domain Object or as Core-reference-eligible.

**DSINV-002 — Distinctness from Portfolio.** Discover SHALL NOT be treated as identical to, or a replacement for, Portfolio; Discover operates outside the owned set, per DS-R-013.

**DSINV-003 — Distinctness from Watchlist.** Discover SHALL NOT be treated as identical to, or a replacement for, Watchlist; Discover is the generative process, Watchlist the static storage it feeds.

**DSINV-004 — Distinctness from Daily Brief.** Discover SHALL NOT be treated as identical to, or a replacement for, Daily Brief; Discover is atemporal and continuous, Daily Brief is a bounded temporal delta.

**DSINV-005 — Discover Never Owns Decisions.** Discover SHALL NOT own, record, or imply a Decision for any Candidate.

**DSINV-006 — Discover Never Creates Decisions.** No requirement in this specification SHALL be read to authorize Discover creating, recording, or triggering a Decision under any circumstance.

**DSINV-007 — Single Priority Model.** Discover SHALL NOT compute an independent priority or ranking model separate from the Atlas Priority Model.

**DSINV-008 — No Automatic Watchlist Creation.** Discover SHALL NOT automatically create a Watchlist Entry from any Candidate absent an explicit Follow act.

**DSINV-009 — Explicit Intent Before Progression.** Every progression of a Candidate into a Watchlist Entry or an Investment Case SHALL be traceable to an explicit Investor act; no progression SHALL be observed occurring through inference, default, or automation.

**DSINV-010 — No Manual Case Administration.** Where Discover routes into a new Investment Case, it SHALL NOT require the Investor to manually create, name, or configure it.

**DSINV-011 — Traceable Candidates.** Every Candidate Discover presents SHALL carry an identifiable, traceable Thread; no Candidate SHALL be presented with no statable reason for its own inclusion.

**DSINV-012 — Previews Are Not Destinations.** The bounded preview Daily Brief hosts of Discover SHALL NOT be treated as the complete destination for Discover's own content.

**DSINV-013 — Read-Only Relationship to Core and Product Records.** Discover SHALL NOT mutate any Investment Case, Decision Context, Decision, Outcome, Watchlist Entry, or Portfolio content it reads.

**DSINV-014 — No Autonomous Commitment.** Discover SHALL NOT cause a Decision Context to close by Commitment, and SHALL NOT present any Discover-level action as though it had done so, per APS-001 DCINV-006.

**DSINV-015 — No New Core Relationship.** This specification, and Discover as it governs, SHALL NOT introduce or rely upon a Core relationship, Core Domain Object, or Core invariant beyond those already adopted in `OE-002` and `OE-004`.

**DSINV-016 — Evidence Remains Product-Layer Only.** This specification SHALL NOT describe Evidence as a Core Domain Object anywhere it is mentioned, per APS-003 EV-R-002 and `OE-002` §4's own closed Domain Object Set.

## 22. Failure and Refusal Behavior

Atlas SHALL fail closed: where continuing would violate this specification, APP-000, APP-001, APS-001, APS-006, APS-007, APS-008, or a Core invariant, Atlas SHALL refuse or halt the action rather than proceed on an assumed or inferred basis. No UI error message is prescribed by this section or by this specification.

**DS-F-001 — Everything is recommended.** Atlas SHALL NOT present a Candidate that fails the Thread requirement of DS-R-027; this violates `DSINV-011` and defeats Discover's own filtered, curated purpose.

**DS-F-002 — Nothing relevant is ever found, and Discover fails to say so.** Where genuinely no Thread-connected Candidate exists, Atlas SHALL state this plainly, per DS-R-061, rather than presenting a blank or broken-seeming surface; the absence itself is not the failure, an undisclosed absence is.

**DS-F-003 — Discover becomes trending stocks.** Atlas SHALL refuse to surface a Candidate on the basis of general popularity or trending status alone, with no statable Thread; this violates DS-R-028, DS-R-029, and `DSINV-011` directly.

**DS-F-004 — Discover becomes news.** Atlas SHALL refuse to report a Candidate for its own general newsworthiness rather than a Thread connection; this violates DS-R-075.

**DS-F-005 — Discover becomes Portfolio.** Atlas SHALL refuse to present owned-position state, or any Portfolio-owned category, within Discover itself; this violates `DSINV-002` and DS-R-070.

**DS-F-006 — Discover becomes AI chat.** Atlas SHALL refuse to present an open-ended conversational interface in place of Discover's own structured, categorized presentation; this violates DS-R-074.

**DS-F-007 — Discover creates urgency without justification.** Atlas SHALL refuse to frame a Candidate with urgency not supported by a genuine timing signal under Valuation Opportunities (DS-R-041) or an equivalent traceable basis; this violates DS-R-067 and `ATLAS_CONSTITUTION.md`'s own Product Philosophy.

**DS-F-008 — Discover automatically progresses opportunities.** Atlas SHALL refuse to create a Watchlist Entry or an Investment Case from a Candidate absent an explicit Investor act; this violates `DSINV-008`, `DSINV-009`, and mirrors APS-001 DCINV-006's own discipline against autonomous Commitment.

**DS-F-009 — A Candidate is presented with no traceable Thread.** Atlas SHALL refuse to present the Candidate; this violates DS-R-030 and `DSINV-011` directly.

**DS-F-010 — Discover Highlights grows to resemble Discover's own full category set.** Atlas SHALL refuse to expand the Daily-Brief-hosted preview beyond a small, curated subset, per DS-R-060; this violates `DSINV-012`.

## 23. Acceptance Criteria

**DS-AC-001 (Purpose understood).** Discover's own content is observed to answer "what should I investigate next," distinctly from Portfolio's "where do I stand," Watchlist's "what should I continue following," and Daily Brief's "what has changed," per DS-R-012 and `DSINV-002` through `DSINV-004`.

**DS-AC-002 (Expands rather than repeats).** No Candidate presented in Discover is ever observed limited to the Investor's own already-owned positions; every Candidate is observed connected via a Thread that extends beyond the current owned-and-followed set, per DS-R-013 and DS-R-027.

**DS-AC-003 (Watchlist progression requires explicit intent).** Every Watchlist Entry traceable to Discover is observed to originate from an explicit Follow act; no Entry is ever observed created by inference or automation, per `DSINV-008` and `DSINV-009`.

**DS-AC-004 (Investment Cases emerge only through genuine action).** Every Investment Case traceable to Discover is observed to originate from a genuine, further Investor act distinct from mere Candidate presentation, per DS-R-053 and DS-R-054.

**DS-AC-005 (Priority consistency with APS-006 and APS-008).** No shared underlying fact between High Conviction Ideas, Portfolio's own Requires Attention, and Daily Brief's own Verdict is ever observed in disagreement; differences are observed limited to scope framing, per DS-R-047.

**DS-AC-006 (No Core or Decision Engine redesign).** No requirement in this specification is observed to require a new Core Domain Object, a new Core invariant, or a change to the Decision Engine's own existing behavior, per `DSINV-001`, `DSINV-005`, `DSINV-006`, and `DSINV-015`.

**DS-AC-007 (Traceable candidates).** Every Candidate presented in Discover is observed accompanied by an identifiable Thread explanation; no Candidate is ever observed with no stated reason for its own inclusion, per `DSINV-011`.

**DS-AC-008 (Previews are not destinations).** The Discover Highlight preview hosted within Daily Brief is observed to link to Discover's own full destination and is never observed as the sole presentation of Discover's own content, per `DSINV-012`.

**DS-AC-009 (Single priority model).** No independently computed ranking is ever observed within Discover's own content, per `DSINV-007`.

**DS-AC-010 (Traceability).** Every requirement in Sections 6 through 20 is traceable, by citation, to at least one of: `ATLAS_CONSTITUTION.md`, an APP-000 Product Principle, an APP-001 provision, an APS-001 provision, an APS-006 provision, an APS-007 provision, an APS-008 provision, or a Core same-Case requirement, per Section 24.

## 24. Traceability

| Requirement / Invariant | Normative basis | Source material (non-normative) | Core basis | Core basis status |
|---|---|---|---|---|
| DS-R-001–006, `DSINV-001` | APP-000 §2, §9; APP-001 §1 | — | `OE-002` §4 (closed Domain Object Set excludes Discover) | Normative (Core) |
| DS-R-007–013, `DSINV-002`, `DSINV-003`, `DSINV-004` | APP-001 §4 | Discover §1 (Purpose) | — | This specification's own product decision, mirroring APS-006 §7 through §8 |
| DS-R-014 | APS-006 §8 PF-R-020 | Discover §6 (Relationship to Portfolio) | — | Normative (Product), cited not redefined |
| DS-R-015, `DSINV-012` | APS-008 §8 DB-R-016, §14 DB-R-059–064 | Discover §6 (Relationship to Daily Brief) | — | Normative (Product), cited not redefined |
| DS-R-016 | APS-007 §8 WL-R-014 | Discover §6 (Relationship to Watchlist) | — | Normative (Product), cited not redefined |
| DS-R-017–020 | APP-001 §3.13 (Investment Case); APS-001 §8 | Discover §6 (Relationship to Investment Cases, Decision Workspace) | `OE-002` §5.5 Decision, §5.6 Outcome | Normative (Core), cited not redefined |
| DS-R-021 | — | Entry Flows §2 (Investor Lab, future) | — | This specification's own product decision |
| DS-R-022, `DSINV-007` | PP-001 | Architecture Resolutions, Decision 2 (Atlas Priority Model) | — | Normative (Product), per APS-006 §10 |
| DS-R-023–026 | PP-003, PP-008 | Discover §10 (Future expansion table: Signals, Themes, AI, Monitoring) | — | This specification's own product decision |
| DS-R-027–032, `DSINV-011` | PP-001, PP-007 | Discover §2 (Philosophy) | — | This specification's own product decision |
| DS-R-033–044 | PP-001, PP-004 | Discover §4 (Information hierarchy) | — | Reconciliation Design source material, restated normatively |
| DS-R-045–048 | PP-001, PP-003 | Discover §4 (High Conviction Ideas) | — | Normative (Product), per APS-006 §10 |
| DS-R-049–052, `DSINV-008`, `DSINV-009` | PP-003, PP-005 | Discover §7 (Discover → Watchlist flow) | APS-007 WL-R-007, WL-R-022 | Normative (Product), cited not redefined |
| DS-R-053–056, `DSINV-010` | PP-002, PP-003, PP-005 | Discover §7 (Discover → Investment Case flow) | APS-001 DC-R-017, DC-R-021, DCINV-006; APS-006 PF-R-047, PF-R-049 | Normative (Product), cited not redefined |
| DS-R-057–060 | — | APS-006 §13 (Preview Governance); APS-008 §14 (Bounded Previews as Host) | — | Normative (Product), cited not redefined |
| DS-R-061–064 | PP-004; PP-007 | Discover §3 (User intent, new investor) | — | — |
| DS-R-065–067 | PP-001; `ATLAS_CONSTITUTION.md` Product Philosophy | Discover §3, §7 (established investor, repeat visits) | — | This specification's own product decision |
| DS-R-068–069 | — | Product Architecture Review §7 (Scalability); Reconciliation Design Open Questions | — | This specification's own product decision |
| DS-R-070–078, `DSINV-016` | APP-000 §10; `ATLAS_CONSTITUTION.md` Non-Negotiable Principles | Discover §5 (Must not become) | `OE-002` §4 (Evidence excluded); APS-003 EV-R-002 | Normative (Core) for Evidence's own status |
| DS-R-079–088 | PP-001 through PP-009, as cited per line; APP-000 §8.2 | Discover §8 (Atlas responsibilities) | — | — |
| `DSINV-005`, `DSINV-006`, `DSINV-013`, `DSINV-014`, `DSINV-015` | PP-003, PP-005, PP-006 | Product Architecture Review Weaknesses (verdict-triplication finding, adapted) | `OE-002`; `OE-004`; APS-001 DCINV-006 | Normative (Core), cited not redefined |

## 25. Open Questions and Deferred Work

- **Opportunity ranking methodology.** This specification defines what qualifies a Candidate for inclusion (Section 9) and how categories are organized (Section 10), but the precise computational method for ranking within and across categories is implementation and calibration work, not defined here. Classified: **non-blocking for APS-009**.
- **Personalization.** How thread-relevance weighting adapts to an individual Investor's own demonstrated preferences over time is not defined here. Classified: **non-blocking for APS-009**, implementation-level, and coupled to Investor Lab's own eventual specification (Section 8, DS-R-021).
- **Theme maturity and depth.** DS-R-025 names Themes as a future capability that would deepen the existing Themes & Trends mechanism; the exact shape of that deepening is not defined here. Classified: **non-blocking for APS-009**.
- **AI-generated opportunities.** DS-R-026 bounds AI's own role in principle — rationale drafting only, never candidate origination or independent judgment — but does not design the mechanism. Classified: **out of current scope**, pending a dedicated future specification for AI capability generally.
- **Institutional discovery.** Asset-manager multi-mandate discovery needs, coupled to Portfolio's and Watchlist's own identical open questions (APS-006 §24, APS-007 §24), are not addressed here. Classified: **requires separate architecture work**, non-blocking for this specification's own completeness.
- **Whether "Candidate" or "Thread" requires later formal Product Concept treatment.** Genuinely open, mirroring the identical, still-open questions APS-006 §24, APS-007 §24, and APS-008 §28 carry for "Holding," "Watchlist Entry," and "Thesis-Impacting Change." Classified: **deferred** — a candidate for a future, dedicated APP-001 amendment this specification has no authority to propose or enact.

---

*This specification does not modify `ATLAS_CONSTITUTION.md`, `Architecture-Governance.md`, `Atlas-Alpha-Baseline-v1.0.md`, APP-000, APP-001, APS-001 through APS-008, any `docs/atlas_ux/` document, or any source code. It introduces no new Core Domain Object and requires no Atlas Core or Decision Engine redesign. This document completes the four-specification APS expansion (Portfolio, Watchlist, Daily Brief, Discover) set out by the accepted Product Architecture Reconciliation Design.*
