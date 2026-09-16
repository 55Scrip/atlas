"""Build the scheduled-composition service from a database engine.

The API wires the composition service through FastAPI's `Depends`, which a
command line cannot use. This assembles the identical object graph from an
engine instead -- the same repositories, the same stores, the same
`InvestmentCaseCompositionService` -- so a scheduled batch composes through
exactly the path an opened Case does. Nothing here is a scheduler-only
variant of anything; if this drifts from `api/dependencies.py`, the two
disagree about what composing a Case means, and that would be a defect.
"""
from __future__ import annotations

from sqlalchemy.engine import Engine

from atlas.alpha.business_data_refresh.repository import SqlAlchemyBusinessRecordRepository
from atlas.alpha.business_data_refresh.table import create_business_record_table
from atlas.alpha.canonical_security_gate.factory import build_listing_mic_reader
from atlas.alpha.case_instrument.repository import CaseInstrumentBindingRepository
from atlas.alpha.case_instrument.table import create_case_instrument_binding_table
from atlas.alpha.investment_case.service import InvestmentCaseCompositionService
from atlas.alpha.investment_case_change.repository import SqlAlchemyInvestmentCaseSnapshotRepository
from atlas.alpha.investment_case_change.table import create_investment_case_snapshot_table
from atlas.alpha.issuer_equity.valuation_basis import IssuerValuationBasisBuilder
from atlas.alpha.portfolio.store import AlphaPortfolioStore
from atlas.alpha.portfolio.table import create_alpha_portfolio_state_table
from atlas.alpha.portfolio.trade_log_store import AlphaTradeLogStore
from atlas.alpha.portfolio.trade_log_table import create_alpha_trade_log_table
from atlas.alpha.scheduled_composition.service import ScheduledCompositionService
from atlas.alpha.security_share_evidence.repository import SqlAlchemySecurityShareEvidenceRepository
from atlas.alpha.watchlist.store import AlphaWatchlistStore
from atlas.alpha.watchlist.table import create_alpha_watchlist_entry_table

__all__ = ["build_scheduled_composition_service"]


def build_scheduled_composition_service(engine: Engine) -> ScheduledCompositionService:
    from atlas.core.infrastructure.persistence.case.sqlalchemy_repository import SqlAlchemyCaseRepository
    from atlas.core.infrastructure.persistence.case.table import create_case_table
    from atlas.core.infrastructure.persistence.decision.sqlalchemy_repository import SqlAlchemyDecisionRepository
    from atlas.core.infrastructure.persistence.decision.table import create_decision_table
    from atlas.core.infrastructure.persistence.evidence.sqlalchemy_repository import SqlAlchemyEvidenceRepository
    from atlas.core.infrastructure.persistence.evidence.table import create_evidence_table
    from atlas.core.infrastructure.persistence.observation.sqlalchemy_repository import (
        SqlAlchemyObservationRepository,
    )
    from atlas.core.infrastructure.persistence.observation.table import create_observation_table
    from atlas.core.infrastructure.persistence.outcome.sqlalchemy_repository import SqlAlchemyOutcomeRepository
    from atlas.core.infrastructure.persistence.outcome.table import create_outcome_table

    for create in (
        create_case_table, create_decision_table, create_observation_table, create_evidence_table,
        create_outcome_table, create_business_record_table, create_investment_case_snapshot_table,
        create_case_instrument_binding_table, create_alpha_portfolio_state_table,
        create_alpha_trade_log_table, create_alpha_watchlist_entry_table,
    ):
        create(engine)

    portfolio_store = AlphaPortfolioStore(engine)
    watchlist_store = AlphaWatchlistStore(engine)
    snapshot_repository = SqlAlchemyInvestmentCaseSnapshotRepository(engine)
    composition_service = InvestmentCaseCompositionService(
        case_repository=SqlAlchemyCaseRepository(engine),
        decision_repository=SqlAlchemyDecisionRepository(engine),
        observation_repository=SqlAlchemyObservationRepository(engine),
        evidence_repository=SqlAlchemyEvidenceRepository(engine),
        outcome_repository=SqlAlchemyOutcomeRepository(engine),
        portfolio_store=portfolio_store,
        trade_log_store=AlphaTradeLogStore(engine),
        business_record_repository=SqlAlchemyBusinessRecordRepository(engine),
        watchlist_store=watchlist_store,
        snapshot_repository=snapshot_repository,
        binding_repository=CaseInstrumentBindingRepository(engine),
        # `listing_mics` is not optional in practice, whatever its default
        # says: without it an issuer whose equity trades as more than one
        # listed class (GOOG/GOOGL) resolves no historical share counts, so
        # every prior epoch disappears and a Case that Atlas calls EXPENSIVE
        # composes as INSUFFICIENT_INPUT. Dropping it once already produced
        # exactly that, and the batch wrote the wrong conclusion to history.
        security_share_repository=SqlAlchemySecurityShareEvidenceRepository(
            engine, listing_mics=build_listing_mic_reader(engine)
        ),
        valuation_basis_builder=IssuerValuationBasisBuilder.from_engine(engine),
    )
    return ScheduledCompositionService(
        composition_service=composition_service,
        portfolio_store=portfolio_store,
        watchlist_store=watchlist_store,
        snapshot_repository=snapshot_repository,
    )
