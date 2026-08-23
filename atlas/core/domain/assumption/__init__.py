"""The Assumption aggregate (ADR-AS-001).

See `docs/ADR-AS-001-Assumption.md` for the governing architecture.
Implementation follows `CaseCondition`'s own already-shipped
conventions (ADR-CC-001, Sprint 10) directly, per ADR-AS-001 §10's own
explicit instruction to reuse that event-stream pattern rather than
inventing a new one.
"""
