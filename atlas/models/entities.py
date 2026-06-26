from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from atlas.database.connection import Base

class Company(Base):
    __tablename__ = "companies"

    id: Mapped[int] = mapped_column(primary_key=True)
    atlas_id: Mapped[str] = mapped_column(unique=True)
    ticker: Mapped[str] = mapped_column(unique=True)
    name: Mapped[str]
    exchange: Mapped[str | None]
    country: Mapped[str | None]
    currency: Mapped[str | None]
    sector: Mapped[str | None]
    industry: Mapped[str | None]
    status: Mapped[str | None]

    financials: Mapped[list["FinancialHistory"]] = relationship(back_populates="company")

class FinancialHistory(Base):
    __tablename__ = "financial_history"
    __table_args__ = (UniqueConstraint("company_id", "fiscal_year"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"))
    fiscal_year: Mapped[int]
    revenue: Mapped[float | None]
    gross_profit: Mapped[float | None]
    operating_income: Mapped[float | None]
    net_income: Mapped[float | None]
    operating_cashflow: Mapped[float | None]
    capex: Mapped[float | None]
    free_cashflow: Mapped[float | None]
    total_assets: Mapped[float | None]
    equity: Mapped[float | None]
    debt: Mapped[float | None]
    cash: Mapped[float | None]
    shares_outstanding: Mapped[float | None]

    company: Mapped[Company] = relationship(back_populates="financials")
