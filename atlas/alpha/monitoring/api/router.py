"""REST controller for Monitoring & Change Detection (Atlas Intelligence
Sprint 7/8). A new, sibling top-level prefix, matching how `evidence-
timeline`/`materiality` themselves introduced their own prefix for a
genuinely new report.

`POST /monitoring/run` is Deliverable 20's own explicit, deterministic
operation -- never invoked automatically by anything in this codebase
(no scheduler exists; see `service.py`'s own module docstring). Sprint
8: `force=false` (the default) only evaluates Cases the cheap dirty
pre-pass finds genuinely due (Deliverable 4); `force=true` evaluates
every known Case regardless, the documented escape hatch for changes
the pre-pass cannot cheaply see (new `BusinessRecord` ingestion -- see
`service.py`'s own module docstring).
`GET /monitoring/results` is Deliverable 21's read model, served from
the last run's own cache without recomputing.
`GET /monitoring/status` is Sprint 8's own operational read model
(Deliverable 7/14) -- deliberately separate from `/results`, since one
answers "is Monitoring itself current" and the other "what does
Monitoring currently believe about each company," and the two must
never be conflated (this sprint's own governing principle).
"""
from __future__ import annotations

from fastapi import APIRouter, Depends

from atlas.alpha.monitoring.api.dependencies import get_monitoring_service
from atlas.alpha.monitoring.api.schemas import MonitoringOperationalStatusView, MonitoringRunView
from atlas.alpha.monitoring.service import MonitoringService

router = APIRouter(prefix="/monitoring", tags=["monitoring"])


@router.post("/run", response_model=MonitoringRunView)
def run_monitoring(force: bool = False, service: MonitoringService = Depends(get_monitoring_service)) -> MonitoringRunView:
    return MonitoringRunView.from_domain(service.run(force=force))


@router.get("/results", response_model=MonitoringRunView)
def get_monitoring_results(service: MonitoringService = Depends(get_monitoring_service)) -> MonitoringRunView:
    return MonitoringRunView.from_domain(service.read_model())


@router.get("/status", response_model=MonitoringOperationalStatusView)
def get_monitoring_status(service: MonitoringService = Depends(get_monitoring_service)) -> MonitoringOperationalStatusView:
    return MonitoringOperationalStatusView.from_domain(service.operational_status())
