"""Calibration benchmark harness -- canonical reasoning edition.

Replaces the Phase 9 harness's reliance on process-state codes. That
harness read `readiness_support/monitoring_current` and
`decision_support_reached` and scored them as investment rationale,
which is why nine companies appeared to share one explanation.

**The contract, stated once:**

  reasoning payload present   -> score the canonical rationale
  payload absent (legacy row) -> UNSCORABLE for every canonical
                                 dimension; never scored as empty
  payload present but empty   -> scorable, and genuinely empty:
                                 reasoning ran and concluded nothing

There is no fallback inference. `change_trigger` is a readiness
blocker and is read only as diagnostics, never as `whatWouldChange`.

Read-only. Point `--database` at a copy if in doubt.
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import sys

from sqlalchemy import create_engine, text

from atlas.analysis_engine.reasoning import (
    LEGACY_RESULT_WITHOUT_REASONING,
    deserialize_reasoning,
)

#: How a row's canonical rationale may be classified. Closed set, so a
#: new state cannot appear without being named here.
CANONICAL = "canonical"
CANONICAL_EMPTY = "canonical_empty"
LEGACY = LEGACY_RESULT_WITHOUT_REASONING


def classify(payload: dict | None) -> str:
    stored = deserialize_reasoning(payload)
    if stored is None:
        return LEGACY
    if not stored.primary_drivers and not stored.counter_drivers:
        return CANONICAL_EMPTY
    return CANONICAL


def collect(database: str) -> list[dict]:
    engine = create_engine(f"sqlite:///{database}", future=True)
    rows: list[dict] = []
    with engine.connect() as connection:
        for ticker, result_json in connection.execute(text(
            "select ticker, result_json from investment_decision_results order by ticker"
        )):
            payload = json.loads(result_json or "{}")
            reasoning_payload = payload.get("reasoning")
            state = classify(reasoning_payload)
            stored = deserialize_reasoning(reasoning_payload)
            rows.append({
                "ticker": ticker,
                # B: authoritative decision fields, owned elsewhere.
                "action": payload.get("action"),
                # A: canonical analytical rationale -- the only fields
                # scored as investment reasoning.
                "reasoning_state": state,
                "primary_drivers": [r.kind.value for r in stored.primary_drivers] if stored else None,
                "counter_drivers": [r.kind.value for r in stored.counter_drivers] if stored else None,
                "what_would_change": list(stored.what_would_change) if stored else None,
                "signal_summary": [
                    {"engine": c.engine.value, "state": c.state.value,
                     "influencedDirection": c.influenced_direction}
                    for c in stored.signal_summary
                ] if stored else None,
                "key_unknowns": [
                    {"kind": u.kind.value, "engine": u.engine.value} for u in stored.key_unknowns
                ] if stored else None,
                "conviction_reasoning": None if not stored or stored.conviction is None else {
                    "level": stored.conviction.level.value if stored.conviction.level else None,
                    "evidential": [r.kind.value for r in stored.conviction.evidential_reasons],
                    "analytical": [r.kind.value for r in stored.conviction.analytical_reasons],
                },
                # C/D: diagnostics only. Never scored as rationale.
                "diagnostic_process_reasons": [
                    f"{r.get('source')}/{r.get('code')}" for r in payload.get("supportingReasons", ())
                ],
                "diagnostic_legacy_change_trigger": payload.get("changeTrigger"),
            })
    return rows


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--database", default="database/atlas.db")
    parser.add_argument("--out")
    args = parser.parse_args()

    rows = collect(args.database)
    blob = json.dumps(rows, sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha256(blob.encode()).hexdigest()[:16]
    if args.out:
        with open(args.out, "w") as handle:
            handle.write(blob)

    states = collections.Counter(r["reasoning_state"] for r in rows)
    print(f"  rows: {len(rows)}   digest: {digest}")
    print(f"  canonical        : {states[CANONICAL]}")
    print(f"  canonical_empty  : {states[CANONICAL_EMPTY]}")
    print(f"  {LEGACY:17s}: {states[LEGACY]}   (UNSCORABLE for canonical dimensions)")

    scorable = [r for r in rows if r["reasoning_state"] != LEGACY]
    print(f"\n  scorable rows: {len(scorable)} / {len(rows)}")
    distinct = {(tuple(r["primary_drivers"] or ()), tuple(r["counter_drivers"] or ()))
                for r in scorable}
    print(f"  distinct driver sets among scorable: {len(distinct)}")
    for row in scorable[:40]:
        print(f"    {str(row['ticker']):8s} {str(row['action']):11s} "
              f"+{row['primary_drivers']} -{row['counter_drivers']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
