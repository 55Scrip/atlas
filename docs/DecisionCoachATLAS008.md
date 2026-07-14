# ATLAS-008 — Decision Coach

**Status:** Implemented, pending review.
**Scope:** A bounded, question-only engagement with one already-produced Decision Reflection — at most one fixed, pre-verified question, with a genuine (ephemeral) response opportunity, never advice, never persisted. No infrastructure layer of its own.
**Depends on:** ATLAS-008-D's authoritative Decision Coach definition, and `DecisionReflection` (ATLAS-007), reused unmodified as Coach's sole input.

---

## 1. Purpose

ATLAS-008-D fixed Decision Coach as the most conversational capability
Atlas has built: a bounded exchange that helps an investor inspect a
Decision Reflection they've already been shown, by asking — never
telling. This increment builds the smallest implementation of that:
exactly one fixed, pre-verified question, dispatched purely on the
Reflection's own shape, with a real (if ephemeral) opportunity for the
investor to respond.

Two corrections were made to the first draft before implementation,
both because the initial design did not yet satisfy the domain
definition:

1. **Coach's own utterance must contain no restated fact.** The first
   draft interpolated `pattern.description`/`strategy_signature.description`
   into the question text — a statement followed by a question, not a
   question. Decision Reflection has already shown that content one line
   above; Coach's questions now reference it only implicitly ("compared
   to *that*"), never repeat it.
2. **A genuine, bounded response opportunity was missing.** Printing
   Coach's question immediately before the existing confidence prompt,
   with no dedicated input turn, would let one `input()` call answer two
   different questions — if the investor responded to Coach, that text
   would be silently rejected as an invalid confidence value. One
   additional, discarded `input()` call was added between Coach's
   question and the real confidence prompt.

## 2. Coaching Input Model

No new input type: Decision Coach's sole input is `DecisionReflection | None`
(ATLAS-007), reused as-is. Everything Coach may reference — `pattern`,
`strategy_signature` — is already fully enumerated there
(ATLAS-008-D invariant 8); introducing a parallel context object would
risk letting Coach see more than Reflection already scoped.

```python
@dataclass(frozen=True)
class CoachingQuestion:
    text: str
    reflection: DecisionReflection
```

`text` contains only the question — no interpolated description.
`reflection` is retained purely for traceability (invariant 9). Not a
domain aggregate: never persisted, occasion-bound exactly as
`DecisionReflection` is.

## 3. Question-Selection Rule

Two fixed templates, containing no restated content, dispatched purely
on whether `reflection.strategy_signature is None`:

```python
_PATTERN_ONLY_QUESTION = (
    "What's similar or different about this situation compared with what "
    "you just saw, if anything?"
)
_SIGNATURE_QUESTION = (
    "What's similar or different about this situation compared with the "
    "broader connection you just saw, if anything?"
)
```

**Verification, performed at design time, never at runtime:**
- **Either-answer test (invariant 10):** "similar *or* different" — two
  symmetric, equally-weighted directions, neither foregrounded — plus a
  trailing "if anything," which explicitly permits a third, equally
  valid answer: no meaningful correspondence at all.
- **No-hidden-conclusion (invariant 16):** no evaluation, recommendation,
  presumed concern, or expected answer — and no restated fact, since
  "what you just saw"/"the broader connection you just saw" refers back
  to what Decision Reflection already displayed immediately beforehand.
  A Strategy Signature is never called a "pattern" here, avoiding
  conflation of the two distinct domain concepts.

Dispatch is the only variable — never how either string is worded.
Neither template ever references the investor's own free-text answers,
which would require semantic inference this increment does not perform.

## 4. Pattern-Grounded Question

`reflection.strategy_signature is None` → `_PATTERN_ONLY_QUESTION`,
verbatim.

## 5. Strategy-Signature-Grounded Question

`reflection.strategy_signature is not None` → `_SIGNATURE_QUESTION`,
verbatim — acknowledging, in fixed wording only, that a Signature
rather than a single Pattern is in view. Relevance is inherited entirely
from `DecisionReflection` (ATLAS-007-D invariant 14); Coach performs no
independent relevance check.

## 6. Silence Conditions

Two distinct, valid "nothing happens" outcomes:
1. **`reflection is None`** — the overwhelming majority of occasions.
2. **The investor does not engage** with the ephemeral response
   opportunity — pressing Enter, typing something, or typing nothing are
   all read once and discarded identically.

Other domain-level silence conditions (declining to interpret if asked;
not following up) hold structurally: this module has no mechanism to
ever read the ephemeral response's content, so there is no follow-up to
suppress.

## 7. Integration Boundary — A Genuine Bounded Exchange

`conversation/cli.py`'s existing ATLAS-007 integration point is extended
into a five-step, CLI-level-only sequence:

```python
def _maybe_reflect_and_coach(decision_reflection_query, session, input_fn=input):
    if not (session.current_step is ConversationStep.DECISION and "decision_type" in session.pending):
        return
    reflection = decision_reflection_query.reflect(context)
    if reflection is None:
        return
    print(f"(Reflection) {reflection.description}")
    coaching_question = select_coaching_question(reflection)
    print(f"(Coach) {coaching_question.text}")
    print("(You may respond, or press Enter to continue.)")
    input_fn("> ")  # read once, discarded unconditionally
```

1. The Reflection is shown.
2. Coach asks exactly one question.
3. The investor receives one optional, ephemeral response opportunity —
   a single `input_fn("> ")` call, injectable for testing exactly as
   `clock` is injected elsewhere in this codebase.
4. That response is read and discarded in the same call — never
   persisted, interpreted, evaluated, classified, or acted on.
5. Control returns to the loop, which prints the real confidence prompt
   and captures the real confidence answer via its own next `input()`,
   uncontaminated.
6. Silence or skipping is valid and consequence-free.

**Zero changes to `session.py`, `orchestrator.py`, or `prompts.py`** —
`ConversationSession`/`ConversationStep` gain no new state; the
ephemeral input is never passed to `ConversationOrchestrator.respond()`,
provably not a new Core Loop step. This is `conversation/cli.py`'s third
disclosed touch (ATLAS-003's engine switch, ATLAS-007's Reflection hook,
now this).

## 8. Presentation and Non-Engagement Behavior

Three lines print when a Reflection fires: the Reflection, Coach's
question, and a short instruction — `"(You may respond, or press Enter
to continue.)"`. The investor's line there is read once and discarded
regardless of content; the next thing printed is always the real
confidence prompt. No acceptance, dismissal, or refusal state exists —
only "a line was read," which carries no meaning anywhere.

## 9. Deterministic Ordering

Trivial: at most one `CoachingQuestion`, never a sequence — one
Reflection (already resolved by ATLAS-007), one boolean template check,
no ranking, no randomness.

## 10. Folder Structure

```
atlas/core/application/decision_coach/
    coaching_question.py   # CoachingQuestion
    coach.py                  # fixed templates + select_coaching_question(reflection)

tests/unit/application/decision_coach/test_coach.py
```

No infrastructure layer — no `Engine`, no composition root, no
repository import anywhere in this module, per ATLAS-008-D's explicit
prohibition on independent querying.

## 11. Test Summary

8 new/updated tests, regression-clean:

- **`test_coach.py`** (7) — no Reflection yields no question; template
  dispatch (Pattern-only vs. Signature-grounded) is the only thing that
  varies; Coach's text never contains a substring of
  `pattern.description`/`strategy_signature.description` (the mechanical
  proof of "no restated fact"); the either-answer/no-hidden-conclusion
  verification documented as durable test assertions; traceability
  (`question.reflection is reflection`).
- **`conversation/test_decision_reflection_integration.py`** (updated,
  +1) — the same scripted seven-answer conversation, run with an
  injected `input_fn`, proves: `input_fn` is never called when no
  Reflection fires; it is called exactly once when one does; its return
  value has no effect on session state or captured Decision fields;
  `turn.prompt` sequences are identical with and without a firing
  Reflection/Coach question.
- **Manual verification:** the same ATLAS-007 three-conversation
  scenario, extended with one scripted line for the ephemeral response
  during the third conversation — confirmed the full sequence (Reflection
  → Coach question → instruction → discarded input → real confidence
  prompt/answer) behaves exactly as designed.

**Regression:** full repository suite: **7,611 passed, 3 skipped**
(7,603 pre-existing + 8 new). Scoped lint: clean. Whole-repo `ruff check
.` count unchanged at 1,202. `git diff --stat` confirms the only
existing files touched are `conversation/cli.py` (the disclosed
integration point) and `conversation/test_decision_reflection_integration.py`
(updated to match the renamed/extended integration function) —
everything else purely additive.

## 12. Architectural Decisions

1. **No interpolated content in Coach's own utterance** — every Coach
   line is functionally a question, satisfying ATLAS-008-D's central
   requirement literally.
2. **A genuine, discarded `input_fn` call** rather than no input
   mechanism at all — the smallest fix that gives the investor a real,
   separate opportunity without ever engaging `ConversationOrchestrator`.
3. **Zero infrastructure layer** for Decision Coach — its only input is
   an already-computed `DecisionReflection`; no Engine, no composition
   root, enforced structurally.
4. **Two wholly fixed templates**, verified once at design time against
   invariants 10 and 16 — never generated or checked per-occasion, since
   this system performs no semantic inference.
5. **`conversation/cli.py`'s third disclosed touch** — tracked explicitly
   rather than treated as incidental.

## 13. Anything That Feels Overengineered

Nothing. The module is two small files with no dependencies beyond
`DecisionReflection` itself.

## 14. What Can Be Simplified

Nothing further at this stage.

## 15. Genuine Risks / Unresolved Questions

- **The ephemeral response opportunity adds one required line of input**
  whenever a Reflection fires, in tests and manual walkthroughs alike —
  disclosed, not hidden.
- **No mechanism exists to ever read the ephemeral response's content**
  — by design, but this means the richer, content-aware coaching style
  ATLAS-008-D itself illustrates (referencing the investor's own stated
  reasoning) remains out of reach until a future increment explicitly
  authorizes controlled reference to investor-authored text.
- **`conversation/cli.py` has now been touched three times** across the
  project's history — still additive each time, worth continuing to
  name explicitly.
- **No persistence** — ephemeral, consistent with every prior increment
  in this vein.
- **No authentication** — same placeholder-identity gap disclosed in
  every prior increment.

## 16. Future Backlog

- A richer, content-aware coaching question style referencing the
  investor's own prior answers — would require its own explicit
  authorization and review of the semantic-inference boundary.
- A second integration point once `same_confidence`-grounded Reflections
  can fire (ATLAS-007's own deferred future work).
- Carried forward, unaffected by this increment: re-evaluating
  `reasoning_link`'s placement and permanence, a REST API layer for the
  Core Loop, the shared structured Error Contract, the brittle
  hard-coded test-count assertion in `README.md`/`tests/test_release_candidate.py`.
- **Recommendation for the next sprint:** product direction on whether
  Decision Coach's ephemeral response should ever become readable —
  the explicit, hard boundary this increment holds — before any future
  capability is scoped in that direction.
