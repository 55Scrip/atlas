# ATLAS-007 — Decision Reflection

**Status:** Implemented, pending review.
**Scope:** The first capability that connects an ongoing, not-yet-recorded decision to the investor's own recognized Patterns and Strategy Signatures — an optional, occasion-bound correspondence, never advice, never persisted. Read-only throughout. Introduces no new domain aggregate, no new persistence.
**Depends on:** ATLAS-007-D's authoritative Decision Reflection definition, and the existing `PatternRecognitionQuery`/`StrategySignatureRecognitionQuery` (ATLAS-005/005B/006), extended with two small, disclosed, additive prerequisites.

---

## 1. Purpose

ATLAS-007-D fixed Decision Reflection as occasion-bound, not a standing
fact like Pattern or Strategy Signature: it connects the investor's
current, in-progress reasoning (not yet a recorded Decision) to their
own already-recognized history, and steps back — descriptive only,
never evaluative, never advice. This increment builds the smallest
capability that draws exactly one such correspondence during a First
Decision Conversation (ATLAS-002).

## 2. Two Prerequisite Findings

**Prerequisite A — `RecognizedPattern` gains `matching_key`.**
`RecognizedPattern` exposed no structured field capturing *what* a
Pattern groups on. Matching an in-progress subject/decision-type against
a specific Pattern had no valid path without one: parsing `description`
would treat a presentation-only field as semantic input (forbidden);
reading Decision Timeline or a Decision directly to recover a grouping
key is explicitly forbidden. `matching_key: tuple[str, ...] = ()` was
added, defaulted for full backward compatibility, and populated by the
two existing strategies from values they already compute internally —
`SameSubjectAndTypeStrategy` → `(subject, decision_type)`,
`SameConfidenceStrategy` → `(str(confidence_value),)`. Deliberately
*not* excluded from equality/hashing: it is a pure function of the same
`(strategy, underlying decisions)` pair that already determines
`member_decision_ids`, so no new distinction is introduced for genuine
data.

**Prerequisite B — `StrategySignatureRecognitionQuery` gains
`recognize(recognized_patterns)`.** A consistency defect was caught
before implementation: `PatternRecognitionQuery.build()` stamps a fresh
`recognized_at` on every call, so calling it once to find a matching
Pattern and again (indirectly, via `StrategySignatureRecognitionQuery.build()`)
would produce `RecognizedPattern` objects that are unequal to the ones
already matched — silently breaking `winning_pattern in
signature.member_patterns` in production. `recognize(recognized_patterns)`
runs strategies over an externally-supplied tuple; `build()` now
delegates through it (`build()`'s own observable behavior is unchanged).

## 3. Recognition Model

```python
@dataclass(frozen=True)
class ReasoningContext:
    subject: str | None = None
    decision_type: str | None = None
    confidence: int | None = None
```
`__post_init__` strips `subject` — mirroring `Subject.__post_init__`'s
own normalization exactly — so it is in precisely the same canonical
form a captured Decision's `Subject.value` will be. `decision_type` and
`confidence` need no equivalent treatment: `prompts.parse_decision_type`
already returns the literal uppercase `DecisionType` values, and
`prompts.parse_confidence` already returns a plain, range-checked `int`.

```python
@dataclass(frozen=True)
class DecisionReflection:
    pattern: RecognizedPattern
    strategy_signature: RecognizedStrategySignature | None
    description: str
    reflected_at: datetime
```
Occasion-bound by nature (ATLAS-007-D §2): never persisted, never
compared across occasions, no "Recognition" split the way Pattern/
Strategy Signature required.

## 4. Correspondence Rule

```python
_MATCHING_KEY_DERIVERS = {
    "same_subject_and_type": lambda ctx: (ctx.subject, ctx.decision_type) if ... else None,
    "same_confidence": lambda ctx: (str(ctx.confidence),) if ... else None,
}
_STRATEGY_PRIORITY = ("same_subject_and_type", "same_confidence")
```
A correspondence exists when the context yields a non-`None` key for
some strategy **and** a `RecognizedPattern` with that exact
`(strategy_name, matching_key)` pair exists in the single
`recognized_patterns` tuple obtained this call. Pure tuple-of-strings
equality — no parsing, no scoring, no thresholds.

## 5. Pattern-Grounded and Strategy-Signature-Grounded Reflection

Pattern Recognition runs **exactly once** per `.reflect()` call. That
one tuple is used both to find the winning Pattern and as the direct
argument to `StrategySignatureRecognitionQuery.recognize(...)` — never
`.build()`. A Signature is attached only because the *same* winning
Pattern is genuinely one of its `member_patterns` (ATLAS-007-D
invariant 14) — never asserted independently. Since a Pattern belongs
to at most one Signature at a time (ATLAS-006-D's partition property),
this lookup is unambiguous.

## 6. Integration Boundary with First Decision Conversation

Verified directly against `conversation/session.py`/`orchestrator.py`:
`ConversationStep.DECISION` covers both decision-type and confidence via
`session.pending["decision_type"]` — no separate step values exist. The
exact moment subject and decision type are both known, confidence not
yet:

```python
session.current_step is ConversationStep.DECISION and "decision_type" in session.pending
```

**Zero changes to `session.py`, `orchestrator.py`, or `prompts.py`.**
`conversation/cli.py` gains its second disclosed touch (the first was
ATLAS-003's shared-engine switch): before the loop, build a
`DecisionReflectionQuery` and call `create_decision_reflection_tables(engine)`
(delegating down to `create_pattern_recognition_tables` →
`create_decision_timeline_tables`, needed since a fresh database may
never have had those tables created); inside the loop, immediately after
`orchestrator.respond(...)`, check the condition above and print the
Reflection if found — **before** `turn.prompt`.

## 7. Presentation and Dismissal Behavior

Printed once, prefixed `"(Reflection) "`, no question, no required
response. The next line printed is always `turn.prompt`, unchanged.
Dismissal is not a tracked action — it is simply answering the next
prompt, which is the same prompt regardless.

## 8. Deterministic Ordering and Selection

At most one `DecisionReflection` per call. `_STRATEGY_PRIORITY` is
checked in fixed order; the first strategy with a derivable key and a
matching Pattern wins. At the one integration point wired up this
increment, confidence is never yet known, so only `same_subject_and_type`
can win in practice — `same_confidence` is fully implemented but dormant
until a future integration point exists after confidence is captured.

## 9. The In-Progress Decision Never Counts Toward Its Own Grounding

`SameSubjectAndTypeStrategy` requires two or more *already-recorded*
Decisions to form any Pattern. The Decision still being reasoned about
has no id and is not persisted, so it cannot appear in
`PatternRecognitionQuery.build()`'s output at the moment `.reflect()`
runs. Concretely, verified by test and manual walkthrough: exactly one
prior matching Decision plus a second, matching, in-progress conversation
yields no Reflection; exactly two prior matching Decisions plus a third
yields one, referencing only the first two.

## 10. Folder Structure

```
atlas/core/application/decision_reflection/
    reasoning_context.py   # ReasoningContext — no ConversationSession coupling
    reflection.py            # DecisionReflection
    query.py                   # DecisionReflectionQuery
    composition.py                # build_decision_reflection_query(engine)

tests/unit/application/pattern_recognition/test_matching_key.py       # Prerequisite A
tests/unit/application/strategy_signature/test_recognize_method.py    # Prerequisite B
tests/unit/application/decision_reflection/test_query.py
tests/unit/application/conversation/test_decision_reflection_integration.py
```

No standalone `decision_reflection` CLI — a Reflection has no meaning
detached from an actual ongoing reasoning context.

## 11. Test Summary

15 new tests, regression-clean:

- **`test_matching_key.py`** (4) — default backward compatibility (two
  patterns without `matching_key` remain equal/hashable-consistent);
  `SameSubjectAndTypeStrategy`'s and `SameConfidenceStrategy`'s
  `matching_key` values, verified against real recorded Decisions.
- **`test_recognize_method.py`** (2) — `recognize()` given a
  self-obtained snapshot matches `build()`'s own output; `recognize()`
  never calls `PatternRecognitionQuery.build()` (a spy raises if it
  does).
- **`decision_reflection/test_query.py`** (8) — no correspondence (empty
  context, no Decisions, exactly one prior matching Decision); Pattern-
  grounded (with canonicalization of whitespace); Strategy-Signature-
  grounded (reusing ATLAS-006's three-Pattern chain, proving invariant 14
  and the single-pass identity guarantee via `is`, not just `==`);
  deterministic priority selection; a runtime "never writes" spy across
  the full dependency chain.
- **`conversation/test_decision_reflection_integration.py`** (1) — the
  same scripted seven-answer conversation run twice (with and without a
  firing Reflection) yields an identical `turn.prompt` sequence and
  identical captured Decision fields.
- **Manual verification:** three First Decision Conversation CLI runs
  sharing one `ATLAS_HOME` (NVIDIA/BUY/90, NVIDIA/BUY/70, then a third
  NVIDIA/BUY conversation) — confirmed no Reflection during the second
  conversation (only one prior Decision recorded) and the Reflection
  firing during the third, immediately after decision type was captured
  and before confidence was asked.

**Regression:** full repository suite: **7,603 passed, 3 skipped**
(7,588 pre-existing + 15 new). Scoped lint: clean. Whole-repo `ruff
check .` count unchanged at 1,202. `git diff --stat` confirms the only
existing files touched are `recognized_pattern.py`, `strategies.py`
(pattern_recognition), `query.py` (strategy_signature), and
`conversation/cli.py` — everything else purely additive.

## 12. Architectural Decisions

1. **`matching_key` on `RecognizedPattern`**, additive and
   backward-compatible, rather than parsing `description` or reading
   Decision Timeline directly — the only path consistent with existing
   invariants and this brief's explicit prohibitions.
2. **`recognize(recognized_patterns)` on `StrategySignatureRecognitionQuery`**,
   with `build()` delegating through it — the smallest fix ensuring
   Pattern Recognition runs exactly once per Reflection.
3. **A CLI-level side-channel integration**, not a Core Loop change —
   `session.py`/`orchestrator.py`/`prompts.py` remain untouched;
   `conversation/cli.py` reads only already-public session state.
4. **Exactly one Reflection per occasion**, deterministically selected
   by a fixed strategy priority — smallest surface area sufficient to
   prove the capability.
5. **No standalone CLI for Decision Reflection** — it has no meaning
   without a real, ongoing reasoning context to attach to.
6. **No persistence** — a Reflection is recomputed fresh every time and
   never distinguishes "seen" from "never triggered."

## 13. Anything That Feels Overengineered

Nothing beyond the two disclosed prerequisites, both minimal and
narrowly scoped. `_STRATEGY_PRIORITY`/`_MATCHING_KEY_DERIVERS` fully
specify `same_confidence` even though it cannot fire yet at this
increment's one integration point — deliberate, so a future integration
point doesn't require revisiting this module, not speculative scope
creep.

## 14. What Can Be Simplified

Nothing at this stage. The most likely future growth points (a second
integration point once confidence is known, additional Pattern
strategies feeding richer correspondences) are deliberately deferred.

## 15. Genuine Risks / Unresolved Questions

- **Two already-shipped, tagged modules were touched** (ATLAS-005/005B's
  `recognized_pattern.py`/`strategies.py`, ATLAS-006's `query.py`) —
  both additive and backward-compatible, confirmed by full regression,
  but a real, disclosed fact about this increment's footprint.
- **Correspondence coverage is limited to two dimensions** (subject+type,
  confidence) and **one integration point** (before confidence is known)
  — a confidence-grounded Reflection cannot fire yet.
- **No persistence** — nothing distinguishes an investor having seen a
  Reflection from never having triggered the condition.
- **No authentication** — same placeholder-identity gap disclosed in
  every prior increment.

## 16. Future Backlog

- A second integration point later in the conversation (after
  confidence is captured), activating the already-implemented
  `same_confidence` correspondence.
- Additional Pattern strategies (reasoning-language, review-completion,
  learning-recurrence) feeding richer Reflection correspondences once
  they exist.
- Carried forward, unaffected by this increment: re-evaluating
  `reasoning_link`'s placement and permanence, a REST API layer for the
  Core Loop, the shared structured Error Contract, the brittle
  hard-coded test-count assertion in `README.md`/`tests/test_release_candidate.py`.
- **Recommendation for the next sprint:** with Decision Reflection now
  connecting live reasoning to recorded history, the natural next step
  is product direction on whether/how a future coaching capability
  should respond to a Reflection — explicitly out of scope here and
  deferred, per ATLAS-007-D §9.
