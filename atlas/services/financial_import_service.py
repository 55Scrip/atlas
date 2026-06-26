import csv
from pathlib import Path

from sqlalchemy import select

from atlas.database.connection import get_session
from atlas.models import Company, FinancialHistory

REQUIRED_COLUMNS = [
    "fiscal_year",
    "revenue",
    "gross_profit",
    "operating_income",
    "net_income",
    "operating_cashflow",
    "capex",
    "free_cashflow",
    "total_assets",
    "equity",
    "debt",
    "cash",
    "shares_outstanding",
]

NUMERIC_COLUMNS = [column for column in REQUIRED_COLUMNS if column != "fiscal_year"]


def import_financials(ticker: str, csv_path: Path, db_path: Path | None = None) -> int:
    rows = _read_financial_rows(csv_path)

    with get_session(db_path) as session:
        company = session.scalar(select(Company).where(Company.ticker == ticker.upper()))
        if not company:
            raise LookupError(f"No company found for ticker: {ticker.upper()}")

        imported_count = 0
        for row in rows:
            fiscal_year = _parse_fiscal_year(row["fiscal_year"])
            financial = session.scalar(
                select(FinancialHistory).where(
                    FinancialHistory.company_id == company.id,
                    FinancialHistory.fiscal_year == fiscal_year,
                )
            )
            if not financial:
                financial = FinancialHistory(company_id=company.id, fiscal_year=fiscal_year)
                session.add(financial)

            for column in NUMERIC_COLUMNS:
                setattr(financial, column, _parse_float(row[column]))
            imported_count += 1

        session.commit()

    return imported_count


def _read_financial_rows(csv_path: Path) -> list[dict[str, str]]:
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")

    with csv_path.open(newline="", encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file)
        fieldnames = reader.fieldnames or []
        missing_columns = [column for column in REQUIRED_COLUMNS if column not in fieldnames]
        if missing_columns:
            missing = ", ".join(missing_columns)
            raise ValueError(f"Missing required CSV columns: {missing}")

        return list(reader)


def _parse_fiscal_year(value: str) -> int:
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Invalid fiscal_year: {value}") from exc


def _parse_float(value: str) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except ValueError as exc:
        raise ValueError(f"Invalid numeric value: {value}") from exc
