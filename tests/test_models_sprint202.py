"""Sprint 202 guardrail tests for atlas/models/ package audit.

Verifies:
- Company and FinancialHistory are importable from atlas.models
- atlas.models.__all__ contains exactly the expected exports
- atlas.models.investment_report is absent (Sprint 198 removal guard)
- atlas.models does not import providers, services, or CLI modules
- atlas.reports is absent (Sprint 198 removal guard)
"""
import importlib
import importlib.util
import sys
import types


def test_company_model_importable_sprint202():
    from atlas.models import Company

    assert Company is not None
    assert Company.__tablename__ == "companies"


def test_financial_history_model_importable_sprint202():
    from atlas.models import FinancialHistory

    assert FinancialHistory is not None
    assert FinancialHistory.__tablename__ == "financial_history"


def test_models_all_exports_sprint202():
    import atlas.models

    assert set(atlas.models.__all__) == {"Company", "FinancialHistory"}


def test_models_investment_report_absent_sprint202():
    try:
        spec = importlib.util.find_spec("atlas.models.investment_report")
    except ModuleNotFoundError:
        spec = None
    assert spec is None, "atlas.models.investment_report must remain absent (Sprint 198 removal)"


def test_atlas_reports_absent_sprint202():
    try:
        spec = importlib.util.find_spec("atlas.reports")
    except ModuleNotFoundError:
        spec = None
    assert spec is None, "atlas.reports must remain absent (Sprint 198 removal)"


def test_models_entities_no_provider_import_sprint202():
    import atlas.models.entities as entities_mod

    source = importlib.util.find_spec("atlas.models.entities").origin
    with open(source) as f:
        content = f.read()
    assert "atlas.providers" not in content
    assert "from atlas.providers" not in content


def test_models_entities_no_service_import_sprint202():
    import atlas.models.entities as entities_mod

    source = importlib.util.find_spec("atlas.models.entities").origin
    with open(source) as f:
        content = f.read()
    assert "atlas.services" not in content
    assert "from atlas.services" not in content


def test_models_entities_no_cli_import_sprint202():
    source = importlib.util.find_spec("atlas.models.entities").origin
    with open(source) as f:
        content = f.read()
    assert "atlas.cli" not in content
    assert "from atlas.cli" not in content


def test_models_init_no_investment_report_reference_sprint202():
    source = importlib.util.find_spec("atlas.models").origin
    with open(source) as f:
        content = f.read()
    assert "investment_report" not in content
    assert "InvestmentReport" not in content


def test_models_unknown_attr_raises_sprint202():
    import atlas.models
    import pytest

    with pytest.raises(AttributeError):
        _ = atlas.models.NonExistentSymbol
