"""The decision firewall around class economic-rights evidence and the
issuer common-equity composer: a closed set of importers. Nothing that
values, recommends, narrates or snapshots a Case reads either."""
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


def test_rights_evidence_is_read_only_by_its_write_path_and_the_composer():
    assert _importers("class_rights_evidence", skip_dir="atlas/alpha/class_rights_evidence/") == {
        "atlas/alpha/business_data_refresh/class_rights_evidence.py",
        "atlas/alpha/issuer_equity/composer.py",
        "atlas/alpha/issuer_equity/reader.py",
        "atlas/dev/backfill_class_rights_evidence.py",
    }


def test_the_composer_is_reached_only_by_the_operator_command():
    assert _importers("issuer_equity", skip_dir="atlas/alpha/issuer_equity/") == {"atlas/dev/backfill_class_rights_evidence.py"}


def test_the_rights_adapter_is_reached_only_through_business_data_refresh():
    assert _importers("sec_edgar_class_rights", skip_dir="atlas/business_data_providers/") == {
        "atlas/alpha/business_data_refresh/class_rights_evidence.py"}


def test_no_decision_layer_names_the_tables_or_the_methodology():
    names = ("class_rights_observations", "class_rights_filings", "issuer_common_equity_market_cap_v1")
    hits = {str(p.relative_to(ROOT)) for p in (ROOT / "atlas").rglob("*.py") if any(n in p.read_text() for n in names)}
    assert hits == {"atlas/alpha/class_rights_evidence/table.py", "atlas/alpha/class_rights_evidence/repository.py",
                    "atlas/alpha/issuer_equity/composer.py"}
