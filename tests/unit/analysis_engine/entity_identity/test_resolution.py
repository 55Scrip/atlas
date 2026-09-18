"""Identity claims, held to the four benchmark corpora.

The controls outnumber the proofs, which is the point: one identity
established from a source is worth more than fifty inferred from
spelling, and every string relation below is a reason to look rather
than a reason to accept.
"""
import pytest

from atlas.analysis_engine.entity_identity.contracts import (
    CandidateSignal,
    IdentityBasis,
    IdentityStatus,
    ReferenceKind,
)
from atlas.analysis_engine.entity_identity.resolution import (
    EntityReference,
    build_identity_claims,
    candidate_signals,
    resolve_identity,
)

# Volvo's own declarations, read from the label linkbase inside the
# cached ESEF package. Two elements one transposed letter apart, each
# with its own label -- the filer's typo, preserved.
VOLVO_LABELS = {
    "abvolvo:FinancialServicesMember": "Financial Services (member)",
    "abvolvo:FinancialServciesMember": "Financial Servcies (member)",
    "abvolvo:IndustrialOperationsMember": "Industriverksamheten (member)",
}


def member(value, issuer="VOLV-B", period=None):
    return EntityReference(kind=ReferenceKind.DIMENSIONAL_MEMBER, value=value, issuer=issuer,
                           source_locator="abvolvo-2022-12-31", period=period)


def label(value, issuer="VOLV-B"):
    return EntityReference(kind=ReferenceKind.TAXONOMY_LABEL, value=value, issuer=issuer)


def mention(value, issuer="VST"):
    return EntityReference(kind=ReferenceKind.STRATEGY_MENTION, value=value, issuer=issuer)


# ------------------------------------------------ identity is provable
def test_a_filers_own_label_establishes_identity():
    claim = resolve_identity(member("abvolvo:FinancialServicesMember"),
                             label("Financial Services (member)"), declared_labels=VOLVO_LABELS)
    assert claim.status is IdentityStatus.SAME
    assert claim.basis is IdentityBasis.TAXONOMY_LABEL
    assert "the filer declares" in claim.supporting[0].detail
    assert "denote one object" in claim.may_conclude


def test_one_transposed_letter_gets_the_opposite_verdict():
    # The whole design in one case: two strings a fuzzy matcher cannot
    # tell apart, resolved oppositely because the filer declared both.
    same = resolve_identity(member("abvolvo:FinancialServciesMember"),
                            label("Financial Servcies (member)"), declared_labels=VOLVO_LABELS)
    not_same = resolve_identity(member("abvolvo:FinancialServicesMember"),
                                label("Financial Servcies (member)"), declared_labels=VOLVO_LABELS)
    assert same.status is IdentityStatus.SAME
    assert not_same.status is IdentityStatus.NOT_SAME


def test_two_separately_declared_elements_are_two_things():
    claim = resolve_identity(member("abvolvo:FinancialServicesMember"),
                            member("abvolvo:FinancialServciesMember"), declared_labels=VOLVO_LABELS)
    assert claim.status is IdentityStatus.NOT_SAME
    assert "separately declared" in claim.reason


def test_a_label_the_filer_never_declared_proves_nothing():
    claim = resolve_identity(member("abvolvo:SomeUndeclaredMember"),
                             label("Something"), declared_labels=VOLVO_LABELS)
    assert claim.status is IdentityStatus.UNRESOLVED
    assert "no declared label" in claim.reason


def test_one_label_on_two_elements_is_ambiguous_not_a_choice():
    labels = dict(VOLVO_LABELS, **{"abvolvo:OtherMember": "Financial Services (member)"})
    claim = resolve_identity(member("abvolvo:FinancialServicesMember"),
                             label("Financial Services (member)"), declared_labels=labels)
    assert claim.status is IdentityStatus.AMBIGUOUS
    assert len(claim.alternatives) == 2


def test_an_identity_claim_carries_its_temporal_scope():
    claim = resolve_identity(member("abvolvo:FinancialServicesMember", period="2022"),
                             label("Financial Services (member)"), declared_labels=VOLVO_LABELS)
    assert claim.temporal_scope == "2022"


# -------------------------------------- the four required VST controls
@pytest.mark.parametrize("left,right", [
    ("Comanche Peak", "vistra:ComanchePeakNuclearPowerPlantMember"),
    ("PJM", "vistra:PJMMidAtlanticMember"),
    ("West Texas", "vistra:TexasSegmentMember"),
    ("Permian", "vistra:TexasSegmentMember"),
    ("Texas Energy Fund", "vistra:TexasSegmentMember"),
])
def test_no_vst_benchmark_pair_resolves_without_a_declared_label(left, right):
    claim = resolve_identity(mention(left), member(right, issuer="VST"))
    assert claim.status is IdentityStatus.UNRESOLVED
    assert claim.basis is None
    assert "no source evidence" in claim.reason


def test_west_texas_is_unresolved_and_not_mistaken_for_proven_difference():
    # Absence of proof is not proof of difference -- the distinction
    # that keeps a later sprint from reading UNRESOLVED as NOT_SAME.
    claim = resolve_identity(mention("West Texas"), member("vistra:TexasSegmentMember", issuer="VST"))
    assert claim.status is IdentityStatus.UNRESOLVED
    assert claim.status is not IdentityStatus.NOT_SAME
    assert "they are different" in claim.may_not_conclude


def test_a_real_acronym_relation_is_a_signal_and_never_a_basis():
    # An initialism that genuinely expands to the other name. The signal
    # fires; the status does not move.
    left = EntityReference(kind=ReferenceKind.STRATEGY_MENTION, value="TEF", issuer="X")
    right = EntityReference(kind=ReferenceKind.DIMENSIONAL_MEMBER,
                            value="x:TexasEnergyFundMember", issuer="X")
    assert CandidateSignal.ACRONYM in candidate_signals(left, right)
    claim = resolve_identity(left, right)
    assert claim.status is IdentityStatus.UNRESOLVED
    assert claim.basis is None


def test_pjm_acronym_is_a_signal_and_never_a_basis():
    left, right = mention("PJM"), member("vistra:PJMMidAtlanticMember", issuer="VST")
    signals = candidate_signals(left, right)
    assert signals            # it is worth looking at
    assert resolve_identity(left, right).status is IdentityStatus.UNRESOLVED
    assert resolve_identity(left, right).basis is None


# ------------------------------------- string relations are never proof
@pytest.mark.parametrize("left,right,expected_signal", [
    ("Phoenix", "Phoenix", CandidateSignal.EXACT_STRING),
    ("phoenix", "Phoenix", CandidateSignal.CASE_FOLDED),
    ("A.B.C.", "ABC", CandidateSignal.PUNCTUATION_NORMALIZED),
    ("Google Cloud", "goog:GoogleCloudMember", CandidateSignal.CAMEL_CASE_EXPANDED),
    ("Cloud", "goog:GoogleCloudMember", CandidateSignal.TOKEN_CONTAINMENT),
])
def test_every_string_relation_is_only_a_signal(left, right, expected_signal):
    a = EntityReference(kind=ReferenceKind.STRATEGY_MENTION, value=left, issuer="X")
    b = EntityReference(kind=ReferenceKind.DIMENSIONAL_MEMBER, value=right, issuer="X")
    assert expected_signal in candidate_signals(a, b)
    assert resolve_identity(a, b).status is IdentityStatus.UNRESOLVED


def test_an_exact_string_is_not_identity():
    # Two references may spell the same and mean a city, a project or a
    # product.
    a = EntityReference(kind=ReferenceKind.STRATEGY_MENTION, value="Phoenix", issuer="X")
    b = EntityReference(kind=ReferenceKind.DIMENSIONAL_MEMBER, value="Phoenix", issuer="X")
    claim = resolve_identity(a, b)
    assert CandidateSignal.EXACT_STRING in claim.signals
    assert claim.status is IdentityStatus.UNRESOLVED


def test_no_candidate_signal_is_ever_an_identity_basis():
    assert not (set(s.value for s in CandidateSignal) & set(b.value for b in IdentityBasis))


# ------------------------------------------------ scope and separation
def test_identity_is_issuer_scoped():
    a = EntityReference(kind=ReferenceKind.STRATEGY_MENTION, value="US", issuer="MA")
    b = EntityReference(kind=ReferenceKind.DIMENSIONAL_MEMBER, value="US", issuer="GOOGL")
    claim = resolve_identity(a, b)
    assert claim.status is IdentityStatus.UNRESOLVED
    assert "different issuers" in claim.reason


def test_claims_are_symmetric():
    left = member("abvolvo:FinancialServicesMember")
    right = label("Financial Services (member)")
    assert resolve_identity(left, right, declared_labels=VOLVO_LABELS).status is \
           resolve_identity(right, left, declared_labels=VOLVO_LABELS).status


# --------------------------------------------------- GOOGL precision
@pytest.mark.parametrize("left,right", [
    ("AI", "goog:TechnicalInfrastructureMember"),
    ("Google Cloud", "goog:GoogleServicesMember"),
    ("technical infrastructure", "goog:GoogleCloudMember"),
    ("Google Cloud", "goog:GoogleMember"),
])
def test_googl_references_never_collapse_into_one_identity(left, right):
    a = EntityReference(kind=ReferenceKind.STRATEGY_MENTION, value=left, issuer="GOOGL")
    b = EntityReference(kind=ReferenceKind.DIMENSIONAL_MEMBER, value=right, issuer="GOOGL")
    assert resolve_identity(a, b).status is not IdentityStatus.SAME


# ------------------------------------------------------- batch + invariants
def _refs():
    left = [mention("Comanche Peak"), mention("PJM"), mention("West Texas")]
    right = [member("vistra:ComanchePeakNuclearPowerPlantMember", issuer="VST"),
             member("vistra:PJMMidAtlanticMember", issuer="VST"),
             member("vistra:TexasSegmentMember", issuer="VST")]
    return left, right


def _fingerprint(claims):
    return sorted((c.left.value, c.right.value, c.status.value,
                   tuple(s.value for s in c.signals)) for c in claims)


def test_the_batch_inspects_only_pairs_with_a_reason():
    left, right = _refs()
    claims = build_identity_claims(left, right)
    assert claims and len(claims) < len(left) * len(right)
    assert all(c.status is IdentityStatus.UNRESOLVED for c in claims)


def test_resolution_is_deterministic():
    left, right = _refs()
    assert _fingerprint(build_identity_claims(left, right)) == \
           _fingerprint(build_identity_claims(left, right))


def test_duplicate_references_do_not_duplicate_claims():
    left, right = _refs()
    once = _fingerprint(build_identity_claims(left, right))
    twice = _fingerprint(build_identity_claims(left + left, right + right))
    assert once == twice


def test_resolution_is_order_independent():
    left, right = _refs()
    assert _fingerprint(build_identity_claims(left, right)) == \
           _fingerprint(build_identity_claims(list(reversed(left)), list(reversed(right))))


def test_resolution_reads_no_clock():
    import pathlib

    for name in ("contracts.py", "resolution.py"):
        source = pathlib.Path(f"atlas/analysis_engine/entity_identity/{name}").read_text(encoding="utf-8")
        assert "datetime" not in source and "now(" not in source


def test_no_world_knowledge_alias_or_ticker_appears_in_the_code():
    import pathlib

    for name in ("contracts.py", "resolution.py"):
        source = pathlib.Path(f"atlas/analysis_engine/entity_identity/{name}").read_text(encoding="utf-8")
        parts = source.split('"""')
        code = parts[0] + "".join(parts[2::2])
        code = "\n".join(l for l in code.splitlines() if not l.lstrip().startswith("#"))
        for token in ("VST", "GOOGL", "AMAT", "Vistra", "Comanche", "vistra:", "goog:",
                      "Nuclear", "Texas", "PJM"):
            assert token not in code, f"{token} appears in executable code of {name}"


def test_the_module_reaches_for_nothing():
    import ast
    import pathlib

    for name in ("contracts.py", "resolution.py"):
        source = pathlib.Path(f"atlas/analysis_engine/entity_identity/{name}").read_text(encoding="utf-8")
        modules = {n.module for n in ast.walk(ast.parse(source)) if isinstance(n, ast.ImportFrom)}
        outside = [m for m in modules if m and m.startswith("atlas")
                   and not m.startswith("atlas.analysis_engine.entity_identity")]
        assert not outside, outside
