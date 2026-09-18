"""A diagnostic rendering of the strategy graph.

Debug surface, not product UI. Prose exists here and nowhere else in
this package, and it is a renderer over structure -- every line is a
field, and no line says anything the graph does not hold. Status is
printed on every row on purpose: a reader must never have to guess
whether they are looking at something management said or something Atlas
put together.
"""
from __future__ import annotations

from atlas.analysis_engine.strategy.contracts import EvidenceStatus, StrategyNodeKind
from atlas.analysis_engine.strategy.models import CompanyStrategy, CrossCompanyAdjacency

__all__ = ["render_company_strategy", "render_adjacency"]

_ORDER = (
    StrategyNodeKind.ECONOMIC_ENGINE,
    StrategyNodeKind.OBJECTIVE,
    StrategyNodeKind.INITIATIVE,
    StrategyNodeKind.RESOURCE_COMMITMENT,
    StrategyNodeKind.DEPENDENCY,
    StrategyNodeKind.EXPECTED_OUTCOME,
    StrategyNodeKind.SUCCESS_CONDITION,
    StrategyNodeKind.FAILURE_MODE,
)


def render_company_strategy(strategy: CompanyStrategy, *, evidence_lines: int = 1) -> tuple[str, ...]:
    lines = [f"STRATEGY  {strategy.company}", f"  composed by {strategy.extractor_version}"]
    for kind in _ORDER:
        nodes = strategy.of_kind(kind)
        if not nodes:
            continue
        lines.append("")
        lines.append(f"  {kind.value.upper().replace('_', ' ')}")
        for node in nodes:
            periods = ",".join(node.observed_periods) or "no period"
            lines.append(
                f"    [{node.status.value}] {node.subject_text}"
                f"  ({periods}; {node.continuity.value})"
            )
            if node.derivation_rule:
                lines.append(f"        rule: {node.derivation_rule}")
            for item in node.supporting[:evidence_lines]:
                who = item.speaker_title or "unattributed"
                lines.append(f'        {item.source_period} {who}: "{item.source_text[:130]}"')
                lines.append(f"        source: {item.source_record_id}")
            if node.contradicting:
                for item in node.contradicting[:evidence_lines]:
                    lines.append(f'        CONTRADICTED BY: "{item.source_text[:120]}"')
    if strategy.edges:
        lines.append("")
        lines.append("  RELATIONS")
        for edge in strategy.edges:
            rule = f"  rule: {edge.derivation_rule}" if edge.derivation_rule else ""
            lines.append(f"    [{edge.status.value}] {edge.source_id} --{edge.relation.value}--> {edge.target_id}{rule}")
    if strategy.unknowns:
        lines.append("")
        lines.append("  NOT RECOVERED FROM THIS CORPUS")
        for unknown in strategy.unknowns:
            lines.append(f"    [{EvidenceStatus.UNKNOWN.value}] {unknown}")
    return tuple(lines)


def render_adjacency(adjacency: CrossCompanyAdjacency) -> tuple[str, ...]:
    lines = [
        f"[{adjacency.status.value}] {adjacency.factor.value}",
        f"    {adjacency.requiring_company} requires | {adjacency.building_company} builds capacity in",
        f"    rule: {adjacency.derivation_rule}",
        f"    may conclude: {adjacency.may_conclude}",
    ]
    lines.extend(f"    may NOT conclude: {claim}" for claim in adjacency.may_not_conclude)
    return tuple(lines)
