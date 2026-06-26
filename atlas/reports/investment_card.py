from atlas.services.company_service import get_company_by_ticker

def generate_investment_card(ticker: str) -> str:
    company = get_company_by_ticker(ticker)
    if not company:
        return f"No company found for ticker: {ticker.upper()}"

    return f"""
# {company.name} ({company.ticker})

Atlas ID: {company.atlas_id}
Exchange: {company.exchange or "-"}
Country: {company.country or "-"}
Sector: {company.sector or "-"}
Industry: {company.industry or "-"}
Status: {company.status or "-"}

## Investment Card

Financial Data: Not imported yet
Valuation: Not calculated yet
Decision: Under Research
""".strip()
