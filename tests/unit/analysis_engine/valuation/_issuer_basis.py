"""Test-only issuer bases for fixtures whose company has one common class.

A fixture's own price and share-count facts describe a single-class issuer:
its issuer common-equity market capitalisation on each observation's date is
that price times that count. These helpers state exactly that as an exact
issuer basis, so downstream tests keep exercising real classifications
through the production v3 evaluator. Production composes its basis from
persisted evidence (`atlas.alpha.issuer_equity.valuation_basis`), never
from these facts.
"""
from __future__ import annotations

from datetime import date, datetime

from atlas.analysis_engine.valuation.cash_flow import fiscal_epochs
from atlas.analysis_engine.valuation.issuer_basis import (
    EpochDenominator,
    IssuerDenominatorQuality,
    IssuerMarketCap,
    IssuerValuationBasis,
    SeniorClaim,
)
from atlas.analysis_engine.valuation.models import FcfYieldEpochObservation, FcfYieldEvidence


def _cap(epoch: FcfYieldEpochObservation, *, scale: tuple[float, float] = (1.0, 1.0),
         quality: IssuerDenominatorQuality = IssuerDenominatorQuality.EXACT) -> IssuerMarketCap:
    cap = epoch.share_price * epoch.shares_outstanding
    return IssuerMarketCap(date.fromisoformat(epoch.observed_on), epoch.share_price, cap * scale[0], cap * scale[1],
                           quality, epoch.currency, ("fixture",))


def basis_for_epochs(epochs: FcfYieldEvidence | None, *, claims: dict[str, tuple[float, float]] | None = None,
                     current_scale: tuple[float, float] = (1.0, 1.0),
                     prior_scale: tuple[float, float] = (1.0, 1.0)) -> IssuerValuationBasis | None:
    if epochs is None:
        return None
    bounded = current_scale != (1.0, 1.0) or prior_scale != (1.0, 1.0)
    quality = IssuerDenominatorQuality.BOUNDED if bounded else IssuerDenominatorQuality.EXACT
    return IssuerValuationBasis(
        current=_cap(epochs.current, scale=current_scale, quality=quality) if epochs.current else None,
        epochs=tuple(EpochDenominator(e.fiscal_period, e.observed_on, _cap(e, scale=prior_scale, quality=quality))
                     for e in epochs.prior_epochs),
        claims=tuple(SeniorClaim(p, lo, hi) for p, (lo, hi) in sorted((claims or {}).items())),
    )


def single_class_basis(business_facts, valuation_facts, *, statement_record_ids, industry, evaluated_at: datetime,
                       **kw) -> IssuerValuationBasis | None:
    """The fixture's own facts as an exact single-class issuer basis."""
    return basis_for_epochs(fiscal_epochs(business_facts, valuation_facts, statement_record_ids=statement_record_ids,
                                          industry=industry, evaluated_at=evaluated_at), **kw)


def single_class_basis_for_records(business_records, *, generated_at: datetime) -> IssuerValuationBasis | None:
    from atlas.analysis_engine.pipeline import fiscal_epochs_for_records

    return basis_for_epochs(fiscal_epochs_for_records(tuple(business_records), generated_at=generated_at))


def evaluate_fixture_valuation(business_facts, valuation_facts, *, statement_record_ids, industry,
                               evaluated_at: datetime):
    """`evaluate_valuation` for a fixture whose facts describe a single-class
    issuer (its own price times its own count is its issuer market cap)."""
    from atlas.analysis_engine.valuation.pipeline import evaluate_valuation

    basis = single_class_basis(tuple(business_facts), tuple(valuation_facts), statement_record_ids=statement_record_ids,
                               industry=industry, evaluated_at=evaluated_at)
    return evaluate_valuation(business_facts, valuation_facts, statement_record_ids=statement_record_ids,
                              industry=industry, evaluated_at=evaluated_at, valuation_basis=basis)


def assemble_fixture_analysis(engine_input, decision_output, *, is_thesis_stale, business_records=(),
                              generated_at: datetime):
    """`assemble_analysis` for fixture records describing a single-class issuer."""
    from atlas.analysis_engine.pipeline import assemble_analysis

    return assemble_analysis(engine_input, decision_output, is_thesis_stale=is_thesis_stale,
                             business_records=business_records, generated_at=generated_at,
                             valuation_basis=single_class_basis_for_records(business_records, generated_at=generated_at))


class FixtureIssuerBasisBuilder:
    """A stand-in for `IssuerValuationBasisBuilder` in service and API
    scenario tests whose fixture companies are single-class issuers described
    only by their own price and share-count facts (no persisted share-class
    or rights evidence). Production composes the same basis from persisted
    evidence -- pinned in `tests/unit/alpha/issuer_equity`."""

    def build(self, *, ticker, every_version, records, epochs, historical, evaluated_at):
        return basis_for_epochs(epochs)
