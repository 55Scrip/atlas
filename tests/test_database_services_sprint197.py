"""Sprint 197/198 guardrail tests: atlas/database/ and atlas/services/ audit.

Sprint 198 updated: replaced Sprint 197 "still present" stubs with absence guards
for the three zero-caller dead symbols removed in Sprint 198.
"""

import importlib


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


# --- deleted module guards: Sprint 198 removal confirmed absent ---


def test_kpi_service_removed_sprint198():
    """atlas/services/kpi_service.py removed Sprint 198 — zero production callers confirmed."""
    import importlib.util

    assert importlib.util.find_spec("atlas.services.kpi_service") is None


def test_investment_report_shim_removed_sprint198():
    """atlas/models/investment_report.py removed Sprint 198 — dead re-export shim, zero callers."""
    import importlib.util

    assert importlib.util.find_spec("atlas.models.investment_report") is None


def test_investment_card_removed_sprint198():
    """atlas/reports/investment_card.py removed Sprint 198 — dead function, zero callers."""
    import importlib.util

    try:
        spec = importlib.util.find_spec("atlas.reports.investment_card")
    except ModuleNotFoundError:
        spec = None
    assert spec is None


def test_atlas_reports_package_removed_sprint198():
    """atlas/reports/ directory removed Sprint 198 — package was empty after investment_card removal."""
    import importlib.util

    assert importlib.util.find_spec("atlas.reports") is None


# --- schema / ORM gap awareness ---


def test_company_model_importable():
    from atlas.models import Company

    assert Company is not None


def test_financial_history_model_importable():
    from atlas.models import FinancialHistory

    assert FinancialHistory is not None
