"""A stored snapshot means what Atlas knew and used THEN.

These tests pin the persistence doctrine rather than any arithmetic: the
evidence beside a stored conclusion comes from the same composition, a
later filing never edits a row that is already written, an evidence-only
move is preserved instead of absorbed, a price tick still writes nothing,
and a row written before this contract reads back as an honest absence
rather than an empty evidence set.

No test here names a real company: every fixture is a shape.
"""
from __future__ import annotations

from datetime import date, datetime, timezone

import pytest
from sqlalchemy import create_engine, insert
from sqlalchemy.pool import StaticPool

from atlas.alpha.investment_case.valuation_evidence_metadata import describe_valuation_evidence
from atlas.alpha.investment_case.valuation_evidence_snapshot import (
    SCHEMA_VERSION,
    FrozenEpoch,
    deserialize_valuation_evidence,
    freeze_valuation_evidence,
    serialize_valuation_evidence,
)
from atlas.alpha.investment_case_change.repository import SqlAlchemyInvestmentCaseSnapshotRepository
from atlas.alpha.investment_case_change.table import (
    create_investment_case_snapshot_table,
    investment_case_snapshot_table,
)
from atlas.analysis_engine.investment_case_change import AnalyticalSnapshot, compare_snapshots
from atlas.analysis_engine.valuation.support import (
    ValuationSupport,
    ValuationSupportGapKind,
    ValuationSupportStatus,
)

from tests.unit.alpha.investment_case.test_valuation_evidence_metadata import (
    epoch,
    evidence_for,
    finding,
)

_T0 = datetime(2026, 1, 1, tzinfo=timezone.utc)
CASE = "case-1"
SUPPORT = ValuationSupport(status=ValuationSupportStatus.INSUFFICIENT_INPUT, reasoning="no envelope",
                           gap=ValuationSupportGapKind.SCENARIO_ENVELOPE_INCONCLUSIVE)
METHOD = "fiscal_epoch_v3+issuer_common_equity_market_cap_v1+common_attributable_fcf_v1"


@pytest.fixture()
def repository():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    create_investment_case_snapshot_table(engine)
    return SqlAlchemyInvestmentCaseSnapshotRepository(engine), engine


def snapshot(*, content_hash: str, captured_at: datetime = _T0) -> AnalyticalSnapshot:
    return AnalyticalSnapshot(
        business_category_states=(("growth", "moderate", "business_finding:growth"),),
        risk_category_states=(),
        valuation_status="fairly_valued",
        valuation_finding_id="valuation_finding:fcf_yield_relative",
        current_yield=0.03,
        strength_kinds=(),
        risk_highlight_kinds=(),
        open_question_origins=(),
        atlas_thesis_narrative="narrative",
        atlas_thesis_posture="strengths_only",
        content_hash=content_hash,
        captured_at=captured_at,
    )


def baseline():
    return compare_snapshots(None, snapshot(content_hash="unused"))


def frozen_issuer(priors, current, support: ValuationSupport = SUPPORT):
    """Same freeze, on the issuer share-count method every real epoch uses."""
    from atlas.analysis_engine.valuation.contracts import ValuationDecisionEligibility
    from atlas.analysis_engine.valuation.models import FcfYieldEvidence, ShareCountMethod, position_of
    evidence = FcfYieldEvidence(
        eligibility=ValuationDecisionEligibility.ELIGIBLE, minimum_prior_epochs=3,
        share_count_method=ShareCountMethod.ISSUER_COMMON_EQUITY_MARKET_CAP,
        current=current, prior_epochs=tuple(priors),
        position=position_of(current.fcf_yield, tuple(p.fcf_yield for p in priors)))
    the_finding = finding(evidence)
    return freeze_valuation_evidence(
        the_finding, support, describe_valuation_evidence(the_finding), valuation_methodology=METHOD)


def frozen(priors, current, support: ValuationSupport = SUPPORT):
    """The evidence of one composition, frozen exactly as production does."""
    the_finding = finding(evidence_for(priors, current))
    return freeze_valuation_evidence(
        the_finding, support, describe_valuation_evidence(the_finding), valuation_methodology=METHOD)


def issuer_epoch(year: int, *, fcf: float, market_cap: float, quality: str = "issuer_exact"):
    """An issuer-basis epoch: its yield is free cash flow over the ISSUER
    market capitalisation, which is not price x this security's shares in
    general. Every real corpus epoch has this shape."""
    from atlas.analysis_engine.valuation.models import FcfYieldEpochObservation
    period = f"{year}-12-31"
    shares = 1_000.0
    return FcfYieldEpochObservation(
        fiscal_period=period, available_from=date(year + 1, 2, 1), observed_on=f"{year + 1}-03-01",
        free_cash_flow=fcf, share_price=market_cap / shares, shares_outstanding=shares, currency="USD",
        free_cash_flow_fact_id=f"fcf:{period}", share_price_fact_id=f"price:{period}",
        shares_outstanding_fact_id=None, market_cap_low=market_cap, market_cap_high=market_cap,
        raw_free_cash_flow=fcf, senior_claim_low=0.0, senior_claim_high=0.0, denominator_quality=quality)


PRIORS = [epoch(2022, fcf=100, market_cap=2_000),
          epoch(2023, fcf=100, market_cap=1_250),
          epoch(2024, fcf=100, market_cap=1_000)]
CURRENT = epoch(2025, fcf=100, market_cap=1_500)


# -- what is frozen ----------------------------------------------------------


class TestFreeze:
    def test_it_records_the_accepted_priors_and_only_those(self):
        evidence = frozen(PRIORS, CURRENT)
        assert [e.fiscal_period for e in evidence.prior_epochs] == ["2022-12-31", "2023-12-31", "2024-12-31"]
        assert evidence.current_epoch.fiscal_period == "2025-12-31"

    def test_it_records_the_figures_the_valuation_actually_compared(self):
        evidence = frozen(PRIORS, CURRENT)
        assert evidence.prior_epochs[0].fcf_yield == pytest.approx(0.05)
        assert evidence.prior_epochs[0].free_cash_flow == 100
        assert evidence.current_yield == pytest.approx(100 / 1_500)

    def test_it_records_support_methodology_and_eligibility(self):
        evidence = frozen(PRIORS, CURRENT)
        assert evidence.valuation_support_status == "insufficient_input"
        assert evidence.valuation_methodology == METHOD
        assert evidence.eligibility == "eligible"
        assert evidence.minimum_prior_epochs == 3

    def test_it_records_the_descriptive_metadata_including_range_edges(self):
        evidence = frozen(PRIORS, CURRENT)
        assert evidence.metadata is not None
        assert evidence.metadata.range_edge.low_edge.fiscal_year == 2022

    def test_the_schema_version_is_separate_from_the_valuation_methodology(self):
        evidence = frozen(PRIORS, CURRENT)
        assert evidence.schema_version == SCHEMA_VERSION
        assert evidence.schema_version != evidence.valuation_methodology
        assert "fiscal_epoch" not in evidence.schema_version

    def test_a_finding_with_no_evidence_freezes_nothing_rather_than_an_empty_set(self):
        from atlas.analysis_engine.valuation.contracts import ValuationDecisionEligibility
        from atlas.analysis_engine.valuation.models import FcfYieldEvidence, ShareCountMethod
        bare = FcfYieldEvidence(
            eligibility=ValuationDecisionEligibility.NOT_APPLICABLE, minimum_prior_epochs=3,
            share_count_method=ShareCountMethod.CURRENT_SHARE_COUNT_PROXY)
        assert freeze_valuation_evidence(finding(bare), SUPPORT, None, valuation_methodology=METHOD) is not None
        empty = finding(bare)
        object.__setattr__(empty, "fcf_yield_evidence", None)
        assert freeze_valuation_evidence(empty, SUPPORT, None, valuation_methodology=METHOD) is None

    def test_an_issuer_basis_epoch_keeps_the_yield_the_valuation_used(self):
        """The stored yield is the issuer-basis figure the classification
        compared, not price x this security's shares recomputed on read --
        for a bounded or equivalent issuer those are different numbers."""
        priors = [issuer_epoch(2022, fcf=100, market_cap=2_000),
                  issuer_epoch(2023, fcf=100, market_cap=1_250),
                  issuer_epoch(2024, fcf=100, market_cap=1_000)]
        current = issuer_epoch(2025, fcf=100, market_cap=1_500)
        evidence = frozen_issuer(priors, current)
        for stored, source in zip(evidence.prior_epochs, priors):
            assert stored.fcf_yield == pytest.approx(source.fcf_yield)
            assert stored.market_cap_low == source.market_cap_low
            assert stored.raw_free_cash_flow == source.raw_free_cash_flow
        assert evidence.prior_epochs[0].denominator_quality == "issuer_exact"

    def test_the_stored_yield_is_copied_rather_than_left_to_arithmetic(self):
        """Today the epoch model forces `share_price * shares == market_cap`
        (`models.py:163`), so recomputing a yield on read would happen to
        agree. Storing it anyway is the point: the record keeps the figure the
        classification used, and stays true if that invariant is ever
        relaxed -- a bounded or equivalent issuer is exactly where it would
        be."""
        bounded = issuer_epoch(2024, fcf=100, market_cap=1_000, quality="issuer_bounded")
        stored = FrozenEpoch.of(bounded)
        assert stored.fcf_yield == pytest.approx(bounded.fcf_yield)
        assert stored.denominator_quality == "issuer_bounded"
        assert stored.market_cap_low == bounded.market_cap_low
        assert stored.market_cap_high == bounded.market_cap_high

    def test_freezing_is_deterministic(self):
        assert frozen(PRIORS, CURRENT) == frozen(PRIORS, CURRENT)
        assert frozen(PRIORS, CURRENT).fingerprint == frozen(PRIORS, CURRENT).fingerprint

    def test_round_trips_through_serialization_unchanged(self):
        evidence = frozen(PRIORS, CURRENT)
        restored = deserialize_valuation_evidence(serialize_valuation_evidence(evidence))
        assert restored.prior_epochs == evidence.prior_epochs
        assert restored.fingerprint == evidence.fingerprint
        assert restored.valuation_support_status == evidence.valuation_support_status


# -- the fingerprint ---------------------------------------------------------


class TestAtomicity:
    def test_the_stored_evidence_describes_the_stored_conclusion(self, repository):
        """Decision and evidence must come from one composition: a row whose
        frozen evidence reports a different status than the snapshot beside it
        would be two moments stitched together."""
        repo, engine = repository
        evidence = frozen(PRIORS, CURRENT)
        repo.add(CASE, snapshot(content_hash="h1"), baseline(), valuation_evidence=evidence)
        import json

        with engine.connect() as connection:
            row = connection.execute(investment_case_snapshot_table.select()).mappings().first()
        payload = json.loads(row["snapshot_json"])
        assert payload["valuation_evidence"]["valuation_status"] == payload["valuation_status"]
        assert payload["valuation_evidence"]["schema_version"] == SCHEMA_VERSION


class TestFingerprint:
    def test_a_price_tick_is_not_new_evidence(self):
        """Mirrors the existing decision that `content_hash` excludes the
        current yield: the market moving is not Atlas learning anything."""
        moved = epoch(2025, fcf=100, market_cap=1_400)
        assert frozen(PRIORS, CURRENT).fingerprint == frozen(PRIORS, moved).fingerprint

    def test_a_restated_prior_year_is_new_evidence(self):
        restated = [epoch(2022, fcf=120, market_cap=2_000), *PRIORS[1:]]
        assert frozen(restated, CURRENT).fingerprint != frozen(PRIORS, CURRENT).fingerprint

    def test_a_newly_available_fiscal_year_is_new_evidence(self):
        deeper = [epoch(2021, fcf=100, market_cap=2_500), *PRIORS]
        assert frozen(deeper, CURRENT).fingerprint != frozen(PRIORS, CURRENT).fingerprint

    def test_a_changed_valuation_support_is_new_evidence(self):
        supported = ValuationSupport(status=ValuationSupportStatus.SUPPORTED, reasoning="envelope")
        assert frozen(PRIORS, CURRENT, supported).fingerprint != frozen(PRIORS, CURRENT).fingerprint


# -- persistence doctrine ----------------------------------------------------


class TestPersistence:
    def test_a_stored_row_carries_the_evidence_of_its_own_composition(self, repository):
        repo, _ = repository
        evidence = frozen(PRIORS, CURRENT)
        assert repo.add(CASE, snapshot(content_hash="h1"), baseline(), valuation_evidence=evidence) is True
        stored = repo.get_latest_valuation_evidence(CASE)
        assert stored.prior_epochs == evidence.prior_epochs
        assert stored.fingerprint == evidence.fingerprint

    def test_an_evidence_only_change_is_preserved_not_absorbed(self, repository):
        """S1/S2: the conclusion stands still while the evidence under it
        moves. Absorbing that would leave the record asserting the evidence
        never changed."""
        repo, engine = repository
        first = frozen(PRIORS, CURRENT)
        repo.add(CASE, snapshot(content_hash="h1"), baseline(), valuation_evidence=first)
        deeper = [epoch(2021, fcf=100, market_cap=2_500), *PRIORS]
        second = frozen(deeper, CURRENT)
        # identical analytical identity -- only the evidence moved
        written = repo.add(CASE, snapshot(content_hash="h1", captured_at=datetime(2026, 2, 1, tzinfo=timezone.utc)),
                           baseline(), valuation_evidence=second)
        assert written is True
        history = repo.get_history(CASE)
        assert len(history) == 2
        assert repo.get_latest_valuation_evidence(CASE).prior_epochs == second.prior_epochs

    def test_the_earlier_row_keeps_its_own_evidence_forever(self, repository):
        """A later filing produces a new snapshot; it never edits an old one."""
        repo, engine = repository
        first = frozen(PRIORS, CURRENT)
        repo.add(CASE, snapshot(content_hash="h1"), baseline(), valuation_evidence=first)
        restated = [epoch(2022, fcf=999, market_cap=2_000), *PRIORS[1:]]
        repo.add(CASE, snapshot(content_hash="h1", captured_at=datetime(2026, 3, 1, tzinfo=timezone.utc)),
                 baseline(), valuation_evidence=frozen(restated, CURRENT))
        import json

        with engine.connect() as connection:
            rows = sorted(
                (row["captured_at"], json.loads(row["snapshot_json"])["valuation_evidence"])
                for row in connection.execute(investment_case_snapshot_table.select()).mappings()
            )
        oldest = rows[0][1]
        assert oldest["prior_epochs"][0]["free_cash_flow"] == 100, "the original row was edited"
        assert rows[1][1]["prior_epochs"][0]["free_cash_flow"] == 999

    def test_a_price_tick_alone_still_writes_nothing(self, repository):
        repo, _ = repository
        repo.add(CASE, snapshot(content_hash="h1"), baseline(), valuation_evidence=frozen(PRIORS, CURRENT))
        moved = epoch(2025, fcf=100, market_cap=1_400)
        assert repo.add(CASE, snapshot(content_hash="h1"), baseline(),
                        valuation_evidence=frozen(PRIORS, moved)) is False
        assert len(repo.get_history(CASE)) == 1

    def test_identical_evidence_is_idempotent(self, repository):
        repo, _ = repository
        evidence = frozen(PRIORS, CURRENT)
        assert repo.add(CASE, snapshot(content_hash="h1"), baseline(), valuation_evidence=evidence) is True
        assert repo.add(CASE, snapshot(content_hash="h1"), baseline(), valuation_evidence=evidence) is False
        assert len(repo.get_history(CASE)) == 1

    def test_a_decision_change_still_writes_as_it_always_did(self, repository):
        repo, _ = repository
        evidence = frozen(PRIORS, CURRENT)
        repo.add(CASE, snapshot(content_hash="h1"), baseline(), valuation_evidence=evidence)
        assert repo.add(CASE, snapshot(content_hash="h2", captured_at=datetime(2026, 4, 1, tzinfo=timezone.utc)),
                        baseline(), valuation_evidence=evidence) is True

    def test_a_caller_that_freezes_nothing_behaves_exactly_as_before(self, repository):
        repo, _ = repository
        assert repo.add(CASE, snapshot(content_hash="h1"), baseline()) is True
        assert repo.add(CASE, snapshot(content_hash="h1"), baseline()) is False
        assert repo.get_latest_valuation_evidence(CASE) is None


# -- legacy rows -------------------------------------------------------------


class TestLegacy:
    def test_a_row_written_before_this_contract_reads_back_as_absent(self, repository):
        """Absent is not empty: a legacy row never recorded evidence, which is
        a different fact from a recorded evidence set with no priors."""
        repo, engine = repository
        import json

        with engine.begin() as connection:
            connection.execute(insert(investment_case_snapshot_table).values(
                id=f"{CASE}:legacy", case_id=CASE, captured_at=_T0.isoformat(), content_hash="old",
                current_yield=None,
                snapshot_json=json.dumps({
                    "business_category_states": [], "risk_category_states": [],
                    "valuation_status": "fairly_valued", "valuation_finding_id": "f",
                    "strength_kinds": [], "risk_highlight_kinds": [], "open_question_origins": [],
                }),
                change_intelligence_json=None))
        assert repo.get_latest_valuation_evidence(CASE) is None
        assert repo.get_latest(CASE) is not None, "the legacy row must still be readable"

    def test_a_recorded_but_empty_prior_set_is_not_absent(self, repository):
        """The honest opposite: a Case whose method produced no valid priors
        still records methodology, eligibility and support."""
        repo, _ = repository
        from atlas.analysis_engine.valuation.contracts import ValuationDecisionEligibility
        from atlas.analysis_engine.valuation.models import FcfYieldEvidence, ShareCountMethod
        bare = FcfYieldEvidence(
            eligibility=ValuationDecisionEligibility.NOT_APPLICABLE, minimum_prior_epochs=3,
            share_count_method=ShareCountMethod.CURRENT_SHARE_COUNT_PROXY)
        evidence = freeze_valuation_evidence(finding(bare), SUPPORT, None, valuation_methodology=METHOD)
        repo.add(CASE, snapshot(content_hash="h1"), baseline(), valuation_evidence=evidence)
        stored = repo.get_latest_valuation_evidence(CASE)
        assert stored is not None
        assert stored.prior_epochs == ()
        assert stored.eligibility == "not_applicable"

    def test_a_legacy_head_followed_by_a_frozen_row_writes_once(self, repository):
        """The one-time transition: a Case whose head predates the contract
        gains exactly one row, then settles."""
        repo, engine = repository
        import json

        with engine.begin() as connection:
            connection.execute(insert(investment_case_snapshot_table).values(
                id=f"{CASE}:legacy", case_id=CASE, captured_at=_T0.isoformat(), content_hash="h1",
                current_yield=None,
                snapshot_json=json.dumps({
                    "business_category_states": [], "risk_category_states": [],
                    "valuation_status": "fairly_valued", "valuation_finding_id": "f",
                    "strength_kinds": [], "risk_highlight_kinds": [], "open_question_origins": [],
                }),
                change_intelligence_json=None))
        evidence = frozen(PRIORS, CURRENT)
        later = datetime(2026, 5, 1, tzinfo=timezone.utc)
        assert repo.add(CASE, snapshot(content_hash="h1", captured_at=later), baseline(),
                        valuation_evidence=evidence) is True
        even_later = datetime(2026, 6, 1, tzinfo=timezone.utc)
        assert repo.add(CASE, snapshot(content_hash="h1", captured_at=even_later), baseline(),
                        valuation_evidence=evidence) is False


# -- methodology identity ----------------------------------------------------


class TestMethodologyIdentity:
    def test_two_methods_produce_different_evidence_identities(self):
        the_finding = finding(evidence_for(PRIORS, CURRENT))
        v3 = freeze_valuation_evidence(the_finding, SUPPORT, None, valuation_methodology=METHOD)
        v4 = freeze_valuation_evidence(the_finding, SUPPORT, None, valuation_methodology="fiscal_epoch_v4")
        assert v3.fingerprint != v4.fingerprint
        assert v3.valuation_methodology != v4.valuation_methodology

    def test_the_method_that_built_the_evidence_travels_with_it(self):
        evidence = frozen(PRIORS, CURRENT)
        restored = deserialize_valuation_evidence(serialize_valuation_evidence(evidence))
        assert restored.valuation_methodology == METHOD
        assert restored.share_count_method == evidence.share_count_method


class TestReconstruction:
    def test_the_history_helper_returns_each_rows_own_frozen_evidence(self, repository):
        repo, _ = repository
        first = frozen(PRIORS, CURRENT)
        repo.add(CASE, snapshot(content_hash="h1"), baseline(), valuation_evidence=first)
        deeper = [epoch(2021, fcf=100, market_cap=2_500), *PRIORS]
        second = frozen(deeper, CURRENT)
        repo.add(CASE, snapshot(content_hash="h1", captured_at=datetime(2026, 7, 1, tzinfo=timezone.utc)),
                 baseline(), valuation_evidence=second)
        history = repo.get_valuation_evidence_history(CASE)
        assert len(history) == 2
        assert [len(evidence.prior_epochs) for _, evidence in history] == [3, 4]
        assert history[0][1].fingerprint == first.fingerprint

    def test_a_legacy_row_appears_in_the_history_as_an_honest_absence(self, repository):
        repo, engine = repository
        import json

        with engine.begin() as connection:
            connection.execute(insert(investment_case_snapshot_table).values(
                id=f"{CASE}:legacy", case_id=CASE, captured_at=_T0.isoformat(), content_hash="old",
                current_yield=None,
                snapshot_json=json.dumps({
                    "business_category_states": [], "risk_category_states": [],
                    "valuation_status": "fairly_valued", "valuation_finding_id": "f",
                    "strength_kinds": [], "risk_highlight_kinds": [], "open_question_origins": [],
                }),
                change_intelligence_json=None))
        repo.add(CASE, snapshot(content_hash="new", captured_at=datetime(2026, 8, 1, tzinfo=timezone.utc)),
                 baseline(), valuation_evidence=frozen(PRIORS, CURRENT))
        history = repo.get_valuation_evidence_history(CASE)
        assert [evidence is None for _, evidence in history] == [True, False]


# -- the firewall ------------------------------------------------------------


#: Every surface that turns evidence into something the investor acts on.
#: None of them may read history: a stored snapshot is a record, and a record
#: that can influence the next decision stops being one.
DECISION_ROOTS = (
    "atlas/analysis_engine", "atlas/decision_engine", "atlas/alpha/portfolio_fit",
    "atlas/alpha/investment_decision", "atlas/alpha/decision_support.py",
    "atlas/alpha/decision_memory", "atlas/alpha/portfolio_intelligence",
)
SNAPSHOT_MODULE = "atlas.alpha.investment_case.valuation_evidence_snapshot"


class TestImportFirewall:
    @staticmethod
    def _python_files(root: str):
        from pathlib import Path
        target = Path(__file__).resolve().parents[4] / root
        return [target] if target.is_file() else sorted(target.rglob("*.py"))

    def test_no_decision_bearing_module_imports_the_frozen_evidence(self):
        import ast
        from pathlib import Path

        repository_root = Path(__file__).resolve().parents[4]
        offenders = []
        for root in DECISION_ROOTS:
            for path in self._python_files(root):
                tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
                for node in ast.walk(tree):
                    module = None
                    if isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
                        module = node.module
                    elif isinstance(node, ast.Import):
                        module = next((a.name for a in node.names if a.name.startswith(SNAPSHOT_MODULE)), None)
                    if module is not None and module.startswith(SNAPSHOT_MODULE):
                        offenders.append(str(path.relative_to(repository_root)))
        assert offenders == []

    def test_no_decision_bearing_module_reads_the_snapshot_repository(self):
        from pathlib import Path

        repository_root = Path(__file__).resolve().parents[4]
        offenders = [
            str(path.relative_to(repository_root))
            for root in DECISION_ROOTS
            for path in self._python_files(root)
            if "get_latest_valuation_evidence" in path.read_text(encoding="utf-8")
        ]
        assert offenders == []

    def test_the_frozen_evidence_never_imports_a_decision_module(self):
        """One-way by construction: evidence flows into the record, never out
        of it into a decision."""
        import ast
        from pathlib import Path

        source = (Path(__file__).resolve().parents[4]
                  / "atlas/alpha/investment_case/valuation_evidence_snapshot.py").read_text(encoding="utf-8")
        imported = {node.module for node in ast.walk(ast.parse(source))
                    if isinstance(node, ast.ImportFrom) and node.module}
        assert not any(name.startswith("atlas.decision_engine") for name in imported)
        assert not any("direction_selector" in name or "recommendation" in name for name in imported)
