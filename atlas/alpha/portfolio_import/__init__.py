"""Zero-Effort Portfolio Onboarding: the unified import pipeline.

Owns column detection, row parsing, company/ticker resolution, and
duplicate detection as one real service, regardless of whether the
investor pasted text, uploaded a CSV, or typed rows by hand -- see the
"Frictionless Import Architecture" and "Zero-Effort Onboarding
Architecture" design artifacts. Exposed as a stateless preview endpoint
(`POST /alpha-portfolio/import/preview`): this package never persists
anything and never calls `atlas.alpha.portfolio` for anything beyond
reading the current holdings' tickers, for against-existing-portfolio
duplicate detection. Confirming an import still goes through the
existing, unmodified `atlas.alpha.portfolio.service.AlphaPortfolioService`
entrypoints.
"""
