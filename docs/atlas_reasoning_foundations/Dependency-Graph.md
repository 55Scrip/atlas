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
Judgment        [Draft — ADR-002]
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

- **Final:** Reasoning (ADR-001).
- **Draft:** Judgment (ADR-002).
- **Planned:** every other node above — no ADR yet exists for any of them; their position in this chain is provisional, not an ontological commitment.

# Primitive Status Table

Where an ADR does not state a fact explicitly, this table records "Unknown" or "Not yet defined" rather than supplying one.

| Primitive | Status | ADR | Depends On | Open Dependencies | Produces |
|---|---|---|---|---|---|
| Reality | Planned | Not yet written | None (root of current chain) | Not yet defined | Observation (per current chain; not established by any ADR) |
| Observation | Planned | Not yet written | Reality (per current chain) | Not yet defined | Evidence (per current chain; not established by any ADR) |
| Evidence | Planned | Not yet written | Observation (per current chain) | Not yet defined | Reasoning (per current chain) — see Open Questions on the relationship between "Evidence" here and "Knowledge" in ADR-001 |
| Reasoning | Final | ADR-001 | Knowledge (per ADR-001) | None currently open in ADR-001 | Judgment (per ADR-001: "a completed Reasoning Act produces an explicit Judgment") |
| Judgment | Draft | ADR-002 | Reasoning (per ADR-001 and ADR-002) | Candidate, Confidence, Agent (per ADR-002) | Confidence — see Open Questions on "produces" versus ADR-002's own "updates" framing |
| Confidence | Planned | Not yet written | Judgment (per current chain) | Not yet defined | Conviction (per current chain; not established by any ADR) |
| Conviction | Planned | Not yet written | Confidence (per current chain) | Not yet defined | Decision (per current chain; not established by any ADR) |
| Decision | Planned | Not yet written | Conviction (per current chain) | Not yet defined | Action (per current chain; not established by any ADR) |
| Action | Planned | Not yet written | Decision (per current chain) | Not yet defined | Outcome (per current chain; not established by any ADR) |
| Outcome | Planned | Not yet written | Action (per current chain) | Not yet defined | Learning (per current chain; not established by any ADR) |
| Learning | Planned | Not yet written | Outcome (per current chain) | Not yet defined | None (terminal node of current chain) |

# Open Questions

Collected from existing ADRs and from directly comparing this chain against them. None are answered here.

- ADR-002's own open dependencies: what is a *Candidate* ("candidates generated through reasoning")? What is *Confidence*? What or who is the *Agent* that updates confidence? None have an ADR.
- *Candidate* and *Agent*, both named as open dependencies in ADR-002, do not currently appear anywhere in the chain above. Whether they belong elsewhere in this graph, are subsumed by an existing node, or require a node of their own is not decided here.
- ADR-001 states that Reasoning operates over established **Knowledge**. This chain instead places **Evidence** immediately prior to Reasoning. Whether Evidence and Knowledge name the same concept, or Evidence is a distinct, not-yet-defined primitive with its own relationship to Knowledge, is unresolved.
- ADR-002's working definition describes Judgment as the process by which confidence is *updated* — implying an existing confidence state acted upon — while this chain places Confidence as a node Judgment simply *produces*. Whether these are compatible framings of the same relationship, or a genuine tension, is unresolved.
- ADR-002 itself already records an open contradiction (whether Judgment is a process or an object) and is not Final. Every downstream node in this chain that would depend on Judgment inherits that same unresolved status.

# Maintenance Rules

- This document is updated only to reflect facts already established elsewhere — a primitive's status changes here only after the corresponding ADR's own status has actually changed (Draft → Final, or a new ADR is written for a previously Planned node).
- Where this document and an ADR disagree, the ADR is authoritative. The disagreement is recorded under Open Questions, not silently corrected here — resolving it is the ADR's job, not this document's.
- New primitives are added to the graph only when they are named as such in an existing ADR or in a direct instruction establishing the current chain — never invented here to fill a perceived gap.
- This document must never be cited as the basis for an architectural or implementation decision. [Doctrine.md](Doctrine.md) and the individual ADRs remain the sole authoritative sources; this document is a map of them, not a replacement for reading them.
