"""Investment Case Lifecycle & Atlas Status (Investment Case Redesign,
Implementation Phase 1).

Introduces the single backend source of truth for where an Investment
Case currently stands -- `COMPANY_ADDED` / `DATA_COLLECTION` /
`ANALYSIS_RUNNING` / `PUBLISHED` / `CONTINUOUS_MONITORING` -- and the
Mandatory Core evaluation (`M1 AND M2 AND M3 AND M4`, each with OR
logic over existing evidence paths) that gates Publication. Reuses
`atlas.analysis_engine`'s own already-real signals (Growth, Capital
Allocation, Financial Risk, the four Risk categories, Valuation,
Business/Market records) and `atlas.alpha.monitoring`'s own
`CaseOperationalFreshness` -- no new analytical engine, no second
identity system, no duplicated Decision Layer logic.

Deliberately additive and observation-only this phase: nothing here
changes what the Investment Case page renders, hides any section, or
alters attention-system semantics. See this package's own `engine.py`
for the deterministic specification this implements (Investment Case
Lifecycle Specification, Phase 3) and `service.py` for exactly which
existing services this reads from (read-only) and what it persists
(only its own regression-detection history, mirroring
`atlas.alpha.decision_readiness`'s own result-table pattern).
"""
