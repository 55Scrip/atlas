"""Where Financial Risk v2's corporate debt measure applies (Financial Risk v2).

Debt divided by operating cash flow describes how heavily an operating
business leans on borrowed money. It does not describe a bank, a dealer or
an insurer: there, debt and deposits fund the balance sheet that *is* the
business, and operating cash flow swings with trading inventories and
policyholder flows. Forcing such a company through the ratio would produce
a confident, meaningless number -- GS's reported operating cash flow was
about -45 billion USD in 2025.

**The rule reads the company-profile industry, never the sector.** The
provider's "Financial Services" sector holds banks and dealers next to
payment networks ("CREDIT SERVICES") and data providers ("FINANCIAL DATA &
STOCK EXCHANGES"), which are ordinary operating businesses the measure
describes well. So only balance-sheet industries are excluded:

- every industry starting ``BANKS`` (``BANKS - DIVERSIFIED``, ``BANKS -
  REGIONAL``);
- every industry starting ``INSURANCE -`` (the carriers; ``INSURANCE
  BROKERS`` has no dash and stays applicable -- brokers do not
  underwrite);
- ``CAPITAL MARKETS`` and ``MORTGAGE FINANCE``.

**Known limitation, disclosed rather than patched per issuer.** The same
industry label can span different business models: ``CREDIT SERVICES``
holds consumer lenders as well as payment networks, and ``CAPITAL
MARKETS`` holds asset-light advisers as well as dealers. The rule follows
the label; it never names a company.

An unknown industry is ``None`` -- applicability cannot be established,
and the evaluator reports that as a gap rather than assuming either way.
"""
from __future__ import annotations

__all__ = ["BALANCE_SHEET_INDUSTRY_PREFIXES", "BALANCE_SHEET_INDUSTRIES", "debt_burden_measure_applies"]

#: Industry-name prefixes whose members are balance-sheet financial
#: businesses. Compared against the upper-cased, stripped label.
BALANCE_SHEET_INDUSTRY_PREFIXES = ("BANKS", "INSURANCE -")

#: Exact industry names that are balance-sheet financial businesses.
BALANCE_SHEET_INDUSTRIES = frozenset({"CAPITAL MARKETS", "MORTGAGE FINANCE"})


def debt_burden_measure_applies(industry: str | None) -> bool | None:
    """`True`/`False` for a known industry; `None` when none is recorded."""
    if industry is None or not industry.strip():
        return None
    label = " ".join(industry.upper().split())
    if label in BALANCE_SHEET_INDUSTRIES or label.startswith(BALANCE_SHEET_INDUSTRY_PREFIXES):
        return False
    return True
