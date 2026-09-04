"""One-off maintenance: attach a CanonicalSecurity to historical
BusinessRecords whose security identity can now be proven.

All decisions come from `canonical_security.security_provenance`, which
is pure and tested; this script only gathers evidence out of the
database, reports the plan, and -- with `--apply` -- writes the
`PROVABLE_SECURITY` rows and nothing else.

Dry run by default. `--apply` requires a backup to already exist.
"""
from __future__ import annotations

import argparse
import collections
import json
import shutil
import sys
from datetime import datetime, timezone

from sqlalchemy import create_engine, text

from atlas.alpha.canonical_security.issuer_cik import normalize_cik
from atlas.alpha.canonical_security.security_provenance import (
    CikSecurityEvidence,
    SecurityProvenanceOutcome,
    plan_security_provenance_repair,
)

DB = "database/atlas.db"


def _gather(connection):
    securities_by_issuer: dict[str, set[str]] = collections.defaultdict(set)
    security_issuer: dict[str, str] = {}
    for sid, iid in connection.execute(text("select id, issuer_id from canonical_securities")):
        security_issuer[sid] = iid
        if iid:
            securities_by_issuer[iid].add(sid)

    linked: dict[str, set[str]] = collections.defaultdict(set)
    companies: dict[str, set[str]] = collections.defaultdict(set)
    for company, metadata_json, sid in connection.execute(text(
        "select company, metadata_json, canonical_security_id from business_records "
        "where metadata_json is not null"
    )):
        cik = normalize_cik((json.loads(metadata_json) or {}).get("sec_cik"))
        if not cik:
            continue
        companies[cik].add(company)
        if sid:
            linked[cik].add(sid)

    cik_evidence = {
        cik: CikSecurityEvidence(frozenset(linked.get(cik, set())), len(names))
        for cik, names in companies.items()
    }
    return (
        {k: frozenset(v) for k, v in securities_by_issuer.items()},
        security_issuer,
        cik_evidence,
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--database", default=DB)
    args = parser.parse_args()

    engine = create_engine(f"sqlite:///{args.database}", future=True)
    with engine.connect() as connection:
        securities_by_issuer, security_issuer, cik_evidence = _gather(connection)
        records = tuple(
            (rid, sid, iid, json.loads(meta or "{}"))
            for rid, sid, iid, meta in connection.execute(text(
                "select id, canonical_security_id, canonical_issuer_id, metadata_json "
                "from business_records where canonical_issuer_id is not null "
                "and canonical_security_id is null"
            ))
        )
        company_of = {i: c for i, c in connection.execute(
            text("select id, company from business_records"))}

    plans = plan_security_provenance_repair(
        records,
        cik_evidence=cik_evidence,
        securities_by_issuer=securities_by_issuer,
        security_issuer=security_issuer,
    )

    by_outcome = collections.Counter(p.outcome for p in plans)
    print(f"{'MODE':22s} {'APPLY' if args.apply else 'DRY RUN'}")
    print(f"{'records considered':22s} {len(plans)}")
    print("\n  CLASSIFICATION")
    for outcome in SecurityProvenanceOutcome:
        if by_outcome.get(outcome):
            print(f"    {outcome.value:32s} {by_outcome[outcome]:4d}")

    grouped: dict[tuple, list] = collections.defaultdict(list)
    for plan in plans:
        grouped[(company_of.get(plan.record_id), plan.outcome, plan.reason)].append(plan)
    print("\n  BY COMPANY")
    for (company, outcome, reason), group in sorted(grouped.items(), key=lambda kv: str(kv[0][0])):
        print(f"    {company:7s} {len(group):4d}  {outcome.value:30s} {reason}")

    repairs = [p for p in plans if p.outcome is SecurityProvenanceOutcome.PROVABLE_SECURITY]
    print(f"\n  to write: {len(repairs)}   left untouched: {len(plans) - len(repairs)}")
    if not args.apply:
        print("\n  DRY RUN -- nothing written.")
        return 0
    if not repairs:
        print("\n  nothing provable; no write attempted.")
        return 0

    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    backup = f"{args.database}.bak-pre-security-provenance-{stamp}.db"
    shutil.copy2(args.database, backup)
    print(f"\n  backup: {backup}")

    with engine.begin() as connection:
        for plan in repairs:
            connection.execute(
                text("update business_records set canonical_security_id = :sid "
                     "where id = :rid and canonical_security_id is null"),
                {"sid": plan.security_id, "rid": plan.record_id},
            )
    print(f"  wrote {len(repairs)} rows.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
