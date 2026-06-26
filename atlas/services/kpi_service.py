def safe_divide(numerator: float | None, denominator: float | None) -> float | None:
    if numerator is None or denominator in (None, 0):
        return None
    return numerator / denominator

def gross_margin(gross_profit: float | None, revenue: float | None) -> float | None:
    return safe_divide(gross_profit, revenue)

def operating_margin(operating_income: float | None, revenue: float | None) -> float | None:
    return safe_divide(operating_income, revenue)

def net_margin(net_income: float | None, revenue: float | None) -> float | None:
    return safe_divide(net_income, revenue)

def fcf_margin(free_cashflow: float | None, revenue: float | None) -> float | None:
    return safe_divide(free_cashflow, revenue)
