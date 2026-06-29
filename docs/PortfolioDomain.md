# Portfolio Domain

The Portfolio domain owns portfolio structure and deterministic portfolio-level
understanding.

It does not create trade recommendations, forecasts, or personalized financial
advice. Its job is to help Atlas understand what a portfolio contains and where
important structural risks or data gaps may exist.

## Responsibility

The domain is responsible for:

- Portfolio and holding structure.
- Holding market value calculation.
- Portfolio value calculation.
- Holding weights.
- Sector and country allocation.
- Cash weight when cash is represented as a holding.
- Largest position and top holdings.
- Concentration level.
- Structured validation issues.
- Calm portfolio observations.

## Model Definitions

Canonical `Portfolio` and `Holding` entities live in `atlas.shared` and are
exported through `atlas.domains.portfolio`.

The domain adds portfolio-specific structured outputs:

- `Allocation`
- `Concentration`
- `PortfolioSnapshot`
- `PortfolioSummary`
- `PortfolioValidationIssue`
- `PortfolioValidationResult`
- `PortfolioObservation`
- `PortfolioDomainReview`

## Calculations

Portfolio calculations are deterministic and explainable:

- Holding market value uses explicit `market_value` first.
- If market value is absent, value is calculated from `quantity * current_price`.
- Portfolio value is the sum of holding market values.
- Holding weight is holding value divided by total portfolio value.
- Sector and country allocation group holdings by reported fields.
- Missing sectors and countries are grouped as unknown in calculations.
- Top holdings are sorted by market value, then ticker for deterministic output.

## Portfolio Review Engine

`PortfolioReviewEngine` produces structured observations only. It can surface:

- Portfolio summary.
- Largest holding.
- Concentration warnings.
- Sector concentration.
- Country concentration.
- Missing data warnings.

The review engine does not recommend actions. It uses calm language such as
`worth monitoring` and focuses on portfolio understanding.

## Validation

Validation returns structured issues rather than crashing unnecessarily.

It checks:

- Empty portfolio.
- Negative quantities.
- Missing prices.
- Missing sectors.
- Missing countries.
- Duplicate tickers.
- Invalid stored weights.
- Unsupported currency assumptions.

Only error-level issues make a portfolio invalid. Warning and info issues are
still returned so callers can show data quality context.

## Known Limitations

- Only USD currency assumptions are currently supported.
- No persistence is added in this sprint.
- No provider or market data integration is added.
- No tax, account, fee, benchmark, or performance calculations are included.
- Existing higher-level portfolio engines have not yet migrated to this domain.

## Recommended Next Sprint

Sprint 38 should connect one existing portfolio-facing surface to the new domain
in a small, reversible way.

Recommended path:

- Adapt Portfolio Review or Atlas Home to consume `PortfolioSummary`.
- Keep CLI output unchanged unless explicitly requested.
- Add tests proving behavior is preserved.
- Avoid broad migrations until the domain boundary has proved useful.

