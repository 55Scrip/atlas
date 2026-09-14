"""Issuer common-equity market capitalisation (Issuer Common-Equity Market
Cap v1): the denominator issuer-wide free cash flow belongs over, composed
on demand from share-count evidence, class economic-rights evidence and
same-date prices, and graded exact / equivalent / bounded / insufficient.

Since fiscal_epoch_v3 this is the valuation's denominator: Case composition
builds each Case's issuer valuation basis from it (`valuation_basis`, with the
senior preferred claims of `claims`), and the FCF-yield evaluator applies it.
Read-only; its importers are pinned by
`tests/unit/alpha/class_rights_evidence/test_firewall.py`.
"""
