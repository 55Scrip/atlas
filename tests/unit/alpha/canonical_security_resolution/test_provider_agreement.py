"""Provider Agreement Engine tests -- Sprint N Phase 8, using the live
MC/EVO collision shapes as the primary fixtures."""
from __future__ import annotations

from atlas.alpha.canonical_security_resolution.candidates import ProviderCandidate
from atlas.alpha.canonical_security_resolution.provider_agreement import evaluate_provider_agreement


def test_mc_collision_produces_conflict() -> None:
    """SEC -> Moelis, Twelve Data -> LVMH -> conflict."""
    sec = ProviderCandidate(provider_name="SEC_EDGAR", symbol="MC", company_name="Moelis & Company")
    twelve_data = ProviderCandidate(provider_name="TWELVE_DATA", symbol="MC", company_name="LVMH Moët Hennessy Louis Vuitton SE")
    result = evaluate_provider_agreement((sec, twelve_data))
    assert result.has_conflict is True
    assert len(result.groups) == 2


def test_evo_collision_produces_conflict() -> None:
    """SEC -> Evotec, OpenFIGI -> Evolution -> conflict."""
    sec = ProviderCandidate(provider_name="SEC_EDGAR", symbol="EVO", company_name="Evotec SE")
    openfigi = ProviderCandidate(provider_name="OPENFIGI", symbol="EVO", company_name="Evolution AB")
    result = evaluate_provider_agreement((sec, openfigi))
    assert result.has_conflict is True


def test_multiple_providers_agreeing_is_not_a_conflict() -> None:
    a = ProviderCandidate(provider_name="SEC_EDGAR", symbol="AAPL", company_name="Apple Inc.")
    b = ProviderCandidate(provider_name="TWELVE_DATA", symbol="AAPL", company_name="Apple Inc.")
    result = evaluate_provider_agreement((a, b))
    assert result.has_conflict is False
    assert result.dominant_group == (a, b)


def test_no_company_name_candidates_never_conflict_with_each_other() -> None:
    """Absence of data is never treated as disagreement."""
    a = ProviderCandidate(provider_name="SEC_EDGAR", symbol="XYZ")
    b = ProviderCandidate(provider_name="ALPHA_VANTAGE", symbol="XYZ")
    result = evaluate_provider_agreement((a, b))
    assert result.has_conflict is False
    assert result.dominant_group is None


def test_dominant_group_is_none_when_tied() -> None:
    a = ProviderCandidate(provider_name="SEC_EDGAR", symbol="MC", company_name="Moelis & Company")
    b = ProviderCandidate(provider_name="TWELVE_DATA", symbol="MC", company_name="LVMH")
    result = evaluate_provider_agreement((a, b))
    assert result.dominant_group is None  # 1-vs-1, no unique majority


def test_dominant_group_identified_with_real_majority() -> None:
    a = ProviderCandidate(provider_name="SEC_EDGAR", symbol="MC", company_name="LVMH")
    b = ProviderCandidate(provider_name="TWELVE_DATA", symbol="MC", company_name="LVMH")
    c = ProviderCandidate(provider_name="OPENFIGI", symbol="MC", company_name="Moelis & Company")
    result = evaluate_provider_agreement((a, b, c))
    assert result.has_conflict is True
    assert result.dominant_group == (a, b)
