# Atlas Alpha Baseline v1.0

**Status:** Accepted — Implementation Baseline.
**Owner:** Atlas Product.
**Governs:** Which documents govern Atlas Alpha implementation, as of this baseline's date. Nothing else.
**Subordinate to:** `ATLAS_CONSTITUTION.md` and `docs/Architecture-Governance.md`.
**Created:** 2026-08-02, on the basis of the completed Atlas Architecture Authority Report and the newly established `docs/Architecture-Governance.md`.

---

## 1. Purpose

This document freezes the current authoritative Atlas Foundation, as it stands on the date above, into one stable implementation baseline.

Atlas's documentation is large, multi-track, and — as `docs/Architecture-Governance.md` §8 records — partially in-progress, partially in tension, and partially still Draft. A developer beginning Alpha implementation should not need to independently re-derive which of dozens of documents currently govern before writing a single line of code. This document exists so they do not have to.

**Future implementation should consult this document first, before consulting any individual specification.** This document does not replace those specifications — it tells a reader which ones currently apply, at what strength, and which questions about them remain open. Where this document and an individual specification appear to disagree about content, the specification governs its own content (per `docs/Architecture-Governance.md` §4); this document only governs which specifications currently apply and in what order.

This document freezes a **snapshot**. It does not freeze Atlas itself, and it does not prevent any track from continuing its own work. A later, explicit baseline supersedes it, per Section 8 below — this document does not attempt to anticipate what that baseline will say.

---

## 2. Alpha Foundation Snapshot

The current Atlas Foundation, as established by `docs/Architecture-Governance.md`, consists of the following layers. Each is summarized by role only — its content is not restated here; consult the named document directly, or `docs/Architecture-Governance.md` §3 for its full responsibility definition.

| Layer | Document(s) | Role |
|---|---|---|
| **Constitution** | `ATLAS_CONSTITUTION.md` | States why Atlas exists, its mission, its non-negotiable principles, and its decision framework. The single document every other layer is ultimately answerable to. |
| **Architecture Governance** | `docs/Architecture-Governance.md` | States how Atlas's own documentation is structured, which documents govern which others, how conflicts are resolved, and how documents are retired. Governs documentation authority only — not Atlas itself. |
| **Core Doctrine** | `docs/atlas_domain_object_architecture/Doctrine.md` | States the method by which Atlas Core's architecture is investigated, decided, and changed. Governs process, not content. |
| **Domain Object Architecture** | `docs/atlas_domain_object_architecture/OE-002` through `OE-006` | The authoritative, Final, code-verified statement of what Domain Objects exist in the implemented system, how they relate, and what invariants hold. |
| **Reasoning Foundations** | `docs/atlas_reasoning_foundations/ADR-001–003`, `Doctrine.md` | Settles the philosophical nature of Reasoning, Judgment, and Knowledge as categories, independent of any specific object or screen. |
| **Product Architecture** | `docs/atlas_product_architecture/APP-000`, `APP-001`, `APS-001–005` | Translates settled Core concepts into named Product Concepts a Product author can specify features against. Currently entirely Draft. |
| **UX Architecture** | `docs/atlas_ux/UX-000-Atlas-UX-Doctrine.md` and the corpus beneath it | Defines how Product Concepts are presented — Workspaces, components, interaction, tokens. |
| **Design Doctrine** | *(no separate document — see below)* | Per `docs/Architecture-Governance.md` §2, no document titled "Design Doctrine" exists apart from `UX-000-Atlas-UX-Doctrine.md` itself, which already serves this role for the UX Architecture track. |
| **Design System** | `docs/atlas_ux/UX-012`, `UX-012A–D` | The shared visual and presentation-token vocabulary — the sole canonical Design Token authority, established through this session's own completed, audited Token Architecture program. |
| **Engineering Handbook** | `docs/DevelopmentGuide.md`, plus the informative implementation-design/architecture-review corpus in `docs/atlas_domain_object_architecture/` and the `*CleanupPlan.md` family | Records local verification steps, code-quality rules, and implementation-level decisions. Explicitly non-normative — never a source of new authority, per every one of these documents' own stated terms. |

Component Specifications (`UX-013A–G`), the Constitution's own sibling documents (`ATLAS_MANIFEST.md`, `docs/ATLAS_ARCHITECTURE.md`, `docs/ATLAS_ROADMAP.md`), and the implementation itself (`atlas/core/`, `frontend/`) all exist and matter to Alpha, but are positioned by the hierarchy above rather than being independent top-level layers — see Section 3 of `docs/Architecture-Governance.md` for their own individual responsibility definitions.

---

## 3. Authority Chain

The current implementation authority chain, per `docs/Architecture-Governance.md` §2 and §4, unchanged and simply restated here for a single point of reference:

```
ATLAS_CONSTITUTION.md
        │
        ▼
Architecture Governance
        │
        ▼
Core Doctrine  &  Domain Object Architecture
        │
        ▼
Reasoning Foundations
        │
        ▼
Product Architecture            (Draft — see Section 4/6 below)
        │
        ▼
UX Architecture
  ├─ UX Doctrine  (UX-000, RC v1.0)
  ├─ Design System  (UX-012 family)
  └─ Component Specifications  (UX-013A–G)
        │
        ▼
Engineering Documentation  (informative only — never normative)
        │
        ▼
Implementation  (atlas/core/, frontend/)
```

Two rules carry forward from `docs/Architecture-Governance.md` §4 and apply directly to every Alpha implementation decision: **higher layers must never redefine lower layers** (a UX specification may not assert a domain relationship Core does not support), and **lower layers must never leak presentation concerns upward** (a Domain Object must never encode a visual treatment). Authority in this chain is never a function of which document is newest — only of the formal process `docs/Architecture-Governance.md` §5–§7 defines.

---

## 4. Alpha Scope

The following reflects the scope most recently articulated for Alpha planning. It is recorded here as the *intended* scope, not as a settled architectural fact — two of the six items below name concepts that `docs/Architecture-Governance.md` §8.7.4 identifies as not yet defined anywhere in the current documentation. That open question is not resolved by this document; it is flagged inline, below, exactly where it matters.

### Included

- **Dashboard** — a fully specified, current UX Workspace (`docs/atlas_ux/UX-012` §14).
- **Investment Case** — intended for Alpha, but **not yet a settled Atlas concept**. `UX-012` itself currently defers "Investment Case" as a UX presentation artifact "whose complete Product-layer correspondence is open pending future Investment Case / Portfolio Product Architecture treatment." Alpha work using this term should be understood as introducing a candidate concept, not citing an existing one — see `docs/Architecture-Governance.md` §8.7.4 and §9.
- **Decision Workspace** — a fully specified, current UX Workspace (`docs/atlas_ux/UX-012`).
- **Knowledge** — corresponds to the existing `atlas.domains.knowledge` package (`docs/ProjectStructure.md`) and/or the `Knowledge Reference` Domain Object (`OE-002` §4); which of the two, or both, Alpha draws on is an implementation-scoping decision outside this document's own authority.
- **Reasoning** — corresponds to the `Reasoning Trace` Domain Object (`OE-002` §4) at the Core layer, and to Reasoning-tier component specifications (`docs/atlas_ux/UX-013B`) at the UX layer. Note that "Reasoning" is also independently the subject of an ontological account in Reasoning Foundations (`ADR-001`) and a distinct Product Concept in Product Architecture (`APP-001` §3.3) — three tracks use the same word for related but not identically-scoped ideas; `docs/Architecture-Governance.md` §8.6 records this as a known naming-discipline gap, not resolved here.
- **Commitment** — intended for Alpha, but **explicitly not a settled Atlas concept**. `docs/atlas_ux/UX-013C` states directly that "Commitment" is distinct from, and not equivalent to, "Decision" — the term the UX and Core tracks actually specify. Alpha work using "Commitment" should either adopt the existing "Decision" / "Record Decision" vocabulary already specified in `UX-013C`, or treat "Commitment" as a new candidate concept requiring its own governance treatment before implementation — this document does not decide which.

### Deferred

- **Monitoring**
- **Reflection**
- **Coach intelligence**
- **Labs**

These are explicitly excluded from the current Alpha scoping and are not addressed by this baseline. Their own governing documentation (where it exists — e.g., `atlas/monitoring`, the `reflection_*` application/domain packages in `atlas/core`) remains part of the Atlas Foundation but is not treated as part of Alpha's implementation surface by this document.

### Out of Scope

- Anything not named above or in "Deferred," including but not limited to: live market data or broker integration, AI-generated reasoning content beyond what is already labeled and governed by existing UX Doctrine rules, multi-device account sync, and any capability named in `docs/AtlasAlphaExperienceSpecification.md`'s own no-account/local-storage/Temporary-Workspace model that is not also present in the Included list above. That document's own relationship to the currently-scoped, Dashboard-based Alpha direction is an open governance question (`docs/Architecture-Governance.md` §8.7.3) and is neither adopted nor rejected by this baseline.

---

## 5. Implementation Principles

These principles govern how Alpha is built, not what it does. They are drawn directly from `ATLAS_CONSTITUTION.md`'s own Non-Negotiable Principles and `docs/Architecture-Governance.md`'s own Authority Chain rules, restated here as implementation-facing commitments:

- **Preserve architecture.** Implementation follows the authority chain in Section 3. No implementation decision may substitute for a governance decision that has not yet been made.
- **Preserve terminology.** Where a term is already settled (e.g., "Decision," "Case," "Observation," "Workspace," "Dashboard"), implementation uses it exactly as specified. Where a term is not yet settled (Section 4's flagged items), implementation does not silently settle it by shipping code that assumes one meaning.
- **Preserve explainability.** Per the Constitution: "Every Atlas Rating must be explainable." Every conclusion Alpha presents traces to the evidence and reasoning behind it — never a bare assertion.
- **Preserve decision traceability.** Per the Constitution's own Mission: "Atlas should preserve the reasoning behind investment decisions, not just the outcomes." Alpha's data model must retain the reasoning trail, not only the final recorded Decision.
- **Evidence before opinion. Context before conclusion. Calm before clever.** The Constitution's own ordering applies to implementation sequencing exactly as it applies to product behavior — features that display a conclusion must not ship ahead of the evidence-and-reasoning surfaces that justify it.
- **No implementation may contradict a governing document.** Where an implementation constraint appears to require contradicting Section 3's chain, the correct action is to escalate for the governing document to be reviewed (per `docs/Architecture-Governance.md` §5, "If Implementation conflicts with documentation") — never to silently diverge.
- **No implementation may resolve an open governance question by default.** Where Section 4 or Section 6 names an open question, code must not encode a silent answer to it. If an answer is operationally unavoidable, it must be recorded as a disclosed assumption, not presented as settled architecture.

---

## 6. Repository Status

Full analysis lives in `docs/Architecture-Governance.md` §8, and is not duplicated here. As of this baseline's date:

- **Active documentation:** Core Doctrine & Domain Object Architecture (Final, code-verified), Reasoning Foundations (Final for Judgment and Knowledge), UX Doctrine (RC v1.0), `ADR-005` (Accepted) — see `docs/Architecture-Governance.md` §8.1.
- **Draft documentation:** all of Product Architecture (`APP-000`, `APP-001`, `APS-001–005`), and the active UX Design System / Component Specification corpus below the Doctrine — see §8.2.
- **Historical documentation:** `UX-000-The-Atlas-Experience.md` — the one cleanly-executed supersession on record — see §8.3.
- **Known governance gaps:** the duplicate "ADR-00N" numbering across three tracks, the second unaddressed "Atlas Core" naming collision, the missing three-way ADR between Domain Object Architecture / Reasoning Foundations / `atlas/core`, and the two undiscoverable ADR-005 citations (`ENG-001`, `ARC-001`) — see §8.6.
- **Known unresolved questions:** the Product↔UX relationship (`APP-001`'s own repeatedly-stated, never-discharged gate), the Core↔Product/UX relationship (never addressed in either direction despite `UX-000` citing Core by name), the status of `docs/AtlasAlphaExperienceSpecification.md`, and whether "Investment Case" and "Commitment" become real Atlas concepts — see §8.7, and Section 4 above.

None of these is resolved by this baseline. This document's own contribution is only to state, in Section 9 of `docs/Architecture-Governance.md` and restated for Alpha specifically in Section 9 below, what implementation may currently build against despite them.

---

## 7. Definition of Done

Alpha implementation is complete only when all of the following hold simultaneously:

- **Repository remains governed by this baseline.** No implementation decision has silently superseded, contradicted, or bypassed the authority chain in Section 3, or any governing document it points to.
- **Core workflow functions.** The workflow intended for Alpha (Dashboard → the Section 4 "Included" capabilities → return to Dashboard) is demonstrably usable end to end, using only terminology already settled or explicitly flagged as a disclosed candidate concept per Section 4.
- **Documentation and implementation remain aligned.** Per `docs/Architecture-Governance.md` §5 ("If Implementation conflicts with documentation: Documentation governs"), no shipped behavior contradicts a Final, Accepted, or Release Candidate document without that document having been formally revisited first.
- **Tests pass.** Per `docs/DevelopmentGuide.md`: `python -m compileall atlas tests` and `python -m pytest` succeed; new behavior carries new tests; deterministic engines carry deterministic tests.
- **Architecture remains intact.** The Domain Object Model (`OE-002`) is unamended by implementation necessity; where a genuine gap surfaces, it is escalated as a governance question (Section 6), not silently patched around in code.

---

## 8. Future Baselines

This baseline is superseded only by another explicit baseline document, never by the passage of time, a change in direction, or a later document's own unilateral claim. This is the same rule `docs/Architecture-Governance.md` §7 establishes for every other document in the repository, applied here to baselines specifically.

A future baseline — for example, **Atlas Alpha Baseline v1.1**, **Atlas Beta Baseline**, or **Atlas v1.0 Baseline** — supersedes this one only when it:

1. Is created as its own, explicitly named document (following this document's own naming pattern: `Atlas-<Stage>-Baseline-<Version>.md`);
2. States its own parent authority (`ATLAS_CONSTITUTION.md` and `docs/Architecture-Governance.md`, unless that chain has itself changed);
3. Names this document (`Atlas-Alpha-Baseline-v1.0.md`) explicitly as what it supersedes, in full or in stated part, per `docs/Architecture-Governance.md` §7's Supersession Notice requirements (dated, named successor, precise scope, original content preserved, rationale stated, no retroactive claim);
4. Is added as a Supersession Notice on *this* document, at the time of the change — not asserted only in the new baseline, and not applied retroactively.

Until such a document exists, **this baseline remains the current, sole entry point for Alpha implementation authority.**

---

## Final Statement

This document freezes the current Atlas Foundation and establishes the official implementation baseline for Atlas Alpha. Future implementation shall treat this document as the primary entry point into the Atlas documentation ecosystem until a subsequent baseline explicitly supersedes it.
