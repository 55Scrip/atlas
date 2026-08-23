# ADR-CC-001 Conformance Report — CaseCondition

**Sprint 7 — Architecture Conformance Review.** Audits `docs/ADR-CC-001-CaseCondition.md` (Accepted) against the repository, including `atlas/monitoring/` (the object this ADR explicitly requires be left untouched).

**Overall Conformance: Not Implemented**

---

## Finding 1 — No `CaseCondition` or `CaseConditionEvent` object exists anywhere

- **Conformance:** Not Implemented.
- **Evidence:** A repository-wide, case-sensitive grep for `CaseCondition` returns zero matches. No domain directory, migration, API router, or test references it.
- **Severity:** High. `CaseCondition` is one of the two largest new domain concepts this program has adopted (alongside `Assumption`), and both UX-008's Monitoring/Invalidation Conditions and UX-009's Review Plan depend structurally on it.
- **Recommendation:** Larger implementation project.
- **Ownership:** Backend, API, UI.
- **Dependencies:** Benefits from, but does not strictly require, `ADR-DD-001` (`DecisionDraft`) existing first, per this ADR's own §7 (condition content may originate as draft content) — `ADR-DD-001` is itself Not Implemented (see that report), so building `CaseCondition` first and having it originate content directly at Decision-commit time, without a draft stage, remains a fully valid interim path per §7's own wording ("may originate," not "must").

## Finding 2 — `atlas/monitoring` is confirmed genuinely untouched, exactly as this ADR requires

- **Conformance:** Fully Implemented (of the negative constraint).
- **Evidence:** `atlas/monitoring/` contains exactly `engine.py` (634 lines), `__init__.py` (17 lines), unchanged in file size and structure from what `Investigation-005` Phase 2 originally documented. No new persistence, no `Decision`/`Case` reference, no threshold/predicate concept has been added to it. This is a rare case where a negative architectural constraint ("keep this fully separate — not reused, not extended, not wrapped, not replaced") is directly, positively verifiable, and holds.
- **Severity:** Informational.
- **Recommendation:** No action.
- **Ownership:** Architecture.
- **Dependencies:** None.

## Finding 3 — No `_is_thesis_stale`-style condition has been generalized into anything resembling `CaseCondition`

- **Conformance:** Not Implemented (confirms the gap, not a new finding).
- **Evidence:** `atlas/alpha/investment_case/service.py`'s own `_is_thesis_stale` (cited throughout the source Investigations as existing, working, time-based-staleness precedent) remains exactly what it was — a fixed, hardcoded `VERY_OLD_CASE_THRESHOLD_DAYS = 90` computation, not backed by any persisted, investor-authored condition object. This is consistent with the ADR's own Migration section ("None to existing code"), not a violation — flagged here only to confirm the precedent this ADR builds on has not itself silently evolved into a substitute.
- **Severity:** Low.
- **Recommendation:** No action — worth a forward pointer for whoever eventually implements Finding 1: `_is_thesis_stale` is a natural first migration target once time-based `CaseCondition`s exist, but migrating it is not required by this ADR.
- **Ownership:** Backend.
- **Dependencies:** Depends on Finding 1.

## Finding 4 — Daily Brief has no `CaseCondition`-sourced projection, correctly, since there is nothing yet to project

- **Conformance:** Not Implemented (vacuously consistent with the ADR's own Migration clause).
- **Evidence:** No Daily Brief code path references conditions, monitoring, or invalidation signals of any kind.
- **Severity:** Informational.
- **Recommendation:** No action now; revisit once Finding 1 is implemented, to confirm §8's narrow-projection boundary is honored from the start.
- **Ownership:** API, UI.
- **Dependencies:** Depends on Finding 1.

---

## Synthesis

Like `ADR-DD-001`, this is architecture awaiting a first implementation, not a drifting or violated one. The one genuinely positive, actively-maintained conformance point is `atlas/monitoring`'s continued isolation — a negative constraint that would be easy to quietly violate (e.g., by "just adding a `case_id` field" to `MonitoringSnapshot`) and has not been.
