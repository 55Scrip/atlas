# APP-001 — Atlas Product Concept Taxonomy

**Status:** Draft, v0.4. This document sits directly beneath APP-000 — Atlas Product Doctrine and above every APS specification. It clarifies and organizes the product concepts APP-000 implies. It introduces no product philosophy of its own. It does not describe screens, workflows, navigation, interaction, UI, implementation, algorithms, or engineering. Amended in v0.4 to accept Investment Case as a Product Concept and to formally recognize Portfolio, Watchlist, Daily Brief, and Discover as territory this document defers to subordinate specification, per the completed Atlas Product Architecture Reconciliation.

---

## 1. Governing Authority and Method

APP-001 derives entirely from APP-000. Where this document accepts, rejects, merges, or relates a concept, the justification traces to APP-000's own philosophy (Section 6), Product Principles (Section 7), or Definitions (Section 5) — never to convenience, familiarity, or precedent from other Atlas documentation.

APP-001 does not redefine any term APP-000 already defines (Investor, Decision, Reasoning, Evidence, Attention, Uncertainty, Learning, Decision Quality, Investor Judgment). Where this investigation finds that one of those terms itself carries an unresolved risk, it is recorded as an **observation for a future APP-000 amendment**, not corrected here — APP-001 has no authority to amend its own governing document.

Every candidate concept was tested against the nine questions APP-001's own charter specifies: does it genuinely exist; why; what single responsibility does it own; is it permanent, persistent, temporary, or ephemeral; who owns it; what does it relate to; could the product exist without it; could another accepted concept fully replace it. A concept that fails this test — most commonly by owning no responsibility a different, already-accepted concept doesn't already discharge — is rejected regardless of how familiar the word is.

---

## 2. Executive Summary

Eleven concepts survive this investigation: **Investor, Decision, Reasoning, Evidence, Investor Judgment, Learning, Attention, Uncertainty, Decision Quality** (all already defined by APP-000, organized rather than altered here) plus **two new concepts this investigation adds: Decision Context and Outcome.**

Six candidates are rejected outright: **Portfolio** and **Watchlist** (APP-000 itself already defers both to subordinate specifications), **Review** (fully absorbed by Learning), **Knowledge** (fully absorbed by Evidence, and carries a serious, avoidable collision with Atlas Core's own Final `Knowledge`/`Knowledge Reference` ontology), **Insight** (fully absorbed by Evidence's provenance-attribution model), and **Recommendation** (fully absorbed by the same model, and carries a separate, already-litigated collision with the `docs/atlas_ux/` corpus's own ADR-003).

One candidate, **Objective**, is not rejected but merged: it is the defining property of Decision Context, not an independently ownable concept.

**Session** is not on this investigation's candidate list, but is carried forward as rejected, per the dedicated APS-001 Pre-Design Investigation that preceded this document; **Decision Context** is that investigation's recommended replacement, now formally accepted and named here.

**Amended in v0.4:** A twelfth concept, **Investment Case**, is now accepted (§3.13), formally distinguishing it from Decision Context and confirming its 1:1 correspondence to Atlas Core's own `Case` — resolving the Decision Context ↔ Case correspondence this document's own §6 and §8 previously left unconfirmed. **Portfolio** and **Watchlist** remain rejected as independent primitive concepts, per the original reasoning below, but are now explicitly named as approved territory for dedicated subordinate specifications (APS-006, APS-007). **Daily Brief** and **Discover** — product surfaces not considered by the original investigation — are newly recorded in Section 4 on the same deferral basis, approved for APS-008 and APS-009. This amendment is the direct product of the completed Atlas Product Architecture Reconciliation; it does not reopen any other determination this document already made.

Two architectural observations are raised for future action outside this document's own authority: APP-000's `Reasoning` carries the same category of Atlas Core naming collision that `Investor Judgment` was created to resolve, and would benefit from the same treatment in a future APP-000 amendment; and `Outcome`, used informally throughout APP-000's own text without ever being formally defined, is the clearest case this investigation found of Critical Review's own warning — "if APP-000 implicitly assumes a concept that has never been explicitly defined, identify it."

**Verdict:** Atlas Product Architecture is conceptually complete enough to begin APS-001, scoped to Decision Context, now. It is not yet safe to begin any future APS work that touches AI-originated content presentation without first resolving this document's one open cross-track risk — the undetermined relationship between `docs/atlas_product_architecture/` and the separately-governed `docs/atlas_ux/` corpus, which already contains its own settled, and partially conflicting, terminology for AI-originated content. See Section 7. Following the v0.4 amendment, Atlas Product Architecture is also conceptually complete enough to begin APS-006 through APS-009, scoped to Portfolio, Watchlist, Daily Brief, and Discover respectively, in that dependency order — see Section 9. This does not lift the AI-originated-content restriction stated above, which remains in force for any of the four.

---

## 3. Accepted Concepts

Each entry states Purpose, Responsibility, Lifetime, Ownership, Relationships, Product Level (all: **Concept**, per Section 1's scope), and Relationship to Atlas Core.

### 3.1 Investor

**Purpose:** the human party whose capital, judgment, and accountability the entire Product Architecture exists to serve (APP-000 §3).
**Responsibility:** holds ownership of, and accountability for, every Decision — the one responsibility no other concept can be delegated (APP-000 §5, PP-005).
**Lifetime:** Permanent, for the duration of the relationship between the person and Atlas.
**Ownership:** Not applicable — the Investor is the owning party for every other Investor-owned concept below; nothing owns the Investor.
**Relationships:** owns Decision, Reasoning, Investor Judgment, Learning, Attention, and Decision Context. Is the sole party at stake in Decision Quality.
**Core relationship:** No correspondence. Atlas Core has no actor or agent primitive — an early candidate ("Agent") was proposed and explicitly rejected from Core's own settled ontology (ADR-002, Revision 2). This is not a gap; Core's Domain Objects are defined to require no actor at all.

### 3.2 Decision

**Purpose:** the point at which the Investor's engagement with a question becomes a committed, durable fact (APP-000 §5).
**Responsibility:** records that a specific commitment to a course of action regarding capital was made, and when.
**Lifetime:** Permanent. A Decision, once made, is never retracted or overwritten — only ever followed by a later, distinct Decision.
**Ownership:** Investor.
**Relationships:** is what Reasoning connects known facts to; is what Decision Context exists to produce; is what Decision Quality is assessed of; is what Outcome later stands apart from without altering.
**Core relationship:** Approximate. Atlas Core's own `Decision` Domain Object (`OE-002` §5.5) — "a permanent Domain Object that records the Case's settled practical commitment... without itself executing behaviour" — describes the same underlying fact from the architecture layer. The two are compatible in substance, differing only in which aspect each document emphasizes (Core: the record's structural properties; APP-000: its human, accountable significance). No qualification is needed, unlike Investor Judgment; see Section 6.

*(The candidate name "Investment Decision" was considered and rejected as a separate concept — APP-000's own `Decision` is already scoped to "a course of action regarding capital," so the longer name adds a word without adding meaning. Renaming an APP-000-defined term is, in any case, outside this document's authority.)*

### 3.3 Reasoning

**Purpose:** what makes a Decision inspectable, rather than a bare assertion (APP-000 §5, §6.5).
**Responsibility:** connects Evidence and Investor Judgment into an explicit chain leading to a Decision.
**Lifetime:** Persistent while a Decision Context remains open; becomes Permanent once attached to a committed Decision (PP-006 forbids it ever being discarded or silently altered thereafter).
**Ownership:** Investor — APP-000 §6.5 is explicit that reasoning is "a fact about the investor's own mind." Atlas may contribute attributable content to it (PP-008) without acquiring ownership of it.
**Relationships:** composed of Evidence and Investor Judgment; connects to Decision; is what Learning later revisits; arises, develops, and may be revised within a Decision Context, whose own responsibility extends to material that precedes it.
**Core relationship:** Approximate, and worth stating precisely because it is easy to mis-map. Atlas Core's own `Reasoning` is "a standing capability, not an object" (ADR-001) — the human capacity itself, not a record. APP-000's `Reasoning` — an explicit, inspectable *chain* — is functionally much closer to Core's separate `Reasoning Trace` Domain Object ("represents one or more already-accepted Domain Objects as providing epistemic support," `OE-002` §5.3). A future APS specification operationalizing PP-006 SHALL map product-language Reasoning onto Core's `Reasoning Trace`, not onto Core's `Reasoning` or `Reasoning Act`.

### 3.4 Evidence

**Purpose:** the raw material Reasoning is built from (APP-000 §5).
**Responsibility:** preserves a fact or observation, together with its source and reliability, without itself asserting a conclusion.
**Lifetime:** Persistent — retained for as long as it remains referenced by active or historical Reasoning; APP-000 does not mandate permanent retention of Evidence independent of the Reasoning it supports, unlike Reasoning itself.
**Ownership:** Neither — Evidence is a fact with a source, not a possession. It may originate from the Investor, from Atlas, or from an external source; PP-008 requires that origin be attributable in every case, which presupposes Evidence is not, in itself, owned the way a Decision or an act of Investor Judgment is.
**Relationships:** feeds into Reasoning; is what PP-007 (Uncertainty Is Disclosed) governs the honest characterization of; is what PP-008 (Provenance Is Always Attributable) governs the origin-labeling of.
**Core relationship:** No correspondence today. Atlas Core's own candidate `Evidence` primitive is explicitly `[Planned]` — no Final ADR exists, and its relationship to Core's own `Knowledge` is itself an open question Core has not resolved. APP-000 §5's own boundary paragraph already anticipates this and requires no further action here; see Section 6.

### 3.5 Investor Judgment

**Purpose:** the Investor's own act of committing, which no other party or process may substitute for (APP-000 §5, PP-003).
**Responsibility:** weighs Evidence, Reasoning, and Uncertainty to reach a Decision.
**Lifetime:** Ephemeral, as an act — it occurs at a point, much as Atlas Core's own Reasoning Act is a bounded occurrence rather than a standing thing. What it produces (a Decision) is Permanent; the act of producing it is not itself a persisting record.
**Ownership:** Investor, exclusively — stated in its own definition, and the one place APP-000's text uses the word "exclusively" for any concept.
**Relationships:** is a component of Reasoning; is what constitutes a Decision (§8.2); is what PP-003 protects from delegation, automation, or substitution.
**Core relationship:** Explicitly non-corresponding, by design. Atlas Core's own `Judgment` Domain Object is settled, Final, and categorically different — "the ontological object produced by a completed Reasoning Act... not the act of reaching it" (ADR-002). APP-000 §5 already states this distinction in Investor Judgment's own definition; this document adds nothing to it beyond confirming the distinction remains correctly stated and does not require further qualification here.

### 3.6 Learning

**Purpose:** the reason Atlas preserves history at all (APP-000 §6.6).
**Responsibility:** improves future Reasoning by examining prior Decisions, the Reasoning that produced them, and what subsequently became known, together.
**Lifetime:** Permanent, as a capability — like Core's own Reasoning, it is a standing capacity, continuously exercisable, never itself completed or exhausted.
**Ownership:** Investor — stated explicitly in its own definition ("The Investor's capacity").
**Relationships:** operates across multiple closed Decision Contexts — including those closed by abandonment, not only by Decision — and the Reasoning, and, where applicable, the Decision and Outcome, each holds; is what PP-006 (Reasoning preserved independent of outcome) exists to make possible.
**Core relationship:** No correspondence. Core has no primitive for cross-Decision synthesis; this is, correctly, product-level territory Core's own ontology has no reason to model.

*(The candidate concept "Review" was considered and rejected as a separate entry: it names the act of exercising Learning, not a distinct thing Learning does not already fully cover. Accepting it would duplicate an already-accepted concept, which the Architectural Rules explicitly forbid.)*

### 3.7 Attention

**Purpose:** names the actual scarce resource Atlas competes for, correcting the more common but wrong assumption that information itself is scarce (APP-000 §6.4).
**Responsibility:** the Investor's finite capacity to engage deliberately with information — what PP-001 exists to protect.
**Lifetime:** Ephemeral — allocated and spent continuously; it does not persist as a retained record of itself.
**Ownership:** Investor — "The Investor's finite capacity" (§5).
**Relationships:** is what PP-001 governs; is degraded by irrelevant content regardless of that content's other qualities; is engaged by, but not owned by, any single Decision Context.
**Core relationship:** No correspondence. Core does not model human cognitive resources.

### 3.8 Uncertainty

**Purpose:** names a permanent structural condition of investing honestly, rather than presenting it as a defect to be engineered away (APP-000 §6.3).
**Responsibility:** the condition in which a fact relevant to a Decision is not, and cannot presently be, known with confidence.
**Lifetime:** Persistent for any specific fact — it holds for as long as that fact remains unresolved, and may never resolve.
**Ownership:** Neither — a condition of the world, not a possession of the Investor or of Atlas.
**Relationships:** is a required input Investor Judgment weighs; is what PP-007 requires be disclosed rather than concealed.
**Core relationship:** No named Core primitive, but a genuine philosophical alignment rather than a gap: Atlas Core independently treats uncertainty as legitimate content ("a determination that may itself consist in the honest conclusion that the available Knowledge does not settle the matter," ADR-002; "Uncertainty is a legitimate outcome of reasoning," ADR-001 §7). This is a reinforcing consistency, not a correspondence requiring further reconciliation.

### 3.9 Decision Quality

**Purpose:** the value APP-000 protects instead of outcome (APP-000 §6.1, PP-009) — the reason Atlas evaluates reasoning, not results.
**Responsibility:** characterizes the soundness of the Reasoning behind a Decision, assessed as of the time the Decision was made.
**Lifetime:** Permanent, and fixed at the moment of assessment — it does not retroactively change with hindsight, by its own definition.
**Ownership:** Neither — an evaluative property of a Decision-and-Reasoning pairing, not itself a possession.
**Relationships:** is assessed of a Decision, with reference to its Reasoning; is explicitly forbidden (PP-009) from being assessed with reference to Outcome.
**Core relationship:** No correspondence. Core's own object model records facts and commitments; it has no notion of evaluating or scoring a Decision at all — this is, correctly, exclusively product-level territory.

### 3.10 Decision Context *(new — formalizes the prior APS-001 Pre-Design Investigation's recommendation; corrected in v0.2 per the Decision Context Architecture Review)*

**Purpose:** the persistent, single-objective boundary within which product material relevant to one prospective Investment Decision can be gathered and related — including material that exists before any explicit Investor Reasoning chain does. Gathered Evidence, unresolved Uncertainty, and preliminary considerations regularly precede the point at which Reasoning, as APP-000 §5 defines it — "the explicit chain of premises, Evidence, and Investor Judgment" — has been assembled at all. Decision Context is necessary because that pre-chain material has nowhere else to live: Reasoning's own definition presupposes the connecting has already happened, so it cannot host material that exists before it does (PP-002, §6.3). Multi-engagement persistence is a consequence of this responsibility, not what makes Decision Context necessary in itself.

**Boundary with Investor Reasoning:** Decision Context is not itself Investor Reasoning. Investor Reasoning may arise, develop, and be revised within a Decision Context, but a Decision Context remains meaningful — open, holding material, directed at its one objective — before a complete or explicit Investor Reasoning chain exists within it. This pre-Reasoning capacity is part of Decision Context's own distinct architectural responsibility, not an incidental feature of it.

**Responsibility:** scopes exactly one objective, directed at exactly one prospective Investment Decision. Within that scope, a Decision Context draws upon Evidence relevant to its objective, may originate or gather Evidence itself, and may relate that Evidence — together with Investor Judgment and, once formed, Investor Reasoning — to its prospective Decision. It does not own Evidence exclusively: the same Evidence may also be relevant to, or referenced by, another Decision Context. This document does not define the mechanism by which Evidence is shared or referenced between Decision Contexts; that is implementation-level and reserved for a subordinate specification.

**Lifetime:** begins open. It may remain open without continuous Attention and without a time limit. It closes through either Investor commitment to its prospective Investment Decision, or explicit Investor abandonment — both legitimate closures. Closure does not destroy or dissolve a Decision Context: a closed Decision Context, whether closed by commitment or by abandonment, persists as a permanent, inspectable historical product record, available to future Learning. Material and Investor Reasoning within an explicitly abandoned Decision Context remain preserved and inspectable; abandonment does not authorize silent deletion or loss. An abandoned context can remain relevant to Learning in its own right — including learning about rejected opportunities, unresolved Uncertainty, and repeated patterns of not deciding.

**Ownership:** Investor — for the same reason Decision itself is Investor-owned.

**Cardinality:** one Investor may have multiple Decision Contexts open concurrently, each scoped to its own exactly-one objective and directed at its own exactly-one prospective Investment Decision. Attention may move among concurrent Decision Contexts, governed by PP-001; this document does not define how Atlas arbitrates competing objectives that draw on the same finite capital — that is a Portfolio-level concern APP-000 §5 already defers to a subordinate specification.

**Changing an objective:** changing a Decision Context's objective into a genuinely different objective does not mutate the original Decision Context's identity — a new objective requires a new Decision Context, and the original, if no longer pursued, closes by abandonment. Where several existing contexts contribute to a newly formulated, combined objective, that combined objective belongs to a new Decision Context; the prior contexts remain historically identifiable and may later be related through subordinate specifications. This document does not define relation types, transitions, or interaction behavior between contexts.

**Relationships:** holds pre-Reasoning material (gathered Evidence, unresolved Uncertainty, preliminary Investor Judgment) and, once it exists, Investor Reasoning; produces exactly one Decision on closure; is the unit Learning later revisits, individually and across many closed instances, whether those instances closed by commitment or by abandonment.

**Core relationship:** Indirect, and now resolved via Investment Case (§3.13, added in v0.4). `OE-002` §3.1 defines Atlas Core's `Case` only as "the normative ownership boundary within which Domain Objects exist and relate to one another," and explicitly declines to define Case's "complete semantics, lifecycle, or implementation… beyond what is required by [the Domain Object] model" — including its real-world scoping cardinality relative to `Decision`. Decision Context, by contrast, is exactly-one-prospective-Decision scoped by definition. Nothing in `OE-002` establishes that a Case is similarly scoped to one Decision; a Case may plausibly be broader, containing many Decisions over time. This is exactly the gap Investment Case (§3.13) now names: Decision Context corresponds to a decision-scoped product sub-boundary *within* Investment Case, which is itself the confirmed, 1:1 product-facing name for a Core Case. Decision Context itself remains, as stated above, not identical to Case and not Core-reference-eligible; only Investment Case carries the confirmed Core correspondence, per §3.13.

*("Objective" was investigated as its own candidate concept and is not accepted separately: it fails the "could another concept fully replace it" test directly — it is definitionally the single scoping property Decision Context already has by design ("scopes exactly one objective"), not a thing with its own independent lifetime, ownership, or responsibility.)*

### 3.11 Outcome *(new — fills a gap APP-000 assumes but never defines)*

**Purpose:** names what APP-000's own Decision Quality definition already depends on without ever formally introducing it — "independent of the outcome that later occurred" (§5) presupposes a concept of outcome that Section 5 never itself defines.
**Responsibility:** records a state of affairs the Investor treats as having become actual, following a Decision.
**Lifetime:** Permanent — once recorded, it stands; a later Outcome does not erase or invalidate an earlier one.
**Ownership:** Neither — a fact about the world, not a possession, matching Uncertainty's own ownership pattern.
**Relationships:** follows a Decision without altering it; is what PP-009 forbids Decision Quality from being judged by; is examined jointly with Reasoning during Learning (§6.6, "what later became known").
**Core relationship:** Approximate, and close. Atlas Core's own `Outcome` Domain Object (`OE-002` §5.6) — "records a determinate state of affairs which the Case treats as having become actual, without asserting objective truth or attributing that realization to a specific cause" — matches the product-level concept closely enough that no separate qualification appears necessary, unlike Investor Judgment. This SHALL still be confirmed, not assumed, by whichever future APS specification first operationalizes it.

### 3.12 Pattern Recognition *(new — accepted per the completed Pattern Recognition & Reflection Product Taxonomy Investigation and the subsequent Pattern Recognition Taxonomy Verification)*

**Purpose:** Pattern Recognition exists to identify recurring structure already present across the Investor's own recorded material — structure that exists whether or not Atlas has found it, not structure Atlas creates.

**Responsibility:** discovers and presents recurring structure without interpreting it for the Investor, deriving a Learning Result, making a Decision, exercising Investor Judgment, issuing a Recommendation, or evaluating Decision Quality. Pattern Recognition's own output remains structural and non-evaluative; any interpretation of what a discovered structure means belongs to the Investor's own Learning or Investor Judgment, never to Pattern Recognition itself.

**Lifetime:** Exercised episodically. Its exercise MAY be ephemeral and repeatable. This document SHALL NOT be read to require a permanent Product record merely because Pattern Recognition occurs; how any particular exercise is technically represented is implementation-level and outside this document's own scope.

**Ownership:** Atlas-performed and attributable, per PP-008. The resulting discovery is not owned by the Investor as an act of Investor interpretation — it remains Atlas-originated content the Investor examines. Any Investor interpretation of a discovered structure belongs to Learning or to Investor Judgment, not to Pattern Recognition itself, which owns no interpretive act of its own; Pattern Recognition is accordingly not Investor-owned in the sense Learning and Investor Judgment are.

**Relationships:** MAY examine an Investor's own recorded material; MAY provide attributable input to Learning, per §3.6 and PP-008; Learning MAY occur without Pattern Recognition input, and does not depend upon it. Pattern Recognition is distinct from Evidence (its own output is ephemeral and recomputed, not a permanently captured fact); distinct from Outcome (it discovers structure across many Decisions, never records a single realized state of affairs); distinct from Decision Quality (it is non-evaluative by responsibility, while Decision Quality is an evaluative property); and distinct from Recommendation (it presents discovered structure only, never a proposed course of action).

**Product Level:** Concept. Not a separate "Product Capability" category — this document has exactly one Product Level value, per §3's own opening schema, and Pattern Recognition is accepted under that same value.

**Core relationship:** None confirmed. Pattern Recognition is not a Core Domain Object; this document does not create, assert, or imply a Core correspondence for it.

### 3.13 Investment Case *(new — formalizes the completed Atlas Product Architecture Reconciliation's own resolution of the Decision Context ↔ Case correspondence question left unconfirmed in §3.10 and §6)*

**Purpose:** the product-facing name for Atlas Core's own `Case` (`OE-002` §3.1) — the enclosing container for everything ever reasoned about one position or idea, across its entire lifetime.

**Responsibility:** encloses one or more Decision Contexts over its lifetime, each directed at its own exactly-one objective, per §3.10. Investment Case itself owns no objective, no Reasoning, and no Decision directly — each of those remains the responsibility of the Decision Context it holds.

**Lifetime:** Permanent, mirroring Core `Case`'s own lack of a closure mechanism. Begins with the first Core record accepted within the Case; remains open indefinitely, available to hold a new Decision Context whenever a genuinely new objective concerning the same position or idea arises.

**Ownership:** Investor — for the same reason Decision Context and Decision are Investor-owned (§3.2, §3.10).

**Cardinality:** Exactly one Investment Case per Core Case (1:1). One Investment Case MAY enclose many Decision Contexts over its lifetime (1:many) — for example, an initial Decision Context resolving in a `BUY` Decision, and a later, separate Decision Context on the same position resolving in a `SELL` Decision, are two distinct Decision Contexts within one Investment Case, per §3.10's own Multi-Decision-Objectives treatment. Whether two Decision Contexts may be concurrently open within one Investment Case is not resolved by this document; it is left to the governing APS specification.

**Relationships:** encloses Decision Context (§3.10), which itself produces Decision (§3.2) on Commitment. A future Portfolio subordinate specification (§4) reads across many Investment Cases, in aggregate, to state what the Investor currently holds.

**Core relationship:** Confirmed, and direct. Investment Case is the 1:1 product-facing name for Atlas Core's own `Case` (`OE-002` §3.1); it introduces no new Core ontology, no new Core reference-eligibility, and no Core invariant beyond what `Case` already carries. This resolves, rather than reopens, §3.10's own prior characterization of the Decision Context ↔ Case relationship as an unconfirmed hypothesis: Decision Context remains a product-level sub-boundary that is not identical to Case, per its own §3.10 Core relationship note; Investment Case is now the name for the Case it is a sub-boundary within.

---

## 4. Rejected Concepts

**Portfolio.** Rejected on APP-000's own explicit authority, not this document's judgment: §5 names "a portfolio" directly among the concepts the Doctrine deliberately does not define, deferring it to subordinate specifications. APP-001 has no basis to promote what APP-000 itself excluded. *Amended in v0.4:* this rejection is reaffirmed, not reversed; Portfolio is formally named as the subject of the approved subordinate specification APS-006, per the completed Atlas Product Architecture Reconciliation.

**Watchlist.** Rejected by the same reasoning as Portfolio, by direct analogy: a tracked collection of subjects of interest is the same architectural category APP-000 already named and deferred, even though APP-000's own text does not use this exact word. *Amended in v0.4:* this rejection is reaffirmed, not reversed; Watchlist is formally named as the subject of the approved subordinate specification APS-007, per the completed Atlas Product Architecture Reconciliation.

**Daily Brief.** Not considered by the original investigation; newly recorded in this v0.4 amendment. Rejected as an independent primitive concept on the same basis as Portfolio and Watchlist: it is a particular product surface, per APP-000 §5's own closing sentence — "Concepts specific to a particular product surface, interaction model, or implementation... are defined, if at all, by subordinate specifications, not by this Doctrine" — not the kind of enduring, implementation-independent primitive §3 accepts. Formally named as the subject of the approved subordinate specification APS-008, per the completed Atlas Product Architecture Reconciliation.

**Discover.** Not considered by the original investigation; newly recorded in this v0.4 amendment. Rejected as an independent primitive concept on the same basis as Daily Brief, per APP-000 §5's own product-surface deferral. Formally named as the subject of the approved subordinate specification APS-009, per the completed Atlas Product Architecture Reconciliation.

**Review.** Rejected — see Section 3.6. Fully absorbed by Learning; naming it separately would duplicate an already-accepted concept's responsibility, which the Architectural Rules forbid.

**Knowledge.** Rejected on two independent grounds. First, it is fully absorbed by Evidence — nothing about "established, accepted information" that Evidence's own definition does not already cover. Second, and more seriously: Atlas Core already has a Final, settled `Knowledge` characterization (ADR-003) and a `Knowledge Reference` Domain Object (`OE-002` §5.2). Introducing a product-level "Knowledge" concept here would recreate, deliberately and avoidably, the exact class of naming collision this program spent a dedicated correction cycle eliminating for Judgment — with no independent product need to justify taking on that risk.

**Insight.** Rejected — fully absorbed by Evidence together with PP-008's existing provenance-attribution requirement. A synthesized, Atlas-originated observation is simply attributable Atlas-originated Evidence; it owns no responsibility Evidence and PP-008 do not already discharge jointly.

**Reflection.** Rejected as a separate Product Concept, per the completed Pattern Recognition & Reflection Product Taxonomy Investigation. Before preservation, Reflection is an occasion or act already governed by Learning (§3.6, where it is the Investor's own interpretation directed toward a generalized lesson) or by Investor Judgment (§3.5, where it is a bounded act of interpretation that does not rise to a distinct Learning Result). After preservation, its content is ordinary Investor-originated Evidence (§3.4), attributable per PP-008. Reflection owns no responsibility that Learning, Investor Judgment, Evidence, and PP-008 do not already discharge jointly — the same ground already established above for Review and for Insight. This rejection concerns Reflection's own standing as a formal Product Concept only; the ordinary-language act of reflecting remains available for informal use in UX, workflow, engineering, or feature descriptions without thereby acquiring separate Product Architecture status, per APP-000 §11.1's own rule that undefined terms carry ordinary meaning.

**Recommendation.** Rejected on two grounds. First, the same absorption argument as Insight applies directly. Second — and this is a finding specific to this repository, not a generic caution — the word is already the subject of an extensive, independently settled resolution in the separately-governed `docs/atlas_ux/` corpus: `ADR-003-Recommendation-Identity-and-Terminology-Resolution.md` there distinguishes "Atlas Recommendation" (a general advisory artifact) from "Proposed Decision Candidate Content" (transient candidate wording for the Proposed Decision field), and neither of those two meanings is one this document has any warrant to reopen, narrow, or extend. Introducing a third meaning at the APP-001 layer, in a track that does not yet state its relationship to that corpus at all, is precisely the risk Section 6 raises formally.

**Objective.** Not rejected outright but merged into Decision Context — see Section 3.10's closing note. Recorded here for completeness of the candidate list's own disposition.

**Session.** Not on this investigation's candidate list, but recorded here for a complete taxonomy: rejected in the dedicated APS-001 Pre-Design Investigation that preceded this document, on the grounds that a time-bounded interaction period owns no responsibility a persistent, single-objective container does not already discharge more coherently. Decision Context (Section 3.10) is that investigation's recommended, now-accepted replacement.

---

## 5. Concept Relationships

```
Investor
  owns → Decision, Reasoning, Investor Judgment, Learning, Attention, Investment Case, Decision Context (possibly several, concurrently)

Investment Case (Investor-owned, 1:1 with a Core Case, added in v0.4)
  encloses → one or more Decision Contexts, over its own permanent lifetime
  owns no objective, Reasoning, or Decision directly → each remains the responsibility of the Decision Context it holds

Decision Context (Investor-owned, scoped to exactly one objective, one prospective Decision, held within exactly one Investment Case)
  holds → pre-Reasoning material (Evidence, Uncertainty, preliminary Investor Judgment), and, once formed, Reasoning
  draws upon (non-exclusively) → Evidence
  produces → Decision, on closure (by commitment or by abandonment; persists historically either way)

Reasoning (Investor-owned)
  composed of → Evidence + Investor Judgment
  connects known facts → Decision
  arises and develops within → Decision Context

Investor Judgment (Investor-owned, exclusive)
  weighs → Evidence + Reasoning + Uncertainty
  → reaches → Decision

Decision (Investor-owned, permanent once made)
  assessed for → Decision Quality (via its own Reasoning, never via Outcome)
  followed by (not altered by) → Outcome

Learning (Investor-owned capability)
  operates across → many closed Decision Contexts (committed or abandoned), their Reasoning, and, where applicable, their Decision and Outcome

Pattern Recognition (Atlas-performed, attributable per PP-008)
  discovers → recurring structure already present across recorded material
  MAY provide attributable input → Learning (Learning MAY occur without it; Learning does not depend on it)

Attention (Investor-owned, ephemeral)
  governed by → PP-001, independent of any single Decision Context, movable among concurrent Decision Contexts

Uncertainty / Evidence (owned by neither)
  Uncertainty → weighed by Investor Judgment, disclosed per PP-007
  Evidence → composes Reasoning, attributed per PP-008, may be drawn upon by more than one Decision Context
```

Every relationship above traces to an already-cited APP-000 provision; none is newly asserted by this document.

---

## 6. Relationship to Atlas Core

| Concept | Correspondence | Core reference |
|---|---|---|
| Investor | None | — (Core has no actor/agent primitive) |
| Decision | Approximate | `OE-002` §5.5 `Decision` |
| Reasoning | Approximate, non-obvious | `OE-002` §5.3 `Reasoning Trace` (not Core's own `Reasoning`) |
| Evidence | None (Core's own `Evidence` is `[Planned]`, unsettled) | Dependency-Graph.md |
| Investor Judgment | Explicitly none, by design | ADR-002 `Judgment` (distinguished, not mapped) |
| Learning | None | — |
| Attention | None | — |
| Uncertainty | None (thematic alignment only) | ADR-001 §7, ADR-002 |
| Decision Quality | None | — |
| Investment Case | Confirmed, direct — 1:1 product-facing name for Core `Case` (added in v0.4) | `OE-002` §3.1 `Case` |
| Decision Context | Indirect — a product-level sub-boundary held within Investment Case, not identical to Case itself | `OE-002` §3.1 `Case`, via Investment Case §3.13 |
| Outcome | Approximate, close | `OE-002` §5.6 `Outcome` |
| Pattern Recognition | None confirmed | — |

This document redefines no Core concept and introduces no new Core ontology anywhere in this table. Every "Approximate," "Indirect," or "Unconfirmed" entry is a hypothesis for a future specification to confirm, not a settled architectural fact this document has the authority to establish; Investment Case's own "Confirmed, direct" entry is the one exception, since it asserts nothing beyond Core's own already-Final `Case` definition, under a product-facing name.

---

## 7. Architectural Observations

1. **`Reasoning` carries the same collision category `Judgment` did, unresolved.** Core's `Reasoning` (a standing capability) and APP-000's `Reasoning` (an inspectable chain, functionally closer to Core's `Reasoning Trace`) are as categorically different as `Judgment` and `Investor Judgment` were before the v0.4 correction. Unlike that correction, this document cannot make the equivalent fix — APP-001 has no authority to rename an APP-000-defined term. **Recommend:** a future, dedicated APP-000 amendment considering "Investor Reasoning," following the identical precedent and justification already established for Investor Judgment.

2. **`Outcome` was an implicit assumption, now made explicit.** APP-000's own Decision Quality definition depends on the concept without ever formally introducing it. This document closes that gap at the APP-001 layer, since doing so adds no new philosophy and contradicts no existing APP-000 statement — but it is worth recording plainly that this is exactly the class of gap Critical Review asked this investigation to find, and it was found in the governing document's own text, not in the candidate list.

3. **The relationship between `docs/atlas_product_architecture/` and `docs/atlas_ux/` is undetermined.** These appear to be two separate documentation tracks with independent governance histories, and this document found at least one direct point of near-collision between them (Recommendation, Section 4). Nothing in APP-000 or APP-001 states whether the UX corpus is a predecessor this track supersedes, a parallel track requiring consistency with this one, or an unrelated body of work. This is a real, unresolved governance question, not merely a naming detail, and it remains open until a dedicated governance task resolves it.

4. **The Pattern Recognition / Reflection taxonomy gap, identified by a later Product Architecture Baseline Review, is now resolved.** Pattern Recognition is formally accepted as a Product Concept (§3.12); Reflection is formally rejected (§4), on the same ground already established for Review and Insight. Both determinations were reached through a dedicated reducibility investigation, following the identical method this document's own Section 1 already applies to every accepted or rejected concept. No second Product Level category was introduced to accommodate Pattern Recognition: this document has exactly one Product Level value, Concept, and Pattern Recognition is accepted under it, per §3's own opening schema.

---

## 8. Risks

- **Cross-track terminology collision remains open** (Observation 3). Concrete risk: a future APS specification, written without awareness of `docs/atlas_ux/`'s own ADR-003, could reintroduce "Recommendation" or a similarly-collided term informally, exactly as this document's rejection was designed to prevent formally.
- **The Reasoning naming gap persists** (Observation 1) until a dedicated APP-000 amendment addresses it. Low near-term risk, since the existing general boundary paragraph in APP-000 §5 already covers it adequately for now — but it is a standing, known gap, not a closed one.
- **RESOLVED in v0.4 — The Decision Context ↔ `Case` correspondence**, previously unconfirmed (see the prior text of Section 3.10 and Section 6, recoverable in this document's revision history). Investment Case (§3.13) now names the confirmed, 1:1 product-facing correspondence to Core `Case`; Decision Context remains, as originally stated, a product-level sub-boundary held within it, not identical to it. No Core compatibility investigation was required to reach this resolution, since Investment Case asserts nothing beyond Core's own already-Final `Case` definition — it introduces no new Core reference-eligibility, mirroring Decision Context's own DCINV-015.
- **Informal reuse of rejected words.** Rejecting Portfolio, Watchlist, Knowledge, Insight, and Recommendation as formal Concepts does not prevent APS authors from using these words informally, per APP-000 §11.1's own rule that undefined terms carry ordinary meaning. The risk is only that an author mistakes ordinary usage for a claim to formal Concept status — a documentation-discipline risk, not a conceptual one.

---

## 9. Recommendations for APS Sequencing

Ordered by dependency, not by schedule or priority — this is a statement of which concepts require a specification before which others can meaningfully build on them, not a roadmap.

1. **Decision Context** — the foundational container every other product-facing specification will need to reference. *Resolved in v0.4:* the Core compatibility question this item originally deferred to APS-001's own work is now answered directly by this document, via Investment Case (§3.13); no separate Core compatibility investigation was required.
2. **Reasoning and Evidence support** — how Reasoning is built and Evidence surfaced within an open Decision Context; depends on (1) existing first, and resolves Observation 1's Reasoning/Reasoning-Trace mapping as part of its own scope, even though it cannot rename the term.
3. **Decision and Outcome capture** — how a Decision Context closes into a Decision, and how Outcome is later recorded against it; depends on (1) and (2).
4. **Learning** — how closed Decision Contexts, their Reasoning, and their Outcomes are later revisited together; depends on all of the above existing first, since Learning by definition operates across them.
5. **Pattern Recognition** — now accepted as a Concept (§3.12). A future, dedicated APS specification MAY operationalize its own product behavior, following the same method already used for Decision Context, Investor Reasoning, Evidence, Learning, and Outcome; this document's own acceptance of the concept does not, by itself, require that such a specification be undertaken.
6. **Investment Case** (§3.13) — accepted directly by this v0.4 amendment; requires no dedicated APS of its own, since its complete product behavior is already stated in §3.13, and it introduces no new Core ontology for any future specification to operationalize.
7. **Portfolio** — depends on (1) and (6) already existing; reads across many Investment Cases in aggregate. Approved for APS-006.
8. **Watchlist** — depends on (6); simpler than Portfolio, no dependency on Decision Context's own machinery. Approved for APS-007.
9. **Daily Brief** — depends on (7); reads Portfolio's own aggregated data, filtered by time. Approved for APS-008.
10. **Discover** — depends on (7) and (8); reads both Portfolio and Watchlist data to compute relevance. Approved for APS-009.

Any specification touching AI-originated content presentation (which will eventually need to operationalize PP-003 and PP-008 concretely) SHALL NOT proceed until Observation 3's cross-track question is resolved.

---

## 10. Verdict

**Atlas Product Architecture is conceptually complete enough to begin APS-006 through APS-009, scoped to Portfolio, Watchlist, Daily Brief, and Discover, now — alongside APS-001 through APS-005, already completed under the original v0.3 concept set.** The twelve accepted concepts in Section 3 form a coherent, non-duplicating set, each satisfying every rule in this document's own Architectural Rules test, each traceable to APP-000, with only one narrow, explicitly-scoped open item remaining (Section 7.1's Reasoning naming gap) that does not block any current specification work. Section 6's previously unconfirmed Decision Context ↔ Case mapping is resolved as of this v0.4 amendment, per Investment Case (§3.13).

It is **not** yet safe to begin any future APS specification touching AI-originated content presentation, Recommendation-adjacent language, or anything else bordering the `docs/atlas_ux/` corpus's own territory, until this document's Section 7.3 finding — the undetermined relationship between the two tracks — is explicitly resolved.
