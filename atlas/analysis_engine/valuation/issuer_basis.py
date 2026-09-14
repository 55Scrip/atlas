"""The issuer basis fiscal_epoch_v3 prices every fiscal epoch on -- a pure
data contract, filled by the Alpha composition layer from persisted
evidence and read by `cash_flow.evaluate_fcf_yield_relative`.

**Why an issuer basis.** Atlas's free cash flow is the issuer's, so it is
comparable only with the issuer's common equity: every outstanding common
class at a price that prices it. The provider's single-listing share count
times a split- and dividend-adjusted historical price (`fiscal_epoch_v2`,
`ShareCountMethod.CURRENT_SHARE_COUNT_PROXY`) is neither.

**Denominator** (`IssuerMarketCap`): the issuer's common-equity market
capitalisation on one economic date (`ISSUER_MARKET_CAP_METHODOLOGY`) --
raw prices, period share counts aligned to the raw price's share basis,
multi-class issuers composed class by class with same-date sibling prices
and temporally valid class rights, participating preferred as-converted,
senior preferred left out. Exact, equivalent, or an evidence-derived
interval; never a point pretending to be exact.

**Numerator** (`COMMON_FCF_NUMERATOR_METHODOLOGY`): Atlas's free cash flow
is operating cash flow minus capital expenditure, as filed. Under US GAAP
interest paid is an operating outflow and dividends are financing flows, so
it is levered cash flow to *all* equity claimants: before preferred
dividends, before distributions to noncontrolling interests, and including
every consolidated subsidiary in full. It is not FCFE (which also adds net
borrowing). The free cash flow attributable to common equity deducts the
contractual claims of senior non-participating preferred outstanding during
the fiscal year (`SeniorClaim`) -- accrued only over the part of the year
the series existed, never before its onset, never after its termination.
Participating preferred is never deducted: it is already common equity in
the denominator. Noncontrolling interests are unmeasured
(`NCI_TREATMENT`) -- a disclosed limitation, never assumed to be zero and
never guessed.

A basis never falls back to another construction: an epoch it cannot price
is absent (with its reason), and a current observation it cannot price
withholds the valuation.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import Enum

from atlas.analysis_engine.exceptions import AnalysisEngineContractError
from atlas.analysis_engine.valuation.contracts import ValuationDataGapKind

__all__ = [
    "COMMON_FCF_NUMERATOR_METHODOLOGY",
    "ISSUER_MARKET_CAP_METHODOLOGY",
    "NCI_TREATMENT",
    "EpochDenominator",
    "IssuerDenominatorQuality",
    "IssuerMarketCap",
    "IssuerValuationBasis",
    "SeniorClaim",
]

#: The denominator's construction (single source: the Alpha composer uses it).
ISSUER_MARKET_CAP_METHODOLOGY = "issuer_common_equity_market_cap_v1"

#: The numerator's construction: consolidated OCF − capex, minus evidenced
#: senior non-participating preferred claims accrued over the fiscal year.
COMMON_FCF_NUMERATOR_METHODOLOGY = "common_attributable_fcf_v1"

#: Noncontrolling interests: Atlas holds no evidence to measure them.
NCI_TREATMENT = "unmeasured"


class IssuerDenominatorQuality(str, Enum):
    #: Every nonzero common class priced by its own listing on the date.
    EXACT = "issuer_exact"
    #: Some class priced through filed or structured economic equivalence.
    EQUIVALENT = "issuer_equivalent"
    #: Some contribution is an evidence-derived interval.
    BOUNDED = "issuer_bounded"


def _fail(message: str) -> None:
    raise AnalysisEngineContractError(message)


@dataclass(frozen=True)
class IssuerMarketCap:
    """The issuer's common-equity market capitalisation on `economic_date`.
    `share_price` is the Case security's own raw price that day."""

    economic_date: date
    share_price: float
    market_cap_low: float
    market_cap_high: float
    quality: IssuerDenominatorQuality
    currency: str
    evidence: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not (self.share_price > 0 and 0 < self.market_cap_low <= self.market_cap_high):
            _fail("An issuer market cap needs a positive price and 0 < low <= high.")
        if self.quality is not IssuerDenominatorQuality.BOUNDED and self.market_cap_low != self.market_cap_high:
            _fail("Only a bounded issuer market cap is an interval.")


@dataclass(frozen=True)
class SeniorClaim:
    """Senior non-participating preferred claims accrued over one fiscal
    year (`fiscal_period` is its end), as an evidence-derived interval."""

    fiscal_period: str
    low: float
    high: float
    evidence: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not 0 <= self.low <= self.high:
            _fail("A senior claim is 0 <= low <= high.")


@dataclass(frozen=True)
class EpochDenominator:
    """One fiscal epoch's denominator, or why it cannot be formed."""

    fiscal_period: str
    observed_on: str
    market_cap: IssuerMarketCap | None = None
    gap: ValuationDataGapKind | None = None

    def __post_init__(self) -> None:
        if (self.market_cap is None) == (self.gap is None):
            _fail("An epoch denominator is either a market cap or a reason, never both or neither.")


@dataclass(frozen=True)
class IssuerValuationBasis:
    """Everything the issuer basis knows for one Case. `current` is composed
    on the Case's own current market date, or is absent with
    `current_gap`. `epochs` covers the prior fiscal epochs. `claims` names
    every fiscal year with a quantified senior claim; `unquantified_claims`
    the fiscal years whose evidenced claim cannot be quantified. A fiscal
    year in neither has no evidenced senior claim."""

    current: IssuerMarketCap | None = None
    current_gap: ValuationDataGapKind | None = None
    epochs: tuple[EpochDenominator, ...] = ()
    claims: tuple[SeniorClaim, ...] = ()
    unquantified_claims: tuple[str, ...] = ()
    nci_treatment: str = NCI_TREATMENT

    def __post_init__(self) -> None:
        if self.current is not None and self.current_gap is not None:
            _fail("A current issuer market cap carries no gap.")
        keys = [(e.fiscal_period, e.observed_on) for e in self.epochs]
        if len(keys) != len(set(keys)):
            _fail("One denominator per epoch.")
        periods = [c.fiscal_period for c in self.claims]
        if len(periods) != len(set(periods)) or set(periods) & set(self.unquantified_claims):
            _fail("One claim per fiscal year, quantified or not.")

    def denominator_for(self, fiscal_period: str, observed_on: str) -> IssuerMarketCap | ValuationDataGapKind:
        for epoch in self.epochs:
            if (epoch.fiscal_period, epoch.observed_on) == (fiscal_period, observed_on):
                return epoch.market_cap if epoch.market_cap is not None else epoch.gap
        return ValuationDataGapKind.DENOMINATOR_EVIDENCE_MISSING

    def claim_for(self, fiscal_period: str) -> SeniorClaim | ValuationDataGapKind | None:
        """The quantified claim, `NUMERATOR_EVIDENCE_MISSING`, or `None` when
        no senior claim on that fiscal year is evidenced."""
        if fiscal_period in self.unquantified_claims:
            return ValuationDataGapKind.NUMERATOR_EVIDENCE_MISSING
        return next((c for c in self.claims if c.fiscal_period == fiscal_period), None)
