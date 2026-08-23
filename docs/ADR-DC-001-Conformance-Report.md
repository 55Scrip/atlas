# ADR-DC-001 Conformance Report — Decision Context

**Sprint 7 — Architecture Conformance Review.** Audits `docs/ADR-DC-001-Decision-Context.md` (Accepted) against `atlas/core/domain/decision_context/`, `atlas/core/application/decision_context/`, `atlas/core/infrastructure/persistence/decision_context/`, `atlas/core/infrastructure/api/decision_context/`, and related tests.

**Overall Conformance: Partially Implemented**

---

## Finding 1 — The domain object matches the ADR's own field set exactly

- **Conformance:** Fully Implemented.
- **Evidence:** `atlas/core/domain/decision_context/entity.py`: `DecisionContext` carries exactly `situation`, `portfolio_relevance`, `capital_considerations`, `alternatives_considered`, `uncertainties`, plus `decision_id`, `context_id`, `captured_at`, `recorded_at` — matching Decision §1 field-for-field, with no field added or removed. The dataclass is `frozen=True`; only a `capture()` classmethod constructs instances, no update method exists — directly satisfies Decision §2's "MUST NOT absorb... anything with a lifecycle after Decision recording."
- **Severity:** Informational.
- **Recommendation:** No action.
- **Ownership:** Backend.
- **Dependencies:** None.

## Finding 2 — At-most-one-per-Decision is enforced at both application and database layers

- **Conformance:** Fully Implemented.
- **Evidence:** `atlas/core/application/decision_context/capture_decision_context.py` checks `self._contexts.get_by_decision_id(decision_id) is not None` before constructing a new context and raises `DuplicateDecisionContextError`. `atlas/core/infrastructure/persistence/decision_context/sqlalchemy_repository.py`'s own docstring states the `decision_id` column carries a database-level `UNIQUE` constraint, translated back to the same domain exception on `IntegrityError`. Matches the ADR's own Invariants exactly.
- **Severity:** Informational.
- **Recommendation:** No action.
- **Ownership:** Backend.
- **Dependencies:** None.

## Finding 3 — A full REST API for DecisionContext already exists — the ADR's own Implementation Note understates current reality

- **Conformance:** Fully Implemented (exceeds what the ADR itself required, since the Implementation Note is explicitly non-binding).
- **Evidence:** `atlas/core/infrastructure/api/decision_context/router.py` implements `POST /decisions/{decision_id}/context` and `GET /decisions/{decision_id}/context`, fully wired through `dependencies.py`, with dedicated `errors.py` HTTP-error mapping and `schemas.py` camelCase request/response models per `ADR-004`. This is not hypothetical future work — it is complete, tested (`tests/unit/infrastructure/api/decision_context/`), and already committed. The ADR's own "Implementation Note (non-binding)" describes this as something that "could" be built, as if it did not yet exist.
- **Severity:** Low. Not a conflict with the ADR's substance (the API is additive, wiring-only, exactly as the Note anticipates) — but the ADR text is factually stale about what already exists.
- **Recommendation:** ADR clarification — update the Implementation Note to state the API endpoint already exists at the `atlas/core` layer, and that what remains is Alpha's own frontend consumption of it (Finding 4).
- **Ownership:** Architecture (documentation fix only).
- **Dependencies:** None.

## Finding 4 — Alpha does not yet consume this API

- **Conformance:** Not Implemented (for the product-facing goal, though correctly out of this ADR's own binding scope).
- **Evidence:** No reference to `decision_context` or `DecisionContext` was found anywhere under `atlas/alpha/` or in frontend code; the only unrelated hit was an identically-named field in `atlas/alpha/watchlist/exceptions.py`. This matches the ADR's own Context section, inherited from `Investigation-001`, which already stated `DecisionContext` was "unwired to Alpha" — this finding confirms that premise remains accurate, not a new gap.
- **Severity:** Medium — real product incompleteness (UX-009's richer decision-time context capture is not yet reachable by an investor), but explicitly not something this ADR itself commits to building.
- **Recommendation:** Larger implementation project, if and when prioritized — wire the existing endpoint into the Decision Workspace UI and Alpha's own investment-case flow.
- **Ownership:** API, UI.
- **Dependencies:** None blocking — the backend is ready.

## Finding 5 — A second, unrelated `DecisionContext` class already exists in production code

- **Conformance:** Conflicts With Implementation (naming, not ontology).
- **Evidence:** `atlas/decision/decision_context.py` defines a second, structurally unrelated `DecisionContext` dataclass — `market_regime`, `portfolio`, `watchlist`, `historical_memory`, `investment_horizon`, `risk_profile`, `available_capital`, `cash_reserve_status`, `comparison_tickers` — an input bundle for `atlas/decision/decision_engine.py`'s own decision-support computation, predating (per `git log`) the ADR's own `DecisionContext` aggregate (added later under `atlas/core`, commit `99088da`). This is the same word used for two structurally unrelated concepts in the same codebase — a real, previously-undocumented naming collision, not caught by any Investigation in this series (which found and disclosed the analogous "Reflection," "Evaluation," and "Assumption"/`OutlookAssumption` collisions, but never checked "DecisionContext" itself against the legacy `atlas/decision/` package).
- **Severity:** High. Unlike `OutlookAssumption` (disclosed and accepted as a known, managed risk), this collision was never surfaced anywhere in the ADR series and carries real, current import-confusion risk: `from atlas.decision.decision_context import DecisionContext` and `from atlas.core.domain.decision_context.entity import DecisionContext` are both valid, live imports today.
- **Recommendation:** ADR clarification in the near term (disclose the collision explicitly, the same discipline already applied to `OutlookAssumption`); a small implementation change (rename the legacy `atlas/decision/decision_context.py` class, e.g. to `DecisionSupportContext`) as a follow-up, since it is the newer, ADR-governed object that should keep the name UX-008/UX-009 actually use.
- **Ownership:** Backend, Architecture.
- **Dependencies:** None.

---

## Synthesis

`ADR-DC-001`'s domain and API layers are fully and correctly implemented, tested, and — on the domain object's own terms — exceed what the ADR itself required. The two real gaps are outside the domain object's own correctness: Alpha still doesn't consume the API (a known, disclosed, non-blocking limitation), and a genuine, previously unrecognized naming collision exists between the ADR's own `DecisionContext` and an older, unrelated class of the same name still in active use.
