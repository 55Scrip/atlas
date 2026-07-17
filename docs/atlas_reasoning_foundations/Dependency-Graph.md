**Atlas Reasoning Foundations — Dependency Graph.** Purely descriptive and navigational. It does not define ontology, does not settle architecture, and is never itself the source of truth — [Doctrine.md](Doctrine.md) and the individual ADRs are.

# Purpose

As the number of Atlas Reasoning Foundations primitives grows, no single ADR gives a reader a view of how they all relate to one another — each ADR argues its own primitive from first principles, with only its own immediate dependencies stated explicitly (per the Doctrine's Explicit Dependency Graph principle). This document exists to collect those individually-stated dependencies into one place, so the current shape of the whole structure — what is settled, what is in progress, and what is merely anticipated — can be seen at a glance. It restates status and dependency facts already established elsewhere; it establishes none of its own.

# Current Cognitive Dependency Graph

```
Reality        [Planned]
   ↓
Observation     [Planned]
   ↓
Evidence        [Planned]
   ↓
Reasoning       [Final — ADR-001]
   ↓
Judgment        [Final — ADR-002]
   ↓
Confidence      [Planned]
   ↓
Conviction      [Planned]
   ↓
Decision        [Planned]
   ↓
Action          [Planned]
   ↓
Outcome         [Planned]
   ↓
Learning        [Planned]
```

- **Final:** Reasoning (ADR-001); Judgment (ADR-002).
- **Draft:** none currently.
- **Planned:** every other node above — no ADR yet exists for any of them; their position in this chain is provisional, not an ontological commitment.

# Primitive Status Table

Where an ADR does not state a fact explicitly, this table records "Unknown" or "Not yet defined" rather than supplying one.

| Primitive | Status | ADR | Depends On | Open Dependencies | Produces |
|---|---|---|---|---|---|
| Reality | Planned | Not yet written | None (root of current chain) | Not yet defined | Observation (per current chain; not established by any ADR) |
| Observation | Planned | Not yet written | Reality (per current chain) | Not yet defined | Evidence (per current chain; not established by any ADR) |
| Evidence | Planned | Not yet written | Observation (per current chain) | Not yet defined | Reasoning (per current chain) — see Open Questions on the relationship between "Evidence" here and "Knowledge" in ADR-001 |
| Reasoning | Final | ADR-001 | Knowledge (per ADR-001) | None currently open in ADR-001 | Judgment (per ADR-001: "a completed Reasoning Act produces an explicit Judgment") |
| Judgment | Final | ADR-002 | Reasoning / Reasoning Act (per ADR-001, as used by ADR-002's Current Best Definition, Identity Criterion, and Equivalence Criterion) | None self-owned — Candidate, Confidence, and Agent were removed from ADR-002 as historical residue of a rejected candidate (ADR-002 Revision 2); they are not dependencies of the settled ontology. Knowledge's own identity criterion is an external dependency ADR-002 references but does not own (ADR-002 Revision 4); it remains unresolved and does not block Judgment's Final status | None established or implied by ADR-001 or ADR-002. This chain's own Judgment→Confidence adjacency is an unresolved chain assumption only, not a production relation ADR-002 asserts |
| Confidence | Planned | Not yet written | Judgment (per current chain) | Not yet defined | Conviction (per current chain; not established by any ADR) |
| Conviction | Planned | Not yet written | Confidence (per current chain) | Not yet defined | Decision (per current chain; not established by any ADR) |
| Decision | Planned | Not yet written | Conviction (per current chain) | Not yet defined | Action (per current chain; not established by any ADR) |
| Action | Planned | Not yet written | Decision (per current chain) | Not yet defined | Outcome (per current chain; not established by any ADR) |
| Outcome | Planned | Not yet written | Action (per current chain) | Not yet defined | Learning (per current chain; not established by any ADR) |
| Learning | Planned | Not yet written | Outcome (per current chain) | Not yet defined | None (terminal node of current chain) |

# Open Questions

Collected from existing ADRs and from directly comparing this chain against them. None are answered here.

- ADR-001 states that Reasoning operates over established **Knowledge**. This chain instead places **Evidence** immediately prior to Reasoning. Whether Evidence and Knowledge name the same concept, or Evidence is a distinct, not-yet-defined primitive with its own relationship to Knowledge, is unresolved.
- This chain places Confidence immediately after Judgment. Neither ADR-001 nor ADR-002 establishes or implies any such production relation — Judgment → Confidence is, at most, an unresolved adjacency assumed by this chain's own illustrative ordering, not a relation ADR-002 owns (ADR-002 Revision 2).
- ADR-002's process/object contradiction is resolved (Resolution Session 1); Judgment is an ontological object, with an explicit numerical-identity and equivalence criterion (Resolution Session 2). Candidate, Confidence, and Agent, previously listed here as open dependencies, have been removed entirely as historical residue of a rejected candidate (ADR-002 Revision 2) — they are no longer part of ADR-002's dependency graph. The antecedent-uncertainty question is also resolved (Resolution Session 3, ADR-002 Revision 3): uncertainty is not a precondition of Judgment. The minimal criterion for identical Judgment content is also resolved (Resolution Session 4, ADR-002 Revision 4). ADR-002 is now Final: it has no remaining open question of its own. The one respect in which it relies on unsettled material — Knowledge's own identity criterion — remains genuinely unresolved and is recorded as an explicit external dependency on a future, not-yet-written Knowledge ADR, not as an open question or blocker of ADR-002's Final status. Every downstream node in this chain that would depend on Judgment inherits this posture: a stable, Final Judgment ontology, plus one explicitly named, unresolved, non-blocking external dependency.

# Maintenance Rules

- This document is updated only to reflect facts already established elsewhere — a primitive's status changes here only after the corresponding ADR's own status has actually changed (Draft → Final, or a new ADR is written for a previously Planned node).
- Where this document and an ADR disagree, the ADR is authoritative. The disagreement is recorded under Open Questions, not silently corrected here — resolving it is the ADR's job, not this document's.
- New primitives are added to the graph only when they are named as such in an existing ADR or in a direct instruction establishing the current chain — never invented here to fill a perceived gap.
- This document must never be cited as the basis for an architectural or implementation decision. [Doctrine.md](Doctrine.md) and the individual ADRs remain the sole authoritative sources; this document is a map of them, not a replacement for reading them.
