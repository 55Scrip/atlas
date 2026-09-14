"""Class economic-rights evidence (Issuer Common-Equity Market Cap v1): what
each class of an issuer's equity is entitled to, as its own SEC filings
state it -- per-class EPS, conversion rates and ratios, as-converted counts,
preferred terms, and filed statements of parity, conversion, voting and
seniority, each with its evidence strength and the dates it holds for.

A separate evidence type from share counts (`security_share_evidence`):
counts say how many shares a class has; this says what a share of it is
worth in another class's terms. Descriptive input only: its one reader is
the issuer common-equity market-cap composer (`atlas.alpha.issuer_equity`),
which no valuation, recommendation or narrative path reads (pinned by
`tests/unit/alpha/class_rights_evidence/test_firewall.py`).
"""
