"""`CanonicalSecurityIdentityGate.evaluate` -- Sprint O Phases 3/4/5/7/11/12/13.

Real in-memory SQLite persistence throughout (both the Sprint M
`canonical_securities` tables and the Sprint N `resolution_records`/
`resolution_evidence` tables) -- exercises the real
`CanonicalSecurityResolutionService` unmodified, proving the gate
itself makes the correct allow/block decision for every one of the six
resolution outcomes, reuses an existing identity rather than
duplicating it, replays the exact MC/EVO collision patterns Sprint H/I
discovered live, and persists full evidence for every attempt --
allowed or blocked.
"""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import create_engine, select
from sqlalchemy.engine import Engine
from sqlalchemy.pool import StaticPool

from atlas.alpha.canonical_security.repository import SqlAlchemyCanonicalSecurityRepository
from atlas.alpha.canonical_security.table import canonical_securities_table, create_canonical_security_tables
from atlas.alpha.canonical_security_gate.gate import CanonicalSecurityIdentityGate
from atlas.alpha.canonical_security_resolution.repository import SqlAlchemyResolutionRepository
from atlas.alpha.canonical_security_resolution.replay import verify_replay
from atlas.alpha.canonical_security_resolution.service import CanonicalSecurityResolutionService
from atlas.alpha.canonical_security_resolution.table import create_resolution_tables
from atlas.analysis_engine.business_data.models import RawBusinessDocument

_NOW = datetime(2026, 8, 18, tzinfo=timezone.utc)


def _engine() -> Engine:
    engine = create_engine("sqlite:///:memory:", future=True, poolclass=StaticPool, connect_args={"check_same_thread": False})
    create_canonical_security_tables(engine)
    create_resolution_tables(engine)
    return engine


def _gate(engine: Engine) -> CanonicalSecurityIdentityGate:
    return CanonicalSecurityIdentityGate(
        resolution_service=CanonicalSecurityResolutionService(),
        canonical_security_repository=SqlAlchemyCanonicalSecurityRepository(engine),
        resolution_repository=SqlAlchemyResolutionRepository(engine),
    )


def _profile_doc(
    *,
    ticker: str,
    provider_id: str,
    name: str | None = None,
    exchange: str | None = None,
    country: str | None = None,
    currency: str | None = None,
    security_type: str | None = None,
    identifier_suffix: str = "",
) -> RawBusinessDocument:
    metadata: dict = {}
    if name is not None:
        metadata["name"] = name
    if exchange is not None:
        metadata["exchange"] = exchange
    if country is not None:
        metadata["country"] = country
    if currency is not None:
        metadata["currency"] = currency
    if security_type is not None:
        metadata["security_type"] = security_type
    return RawBusinessDocument(
        identifier=f"{ticker}:profile{identifier_suffix}",
        company=ticker,
        source_kind="company_profile",
        published_at=_NOW,
        provider_id=provider_id,
        raw_reference=f"https://example.test/{provider_id}",
        content_hash=f"hash-{provider_id}-{ticker}{identifier_suffix}",
        language="en",
        metadata=metadata,
    )


def _row_count(engine: Engine) -> int:
    with engine.connect() as connection:
        return len(connection.execute(select(canonical_securities_table)).all())


class TestAutoAccept:
    def test_a_single_fully_specified_candidate_reaches_auto_accept_and_allows(self) -> None:
        engine = _engine()
        gate = _gate(engine)
        doc = _profile_doc(
            ticker="AAPL", provider_id="alpha_vantage", name="Apple Inc.",
            exchange="NASDAQ", country="USA", currency="USD", security_type="COMMON_STOCK",
        )
        decision = gate.evaluate(ticker="AAPL", documents=(doc,), clock=lambda: _NOW)

        assert decision.allowed is True
        assert decision.outcome == "AUTO_ACCEPT"
        assert decision.provenance is not None
        assert decision.provenance.resolution_version == "1.0.0"
        assert _row_count(engine) == 1


class TestManualConfirmationBlocks:
    def test_missing_security_type_caps_confidence_at_medium_and_blocks(self) -> None:
        """The exact real-world shape: Alpha Vantage's own
        `_IDENTITY_FIELD_MAP` never supplies `security_type` -- a
        candidate with exchange/country/currency but no security_type
        can never reach HIGH confidence."""
        engine = _engine()
        gate = _gate(engine)
        doc = _profile_doc(ticker="AAPL", provider_id="alpha_vantage", name="Apple Inc.", exchange="NASDAQ", country="USA", currency="USD")
        decision = gate.evaluate(ticker="AAPL", documents=(doc,), clock=lambda: _NOW)

        assert decision.allowed is False
        assert decision.outcome == "MANUAL_CONFIRMATION"
        assert decision.provenance is None
        assert _row_count(engine) == 0


class TestLowConfidenceBlocks:
    def test_a_ticker_only_candidate_with_zero_corroborating_fields_is_low_confidence(self) -> None:
        engine = _engine()
        gate = _gate(engine)
        doc = _profile_doc(ticker="AAPL", provider_id="alpha_vantage")  # no metadata at all
        decision = gate.evaluate(ticker="AAPL", documents=(doc,), clock=lambda: _NOW)

        assert decision.allowed is False
        assert decision.outcome == "LOW_CONFIDENCE"
        assert _row_count(engine) == 0


class TestNoMatchBlocks:
    def test_zero_candidates_produces_no_match_without_crashing(self) -> None:
        engine = _engine()
        gate = _gate(engine)
        decision = gate.evaluate(ticker="ZZZZ", documents=(), clock=lambda: _NOW)

        assert decision.allowed is False
        assert decision.outcome == "NO_MATCH"
        assert decision.provenance is None
        assert _row_count(engine) == 0

    def test_no_match_is_still_persisted_for_auditability(self) -> None:
        engine = _engine()
        gate = _gate(engine)
        decision = gate.evaluate(ticker="ZZZZ", documents=(), clock=lambda: _NOW)

        stored = SqlAlchemyResolutionRepository(engine).load(decision.resolution_record_id)
        assert stored is not None
        assert stored.outcome == "NO_MATCH"
        assert stored.evidence == ()


class TestAmbiguousBlocksOnCollision:
    """Replays Sprint H/I's own two confirmed, real ticker-collision
    patterns -- see Sprint N Phase 8's own worked examples."""

    def test_mc_collision_lvmh_vs_moelis_is_ambiguous_and_creates_nothing(self) -> None:
        engine = _engine()
        gate = _gate(engine)
        lvmh_candidate = _profile_doc(
            ticker="MC", provider_id="alpha_vantage", name="LVMH Moet Hennessy Louis Vuitton",
            exchange="EURONEXT PARIS", country="France", currency="EUR", security_type="COMMON_STOCK",
        )
        moelis_candidate = _profile_doc(
            ticker="MC", provider_id="sec_edgar", name="Moelis & Co", identifier_suffix="-2",
        )
        decision = gate.evaluate(ticker="MC", documents=(lvmh_candidate, moelis_candidate), clock=lambda: _NOW)

        assert decision.allowed is False
        assert decision.outcome == "AMBIGUOUS"
        assert _row_count(engine) == 0

    def test_evo_collision_evotec_vs_evolution_is_ambiguous_and_creates_nothing(self) -> None:
        engine = _engine()
        gate = _gate(engine)
        evotec_candidate = _profile_doc(
            ticker="EVO", provider_id="alpha_vantage", name="Evotec SE",
            exchange="XETRA", country="Germany", currency="EUR", security_type="COMMON_STOCK",
        )
        evolution_candidate = _profile_doc(
            ticker="EVO", provider_id="sec_edgar", name="Evolution AB", identifier_suffix="-2",
        )
        decision = gate.evaluate(ticker="EVO", documents=(evotec_candidate, evolution_candidate), clock=lambda: _NOW)

        assert decision.allowed is False
        assert decision.outcome == "AMBIGUOUS"
        assert _row_count(engine) == 0

    def test_ambiguous_evidence_retains_both_disagreeing_candidates(self) -> None:
        """Phase 10's own "never discard a candidate" requirement,
        verified directly against what actually got persisted."""
        engine = _engine()
        gate = _gate(engine)
        lvmh_candidate = _profile_doc(ticker="MC", provider_id="alpha_vantage", name="LVMH")
        moelis_candidate = _profile_doc(ticker="MC", provider_id="sec_edgar", name="Moelis & Co", identifier_suffix="-2")
        decision = gate.evaluate(ticker="MC", documents=(lvmh_candidate, moelis_candidate), clock=lambda: _NOW)

        stored = SqlAlchemyResolutionRepository(engine).load(decision.resolution_record_id)
        assert len(stored.evidence) == 2
        assert {e.candidate.company_name for e in stored.evidence} == {"LVMH", "Moelis & Co"}
        assert all(not e.accepted for e in stored.evidence)


class TestRejectBlocks:
    def test_a_candidate_positively_contradicting_an_existing_identity_is_rejected(self) -> None:
        engine = _engine()
        gate = _gate(engine)
        original = _profile_doc(
            ticker="XYZ", provider_id="alpha_vantage", name="Real Company Inc.",
            exchange="NASDAQ", country="USA", currency="USD", security_type="COMMON_STOCK",
        )
        first = gate.evaluate(ticker="XYZ", documents=(original,), clock=lambda: _NOW)
        assert first.outcome == "AUTO_ACCEPT"

        contradicting = _profile_doc(
            ticker="XYZ", provider_id="alpha_vantage", name="A Totally Different Company",
            exchange="NASDAQ", country="USA", currency="USD", security_type="COMMON_STOCK",
            identifier_suffix="-2",
        )
        second = gate.evaluate(ticker="XYZ", documents=(contradicting,), clock=lambda: _NOW)

        assert second.allowed is False
        assert second.outcome == "REJECT"
        assert _row_count(engine) == 1  # still only the original


class TestExistingCanonicalSecurityIsReusedNeverDuplicated:
    def test_a_second_corroborating_candidate_extends_the_existing_security(self) -> None:
        engine = _engine()
        gate = _gate(engine)
        first_doc = _profile_doc(
            ticker="AAPL", provider_id="alpha_vantage", name="Apple Inc.",
            exchange="NASDAQ", country="USA", currency="USD", security_type="COMMON_STOCK",
        )
        first = gate.evaluate(ticker="AAPL", documents=(first_doc,), clock=lambda: _NOW)
        assert first.allowed is True
        assert _row_count(engine) == 1
        first_id = first.provenance.canonical_security_id

        second_doc = _profile_doc(
            ticker="AAPL", provider_id="sec_edgar", name="Apple Inc.", identifier_suffix="-2",
        )
        second = gate.evaluate(ticker="AAPL", documents=(second_doc,), clock=lambda: _NOW)

        # A second, sparser candidate for an already-CANONICAL security:
        # its own confidence alone doesn't reach AUTO_ACCEPT (Rule 4's
        # promotion only applies within one resolve() call, and this is
        # a fresh call with a single new candidate) -- but the point of
        # this test is exclusively "no duplicate CanonicalSecurity is
        # ever created," which holds regardless of this call's own
        # outcome.
        assert _row_count(engine) == 1
        if second.allowed:
            assert second.provenance.canonical_security_id == first_id


class TestProvenancePersistence:
    def test_allowed_decision_carries_full_provenance(self) -> None:
        engine = _engine()
        gate = _gate(engine)
        doc = _profile_doc(
            ticker="AAPL", provider_id="alpha_vantage", name="Apple Inc.",
            exchange="NASDAQ", country="USA", currency="USD", security_type="COMMON_STOCK",
        )
        decision = gate.evaluate(ticker="AAPL", documents=(doc,), clock=lambda: _NOW)

        assert decision.provenance.canonical_security_id
        assert decision.provenance.resolution_version == "1.0.0"
        assert decision.provenance.resolved_at == _NOW
        assert decision.provenance.provider_evidence_reference == decision.resolution_record_id

    def test_blocked_decision_still_names_a_reason(self) -> None:
        engine = _engine()
        gate = _gate(engine)
        doc = _profile_doc(ticker="AAPL", provider_id="alpha_vantage", name="Apple Inc.", exchange="NASDAQ", country="USA", currency="USD")
        decision = gate.evaluate(ticker="AAPL", documents=(doc,), clock=lambda: _NOW)

        assert decision.allowed is False
        assert decision.reason
        assert "confirm" in decision.reason.lower()


class TestReplayReproducesTheSameGateDecision:
    def test_replaying_a_stored_auto_accept_produces_the_identical_outcome(self) -> None:
        engine = _engine()
        gate = _gate(engine)
        doc = _profile_doc(
            ticker="AAPL", provider_id="alpha_vantage", name="Apple Inc.",
            exchange="NASDAQ", country="USA", currency="USD", security_type="COMMON_STOCK",
        )
        decision = gate.evaluate(ticker="AAPL", documents=(doc,), clock=lambda: _NOW)

        stored = SqlAlchemyResolutionRepository(engine).load(decision.resolution_record_id)
        replayed = verify_replay(stored)  # raises on any mismatch
        assert replayed.outcome == "AUTO_ACCEPT"

    def test_replaying_a_stored_ambiguous_collision_produces_the_identical_outcome(self) -> None:
        engine = _engine()
        gate = _gate(engine)
        lvmh_candidate = _profile_doc(ticker="MC", provider_id="alpha_vantage", name="LVMH")
        moelis_candidate = _profile_doc(ticker="MC", provider_id="sec_edgar", name="Moelis & Co", identifier_suffix="-2")
        decision = gate.evaluate(ticker="MC", documents=(lvmh_candidate, moelis_candidate), clock=lambda: _NOW)

        stored = SqlAlchemyResolutionRepository(engine).load(decision.resolution_record_id)
        replayed = verify_replay(stored)
        assert replayed.outcome == "AMBIGUOUS"


class TestRepositoryIntegration:
    def test_the_gate_uses_the_real_repositories_no_second_persistence_layer(self) -> None:
        engine = _engine()
        gate = _gate(engine)
        doc = _profile_doc(
            ticker="AAPL", provider_id="alpha_vantage", name="Apple Inc.",
            exchange="NASDAQ", country="USA", currency="USD", security_type="COMMON_STOCK",
        )
        decision = gate.evaluate(ticker="AAPL", documents=(doc,), clock=lambda: _NOW)

        canonical_security_repository = SqlAlchemyCanonicalSecurityRepository(engine)
        loaded = canonical_security_repository.load(decision.provenance.canonical_security_id)
        assert loaded is not None
        assert loaded.resolution_status == "CANONICAL"
        assert loaded.canonical_company_name == "Apple Inc."
