# ATLAS-003 — Decision Review

**Status:** Implemented, pending review.
**Scope:** The human-facing occasion on which the existing Outcome → Evaluation → Learning part of the Core Loop is completed for one previously recorded Decision. Introduces no new domain concept.
**Depends on:** the existing, unmodified `DecisionRepository`, `OutcomeService`, `EvaluationService`, and `LearningService` (API-001, ATLAS-001).

---

## 1. Purpose

The accepted domain definition: a Decision Review is the occasion on
which an investor returns, after real time has passed, to a specific
Decision they already made, to record what happened, how that compares to
what was expected, and what should be carried forward. ATLAS-002 gave a
person a way to reach a recorded Decision through conversation, but
stopped there by design — a decision cannot honestly produce its own
outcome, evaluation, and learning in the same sitting it was made in.
ATLAS-003 is the separate, later occasion that completes the cycle.

## 2. The Persistence Prerequisite, and What Was Reused

ATLAS-002's CLI originally created a fresh temporary directory on every
run, so a Decision it recorded could not be found by any later process.
Decision Review's entire premise requires that gap closed.

Rather than inventing a new default database location, this increment
reuses `atlas.config.DATABASE_PATH` — already neutral, already
`ATLAS_HOME`-overridable, and already the same physical database the
existing REST API layer (Decision, DecisionContext, Observation,
Hypothesis, Evidence) reads and writes. A new, genuinely neutral module,
`atlas/core/infrastructure/config/database.py`, wraps it:

```python
resolve_database_path(explicit_path=None)  # explicit arg > ATLAS_CORE_DB_PATH env var > atlas.config.DATABASE_PATH
create_database_engine(explicit_path=None)  # engine for the resolved path
```

This module contains no conversation or review behavior whatsoever —
purely path and engine resolution, creating the parent directory if
needed. Both the First Decision Conversation CLI and the new Decision
Review CLI import it. **The only touch to existing code in this
increment:** `atlas/core/application/conversation/cli.py` now calls
`create_database_engine()` instead of `tempfile.mkdtemp()` — a one-line
change to where its database comes from, not to its conversation logic,
prompts, orchestration, or session behavior.

Verified end-to-end with three separate process invocations sharing one
`ATLAS_HOME`: a First Decision Conversation run, followed by a Decision
Review run against the resulting Decision, followed by a second,
independent Decision Review run against the same Decision — all
reconnecting correctly through the shared database.

## 3. Folder Structure

```
atlas/core/infrastructure/config/
    database.py           # resolve_database_path / create_database_engine — neutral, no conversation/review behavior

atlas/core/application/decision_review/
    session.py             # DecisionReviewStep (OUTCOME, EVALUATION, LEARNING, REVIEW_RECORDED), DecisionReviewSession
    prompts.py              # human-facing question copy
    lookup.py                # Decision listing/selection — read-only
    orchestrator.py           # DecisionReviewOrchestrator — three explicit step handlers
    composition.py             # build_decision_review_orchestrator(engine) / create_decision_review_tables(engine)
    cli.py                      # standalone entry point: python -m atlas.core.application.decision_review.cli

tests/unit/infrastructure/config/test_database.py
tests/unit/application/decision_review/{test_orchestrator.py, test_review_end_to_end.py}
```

No new domain aggregate, no new persistence table beyond what Outcome/
Evaluation/Learning already define, no new REST endpoint, no
modification to any Core Loop domain file, `reasoning_link`, or
`ConversationOrchestrator`'s own logic.

## 4. Decision Lookup and Selection

Built entirely on `DecisionRepository`'s existing, unmodified
`list_all() -> list[Decision]` — no new query method. `lookup.py`
formats each Decision using only its already-public fields (`subject`,
`decision_type`, `decided_at`, `confidence`) and returns a 1-based
index-to-`Decision` mapping. `select_decision(...)` resolves a person's
typed number to a `Decision`, returning `None` on an invalid answer so
the caller re-asks rather than guesses. **This is the only repository
this increment ever reads from without also being permitted to write
to** — `lookup.py` never calls `DecisionRepository.add(...)`.

## 5. Review Conversation Lifecycle

1. **Selection** — the CLI lists every recorded Decision, numbered;
   an invalid number re-asks.
2. **Outcome** — *"Looking back, what actually happened?"* →
   `OutcomeService.capture(...)`, unmodified.
3. **Evaluation** — *"How did that compare to what you expected?"* →
   `EvaluationService.capture(...)`, unmodified.
4. **Learning** — *"What will you take from this for next time?"* →
   `LearningService.capture(...)`, unmodified.
5. **Closing** — terminal `REVIEW_RECORDED` state.

**Every Decision Review always produces exactly one full, fresh Outcome
→ Evaluation → Learning triple.** It never detects or resumes a
partially-completed prior review. **Explicitly documented, not silently
handled:** if a person quits partway through — for instance after
Outcome but before Evaluation — that Outcome simply exists with no
Evaluation or Learning attached, permanently. ATLAS-003 does not detect
this, does not resume it, and does not repair it. Running the review
again against the same Decision produces a second, independent Outcome,
unrelated to the incomplete first one. `test_review_end_to_end.py`
asserts this directly, not just as an implied consequence.

## 6. Boundary Between Review Orchestration and Core Loop

Identical framing to ATLAS-002's boundary, extended by one item:

**Review orchestration owns:** session state, Decision lookup/selection,
which question to ask next, and elicitation. **The three existing
services remain the sole owners of:** domain object creation, validation,
and the reasoning records themselves.

- The orchestrator may list and read Decisions but never writes to
  `DecisionRepository`.
- The orchestrator copies the person's own words into `Evaluation`'s
  statement verbatim — **Atlas never evaluates the investor; it records
  the investor's own reflection.** This is not new machinery: it is the
  same non-scoring, free-text design `Evaluation.capture()` already has.
  Decision Review provides the human-facing occasion to invoke what
  already refuses to judge; it adds no judgment of its own.
- Outcome, Evaluation, and Learning are append-only exactly as they
  already are everywhere else.

## 7. `DecisionReviewSession` — Not a Domain Aggregate

Same rationale as `ConversationSession` (ATLAS-002): a plain, mutable,
non-persisted class. It holds `session_id`, `decision_id` (the one
Decision being reviewed), `current_step`, the three ids produced as the
review progresses, and partial values for the current step. It is
exempt from this codebase's insert-only/immutability discipline because
it is orchestration state, not domain data.

## 8. Sequence — One Full Review

```
Person                    DecisionReviewOrchestrator          Core Loop services
  |--(views numbered list)->| list_decisions()                |
  |                          |--DecisionRepository.list_all()->| (read-only)
  |--"1"------------------->| select(numbered, "1")            |
  |                          |--DecisionRepository ... (read)-->|
  |<--"What happened?"------|  (DecisionReviewSession created) |
  |--"Revenue grew..."----->| _handle_outcome                  |
  |                          |--OutcomeService.capture-------->| (existing, unmodified)
  |<--"How did that..."-----|                                   |
  |--"As expected"---------->| _handle_evaluation                |
  |                          |--EvaluationService.capture----->| (existing, unmodified)
  |<--"What will you..."----|                                   |
  |--"Weigh guidance..."---->| _handle_learning                  |
  |                          |--LearningService.capture------->| (existing, unmodified)
  |<--closing message-------|  (current_step = REVIEW_RECORDED) |
```

## 9. Test Summary

19 new tests, regression-clean against the existing suite:

- **Config module (5 tests):** explicit-path precedence, environment
  variable override, fallback to `atlas.config.DATABASE_PATH`,
  parent-directory creation, engine construction.
- **Orchestrator (9 tests):** listing (empty and populated), selection
  (valid, invalid number, non-numeric, never writes to
  `DecisionRepository`), and each of the three step handlers.
- **End-to-end (5 tests):** one full scripted review with the exact
  linked state verified; confirmation the Decision itself is never
  written to; two independent reviews of the same Decision producing two
  separate triples; an interrupted review leaving exactly an orphaned
  Outcome (asserted directly); a fresh review after an interruption
  producing a second, unrelated Outcome.
- **Manual verification:** three separate process invocations sharing
  one `ATLAS_HOME` — First Decision Conversation, then Decision Review,
  then a second Decision Review against the same Decision — confirming
  cross-process reconnection actually works.

**Regression:** full repository suite: **7,548 passed, 3 skipped**
(7,529 pre-existing + 19 new). Scoped lint (`atlas/core`, `tests/unit`):
clean. Whole-repo `ruff check .` count unchanged at 1,202. `git diff
--stat` confirms the change set is additive except for the one disclosed
line in `atlas/core/application/conversation/cli.py`.

**A pre-existing test-isolation issue was found and worked around, not
fixed at its source.** `tests/test_config_sprint195.py`'s
`test_atlas_home_env_var_respected` reloads `atlas.config` via
`importlib.reload` with a monkeypatched `ATLAS_HOME`, and its own
"restore" step re-imports the module before `monkeypatch` reverts the
environment variable — leaving the live `atlas.config.DATABASE_PATH`
module attribute unreliable for the remainder of the test session. This
increment's own config test was written to compare against
`resolve_database_path()`'s own frozen internal reference rather than a
fresh, order-dependent re-import of `atlas.config.DATABASE_PATH`,
sidestepping the issue without touching the unrelated legacy test file.
See §12 for why this wasn't fixed at the source.

## 10. Architectural Decisions

1. **Reused `atlas.config.DATABASE_PATH` as the shared default** rather
   than inventing a new, competing location — converges the CLIs onto
   the same physical database the REST layer already uses.
2. **The neutral config module contains zero conversation/review logic**
   — a deliberate, narrow boundary, not a general-purpose settings
   system.
3. **Fresh-triple review model, with the interrupted-review limitation
   stated explicitly** rather than merely implied — a real, disclosed
   trade-off, not a silently-accepted gap.
4. **Decision lookup is read-only by construction** — `lookup.py` has no
   code path that could write to `DecisionRepository`.
5. **A separate `decision_review/` module**, not folded into
   `conversation/` — Decision Review is a distinct session type
   triggered at an unrelated, later time.

## 11. Genuine Risks / Unresolved Questions

- **An interrupted review permanently leaves an orphaned Outcome (or
  Outcome + Evaluation)** — accepted, disclosed limitation, not
  addressed in this increment.
- **A plain, unfiltered Decision list won't scale** once many Decisions
  accumulate.
- **No indication at selection time of prior review history** for a
  given Decision.
- **No authentication** — same placeholder-identity gap already
  disclosed in ATLAS-002.
- **Both CLIs now share one physical database with the existing REST
  layer** — the point of this increment, but a change in kind from
  ATLAS-002's original fully-isolated, throwaway-database behavior.

## 12. Future Backlog

- **Design partial-review detection/resume/repair**, if real usage shows
  interrupted reviews are common enough to matter.
- **Search/filter the Decision lookup** once the list is large enough to
  need it.
- **Fix `tests/test_config_sprint195.py`'s reload-order test-isolation
  issue at its source** (§9) — out of scope for this increment (an
  unrelated, pre-existing legacy test), worked around rather than
  touched, consistent with this codebase's discipline of not silently
  fixing things outside a increment's stated scope.
- Carried forward, unaffected by this increment: re-evaluating
  `reasoning_link`'s placement and permanence (per explicit product
  direction), a REST API layer for the Core Loop, the shared structured
  Error Contract, and the brittle hard-coded test-count assertion in
  `README.md`/`tests/test_release_candidate.py`.
