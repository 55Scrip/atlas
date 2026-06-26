from sqlalchemy import select
from atlas.database.connection import get_session
from atlas.models import Company

def add_company(
    ticker: str,
    name: str,
    atlas_id: str,
    exchange: str | None = None,
    country: str | None = None,
    currency: str = "USD",
    sector: str | None = None,
    industry: str | None = None,
    status: str = "Active",
) -> Company:
    with get_session() as session:
        existing = session.scalar(select(Company).where(Company.ticker == ticker.upper()))
        if existing:
            return existing

        company = Company(
            ticker=ticker.upper(),
            name=name,
            atlas_id=atlas_id,
            exchange=exchange,
            country=country,
            currency=currency,
            sector=sector,
            industry=industry,
            status=status,
        )
        session.add(company)
        session.commit()
        session.refresh(company)
        return company

def list_companies() -> list[Company]:
    with get_session() as session:
        return list(session.scalars(select(Company).order_by(Company.atlas_id)))

def get_company_by_ticker(ticker: str) -> Company | None:
    with get_session() as session:
        return session.scalar(select(Company).where(Company.ticker == ticker.upper()))
