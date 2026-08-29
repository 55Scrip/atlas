"""Industry classification (Calibration Phase 7, Phase 1/2) -- a
closed, deterministic translation from Alpha Vantage's own real
`sector`/`industry` strings into `IndustryFamily`. Mirrors
`atlas.alpha.canonical_security_gate.candidate_mapping
._ASSET_TYPE_TRANSLATION`'s exact pattern: a closed lookup table over a
known external vocabulary, falling through to an honest catch-all
(`UNCLASSIFIED`) rather than guessing.

**Keyed on `industry` (the finer-grained string), not `sector`.**
Alpha Vantage's `sector` values (`"COMMUNICATION SERVICES"`,
`"FINANCIAL SERVICES"`) each span multiple, economically distinct
families this sprint's own `IndustryFamily` model deliberately
separates (Communication Services covers both Internet Platforms and
Telecom; Financial Services covers Banks, Insurance, Asset Managers,
and Payments) -- a sector-level fallback would risk exactly the
"convert stereotypes into facts" outcome the brief forbids. The only
sector-level fallbacks kept are the three sectors that map 1:1 onto a
single family with no ambiguity: Utilities, Energy, Real Estate.

**`HOLDING_COMPANIES` has no entry in this table.** Alpha Vantage
classifies a company by its largest reported operating segment, not by
economic structure -- a true capital-allocation holding company
(Berkshire Hathaway, Investor, Industrivarden, Latour) is typically
reported under its largest subsidiary's own industry (e.g. insurance),
not as a holding company at all. Mapping any real string to
`HOLDING_COMPANIES` today would be an unverifiable guess, not a
translation -- disclosed here, not silently worked around (see the
design doc's own Part A).

**Only 7 of these 60+ table entries have been directly confirmed
against live Atlas data this sprint** (`SOFTWARE - INFRASTRUCTURE`,
`INTERNET RETAIL`, `INTERNET CONTENT & INFORMATION`, `DRUG
MANUFACTURERS - GENERAL`, `CREDIT SERVICES`, `SEMICONDUCTORS`,
`SEMICONDUCTOR EQUIPMENT & MATERIALS`) -- the remainder are drawn from
the same standard, published Alpha-Vantage/Yahoo-Finance industry
taxonomy those 7 confirmed values belong to (a real, external,
well-known vocabulary Atlas already ingests verbatim), not invented for
this sprint.
"""
from __future__ import annotations

from atlas.alpha.industry_intelligence.models import IndustryClassification, IndustryFamily

__all__ = ["classify_industry"]

_INDUSTRY_TRANSLATION: dict[str, IndustryFamily] = {
    # -- Software (SOFTWARE - INFRASTRUCTURE confirmed live: MSFT) -----
    "SOFTWARE - INFRASTRUCTURE": IndustryFamily.SOFTWARE,
    "SOFTWARE - APPLICATION": IndustryFamily.SOFTWARE,
    # -- Semiconductors (both confirmed live: SKHY, AMAT) --------------
    "SEMICONDUCTORS": IndustryFamily.SEMICONDUCTORS,
    "SEMICONDUCTOR EQUIPMENT & MATERIALS": IndustryFamily.SEMICONDUCTORS,
    # -- Internet Platforms (both confirmed live: AMZN, GOOG/META) -----
    "INTERNET CONTENT & INFORMATION": IndustryFamily.INTERNET_PLATFORMS,
    "INTERNET RETAIL": IndustryFamily.INTERNET_PLATFORMS,
    # -- Banks ----------------------------------------------------------
    "BANKS - REGIONAL": IndustryFamily.BANKS,
    "BANKS - DIVERSIFIED": IndustryFamily.BANKS,
    "BANKS": IndustryFamily.BANKS,
    # -- Insurance --------------------------------------------------------
    "INSURANCE - LIFE": IndustryFamily.INSURANCE,
    "INSURANCE - PROPERTY & CASUALTY": IndustryFamily.INSURANCE,
    "INSURANCE - DIVERSIFIED": IndustryFamily.INSURANCE,
    "INSURANCE - SPECIALTY": IndustryFamily.INSURANCE,
    "INSURANCE - REINSURANCE": IndustryFamily.INSURANCE,
    "INSURANCE BROKERS": IndustryFamily.INSURANCE,
    # -- Asset Managers / Financial Platforms ----------------------------
    "ASSET MANAGEMENT": IndustryFamily.ASSET_MANAGERS,
    "CAPITAL MARKETS": IndustryFamily.ASSET_MANAGERS,
    # -- Industrials / Automation / Capital Goods ------------------------
    "SPECIALTY INDUSTRIAL MACHINERY": IndustryFamily.INDUSTRIALS,
    "ELECTRICAL EQUIPMENT & PARTS": IndustryFamily.INDUSTRIALS,
    "CONGLOMERATES": IndustryFamily.INDUSTRIALS,
    "INDUSTRIAL DISTRIBUTION": IndustryFamily.INDUSTRIALS,
    "FARM & HEAVY CONSTRUCTION MACHINERY": IndustryFamily.INDUSTRIALS,
    "TOOLS & ACCESSORIES": IndustryFamily.INDUSTRIALS,
    "SCIENTIFIC & TECHNICAL INSTRUMENTS": IndustryFamily.INDUSTRIALS,
    "AEROSPACE & DEFENSE": IndustryFamily.INDUSTRIALS,
    # -- Consumer Staples -------------------------------------------------
    "PACKAGED FOODS": IndustryFamily.CONSUMER_STAPLES,
    "BEVERAGES - NON-ALCOHOLIC": IndustryFamily.CONSUMER_STAPLES,
    "BEVERAGES - WINERIES & DISTILLERIES": IndustryFamily.CONSUMER_STAPLES,
    "HOUSEHOLD & PERSONAL PRODUCTS": IndustryFamily.CONSUMER_STAPLES,
    "DISCOUNT STORES": IndustryFamily.CONSUMER_STAPLES,
    "GROCERY STORES": IndustryFamily.CONSUMER_STAPLES,
    "TOBACCO": IndustryFamily.CONSUMER_STAPLES,
    # -- Consumer Discretionary / Retail ------------------------------------
    "SPECIALTY RETAIL": IndustryFamily.CONSUMER_DISCRETIONARY,
    "RESTAURANTS": IndustryFamily.CONSUMER_DISCRETIONARY,
    "APPAREL RETAIL": IndustryFamily.CONSUMER_DISCRETIONARY,
    "HOME IMPROVEMENT RETAIL": IndustryFamily.CONSUMER_DISCRETIONARY,
    "AUTO MANUFACTURERS": IndustryFamily.CONSUMER_DISCRETIONARY,
    "LODGING": IndustryFamily.CONSUMER_DISCRETIONARY,
    # -- Luxury -------------------------------------------------------------
    "LUXURY GOODS": IndustryFamily.LUXURY,
    # -- Pharmaceuticals / Biotechnology (confirmed live: AZN) ---------------
    "DRUG MANUFACTURERS - GENERAL": IndustryFamily.PHARMA_BIOTECH,
    "DRUG MANUFACTURERS - SPECIALTY & GENERIC": IndustryFamily.PHARMA_BIOTECH,
    "BIOTECHNOLOGY": IndustryFamily.PHARMA_BIOTECH,
    # -- Medical Devices ------------------------------------------------------
    "MEDICAL DEVICES": IndustryFamily.MEDICAL_DEVICES,
    "MEDICAL INSTRUMENTS & SUPPLIES": IndustryFamily.MEDICAL_DEVICES,
    "DIAGNOSTICS & RESEARCH": IndustryFamily.MEDICAL_DEVICES,
    # -- Utilities / Power -----------------------------------------------------
    "UTILITIES - REGULATED ELECTRIC": IndustryFamily.UTILITIES,
    "UTILITIES - REGULATED GAS": IndustryFamily.UTILITIES,
    "UTILITIES - REGULATED WATER": IndustryFamily.UTILITIES,
    "UTILITIES - DIVERSIFIED": IndustryFamily.UTILITIES,
    "UTILITIES - INDEPENDENT POWER PRODUCERS": IndustryFamily.UTILITIES,
    "UTILITIES - RENEWABLE": IndustryFamily.UTILITIES,
    # -- Energy -------------------------------------------------------------
    "OIL & GAS E&P": IndustryFamily.ENERGY,
    "OIL & GAS INTEGRATED": IndustryFamily.ENERGY,
    "OIL & GAS MIDSTREAM": IndustryFamily.ENERGY,
    "OIL & GAS REFINING & MARKETING": IndustryFamily.ENERGY,
    "OIL & GAS EQUIPMENT & SERVICES": IndustryFamily.ENERGY,
    # -- Real Estate / REITs --------------------------------------------------
    "REIT - RETAIL": IndustryFamily.REAL_ESTATE,
    "REIT - RESIDENTIAL": IndustryFamily.REAL_ESTATE,
    "REIT - DIVERSIFIED": IndustryFamily.REAL_ESTATE,
    "REIT - INDUSTRIAL": IndustryFamily.REAL_ESTATE,
    "REIT - OFFICE": IndustryFamily.REAL_ESTATE,
    "REIT - HEALTHCARE FACILITIES": IndustryFamily.REAL_ESTATE,
    "REIT - SPECIALTY": IndustryFamily.REAL_ESTATE,
    "REAL ESTATE SERVICES": IndustryFamily.REAL_ESTATE,
    # -- Telecom ---------------------------------------------------------------
    "TELECOM SERVICES": IndustryFamily.TELECOM,
    # -- Payments / Transaction Networks (confirmed live: MA) ------------------
    "CREDIT SERVICES": IndustryFamily.PAYMENTS,
}

_SECTOR_FALLBACK: dict[str, IndustryFamily] = {
    "UTILITIES": IndustryFamily.UTILITIES,
    "ENERGY": IndustryFamily.ENERGY,
    "REAL ESTATE": IndustryFamily.REAL_ESTATE,
}


def classify_industry(sector: str | None, industry: str | None) -> IndustryClassification:
    """Deterministic: identical `(sector, industry)` always produces an
    identical `IndustryClassification`. `industry` (the finer-grained
    string) is checked first; the sector fallback only applies to the
    three sectors with no cross-family ambiguity. Neither field present
    -> `UNKNOWN` (no `CompanyProfile` at all); a real string with no
    table entry -> `UNCLASSIFIED` (a translation-table gap, not a data
    gap) -- the same distinction `AnalysisCoverageLevel.NO_COVERAGE`
    vs. `PARTIAL_COVERAGE` already draws for a different pair of
    "missing data" reasons."""
    if sector is None and industry is None:
        family = IndustryFamily.UNKNOWN
    elif industry is not None and industry.strip().upper() in _INDUSTRY_TRANSLATION:
        family = _INDUSTRY_TRANSLATION[industry.strip().upper()]
    elif sector is not None and sector.strip().upper() in _SECTOR_FALLBACK:
        family = _SECTOR_FALLBACK[sector.strip().upper()]
    else:
        family = IndustryFamily.UNCLASSIFIED

    return IndustryClassification(family=family, raw_sector=sector, raw_industry=industry)
