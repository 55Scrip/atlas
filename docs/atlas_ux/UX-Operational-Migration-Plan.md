# UX Operational Migration Plan

**Status:** Draft, v0.1. This is a design document only. It authorizes no edit to any operational UX document, ADR, or UX-000 itself. It defines the migration architecture that a future, separately-authorized implementation task will execute.

**Phase 0 Closure Update (2026-08-01, per the "Atlas Memory" Status Investigation and the Atlas UX Architecture Governance Phase 0 Closure task):** Phase 0 (Section 11) is complete. Atlas Memory's own Product-layer status is resolved — the completed "Atlas Memory" Status Investigation found it reduces to a composite, no-independent-identity UX view, most precisely decomposing into the already-existing `DecisionHistory`/`Decision Timeline` components, with the umbrella term itself deprecated (Final Verdict D). `ADR-001` is ratified to Accepted. The historical `UX-000-The-Atlas-Experience.md` now carries its own explicit supersession notice. `UX-000-Atlas-UX-Doctrine.md` is now Release Candidate, RC v1.0, and is the migration baseline. **Operational migration may now proceed to Phase 1**, per Section 15's own updated conclusion below. This update is additive only; it does not rewrite Section 11's own migration strategy, reopen any finding, or perform any operational-document correction.

---

## 1. Repository Baseline

Branch `main`, HEAD `91d71fef21dba401d6e9f11195c5a030cb485a23` (unchanged for this entire session). Working tree: nothing staged before this task began; untracked files were the pre-existing `docs/atlas_product_architecture/` directory and `docs/atlas_ux/UX-000-Atlas-UX-Doctrine.md`. No operational UX document, ADR, or `UX-000-Atlas-UX-Doctrine.md` was modified during this task. This document is the only file created.

## 2. Sources Read

**Normative Core** (not re-read this task; unchanged since earlier fresh reads this session, confirmed via `git status`): Atlas Core Architecture Doctrine, OE-002, OE-004.

**Normative Product** (same basis): APP-000, APP-001, APS-001–005.

**Normative UX Doctrine** (read fresh, in full, this task): `UX-000-Atlas-UX-Doctrine.md`, Draft v0.2.

**Normative UX (Accepted ADR)** (read fresh, in full, this task — reconfirmed unchanged since earlier reads this session): `ADR-001` (Proposed, not Accepted), `ADR-002`, `ADR-003`, `ADR-004`.

**Operational UX** (structure read fresh this task — headings, status lines, Correction Notices, and governing-reference declarations for all 13 documents; targeted deeper reads only where required to determine migration scope, per the task's own instruction; UX-013B §1 Conclusion had already been read in full during the "Conclusion" Status Investigation and is not re-read here): `UX-004-Investment-Workspace-Philosophy.md` (780 lines, 30 sections), `UX-005-Investment-Workspace-Screen-Specification.md` (925 lines, 27 sections), `UX-007A-Portfolio-Workspace-Wireframe-Specification.md` (1,608 lines, 40 sections), `UX-007P-Portfolio-Workspace-Final-Polish.md` (591 lines, 15 sections), `UX-008-Decision-Workspace-Philosophy.md` (762 lines, 20 sections), `UX-009-Decision-Workspace-Screen-Specification.md` (774 lines, 13-section canonical list), `UX-009A-Decision-Workspace-Wireframe-Specification.md` (1,136 lines, 13 sections in detail), `UX-010-Decision-Workspace-Interaction-Microinteraction-Specification.md` (886 lines, 26 sections), `UX-011-Decision-Workspace-Visual-Design-Polish-Specification.md` (901 lines, 31 sections), `UX-012-Atlas-Design-System-Workspace-Consistency-Specification.md` (2,257 lines, six Parts), `UX-013A-Atlas-Component-Specification-Foundation-Components.md` (2,467 lines, 20 sections), `UX-013B-Atlas-Component-Specification-Reasoning-Components.md` (2,495 lines, 19 sections), `UX-013E-Atlas-Component-Library-Final-Assembly-Architecture-Implementation-Readiness.md` (3,089 lines, 58 sections).

**Historical only, discovered during this task, not previously scoped:** `UX-013E`'s own current header states its own **Status: Superseded**, pointing to `UX-013F-Foundation-Reasoning-Component-Library-Assembly.md` for Foundation/Reasoning assembly authority and `UX-013-Interim-Decision-Monitoring-AI-Metadata-Governance-Note.md` for provisional Decision/Monitoring/AI-Collaboration/Metadata authority — a supersession the existing UX governance track already performed, implementing `ADR-002` C-05, before this migration program began. Neither `UX-013F` nor the interim governance note was in this task's own required-read list; their existence and role are recorded here because `UX-013E`'s own header directly names them, but neither was read in full. This is flagged as a scope gap in Section 13 (Deferred Work).

## 3. Current Operational UX Architecture

The operational corpus divides into five layers, exactly as `UX-Architecture-Review-001.md` §3 already found and this task's own structural read confirms unchanged: **(1) philosophy** — `UX-004`, `UX-008` (no screen, no component, explicit self-exclusion of layout); **(2) screen/information-architecture** — `UX-005`, `UX-009`; **(3) wireframe/structure** — `UX-007A`, `UX-009A`; **(4) interaction and visual design** — `UX-010`, `UX-011`, `UX-007P`; **(5) cross-Workspace design system and component library** — `UX-012`, `UX-013A`, `UX-013B`, `UX-013E` (now Superseded).

**Authority citation discipline is loose and inconsistent, confirmed directly this task.** Every APS document in the Product Architecture track carries an explicit §1 "Document Status and Authority" section naming its exact upstream dependencies. No operational UX document does this with comparable rigor. A direct search for the literal string `UX-000` across all 13 documents found it in only three: `UX-007A`, `UX-007P`, and `UX-008` — each citing the *old* `UX-000-The-Atlas-Experience.md`. The remaining ten (`UX-004`, `UX-005`, `UX-009`, `UX-009A`, `UX-010`, `UX-011`, `UX-012`, `UX-013A`, `UX-013B`, `UX-013E`) contain **zero** citation of any UX-000, old or new — the prior doctrine functioned as ambient, uncited philosophy for most of the corpus, not a formally-chained dependency. This is the single most consequential authority-architecture fact this task found, and it reframes "Authority Migration" (Section 8) from "update an existing citation" to, for ten of thirteen documents, "add a citation that has never existed."

**Prior corrections are real, dated, and already disciplined.** `UX-009`, `UX-012`, `UX-013A`, `UX-013B`, and `UX-013E` each already carry one or more Correction Notices citing `ADR-002`, `ADR-003`, or `ADR-004` by name, each preserving prior text in quotation rather than silently rewriting it — the exact non-erasure discipline `UX-000` §23 itself now requires as doctrine. These citations remain individually accurate and require no rework; they need only a parallel, new citation to `UX-000` itself alongside them, per Section 8.

**A pervasive, load-bearing term never yet tested against Product Architecture was found.** "Atlas Memory" appears 44 times across eight documents (`UX-008`, `UX-009`, `UX-009A`, `UX-010`, `UX-011`, `UX-012A`, `UX-012C`, `UX-012D`), functioning as what reads as a genuine, named, permanent container — "The Decision Workspace is part of Atlas Memory"; "the permanent decision record shown in Atlas Memory"; feeding "thesis monitoring, and decision pattern recognition" (`UX-008`). This was not surfaced by any of the three prior investigations, none of which had reason to search the operational corpus for it. It is addressed as a REQUIRED finding in Sections 4, 7, and 16.

## 4. Relationship to UX-000

| Document | Relationship |
|---|---|
| UX-004 | Needs migration — terminology and authority only; philosophy content itself is largely compatible |
| UX-005 | Needs migration — terminology and authority; one Conclusion-variant correction required |
| UX-007A | Needs migration — authority citation update (already cites old UX-000); terminology |
| UX-007P | Needs migration — same as UX-007A |
| UX-008 | Needs migration — authority citation update; the "Atlas Memory" term is most load-bearing here |
| UX-009 | Needs migration — terminology and authority; already ADR-002-corrected, compatible with the corrected canonical sequence |
| UX-009A | Needs migration — same profile as UX-009, more granular |
| UX-010 | Needs migration — terminology (Conclusion, Atlas Memory) and authority |
| UX-011 | Needs migration — terminology and authority; visual-only content otherwise compatible |
| UX-012 | Needs restructuring — the corpus's own central authority; carries the Conclusion, Recommendation, and Confidence definitions UX-000 now governs the Product-layer correspondence of; needs the most careful terminology pass |
| UX-013A | Compatible, minor migration — Foundation Components carry the least Product-adjacent content of any operational document |
| UX-013B | Needs restructuring — owns the full Conclusion component definition (§1) and the Proposed Decision Candidate Content component (§10); must be checked section-by-section against UXD-R-071 through UXD-R-073, UXD-R-076, UXD-R-111 |
| UX-013E | Historical only — already internally marked Superseded by the existing UX governance track (`ADR-002` C-05), before this program began; excluded from active migration scope |

No operational document was found fully "No change" — every one requires at minimum an authority-citation addition, per Section 3's own finding.

## 5. Migration Principles

1. **Never duplicate doctrine.** An operational document restates a UX-000 rule only by citation, never by repeating its normative text. Where an operational document currently states something UX-000 now governs more precisely (e.g., the Conclusion/Decision distinction), the operational document is corrected to cite UX-000, not left as a competing, parallel statement.
2. **Never redefine a Product Concept.** Any operational-document statement that touches what a Decision, Evidence, Learning, or Outcome *is* — not merely how it is rendered — must be checked against, and made to defer to, UX-000's own Section 9 and the APS it cites.
3. **Keep implementation local.** Screens, wireframes, components, tokens, visual design, animation, and Figma/engineering mapping remain exactly where they are. UX-000 governs none of this and this migration introduces none of it upward.
4. **Move only genuinely doctrine-level, cross-Workspace rules upward — and only when they do not already exist in UX-000.** No operational content is moved into UX-000 by this migration; UX-000 is already Release-Candidate-ready and closed to new rules absent its own amendment process (`UXD-R-110`). Where an operational document contains a rule that reads as doctrine-level, this plan flags it as a candidate for a *future* UX-000 amendment, never migrates it directly.
5. **Preserve historical integrity absolutely.** Every correction is additive and dated, following the exact Correction Notice pattern the corpus already, correctly, uses five times over. No prior wording is deleted; it is quoted and superseded in place.
6. **Terminology follows UX-000 exactly, not the reverse.** Where an operational term's own established meaning conflicts with UX-000's own terminology discipline (Section 20), the operational term is corrected or disambiguated; UX-000 is not reopened to accommodate legacy usage, consistent with this program's own standing rule against reopening accepted architecture.
7. **A term with no tested Product-layer correspondence is not silently assumed compatible.** Following the exact precedent the "Conclusion" Status Investigation set, any operational term found, during migration, to carry unexamined Product-adjacent weight (ownership, identity, persistence, cross-Workspace permanence) is referred to its own dedicated investigation before correction, never resolved inline.
8. **Correction order follows dependency order**, exactly as the Atlas UX Source Correction Plan's own precedent already established for the `ADR-002` corrections: an already-authoritative assembled document is corrected before the volumes beneath it are re-checked against it.

## 6. Document-by-Document Migration Matrix

| Document | Survives unchanged | Terminology alignment | Authority update | Move to UX-000 | Remain local | Redundant | Historical | ADR refs change | Split/Merge |
|---|---|---|---|---|---|---|---|---|---|
| UX-004 | Philosophy content (Workspace purpose, "Conclusions Before Evidence" heuristic) | Yes — §6 "Conclusion," §15 "long-term memory" | Add UX-000 citation (currently none) | No | Yes, entirely | §8/§30 core-principles overlap with UX-000 §12/§24 (restatement, not conflict) | No | None currently cited | No |
| UX-005 | Screen structure (§4–§27) | Yes — §5 "Atlas Conclusion," §9 "Your Decision" | Add UX-000 citation (currently none); its own Correction Notice re: UX-003 stands unchanged | No | Yes, entirely | None found | No | None currently cited | No |
| UX-007A | Wireframe structure | Yes — "Atlas Portfolio Conclusion" (§9), Scenario Analysis (§18) | Update existing old-UX-000 citation to new UX-000 | No | Yes, entirely | None found | No | None currently cited | No |
| UX-007P | Polish content | Yes — same Conclusion terms as UX-007A | Update existing old-UX-000 citation | No | Yes, entirely | None found | No | None currently cited | No |
| UX-008 | Decision-as-first-class-object philosophy (§2), Decision Quality framing (§5) | Yes, most load-bearing — "Atlas Memory" (pervasive), §4 Conclusion/Decision distinction | Update existing old-UX-000 citation | No | Yes, entirely | §20 Governing Principles list overlaps UX-000 §24 UXPs (restatement) | No | None currently cited | No |
| UX-009 | Canonical 13-section list (already ADR-002-corrected) | Yes — Section 1 "Current Conclusion," Section 3 "Proposed Decision" | Add UX-000 citation alongside existing ADR-002 Correction Notice | No | Yes, entirely | None found | No | ADR-002 citation stands; add UX-000 | No |
| UX-009A | Same 13-section detail | Yes, same terms, more granular (§1, §3 anatomy-level) | Add UX-000 citation | No | Yes, entirely | None found | No | None currently cited | No |
| UX-010 | Interaction/microinteraction content | Yes — Conclusion (§9), "Atlas Memory" (§18 "View decision in Atlas Memory") | Add UX-000 citation | No | Yes, entirely | None found | No | None currently cited | No |
| UX-011 | Visual design content | Yes — "The Current Conclusion Card" (§30) | Add UX-000 citation | No | Yes, entirely | None found | No | None currently cited | No |
| UX-012 | Parts II, V, VI (typography/spacing, interaction/navigation, tokens) | Yes, most extensive — Conclusion (4 variants defined here), Atlas Recommendation (§28), Confidence (already qualitative, compatible) | Add UX-000 citation alongside existing ADR-002/ADR-004 Correction Notices | No | Yes, entirely | None found beyond restatement already resolved by prior ADR corrections | No | ADR-002, ADR-004 citations stand; add UX-000 | Consider whether the Conclusion variant table (Primary/Current/Portfolio/Review) should be extracted into its own cross-referenced subsection once corrected, for discoverability — not required |
| UX-013A | Foundation Component anatomy | Minimal — least Product-adjacent document in the corpus | Add UX-000 citation (currently cites only UX-012) | No | Yes, entirely | None found | No | ADR-004 citation stands; add UX-000 | No |
| UX-013B | §1 Conclusion (full component spec), §10 Proposed Decision Candidate Content, §9 Scenario Analysis | Yes, most extensive of any single document — every UXD-R-071–073, UXD-R-076, UXD-R-089, UXD-R-111 correspondence applies directly here | Add UX-000 citation alongside existing ADR-002/ADR-003/ADR-004 Correction Notices | No | Yes, entirely | None found | No | ADR-002, ADR-003, ADR-004 citations stand; add UX-000 | No |
| UX-013E | None — entire document | N/A — historical | N/A | No | No | Entire document, relative to UX-013F | **Yes — already Superseded per its own header, independent of this migration** | N/A | No |

## 7. Terminology Migration

**Conclusion** — the single largest terminology item, present as a load-bearing term in all 13 documents. Every occurrence must be checked against `UXD-R-071`'s five-variant model (initial Current Conclusion, Investor-engaged Current Conclusion, Historical Conclusion, Review Conclusion, Primary/Portfolio Conclusion). `UX-013B` §1 already matches this model almost exactly (confirmed by the "Conclusion" Status Investigation's own full read); `UX-012`'s own four-variant definition (Primary/Current/Portfolio/Review) is the corpus's second most load-bearing source and needs the same check. No document was found to *contradict* the model; several (`UX-013B` §1's own "Semantic Meaning": "It is not candidate content... It is not a decision") already anticipate it closely. The correction is additive citation, not rewrite, in every instance found.

**Recommendation / Atlas Recommendation / Proposed Decision Candidate Content** — already resolved architecturally by `ADR-003`, already partially implemented in `UX-013B` (its own Correction Notice documents the Phase 3D-1 rename). `UX-012` §28's "Atlas Recommendation" remains untouched and correct. One residual item, already known and out of `ADR-003`'s own scope: "Portfolio Recommendation" (`UX-013B`, per its own Correction Notice) remains named "Recommendation" and requires its own future, dedicated terminology decision per `UXD-R-076` before correction — not resolved here.

**Proposed Decision** — present in `UX-009`/`UX-009A` Section 3, `UX-012`'s canonical list. Needs an added citation to `UXD-R-111` wherever it appears as a defined field, not a rewrite.

**Reasoning** — used pervasively as "Reasoning Components," "Reasoning Component Philosophy" (`UX-013B`). APP-001 §7 Observation 1's own "Investor Reasoning" rename remains open at the Product layer; this migration does not rename "Reasoning" anywhere, since the Product-layer rename has not itself occurred. Flagged for future alignment only if/when APP-000 is amended, per `UXD-R-096`.

**Learning** — not found as a named UX-layer term anywhere in the 13 documents' own headings; the operational corpus uses "Atlas Memory" instead (see below), never "Learning" directly. No direct terminology conflict found, but see the "Atlas Memory" finding, which is closely adjacent.

**Reflection** — confirmed, again, absent from every document in this task's own read scope, consistent with both prior investigations' identical finding. No action required.

**Workspace / Dashboard** — used correctly and consistently throughout, exactly as `UXD-R-095` already requires. Needs only a citation addition, no rewrite.

**Memory — REQUIRED, the most significant new finding of this task.** "Atlas Memory" appears 44 times across eight documents, functioning as a named, apparently-permanent container ("The Decision Workspace is part of Atlas Memory"; feeds "thesis monitoring, and decision pattern recognition," per `UX-008`). `UXD-R-094` states Memory "SHALL NOT be used as a Product Concept" and "MAY remain ordinary UX language only where it implies no independent Product semantics" — but "Atlas Memory," as actually used, reads far closer to a genuine, cross-Workspace, permanent product surface than to incidental ordinary language. This term has never been tested against Product Architecture the way "Conclusion" was. Per Migration Principle 7, this is referred to its own dedicated investigation, mirroring the "Conclusion" Status Investigation exactly, before any operational document containing it is corrected. See Section 16, REQUIRED.

**Session** — not found as a load-bearing heading term in this task's own structural read of the 13 documents (it appears, per the Architecture Review's own earlier finding, only as an unresolved scroll-restoration boundary question in `UX-013A`/`UX-013E`). No correction required beyond the existing `UXD-R-093` rule already covering informal use.

**Confidence** — `UX-012`'s own definition ("not a gauge or percentage; a qualitative statement") is already fully compatible with `UXD-R-063`–`065`. `UX-008` §11, `UX-010` §11, `UX-011` §14, and `UX-013E` §21's own "Confidence presentation tokens" all need a consistency check against `UX-012`'s own already-correct qualitative model, not a rewrite of any single document — this is an internal-corpus consistency item, not a UX-000-driven correction.

**Outcome / Scenario "outcomes"** — the lowercase/capitalized collision `ADR-004` and the Terminology Reconciliation Investigation both already flagged. Present in `UX-007A` §18 and `UX-013B` §9 (Scenario Analysis). Needs the disambiguating terminology `UXD-R-089` already requires; no document currently misuses the capitalized Product Concept.

**Comparison** — `UX-013B` §8, already correctly scoped per `ADR-004`; needs only a citation addition.

**Decision Context / Investor Reasoning** — confirmed, by direct corpus-wide search, to appear in **zero** operational documents. `UX-000`'s own `UXD-R-095` states a Decision Workspace "MAY represent one Decision Context" without either term ever having been introduced to the operational corpus that would need to state this correspondence. This is a real, load-bearing gap: no operational document currently has anywhere to place this cross-reference. Recommended as a `UX-012`-level addition (its own canonical-terminology home) during migration, not a UX-000 change.

**Historical Record** — already reasonably disciplined per the Terminology Reconciliation Investigation's own finding; needs a citation addition only.

## 8. Authority Migration

**The exact citation change required, by document:**

- `UX-004`, `UX-005`, `UX-009`, `UX-009A`, `UX-010`, `UX-011`, `UX-012`, `UX-013A`, `UX-013B` — **add** a `UX-000 — Atlas UX Doctrine (Draft v0.2)` governing-authority citation; none currently exists.
- `UX-007A`, `UX-007P`, `UX-008` — **replace** the existing citation to `UX-000 — The Atlas Experience` with `UX-000 — Atlas UX Doctrine (Draft v0.2)`, per a formal Correction Notice. `UX-000-The-Atlas-Experience.md` now carries its own supersession notice, per `UX-000`'s own `UXD-R-109` — this prerequisite is satisfied; see Section 15's own update.
- `UX-013E` — no citation change; historical, out of active scope.

Every existing `ADR-002`/`ADR-003`/`ADR-004` citation across `UX-009`, `UX-012`, `UX-013A`, `UX-013B` remains accurate and unchanged; these ADRs are themselves now cited as Normative UX authority *within* `UX-000` Section 4, so no operational document's own ADR citation becomes incorrect — it becomes doubly grounded, first directly and now also transitively through `UX-000`.

## 9. Redundant Material

No duplicated *rule* was found — only duplicated *restatement* at a different register, the same pattern this program has already classified, at the doctrine level, as acceptable (Product Principles restated at increasing specificity through APS documents; the old `UX-000`'s own sections restated at the doctrine level in the new `UX-000`). Specifically: `UX-004` §8/§30 and `UX-008` §20's own principle lists overlap substantively with `UX-000` §12 and §24's own `UXP`s. Nothing is removed by this classification — both are retained, with the operational document's own list becoming, on migration, an explicit restatement grounded in and citing the corresponding `UXP`, exactly as `UX-000`'s own Section 24 opening statement requires of every `UXP` itself.

## 10. Historical Preservation

Every correction contemplated by this plan follows the identical Correction Notice pattern the corpus has already used five times (`UX-005`, `UX-008`, `UX-009`, `UX-012`, `UX-013A`, `UX-013B`): prior text preserved verbatim in quotation, the correction dated, the governing ADR or document named, and an explicit statement that the correction does not claim the new wording existed historically. `UX-013E`'s own existing historical treatment (marked Superseded, its body "preserved verbatim... not edited further," per its own header) is the model this plan follows for any future document a migration phase fully retires. `UX-000-The-Atlas-Experience.md` itself remains untouched by this plan, per Section 8, above, and per `UX-000`'s own `UXD-R-105`–`109`.

## 11. Recommended Migration Order

**Phase 0 — Prerequisite (blocks all else).** Resolve the "Atlas Memory" open question (Section 7, Section 16) via its own dedicated investigation, mirroring the "Conclusion" Status Investigation. Formally ratify `ADR-001` to Accepted status. Add the required supersession notice to `UX-000-The-Atlas-Experience.md` itself. None of these three items touches any operational document; all three are prerequisites `UX-000` itself already names as open (Section 26) or this plan newly surfaces.

**Phase 1 — The corpus's own central authority.** Correct `UX-012` first, exactly mirroring the Atlas UX Source Correction Plan's own established precedent ("the assembled document is corrected first, because it is already the sole authority"). Add the UX-000 citation; check its four-variant Conclusion definition and its Confidence definition against Sections 9 and 13/14 of `UX-000`; add the Decision Context ↔ Decision Workspace cross-reference (Section 7, above).

**Phase 2 — The component library's own Product-adjacent volume.** Correct `UX-013B`, since it owns the fullest single concentration of Product-adjacent content (the Conclusion component, Proposed Decision Candidate Content, Scenario Analysis) and depends on `UX-012`'s own Phase 1 correction landing first.

**Phase 3 — The Decision Workspace lineage**, in its own existing dependency order: `UX-008` → `UX-009` → `UX-009A` → `UX-010` → `UX-011`. Each depends on the one before it, exactly as their own existing `Depends on` headers already state; correcting out of this order would require redoing work once an upstream document changes.

**Phase 4 — The Investment and Portfolio Workspace lineages**, which do not depend on Phase 3 and may proceed in parallel with it: `UX-004` → `UX-005`; `UX-007A` → `UX-007P`.

**Phase 5 — Foundation Components.** `UX-013A`, last, since it carries the least Product-adjacent content of any document and depends on nothing from Phases 1–4.

**Not phased — excluded from active scope.** `UX-013E`, already historical.

## 12. Risks

**Migration risk.** Correcting `UX-012` (Phase 1) before Phase 0's "Atlas Memory" question is resolved risks correcting a document whose own content may itself need revision once that question is answered — exactly the sequencing risk this program's own established discipline (resolve the open concept question before touching dependent documents) exists to prevent.

**Governance risk.** `ADR-001`'s own unratified status (still Proposed) means any future ADR produced during this migration inherits the same unresolved-authority question `UX-000` §21 already flags; a migration-phase ADR should not be the vehicle used to also ratify `ADR-001` itself, since that would conflate two different, independently-justified decisions.

**Terminology risk.** "Atlas Memory" is the dominant risk in this category (Section 16). A secondary, lower risk: correcting Conclusion terminology across 13 documents in parallel, rather than in the phased order above, risks inconsistent application if `UX-012`'s own four-variant definition is not corrected first as the shared reference point.

**Historical risk.** None found beyond the already-known, already-tracked `UX-013C`/`UX-013D` provenance gap (`ADR-001`/`ADR-002` C-05), which this migration does not touch and does not need to resolve.

**Authority risk.** Ten of thirteen documents currently have no UX-000 citation at all (Section 3). Until Phase 0–5 corrections land, these documents remain, formally, uncited to any UX doctrine — a real, if already-disclosed, gap this plan closes but has not yet closed.

## 13. Deferred Work

`UX-013F-Foundation-Reasoning-Component-Library-Assembly.md` and `UX-013-Interim-Decision-Monitoring-AI-Metadata-Governance-Note.md` — discovered via `UX-013E`'s own header, named as its replacement authority, but neither was in this task's own required-read list and neither was read. A future task must determine their own relationship to this migration plan before Phase 2 (which targets `UX-013B`, adjacent to but not identical to this pair) can be considered complete. "Portfolio Recommendation"'s own terminology correction, per `ADR-003`'s own explicit non-scope. The `UX-004`/`UX-008` principle-list-to-`UXP`-citation restatement (Section 9) is deferred to whichever phase corrects each document, not resolved as its own separate item. Full migration of `UX-013E`'s own Decision/Monitoring/AI-Collaboration content is explicitly out of scope — it is historical, per Section 6.

## 14. Final Migration Strategy

**Recommended model: phased, dependency-ordered correction, Phase 0 first (Section 11), using the Correction Notice pattern the corpus has already used five times, never a wholesale rewrite of any document.**

**Rejected alternative — migrate all 13 documents simultaneously.** Rejected because it violates Migration Principle 8 (dependency order) and risks exactly the inconsistency Section 12's Terminology risk names — correcting `UX-013B`'s own Conclusion content before `UX-012`'s shared reference definition is corrected would require redoing `UX-013B`'s own work once `UX-012` changes.

**Rejected alternative — defer all terminology correction until every open question (Atlas Memory, Portfolio Recommendation, Confidence scale) is resolved.** Rejected as unnecessarily blocking: most of the corpus (12 of 13 documents' worth of Conclusion, Workspace, Dashboard, Session, Historical Record, and authority-citation corrections) does not depend on Atlas Memory's own resolution at all, and holding the entire program hostage to one open question — the exact failure mode this program's own methodology exists to avoid — would be a worse outcome than the bounded, disclosed Phase 0 gate this plan instead proposes.

**Rejected alternative — treat `UX-013E` as still-active and migrate it.** Rejected because it is already, independently, correctly marked Superseded by the existing UX governance track, before this program began; migrating it would duplicate work its own successor documents (out of this task's scope) already exist to do.

## 15. Readiness

**Operational migration cannot begin immediately for Phase 1 as originally scoped.** The exact blocker: Section 16's REQUIRED "Atlas Memory" finding must be resolved by its own dedicated investigation before `UX-012` — the very first document in the recommended order — can be safely corrected, since `UX-012A`/`UX-012C`/`UX-012D` (the Design System's own foundational lineage) are among the eight documents carrying the term.

**Phase 0's other two items (ADR-001 ratification, the old UX-000 supersession notice) do not block operational-document correction directly, but do block the authority-citation update for `UX-007A`/`UX-007P`/`UX-008` specifically** (Section 8), since those three documents' own citation correction is explicitly conditioned on the old UX-000 carrying its own supersession notice first.

**No blocker prevents this plan itself, or preparatory work not touching operational documents, from proceeding now.**

**Update (2026-08-01):** the Phase 1 blocker stated above is resolved. Atlas Memory's status was determined by its own dedicated investigation (Final Verdict D — deprecated terminology, decomposes into `DecisionHistory`/`Decision Timeline`, no independent Product identity); `ADR-001` is ratified; the old UX-000 carries its own supersession notice; `UX-000-Atlas-UX-Doctrine.md` RC v1.0 is the migration baseline. Phase 0 is complete in full. **Operational migration may now proceed to Phase 1**, adopting the Atlas Memory rule stated in that investigation's own Section 21 as part of `UX-012`'s own correction. The original analysis above is preserved unchanged as the historical record of what the blocker was and why.

## 16. Classified Findings

**BLOCKER:** none. Nothing found in this task prevents the migration program from ever proceeding; the one gating item (Atlas Memory) is a bounded, precedented next step, not a structural failure.

**REQUIRED:**
1. **RESOLVED (2026-08-01) — "Atlas Memory"'s own Product-layer correspondence must be resolved by a dedicated investigation before any document containing it is corrected** (Sections 3, 7, 11, 15). 44 occurrences across 8 documents; functioned as an apparent permanent, cross-Workspace container, never yet tested against Product Architecture. The completed "Atlas Memory" Status Investigation resolved this (Final Verdict D): the term is deprecated, decomposing into the already-existing `DecisionHistory`/`Decision Timeline` components, with no independent Product identity. This finding is not reopened here; only its resolution status is recorded.
2. **Ten of thirteen operational documents currently carry no UX-000 citation at all** and require one added, not merely updated (Sections 3, 8).
3. **`UX-013F` and the interim Decision/Monitoring/AI-Collaboration governance note must be read and their own relationship to this plan determined** before Phase 2 can be considered complete (Section 13).

**RECOMMENDED:**
1. Add an explicit Decision Context ↔ Decision Workspace cross-reference at the `UX-012` level, since no operational document currently states this correspondence at all (Section 7).
2. Reconcile `UX-013E` §21's "Confidence presentation tokens" language against `UX-012`'s own already-correct qualitative model, as an internal-corpus consistency item independent of UX-000 (Section 7).
3. Resolve "Portfolio Recommendation"'s own outstanding terminology question, per `ADR-003`'s own explicit deferral, before or during Phase 2 (Section 13).

**OBSERVATION:**
1. The corpus's own existing Correction Notice discipline (five prior instances, all citing a specific ADR, all preserving prior text in quotation) is already the exact model this plan's own every future correction should follow — a genuine strength, not a gap.
2. `UX-013E`'s own self-supersession, discovered mid-task, is independent confirmation that the corpus's own governance discipline continues to function correctly even absent this program's own direct involvement.

## 17. Repository Verification

`git status`: only the pre-existing `docs/atlas_product_architecture/` directory, `docs/atlas_ux/UX-000-Atlas-UX-Doctrine.md`, and this newly-created `docs/atlas_ux/UX-Operational-Migration-Plan.md` appear, all untracked. Nothing staged. No operational UX document, ADR, or `UX-000-Atlas-UX-Doctrine.md` was modified. HEAD unchanged at `91d71fef21dba401d6e9f11195c5a030cb485a23`. Working tree unchanged from baseline except for the one new file this task was authorized to create.
