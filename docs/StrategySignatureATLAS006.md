# ATLAS-006 — Strategy Signature Recognition

**Status:** Implemented, pending review.
**Scope:** The first capability that looks *across* Patterns — a coherent characterization of an investor's decision-making process, built from two or more of their own recognized Patterns, in the sense fixed by ATLAS-006-D. Read-only throughout. Introduces no new domain aggregate, no new persistence, no new writes.
**Depends on:** ATLAS-006-D's authoritative Strategy Signature definition, and the existing, unmodified `PatternRecognitionQuery` (ATLAS-005/005B).

---

## 1. Purpose

ATLAS-006-D fixed a strict distinction, mirroring Pattern's own: a
**Strategy Signature** is a coherence among an investor's Patterns that
exists whether or not Atlas has found it; **Strategy Signature
Recognition** is the separate act that discovers it. This increment
builds the smallest capability that performs that act, formalized as
graph connectivity: **two Patterns are adjacent when they share at
least one Decision id, and a Strategy Signature is the maximal
connected set induced by that adjacency relation.**

An earlier attempt (documented in ATLAS-006's feasibility assessment)
found that "all currently recognized Patterns, taken together" was not
valid coherence, and that the one genuine rule available — Patterns
sharing a Decision — could never fire with only one Pattern strategy in
place, because `SameSubjectAndTypeStrategy` is a strict partition and
cannot overlap with itself. ATLAS-005B added `SameConfidenceStrategy`
specifically to make genuine overlap possible; this increment is what
that unblocked.

## 2. Recognition Model

```python
@dataclass(frozen=True)
class RecognizedStrategySignature:
    strategy_name: str
    member_patterns: tuple[RecognizedPattern, ...]
    description: str
    recognized_at: datetime
```

- **`member_patterns`** — the actual `RecognizedPattern` objects forming
  one connected component. This is the artifact's **structural
  identity**.
- **`strategy_name`** — records *how* the Signature was discovered.
  Recognition metadata, not identity.
- **`recognized_at`** — when the recognition act happened. Also
  metadata, not identity.
- **`description`** — presentation only, generated *after* group
  membership is already finalized, by concatenating the member
  Patterns' own descriptions. Performs no semantic synthesis and is
  never used as input to determine membership, identity, or coherence.

## 3. Invariants

1. **A `RecognizedStrategySignature` represents one maximal connected
   component in the Pattern-overlap graph.** No two
   `RecognizedStrategySignature`s produced by the same recognition pass
   may share a Pattern — a direct, tested consequence of connected
   components partitioning the node set.
2. **Structural identity is determined only by the ordered set of
   member Patterns.** `strategy_name` and `recognized_at` describe how
   and when a Signature was found, not which Signature it is. Two
   recognition strategies that independently discover the same member
   Patterns are recognizing the same underlying Strategy Signature.
3. **`description` performs no semantic synthesis and carries no
   authority over membership, identity, or coherence.**

## 4. Adjacency and Connectivity Rule

The domain-level rule, stated purely relationally:

- **Two Patterns are adjacent** when
  `set(A.member_decision_ids) & set(B.member_decision_ids)` is
  non-empty. Pure set-intersection over already-structured `DecisionId`
  values — no description parsing, no Decision lookup, no heuristic.
- **A Strategy Signature is the maximal connected set induced by that
  adjacency relation** — every Pattern reachable from another through a
  chain of shared-Decision edges belongs to the same Signature.

How this maximal connected set is computed (BFS, DFS, or Union-Find) is
an implementation detail, not part of the domain rule (§9).

## 5. Folder Structure

```
atlas/core/application/strategy_signature/
    recognized_strategy_signature.py   # RecognizedStrategySignature
    strategies.py                        # StrategySignatureRecognitionStrategy protocol + ConnectedPatternsStrategy
    query.py                               # StrategySignatureRecognitionQuery
    composition.py                           # build_strategy_signature_recognition_query(engine)
    cli.py                                      # standalone entry point

tests/unit/application/strategy_signature/test_query.py
```

No new domain aggregate, no new persistence table, no new repository
method, no new REST endpoint, no modification to Pattern, Pattern
Recognition, Decision Timeline, Decision Review, or Core Loop.

## 6. Deterministic Ordering

Two independent ordering rules, both derived purely from each
`RecognizedPattern`'s own already-structured fields — never from
`recognized_at` (a per-strategy-run artifact) and never from whichever
order a traversal algorithm happens to visit nodes in:

- **Pattern sort key**: `(strategy_name, tuple(d.value for d in member_decision_ids))`
  — `DecisionId.value` is a `uuid.UUID`, directly orderable.
- **Patterns within one `RecognizedStrategySignature`**: sorted
  ascending by the pattern sort key.
- **`RecognizedStrategySignature`s relative to each other**: sorted
  ascending by the minimum pattern sort key among each component's
  members.

## 7. Traceability

`RecognizedStrategySignature.member_patterns` names the specific
Patterns in the component; each, in turn, already names its own
`member_decision_ids`. Walking `Signature → member_patterns →
member_decision_ids` reconstructs every Decision behind the Signature.

Because a connected component may be a **chain**, not a clique, two
member Patterns may be connected only transitively, through a third.
Full explainability of *why* two Patterns ended up in the same
Signature remains reconstructable on demand by re-running the same
set-intersection check between any two members — no new stored field
is needed.

## 8. Handling of Isolated Patterns

A `RecognizedPattern` with no edge to any other currently-recognized
Pattern forms its own connected component of size one. Per invariant 1,
a size-one component produces **no** `RecognizedStrategySignature` —
not an error, the correct and expected outcome whenever a Pattern
happens not to share a Decision with any other.

## 9. Why Connected Components, Not Pairwise Composition or Cliques

- **Pairwise composition** (each overlapping pair its own Signature) —
  rejected: fragments one coherent story and cannot represent a chain.
  If A–B share a Decision and B–C share a different one, but A–C share
  nothing, pairwise composition produces two disconnected Signatures,
  hiding that all three are connected through B.
- **Complete cliques** (every pair must mutually overlap) — rejected:
  strictly stronger than the domain requires. A documented chain of
  real evidence is exactly as explainable as full pairwise overlap;
  requiring a clique would silently exclude real, transitively-connected
  groups and tie correctness to NP-hard clique detection for no
  domain benefit.
- **Connected components** capture every Pattern transitively linked by
  genuine shared-Decision evidence as one coherent structure, with
  every edge still carrying real, named evidence.

**Traversal algorithm**: BFS (`collections.deque`, stdlib only),
recommended for readability given the expected small number of
currently-recognized Patterns; Union-Find is an equally valid
alternative if performance ever requires it.

## 10. Read Boundary

- Never calls `.add(...)` on anything — this module never imports any
  repository type at all.
- No Decision lookup — the only input type is `RecognizedPattern`.
- Never evaluates the investor: descriptions state connectivity in
  neutral terms only.
- No persisted `RecognizedStrategySignature` history across runs — an
  explicit, disclosed simplification, consistent with ATLAS-004/005/005B.

## 11. Components

- **`RecognizedStrategySignature`** — frozen dataclass (§2).
- **`StrategySignatureRecognitionStrategy`** (`Protocol`):
  `recognize(recognized_patterns: tuple[RecognizedPattern, ...]) -> tuple[RecognizedStrategySignature, ...]`.
- **`ConnectedPatternsStrategy`** — the one concrete strategy shipped,
  implementing §4/§9.
- **`StrategySignatureRecognitionQuery`** — constructor takes a
  `PatternRecognitionQuery` and a sequence of strategies; `build()`
  assembles the Patterns once, then runs every strategy over them.
- **`build_strategy_signature_recognition_query(engine)`** — the only
  place aware of an `Engine`; reuses `build_pattern_recognition_query(engine)`
  (ATLAS-005/005B) unmodified.
- **`cli.py`** — standalone entry point, same independence discipline
  as the existing CLIs.

## 12. Sequence

```
Person       CLI      StrategySignatureRecognitionQuery   PatternRecognitionQuery
  |--run---->| build() |                                  |
  |          |-------->| build()                          |
  |          |         |--------------------------------->| build() (ATLAS-005/005B, read-only)
  |          |         |<--RecognizedPatterns--------------|
  |          |         | build adjacency, find components |
  |<--RecognizedStrategySignatures, ordered, with member Patterns------|
```

## 13. Test Summary

15 new tests in `tests/unit/application/strategy_signature/test_query.py`,
regression-clean against the existing suite:

- **`TestIsolatedPatterns`** — no Patterns, a single Pattern, and two
  non-overlapping Patterns all yield no Signature.
- **`TestConnectedComponent`** — two overlapping Patterns yield one
  Signature; **a three-Pattern chain** (A–B share a Decision, B–C share
  a different Decision, A–C share nothing directly) is recognized as
  one Signature — the concrete proof that connectivity, not pairwise or
  clique logic, was implemented; two separate components yield two
  separate Signatures.
- **`TestPartitionProperty`** — no Pattern appears in more than one
  Signature from the same recognition pass (invariant 1).
- **`TestIdentityMetadataSeparation`** — two constructed Signatures with
  identical `member_patterns` but different `strategy_name`/
  `recognized_at` are the same underlying Signature by `member_patterns`
  comparison, documenting that metadata is not identity (invariant 2).
- **`TestDeterministicOrdering`** — member Patterns are sorted by the
  defined key, not discovery order; repeated recognition of the same
  input yields the same output order.
- **`TestDescriptionPlaysNoRoleInMembership`** — overlapping Decision
  ids group together despite unrelated descriptions; disjoint Decision
  ids never group despite similar descriptions (invariant 3).
- **`TestTraceability`** — every Decision id is reachable by walking
  `member_patterns`.
- **`TestEndToEndWithRealStrategies`** — the same three-Pattern chain,
  built from four real Decisions and the two real Pattern Recognition
  strategies (`SameSubjectAndTypeStrategy`, `SameConfidenceStrategy`),
  proving the capability is non-vacuous today, not just with test
  doubles.
- **`TestNeverWritesEndToEnd`** — a runtime spy (`RaisingOnAdd`) wrapping
  every repository beneath the full `DecisionTimelineQuery` →
  `PatternRecognitionQuery` → `StrategySignatureRecognitionQuery` chain
  raises `AssertionError` if `.add()` is called; `build()` completes
  without raising.
- **Manual verification:** four First Decision Conversation CLI runs
  sharing one `ATLAS_HOME` (NVIDIA/BUY/90, NVIDIA/BUY/70, AMD/SELL/90,
  AMD/SELL/60), followed by the Pattern Recognition and Strategy
  Signature Recognition CLIs — correctly surfaced three real Patterns
  connected through two shared Decisions, assembled into one Strategy
  Signature.

**Regression:** full repository suite: **7,588 passed, 3 skipped**
(7,573 pre-existing + 15 new). Scoped lint: clean. Whole-repo `ruff
check .` count unchanged at 1,202. `git diff --stat` confirms the
change set is purely additive — zero existing file touched.

## 14. Architectural Decisions

1. **Graph connectivity (adjacency + maximal connected components)**,
   not "all Patterns together" or pairwise composition or complete
   cliques — the only rule that is both genuine coherence and provably
   non-vacuous (§9).
2. **`RecognizedStrategySignature`, not `StrategySignature`** — avoids
   conflating the discovered artifact with the domain fact whose
   existence is independent of recognition (ATLAS-006-D invariant 10).
3. **Structural identity is `member_patterns` alone**, with
   `strategy_name`/`recognized_at` demoted to metadata — required by
   ATLAS-006-D's own distinction between a Signature and its Recognition.
4. **`description` is strictly post-hoc presentation** — assembled only
   after membership is finalized, never used to decide it.
5. **No stored edge list** — connectivity evidence is recomputable on
   demand from `member_patterns`, keeping the artifact minimal.
6. **No persistence, ephemeral recomputation every run** — consistent
   with ATLAS-004/005/005B precedent.

## 15. Anything That Feels Overengineered

Nothing beyond what the graph-connectivity domain rule required. BFS
was chosen over Union-Find purely for readability; no registry,
ranking, or merging logic was added ahead of a second strategy needing
it.

## 16. What Can Be Simplified

Nothing at this stage. The most likely future growth points (a second
Strategy Signature Recognition strategy, persistence of recognition
runs, an inverted index for adjacency at scale) are deliberately
deferred rather than half-built now.

## 17. Genuine Risks / Unresolved Questions

- **`O(n²)` pairwise overlap comparison** will not scale indefinitely as
  the number of currently-recognized Patterns grows — acceptable at
  today's scale; an inverted index (Decision id → Patterns referencing
  it) could reduce this if it becomes a bottleneck.
- **A single very large connected component** could form once many
  Pattern strategies exist and Decisions are highly interlinked,
  producing one sprawling, hard-to-read Signature — a disclosed
  consequence of choosing maximal connectivity over a stricter but
  domain-invalid alternative.
- **Still entirely dependent on real overlap occurring** in an
  investor's data — demonstrated non-vacuous by this increment's own
  manual walkthrough, but any given dataset may still produce zero
  Signatures.
- **No authentication** — same placeholder-identity gap disclosed in
  every prior increment.

## 18. Future Backlog

- A second Strategy Signature Recognition strategy, once a genuine need
  for one is identified — the protocol was designed for exactly this.
- An inverted index for adjacency computation if the Pattern count grows
  large enough for `O(n²)` comparison to matter.
- Persisting each recognition run as its own dated record, if usage
  shows comparing Signatures over time is needed.
- Carried forward, unaffected by this increment: additional Pattern
  Recognition strategies (repeated reasoning language, review-completion
  recurrence, learning-recurrence), re-evaluating `reasoning_link`'s
  placement and permanence, a REST API layer for the Core Loop, the
  shared structured Error Contract, the brittle hard-coded test-count
  assertion in `README.md`/`tests/test_release_candidate.py`.
- **Recommendation for the next sprint:** with Strategy Signature
  Recognition now in place, the natural next step is either (a) a
  presentation-layer enhancement showing which specific Decision links
  each pair of connected Patterns, or (b) the first coaching layer built
  atop recognized Strategy Signatures — both explicitly out of scope
  here and deferred to product direction.
