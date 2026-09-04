"""Security-level provenance repair -- the rules that decide whether a
historical record may receive a CanonicalSecurity.

The case every test here exists for: Alphabet files under one CIK
(0001652044) for two listed share classes, and every already-linked
Alphabet record points at the GOOGL security only because the GOOG
security was created later and nothing has been linked to it. An index
built from those records converges on GOOGL with total confidence and
is wrong. These tests pin the veto that catches it, and pin that the
planner cannot see a ticker even if someone later wants it to.
"""
from __future__ import annotations

import pytest

from atlas.alpha.canonical_security.security_provenance import (
    CikSecurityEvidence,
    SecurityProvenanceOutcome,
    SecurityRecordRepair,
    plan_security_provenance_repair,
)

_NVDA_CIK = "0001045810"
_ALPHABET_CIK = "0001652044"


def _plan(records, *, cik_evidence, securities_by_issuer, security_issuer):
    return plan_security_provenance_repair(
        records,
        cik_evidence=cik_evidence,
        securities_by_issuer=securities_by_issuer,
        security_issuer=security_issuer,
    )


def _single_issuer_world():
    """One issuer, one security, one listing -- the repairable shape."""
    return dict(
        cik_evidence={_NVDA_CIK: CikSecurityEvidence(frozenset({"sec-nvda"}), 1)},
        securities_by_issuer={"iss-nvda": frozenset({"sec-nvda"})},
        security_issuer={"sec-nvda": "iss-nvda"},
    )


def _alphabet_world():
    """Two share classes, one CIK, and only GOOGL linked so far."""
    return dict(
        cik_evidence={_ALPHABET_CIK: CikSecurityEvidence(frozenset({"sec-googl"}), 2)},
        securities_by_issuer={"iss-alphabet-a": frozenset({"sec-googl"})},
        security_issuer={"sec-googl": "iss-alphabet-a"},
    )


class TestUniquelyProvableEvidenceRepairs:
    def test_single_listing_cik_with_one_linked_security_is_provable(self):
        (plan,) = _plan(
            (("r1", None, "iss-nvda", {"sec_cik": _NVDA_CIK}),), **_single_issuer_world()
        )
        assert plan.outcome is SecurityProvenanceOutcome.PROVABLE_SECURITY
        assert plan.security_id == "sec-nvda"

    def test_an_unpadded_cik_is_normalized_before_lookup(self):
        """Stored CIKs vary in padding; the planner must not miss
        evidence over a formatting difference."""
        (plan,) = _plan(
            (("r1", None, "iss-nvda", {"sec_cik": "1045810"}),), **_single_issuer_world()
        )
        assert plan.outcome is SecurityProvenanceOutcome.PROVABLE_SECURITY


class TestAmbiguousEvidenceNeverRepairs:
    def test_a_cik_spanning_two_listings_is_refused_even_though_the_index_converges(self):
        """The GOOG case exactly. The index holds exactly one security
        and would otherwise look conclusive -- the share-class veto is
        the only thing standing between that and a wrong-class link."""
        (plan,) = _plan(
            (("goog-1", None, "iss-alphabet-a", {"sec_cik": _ALPHABET_CIK}),), **_alphabet_world()
        )
        assert plan.outcome is SecurityProvenanceOutcome.MULTIPLE_POSSIBLE_SECURITIES
        assert plan.security_id is None

    def test_the_veto_applies_to_the_class_the_index_actually_names(self):
        """GOOGL is refused too. Repairing only the listing the index
        happens to name would bake the asymmetry in permanently."""
        (plan,) = _plan(
            (("googl-1", None, "iss-alphabet-a", {"sec_cik": _ALPHABET_CIK}),), **_alphabet_world()
        )
        assert plan.outcome is SecurityProvenanceOutcome.MULTIPLE_POSSIBLE_SECURITIES

    def test_a_cik_resolving_to_two_securities_is_refused(self):
        (plan,) = _plan(
            (("r1", None, "iss-x", {"sec_cik": _NVDA_CIK}),),
            cik_evidence={_NVDA_CIK: CikSecurityEvidence(frozenset({"sec-a", "sec-b"}), 1)},
            securities_by_issuer={"iss-x": frozenset({"sec-a", "sec-b"})},
            security_issuer={"sec-a": "iss-x", "sec-b": "iss-x"},
        )
        assert plan.outcome is SecurityProvenanceOutcome.MULTIPLE_POSSIBLE_SECURITIES

    def test_a_security_belonging_to_a_different_issuer_is_never_attached(self):
        """Contradiction between two proven signals is UNKNOWN, not a
        silent pick of either one."""
        (plan,) = _plan(
            (("r1", None, "iss-nvda", {"sec_cik": _NVDA_CIK}),),
            cik_evidence={_NVDA_CIK: CikSecurityEvidence(frozenset({"sec-other"}), 1)},
            securities_by_issuer={"iss-nvda": frozenset({"sec-nvda"})},
            security_issuer={"sec-other": "iss-elsewhere", "sec-nvda": "iss-nvda"},
        )
        assert plan.outcome is SecurityProvenanceOutcome.UNKNOWN
        assert plan.security_id is None

    def test_an_issuer_owning_two_securities_is_never_repaired(self):
        (plan,) = _plan(
            (("r1", None, "iss-x", {"sec_cik": _NVDA_CIK}),),
            cik_evidence={_NVDA_CIK: CikSecurityEvidence(frozenset({"sec-a"}), 1)},
            securities_by_issuer={"iss-x": frozenset({"sec-a", "sec-b"})},
            security_issuer={"sec-a": "iss-x", "sec-b": "iss-x"},
        )
        assert plan.outcome is SecurityProvenanceOutcome.UNKNOWN


class TestAbsentEvidenceIsNotDisagreement:
    def test_no_cik_is_insufficient_evidence_not_a_refusal_to_exist(self):
        (plan,) = _plan((("r1", None, "iss-nvda", {}),), **_single_issuer_world())
        assert plan.outcome is SecurityProvenanceOutcome.INSUFFICIENT_EVIDENCE

    def test_a_malformed_cik_is_treated_as_absent(self):
        (plan,) = _plan(
            (("r1", None, "iss-nvda", {"sec_cik": "not-a-cik"}),), **_single_issuer_world()
        )
        assert plan.outcome is SecurityProvenanceOutcome.INSUFFICIENT_EVIDENCE

    def test_a_cik_no_linked_record_carries_is_insufficient(self):
        (plan,) = _plan(
            (("r1", None, "iss-nvda", {"sec_cik": "0000000123"}),), **_single_issuer_world()
        )
        assert plan.outcome is SecurityProvenanceOutcome.INSUFFICIENT_EVIDENCE

    def test_an_issuer_with_no_security_yet_is_its_own_outcome(self):
        (plan,) = _plan(
            (("r1", None, "iss-new", {"sec_cik": _NVDA_CIK}),),
            cik_evidence={_NVDA_CIK: CikSecurityEvidence(frozenset({"sec-nvda"}), 1)},
            securities_by_issuer={},
            security_issuer={"sec-nvda": "iss-nvda"},
        )
        assert plan.outcome is SecurityProvenanceOutcome.NO_SECURITY_EXISTS

    def test_a_record_with_no_proven_issuer_is_never_repaired(self):
        (plan,) = _plan((("r1", None, None, {"sec_cik": _NVDA_CIK}),), **_single_issuer_world())
        assert plan.outcome is SecurityProvenanceOutcome.INSUFFICIENT_EVIDENCE


class TestIdempotenceAndTotality:
    def test_an_already_linked_record_is_left_alone(self):
        (plan,) = _plan(
            (("r1", "sec-nvda", "iss-nvda", {"sec_cik": _NVDA_CIK}),), **_single_issuer_world()
        )
        assert plan.outcome is SecurityProvenanceOutcome.ALREADY_LINKED
        assert plan.security_id is None

    def test_replanning_after_a_repair_proposes_nothing_further(self):
        """Idempotence at the planning layer: feed the plan's own result
        back in and no second write is proposed."""
        world = _single_issuer_world()
        record = ("r1", None, "iss-nvda", {"sec_cik": _NVDA_CIK})
        (first,) = _plan((record,), **world)
        assert first.outcome is SecurityProvenanceOutcome.PROVABLE_SECURITY

        (second,) = _plan(((record[0], first.security_id, record[2], record[3]),), **world)
        assert second.outcome is SecurityProvenanceOutcome.ALREADY_LINKED

    def test_every_record_receives_exactly_one_classification(self):
        records = (
            ("a", None, "iss-nvda", {"sec_cik": _NVDA_CIK}),
            ("b", "sec-nvda", "iss-nvda", {}),
            ("c", None, None, {}),
            ("d", None, "iss-nvda", {}),
        )
        plans = _plan(records, **_single_issuer_world())
        assert len(plans) == len(records)
        assert [p.record_id for p in plans] == ["a", "b", "c", "d"]
        assert all(isinstance(p, SecurityRecordRepair) for p in plans)


class TestThePlannerCannotSeeATicker:
    def test_no_ticker_or_company_name_reaches_the_planner(self):
        """`legacy_provenance` deliberately does not accept a ticker so
        a future edit cannot quietly start matching on one. The same
        constraint holds here -- the only ticker-derived input is an
        integer count that can veto but never select."""
        import inspect

        from atlas.alpha.canonical_security import security_provenance

        source = inspect.getsource(security_provenance)
        for forbidden in ("native_ticker", "company_name", "legal_name", ".upper()", ".lower()"):
            assert forbidden not in source, forbidden

    def test_evidence_carries_a_count_never_the_company_strings(self):
        evidence = CikSecurityEvidence(frozenset({"sec-a"}), 2)
        assert isinstance(evidence.distinct_company_count, int)
        assert not hasattr(evidence, "companies")
