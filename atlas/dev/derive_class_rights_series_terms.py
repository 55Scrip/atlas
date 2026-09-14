"""Derive preferred-series terms (issuance date, fixed rate to its floating
reset, series share counts) from the class economic-rights evidence Atlas
already holds, and record them as structured observations
(`class_rights_evidence.series_terms`, fiscal_epoch_v3).

Reads only persisted rights evidence -- no provider request of any kind.
Append-only through the rights repository: one transaction per source
filing, recorded under `series_terms_v1`; a filing already recorded under
that version is left exactly as it is, so a second run writes nothing.

    python -m atlas.dev.derive_class_rights_series_terms [--database PATH] [--dry-run]
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone

from sqlalchemy import create_engine

from atlas.alpha.class_rights_evidence.repository import SqlAlchemyClassRightsEvidenceRepository
from atlas.alpha.class_rights_evidence.series_terms import record_series_terms
from atlas.core.infrastructure.config.database import resolve_database_path
from atlas.dev.guard import ensure_development_environment


def main() -> int:
    ensure_development_environment()
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--database", default=None)
    parser.add_argument("--dry-run", action="store_true")
    arguments = parser.parse_args()
    engine = create_engine(f"sqlite:///{arguments.database or resolve_database_path()}", future=True)
    repository = SqlAlchemyClassRightsEvidenceRepository(engine)
    rows = record_series_terms(repository, repository.issuer_ciks(), recorded_at=datetime.now(timezone.utc),
                               dry_run=arguments.dry_run)
    for accession, count, wrote in rows:
        state = "dry-run" if arguments.dry_run else ("recorded" if wrote else "already recorded")
        print(f"  {accession}: {count} series-term observations ({state})")
    print(f"{len(rows)} filings with series terms; {sum(1 for r in rows if r[2])} recorded")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
