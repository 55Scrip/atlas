# Architecture Governance

**Status:** Accepted.
**Owner:** Atlas Product.
**Governs:** The authority, hierarchy, and lifecycle of Atlas's own documentation. Nothing else.
**Subordinate to:** `ATLAS_CONSTITUTION.md` only.
**Created:** 2026-08-02, on the basis of the completed Atlas Architecture Authority Report investigation (a read-only audit of the full documentation tree, referenced throughout Section 8).

This document does not define Atlas. It defines how Atlas's documentation defines Atlas.

---

## 1. Purpose

Atlas is described by many documents, written at different times, by different efforts, at different levels of maturity, using different vocabularies. Before this document existed, no single place stated which of those documents governed which others, what a document's own stated status actually permitted or forbade, or what a future contributor should do when two documents disagreed.

The completed Atlas Architecture Authority Report found exactly this condition: four active documentation tracks (Atlas Core Doctrine, Product Architecture, UX Architecture, and an orphaned Alpha Experience specification), each internally coherent, several citing one another as authoritative without the citation being reciprocated or even acknowledged, and at least one document repeatedly declaring its own relationship to a sibling track "unresolved" without that resolution ever occurring. None of this is a defect in the ideas each track contains. It is the absence of a governance layer describing how the tracks relate. This document is that layer.

**Architecture Governance exists to answer exactly one class of question: given two or more documents, which one governs, and by what process was that determined?**

### 1.1 What this document does not do

This document does not, anywhere, in any section:

- define product behaviour;
- define the domain model, its objects, or their relationships;
- define UX, interaction, or visual design;
- define implementation, code structure, or technology choice;
- introduce, rename, or redefine any Atlas concept, term, or ontology.

Where this document appears to describe a concept (for example, "Case," "Decision," or "Dashboard," used below only as illustration of *which document owns the term*), that description is not authoritative. The owning document, identified below, remains the sole source of that concept's actual meaning. This document's own authority is confined to *documentation governance* — who may say what, in what document, with what force — never to the content of what is said.

### 1.2 Relationship to `ATLAS_ARCHITECTURE.md`

`docs/ATLAS_ARCHITECTURE.md` describes Atlas's own conceptual *system* information flow (Market Data → Evidence → Analysis Engines → Reasoning → Suitability → Portfolio Context → Risk and Drift → Language Layer → User Experience → Memory, Monitoring, and Journal). This document is unrelated to that one and does not supersede, amend, or depend on it. `ATLAS_ARCHITECTURE.md` answers "how does Atlas reason." This document answers "which document says so, and who may change it." A future contributor needs both, for different questions.

---

## 2. Documentation Hierarchy

The example hierarchy provided when this document was commissioned proposed a single linear chain: Constitution → Architecture Governance → Core Doctrine → Domain Object Architecture → Reasoning Foundations → Product Architecture → UX Architecture → Design Doctrine → Design System → Implementation.

Repository evidence supports most of this chain, but not all of it, in two specific ways, both preserved below with the evidence stated plainly rather than silently corrected:

1. **"Core Doctrine" and "Domain Object Architecture" are not two sequential layers — they are two documents within one track**, both self-declared **Final**, both governing the same implemented system (`atlas/core/`) at the same level of authority, with Domain Object Architecture (`OE-002` through `OE-006`) the more detailed and more recently exercised of the two. Ordering one strictly above the other would overstate a distinction the documents themselves do not draw. They are presented below as a single track with two named parts.
2. **No document titled "Design Doctrine" exists as a track separate from UX Architecture.** `docs/atlas_ux/UX-000-Atlas-UX-Doctrine.md` *is* Atlas's design doctrine — it is the highest-authority document within `docs/atlas_ux/`, and `UX-012` ("Design System") and `UX-013A–G` ("Component Specifications") are subordinate to it, not to some other, undiscovered doctrine. The example hierarchy's "Design Doctrine" and "Design System" rows are therefore represented below as two sub-layers *within* the UX Architecture track, not as a separate track between Product Architecture and UX Architecture.

With those two corrections, the current, evidence-supported hierarchy is:

```
ATLAS_CONSTITUTION.md
        │
        ▼
Architecture Governance  (this document)
        │
        ▼
Atlas Core Doctrine & Domain Object Architecture
  (docs/atlas_reasoning_foundations/Doctrine.md — method-level "Normative"
   docs/atlas_domain_object_architecture/Doctrine.md, OE-002–OE-006 — "Final")
        │
        ▼
Reasoning Foundations  (ontology only)
  (docs/atlas_reasoning_foundations/ADR-001, ADR-002 "Final", ADR-003 "Final")
        │
        ▼
Product Architecture
  (docs/atlas_product_architecture/APP-000 "Draft v0.4", APP-001 "Draft v0.3",
   APS-001–005, all "Draft")
        │
        ▼
UX Architecture
  ├─ UX Doctrine        (docs/atlas_ux/UX-000-Atlas-UX-Doctrine.md — "RC v1.0")
  ├─ Design System       (docs/atlas_ux/UX-012, UX-012A–D)
  └─ Component Specs     (docs/atlas_ux/UX-013A–G)
        │
        ▼
Engineering Documentation
  (implementation-design, architecture-review, and reconciliation artifacts;
   explicitly non-normative by their own declared terms)
        │
        ▼
Implementation
  (atlas/core/ — implemented, tested, persisted;
   frontend/ — reserved, not yet implemented)
```

### 2.1 Why each layer exists, and why it depends on the one above it

**Atlas Core Doctrine & Domain Object Architecture** exists because a running system needs a settled statement of what objects exist, how they relate, and what invariants hold, independent of what any product or interface eventually does with them. It depends on nothing but the Constitution and this document, because ontology of *what exists* is prior to any question of *what it means to a user* or *how it is shown*.

**Reasoning Foundations** exists because "reasoning," "judgment," and "knowledge" are used as ordinary words throughout Atlas's product language, and at least one of them ("Judgment") has already collided, unresolved, with a distinct product-layer term ("Investor Judgment" — see Section 8). Reasoning Foundations exists to settle what these words mean *as philosophical/ontological categories*, independent of any specific object or screen. It sits beside, not strictly beneath, the Domain Object Architecture — both are Atlas Core-track documents — but is listed second because its own scope is narrower and its findings (e.g., ADR-002's account of Judgment) are consumed by name in later, more product-facing work.

**Product Architecture** exists because ontology alone does not tell a team what a user experiences or why. Product Architecture translates settled Core concepts into Product Concepts — the things a Product person can reason about, name, and specify features against — without yet describing a single screen. It depends on Core Doctrine and Reasoning Foundations because a Product Concept that contradicts settled ontology is not a valid concept; APP-001 §6 ("Relationship to Atlas Core") makes exactly this dependency explicit for every concept it accepts.

**UX Architecture** exists because Product Concepts do not by themselves describe how a person interacts with them — what screen they see, what a component looks like, what token renders which state. It depends on Product Architecture because presentation of a concept that does not exist at the Product layer has nothing to present.

**Engineering Documentation** exists because building software surfaces real, moment-to-moment decisions — a token migration, a reconciliation of two naming schemes, a pre-commit review — that must be recorded for auditability but do not, and must not, carry the authority to redefine anything above them. It depends on every layer above it because its entire purpose is implementing what those layers have already settled.

**Implementation** exists because documentation, however authoritative, is not software. It depends on everything above it and adds nothing back upward: no code comment, variable name, or runtime behavior may be cited as evidence of what a higher layer says.

---

## 3. Responsibilities

Each documentation family is defined here in full, using the schema commissioned for this section.

### 3.1 Core Doctrine (Atlas Core)

- **Purpose:** State the method by which Atlas Core's own architecture is investigated, decided, and changed.
- **Authority:** Final (`docs/atlas_domain_object_architecture/Doctrine.md`). Governs its own track's process, not its content.
- **Scope:** How architectural questions about the implemented system are investigated, what counts as a decision, how a decision becomes Final, how a Final decision is later amended.
- **Explicit Non-Scope:** Does not itself state what any Domain Object is. Does not govern Product, UX, or any track outside `docs/atlas_domain_object_architecture/` and `docs/atlas_reasoning_foundations/`.
- **Dependencies:** `ATLAS_CONSTITUTION.md`; this document.
- **Required Inputs:** None beyond the Constitution.
- **Produced Outputs:** The process contract every other document in the Atlas Core track (OE-002–006, ADR-001–003, ADR-005) is written under.
- **Primary Consumers:** Engineers and architects working on `atlas/core/`.
- **Expected Success Criteria:** Every Atlas Core decision is traceable to an investigation, a decision record, and a stated status, per its own Change Protocol.

### 3.2 Domain Object Architecture

- **Purpose:** Define the canonical Domain Object Set, its relationships, invariants, validation, and acceptance model for the implemented system.
- **Authority:** Final (`OE-002` through `OE-006`), unamended since adoption.
- **Scope:** `atlas/core/domain/` — the six-object model (Observation, Knowledge Reference, Reasoning Trace, Judgment, Decision, Outcome) and Case as their ownership boundary.
- **Explicit Non-Scope:** Does not govern product meaning, UX presentation, or the legacy objects (Hypothesis, Evidence, Conclusion, Evaluation, Learning, Question, Interpretation) beyond the reducibility findings already recorded against them.
- **Dependencies:** Core Doctrine.
- **Required Inputs:** A settled architectural question, investigated per the Core Doctrine's process.
- **Produced Outputs:** The Domain Object Model, Event Model, Invariants, Validation Model, and Acceptance Model — the normative shape `atlas/core/` code is written against.
- **Primary Consumers:** Engineers implementing or modifying `atlas/core/domain/`, `application/`, and `infrastructure/`.
- **Expected Success Criteria:** Implementation matches the documented model; where it does not, the discrepancy is investigated and resolved in the model's favor unless the model is itself formally amended.

### 3.3 Reasoning Foundations

- **Purpose:** Settle the ontological nature of Reasoning, Judgment, and Knowledge as philosophical categories.
- **Authority:** Doctrine — Normative (process only). ADR-002 (Judgment) and ADR-003 (Knowledge) — Final. ADR-001 (Reasoning) — status asserted only externally by this track's own `README.md` and `Dependency-Graph.md`, not self-declared in ADR-001's own text; treated as Final pending that gap being closed.
- **Scope:** Exactly what its own `README.md` states: "Nothing outside `docs/atlas_reasoning_foundations/` is part of Atlas Reasoning Foundations."
- **Explicit Non-Scope:** No architecture, no implementation, no product concept, no UX concept. Explicitly, by its own words: no work exists here at the Architecture or Implementation layers.
- **Dependencies:** Core Doctrine (shares its process discipline by precedent, not by formal citation).
- **Required Inputs:** A named philosophical question about a category Atlas uses informally elsewhere.
- **Produced Outputs:** Settled definitions later product-layer work may cite by name (e.g., APP-001's own account of "Investor Judgment" explicitly distinguishes itself from this track's "Judgment").
- **Primary Consumers:** Authors of Product Architecture and Domain Object Architecture documents who need a settled account of what these words mean before using them.
- **Expected Success Criteria:** A category's nature is stated once, precisely, and not re-litigated informally elsewhere.

### 3.4 Product Architecture

- **Purpose:** Translate settled Core concepts into named Product Concepts a Product author can build feature specifications against.
- **Authority:** Draft throughout (APP-000 v0.4, APP-001 v0.3, APS-001–005 v0.1–v0.2). Untracked in git as of this document's writing.
- **Scope:** Product philosophy, principles, responsibilities, and the accepted/rejected Product Concept taxonomy (Investor, Decision, Reasoning, Evidence, Investor Judgment, Learning, Attention, Uncertainty, Decision Quality, Decision Context, Outcome, Pattern Recognition).
- **Explicit Non-Scope:** By APP-000's own stated rule — no workflows, screens, workspaces, interaction design, visual design, implementation, architecture, data models, AI models/algorithms, or roadmap/release sequencing.
- **Dependencies:** Core Doctrine, Domain Object Architecture, Reasoning Foundations.
- **Required Inputs:** A candidate concept, tested against APP-001's own Architectural Rules and cross-checked for Core correspondence.
- **Produced Outputs:** Accepted/rejected Product Concepts, each with a stated (and where applicable, explicitly unconfirmed) Core correspondence.
- **Primary Consumers:** Authors of UX Architecture and Atlas Product Specification (APS) documents.
- **Expected Success Criteria:** Per APP-001's own Architectural Rules test — every accepted concept is irreducible to another accepted concept, traceable to APP-000, and does not duplicate an existing term.

### 3.5 UX Architecture

- **Purpose:** Define how Product Concepts are presented — Workspaces, components, states, interaction, tokens.
- **Authority:** UX Doctrine (`UX-000-Atlas-UX-Doctrine.md`) — Release Candidate RC v1.0. Design System (`UX-012` family) and Component Specifications (`UX-013A–G`) — active, currently in progress, with uncommitted working-tree edits as of this document's writing.
- **Scope:** Everything under `docs/atlas_ux/` — Workspace definitions, component anatomy/states/tokens, the Design Token Architecture, accessibility behavior, interaction model.
- **Explicit Non-Scope:** Does not define Product Concepts (it consumes them), does not define the domain model, does not define implementation technology.
- **Dependencies:** Product Architecture, per `UX-000`'s own stated subordination (Section 8.3 below records the caveat on this dependency).
- **Required Inputs:** An accepted Product Concept, or an already-specified UX Doctrine rule.
- **Produced Outputs:** Component specifications and token definitions implementation can build directly from.
- **Primary Consumers:** Designers, frontend engineers, and this session's own Token Architecture program.
- **Expected Success Criteria:** Every component and token traces to a canonical source; no unsupported namespace; no contradiction between component documents (the standard this session's own multi-phase Token Architecture program and its Release Candidate Audit were built to enforce).

### 3.6 Design System

*(A sub-layer of UX Architecture, not a separate track — see Section 2.)*

- **Purpose:** Define the shared visual and presentation-token vocabulary every component draws from.
- **Authority:** `UX-012` (Workspace/component consistency), `UX-012A` (Foundations), `UX-012B` (Components & Reusable Patterns), `UX-012C` (Interaction/Navigation/Responsive), `UX-012D` (Governance, Tokens & Evolution) — the sole canonical Design Token authority, per this session's own completed Governance Authority Resolution.
- **Scope:** Token categories, naming conventions, component/pattern/Workspace governance, accessibility governance, consistency audit process.
- **Explicit Non-Scope:** Individual component anatomy (owned by `UX-013A–G`); Product meaning (owned by Product Architecture).
- **Dependencies:** UX Doctrine.
- **Required Inputs:** A presentation need not already served by an existing token or pattern.
- **Produced Outputs:** Canonical tokens (`color.*`, `type.*`, `space.*`, `motion.*`, `surface.*`, `border.*`, `focus.*`, `opacity.*`, `width.*`, `radius.*`, `accessibility.*`, `cursor.*` — the closed top-level category list) and the governance rules for extending them.
- **Primary Consumers:** Component specification authors, frontend implementers.
- **Expected Success Criteria:** No unsupported top-level namespace; every token traces to a canonical definition; established by the completed Reasoning Token Architecture program (Phases 1–3C) and its Release Candidate Audit.

### 3.7 Engineering Documentation

- **Purpose:** Record implementation-level design decisions, migrations, reconciliations, and readiness reviews.
- **Authority:** None, by explicit, uniform, repeated self-declaration. Every such document found in this repository (the ~25 "Implementation Design," "Architecture Review," "Reconciliation Investigation," "Pre-Commit Review," and "Readiness Review" documents in `docs/atlas_domain_object_architecture/`, and the many `*CleanupPlan.md` documents at the top of `docs/`) states some form of: "carries no Doctrine status... where anything here conflicts with [the normative documents], those documents govern and this one is wrong and must be corrected."
- **Scope:** Whatever specific implementation question the document was written to resolve.
- **Explicit Non-Scope:** Cannot establish, amend, or override any normative document at any layer above it.
- **Dependencies:** Everything above it in the hierarchy.
- **Required Inputs:** A concrete implementation question arising from building against a normative document.
- **Produced Outputs:** A recorded engineering decision, explicitly informative, never normative.
- **Primary Consumers:** Engineers implementing the specific change the document addresses.
- **Expected Success Criteria:** The document is honest about its own non-authority and does not get mistaken, later, for a normative source.

### 3.8 Implementation

- **Purpose:** The running system.
- **Authority:** None over documentation. Code is downstream of every layer above it; code never establishes what a document must say.
- **Scope:** `atlas/core/` (implemented, tested, persisted) and `frontend/` (reserved, not yet implemented, per its own README).
- **Explicit Non-Scope:** Implementation choices (framework, code organization, technology) are explicitly the domain of engineering, not of any document above Engineering Documentation, per Core Doctrine's own stated boundary.
- **Dependencies:** Everything above it.
- **Required Inputs:** A normative specification to build against.
- **Produced Outputs:** The product itself.
- **Primary Consumers:** Users, and the test suite that verifies conformance to the documented model.
- **Expected Success Criteria:** Behavior matches the documented model; where it cannot (a genuine implementation constraint), the constraint is escalated for the model to be reviewed — never silently diverged from.

---

## 4. Authority Chain

Authority flows in exactly one direction:

```
Ontology  (Core Doctrine, Domain Object Architecture, Reasoning Foundations)
     ↓
Product Meaning  (Product Architecture)
     ↓
Presentation  (UX Architecture: Doctrine → Design System → Component Specs)
     ↓
Implementation  (atlas/core/, frontend/)
```

**Higher layers must never redefine lower layers.** A UX component specification that quietly asserts a new domain relationship, a Product Concept that contradicts a settled Core invariant, or a token that encodes Product meaning (Decision Quality, Confidence, Conviction, Truth, Investor ownership, Atlas authority, Evidence validity — the exact boundary this session's own Token Architecture program repeatedly verified) are all violations of this rule, regardless of how well-intentioned or how detailed the higher-layer document is.

**Lower layers must never leak presentation concerns upward.** A Domain Object Model that specifies a visual treatment, a Product Concept definition that specifies a screen layout, or a Core Doctrine passage that names a specific UI component are all violations of this rule in the other direction. `APP-000`'s own stated non-scope list (no workflows, screens, workspaces, interaction design, visual design) is the clearest existing example of a lower-in-the-chain-relative-to-UX document correctly refusing to leak upward-owned concerns downward into itself — Product Architecture sits *above* UX in this chain but still, correctly, declines to specify what UX alone should specify.

Authority is **not** the same as recency. A newer document does not automatically outrank an older one; a document only gains authority over another through the explicit process this document establishes (Sections 6 and 7). Where a newer document's own text asserts subordination to an older one, or vice versa, that assertion is only valid if the cited document has, in fact, agreed — silence or non-reciprocation does not constitute agreement (see Section 8.3 for a live example of exactly this condition, documented, not resolved, here).

---

## 5. Conflict Resolution

This section defines *process only*. No conflict identified anywhere in this document, including in Section 8, is resolved by this section. Resolving a conflict requires a dedicated governance task following the process below — never a unilateral declaration inside an unrelated document.

**If Product Architecture and UX Architecture disagree:** Product Architecture governs Product meaning; UX Architecture governs presentation of that meaning. A disagreement about what a concept *means* is resolved in Product Architecture's favor. A disagreement about how an agreed concept is *shown* is resolved in UX Architecture's favor. A disagreement about whether the two tracks' relationship is settled at all (the condition APP-001 itself flags) is not resolvable by either track alone — it requires the dedicated governance task both APP-001 and the Architecture Authority Report recommend, producing a document at this level (Architecture Governance) or above, never a self-assertion inside either track.

**If UX Architecture and the Design System disagree:** The Design System is a sub-layer of UX Architecture (Section 2). A disagreement here is an internal consistency defect within one track, resolved through that track's own established correction discipline (additive Correction Notices, non-erasure, traceability — the pattern this session's own Token Architecture program used throughout) rather than through this document.

**If Design (UX Architecture) conflicts with Core (Domain Object Architecture / Reasoning Foundations):** Core governs what exists; UX governs how it is shown. A UX document that requires a domain relationship Core does not support is not resolved by UX asserting the relationship anyway — it is a signal that either a new Core investigation is required (escalated upward, through Core's own Change Protocol) or the UX design must change to fit what Core actually supports. UX Architecture may never treat its own presentation need as sufficient justification for inventing a domain fact.

**If Implementation conflicts with documentation:** Documentation governs. A discrepancy between running code and its governing document is a defect to escalate and correct — in the code, if the document is right, or in the document, through the document's own formal amendment process, if the investigation shows the document was wrong. Code is never, by virtue of merely running, treated as having silently amended a normative document. This mirrors the Domain Object Architecture track's own already-proven resolution of its "Case vs. Observation" type-set discrepancy (Section 8.1).

**If two Draft documents disagree:** Neither outranks the other by virtue of being Draft. The conflict is recorded (an Open Governance Question, Section 8.4-style) and resolved only when at least one side reaches a higher, ratified status through its own track's normal process, or through an explicit joint resolution at this document's own level.

**If an older document contradicts a newer document:** Age alone settles nothing. The newer document only prevails if it was created *through the correct supersession process* (Section 7) with respect to the older one. Absent a formal Supersession Notice, both documents remain simultaneously in the repository and the contradiction is an Open Governance Question, not a de facto resolution in the newer document's favor — this is the exact condition `AtlasAlphaExperienceSpecification.md` and `UX-012`'s Dashboard specification are in today (Section 8.4).

---

## 6. Document Status Definitions

| Status | Meaning | Authority Level | Implementation May Depend On It | May Be Referenced | Can Be Superseded |
|---|---|---|---|---|---|
| **Normative** | Governs *process*, not content — how decisions in its own track are made. | High, but process-scoped only. | Indirectly (via the decisions it governs). | Yes. | Yes, through its own track's amendment process. |
| **Informative** | Explanatory, historical, or engineering context. Never a source of new authority. | None. | No. | Yes, as context — never as a normative citation. | Not applicable — it never held normative authority to lose. |
| **Draft** | Actively being developed; internally coherent but not yet reviewed to completion. | Provisional within its own track only. | No, without an explicit, documented exception. | Yes, with the Draft status stated alongside the reference. | Yes, freely, by its own authors, without a formal Supersession Notice. |
| **Release Candidate** | Has completed its track's own review process and is believed final, pending a defined remaining confirmation step. | High within its own track. | Yes, with the specific pending confirmation named. | Yes. | Yes, through the normal amendment/supersession process once final status is reached or reconsidered. |
| **Accepted** | Formally adopted by whatever process its track defines (e.g., an ADR's own acceptance). | Full, within its own track's scope. | Yes. | Yes. | Yes, through the formal process (Section 7). |
| **Final** | The track's own strongest status — settled, unamended, authoritative until formally revisited. | Full. | Yes. | Yes. | Yes, but only through the track's own defined amendment protocol — never informally. |
| **Historical** | Preserved for record; its own content is no longer current, but it is not erased or hidden. | None, for current guidance. Full, as a record of what was once true. | No. | Yes, explicitly as historical record, never as current authority. | Not applicable. |
| **Deprecated** | Still current but scheduled for retirement; a replacement is named or being prepared. | Diminishing — still authoritative until the retirement date, explicitly not authoritative for new work. | Existing dependents only; no new dependents. | Yes, with the deprecation and its replacement stated. | Yes — deprecation is the step immediately preceding formal supersession. |
| **Superseded** | Formally replaced by a named successor document, through an explicit Supersession Notice (Section 7). | None for current guidance; the notice itself, and the original text beneath it, remain as record. | No. | Yes, as historical record and as the subject of the Supersession Notice. | Not applicable — already superseded. |
| **Experimental** | A trial, not yet a commitment; may be withdrawn without a formal supersession process. | None binding. | No. | Yes, labeled Experimental. | Freely withdrawn without formal process. |
| **Archived** | Removed from active consideration entirely; retained only for provenance. | None. | No. | Discouraged; if referenced, only with explicit acknowledgment of archived status. | Not applicable. |

Where a document in this repository does not state its own status (the Architecture Authority Report found exactly one such case — Reasoning Foundations' `ADR-001`), it is treated as holding the status externally, consistently attributed to it by its own track's other documents, until it is corrected to self-declare, per Section 10's requirement that every future document declare its own status explicitly.

---

## 7. Supersession Rules

**A document is never superseded merely because a newer document exists.** Chronological succession is not supersession. Two documents may coexist indefinitely, even in direct tension, until the formal process below is completed.

**A document becomes Superseded only through an explicit Supersession Notice**, added to the *original* document (not merely asserted in the new one), meeting all of the following requirements — the exact pattern this session's own UX Architecture track has already used correctly once (`UX-000-The-Atlas-Experience.md`, superseded by `UX-000-Atlas-UX-Doctrine.md`) and has not yet used, incorrectly, for `AtlasAlphaExperienceSpecification.md`, which remains self-labeled Canonical despite being substantively contradicted:

1. **Dated.** The notice states the date of supersession.
2. **Named successor.** The notice names the specific document that now governs, by its exact path/title.
3. **Scope of supersession stated precisely.** Whether the entire document is superseded, or only a specific section, claim, or passage — a partial supersession (as this session's own Governance Authority Resolution performed on `UX-012`'s introduction) is valid and must say exactly what portion is affected.
4. **Original content preserved verbatim beneath the notice.** The prior text is never deleted, rewritten, or silently altered. A reader must be able to see exactly what the document used to say.
5. **Rationale stated.** Why the supersession occurred — what was found, decided, or changed.
6. **No retroactive claim.** The notice does not claim the successor's own content or reasoning existed at the time the original document was written.

**Historical documents remain in the repository.** Nothing described by this document is ever deleted as part of a supersession. A superseded document's file remains, in place, permanently, exactly as `UX-000-The-Atlas-Experience.md` remains today, in full, beneath its own Supersession Notice.

**Implicit retirement is not permitted.** A document does not become non-authoritative because a project stopped updating it, because a sprint-tracking convention changed, or because later work silently moved in a different direction. The Architecture Authority Report found exactly this condition affecting `AtlasAlphaExperienceSpecification.md` — untouched since 2026-07-08, substantively contradicted by later work, yet still self-labeled Canonical because no Supersession Notice was ever written. Per this section, that document remains, today, exactly as authoritative as its own unrevoked status claims, until a proper notice is produced. This document does not produce that notice — doing so is a content decision this document's own Section 1.1 and this task's own constraints forbid it from making.

---

## 8. Current Repository Status

This section records, without resolving, the findings of the completed Atlas Architecture Authority Report (2026-08-02, a full read-only investigation of every documentation track). It is presented here as of that investigation's date; it will drift as the repository changes and should be refreshed by a future governance pass rather than assumed current indefinitely.

### 8.1 Current authoritative tracks

- **Atlas Core Doctrine & Domain Object Architecture** — `Doctrine.md`, `OE-002` through `OE-006`, all **Final**, unamended, and independently verified against the actual `atlas/core/` code (the Case-ownership-boundary / six-Domain-Object model is implemented exactly as documented, including a previously-drifted "Case vs. Observation" type-set discrepancy that was investigated and correctly resolved in the documentation's favor).
- **Reasoning Foundations** — `ADR-002` (Judgment) and `ADR-003` (Knowledge), both **Final**. `ADR-001` (Reasoning) is treated as Final by consistent external attribution, though it does not self-declare (Section 6, final paragraph).
- **UX Doctrine** — `UX-000-Atlas-UX-Doctrine.md`, **Release Candidate RC v1.0**, with a correctly-executed formal supersession of its own predecessor already on record.
- **`ADR-005-Atlas-Reasoning-Foundations-Naming-and-Authority.md`** — **Accepted**. Cleanly resolved the original `atlas/core` (code) vs. `docs/atlas_core` (ontology track) naming collision.

### 8.2 Current draft tracks

- **Atlas Product Architecture** — `APP-000` (Draft v0.4), `APP-001` (Draft v0.3), `APS-001` through `APS-005` (all Draft, v0.1–v0.2). The entire track is currently **untracked in git** — no commit history exists for it to audit. The five APS documents were produced within a sixteen-second window of each other, which the Architecture Authority Report notes is inconsistent with the staged, dependency-respecting drafting process `APP-001` itself recommends; in particular, `APS-004` (Learning) was finalized before `APS-005` (Outcome) despite `APP-001`'s own stated position that Learning depends on Outcome existing first.
- **UX Architecture below the Doctrine** — `UX-012` and `UX-013A–G` are active and, as of this writing, carry uncommitted working-tree modifications (the result of this session's own in-progress Token Architecture and component-specification work).

### 8.3 Current historical documents

- **`UX-000-The-Atlas-Experience.md`** — formally **Historical/Superseded**, correctly retired via a dated Supersession Notice naming `UX-000-Atlas-UX-Doctrine.md` as successor, with its own original text preserved in full beneath the notice. This is the one clean example in the repository of the process Section 7 requires.

### 8.4 Current superseded documents

- Only `UX-000-The-Atlas-Experience.md`, as above. No other document in the repository carries a formal Supersession Notice meeting Section 7's requirements.

### 8.5 Current implementation documents (Engineering Documentation, informative only)

- The roughly twenty-five "Implementation Design," "Architecture Review," "Reconciliation Investigation," "Pre-Commit Review," and "Readiness Review" documents inside `docs/atlas_domain_object_architecture/`, each explicitly self-declaring no Doctrine status.
- The `*CleanupPlan.md` family and similar engineering-process documents at the top level of `docs/`.
- `atlas/core/` itself — the implementation, downstream of all normative documents above it.
- `frontend/` — reserved for a future interface; explicitly, by its own README, containing no runtime implementation yet.

### 8.6 Known governance gaps

- **Two separate, unreconciled "ADR-00N" numbering sequences exist simultaneously** in this repository — top-level `docs/ADR-004`/`ADR-005`, `docs/atlas_reasoning_foundations/ADR-001–003`, and `docs/atlas_ux/governance/ADR-001–004` — three tracks reusing the identical numbering convention independently. No document anywhere requires track-qualified citation of an ADR number, creating a latent ambiguity risk whenever "ADR-002" or similar is cited without its track.
- **"Atlas Core" is used ambiguously a second time.** `ADR-005` resolved the original collision between `atlas/core` (code) and the old `docs/atlas_core` (ontology track, since renamed to `docs/atlas_reasoning_foundations`). One day after `ADR-005`, `docs/atlas_domain_object_architecture/Doctrine.md` adopted the title "Atlas Core — Architecture Doctrine," recreating the identical naming ambiguity `ADR-005` had just foreclosed. No document has addressed this second collision.
- **No ADR governs the three-way relationship** between Domain Object Architecture, Reasoning Foundations, and `atlas/core` as a track-level question — `ADR-005` predates Domain Object Architecture's own creation by roughly one day and could not have addressed a track that did not yet exist. Individual Domain Object Architecture implementation documents have informally applied `ADR-005`'s precedent to themselves, but no document with actual cross-track authority has done so formally.
- **`ADR-005` cites two decision records ("ENG-001," "ARC-001") that do not exist as files anywhere in this repository.** Their underlying reasoning is not independently recoverable from the repository as it currently stands.
- **The Domain Object Architecture track is entirely absent from the top-level repository `README.md`'s documentation index**, most likely simple staleness — the `README.md` was last touched the day before this track began and was never revisited.

### 8.7 Known unresolved governance questions

These are recorded, per this task's own explicit instruction, without resolution:

1. **The relationship between Product Architecture and UX Architecture.** `APP-001` states, in its own words, across all five of its APS documents in sequence: *"The relationship between `docs/atlas_product_architecture/` and `docs/atlas_ux/` is undetermined... a real, unresolved governance question... it remains open until a dedicated governance task resolves it,"* and explicitly gates any specification touching AI-originated content presentation on that resolution occurring first. `UX-000-Atlas-UX-Doctrine.md`, dated one day later, declares itself subordinate to Product Architecture as settled fact and proceeds to govern AI-originated content presentation directly (its own Sections 10–11), without citing, engaging, or discharging `APP-001`'s stated gate.
2. **The relationship between the Atlas Core track and Product Architecture / UX Architecture.** No document in either direction — Core-track or Product/UX-track — has ever referenced the other. `UX-000` nonetheless cites "the Atlas Core Architecture Doctrine, OE-002, and OE-004" by name as authorities it is subordinate to; those documents do not reciprocate or acknowledge UX-000's existence.
3. **The status of `docs/AtlasAlphaExperienceSpecification.md`.** Self-labeled Canonical, untouched since 2026-07-08, its own binding "input-first, not dashboard-first" principle now substantively contradicted by `UX-012`'s fully specified Dashboard Workspace, with no Supersession Notice on record for either document with respect to the other.
4. **Whether "Investment Case" and "Commitment" are, or should become, Atlas concepts.** Neither term is currently defined as a settled concept in any of the four tracks. `UX-012` explicitly defers "Investment Case" pending future Product Architecture treatment. `UX-013C` explicitly states that "Commitment" is distinct from, and not equivalent to, "Decision" — the term the UX and Core tracks actually use. Any future work using either term should be understood as introducing a new candidate concept, not as citing an existing one.

---

## 9. Current Implementation Baseline

This section states which documentation implementation should currently follow, and which should not yet be relied upon, without resolving any question in Section 8.

**Currently authoritative enough for implementation:**

- `atlas/core/` itself, for anything already implemented — the Domain Object Model, its persistence, and its API surface are Final-governed and code-verified (Section 8.1).
- `UX-012D` (Design Token Architecture) and the completed Reasoning Token Architecture program's own canonical tokens, for anything already built in `docs/atlas_ux/UX-013A–G` — this is the most rigorously, repeatedly audited layer of documentation in the repository, with a completed Release Candidate Audit on record.
- `UX-000-Atlas-UX-Doctrine.md`, for UX-layer behavior (interaction model, accessibility, non-color communication) *not* dependent on the unresolved Section 8.7.1/8.7.2 questions.

**Advisory only — not yet safe to build against without qualification:**

- `docs/atlas_product_architecture/` in its entirety — every document in it is Draft, several of its own internal sequencing commitments were not honored (Section 8.2), and it is untracked in git.
- Any UX Architecture content that presents AI-originated content, or that depends on the Product↔UX relationship being settled (Section 8.7.1) — `APP-001`'s own stated gate on this category has not been satisfied.
- `docs/AtlasAlphaExperienceSpecification.md` — advisory as a record of a considered, once-binding product direction, but in direct, undocumented tension with the currently-active `UX-012` Dashboard specification; implementation should not silently pick a side.

**Requiring future governance resolution before being treated as settled:**

- Whether "Investment Case" and "Commitment" become real Atlas concepts, and if so, what they mean and how they relate to the existing "Case" (Core) and "Decision" (Core, Product, and UX) vocabulary already in use.
- The Product↔UX and Core↔Product/UX relationship questions in full (Section 8.7.1, 8.7.2).
- The formal status of `AtlasAlphaExperienceSpecification.md` relative to the current Dashboard-based UX direction (Section 8.7.3).

A future Sprint 1 implementation plan should treat the "Currently authoritative" list above as its foundation, treat the "Advisory only" list as informative context that must not be silently contradicted or silently assumed resolved, and should not attempt to build features that require the "Requiring future governance resolution" items to already be settled.

---

## 10. Future Governance

Every future Atlas document, at any layer of the hierarchy in Section 2, must state the following at its own outset, following the pattern the strongest existing documents in this repository (`UX-000-Atlas-UX-Doctrine.md`, the `OE-002` through `OE-006` series) already use:

1. **Parent authority** — which document(s), per Section 2, it is subordinate to.
2. **Dependencies** — which other documents its own claims rely on.
3. **Scope** — what it governs.
4. **Non-scope** — what it explicitly does not govern, especially anything a reader might otherwise assume it covers.
5. **Affected documents** — which existing documents its introduction touches, even informatively.
6. **Superseded documents** — named explicitly, with a proper Supersession Notice per Section 7, or stated as none.
7. **Migration requirements** — what, if anything, must change in dependent documents or implementation as a result.
8. **Implementation impact** — whether, and how, `atlas/core/` or `frontend/` must change.

**Future documents must never silently replace existing documents.** A new document that intends to supersede an old one must say so explicitly, in both directions — the new document names what it supersedes, and the superseded document receives the formal Supersession Notice, per Section 7, at the time of the change, not retroactively and not by omission.

**This document's own future amendment** follows the same rule it imposes on everything else: a future revision to Architecture Governance itself must state its own parent authority (`ATLAS_CONSTITUTION.md`), what it changes, and must not silently redefine any Section 8 finding — Section 8 should instead be *refreshed*, dated, and its prior version preserved per Section 7, exactly as it asks every other document in the repository to do.
