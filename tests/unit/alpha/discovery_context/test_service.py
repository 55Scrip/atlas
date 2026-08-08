"""Direct unit tests for `DiscoveryContextService` (ATLAS-018).

Uses fake `PortfolioIntelligenceService`/`CaseIntelligenceService`
stand-ins (a `build_report` method returning a fixed sentinel) rather
than a real database, since the behavior under test here is purely the
identity-resolution branching (Phase 3) -- whether `CaseIntelligenceService
.build_report()` itself returns the right thing for real data is already
covered by `tests/unit/infrastructure/api/case/test_case_intelligence_v1_scenarios.py`.
"""
from __future__ import annotations

import uuid

from atlas.alpha.discovery_context.models import IdentityResolutionStatus
from atlas.alpha.discovery_context.service import DiscoveryContextService
from atlas.alpha.portfolio_intelligence.models import PortfolioIntelligenceReport


class _FakePortfolioIntelligenceService:
    def __init__(self, report: PortfolioIntelligenceReport) -> None:
        self._report = report

    def build_report(self) -> PortfolioIntelligenceReport:
        return self._report


class _FakeCaseIntelligenceService:
    def __init__(self, reports_by_case_id: dict[str, object]) -> None:
        self._reports_by_case_id = reports_by_case_id
        self.received_case_ids: list[str] = []

    def build_report(self, case_id: str):
        self.received_case_ids.append(case_id)
        return self._reports_by_case_id.get(case_id)


_SENTINEL_PORTFOLIO = PortfolioIntelligenceReport.empty()


def _service(case_reports: dict[str, object] | None = None) -> tuple[DiscoveryContextService, _FakeCaseIntelligenceService]:
    case_service = _FakeCaseIntelligenceService(case_reports or {})
    service = DiscoveryContextService(
        portfolio_intelligence_service=_FakePortfolioIntelligenceService(_SENTINEL_PORTFOLIO),
        case_intelligence_service=case_service,
    )
    return service, case_service


class TestNoCaseIdRequested:
    def test_status_is_not_requested(self):
        service, case_service = _service()
        context = service.build(None)
        assert context.identity.status is IdentityResolutionStatus.NOT_REQUESTED
        assert context.identity.case_id is None
        assert context.identity.ticker is None
        assert context.case is None
        assert case_service.received_case_ids == []  # never even queried

    def test_portfolio_is_still_the_real_report(self):
        service, _ = _service()
        context = service.build(None)
        assert context.portfolio is _SENTINEL_PORTFOLIO


class TestMalformedCaseId:
    def test_status_is_unresolved_and_case_service_never_queried(self):
        service, case_service = _service()
        context = service.build("not-a-real-uuid")
        assert context.identity.status is IdentityResolutionStatus.UNRESOLVED
        assert context.identity.case_id == "not-a-real-uuid"
        assert context.identity.ticker is None
        assert context.case is None
        # A malformed id is never even worth querying the repository with.
        assert case_service.received_case_ids == []

    def test_never_raises(self):
        service, _ = _service()
        context = service.build("")
        assert context.identity.status is IdentityResolutionStatus.UNRESOLVED


class TestWellFormedButNonexistentCaseId:
    def test_status_is_unresolved(self):
        case_id = str(uuid.uuid4())
        service, case_service = _service(case_reports={})  # nothing registered for this id
        context = service.build(case_id)
        assert context.identity.status is IdentityResolutionStatus.UNRESOLVED
        assert context.identity.case_id == case_id
        assert context.identity.ticker is None
        assert context.case is None
        # It *was* queried this time -- the id was well-formed enough to try.
        assert case_service.received_case_ids == [case_id]


class TestResolvedCaseId:
    def test_status_is_resolved_and_ticker_comes_from_the_report(self):
        case_id = str(uuid.uuid4())

        class _FakeCurrentView:
            ticker = "AMD"

        class _FakeReport:
            current_view = _FakeCurrentView()

        service, case_service = _service(case_reports={case_id: _FakeReport()})
        context = service.build(case_id)

        assert context.identity.status is IdentityResolutionStatus.RESOLVED
        assert context.identity.case_id == case_id
        assert context.identity.ticker == "AMD"
        assert context.case is case_service.build_report(case_id)  # same report, not reconstructed

    def test_unheld_case_resolves_with_no_ticker(self):
        case_id = str(uuid.uuid4())

        class _FakeCurrentView:
            ticker = None

        class _FakeReport:
            current_view = _FakeCurrentView()

        service, _ = _service(case_reports={case_id: _FakeReport()})
        context = service.build(case_id)

        assert context.identity.status is IdentityResolutionStatus.RESOLVED
        assert context.identity.ticker is None
