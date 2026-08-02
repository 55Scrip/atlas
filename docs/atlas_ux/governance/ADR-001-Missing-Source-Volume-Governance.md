# ADR-001 — Missing Source Volume Governance

## Status

Accepted

**Ratification Note (2026-08-01, per the Atlas UX Architecture Governance Phase 0 Closure task):** This ADR's status is corrected from Proposed to Accepted. This correction resolves a pre-existing mismatch between this ADR's own formal status and its actual downstream reliance: `ADR-002-Critical-UX-Architecture-Resolutions.md`, `ADR-003-Recommendation-Identity-and-Terminology-Resolution.md`, and `ADR-004-Scenario-Analysis-Comparison-and-Sequence-Authority-Resolution.md` — and, subsequently, `UX-000-Atlas-UX-Doctrine.md` itself — already relied on this ADR's own governance rules as binding before this ratification occurred. The substantive decision recorded below is unchanged by this ratification; no Decision Driver, Considered Option, Decision, Governance Rule, Consequence, Future Work item, Applicability statement, or Open Question is altered. This ratification does not retroactively fabricate authority for any period before this date, and does not erase or rewrite the fact that this ADR carried Proposed status from its own original adoption (per the Working Tree Verification below) until this correction — that historical period remains part of the record, exactly as this ADR's own Governance Rules already require of every other document's history. This ADR remains bounded to documentary-source and missing-source governance, per its own Applicability section, unchanged; ratification does not broaden its scope. This ADR does not, by virtue of this ratification, obtain any authority to amend `UX-000-Atlas-UX-Doctrine.md` through the ordinary ADR mechanism — any future amendment to that Doctrine remains governed exclusively by its own `UXD-R-007` and `UXD-R-110`, unaffected by this or any other ADR's own status.

## Context

Atlas's UX documentation is organized as a layered set of governing documents: product/experience philosophy (UX-000, UX-004, UX-008), screen and wireframe specification (UX-005, UX-007A, UX-009, UX-009A), interaction and visual design (UX-010, UX-011, UX-007P), and a cross-Workspace design system and component library (UX-012 and its four superseded parts UX-012A–D; UX-013A, UX-013B, and UX-013E). This layering, and the practice of periodically "assembling" a set of parallel sub-volumes into one reconciling document that supersedes them (UX-012A–D → UX-012; the intended UX-013A–D → UX-013E), is an established and generally sound pattern within this documentation series.

An independent architecture review (`UX-Architecture-Review-001.md`) discovered that UX-013E — the document intended to assemble and supersede UX-013A, UX-013B, UX-013C, and UX-013D — cites UX-013C ("Decision & Monitoring Components") and UX-013D ("AI Collaboration, Metadata & System Components") as governing source volumes, attributing to them specific, granular claims: exact component counts, exact lifecycle-variant counts, exact prop and API names, and exact naming/merge decisions. Neither UX-013C nor UX-013D exists anywhere in the committed repository. A separate document in the same series, UX-013B, states in its own words, written before UX-013E existed, "Do not produce UX-013C yet. The completed UX-013B is the prerequisite" — establishing that UX-013C did not exist at the time UX-013B was written. Whether it was later written and never captured, or never written at all, cannot be determined from anything in this repository. A subsequent independent governance analysis evaluated six candidate responses to this discovery (Options A–F) and concluded that one model — referred to there as "Option F" — is the strongest available response.

**Why this is a governance problem, not simply a documentation problem.** A documentation problem has a documentation fix: correct the wording, fill the gap, move on. This is not that. The gap here is a break in the chain of *evidence* a governing document rests on — UX-013E asserts specific facts about component design that only its own, unverifiable account currently supports. A wording fix cannot repair a break in evidence; only a rule about how evidence gaps of this kind are handled, applied consistently and durably, can. That rule is a governance decision, and it has consequences far beyond this one pair of missing documents: any future "assembly" document in this series (a future UX-014, a future Portfolio Workspace design-system revision, a future entirely new Workspace's own component library) can develop the identical failure mode — an assembler citing a source volume that was never actually finished or never actually captured. Without a standing rule, each future occurrence would be resolved ad hoc, inconsistently, by whoever happens to notice it.

**Why historical truthfulness is more important than apparent completeness.** Atlas's own product philosophy states, repeatedly and without qualification, that the product's own historical record must never be rewritten, that uncertainty must be disclosed rather than concealed, and that the product must never "manufacture false confidence to appear more useful" (UX-000). A documentation practice that fabricates a missing source, or quietly erases the sign that one is missing, applies the opposite standard to the documentation than the product's own philosophy requires of the product's data. A component library that looks complete because its gaps were papered over is worse than one that visibly, honestly, is not yet complete — the first can only be discovered to be false at a cost (every other claim in the corpus becomes suspect once one is found fabricated); the second costs nothing but the honest inconvenience of saying "not yet."

## Decision Drivers

- **Documentary truthfulness** — every claim a governing document makes must be either independently verifiable or explicitly disclosed as not yet verifiable; no document may assert more certainty than the evidence supports.
- **Provenance** — every fact in a governing document must be traceable to where it actually came from, not to where a later document merely claims it came from.
- **Auditability** — a future reviewer must be able to check any claim in bounded time, without needing to trust the document making the claim.
- **Implementation safety** — no team should build a safety-critical product surface against a specification whose grounding cannot be checked.
- **Long-term maintainability** — the governance response must not create a permanent, unowned, indefinitely-deferred obligation; it must include its own path to closure.
- **Contributor trust** — a new contributor's confidence in the documentation set as a whole depends on every document in it being what it claims to be.
- **Historical integrity** — the documentation must hold itself to the same non-fabrication, non-erasure standard the product itself is required to hold its own data to.
- **Explicit governance** — the rule adopted here must be stated once, generally, and applied by future authors without requiring this specific incident to be re-litigated each time it recurs.

## Considered Options

- **Option A — Reconstruct UX-013C/UX-013D as if they were historical source volumes, derived from UX-013E.** Core idea: back-fill the missing citations' targets. Primary strength: fastest apparent closure. Primary weakness: the reconstructed documents would be authored entirely from, and after, the very document that claims descent from them — a closed loop containing no independent content, i.e., fabricated provenance. **Rejected** — direct violation of the non-fabrication driver; the single most severe option evaluated.

- **Option B — Author completely new, honestly-dated canonical UX-013C and UX-013D.** Core idea: do the real specification work that was never done, dated truthfully as new. Primary strength: the only option that actually closes the underlying gap, not merely its symptom. Primary weakness: substantial, unavoidable authorship cost, and by itself does not describe what governs the documentation in the meantime. **Accepted as necessary future work, not as a sufficient governance model on its own** — it is the eventual completion this ADR's decision points toward, not a standalone answer to how the interim state should be governed.

- **Option C — Accept UX-013E as independently canonical and remove its unverifiable provenance claims.** Core idea: stop citing what can't be checked. Primary strength: cheapest possible edit. Primary weakness: removes the disclosure of the gap without closing the gap itself, and silently converts UX-013E's own declared genre (an assembly of four source volumes) into something it never disclosed being (partial original author) — resolving an audit finding by deleting the evidence of it. **Rejected** — fails the auditability and contributor-trust drivers by design.

- **Option D — Tag unsupported sections "Draft — Provenance Unconfirmed" in place.** Core idea: honest, inline disclosure. Primary strength: truthful, cheap, non-fabricating. Primary weakness: an inline tag inside a document of several thousand lines has no owner and no trigger to ever resolve it, and risks becoming a permanent, unenforced caveat over exactly the tier (Decision components) where that would matter most. **Rejected as insufficient on its own** — sound in substance, fragile in durability.

- **Option E — Physically split the document along its trust boundary into separately governed volumes.** Core idea: make the boundary structural, not merely textual. Primary strength: far harder to overlook than an inline tag; mirrors this series' own established practice of splitting along governance boundaries (as UX-012 was split into UX-012A–D). Primary weakness: treats all unconfirmed content as equally unconfirmed, when some of it is in fact independently corroborated at the broad-concept level by other committed documents. **Superseded by Option F, which retains E's structural split and adds finer-grained honesty.**

- **Option F — Structural split (per E) plus a three-tier corroboration classification (independently confirmed / unconfirmed / to-be-authored) plus an explicit, named commissioning trigger for the eventual replacement work.** Core idea: disclose exactly what is known, at exactly the resolution the evidence supports, with a scheduled path to closure rather than an open-ended caveat. Primary strength: the only option that achieves full truthfulness, full auditability, and a durable (not indefinitely-deferred) resolution path simultaneously. Primary weakness: requires more upfront classification work than D or C, though most of that work was already performed by the preceding architecture review and governance analysis. **Accepted.**

## Decision

**The governance model corresponding to Option F is formally adopted as a permanent governance principle of Atlas's documentation practice — not as a one-time workaround for UX-013C and UX-013D, and not limited to the UX-013 series.**

Specifically, and permanently, going forward:

- **No fabricated historical source document is ever created.** A document must never be authored in a way that presents it as having existed, or having been consulted, prior to a point in time when it did not actually exist.
- **No provenance claim is ever silently removed to resolve an audit finding.** If a claim's source cannot be verified, the correct response is to disclose that fact precisely, never to delete the disclosure.
- **Unsupported claims remain explicitly identified as unsupported**, for as long as they remain unsupported — not merged indistinguishably into the surrounding, well-supported material.
- **Partially corroborated claims are distinguished from wholly unsupported claims.** Where a broad concept is independently attested elsewhere (even if a specific detail is not), that distinction is preserved and stated, rather than collapsed into one blanket status.
- **Genuine new source specifications, when written, are always honestly authored** — dated to when they are actually produced, citing only governing documents that actually exist, and never claiming retroactive authorship.
- **Provenance gaps are closed through new, honest authorship — never through reconstructed history.** The only legitimate way to make an unsupported claim supported is to do the work that supports it, not to manufacture a source that appears to.

## Governance Rules

The following rules apply to every Atlas document going forward — this UX series, the Design System documentation, the Architecture documentation, and any future documentation this project produces — not only to UX-013E, UX-013C, or UX-013D:

1. **Missing source documents are never fabricated.** If a document cites a source that does not exist in the repository, the correct remedy is disclosure or genuine authorship — never retroactive construction of a document designed to satisfy the citation.
2. **Provenance is never inferred.** A claim's origin is either directly traceable to an existing document, or it is stated as untraceable. It is never assumed, guessed, or reconstructed from context, prompts, or general expectation.
3. **Historical claims require historical evidence.** A statement about what a prior document "established" or "decided" must be checkable against that document's own actual text. If the document is absent, the claim is not historical fact — it is, at most, a present-day assertion requiring its own present-day justification.
4. **Assemblies may only claim sources that actually exist.** A document that presents itself as an assembly, reconciliation, or supersession of prior volumes may only name, as governing inputs, volumes actually present and checkable in the repository at the time the assembly is written.
5. **Interim documents must disclose their own confidence level.** Where a governance gap cannot be closed immediately, the interim document covering it must state, per claim or per section, how well-supported that specific content currently is — not one uniform status for content of genuinely different evidentiary weight.
6. **Unsupported implementation details cannot silently become canonical.** A detail that exists only inside an unverifiable secondhand account does not acquire canonical authority merely by appearing in a document that is otherwise largely canonical. Canonical status is earned per claim, by evidence, not inherited automatically from a document's overall status.
7. **New canonical documents must preserve documentary honesty as a precondition of adoption.** A document is not eligible to be treated as canonical, however complete or well-written, if adopting it requires accepting an unverifiable or fabricated claim about its own provenance.

## Consequences

**Positive consequences:**
- Every future contributor can trust that no document in this series claims a history it does not have.
- Audit findings of this kind (an assembler citing an absent source) become mechanically resolvable under a standing rule, rather than requiring a fresh governance debate each time they recur.
- The documentation set holds itself to the same immutable, non-fabricated historical-integrity standard the product's own data model already requires — removing what would otherwise be a visible inconsistency between what Atlas promises its users and what its own architecture documents practice.
- Partially-corroborated content becomes usable, correctly labeled, rather than being blocked alongside genuinely unsupported content — this is more useful, not merely more cautious, than a single blanket "unconfirmed" status.

**Negative consequences:**
- Closing a provenance gap now costs more, upfront, than papering over it would — the honest path (new authorship, or a disclosed, unresolved gap) is never the cheapest available option in the moment.
- Some governing documents will visibly, permanently (until genuinely resolved) carry a lower-confidence or split-out status, which is less tidy in appearance than a document set with no visible seams.
- This rule creates ongoing classification work whenever an assembly document is produced — a discipline cost paid on every future assembly, not just this one.

**Accepted trade-offs:**
- This ADR knowingly accepts short-term inconvenience (real authorship labor, visible disclosure of gaps, ongoing classification effort) in exchange for long-term trust and auditability, which this ADR treats as the more valuable and harder-to-recover property of the two.
- This ADR knowingly accepts that some component tiers (Decision, Monitoring, AI Collaboration, Metadata & System) remain correctly blocked from full implementation until genuinely authored, rather than resolving that block by lowering the evidentiary bar.

## Future Work

- **This ADR does not itself change UX-013E.** No section of UX-013E is split, edited, retitled, or reclassified by this document. That is separately-scoped implementation work, to be carried out only once explicitly authorized as its own task.
- **This ADR does not authorize rewriting history.** No existing document's stated timeline, authorship, or sequence of events is altered by this decision. Any future correction must add a dated, disclosed amendment — it may never silently rewrite what a document previously said about itself.
- **This ADR requires a future governance migration** to actually apply the model adopted here to UX-013E specifically: the structural split and three-tier classification described under Option F above, performed as its own, separately-authorized task.
- **Genuine UX-013C and UX-013D may later be authored** — as new, honestly-dated canonical specifications, citing only documents that exist at the time of their writing, following the same process UX-013A and UX-013B themselves used. They are not reconstructed, not silently substituted, and not backdated.
- **Any future revision of UX-013E, once the migration above occurs, must comply with this ADR** — it may cite as governing sources only documents that exist and are checkable at the time it is written.

## Applicability

This ADR applies to:
- Atlas UX documentation (the full `docs/atlas_ux/` series, present and future);
- Design System documentation (UX-012 and its successors);
- Architecture documentation more broadly, wherever a document claims to assemble, reconcile, or supersede other governing documents;
- any future Atlas documentation, in any track, where an assembled or reconciling document references governing sources — this rule is general to the practice of assembly, not specific to the UX-013 series.

## Supersession

This ADR does not supersede any previous ADR. No prior ADR of this kind exists in the Atlas UX documentation series. This ADR establishes a new governance rule where none previously existed.

## Open Questions

- **What mechanism (automated check, manual review checklist, or editorial convention) will verify, going forward, that a new assembly document cites only sources that actually exist in the repository at the time it is written?** This ADR establishes the rule; it does not specify its enforcement mechanism, which is a separate, not-yet-scoped process decision.
- **Who owns the commissioning trigger for the future UX-013C/UX-013D authorship work**, and on what timeline? This ADR establishes that the work must eventually happen and must be honestly authored when it does; it does not assign ownership or a deadline, both of which require a decision this ADR is not positioned to make on its own.
- **Does this same provenance gap exist anywhere else in the Atlas documentation corpus, beyond the one instance this ADR was written in response to?** This ADR was not the product of a corpus-wide search for other instances of the same failure mode; whether one is needed is a separate, unresolved question.

## Working Tree Verification

**Branch:** main
**HEAD:** `f2d5adbb7cd260853f56197e35fcc776caf85a78` — unchanged.
**Files created:** `docs/atlas_ux/governance/ADR-001-Missing-Source-Volume-Governance.md` (this document), and the directory `docs/atlas_ux/governance/`, which did not previously exist.
**Files modified:** none. No UX source document under `docs/atlas_ux/*.md` was changed. No review document under `docs/atlas_ux/reviews/` was changed.
**Staged files:** none.
**Untracked paths:** `docs/atlas_ux/governance/` (new) and `docs/atlas_ux/reviews/` (pre-existing, unchanged).

No commit was made.

## Working Tree Verification (Ratification)

**Branch:** main
**HEAD at time of this ratification:** `91d71fef21dba401d6e9f11195c5a030cb485a23` — unchanged throughout this task.
**Files modified:** `docs/atlas_ux/governance/ADR-001-Missing-Source-Volume-Governance.md` (this document — Status header and this Ratification Note added; all other content unchanged).
**Files created:** none.
**Staged files:** none.

No commit was made.
