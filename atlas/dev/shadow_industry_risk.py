"""What Financial Risk would say if Atlas knew each issuer's industry.

Atlas withholds Financial Risk for every European holding with the single
gap `industry_unknown`, because no connected source classifies a Stockholm
or Paris listing. Deciding whether a licensed classification is worth
buying means knowing what it would actually buy -- which of those holdings
would then conclude, and which would still withhold for some other reason.

This answers that without writing anything. It reads the stored records,
substitutes an industry label supplied on the command line, and runs the
real `evaluate_financial_risk` -- the same function the production pipeline
calls, unmodified. Nothing is persisted, no Case is composed, no provider
is contacted.

    python -m atlas.dev.shadow_industry_risk [--database PATH]
        [--industry TICKER='Some Label' ...] [--all-as LABEL]

`--industry` supplies one issuer's label; `--all-as` supplies the same
label for every issuer named, which is how you see whether an issuer is
blocked by its industry or by something underneath it.

**The label is evidence, not a guess.** Whatever is passed here should be
what a real source says. Passing a plausible-sounding label produces a
plausible-sounding answer, and that is exactly the mistake this tool exists
to stop being made by hand: a hard-coded "Industrials" once made three
holdings look covered when Atlas had no industry for any of them.
"""
from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone

from sqlalchemy import create_engine

from atlas.alpha.business_data_refresh.repository import SqlAlchemyBusinessRecordRepository
from atlas.analysis_engine.business_data.sources import SourceKind
from atlas.analysis_engine.business_data.versioning import latest_versions
from atlas.analysis_engine.business_facts.extraction import extract_facts_from_records
from atlas.analysis_engine.pipeline import _company_industry
from atlas.analysis_engine.risk.applicability import debt_burden_measure_applies
from atlas.analysis_engine.risk.financial_risk import evaluate_financial_risk
from atlas.core.infrastructure.config.database import resolve_database_path
from atlas.dev.guard import ensure_development_environment

#: The holdings whose Financial Risk is blocked on industry today.
EUROPEAN_HOLDINGS = ("ALFA", "MTRS", "ASSA-B", "VOLV-B", "ATCO-B", "INVE-B", "SU.PA", "SAND")


def _outcome(repository, ticker: str, industry: str | None, evaluated_at: datetime):
    records = latest_versions(tuple(repository.get_by_company(ticker)))
    if not records:
        return None
    statements = frozenset(r.id for r in records if r.document_type is SourceKind.FINANCIAL_STATEMENT)
    facts = extract_facts_from_records(records, evaluated_at=evaluated_at)
    return evaluate_financial_risk(
        facts, statement_record_ids=statements, industry=industry, evaluated_at=evaluated_at)


def main(argv: list[str] | None = None) -> int:
    ensure_development_environment()
    parser = argparse.ArgumentParser(
        prog="python -m atlas.dev.shadow_industry_risk",
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--database", default=None)
    parser.add_argument("--industry", action="append", default=[], metavar="TICKER=LABEL",
                        help="The label a real source gives this issuer.")
    parser.add_argument("--all-as", default=None, metavar="LABEL",
                        help="Apply one label to every issuer, to see what industry alone unblocks.")
    arguments = parser.parse_args(argv)

    supplied: dict[str, str] = {}
    for pair in arguments.industry:
        ticker, _, label = pair.partition("=")
        if not label:
            print(f"--industry expects TICKER=LABEL, got {pair!r}", file=sys.stderr)
            return 2
        supplied[ticker] = label

    path = arguments.database or resolve_database_path()
    repository = SqlAlchemyBusinessRecordRepository(create_engine(f"sqlite:///{path}", future=True))
    evaluated_at = datetime.now(timezone.utc)

    print(f"database : {path}")
    print("writes   : none -- this reads records and evaluates; it stores nothing\n")
    header = f"{'holding':9}{'industry supplied':34}{'applies?':10}{'now':20}{'would be':20}gaps"
    print(header)
    print("-" * len(header))
    for ticker in EUROPEAN_HOLDINGS:
        label = supplied.get(ticker, arguments.all_as)
        before = _outcome(repository, ticker, None, evaluated_at)
        if before is None:
            print(f"{ticker:9}no records")
            continue
        # The industry Atlas genuinely holds, so a holding that already has
        # one is not silently overwritten by the experiment.
        actual = _company_industry(latest_versions(tuple(repository.get_by_company(ticker))))
        after = _outcome(repository, ticker, label or actual, evaluated_at)
        gaps = [getattr(g, "value", g) for g in after.missing_evidence]
        applies = debt_burden_measure_applies(label or actual)
        print(f"{ticker:9}{str(label or actual):34}{str(applies):10}"
              f"{before.status.value:20}{after.status.value:20}{gaps}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
