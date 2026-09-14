"""Security-level share-class evidence (Security-Level Share-Class Evidence
v1): per-class outstanding shares as each annual SEC filing reports them,
linked to an exchange-listed security only by a dimension the filing
itself shares between its cover page and its share facts.

Descriptive input only. Its one reader in the product is
`atlas.alpha.investment_case.historical_market_cap` (through
`InvestmentCaseCompositionService`); valuation, sensitivity,
recommendation, conviction, Portfolio Fit, Stance, the Daily Brief and
every decision surface never see it (pinned by
`tests/unit/alpha/security_share_evidence/test_firewall.py`).
"""
