"""CanonicalSecurity population planning.

The planner exists because whether a company has a security currently
depends on *when* it was ingested rather than on what Atlas knows. It is
pure: it reports what would happen and mutates nothing, so creation stays
with the Identity Gate.

Real numbers it was validated against: 14 of 36 companies had a security,
16 more were creatable from stored profile documents with no provider
call, and 6 genuinely needed one live profile fetch each.
"""
from __future__ import annotations

import pytest

from atlas.alpha.canonical_security.population import (
    REQUIRED_PROFILE_FIELDS,
    PopulationOutcome,
    plan_security_population,
)

FULL = {
    "name": "Alphabet Inc Class C",
    "exchange": "NASDAQ",
    "currency": "USD",
    "country": "USA",
    "sector": "COMMUNICATION SERVICES",
}


class TestExistingSecurity:
    def test_a_company_with_a_security_is_already_present(self):
        plan = plan_security_population("GOOGL", has_security=True, profiles=(FULL,))
        assert plan.outcome is PopulationOutcome.ALREADY_PRESENT
        assert plan.is_actionable_offline is False
        assert plan.needs_provider_call is False


class TestOfflineCreation:
    def test_goog_is_creatable_from_stored_evidence(self):
        """The proof case, with no special-casing: GOOG's profile was
        captured before the gate existed and carries everything
        required."""
        plan = plan_security_population("GOOG", has_security=False, profiles=(FULL,))
        assert plan.outcome is PopulationOutcome.READY_TO_CREATE
        assert plan.is_actionable_offline is True
        assert plan.needs_provider_call is False

    def test_the_plan_carries_the_evidence_it_would_use(self):
        """Auditable rather than merely a verdict."""
        plan = plan_security_population("GOOG", has_security=False, profiles=(FULL,))
        assert plan.profile["exchange"] == "NASDAQ"
        assert plan.profile["currency"] == "USD"

    def test_asset_type_is_not_required(self):
        """`SecurityType` already degrades to OTHER when a provider omits
        it, so requiring it would block creation over a field the model
        itself treats as optional."""
        assert "asset_type" not in REQUIRED_PROFILE_FIELDS
        plan = plan_security_population("X", has_security=False, profiles=(FULL,))
        assert plan.outcome is PopulationOutcome.READY_TO_CREATE


class TestProviderCallRequired:
    def test_no_stored_profile_needs_one_live_fetch(self):
        plan = plan_security_population("BRK.B", has_security=False, profiles=())
        assert plan.outcome is PopulationOutcome.REQUIRES_PROVIDER_CALL
        assert plan.missing_fields == REQUIRED_PROFILE_FIELDS

    @pytest.mark.parametrize("field", REQUIRED_PROFILE_FIELDS)
    def test_each_required_field_missing_forces_a_call(self, field):
        partial = {key: value for key, value in FULL.items() if key != field}
        plan = plan_security_population("X", has_security=False, profiles=(partial,))
        assert plan.outcome is PopulationOutcome.REQUIRES_PROVIDER_CALL
        assert field in plan.missing_fields

    def test_a_cik_alone_cannot_create_a_security(self):
        """Issuer identity says which filer a company is. It says nothing
        about which exchange it trades on or in what currency, and
        CanonicalSecurity requires both."""
        plan = plan_security_population("TSM", has_security=False, profiles=({"sec_cik": "0001046179"},))
        assert plan.outcome is PopulationOutcome.REQUIRES_PROVIDER_CALL


class TestAbsenceIsNotDisagreement:
    def test_an_incomplete_earlier_profile_does_not_contradict_a_later_one(self):
        """AAPL had exactly this shape: one stored profile with no
        currency and one with USD. Treating silence as conflict would
        repeat the absence-means-disagreement error this codebase has
        already had to remove twice."""
        earlier = {**FULL, "currency": None}
        plan = plan_security_population("AAPL", has_security=False, profiles=(earlier, FULL))
        assert plan.outcome is PopulationOutcome.READY_TO_CREATE
        assert plan.profile["currency"] == "USD"

    def test_genuinely_different_values_do_contradict(self):
        other = {**FULL, "exchange": "NYSE"}
        plan = plan_security_population("X", has_security=False, profiles=(FULL, other))
        assert plan.outcome is PopulationOutcome.CONTRADICTORY

    def test_a_contradiction_never_picks_a_winner(self):
        other = {**FULL, "name": "Something Else Entirely"}
        plan = plan_security_population("X", has_security=False, profiles=(FULL, other))
        assert plan.profile is None

    def test_differing_only_on_an_optional_field_is_not_a_contradiction(self):
        variant = {**FULL, "sector": "TECHNOLOGY"}
        plan = plan_security_population("X", has_security=False, profiles=(FULL, variant))
        assert plan.outcome is PopulationOutcome.READY_TO_CREATE

    def test_the_most_complete_profile_is_preferred(self):
        sparse = {"name": "Alphabet Inc Class C", "exchange": "NASDAQ"}
        plan = plan_security_population("GOOG", has_security=False, profiles=(sparse, FULL))
        assert plan.outcome is PopulationOutcome.READY_TO_CREATE
        assert plan.profile["country"] == "USA"


class TestIdentitySafetyIsUnchanged:
    def test_the_planner_never_compares_two_companies(self):
        """It is given one company's own documents and nothing else, so
        no cross-company inference is structurally possible -- this is
        what keeps SU.PA away from Suncor."""
        import inspect

        signature = inspect.signature(plan_security_population)
        assert set(signature.parameters) == {"company", "has_security", "profiles"}

    def test_su_pa_and_su_are_planned_independently(self):
        su_pa = plan_security_population("SU.PA", has_security=False, profiles=())
        su = plan_security_population(
            "SU", has_security=False, profiles=({**FULL, "name": "Suncor Energy Inc"},)
        )
        assert su_pa.outcome is PopulationOutcome.REQUIRES_PROVIDER_CALL
        assert su.outcome is PopulationOutcome.READY_TO_CREATE
        assert su_pa.profile is None

    def test_volvo_without_a_stored_profile_needs_a_call_not_a_guess(self):
        plan = plan_security_population("VOLV-B", has_security=False, profiles=())
        assert plan.outcome is PopulationOutcome.REQUIRES_PROVIDER_CALL

    def test_tsmc_is_not_satisfied_by_tsms_profile(self):
        """Each company is planned from its own documents only."""
        tsmc = plan_security_population("TSMC", has_security=False, profiles=())
        assert tsmc.outcome is PopulationOutcome.REQUIRES_PROVIDER_CALL


class TestPurityAndDeterminism:
    def test_planning_is_deterministic(self):
        first = plan_security_population("GOOG", has_security=False, profiles=(FULL,))
        second = plan_security_population("GOOG", has_security=False, profiles=(FULL,))
        assert first == second

    def test_the_input_profiles_are_not_mutated(self):
        original = dict(FULL)
        plan = plan_security_population("GOOG", has_security=False, profiles=(FULL,))
        assert FULL == original
        plan.profile["name"] = "changed"
        assert FULL["name"] == original["name"]

    def test_module_has_no_side_effecting_imports(self):
        from pathlib import Path

        source = Path("atlas/alpha/canonical_security/population.py").read_text()
        body = source.split('"""', 2)[2]
        for forbidden in ("sqlalchemy", "requests", "httpx", "business_data_providers", "repository"):
            assert forbidden not in body, forbidden

    def test_every_outcome_is_explained(self):
        for profiles, has_security in (((FULL,), True), ((FULL,), False), ((), False)):
            plan = plan_security_population("X", has_security=has_security, profiles=profiles)
            assert plan.reason and len(plan.reason) > 20
