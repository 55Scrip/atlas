"""One-off database repair: remove the 16 false `NO_MATCH` resolution
records written by the throttled coverage replay of 2026-09-01.

**Why these rows are wrong.** `CanonicalSecurityIdentityGate.evaluate()`
persists *every* attempt it is given, including the zero-candidate case,
as a `NO_MATCH` record whose documented meaning is:

    "No provider returned any identity-bearing candidate for this ticker."

That sentence is false for these 16. Alpha Vantage rejected every call
with an explicit daily-rate-limit payload *before* returning any
identity data, so nothing was ever learned about the companies. The rows
assert a per-company identity failure that never happened, and are
indistinguishable from a genuine one -- exactly the "one word meaning
several things" failure the Provider Quota Intelligence sprint exists to
remove. The behaviour that created them is already fixed in `fc1375c`
(`refresh_company_data` now returns `NOT_EVALUATED_PROVIDER_THROTTLED`
without calling the gate); this script removes the rows that fix arrived
too late to prevent.

**Why deletion rather than annotation.** The schema has no annotation
field, and a row whose `outcome` column reads `NO_MATCH` will keep being
read as one by every consumer.

**Safety.** This script is idempotent and refuses to delete anything
that does not match the full proven signature -- it re-derives every
precondition itself rather than trusting the id list. Running it twice
is a no-op. Run with `--apply` to actually delete; the default is a dry
run.

Deliberately out of scope: the older `NO_MATCH` rows from the 2026-08-28
import, when `ALPHA_VANTAGE_API_KEY` was unreadable. Those are equally
not genuine identity failures, but they have not been audited and are a
separate task.
"""
from __future__ import annotations

import argparse
import sqlite3
import sys

#: The exact rows this repair removes, captured during the 2026-09-01
#: audit. Listed explicitly so the script can never widen its own blast
#: radius: a row is deleted only if its id appears here AND it
#: independently satisfies every check in `_verify`.
TARGET_ROW_IDS: tuple[str, ...] = (
    "5a2ed8f6-e4aa-4ed0-a6d5-c01f266f4999",  # INVE-B
    "adb6e629-3b8f-4f5c-8d29-083a0ec75dc5",  # AVGO
    "294b0c4e-8e4e-4547-b1af-724d42d6fa5a",  # TSMC
    "80f4173f-3b66-4648-aa33-826b7866c79b",  # VST
    "1c3f85fa-88f4-4c7b-b4bc-4925a75fcbef",  # ABB
    "b33f8876-a440-433f-84a8-eb1c83d09acb",  # BRK.B
    "6a65b3aa-b1f2-4aee-bdfb-08bf9eea5352",  # VOLV-B
    "d8803289-9436-4a47-afbd-00af284146ef",  # ALFA
    "ef872de1-88f1-49f0-b2f0-a24cd8257d44",  # SAND
    "403a70ff-2b29-4d60-a53a-5ce697952164",  # SU.PA
    "ca7a99a7-8a44-48e7-afab-1bc7810b2614",  # ATCO-B
    "49630c7d-a9f2-47c6-9058-7127fd076bb3",  # ASSA-B
    "8262a4f4-57df-4b68-b98d-fabda630e1e4",  # NVO
    "5c05bdf9-6950-415f-a2c2-0b214c2b553b",  # VRT
    "3f759e5e-46e2-4071-b103-c5c50f63aba5",  # MTRS
    "04390c10-db21-410c-815a-ebdba6b66d07",  # LATO-B
)

#: The replay's own window. A row outside it is never touched, even if
#: its id is listed above.
_REPLAY_WINDOW_PREFIX = "2026-09-01T00:05:"

_TABLE = "canonical_security_resolution_records"
_EVIDENCE_TABLE = "canonical_security_resolution_evidence"


class RepairRefused(RuntimeError):
    """A precondition failed. Nothing is deleted."""


def _verify(connection: sqlite3.Connection) -> list[sqlite3.Row]:
    """Re-derives the proof from the database itself. Returns the rows
    safe to delete, or raises."""
    placeholders = ",".join("?" * len(TARGET_ROW_IDS))
    rows = list(
        connection.execute(
            f"""select id, investor_ticker, outcome, resolved_at,
                       existing_canonical_security_id, resulting_canonical_security_id
                from {_TABLE} where id in ({placeholders})""",
            TARGET_ROW_IDS,
        )
    )
    if not rows:
        return []

    for row in rows:
        if row["outcome"] != "NO_MATCH":
            raise RepairRefused(f"{row['id']}: outcome is {row['outcome']!r}, expected NO_MATCH")
        if row["resulting_canonical_security_id"] is not None:
            raise RepairRefused(f"{row['id']}: produced a canonical security; a real resolution")
        if row["existing_canonical_security_id"] is not None:
            raise RepairRefused(f"{row['id']}: compared against an existing canonical security")
        if not str(row["resolved_at"]).startswith(_REPLAY_WINDOW_PREFIX):
            raise RepairRefused(f"{row['id']}: resolved_at {row['resolved_at']!r} is outside the replay window")

    attached = connection.execute(
        f"select count(*) from {_EVIDENCE_TABLE} where resolution_record_id in ({placeholders})",
        TARGET_ROW_IDS,
    ).fetchone()[0]
    if attached:
        raise RepairRefused(
            f"{attached} candidate-evidence rows are attached -- a throttled attempt cannot have any, "
            "so these are not the rows this repair targets"
        )
    return rows


def _unrelated_fingerprint(connection: sqlite3.Connection) -> tuple[int, str]:
    """Count and checksum of every resolution record this repair must
    NOT touch -- compared before and after to prove the blast radius."""
    placeholders = ",".join("?" * len(TARGET_ROW_IDS))
    row = connection.execute(
        f"""select count(*), coalesce(group_concat(id, '|'), '')
            from (select id from {_TABLE} where id not in ({placeholders}) order by id)""",
        TARGET_ROW_IDS,
    ).fetchone()
    import hashlib

    return row[0], hashlib.sha256(row[1].encode("utf-8")).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", default="database/atlas.db")
    parser.add_argument("--apply", action="store_true", help="actually delete (default: dry run)")
    args = parser.parse_args()

    connection = sqlite3.connect(args.database)
    connection.row_factory = sqlite3.Row

    try:
        rows = _verify(connection)
    except RepairRefused as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        return 2

    if not rows:
        print("Nothing to do -- the targeted rows are already absent (repair is idempotent).")
        return 0

    before_count, before_hash = _unrelated_fingerprint(connection)
    total_before = connection.execute(f"select count(*) from {_TABLE}").fetchone()[0]

    print(f"Verified {len(rows)} rows safe to delete:")
    for row in rows:
        print(f"  {row['investor_ticker']:9s} {row['resolved_at'][:19]}  {row['id']}")

    if not args.apply:
        print("\nDRY RUN -- nothing deleted. Re-run with --apply.")
        return 0

    placeholders = ",".join("?" * len(TARGET_ROW_IDS))
    with connection:
        connection.execute(f"delete from {_TABLE} where id in ({placeholders})", TARGET_ROW_IDS)

    after_count, after_hash = _unrelated_fingerprint(connection)
    total_after = connection.execute(f"select count(*) from {_TABLE}").fetchone()[0]

    print(f"\nresolution records : {total_before} -> {total_after}  (removed {total_before - total_after})")
    print(f"unrelated records  : {before_count} -> {after_count}")
    print(f"unrelated checksum : {'UNCHANGED' if before_hash == after_hash else 'CHANGED -- INVESTIGATE'}")
    integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
    orphans = connection.execute(
        f"""select count(*) from {_EVIDENCE_TABLE} e
            where not exists (select 1 from {_TABLE} r where r.id = e.resolution_record_id)"""
    ).fetchone()[0]
    print(f"integrity_check    : {integrity}")
    print(f"orphaned evidence  : {orphans}")

    if before_hash != after_hash or integrity != "ok" or orphans:
        print("POST-CONDITION FAILED", file=sys.stderr)
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main())
