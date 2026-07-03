"""Sprint 197 guardrail tests: atlas/database/ and atlas/services/ audit."""

import importlib
import sys


# --- database/connection.py imports ---


def test_database_connection_base_importable():
    from atlas.database.connection import Base

    assert Base is not None


def test_database_connection_get_engine_importable():
    from atlas.database.connection import get_engine

    assert callable(get_engine)


def test_database_connection_get_session_importable():
    from atlas.database.connection import get_session

    assert callable(get_session)


def test_database_connection_no_provider_imports():
    import atlas.database.connection as mod

    provider_names = {"CompanyDataProvider", "MockCompanyAnalysisProvider", "YahooFinanceProvider"}
    module_attrs = set(dir(mod))
    assert not provider_names.intersection(module_attrs)


def test_database_connection_no_network_imports():
    import atlas.database.connection as mod

    src = importlib.util.find_spec("atlas.database.connection").origin
    with open(src, encoding="utf-8") as f:
        content = f.read()
    assert "requests" not in content
    assert "urllib.request" not in content
    assert "urlopen" not in content


# --- services/database_service.py imports ---


def test_database_service_init_database_importable():
    from atlas.services.database_service import init_database

    assert callable(init_database)


def test_database_service_no_provider_imports():
    import atlas.services.database_service as mod

    provider_names = {"CompanyDataProvider", "MockCompanyAnalysisProvider", "YahooFinanceProvider"}
    module_attrs = set(dir(mod))
    assert not provider_names.intersection(module_attrs)


# --- services/company_service.py imports ---


def test_company_service_add_company_importable():
    from atlas.services.company_service import add_company

    assert callable(add_company)


def test_company_service_list_companies_importable():
    from atlas.services.company_service import list_companies

    assert callable(list_companies)


def test_company_service_get_company_by_ticker_importable():
    from atlas.services.company_service import get_company_by_ticker

    assert callable(get_company_by_ticker)


# --- services/financial_import_service.py imports ---


def test_financial_import_service_import_financials_importable():
    from atlas.services.financial_import_service import import_financials

    assert callable(import_financials)


def test_financial_import_service_required_columns_importable():
    from atlas.services.financial_import_service import REQUIRED_COLUMNS

    assert isinstance(REQUIRED_COLUMNS, (list, tuple, set, frozenset))


# --- boundary: no upward dependencies ---


def test_database_connection_does_not_import_services():
    src = importlib.util.find_spec("atlas.database.connection").origin
    with open(src, encoding="utf-8") as f:
        content = f.read()
    assert "atlas.services" not in content


def test_database_connection_does_not_import_cli():
    src = importlib.util.find_spec("atlas.database.connection").origin
    with open(src, encoding="utf-8") as f:
        content = f.read()
    assert "atlas.cli" not in content


# --- deleted module guards: Sprint 197 zero-caller candidates still present ---
# These tests assert the current state — they become EXPECTED TO FAIL after Sprint 198 removes them.
# Sprint 198 will replace these with absence guards.


def test_kpi_service_still_present_sprint197():
    """kpi_service.py identified as zero-production-caller candidate for Sprint 198 removal."""
    import atlas.services.kpi_service as mod

    assert hasattr(mod, "gross_margin")
    assert hasattr(mod, "operating_margin")
    assert hasattr(mod, "net_margin")
    assert hasattr(mod, "fcf_margin")
    assert hasattr(mod, "safe_divide")


def test_investment_report_shim_still_present_sprint197():
    """atlas/models/investment_report.py identified as dead re-export shim for Sprint 198 removal."""
    import atlas.models.investment_report as mod

    assert hasattr(mod, "InvestmentReport")
    assert hasattr(mod, "ScoreCategory")


def test_investment_card_still_present_sprint197():
    """atlas/reports/investment_card.py identified as zero-caller dead function for Sprint 198 removal."""
    import atlas.reports.investment_card as mod

    assert hasattr(mod, "generate_investment_card")


# --- schema / ORM gap awareness ---


def test_company_model_importable():
    from atlas.models import Company

    assert Company is not None


def test_financial_history_model_importable():
    from atlas.models import FinancialHistory

    assert FinancialHistory is not None
