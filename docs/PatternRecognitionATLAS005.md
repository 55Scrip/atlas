# ATLAS-005 — Pattern Recognition

**Status:** Implemented, pending review.
**Scope:** The first capability that looks *across* an investor's recorded Decisions to discover structural recurrence — a Pattern, in the sense fixed by ATLAS-005-D — and expose it. Read-only throughout. Introduces no new domain aggregate, no new persistence, no new writes.
**Depends on:** ATLAS-005-D's authoritative Pattern definition, and the existing, unmodified `DecisionTimelineQuery` (ATLAS-004).

---

## 1. Purpose

ATLAS-005-D fixed a strict distinction: a **Pattern** is a recurring
structure that exists in an investor's recorded history whether or not
Atlas has found it; **Pattern Recognition** is the separate act that
discovers a Pattern already there — it never creates one. This
increment builds the smallest capability that performs that act: it
reads an investor's already-assembled Decision Timeline, looks for
recurring structure within it, and presents whatever it finds. Nothing
about the domain definition changed to accommodate this; the increment
was designed to fit it.

## 2. Naming: `RecognizedPattern`, Not `PatternObservation`

The recorded artifact one act of Pattern Recognition produces is named
**`RecognizedPattern`**, deliberately not `PatternObservation`. Atlas's
Core Loop already has a first-class `Observation` aggregate
(API-003/ATLAS-001) with an unrelated, established meaning — what an
investor noticed about the world while reasoning toward a Decision.
Reusing "Observation" for Pattern Recognition's output would have
created exactly the kind of terminology collision this codebase has
consistently avoided (the `atlas.memory.timeline.Timeline` /
`DecisionTimeline` precedent, ATLAS-004). `RecognizedPattern` reads
correctly in the domain: it names the thing as *a Pattern, as
recognized* — not a new species of Observation.

## 3. Folder Structure

```
atlas/core/application/pattern_recognition/
    recognized_pattern.py   # RecognizedPattern — the recorded artifact of one recognition act
    strategies.py             # PatternRecognitionStrategy protocol + SameSubjectAndTypeStrategy
    query.py                   # PatternRecognitionQuery — runs registered strategies over a DecisionTimeline
    composition.py               # build_pattern_recognition_query(engine) — the only place aware of an Engine
    cli.py                          # standalone entry point: python -m atlas.core.application.pattern_recognition.cli

tests/unit/application/pattern_recognition/test_query.py
```

No new domain aggregate, no new persistence table, no new repository
method, no new REST endpoint, no modification to Pattern's domain
definition, Core Loop, Decision Review, or Decision Timeline.

## 4. Recognition Model

**`RecognizedPattern`** (frozen dataclass):

```python
@dataclass(frozen=True)
class RecognizedPattern:
    strategy_name: str
    member_decision_ids: tuple[DecisionId, ...]
    description: str
    recognized_at: datetime
```

- `member_decision_ids` — the traceability anchor: the exact,
  enumerable Decisions the recognized Pattern is about, independently
  verifiable against the Decision Timeline.
- `description` — explicitly a **presentation** field (ATLAS-005-D §3,
  invariant 11): a plain-language sentence the strategy generates,
  attached for convenience but never part of the artifact's identity.
  Identity is `(strategy_name, member_decision_ids)`.
- `recognized_at` — when this recognition act happened. Each run
  produces fresh `RecognizedPattern`s; nothing is merged into or
  overwrites a prior run (ATLAS-005-D invariant 9: recognition is a
  discrete, dated act, not a subscription).
- Not a domain aggregate: no identity beyond its content, never
  persisted, recomputed fresh every call — the same status already
  established for `DecisionTimeline`/`DecisionTimelineEntry`.

**`PatternRecognitionStrategy`** (`Protocol`): one method,
`recognize(timeline: DecisionTimeline) -> tuple[RecognizedPattern, ...]`
— a pure function of an already-assembled `DecisionTimeline`, no side
effects, no I/O.

**`SameSubjectAndTypeStrategy`** (the one concrete strategy shipped):
groups Decisions by `(subject.value, decision_type)`; any group of two
or more becomes one `RecognizedPattern` — e.g. *"You have made 2 BUY
decisions on NVIDIA."* Uses only exact equality on already-structured
fields — no text similarity, no heuristic scoring — so every result is
trivially explainable and traceable. Other strategies ATLAS-005-D's own
examples anticipate (repeated reasoning language, confidence-level
recurrence, review-completion recurrence, learning-recurrence) are
explicitly deferred; the protocol exists so they can be added later
without touching this one.

## 5. Recognition Lifecycle

No session, no state that advances — nothing is being captured.

1. **Assemble** — `build_decision_timeline_query(engine).build()`
   (ATLAS-004, unmodified) produces one `DecisionTimeline`.
2. **Recognize** — `PatternRecognitionQuery.build()` runs every
   registered strategy over that same `DecisionTimeline`, collecting
   each strategy's `RecognizedPattern`s independently. Strategies are
   never merged, deduplicated, or ranked against each other.
3. **Present** — the CLI lists every `RecognizedPattern`, each with its
   `description` and the specific Decisions it traces back to.
4. There is no step 4. Nothing is written; nothing persists between
   runs.

## 6. Read Boundary

- `PatternRecognitionQuery` and every strategy never call `.add(...)`
  on any repository — proved both structurally and at runtime (a
  `RaisingOnAdd`-style spy test, matching ATLAS-004).
- Never creates, modifies, or deletes any Decision, Outcome, Evaluation,
  or Learning.
- Never evaluates the investor: `description` states recurrence in
  neutral, structural terms only ("you made N decisions of type X on
  subject Y"), never a judgment.
- Fully derived from `DecisionTimeline` — no new repository method, no
  new SQL, no `Engine` dependency outside `composition.py`.
- No persisted `RecognizedPattern` history across runs — an explicit,
  disclosed simplification (§10), not a silent gap.

## 7. Components

- **`RecognizedPattern`**, **`PatternRecognitionStrategy`**,
  **`SameSubjectAndTypeStrategy`** — §4.
- **`PatternRecognitionQuery`** — constructor takes a
  `DecisionTimelineQuery` and a sequence of strategies;
  `build() -> tuple[RecognizedPattern, ...]` assembles the timeline
  once, then runs every strategy over it.
- **`build_pattern_recognition_query(engine)`** (`composition.py`) —
  the only place in this module aware of an `Engine`; reuses
  `build_decision_timeline_query(engine)` (ATLAS-004) unmodified and
  wires it to the default strategy list.
- **`cli.py`** — standalone entry point, same independence discipline
  as the three existing CLIs: no registration in `atlas/cli/main.py`,
  no import to/from `atlas/conversation/`, shares the database via the
  existing `create_database_engine()` (ATLAS-003).

## 8. Sequence

```
Person                CLI                PatternRecognitionQuery      DecisionTimelineQuery
  |--run------------->| build()          |                            |
  |                    |----------------->| build()                   |
  |                    |                  |-------------------------->| (read-only, ATLAS-004)
  |                    |                  |<--DecisionTimeline---------|
  |                    |                  | run each strategy over it |
  |<--RecognizedPatterns, grouped by strategy_name, with descriptions--|
```

## 9. Test Summary

9 new tests in `tests/unit/application/pattern_recognition/test_query.py`,
regression-clean against the existing suite:

- **`TestNoRecurrence`** — no Decisions, a single Decision, two
  Decisions with different subjects, and two Decisions with the same
  subject but different type all yield no results.
- **`TestSameSubjectAndTypeRecurrence`** — two matching Decisions yield
  one `RecognizedPattern` with the correct `member_decision_ids`,
  description, and `recognized_at`; a dedicated traceability test
  confirms the recognized ids exactly match what an independent read of
  the Decision Timeline for that subject/type pair would show; three
  matching Decisions are all captured as members of one
  `RecognizedPattern` (not silently limited to two).
- **`TestStrategyExtensibility`** — a second, independent fake strategy
  runs alongside `SameSubjectAndTypeStrategy` without interference; both
  sets of results appear, tagged by `strategy_name`, unmerged.
- **`TestNeverWrites`** — a runtime spy (`RaisingOnAdd`) wrapping every
  repository beneath the `DecisionTimelineQuery` raises `AssertionError`
  if `.add()` is called; `PatternRecognitionQuery.build()` completes
  without raising, proving no write path exists at runtime.
- **Manual verification:** two First Decision Conversation CLI runs
  sharing one `ATLAS_HOME`, both recording a BUY decision on NVIDIA with
  different reasoning, followed by the Pattern Recognition CLI —
  correctly surfaced one `RecognizedPattern`, *"You have made 2 BUY
  decisions on NVIDIA,"* listing both Decision ids.

**Regression:** full repository suite: **7,567 passed, 3 skipped**
(7,558 pre-existing + 9 new). Scoped lint (`atlas/core`, `tests/unit`):
clean. Whole-repo `ruff check .` count unchanged at 1,202. `git diff
--stat` confirms the change set is purely additive — zero existing file
touched.

## 10. Architectural Decisions

1. **`RecognizedPattern`, not `PatternObservation`** — avoids colliding
   with the Core Loop's existing `Observation` aggregate (§2).
2. **A pluggable `PatternRecognitionStrategy` protocol**, not a single
   monolithic "detect everything" function — directly satisfies
   ATLAS-005-P's constraint that different recognition strategies may
   legitimately identify different Patterns from the same history, and
   keeps each strategy independently simple, testable, and explainable.
3. **Exact structural field equality only** for the first strategy — no
   text similarity or heuristic scoring, guaranteeing every result stays
   explainable and keeping this increment clear of anything
   ML-adjacent, which the domain definition explicitly forbids.
4. **Reuse `DecisionTimelineQuery`'s already-assembled `DecisionTimeline`**
   rather than querying the four repositories directly — avoids
   duplicating assembly/ordering logic and guarantees Pattern
   Recognition's view of history is always identical to what Decision
   Timeline already shows, which traceability depends on.
5. **No persistence of `RecognizedPattern`s across runs** — recomputed
   fresh every time, consistent with ATLAS-004's own precedent; a real,
   disclosed trade-off, not a silently-accepted gap.
6. **A separate `pattern_recognition/` module and CLI**, not folded into
   `decision_timeline`'s — matching the independence discipline already
   applied to every prior standalone capability.

## 11. Anything That Feels Overengineered

Nothing beyond what the domain definition and the "smallest possible
capability" mandate required. The `PatternRecognitionStrategy` protocol
is one method; only one concrete strategy ships. No registry, no
configuration system, no ranking or merging logic was added ahead of
having a second strategy that would need it.

## 12. What Can Be Simplified

Nothing at this stage — the module is already minimal. The most likely
future growth points (additional strategies, persistence of recognition
runs, filtering/search) are all deliberately deferred rather than
half-built now.

## 13. Genuine Risks / Unresolved Questions

- **Exact-match strategy can miss real recurrences** from trivial
  variation (e.g., "NVIDIA" vs. "Nvidia Corp") — `Subject` normalizes
  whitespace but not casing or aliasing; a disclosed limitation of this
  first strategy.
- **No persisted recognition history** — re-running always recomputes
  from scratch; there is no way yet to compare "what was recognized last
  week" against today.
- **Multiple future strategies may produce overlapping or seemingly
  contradictory results** with no reconciliation — by design, but only
  latent while a single strategy ships.
- **No authentication** — same placeholder-identity gap disclosed in
  every prior increment; `DecisionRepository.list_all()` is not scoped
  to a single investor yet.

## 14. Future Backlog

- Additional recognition strategies already anticipated by the domain
  definition's own examples: repeated reasoning language, confidence-
  level recurrence, review-completion recurrence, learning-recurrence.
- Persisting each recognition run as its own dated record, if usage
  shows comparing recognition results over time is needed.
- Filtering, search, or ranking across `RecognizedPattern`s once
  multiple strategies and a larger history make the plain list hard to
  scan.
- Carried forward, unaffected by this increment: re-evaluating
  `reasoning_link`'s placement and permanence, a REST API layer for the
  Core Loop, the shared structured Error Contract, the brittle
  hard-coded test-count assertion in `README.md`/`tests/test_release_candidate.py`,
  and the `tests/test_config_sprint195.py` test-isolation issue
  (currently being fixed in a separate session).
- **Recommendation for the next sprint:** a second recognition strategy
  — most likely repeated-reasoning-language or review-completion
  recurrence — to prove the `PatternRecognitionStrategy` protocol
  actually supports multiple, independent, non-reconciled strategies in
  practice, not just in test doubles.
