"""Legacy identity provenance repair.

570 of 2506 stored records -- 22.7% -- carry an authoritative SEC CIK and
no security link, because they were ingested before the Identity Gate
stamped identity onto records. This repairs what can be repaired from
evidence already held, and refuses the rest.

The two invariants these tests exist to defend, because both would look
identical in the GOOG case and only one is safe:

* identity may come from a shared **identifier**, never from an equal
  **ticker** (`SU.PA` and `SU` would collapse), and
* proving the **issuer** never licenses claiming the **security** (one
  Alphabet 10-K covers both GOOG and GOOGL).
"""
from __future__ import annotations

import pytest

from atlas.alpha.canonical_security.legacy_provenance import (
    ISSUER_LEVEL_DOCUMENT_TYPES,
    LegacyRepairOutcome,
    build_cik_to_issuer_index,
    plan_legacy_repair,
)

ALPHABET_CIK = "0001652044"
APPLE_CIK = "0000320193"
ALPHABET_ISSUER = "issuer-alphabet"


def _linked(record_id, security_id, cik):
    return (record_id, security_id, {"sec_cik": cik} if cik else {})


def _record(record_id, security_id, document_type, cik):
    return (record_id, security_id, document_type, {"sec_cik": cik} if cik else {})


class TestIndexIsBuiltOnlyFromProvenIdentity:
    def test_index_maps_cik_to_issuer_via_linked_records(self):
        index = build_cik_to_issuer_index(
            (_linked("r1", "sec-googl", ALPHABET_CIK),), {"sec-googl": ALPHABET_ISSUER}
        )
        assert index == {ALPHABET_CIK: {ALPHABET_ISSUER}}

    def test_unlinked_records_cannot_vouch_for_their_own_issuer(self):
        """Otherwise the evidence would be circular: a legacy record
        would establish the very fact it is asking to be judged by."""
        index = build_cik_to_issuer_index((_linked("r1", None, ALPHABET_CIK),), {})
        assert index == {}

    def test_a_security_with_no_issuer_contributes_nothing(self):
        index = build_cik_to_issuer_index(
            (_linked("r1", "sec-x", ALPHABET_CIK),), {"sec-x": None}
        )
        assert index == {}

    def test_one_cik_seen_for_two_issuers_is_recorded_as_ambiguous(self):
        index = build_cik_to_issuer_index(
            (_linked("r1", "sec-a", ALPHABET_CIK), _linked("r2", "sec-b", ALPHABET_CIK)),
            {"sec-a": "issuer-1", "sec-b": "issuer-2"},
        )
        assert index[ALPHABET_CIK] == {"issuer-1", "issuer-2"}


class TestTheGoogProofCase:
    """GOOG has CIK-bearing records, no security link, and no
    CanonicalSecurity row. GOOGL's linked records establish the CIK."""

    def _index(self):
        return build_cik_to_issuer_index(
            (_linked("googl-1", "sec-googl", ALPHABET_CIK),), {"sec-googl": ALPHABET_ISSUER}
        )

    def test_goog_filings_attach_to_alphabets_issuer(self):
        repairs = plan_legacy_repair(
            (_record("goog-1", None, "financial_statement", ALPHABET_CIK),), self._index()
        )
        assert repairs[0].outcome is LegacyRepairOutcome.ISSUER_PROVEN
        assert repairs[0].canonical_issuer_id == ALPHABET_ISSUER

    def test_the_repair_never_claims_a_security(self):
        """One Alphabet 10-K covers both GOOG and GOOGL, so a CIK cannot
        say which listing produced the record."""
        repairs = plan_legacy_repair(
            (_record("goog-1", None, "financial_statement", ALPHABET_CIK),), self._index()
        )
        assert "canonical_security_id" not in repairs[0].__dataclass_fields__

    def test_an_already_linked_record_is_left_alone(self):
        repairs = plan_legacy_repair(
            (_record("googl-1", "sec-googl", "financial_statement", ALPHABET_CIK),), self._index()
        )
        assert repairs[0].outcome is LegacyRepairOutcome.ALREADY_LINKED
        assert repairs[0].canonical_issuer_id is None


class TestNoTickerBackfillInvariant:
    def test_the_planner_is_never_given_a_ticker_at_all(self):
        """Structural, not behavioural: a future edit cannot quietly
        start matching on one because the parameter does not exist.

        Scans the executable body only -- the docstring legitimately
        mentions tickers in order to say they are not used."""
        import inspect

        source = inspect.getsource(plan_legacy_repair)
        body = source.split('"""')[2]
        for forbidden in ("ticker", "company_name", "native_ticker"):
            assert forbidden not in body, forbidden
        assert "ticker" not in str(inspect.signature(plan_legacy_repair))

    def test_su_pa_cannot_inherit_suncors_issuer(self):
        """Both would match on a ticker stem. Neither has a CIK, so
        neither is repairable -- and that is the whole safety story."""
        index = build_cik_to_issuer_index(
            (_linked("su-1", "sec-suncor", None),), {"sec-suncor": "issuer-suncor"}
        )
        repairs = plan_legacy_repair(
            (_record("supa-1", None, "financial_statement", None),), index
        )
        assert repairs[0].outcome is LegacyRepairOutcome.NO_EVIDENCE
        assert repairs[0].canonical_issuer_id is None

    def test_tsmc_does_not_inherit_tsm_issuer_without_a_shared_cik(self):
        index = build_cik_to_issuer_index(
            (_linked("tsm-1", "sec-tsm", "0001046179"),), {"sec-tsm": "issuer-tsm"}
        )
        repairs = plan_legacy_repair((_record("tsmc-1", None, "financial_statement", None),), index)
        assert repairs[0].outcome is LegacyRepairOutcome.NO_EVIDENCE

    def test_volv_b_does_not_inherit_volvf_issuer(self):
        repairs = plan_legacy_repair((_record("volvb-1", None, "financial_statement", None),), {})
        assert repairs[0].outcome is LegacyRepairOutcome.NO_EVIDENCE

    def test_brk_dot_b_and_brk_dash_b_need_a_shared_cik_not_a_similar_ticker(self):
        index = build_cik_to_issuer_index(
            (_linked("brk-1", "sec-brk", "0001067983"),), {"sec-brk": "issuer-brk"}
        )
        # Same CIK -> repairable. Different notation is irrelevant either way.
        ok = plan_legacy_repair((_record("brk-2", None, "company_filing", "0001067983"),), index)
        assert ok[0].outcome is LegacyRepairOutcome.ISSUER_PROVEN
        # No CIK -> not repairable, however similar the ticker looks.
        no = plan_legacy_repair((_record("brk-3", None, "company_filing", None),), index)
        assert no[0].outcome is LegacyRepairOutcome.NO_EVIDENCE


class TestNoNameBackfillInvariant:
    def test_the_planner_never_receives_a_company_name(self):
        repairs = plan_legacy_repair((_record("r1", None, "financial_statement", None),), {})
        assert repairs[0].outcome is LegacyRepairOutcome.NO_EVIDENCE

    def test_volvo_ab_and_volvo_car_ab_cannot_share_by_name(self):
        """Neither has a CIK; name similarity is not an input to this
        module at all."""
        index = build_cik_to_issuer_index(
            (_linked("v-1", "sec-volvo", None),), {"sec-volvo": "issuer-volvo"}
        )
        repairs = plan_legacy_repair((_record("vc-1", None, "financial_statement", None),), index)
        assert repairs[0].canonical_issuer_id is None


class TestContradictionAndAbsence:
    def test_a_cik_mapping_to_two_issuers_refuses_repair(self):
        index = {ALPHABET_CIK: {"issuer-1", "issuer-2"}}
        repairs = plan_legacy_repair(
            (_record("r1", None, "financial_statement", ALPHABET_CIK),), index
        )
        assert repairs[0].outcome is LegacyRepairOutcome.CONTRADICTORY
        assert repairs[0].canonical_issuer_id is None

    def test_a_cik_with_no_known_issuer_is_named_not_guessed(self):
        repairs = plan_legacy_repair(
            (_record("r1", None, "financial_statement", APPLE_CIK),), {}
        )
        assert repairs[0].outcome is LegacyRepairOutcome.NO_ISSUER_FOR_CIK

    def test_a_malformed_cik_is_absent_evidence(self):
        repairs = plan_legacy_repair(
            ((("r1", None, "financial_statement", {"sec_cik": "not-a-cik"})),), {ALPHABET_CIK: {ALPHABET_ISSUER}}
        )
        assert repairs[0].outcome is LegacyRepairOutcome.NO_EVIDENCE


class TestSecuritySpecificExclusions:
    def test_a_price_snapshot_never_receives_issuer_provenance(self):
        """A price belongs to a listing, not to a company. Issuer
        provenance would let it cross a security boundary."""
        index = {ALPHABET_CIK: {ALPHABET_ISSUER}}
        repairs = plan_legacy_repair(
            (_record("p1", None, "market_data_snapshot", ALPHABET_CIK),), index
        )
        assert repairs[0].outcome is LegacyRepairOutcome.SECURITY_SPECIFIC_EXCLUDED
        assert repairs[0].canonical_issuer_id is None

    def test_market_data_is_not_an_issuer_level_document_type(self):
        assert "market_data_snapshot" not in ISSUER_LEVEL_DOCUMENT_TYPES

    @pytest.mark.parametrize("document_type", sorted(ISSUER_LEVEL_DOCUMENT_TYPES))
    def test_issuer_level_kinds_are_eligible(self, document_type):
        repairs = plan_legacy_repair(
            (_record("r1", None, document_type, ALPHABET_CIK),), {ALPHABET_CIK: {ALPHABET_ISSUER}}
        )
        assert repairs[0].outcome is LegacyRepairOutcome.ISSUER_PROVEN


class TestDeterminismAndIdempotence:
    def test_planning_is_deterministic(self):
        args = (
            (_record("r1", None, "financial_statement", ALPHABET_CIK),),
            {ALPHABET_CIK: {ALPHABET_ISSUER}},
        )
        assert plan_legacy_repair(*args) == plan_legacy_repair(*args)

    def test_replanning_after_repair_targets_the_same_issuer(self):
        """The script skips a record already at its target value, so a
        second run writes nothing."""
        index = {ALPHABET_CIK: {ALPHABET_ISSUER}}
        first = plan_legacy_repair((_record("r1", None, "financial_statement", ALPHABET_CIK),), index)
        second = plan_legacy_repair((_record("r1", None, "financial_statement", ALPHABET_CIK),), index)
        assert first[0].canonical_issuer_id == second[0].canonical_issuer_id == ALPHABET_ISSUER

    def test_index_construction_is_order_independent(self):
        forward = build_cik_to_issuer_index(
            (_linked("a", "sec-1", ALPHABET_CIK), _linked("b", "sec-1", ALPHABET_CIK)),
            {"sec-1": ALPHABET_ISSUER},
        )
        backward = build_cik_to_issuer_index(
            (_linked("b", "sec-1", ALPHABET_CIK), _linked("a", "sec-1", ALPHABET_CIK)),
            {"sec-1": ALPHABET_ISSUER},
        )
        assert forward == backward


class TestArchitectureBoundaries:
    def test_module_imports_no_provider_and_no_repository(self):
        from pathlib import Path

        source = Path("atlas/alpha/canonical_security/legacy_provenance.py").read_text()
        body = source.split('"""', 2)[2]
        for forbidden in ("business_data_providers", "sqlalchemy", "requests", "httpx"):
            assert forbidden not in body
