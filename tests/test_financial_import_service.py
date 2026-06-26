import pytest
from sqlalchemy import select

from atlas.database.connection import get_session
from atlas.models import Company, FinancialHistory
from atlas.services.database_service import init_database
from atlas.services.financial_import_service import import_financials


CSV_HEADER = (
    "fiscal_year,revenue,gross_profit,operating_income,net_income,"
    "operating_cashflow,capex,free_cashflow,total_assets,equity,debt,cash,"
    "shares_outstanding"
)


def test_import_financials_inserts_rows(tmp_path):
    db_path = tmp_path / "atlas.db"
    init_database(db_path)
    _add_company(db_path)

    csv_path = tmp_path / "financials.csv"
    csv_path.write_text(
        "\n".join(
            [
                CSV_HEADER,
                "2023,100,55,30,25,35,-10,25,500,300,100,80,1000",
                "2024,120,70,40,32,45,-12,33,550,340,90,100,1005",
            ]
        ),
        encoding="utf-8",
    )

    imported_count = import_financials("TSM", csv_path, db_path)

    assert imported_count == 2
    with get_session(db_path) as session:
        rows = list(session.scalars(select(FinancialHistory).order_by(FinancialHistory.fiscal_year)))

    assert [row.fiscal_year for row in rows] == [2023, 2024]
    assert rows[0].revenue == 100
    assert rows[1].free_cashflow == 33


def test_import_financials_updates_existing_row(tmp_path):
    db_path = tmp_path / "atlas.db"
    init_database(db_path)
    _add_company(db_path)

    csv_path = tmp_path / "financials.csv"
    csv_path.write_text(
        "\n".join(
            [
                CSV_HEADER,
                "2024,120,70,40,32,45,-12,33,550,340,90,100,1005",
            ]
        ),
        encoding="utf-8",
    )

    assert import_financials("TSM", csv_path, db_path) == 1
    csv_path.write_text(
        "\n".join(
            [
                CSV_HEADER,
                "2024,125,75,45,37,50,-13,37,560,350,85,105,1006",
            ]
        ),
        encoding="utf-8",
    )

    assert import_financials("TSM", csv_path, db_path) == 1
    with get_session(db_path) as session:
        rows = list(session.scalars(select(FinancialHistory)))

    assert len(rows) == 1
    assert rows[0].revenue == 125
    assert rows[0].shares_outstanding == 1006


def test_import_financials_validates_required_columns(tmp_path):
    db_path = tmp_path / "atlas.db"
    init_database(db_path)
    _add_company(db_path)

    csv_path = tmp_path / "financials.csv"
    csv_path.write_text("fiscal_year,revenue\n2024,120\n", encoding="utf-8")

    with pytest.raises(ValueError, match="Missing required CSV columns"):
        import_financials("TSM", csv_path, db_path)


def _add_company(db_path):
    with get_session(db_path) as session:
        session.add(
            Company(
                atlas_id="AI-001",
                ticker="TSM",
                name="Taiwan Semiconductor Manufacturing Company",
                currency="USD",
                status="Active",
            )
        )
        session.commit()
