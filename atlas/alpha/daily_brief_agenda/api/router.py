"""REST controller for the Daily Brief Agenda.

A new, sibling top-level prefix (own resource, matching how
`portfolio_fit`/`daily_brief` each introduced their own prefix for a
genuinely new report).
"""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query

from atlas.alpha.daily_brief_agenda.api.dependencies import get_daily_brief_agenda_service
from atlas.alpha.daily_brief_agenda.api.schemas import DailyBriefAgendaView
from atlas.alpha.daily_brief_agenda.service import DailyBriefAgendaService
from atlas.alpha.daily_brief_change_log.api.dependencies import get_case_baseline_store, get_daily_brief_change_log_store
from atlas.alpha.daily_brief_change_log.case_baseline import CaseBaselineStore
from atlas.alpha.daily_brief_change_log.eligibility import extract_eligible_changes
from atlas.alpha.daily_brief_change_log.store import DailyBriefChangeLogStore

router = APIRouter(prefix="/daily-brief-agenda", tags=["daily-brief-agenda"])


@router.get("", response_model=DailyBriefAgendaView)
def get_daily_brief_agenda(
    user_id: str | None = Query(default=None, alias="userId"),
    service: DailyBriefAgendaService = Depends(get_daily_brief_agenda_service),
    change_log_store: DailyBriefChangeLogStore = Depends(get_daily_brief_change_log_store),
    case_baseline_store: CaseBaselineStore = Depends(get_case_baseline_store),
) -> DailyBriefAgendaView:
    """Daily Brief 2.0 -- building the agenda is also the one and only
    moment an eligible change can be durably recorded (see
    `daily_brief_change_log/__init__.py` for why: the upstream engines'
    own transition detection self-erases after this exact call). The
    recording is a best-effort side effect keyed on `user_id`, which is
    optional and additive -- a caller that omits it (or any test/tool
    exercising this endpoint directly) gets the identical `DailyBrief
    AgendaView` this endpoint has always returned; nothing about the
    existing contract changed.

    RC-3, Phase 3 -- every real case_id present in this pass (not only
    ones with an eligible fact) is checked against the case-baseline
    store first, so a case observed for the first time this call has
    its baseline established before `extract_eligible_changes`' own
    facts for it are recorded (see `case_baseline.py` for why this
    can't be derived from the change log's own rows alone)."""
    agenda = service.build_agenda()
    if user_id is not None:
        case_ids = frozenset(item.case_id for item in agenda.items if item.case_id is not None)
        newly_baseline_cases = case_baseline_store.mark_seen_and_get_new(user_id, case_ids, now=datetime.now(timezone.utc))
        eligible_changes = extract_eligible_changes(agenda)
        change_log_store.record_if_new(user_id, eligible_changes, newly_baseline_cases=newly_baseline_cases)
    return DailyBriefAgendaView.from_domain(agenda)
