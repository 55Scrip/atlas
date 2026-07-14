# ATLAS-004 — Decision Timeline

**Status:** Implemented, pending review.
**Scope:** The first longitudinal, read-only capability — a chronological arrangement of an investor's own recorded Decisions, each with every Decision Review chain (Outcome → Evaluation(s) → Learning(s)) nested underneath it. Introduces no new domain concept, no new persistence, no new writes.
**Depends on:** the existing, unmodified `DecisionRepository`, `OutcomeRepository`, `EvaluationRepository`, `LearningRepository` (API-001, ATLAS-001), and the shared database configuration (ATLAS-003).

---

## 1. Purpose

Every Decision, up through ATLAS-003, exists only in isolation — an
investor can capture one, and can later review one, but has no way to
see their own decision history *as a history*. ATLAS-004 is the first
longitudinal capability: not analytics, not coaching, just a
chronological foundation those could later be built on. A Decision
Timeline is not a database query, a report, or a dashboard — it is the
chronological arrangement of an investor's own Decisions, each shown
exactly as it was recorded, in the order it actually happened, with
nothing added, nothing interpreted, and no cardinality invented that the
domain doesn't actually have.

## 2. Cardinality Verified Directly Against Persistence, Not Assumed

Before modeling the read structure, `atlas/core/infrastructure/persistence/evaluation/table.py`
and `.../learning/table.py` were read directly: neither
`evaluations_table.outcome_id` nor `learnings_table.evaluation_id`
carries `unique=True`, and neither table declares a SQL `ForeignKey` —
the same "no artificial 1:1" design already present for
`outcomes_table.decision_id`. **Multiple Evaluations may exist for a
single Outcome, and multiple Learnings may exist for a single
Evaluation** — a Decision Review producing a second Evaluation for the
same Outcome, or a second Learning for the same Evaluation, is entirely
legal today. The read model therefore exposes every recorded Evaluation
and every recorded Learning as ordered tuples, never silently selecting
one.

## 3. Folder Structure

```
atlas/core/application/decision_timeline/
    timeline.py    # DecisionTimeline, DecisionTimelineEntry, DecisionReviewChain, EvaluationWithLearnings — plain, immutable, not domain aggregates
    query.py        # DecisionTimelineQuery — assembles a DecisionTimeline from repository interfaces only, no Engine dependency
    composition.py   # build_decision_timeline_query(engine) / create_decision_timeline_tables(engine) — the only place aware of an Engine
    cli.py             # standalone entry point: python -m atlas.core.application.decision_timeline.cli

tests/unit/application/decision_timeline/test_query.py
```

No new domain aggregate, no new persistence table, no new repository
method, no new REST endpoint, no modification to any Core Loop domain
file, `reasoning_link`, `ConversationOrchestrator`, or
`DecisionReviewOrchestrator`.

**Legacy naming check:** `atlas/memory/timeline.py` already defines an
unrelated `Timeline`/`TimelineComparison` snapshot-diff concept over a
`MemoryStore`. Every type this increment introduces uses the
domain-specific `Decision*` prefix, so no bare `Timeline` name is added
alongside the existing one.

## 4. Timeline Model

- **`DecisionTimelineEntry`** — one entry per Decision: the `Decision`
  itself, verbatim, plus a tuple of `DecisionReviewChain` (zero, one, or
  more — Decision Review permits repeat reviews).
- **`DecisionReviewChain`** — one Outcome and every Evaluation recorded
  against it: `outcome: Outcome`, `evaluations: tuple[EvaluationWithLearnings, ...]`
  (may be empty — an Outcome with no Evaluation yet, per ATLAS-003's own
  disclosed interrupted-review case).
- **`EvaluationWithLearnings`** — one Evaluation and every Learning
  recorded against it: `evaluation: Evaluation`, `learnings: tuple[Learning, ...]`
  (may be empty).
- **`DecisionTimeline`** — an ordered, immutable `entries: tuple[DecisionTimelineEntry, ...]`.

All four are plain frozen dataclasses, explicitly documented as **not
domain aggregates**: no identity of their own, never persisted,
recomputed fresh on every call — closer to a read-model than even
session state.

**Deterministic ordering, by the child record's own `recorded_at`
(Atlas's own clock), never the investor-supplied timestamp, at every
nesting level:**

- Decisions: `(decided_at, decision_id)` ascending. `Decision.decided_at`
  is already UTC-normalized at capture time, so this is a plain, correct
  sort.
- Outcomes within a Decision: `(outcome.recorded_at, outcome_id)`.
- Evaluations within an Outcome: `(evaluation.recorded_at, evaluation_id)`.
- Learnings within an Evaluation: `(learning.recorded_at, learning_id)`.

Every `*_id` tie-breaker carries no meaning of its own — it exists only
for determinism when two sibling records share an identical
`recorded_at`.

## 5. Read Boundary

Timeline never owns Decisions, Outcomes, Evaluations, or Learnings — it
only reads them.

- `DecisionTimelineQuery` never calls `.add(...)` on any repository —
  proved at runtime, not just by inspection (`TestNeverWrites`, §7).
- Timeline never summarizes reasoning: every statement is displayed
  exactly as recorded.
- Timeline never evaluates: no score, no judgment.
- Timeline never invents cardinality: every Evaluation per Outcome and
  every Learning per Evaluation that actually exists is exposed, in
  deterministic order.
- `DecisionTimelineQuery` depends only on the four repository interfaces
  — `composition.py` is the only file in this module aware of a
  SQLAlchemy `Engine` — compatible with a future coaching/analytics
  capability without modification.

## 6. Lifecycle

No session, no state that advances — nothing is being captured.

1. **Assemble** — `DecisionTimelineQuery.build()` reads every Decision
   (`DecisionRepository.list_all()`), every Outcome per Decision
   (`OutcomeRepository.list_by_decision_id(...)`), every Evaluation per
   Outcome (`EvaluationRepository.list_by_outcome_id(...)`), and every
   Learning per Evaluation (`LearningRepository.list_by_evaluation_id(...)`)
   — entirely via existing, unmodified repository methods — and returns
   one fully-ordered `DecisionTimeline`.
2. **Present** — the CLI prints the ordered list, then lets a person
   pick one entry to see its full detail: the Decision's own fields,
   then every Outcome, and under each, every Evaluation, and under each,
   every Learning — all verbatim, all shown, none collapsed.
3. There is no step 3. Nothing is written.

## 7. Components

- **`EvaluationWithLearnings`**, **`DecisionReviewChain`**,
  **`DecisionTimelineEntry`**, **`DecisionTimeline`** — frozen
  dataclasses (§4).
- **`DecisionTimelineQuery`** — constructor takes `DecisionRepository`,
  `OutcomeRepository`, `EvaluationRepository`, `LearningRepository`. One
  method: `build() -> DecisionTimeline`.
- **`build_decision_timeline_query(engine)`** / **`create_decision_timeline_tables(engine)`**
  (`composition.py`) — the only place in this module aware of an
  `Engine`.
- **`cli.py`** — standalone entry point, same independence discipline as
  the First Decision Conversation and Decision Review CLIs: zero
  registration in `atlas/cli/main.py`, zero import to/from
  `atlas/conversation/`, uses the shared `create_database_engine()` so it
  reads whatever those CLIs have already recorded.

## 8. Sequence

```
Person                CLI                DecisionTimelineQuery       Repositories
  |--run------------->| build()          |                          |
  |                    |----------------->| list_all() / list_by_*  |
  |                    |                  |------------------------>| (read-only)
  |<--numbered list----|<--DecisionTimeline--                       |
  |--"2"-------------->| _print_detail(entry)                       |
  |<--full nested detail (Decision, Outcomes, Evaluations, Learnings)|
```

## 9. Test Summary

10 new tests in `tests/unit/application/decision_timeline/test_query.py`,
regression-clean against the existing suite:

- **`TestEmptyTimeline`** — no Decisions yields no entries.
- **`TestDecisionOrdering`** — ascending `decided_at` order; identical
  `decided_at` tie-broken deterministically by `decision_id`.
- **`TestReviewChainNesting`** — a Decision with no Outcomes has empty
  review chains; multiple Outcomes ordered by `recorded_at`; an Outcome
  with no Evaluations has an empty evaluations tuple.
- **`TestMultipleEvaluationsPerOutcomeAreAllPreserved`** — two
  Evaluations for the same Outcome both appear, correctly ordered
  (the cardinality-correctness test required before implementation);
  an Evaluation with no Learnings has an empty learnings tuple.
- **`TestMultipleLearningsPerEvaluationAreAllPreserved`** — two Learnings
  for the same Evaluation both appear, correctly ordered.
- **`TestNeverWrites`** — a runtime spy wrapper (`RaisingOnAdd`) around
  every repository raises `AssertionError` if `.add()` is called;
  `build()` completes without raising, proving no write path exists at
  runtime, not just by code inspection.
- **Manual verification:** a four-process walkthrough sharing one
  `ATLAS_HOME` — First Decision Conversation, then two independent
  Decision Review runs against the same Decision, then the Decision
  Timeline CLI — confirmed the timeline correctly showed "reviewed 2x"
  with both full review chains nested under the one Decision, in order.

**Regression:** full repository suite: **7,558 passed, 3 skipped**
(7,548 pre-existing + 10 new). Scoped lint (`atlas/core`, `tests/unit`):
clean. Whole-repo `ruff check .` count unchanged at 1,202. `git diff
--stat` confirms the change set is purely additive — zero existing file
touched (unlike ATLAS-003, no approved touch to existing code was part
of this plan).

## 10. Architectural Decisions

1. **`DecisionTimelineQuery` depends only on repository interfaces, never
   on a SQLAlchemy `Engine`** — `composition.py` is the sole place in
   this module aware of one, mirroring the domain/application vs.
   infrastructure separation used everywhere else in this codebase, now
   applied for the first time to a read path rather than a write path.
2. **Domain-specific `Decision*`-prefixed type names**, avoiding a second
   bare `Timeline` concept alongside `atlas.memory.timeline.Timeline`.
3. **Cardinality verified against the actual persistence layer before
   modeling**, not assumed — the corrected model exposes every recorded
   Evaluation and Learning as immutable, deterministically-ordered
   tuples rather than silently picking one.
4. **Deterministic `(recorded_at, id)` ordering applied uniformly at
   every nesting level** — Decisions, Outcomes, Evaluations, and
   Learnings all order by the record's own Atlas-assigned timestamp, not
   the investor-supplied one, because only Atlas's own clock is
   guaranteed unambiguous across sibling records.
5. **No new persistence, no new repository method** — the entire
   capability is assembled from methods the domain layer already
   exposed.

## 11. Anything That Feels Overengineered

Nothing new was introduced beyond what the cardinality finding required.
The four nested frozen dataclasses are the minimum needed to represent
"all recorded history, nothing collapsed" without inventing a merged
event stream or a persisted read-model — both considered and rejected as
premature for a first longitudinal slice.

## 12. What Can Be Simplified

- No filtering, search, or pagination exists yet — acceptable at current
  scale, a real constraint once many Decisions (or many Evaluations per
  Outcome, many Learnings per Evaluation) accumulate.
- The CLI's plain-text nested detail view will become harder to read
  well once multiple Evaluations/Learnings per node are common —
  acceptable for this slice, a genuine design question for any future
  UI.

## 13. Genuine Risks / Unresolved Questions

- **A plain, unfiltered timeline won't scale** once many Decisions (or
  deeply nested review chains) accumulate.
- **An incomplete review chain renders exactly as incomplete** — an
  Outcome with an empty `evaluations` tuple, or an Evaluation with an
  empty `learnings` tuple, must display gracefully, not as an error;
  confirmed correct in both automated tests and the manual walkthrough.
- **Multiple Evaluations per Outcome or Learnings per Evaluation may be
  visually confusing in a plain-text CLI** once they're common — no
  attempt made here to explain *why* a chain looks the way it does.
- **No authentication** — same placeholder-identity gap already
  disclosed in ATLAS-002/003.

## 14. Future Backlog

- Filtering, search, and pagination over the Decision Timeline once
  volume warrants it.
- A merged, single reasoning-event stream (rather than reviews nested
  under their Decision) — deliberately not attempted here.
- A persisted or cached read-model, if `DecisionTimelineQuery.build()`'s
  fully-fresh reassembly becomes a performance concern.
- Carried forward, unaffected by this increment: re-evaluating
  `reasoning_link`'s placement and permanence, a REST API layer for the
  Core Loop, the shared structured Error Contract, the brittle
  hard-coded test-count assertion in `README.md`/`tests/test_release_candidate.py`,
  and the pre-existing `tests/test_config_sprint195.py` test-isolation
  issue (ATLAS-003, §12).
- **Recommendation for the next sprint:** with a Decision Timeline now
  in place, the natural next longitudinal capability is either (a) a
  read-only Portfolio or cross-Decision view grouped by subject, or (b)
  the first coaching/analytics layer built atop `DecisionTimelineQuery`
  — both explicitly out of scope for ATLAS-004 and deferred to product
  direction.
