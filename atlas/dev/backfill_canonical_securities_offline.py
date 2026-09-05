"""Create CanonicalSecurities from already-stored profile evidence.

Zero provider calls. Every company handled here already has a
`company_profile` document in `business_records` carrying the name,
exchange, currency and country that `CanonicalSecurity` requires -- it
was captured before the Identity Gate existed and nothing has ever acted
on it.

**Routed through the production Identity Gate, not ad-hoc inserts.** The
stored profile is rebuilt into the same `RawBusinessDocument` shape a
live fetch produces and handed to `CanonicalSecurityIdentityGate
.evaluate()`. That means candidate mapping, resolution, confidence
scoring, issuer creation and the persisted resolution audit record all
happen exactly as they would for a live company. The only difference is
where the bytes came from, and the gate cannot tell -- which is the
point: no second creation path exists that could drift from the real one.

**What it will not do.** No live call, no symbol search, no fuzzy
matching, no cross-venue linking. It refuses any company whose plan is
not `READY_TO_CREATE`, and it refuses to touch a ticker/exchange pair a
CanonicalSecurity already claims.

Dry run by default; `--apply` to write. Back up the database first.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from datetime import datetime, timezone

from sqlalchemy import create_engine, select

from atlas.alpha.business_data_refresh.table import business_record_table, create_business_record_table
from atlas.alpha.canonical_security.population import PopulationOutcome, plan_security_population
from atlas.alpha.canonical_security.repository import SqlAlchemyCanonicalSecurityRepository
from atlas.alpha.canonical_security.table import (
    canonical_securities_table,
    create_canonical_security_tables,
)
from atlas.alpha.canonical_security_gate.exchange_mapping import map_exchange_display_name_to_mic
from atlas.alpha.canonical_security_gate.factory import build_identity_gate
from atlas.analysis_engine.business_data.models import RawBusinessDocument
from atlas.analysis_engine.business_data.sources import SourceKind


def _document(company: str, provider_id: str, metadata: dict, evaluated_at: datetime) -> RawBusinessDocument:
    """Rebuild the stored profile into the exact shape a live
    `fetch_company_profile` returns, so the gate sees no difference."""
    return RawBusinessDocument(
        identifier=f"{company}:profile:offline-backfill",
        company=company,
        source_kind=SourceKind.COMPANY_PROFILE.value,
        published_at=evaluated_at,
        provider_id=provider_id,
        raw_reference=f"stored://business_records/company_profile/{company}",
        content_hash=f"offline-backfill-{company}",
        language="en",
        metadata=metadata,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", default="database/atlas.db")
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    engine = create_engine(f"sqlite:///{args.database}", future=True)
    create_business_record_table(engine)
    create_canonical_security_tables(engine)
    securities = SqlAlchemyCanonicalSecurityRepository(engine)
    gate = build_identity_gate(engine)

    with engine.connect() as connection:
        existing = {row[0] for row in connection.execute(select(canonical_securities_table.c.native_ticker))}
        profile_rows = (
            connection.execute(
                select(
                    business_record_table.c.company,
                    business_record_table.c.provider_id,
                    business_record_table.c.metadata_json,
                )
                .where(business_record_table.c.document_type == "company_profile")
                .order_by(business_record_table.c.version_created_at)
            )
            .mappings()
            .all()
        )
        companies = sorted(
            {row[0] for row in connection.execute(select(business_record_table.c.company))}
        )

    profiles: dict[str, list[dict]] = defaultdict(list)
    provider_of: dict[str, str] = {}
    for row in profile_rows:
        try:
            profiles[row["company"]].append(json.loads(row["metadata_json"] or "{}"))
        except json.JSONDecodeError:
            continue
        provider_of[row["company"]] = row["provider_id"]

    plans = [
        plan_security_population(
            company, has_security=company in existing, profiles=tuple(profiles.get(company, ()))
        )
        for company in companies
    ]
    ready = [plan for plan in plans if plan.outcome is PopulationOutcome.READY_TO_CREATE]

    print(f"  companies                    : {len(companies)}")
    print(f"  securities before            : {len(existing)}")
    print(f"  READY_TO_CREATE              : {len(ready)}\n")

    eligible = []
    for plan in ready:
        profile = plan.profile or {}
        mic = map_exchange_display_name_to_mic(profile.get("exchange"))
        refusal = None
        if mic is None:
            refusal = f"exchange {profile.get('exchange')!r} maps to no MIC"
        elif securities.find_by_ticker_and_exchange(plan.company, mic.value) is not None:
            refusal = f"a CanonicalSecurity already claims {plan.company}/{mic.value}"
        status = "REFUSED: " + refusal if refusal else "eligible"
        print(
            f"    {plan.company:8s} {str(profile.get('name'))[:32]:32s} "
            f"{str(profile.get('exchange')):8s} {str(mic.value if mic else '-'):6s} "
            f"{str(profile.get('currency')):4s} {str(profile.get('country')):4s}  {status}"
        )
        if not refusal:
            eligible.append(plan)

    print(f"\n  eligible for offline creation: {len(eligible)}")
    if not eligible:
        print("  Nothing to do.")
        return 0
    if not args.apply:
        print("\n  DRY RUN -- nothing written. Re-run with --apply.")
        return 0

    now = datetime.now(timezone.utc)
    created, refused = 0, []
    for plan in eligible:
        document = _document(plan.company, provider_of.get(plan.company, "alpha_vantage"), plan.profile or {}, now)
        decision = gate.evaluate(ticker=plan.company, documents=(document,), clock=lambda: now)
        if decision.allowed:
            created += 1
        else:
            refused.append((plan.company, decision.outcome))

    with engine.connect() as connection:
        after = connection.execute(select(canonical_securities_table.c.native_ticker)).all()
    print(f"\n  securities created           : {created}")
    print(f"  refused by the gate          : {refused or 'none'}")
    print(f"  securities after             : {len(after)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
