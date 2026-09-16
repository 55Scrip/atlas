"""The firewall around class economic-rights evidence and the issuer
common-equity composer: a closed set of importers. Since fiscal_epoch_v3 the
valuation reads them -- only through Case composition's issuer valuation
basis; no recommendation, narrative, snapshot or Decision Layer module names
the evidence, its tables or its methodology."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]


def _importers(fragment: str, *, skip_dir: str = "") -> set[str]:
    out = set()
    for p in (ROOT / "atlas").rglob("*.py"):
        rel = str(p.relative_to(ROOT))
        if skip_dir and rel.startswith(skip_dir):
            continue
        if any(line.lstrip().startswith(("from ", "import ")) and fragment in line for line in p.read_text().splitlines()):
            out.add(rel)
    return out


def test_rights_evidence_is_read_only_by_its_write_path_and_the_issuer_composers():
    assert _importers("class_rights_evidence", skip_dir="atlas/alpha/class_rights_evidence/") == {
        "atlas/alpha/business_data_refresh/class_rights_evidence.py",
        "atlas/alpha/issuer_equity/claims.py",
        "atlas/alpha/issuer_equity/composer.py",
        "atlas/alpha/issuer_equity/reader.py",
        "atlas/dev/backfill_class_rights_evidence.py",
        "atlas/dev/derive_class_rights_series_terms.py",
    }


def test_the_composers_are_reached_only_through_case_composition_wiring_and_the_operator_command():
    assert _importers("issuer_equity", skip_dir="atlas/alpha/issuer_equity/") == {
        "atlas/alpha/investment_case/service.py",
        "atlas/alpha/investment_case/api/dependencies.py",
        "atlas/alpha/discovery_context/dependencies.py",
        "atlas/alpha/monitoring/api/dependencies.py",
        "atlas/alpha/portfolio_cockpit/api/dependencies.py",
        "atlas/dev/backfill_class_rights_evidence.py",
        # Case composition wiring for the scheduled batch -- the engine-built
        # twin of `investment_case/api/dependencies.py`, reached only by the
        # operator command. Still no recommendation, narrative, snapshot or
        # Decision Layer module names the evidence.
        "atlas/alpha/scheduled_composition/factory.py",
    }


def test_the_rights_adapter_is_reached_only_through_business_data_refresh():
    assert _importers("sec_edgar_class_rights", skip_dir="atlas/business_data_providers/") == {
        "atlas/alpha/business_data_refresh/class_rights_evidence.py"}


def test_no_decision_layer_names_the_tables_or_the_methodology():
    names = ("class_rights_observations", "class_rights_filings", "issuer_common_equity_market_cap_v1")
    hits = {str(p.relative_to(ROOT)) for p in (ROOT / "atlas").rglob("*.py") if any(n in p.read_text() for n in names)}
    assert hits == {"atlas/alpha/class_rights_evidence/table.py", "atlas/alpha/class_rights_evidence/repository.py",
                    "atlas/analysis_engine/valuation/issuer_basis.py"}
