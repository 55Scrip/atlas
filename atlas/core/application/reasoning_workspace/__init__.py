"""The Reasoning Workspace orchestration layer (Sprint 12).

Not a new aggregate, not a new ontology concept — introduces zero new
domain entities, zero new tables, zero new event types. This package
composes `Decision`, `DecisionContext`, `DecisionDraft`, `Assumption`,
and `CaseCondition` — every one of them already fully implemented
(ADR-DD-001/CC-001/AS-001, Sprints 9-11) — by calling their own,
completely unmodified application services. Every read/write in this
package flows through an existing service's own public method; nothing
here talks to a repository or a domain entity's own construction path
that isn't already exposed by one of those five services'/two
repositories' own public interface.

See `docs/ReasoningWorkspace-Implementation-Report.md` for the full
account of what is, and is not, introduced here.
"""
