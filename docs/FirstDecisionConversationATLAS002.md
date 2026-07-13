# ATLAS-002 — First Decision Conversation

**Status:** Implemented, pending review.
**Scope:** The first human-facing entry point to the Core Loop — a standalone CLI that walks a person through one Decision, via plain-English questions, from Question through Decision. Outcome, Evaluation, and Learning are explicitly out of scope (§3).
**Depends on:** the seven Core Loop application services built in API-001, API-003, API-004, API-005, and ATLAS-001 — used entirely unmodified.

---

## 1. Purpose

ATLAS-001 proved the full ten-step Core Loop could be executed, but only
through direct, manually-sequenced Python calls in a test — no person
could use that without writing code. ATLAS-002 is the first real
application boundary between a human and the Core Loop: a small,
independent CLI conversation that produces one recorded Decision, using
natural questions that never surface an aggregate name.

## 2. Why This Is a *First Decision* Conversation, Not a Full Ten-Step One

A real investment decision cannot naturally produce its own Outcome,
Evaluation, and Learning in the same conversation that made it — those
three steps depend on real-world time passing before there is anything
true to say. Asking a person to "evaluate" or state the "outcome" of a
decision they made thirty seconds ago would mean either fabricating a
result or asking a question with no honest answer. An in-memory session
(§6) also cannot bridge that gap — it can't still exist when the person
returns weeks later.

ATLAS-002 therefore covers exactly:

```
Question → Observation → Interpretation → Hypothesis → Evidence → Conclusion → Decision
```

The conversation ends the instant the Decision is recorded. Outcome,
Evaluation, and Learning are not touched anywhere in this increment — no
service call, no prompt, no table creation (§8) — and are explicitly a
later review phase, to be designed separately (§10).

## 3. The Conversation ↔ Reasoning Boundary

**Conversation owns:** session state, which question to ask next, the
wording of that question, and elicitation (turning a person's typed
answer into a value). **The seven existing Core Loop services remain the
sole owners of:** domain object creation, all validation, and every
reasoning record.

The orchestrator is **allowed** to:
- Decide which question to ask next, based only on which step is current
  and which values are still missing.
- Copy a person's free-text answer verbatim into the field it was
  elicited for — no summarization, no rewriting.
- Perform **literal, deterministic keyword-to-enum translation of the
  person's own stated judgment** (`prompts.parse_direction`,
  `prompts.parse_decision_type`) — e.g. mapping their own words
  "supports"/"challenges" to `Direction.SUPPORTS`/`CHALLENGES`. This is
  translating what the person already said, not the orchestrator forming
  a judgment. An unrecognized answer triggers a re-ask, never a guess.
- Default a field to an already-collected value to avoid asking the same
  thing twice (§7), and construct the existing Request dataclass once a
  step's values are complete.

The orchestrator is **never allowed** to:
- Decide on its own whether something counts as evidence, or whether it
  supports or challenges anything — that word always comes from the
  person.
- Form or word a hypothesis, a conclusion, or a decision itself.
- Skip, weaken, or duplicate any domain-layer validation (each service
  call is wrapped in a broad `try/except`, re-asking the same question on
  failure — this reacts to the domain's own validation outcome, it does
  not re-implement it).
- Persist anything directly — every entity is still created by calling
  one of the seven existing, unmodified services.
- Ask about, infer, or fabricate an Outcome, Evaluation, or Learning. The
  terminal state after Decision is a hard stop, not a soft pause — there
  is no "continue anyway" path in this increment.

## 4. Folder Structure

```
atlas/core/application/conversation/
    __init__.py
    session.py          # ConversationStep (7 steps + DECISION_RECORDED), ConversationSession
    prompts.py           # human-facing question copy + keyword maps for Direction and DecisionType
    orchestrator.py       # ConversationOrchestrator — seven explicit step handlers
    composition.py        # build_conversation_orchestrator(engine) / create_conversation_tables(engine)
    cli.py                 # standalone entry point: python -m atlas.core.application.conversation.cli

tests/unit/application/conversation/
    test_orchestrator.py           # each of the 7 step handlers in isolation
    test_conversation_end_to_end.py # one scripted full conversation
```

No new domain aggregate, no new persistence table beyond what the seven
existing services already define, no new REST endpoint, no modification
to any existing Core Loop file, `app.py`, or `atlas/cli/main.py`.

## 5. `ConversationSession` — Not a Domain Aggregate

`ConversationSession` (`session.py`) is a plain, **mutable** class — the
first intentional exception to this codebase's frozen-dataclass
convention. It is deliberately not a domain aggregate: never persisted,
never touches a repository, not subject to the insert-only/immutability
discipline governing every `atlas/core` aggregate — because it isn't
domain data, it's orchestration state answering "where are we in this
conversation." It holds `session_id`, `current_step`, one id per
completed step, two remembered values used for defaulting (§7), and the
partial answers collected so far for whichever step is in progress.

`ConversationStep` has exactly seven working values (`QUESTION` …
`DECISION`) plus terminal `DECISION_RECORDED`. There are no
Outcome/Evaluation/Learning values in this enum at all — their absence is
the scope boundary itself, not an unused branch.

## 6. Legacy Independence — `atlas/conversation/`

A live, CLI-wired module already exists at `atlas/conversation/engine.py`
(`ConversationEngine`, `ConversationInput`, `ConversationIntent`,
`ConversationResponse`) — a **stateless, single-turn** question router
that classifies intent and dispatches to an existing analysis engine
(backs `atlas ask <question>` in `atlas/cli/main.py`). It has no
multi-turn session concept. No literal name collides with
`ConversationSession`/`ConversationOrchestrator`, but "Conversation" is a
hot, live word in this repository's vocabulary, and
`docs/ConversationCleanupPlan.md` explicitly names a future
"Blueprint-aligned conversation capability" as its own reopening trigger.

This increment is **fully independent**: zero imports between
`atlas/core/application/conversation/` and `atlas/conversation/` in
either direction, verified by grep. The new CLI entry point
(`python -m atlas.core.application.conversation.cli`) is a **standalone
script — not a registration inside `atlas/cli/main.py`**, which is the
file that imports the legacy package today; keeping the new entry point
physically separate is the safest reading of "do not integrate with or
modify the legacy capability."

## 7. Human-Facing Prompts and Field Defaults

No Core Loop aggregate name is ever surfaced. Representative copy:

| Step | Prompt(s) |
|---|---|
| Question | *"What are you trying to figure out?"* |
| Observation | *"What company, sector, or market is this about?"* → *"What did you notice?"* |
| Interpretation | *"Why does that matter — what do you think it suggests?"* |
| Hypothesis | *"Based on that, what do you believe might be going on?"* |
| Evidence | *"What have you found that relates to that belief?"* → *"Does that support it, or challenge it?"* |
| Conclusion | *"Given everything so far, what's your takeaway?"* |
| Decision | *"What are you deciding to do — buy, sell, hold, watch, or pass?"* → *"How confident are you, 0 to 100?"* |

**Fields deliberately never asked:**
- `Decision.subject` defaults to the Observation subject already
  collected.
- `Decision.reason` defaults to the Conclusion statement already
  collected.
- Every timestamp (`raised_at`, `observed_at`, `interpreted_at`,
  `formulated_at`, `concluded_at`, `decided_at`) auto-fills to
  `datetime.now(timezone.utc)`.
- `Decision.user_id` is the session's own `session_id` — a placeholder,
  not a real identity (§9).
- Optional fields (`source`, `note`) everywhere are never elicited.

## 8. Composition Root

`composition.py`'s `create_conversation_tables(engine)` creates exactly
the tables the seven steps need — `questions`, `observations`,
`interpretations`, `hypotheses`, `evidence`, `conclusions`, `decisions`,
plus the four `reasoning_link` tables — and deliberately does **not**
call `create_outcome_table`/`create_evaluation_table`/
`create_learning_table`. `build_conversation_orchestrator(engine)` wires
the seven services in the same order
`tests/unit/application/reasoning_link/test_core_loop_end_to_end.py`
already proved correct, and does not construct `OutcomeService`,
`EvaluationService`, or `LearningService` at all.

## 9. Traceability — Actual Mechanism Per Edge

The final Decision is traceable back through the chain, and each edge
uses the mechanism ATLAS-001 actually built for it — some are a direct FK
field, some are a `reasoning_link` bridge record:

```
Decision --(ConclusionDecisionLink)--> Conclusion
Conclusion --(Conclusion.evidence_id, direct FK)--> Evidence
Evidence --(HypothesisEvidenceLink)--> Hypothesis
Hypothesis --(InterpretationHypothesisLink)--> Interpretation
Interpretation --(Interpretation.observation_id, direct FK)--> Observation
Observation --(QuestionObservationLink)--> Question
```

`tests/unit/application/conversation/test_conversation_end_to_end.py`
asserts every one of these six relationships individually, using the
correct mechanism for each — not a generic "everything is linked"
assertion.

## 10. Sequence — One Full Conversation

```
Person                          ConversationOrchestrator                Core Loop services
  |--"Is demand accelerating?"->| _handle_question                      |
  |                              |--QuestionService.capture------------->|
  |<--"What company/sector..."--|                                        |
  |--"Semiconductor sector"---->| _handle_observation (1st of 2 fields)  |
  |<--"What did you notice?"----|                                        |
  |--"Capex guidance raised"--->| _handle_observation (2nd field)        |
  |                              |--ObserveFromQuestionService.observe-->|
  |<--"Why does that matter?"---|                                        |
  |--...------------------------>| _handle_interpretation                 |
  |                              |--InterpretationService.capture------->|
  ...
  |--"80"---------------------->| _handle_decision (2nd field)           |
  |                              |--CommitDecisionFromConclusionService  |
  |                              |   .commit---------------------------->|
  |<--closing message-----------|  (session.current_step = DECISION_RECORDED)
```

Every read/write against a Core Loop service is exactly the call that
service already exposed before this increment — the orchestrator adds no
new service methods, only sequencing and elicitation around existing
ones.

## 11. Test Summary

17 new tests, regression-clean against the existing suite:

- **Orchestrator (14 tests):** each of the seven step handlers in
  isolation — correct question sequencing (including the two-field steps
  Observation/Evidence/Decision), correct keyword mapping for direction
  and decision type (including the re-ask fallback and a "challenges"
  case), correct Request construction, correct session advancement, and
  explicit confirmation that `Decision.subject`/`reason` default from
  earlier answers rather than being asked again.
- **End-to-end (3 tests):** one scripted full seven-step conversation
  asserting every entity round-trips and every one of the six
  traceability edges holds via its actual mechanism (§9); a second test
  asserting the `outcomes`/`evaluations`/`learnings` tables are never
  even created; a third asserting the closing message contains no
  mention of outcome/evaluation/learning.
- **Manual verification:** a live run of
  `python -m atlas.core.application.conversation.cli`, transcript
  captured, confirming no domain jargon appears in any prompt and the
  closing message reads as a clean, honest stop.

**Regression:** full repository suite: **7,529 passed, 3 skipped**
(7,512 pre-existing + 17 new). Scoped lint (`atlas/core`, `tests/unit`):
clean. Whole-repo `ruff check .` count unchanged at 1,202. Zero
modifications to any existing file — confirmed by `git status` showing
only two new directories.

## 12. Architectural Decisions

1. **`ConversationSession` is explicitly not a domain aggregate** — the
   first intentional exception to the frozen-dataclass convention,
   because it belongs to the application layer, not the domain model.
2. **Seven explicit step-handler methods, not a generic metadata-driven
   engine** — consistent with this codebase's stated preference for
   simplicity over premature abstraction at this scale.
3. **In-memory session only, no persistence** — reinforced, not merely
   permitted, by the scope cut in §2: a single-sitting conversation that
   by design never needs resuming after a gap.
4. **Standalone CLI script, not a registration inside
   `atlas/cli/main.py`** — keeps full independence from that file's
   existing import of the legacy `atlas.conversation` package.
5. **Broad `try/except` around each service call, re-asking on failure**
   — reacts to the domain layer's own validation outcome without
   duplicating or weakening it.
6. **`Decision.user_id` is the session's own UUID** — a disclosed
   placeholder, not a real identity system.

## 13. Genuine Risks / Unresolved Questions

- **Keyword mapping can fail to recognize an answer** (e.g. "kind of
  supports it, I guess") — mitigated by a re-ask, not a guess.
- **"Conversation" remains a hot word** in this repo's vocabulary — no
  literal collision, but readers should cross-reference this doc and
  `docs/ConversationCleanupPlan.md` to avoid confusing the two.
- **`docs/ConversationCleanupPlan.md`'s own reopening trigger** may be
  considered triggered by this increment's existence — this doc does not
  perform that review.
- **No session persistence** — a conversation cannot survive a process
  restart.
- **`Decision.user_id` has no real identity/auth backing.**
- **The future review phase needs its own re-entry design** — some way
  to find and resume *this* Decision later, once real time has passed.
  That mechanism does not exist yet (§10).

## 14. Future Backlog

- **Design the Outcome/Evaluation/Learning review re-entry point** — how
  does a person later find a previously-recorded Decision and attach an
  Outcome, then eventually an Evaluation and Learning, to it? This
  requires session/decision persistence and a lookup mechanism that don't
  exist yet. Explicitly the next open question this increment surfaces
  without answering.
- Carried forward, unaffected by this increment: re-evaluating
  `reasoning_link`'s placement and permanence (per explicit product
  direction, not to be revisited until real consumer evidence justifies
  it), a REST API layer for the Core Loop, the shared structured Error
  Contract, and the brittle hard-coded test-count assertion in
  `README.md`/`tests/test_release_candidate.py`.
