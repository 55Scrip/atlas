"""Portfolio Integration (Deliverable 7) -- pure, structural grouping
across holdings. "Ingen ny ranking. Endast förståelse": every function
here only groups already-real facts by exact match; nothing here
scores, ranks, or prioritizes a holding.

Three real, closed groupings, chosen because each is grounded in an
already-real, already-structured field -- no new taxonomy invented:

- **Shared weak assumption**: a `CHALLENGED` Assumption (real status,
  set only by `AssumptionService.challenge` -- "evidence supports or
  challenges an Assumption's underlying claim") whose exact statement
  text (trimmed, case-folded) recurs across more than one holding.
- **Shared condition** (the brief's "makroberoende" -- a shared macro
  dependency): a CaseCondition whose exact predicate text recurs across
  more than one holding. CaseConditions are the one investor-authored,
  free-text object this codebase has that is routinely macro-flavored
  in practice (e.g. "Data center capex growth decelerates below 10%
  YoY") -- there is no separate "macro" taxonomy anywhere in this
  codebase to group by instead (confirmed by this sprint's own
  Dependency Audit), so exact-text recurrence is the only honest,
  non-fabricated signal available.
- **Shared missing evidence**: a `FINDING` node this sprint's own
  `WeaknessKind.NO_SUPPORT` already flagged, grouped by its real
  `FindingKind` value, recurring across more than one holding.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from atlas.alpha.evidence_graph.models import GraphNodeKind, WeaknessKind

if TYPE_CHECKING:
    from atlas.alpha.evidence_graph.service import CaseEvidenceGraph

__all__ = ["SharedWeakPoint", "PortfolioSharedWeakPoints", "find_shared_weak_points"]


@dataclass(frozen=True)
class SharedWeakPoint:
    signature: str
    """The real, exact text/kind two or more holdings share -- never a
    generated summary."""
    case_ids: tuple[str, ...]
    tickers: tuple[str, ...]


@dataclass(frozen=True)
class PortfolioSharedWeakPoints:
    shared_weak_assumptions: tuple[SharedWeakPoint, ...]
    shared_conditions: tuple[SharedWeakPoint, ...]
    shared_missing_evidence: tuple[SharedWeakPoint, ...]


def _normalize(text: str) -> str:
    return " ".join(text.strip().lower().split())


def find_shared_weak_points(
    graphs_by_case: dict[str, CaseEvidenceGraph], ticker_by_case: dict[str, str | None]
) -> PortfolioSharedWeakPoints:
    assumption_groups: dict[str, dict[str, tuple[str, str | None]]] = {}
    condition_groups: dict[str, dict[str, tuple[str, str | None]]] = {}
    missing_evidence_groups: dict[str, dict[str, tuple[str, str | None]]] = {}

    for case_id, built in graphs_by_case.items():
        ticker = ticker_by_case.get(case_id)
        no_support_finding_ids = {
            w.node_id for w in built.weak_dependencies if w.kind is WeaknessKind.NO_SUPPORT
        }

        for node in built.graph.nodes:
            if node.kind is GraphNodeKind.ASSUMPTION and node.details.get("status") == "challenged":
                statement = node.details.get("statement")
                if isinstance(statement, str) and statement.strip():
                    key = _normalize(statement)
                    assumption_groups.setdefault(key, {})[case_id] = (statement.strip(), ticker)

            elif node.kind is GraphNodeKind.CASE_CONDITION:
                predicate = node.details.get("predicate_text")
                if isinstance(predicate, str) and predicate.strip():
                    key = _normalize(predicate)
                    condition_groups.setdefault(key, {})[case_id] = (predicate.strip(), ticker)

            elif node.kind is GraphNodeKind.FINDING and node.id in no_support_finding_ids:
                finding_kind = node.details.get("kind")
                if isinstance(finding_kind, str) and finding_kind:
                    missing_evidence_groups.setdefault(finding_kind, {})[case_id] = (finding_kind, ticker)

    def _to_weak_points(groups: dict[str, dict[str, tuple[str, str | None]]]) -> tuple[SharedWeakPoint, ...]:
        results = []
        for members in groups.values():
            if len(members) < 2:
                continue
            signature = next(iter(members.values()))[0]
            case_ids = tuple(sorted(members.keys()))
            tickers = tuple(sorted({t for _, t in members.values() if t is not None}))
            results.append(SharedWeakPoint(signature=signature, case_ids=case_ids, tickers=tickers))
        return tuple(sorted(results, key=lambda w: w.signature))

    return PortfolioSharedWeakPoints(
        shared_weak_assumptions=_to_weak_points(assumption_groups),
        shared_conditions=_to_weak_points(condition_groups),
        shared_missing_evidence=_to_weak_points(missing_evidence_groups),
    )
