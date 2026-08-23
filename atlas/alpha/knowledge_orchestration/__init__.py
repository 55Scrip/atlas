"""Knowledge Orchestration Engine. See `capability.py`/`planner.py`/
`dependency.py`/`orchestrator.py`/`reanalysis.py` for the full design
rationale."""
from __future__ import annotations

from .capability import (
    PROVIDER_CAPABILITIES,
    AcquisitionCost,
    AcquisitionPriority,
    DomainCriticality,
    ExecutionConstraint,
    ProviderCapability,
)
from .dependency import resolve_order
from .orchestrator import AcquisitionStepOutcome, OrchestrationOutcome, run_orchestrated_acquisition
from .planner import (
    AcquisitionPlan,
    AcquisitionPlanItem,
    DomainState,
    PlanReasonCode,
    SufficiencyAssessment,
    SufficiencyReason,
    classify_domain_state,
    plan_acquisition,
)
from .reanalysis import should_trigger_reanalysis

__all__ = [
    "PROVIDER_CAPABILITIES",
    "AcquisitionCost",
    "AcquisitionPriority",
    "DomainCriticality",
    "ExecutionConstraint",
    "ProviderCapability",
    "resolve_order",
    "AcquisitionStepOutcome",
    "OrchestrationOutcome",
    "run_orchestrated_acquisition",
    "AcquisitionPlan",
    "AcquisitionPlanItem",
    "DomainState",
    "PlanReasonCode",
    "SufficiencyAssessment",
    "SufficiencyReason",
    "classify_domain_state",
    "plan_acquisition",
    "should_trigger_reanalysis",
]
