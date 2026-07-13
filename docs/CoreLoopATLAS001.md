# ATLAS-001 — Core Loop Skeleton

**Status:** Implemented, pending review.
**Scope:** Prove that one complete Atlas Core Loop reasoning cycle can be executed through the existing architecture — Question → Observation → Interpretation → Hypothesis → Evidence → Conclusion → Decision → Outcome → Evaluation → Learning.
**Depends on:** the four aggregates already built in API-001/003/004/005 (Decision, Observation, Hypothesis, Evidence) — **preserved exactly as they were, zero modifications.**

---

## 1. Purpose

Atlas Foundation's prior increments (API-001 through API-005) each built one
reasoning concept as a fully independent, unlinked aggregate. ATLAS-001 is
the first increment that connects them: it adds the six missing Core Loop
concepts and the minimum machinery required to walk one complete reasoning
cycle from a raised Question to a distilled Learning, without redesigning
or duplicating anything already built.

## 2. The Ten-Step Core Loop, As Implemented

| Step | Concept | Status | Application service |
|---|---|---|---|
| 1 | Question | new | `QuestionService.capture` |
| 2 | Observation | **existing, untouched** | `ObserveFromQuestionService.observe` (reuses `CaptureObservationService`) |
| 3 | Interpretation | new | `InterpretationService.capture` |
| 4 | Hypothesis | **existing, untouched** | `FormHypothesisFromInterpretationService.form` (reuses `HypothesisService`) |
| 5 | Evidence | **existing, untouched** | `CaptureEvidenceFromHypothesisService.capture` (reuses `EvidenceService`) |
| 6 | Conclusion | new | `ConclusionService.capture` |
| 7 | Decision | **existing, untouched** | `CommitDecisionFromConclusionService.commit` (reuses `CaptureDecisionService`) |
| 8 | Outcome | new | `OutcomeService.capture` |
| 9 | Evaluation | new | `EvaluationService.capture` |
| 10 | Learning | new | `LearningService.capture` |

Four of the ten application-service operations are **composite**: they
verify an upstream reference exists, then delegate to the corresponding
protected aggregate's own existing, unmodified application service, and
finally record a bridging Link (§6). The other six are ordinary
capture/get/list-all services matching the shape established by every
prior increment.

## 3. Interpretation vs. Hypothesis

`Hypothesis`'s own existing docstring (API-004) already claims "the
investor's provisional interpretation of reality," so a new
`Interpretation` concept needed an explicit, non-overlapping reason to
exist rather than restating the same idea under a new name.

**Resolution: Interpretation is *anchored*, Hypothesis stays
*unanchored*.**

| | Interpretation (new) | Hypothesis (existing, API-004) |
|---|---|---|
| Answers | "Why does this specific Observation matter?" | "What do I believe, freestanding of any one fact?" |
| Anchor | Mandatory `observation_id` — always a reading of one specific, already-recorded Observation | None — a Hypothesis carries no field tying it to anything |
| Example | "This suggests demand may be accelerating." (in response to a specific capex-guidance Observation) | "Demand for AI infrastructure may be accelerating." |

The provenance link from an Interpretation to the Hypothesis it informed
lives only in `InterpretationHypothesisLink` (§6), never as a field on
`Hypothesis` itself — `Hypothesis`'s existing shape required zero changes.

## 4. Folder and Package Structure

Six new aggregates, each a sibling to the five existing ones, following
the exact established per-aggregate layout:

```
atlas/core/domain/{question,interpretation,conclusion,outcome,evaluation,learning}/
    __init__.py, entity.py, exceptions.py, repository.py, value_objects.py
atlas/core/domain/reasoning_link/          # provisional — see §6
    __init__.py, entity.py, exceptions.py, repository.py, value_objects.py

atlas/core/application/{question,interpretation,conclusion,outcome,evaluation,learning}/
    __init__.py, capture_<name>.py
atlas/core/application/reasoning_link/
    __init__.py,
    observe_from_question.py, form_hypothesis_from_interpretation.py,
    capture_evidence_from_hypothesis.py, commit_decision_from_conclusion.py

atlas/core/infrastructure/persistence/{question,interpretation,conclusion,outcome,evaluation,learning,reasoning_link}/
    __init__.py, table.py, sqlalchemy_repository.py

atlas/core/infrastructure/api/   # UNTOUCHED this increment — no REST layer (§7)

tests/unit/{domain,application,infrastructure/persistence}/{question,interpretation,conclusion,outcome,evaluation,learning,reasoning_link}/
    (mirrors the layer structure above)
```

`git status` confirms this increment is **purely additive**: every changed
path is a brand-new file. `atlas/core/infrastructure/api/app.py` was not
touched, unlike every prior increment — because there is no REST layer
this sprint (§7).

## 5. Aggregate and Value-Object Rationale

Each of the six new aggregates follows the exact minimal shape established
by Observation/Hypothesis/Evidence: `@dataclass(frozen=True)`, a single
`capture()` classmethod with an injectable `clock` (default
`datetime.now(timezone.utc)`), a mandatory `Statement` value object
(non-empty-after-strip, no semantic validation of content), one
investor-supplied timestamp (**offset preserved, never normalized**), a
system `recorded_at` (**always UTC**), and an optional `note`
(blank-normalizes-to-`None`).

| Aggregate | New field beyond id/statement/timestamps/note | Read-only reference to |
|---|---|---|
| `Question` | — (root, no reference) | none |
| `Interpretation` | `observation_id: ObservationId` | `atlas.core.domain.observation.value_objects` |
| `Conclusion` | `evidence_id: EvidenceId` | `atlas.core.domain.evidence.value_objects` |
| `Outcome` | `decision_id: DecisionId` | `atlas.core.domain.decision.value_objects` |
| `Evaluation` | `outcome_id: OutcomeId` | this increment's own `outcome.value_objects` |
| `Learning` | `evaluation_id: EvaluationId` | this increment's own `evaluation.value_objects` |

No `confidence`, `strength`, `tags`, or other speculative fields anywhere
— only what the ten-step cycle strictly needs. `source` was deliberately
**not** added to all six the way `Observation`/`Evidence` have it; only
those two aggregates' own specs asked for it, and adding it elsewhere
would have been unrequested scope expansion.

**Conclusion's cardinality — an explicit, documented simplification, not
the conceptual model.** Conceptually, a Conclusion represents *the output
of the reasoning process* — not merely "a conclusion from one piece of
evidence." For this increment, `Conclusion` carries a single
`evidence_id: EvidenceId`, matching the DoD's literal scope ("one
complete reasoning cycle"). A future increment extending this to
`evidence_ids: tuple[EvidenceId, ...]` (synthesizing multiple Evidence
records) plus a direct `hypothesis_id` is expected, not merely possible —
see Future Backlog (§13).

Every new aggregate's application service is fuller than API-003's
original shape: `capture()` + `get()` + `list_all()` + its own
`<Name>NotFoundError`, matching API-004/005's convention — because every
one of them is needed as a read-only existence-check collaborator by
whatever comes next in the chain.

## 6. reasoning_link — Four Bridge Entities (Provisional, Not a Stable Domain Concept)

**Status: temporary orchestration mechanism.** Walking the ten-step chain
and classifying each edge by whether its *later* (dependent) node is one
of the four protected, unmodifiable aggregates:

1. Question(new) → **Observation(existing)**
2. Observation(existing) → Interpretation(new)
3. Interpretation(new) → **Hypothesis(existing)**
4. **Hypothesis(existing) → Evidence(existing)**
5. Evidence(existing) → Conclusion(new)
6. Conclusion(new) → **Decision(existing)**
7. Decision(existing) → Outcome(new)
8. Outcome(new) → Evaluation(new)
9. Evaluation(new) → Learning(new)

For edges 2, 5, 7, 8, 9 (the later node is new), the established
`DecisionContext.decision_id`-style pattern applies directly: the new
aggregate stores the upstream id as a plain field (§5). For edges 1, 3,
4, 6 (the later node is one of the four **protected** aggregates), that
pattern cannot apply — it always puts the foreign id on the new/later
side, but here the later side is exactly what must not be modified, and
every aggregate in this codebase is insert-only (no UPDATE, ever), so a
"preceding" concept can never be retrofitted with a forward-pointing
field once the "following" concept already exists.

`reasoning_link` (`atlas/core/domain/reasoning_link/`) exists solely to
bridge these four edges:

- `QuestionObservationLink(link_id, question_id, observation_id, linked_at)`
- `InterpretationHypothesisLink(link_id, interpretation_id, hypothesis_id, linked_at)`
- `HypothesisEvidenceLink(link_id, hypothesis_id, evidence_id, linked_at)`
- `ConclusionDecisionLink(link_id, conclusion_id, decision_id, linked_at)`

Each is thinner than the six step aggregates: no investor-supplied
timestamp (the meaningful moment already lives on the downstream entity's
own timestamp), just `linked_at` (always UTC). No `NotFoundError` classes
in this module — links are written and joined-through, never looked up
by id as a primary use case. No uniqueness constraint on any of the
four — none of these four edges is 1:1 the way `DecisionContext:Decision`
is (e.g. a Hypothesis may accrue many Evidence links over time).

**This module is explicitly not a permanent addition to the ubiquitous
language.** It is a structural workaround for one specific constraint
(protected aggregates + insert-only + no relationships), not a modeling
decision about what "linking" means in Atlas's domain. A later iteration
will evaluate whether this bridging responsibility should live inside the
domain model, move up into the application layer as pure in-memory
orchestration (no persisted link records at all), or take some other
shape entirely — this increment deliberately does not prejudge that
outcome. Both the module's own docstrings and this document state that
status explicitly so it is never mistaken for settled architecture.

## 7. Application Service Contract (No REST API This Increment)

The spec's own Deliverables list (Domain, Application services, Repository
interfaces, Tests, Documentation) omits a REST API, and "No UI work unless
required for testing" supports the same reading. This increment therefore
implements **no REST layer** — `atlas/core/infrastructure/api/` and
`app.py` are completely untouched. The whole Core Loop is reachable only
via direct Python application-service calls (exercised by the test suite),
until a follow-up increment adds REST endpoints.

Ten operations, in dependency order:

```python
QuestionService.capture(CaptureQuestionRequest) -> Question
ObserveFromQuestionService.observe(ObserveFromQuestionRequest) -> ObserveFromQuestionResult
InterpretationService.capture(CaptureInterpretationRequest) -> Interpretation
FormHypothesisFromInterpretationService.form(FormHypothesisFromInterpretationRequest) -> FormHypothesisFromInterpretationResult
CaptureEvidenceFromHypothesisService.capture(CaptureEvidenceFromHypothesisRequest) -> CaptureEvidenceFromHypothesisResult
ConclusionService.capture(CaptureConclusionRequest) -> Conclusion
CommitDecisionFromConclusionService.commit(CommitDecisionFromConclusionRequest) -> CommitDecisionFromConclusionResult
OutcomeService.capture(CaptureOutcomeRequest) -> Outcome
EvaluationService.capture(CaptureEvaluationRequest) -> Evaluation
LearningService.capture(CaptureLearningRequest) -> Learning
```

Each `*Result` from a composite service bundles the constructed entity and
its Link — a new pattern (no existing service previously returned more
than one constructed object), adopted so the caller receives both halves
of one atomic step without a second query. The alternative (return just
the entity, let the caller separately query the link repository) is
simpler and was seriously considered; bundling was chosen because the
Link is created as an unconditional side effect of the same operation, not
an independent fact the caller might not want.

**`CommitDecisionFromConclusionRequest` is necessarily heavier than the
other three composite requests** — `Decision.register()` requires
`user_id`, `decision_type`, `subject`, `investment_case`, and
`confidence`, none of which are derivable from a `Conclusion`. This is a
direct consequence of `Decision`'s own existing required fields (API-001),
not scope creep introduced by this increment.

**Error handling — reuse vs. define fresh, applied consistently:** every
composite service's existence check reuses the referenced aggregate's own
`NotFoundError` when one already exists (`HypothesisNotFoundError`,
`EvidenceNotFoundError` — both from API-004/005), and defines a fresh one,
scoped to the consuming module, only when nothing exists to reuse
(`Observation` and `Decision` have no `NotFoundError` of their own, the
same situation `decision_context`/API-002 was in with `Decision`). Net
effect: **`DecisionNotFoundError` now exists as two independently-defined
classes** (`atlas.core.domain.decision_context.exceptions.DecisionNotFoundError`
and `atlas.core.domain.outcome.exceptions.DecisionNotFoundError`) — an
intentional, disclosed naming collision, the same category already
accepted for the legacy `Observation`/`Evidence` collisions in
API-003/005, not an oversight.

## 8. Persistence Design

One table per new aggregate (`questions`, `interpretations`,
`conclusions`, `outcomes`, `evaluations`, `learnings`), each with its own
`MetaData()`, matching every prior increment. Four link tables
(`question_observation_links`, `interpretation_hypothesis_links`,
`hypothesis_evidence_links`, `conclusion_decision_links`) share **one**
`MetaData()` in `reasoning_link`'s own `table.py`, exposed via a single
`create_reasoning_link_tables(engine)` call — the first time this
codebase has grouped multiple tables under one creation function, since
`reasoning_link` is one bounded context housing four small, structurally
identical aggregates, matching the existing "one module = one MetaData"
convention at the module level rather than the individual-table level.

**No SQL `ForeignKey` anywhere** in any of the ten new tables, confirmed
consistent with all five existing modules — every reference is a plain
indexed `String` column. **No `unique=True` anywhere** — confirmed none
of the nine Core Loop edges is 1:1 the way `DecisionContext:Decision` is.

Each of the six new aggregates' `list_all()` follows
`SqlAlchemyHypothesisRepository`'s pattern: fetch ordered by
`recorded_at`, then re-sort in Python on
`(own_timestamp, recorded_at, id.value)`, because the own-timestamp field
preserves an arbitrary offset and a SQL-level `ORDER BY` on it would not
reflect true chronological order. The four link repositories don't need
this — `linked_at` is always UTC, so a plain SQL `ORDER BY` is correct.

All ten new tables share the same physical SQLite file as the existing
five, via the same shared engine (`get_decision_engine` in tests, per the
established convention) — no second database introduced.

## 9. Sequence — The Ten-Step Application-Service Call Chain

Replacing the usual REST sequence diagram (none exists this increment):

```
Investor                         Application layer                          Repositories
   |                                     |                                        |
   |--"What's happening with X?"------->| QuestionService.capture                |
   |                                     |--add(question)------------------------>|
   |                                     |
   |--"I noticed Y"--------------------->| ObserveFromQuestionService.observe
   |                                     |--QuestionRepository.get(question_id)-->|
   |                                     |   [None -> QuestionNotFoundError]
   |                                     |--CaptureObservationService.capture---->| (existing, untouched)
   |                                     |--QuestionObservationLink.capture()
   |                                     |--add(link)------------------------------>|
   |
   |--"That suggests Z"----------------->| InterpretationService.capture
   |                                     |--ObservationRepository.get(...)-------->| (existing, untouched — read only)
   |                                     |   [None -> ObservationNotFoundError]
   |                                     |--add(interpretation)-------------------->|
   |
   |--"So I believe H"------------------>| FormHypothesisFromInterpretationService.form
   |                                     |--InterpretationRepository.get(...)------>|
   |                                     |   [None -> InterpretationNotFoundError]
   |                                     |--HypothesisService.capture------------->| (existing, untouched)
   |                                     |--InterpretationHypothesisLink.capture()
   |                                     |--add(link)------------------------------->|
   |
   |--"Evidence E supports/challenges H"->| CaptureEvidenceFromHypothesisService.capture
   |                                     |--HypothesisRepository.get(...)---------->| (existing, untouched — read only)
   |                                     |   [None -> HypothesisNotFoundError (reused)]
   |                                     |--EvidenceService.capture---------------->| (existing, untouched)
   |                                     |--HypothesisEvidenceLink.capture()
   |                                     |--add(link)-------------------------------->|
   |
   |--"Therefore, my conclusion is C"--->| ConclusionService.capture
   |                                     |--EvidenceRepository.get(...)------------->| (existing, untouched — read only)
   |                                     |   [None -> EvidenceNotFoundError (reused)]
   |                                     |--add(conclusion)---------------------------->|
   |
   |--"I decide D"---------------------->| CommitDecisionFromConclusionService.commit
   |                                     |--ConclusionRepository.get(...)------------->|
   |                                     |   [None -> ConclusionNotFoundError]
   |                                     |--CaptureDecisionService.capture------------>| (existing, untouched)
   |                                     |--ConclusionDecisionLink.capture()
   |                                     |--add(link)----------------------------------->|
   |
   |--"What happened was O"------------->| OutcomeService.capture
   |                                     |--DecisionRepository.get(...)---------------->| (existing, untouched — read only)
   |                                     |   [None -> DecisionNotFoundError]
   |                                     |--add(outcome)------------------------------------>|
   |
   |--"My assessment is V"-------------->| EvaluationService.capture
   |                                     |--OutcomeRepository.get(...)-------------------->|
   |                                     |   [None -> OutcomeNotFoundError]
   |                                     |--add(evaluation)---------------------------------->|
   |
   |--"What I learned is L"------------->| LearningService.capture
   |                                     |--EvaluationRepository.get(...)-------------------->|
   |                                     |   [None -> EvaluationNotFoundError]
   |                                     |--add(learning)-------------------------------------->|
```

Every read against a protected aggregate's repository (`Observation`,
`Hypothesis`, `Evidence`, `Decision`) is a pure `.get()` lookup — none of
them is ever written to by any Core Loop operation. This is the structural
guarantee behind "existing aggregates preserved exactly as they were."

## 10. Core Domain Decision, As Implemented — Verified Structurally

Grep-verified in both directions:

- **Zero new imports into any of the five protected modules'** (`decision`,
  `decision_context`, `observation`, `hypothesis`, `evidence`) domain,
  application, or persistence layers. The only textual matches for Core
  Loop terms inside those modules are pre-existing English-prose docstring
  usages (e.g. `Observation`'s own docstring already said "not an
  interpretation"; `Hypothesis`'s own docstring already said "not an
  Atlas-generated conclusion") — not new code, not new imports.
- `atlas/core/infrastructure/api/app.py` was not modified — confirmed by
  `git status`/`git diff --stat` showing zero changes to any pre-existing
  tracked file. This increment's change set is **100% additive new
  files**.

## 11. Test Summary

286 new tests, regression-clean against the existing suite:

- **Question (39 tests):** domain (11), application (7), persistence (11)
  — the standalone root aggregate, no upstream dependency.
- **Interpretation (39 tests):** domain, application (including the
  Observation-existence-check happy path and rejection, and a
  does-not-write-to-Observation-repository guard), persistence (including
  `list_by_observation_id`).
- **Conclusion (39 tests):** same shape, anchored to Evidence, reusing
  Evidence's own `EvidenceNotFoundError`.
- **Outcome (39 tests):** anchored to Decision; defines a fresh
  `DecisionNotFoundError` (Decision has none of its own).
- **Evaluation (39 tests):** anchored to Outcome, reusing `OutcomeNotFoundError`.
- **Learning (39 tests):** anchored to Evaluation, reusing
  `EvaluationNotFoundError`; the terminal node.
- **reasoning_link (25 tests):** domain (value objects + all four Link
  entities' `capture()`, identity, immutability), persistence (round-trip
  by both ids for all four link types, multi-link-per-upstream-id cases,
  a structural no-foreign-key and no-uniqueness check across all four
  tables).
- **Four composite application services (17 tests):** one test module per
  service, each exercising the happy path (entity + link both created
  correctly), the not-found rejection, a does-not-write-to-upstream-repo
  guard, and link queryability.
- **The end-to-end integration test (10 tests):** one test walking all ten
  steps Question → Learning against a single in-memory SQLite engine,
  asserting every entity and link round-trips by id and every FK field
  points correctly upstream, plus nine negative tests (one per composite/
  anchored step) confirming each not-found case writes nothing.

**Regression:** API-001 through API-005 test modules were run in isolation
and all **315 pass unchanged** (matching the pre-ATLAS-001 count exactly:
243 for API-001–004 + 72 for API-005). Full repository suite: **7,512
passed, 3 skipped** (7,226 pre-existing + 286 new). Scoped lint
(`atlas/core`, `tests/unit`): clean. Whole-repo `ruff check .` count
unchanged at 1,202 pre-existing findings.

## 12. Architectural Decisions

1. **The four protected aggregates required zero modification.** Verified
   both by design (no code was written inside their modules) and
   structurally (grep confirms zero new imports into them).
2. **`reasoning_link` is explicitly provisional**, not a stable domain
   concept — see §6. This is a deliberate, disclosed architectural
   decision, not a placeholder left unexplained.
3. **Composite application services depend on other application
   services** — new territory in this codebase (no prior service
   previously depended on another service instance). Chosen because it
   lets each composite operation reuse an existing aggregate's full,
   already-tested construction logic rather than duplicating it.
4. **`*Result` dataclasses bundle entity + link** for the four composite
   operations — a new return-shape pattern, adopted deliberately (§7) and
   flagged rather than silently introduced.
5. **`Conclusion`'s single-`evidence_id` shape is an explicit
   simplification for this sprint**, not the conceptual model (§5) — a
   Conclusion is understood to represent the output of the reasoning
   process broadly, not merely a reaction to one Evidence record.
6. **`Interpretation` is anchored, `Hypothesis` stays unanchored** (§3) —
   the one genuinely underspecified modeling decision this increment made,
   resolved and disclosed rather than left ambiguous.
7. **No REST API this increment** (§7) — a scoping decision consistent
   with the spec's own Deliverables list, not an oversight.

## 13. Genuine Risks / Unresolved Questions

- **`reasoning_link`'s eventual home is genuinely unresolved.** It may
  belong in the domain model, the application layer as pure in-memory
  orchestration, or some other mechanism entirely once real usage patterns
  emerge — see Future Backlog.
- **`Conclusion`'s single-Evidence cardinality** will need to become
  plural (`evidence_ids`) plus a direct `hypothesis_id` once real
  multi-evidence reasoning is exercised — flagged as expected, not merely
  possible.
- **Two independently-defined `DecisionNotFoundError` classes** now exist
  (`decision_context.exceptions` and `outcome.exceptions`) — intentional,
  same category as already-accepted legacy naming collisions, but worth
  naming again so it isn't mistaken for an oversight.
- **No REST surface exists for any of the ten Core Loop operations** —
  the cycle is currently only executable via direct Python service calls
  (as proven by the test suite), not through any running application.
- **`*Result` dataclasses are a new return-shape pattern** with no prior
  precedent in this codebase to validate against; worth revisiting once a
  second consumer (e.g. a future REST layer) exercises these services.
- **`CommitDecisionFromConclusionRequest`'s heavier shape** (carrying
  `Decision`'s full existing required field set) may feel like an
  awkward seam once a UI/API is built on top of it — flagged for that
  future design, not resolved here.

## 14. Future Backlog

- **Re-evaluate `reasoning_link`'s placement and permanence** — the
  explicit next-iteration question this increment was built to defer,
  not resolve (§6).
- **Extend `Conclusion` to `evidence_ids: tuple[EvidenceId, ...]` plus a
  direct `hypothesis_id`** once real reasoning cycles need to synthesize
  more than one piece of Evidence per Conclusion (§5, §13).
- **Add a REST API layer for all ten Core Loop operations**, once the
  domain model above is confirmed and (if desired) the shared, structured
  Error Contract already deferred from API-004/005's reviews is designed.
- **Revisit the Interpretation/Hypothesis boundary** once real usage
  patterns emerge — the anchored/unanchored distinction (§3) is a
  reasonable first cut, not guaranteed to be the final word.
- Carried forward, unaffected by this increment: the shared structured
  Error Contract and the brittle hard-coded test-count assertion in
  `README.md`/`tests/test_release_candidate.py`, both already recorded as
  open backlog items from API-004/005's reviews.
