"""Scenario Analysis v1 (ATLAS-024, Phase 8) -- real, tested structure;
honestly `INSUFFICIENT_INPUT` for all three scenarios this sprint.

**Why fabricating BEAR/BASE/BULL values is refused.** Studied
`atlas/value_scenario/schema.py` as prior art (confirmed unreachable
from the live app, same legacy tree every prior sprint's audit already
found) -- its own stated principle, "Atlas should help users understand
possible value ranges, not pretend to know the future," is exactly
right, and this module follows it without importing any of that
package's code. A real BEAR/BULL scenario requires a *forward*
assumption (a growth rate, a discount rate, a terminal multiple) --
Phase 8's own rule is that "a scenario cannot silently create
assumptions... every assumption must either come from canonical data,
be explicitly supplied, or be marked unavailable." Atlas has no
canonical source for a forward growth-rate assumption today, and this
sprint builds no UI for an investor to explicitly supply one --
`ValuationAssumptionKind` (`contracts.py`) names the assumption types a
future input mechanism would supply, reserved and unconstructed, so
this module needs no shape change when that mechanism exists.

`build_scenario_findings` is real, deterministic, and tested -- it is
not a stub standing in for unfinished work. It genuinely proves the
structure end-to-end (three named `ValuationFinding`s, one per
`ValuationMethodKind` scenario member, each carrying
`ValuationDataGapKind.MISSING_SCENARIO_ASSUMPTIONS`); what remains
unbuilt is *only* the future assumption-supply mechanism, named
explicitly rather than hidden.
"""
from __future__ import annotations

from datetime import datetime

from atlas.analysis_engine.provenance import Consumer, Provenance, SourceKind, UpdateTrigger
from atlas.analysis_engine.valuation.contracts import (
    ValuationDataGapKind,
    ValuationMethodKind,
    ValuationStatus,
    severity_for_valuation_status,
)
from atlas.analysis_engine.valuation.models import ValuationFinding
from atlas.decision_engine.contracts import EvidenceCoverageLevel

__all__ = ["SCENARIO_METHOD_KINDS", "build_scenario_findings"]

SCENARIO_METHOD_KINDS = (
    ValuationMethodKind.SCENARIO_BEAR,
    ValuationMethodKind.SCENARIO_BASE,
    ValuationMethodKind.SCENARIO_BULL,
)

_ALL_CONSUMERS = (
    Consumer.PORTFOLIO_PAGE,
    Consumer.INVESTMENT_CASE_PAGE,
    Consumer.DISCOVERY,
    Consumer.HISTORY,
)


def build_scenario_findings(*, evaluated_at: datetime) -> tuple[ValuationFinding, ...]:
    """Deterministic: always returns the same three `INSUFFICIENT_INPUT`
    findings, one per `SCENARIO_METHOD_KINDS` member -- real, complete
    `ValuationFinding` objects, not placeholders standing in for a
    missing type.
    """
    status = ValuationStatus.INSUFFICIENT_INPUT
    return tuple(
        ValuationFinding(
            id=f"valuation_finding:{kind.value}",
            kind=kind,
            status=status,
            severity=severity_for_valuation_status(status),
            supporting_facts=(),
            contradicting_facts=(),
            assumptions=(),
            missing_evidence=(ValuationDataGapKind.MISSING_SCENARIO_ASSUMPTIONS,),
            confidence=EvidenceCoverageLevel.NOT_APPLICABLE,
            provenance=Provenance(
                source_kind=SourceKind.ANALYSIS_ENGINE_STAGE,
                source_references=(),
                dependencies=(),
                update_trigger=UpdateTrigger.EXTERNAL_BUSINESS_DATA_INGESTED,
                consumers=_ALL_CONSUMERS,
                computed_at=evaluated_at,
            ),
            evaluated_at=evaluated_at,
        )
        for kind in SCENARIO_METHOD_KINDS
    )
