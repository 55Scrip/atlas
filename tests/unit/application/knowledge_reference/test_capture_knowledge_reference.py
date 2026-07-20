"""Application-layer tests for KnowledgeReferenceService (DO-IMP-003).

**Corrected per docs/atlas_domain_object_architecture/
Knowledge-Reference-Pre-Commit-Architecture-Review.md, Outcome 2**:
capture is currently enabled only for `DomainObjectType.KNOWLEDGE_REFERENCE`
targets. Observation, Reasoning Trace, Judgment, Decision, and Outcome
remain fully canonical, reference-eligible target types (OE-002 §5.2)
but are all currently rejected with `TargetTypeUnavailableError`, since
none of their applicable invariants can currently be positively
established (see `capture_knowledge_reference.py`'s own module
docstring for the precise, per-type reasons).

**A genuine consequence of the correction, not a test artifact**: since
capture is enabled only for Knowledge-Reference-targeting-Knowledge-
Reference, and Knowledge Reference has no internal-content alternative
form (OE-002 §5.2 names only the referential form), `service.capture()`
itself can never produce the *first* accepted Knowledge Reference in an
empty store — there is nothing yet to target. Every test below that
needs a pre-existing accepted Knowledge Reference to reference seeds
one directly via `KnowledgeReference.capture()` + `repository.add()`
(bypassing the service's own referential validation entirely, exactly
as the persistence-layer tests already do), then exercises the actual
unit under test — `KnowledgeReferenceService` — against that seed.

Exercises the service against a real (in-memory) SQLite repository, not
a fake, matching the convention used elsewhere in this codebase.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from atlas.core.application.knowledge_reference.capture_knowledge_reference import (
    CaptureKnowledgeReferenceRequest,
    KnowledgeReferenceService,
)
from atlas.core.domain.case.value_objects import CaseId
from atlas.core.domain.knowledge_reference.entity import KnowledgeReference
from atlas.core.domain.knowledge_reference.exceptions import (
    CrossCaseTargetError,
    KnowledgeReferenceNotFoundError,
    TargetNotFoundError,
    TargetTypeUnavailableError,
)
from atlas.core.domain.knowledge_reference.value_objects import KnowledgeReferenceId
from atlas.core.domain.shared.domain_object_type import DomainObjectType
from atlas.core.domain.shared.typed_reference import TypedDomainObjectReference
from atlas.core.infrastructure.persistence.knowledge_reference.sqlalchemy_repository import (
    SqlAlchemyKnowledgeReferenceRepository,
)
from atlas.core.infrastructure.persistence.knowledge_reference.table import (
    create_knowledge_reference_table,
    knowledge_references_table,
)

_CURRENTLY_UNAVAILABLE_TARGET_TYPES = (
    DomainObjectType.OBSERVATION,
    DomainObjectType.REASONING_TRACE,
    DomainObjectType.JUDGMENT,
    DomainObjectType.DECISION,
    DomainObjectType.OUTCOME,
)


@pytest.fixture
def repository():
    engine = create_engine(
        "sqlite:///:memory:",
        future=True,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    create_knowledge_reference_table(engine)
    return SqlAlchemyKnowledgeReferenceRepository(engine)


@pytest.fixture
def service(repository):
    return KnowledgeReferenceService(repository)


def _seed(repository, *, case_id: uuid.UUID | None = None) -> KnowledgeReference:
    """Directly construct and persist a Knowledge Reference, bypassing
    KnowledgeReferenceService's own referential validation — the only
    way any Knowledge Reference can exist to be targeted by the first
    real, service-validated capture in an otherwise-empty store.
    """
    seed = KnowledgeReference.capture(
        case_id=CaseId(case_id if case_id is not None else uuid.uuid4()),
        target=TypedDomainObjectReference(
            target_type=DomainObjectType.KNOWLEDGE_REFERENCE, target_id=uuid.uuid4()
        ),
    )
    repository.add(seed)
    return seed


def _row_ids(repository) -> set[str]:
    with repository._engine.connect() as connection:
        from sqlalchemy import select

        rows = connection.execute(select(knowledge_references_table)).mappings().all()
    return {row["knowledge_reference_id"] for row in rows}


class TestSuccessfulCapture:
    def test_captures_against_a_previously_accepted_knowledge_reference_in_the_same_case(
        self, service, repository
    ):
        case_id = uuid.uuid4()
        seed = _seed(repository, case_id=case_id)
        captured = service.capture(
            CaptureKnowledgeReferenceRequest(
                case_id=case_id,
                target_type=DomainObjectType.KNOWLEDGE_REFERENCE,
                target_id=seed.id.value,
            )
        )
        assert captured.target.target_type is DomainObjectType.KNOWLEDGE_REFERENCE
        assert captured.target.target_id == seed.id.value

    def test_target_is_persisted_exactly(self, service, repository):
        case_id = uuid.uuid4()
        seed = _seed(repository, case_id=case_id)
        captured = service.capture(
            CaptureKnowledgeReferenceRequest(
                case_id=case_id,
                target_type=DomainObjectType.KNOWLEDGE_REFERENCE,
                target_id=seed.id.value,
            )
        )
        reloaded = repository.get(captured.id)
        assert reloaded.target.target_type is DomainObjectType.KNOWLEDGE_REFERENCE
        assert reloaded.target.target_id == seed.id.value

    def test_recorded_at_remains_acceptance_time(self, service, repository):
        case_id = uuid.uuid4()
        seed = _seed(repository, case_id=case_id)
        before = datetime.now(timezone.utc)
        captured = service.capture(
            CaptureKnowledgeReferenceRequest(
                case_id=case_id,
                target_type=DomainObjectType.KNOWLEDGE_REFERENCE,
                target_id=seed.id.value,
            )
        )
        after = datetime.now(timezone.utc)
        assert before <= captured.recorded_at <= after

    def test_a_third_knowledge_reference_may_target_an_earlier_accepted_one(
        self, service, repository
    ):
        case_id = uuid.uuid4()
        seed = _seed(repository, case_id=case_id)
        second = service.capture(
            CaptureKnowledgeReferenceRequest(
                case_id=case_id,
                target_type=DomainObjectType.KNOWLEDGE_REFERENCE,
                target_id=seed.id.value,
            )
        )
        third = service.capture(
            CaptureKnowledgeReferenceRequest(
                case_id=case_id,
                target_type=DomainObjectType.KNOWLEDGE_REFERENCE,
                target_id=seed.id.value,
            )
        )
        assert third.target.target_id == seed.id.value
        assert third.id != second.id


class TestPriorAcceptance:
    def test_rejects_a_nonexistent_knowledge_reference(self, service):
        with pytest.raises(TargetNotFoundError):
            service.capture(
                CaptureKnowledgeReferenceRequest(
                    case_id=uuid.uuid4(),
                    target_type=DomainObjectType.KNOWLEDGE_REFERENCE,
                    target_id=uuid.uuid4(),
                )
            )

    def test_no_knowledge_reference_is_persisted_after_rejection(self, service, repository):
        bogus_target_id = uuid.uuid4()
        with pytest.raises(TargetNotFoundError):
            service.capture(
                CaptureKnowledgeReferenceRequest(
                    case_id=uuid.uuid4(),
                    target_type=DomainObjectType.KNOWLEDGE_REFERENCE,
                    target_id=bogus_target_id,
                )
            )
        assert repository.get(KnowledgeReferenceId(bogus_target_id)) is None


class TestSameCase:
    def test_rejects_a_knowledge_reference_target_from_a_different_case(self, service, repository):
        seed = _seed(repository)  # its own random Case
        with pytest.raises(CrossCaseTargetError):
            service.capture(
                CaptureKnowledgeReferenceRequest(
                    case_id=uuid.uuid4(),  # deliberately a different Case
                    target_type=DomainObjectType.KNOWLEDGE_REFERENCE,
                    target_id=seed.id.value,
                )
            )

    def test_no_knowledge_reference_is_persisted_after_cross_case_rejection(
        self, service, repository
    ):
        seed = _seed(repository)
        before_ids = _row_ids(repository)
        with pytest.raises(CrossCaseTargetError):
            service.capture(
                CaptureKnowledgeReferenceRequest(
                    case_id=uuid.uuid4(),
                    target_type=DomainObjectType.KNOWLEDGE_REFERENCE,
                    target_id=seed.id.value,
                )
            )
        assert _row_ids(repository) == before_ids


class TestCanonicalButCurrentlyUnavailableTargetTypes:
    """Every one of these five target types is a fully adopted,
    canonical DomainObjectType member (OE-002 §5.2) — rejection here
    reflects only that Knowledge Reference capture cannot currently
    establish every applicable invariant for it, never that the type
    itself is unknown, invalid, or non-adopted.
    """

    @pytest.mark.parametrize("target_type", _CURRENTLY_UNAVAILABLE_TARGET_TYPES)
    def test_the_target_type_is_structurally_valid(self, target_type):
        assert target_type in set(DomainObjectType)

    @pytest.mark.parametrize("target_type", _CURRENTLY_UNAVAILABLE_TARGET_TYPES)
    def test_capture_rejects_it(self, service, target_type):
        with pytest.raises(TargetTypeUnavailableError):
            service.capture(
                CaptureKnowledgeReferenceRequest(
                    case_id=uuid.uuid4(),
                    target_type=target_type,
                    target_id=uuid.uuid4(),
                )
            )

    @pytest.mark.parametrize("target_type", _CURRENTLY_UNAVAILABLE_TARGET_TYPES)
    def test_the_error_does_not_claim_the_type_is_unknown_or_non_adopted(
        self, service, target_type
    ):
        with pytest.raises(TargetTypeUnavailableError) as excinfo:
            service.capture(
                CaptureKnowledgeReferenceRequest(
                    case_id=uuid.uuid4(),
                    target_type=target_type,
                    target_id=uuid.uuid4(),
                )
            )
        message = str(excinfo.value).lower()
        assert "unknown" not in message
        assert "invalid" not in message
        assert "canonical" in message or "reference-eligible" in message

    @pytest.mark.parametrize("target_type", _CURRENTLY_UNAVAILABLE_TARGET_TYPES)
    def test_no_knowledge_reference_is_persisted(self, service, repository, target_type):
        with pytest.raises(TargetTypeUnavailableError):
            service.capture(
                CaptureKnowledgeReferenceRequest(
                    case_id=uuid.uuid4(),
                    target_type=target_type,
                    target_id=uuid.uuid4(),
                )
            )
        assert _row_ids(repository) == set()


class TestUnknownTargetTypeIsNotConflatedWithUnavailableTypes:
    def test_domain_object_type_itself_rejects_unknown_values_before_capture(self):
        # "Case" is not a member of DomainObjectType at all (the
        # ownership boundary, OE-002 §3.1 — not a Domain Object). This
        # is rejected by DomainObjectType.parse/the API schema layer,
        # never reaching KnowledgeReferenceService at all — a
        # different failure mode from the five canonical-but-
        # unavailable types above, which DO reach the service and are
        # rejected there, deliberately, with a distinct exception.
        from atlas.core.domain.shared.exceptions import UnknownDomainObjectTypeError

        with pytest.raises(UnknownDomainObjectTypeError):
            DomainObjectType.parse("Case")


class TestRetrieveById:
    def test_returns_the_captured_knowledge_reference(self, service, repository):
        case_id = uuid.uuid4()
        seed = _seed(repository, case_id=case_id)
        captured = service.capture(
            CaptureKnowledgeReferenceRequest(
                case_id=case_id,
                target_type=DomainObjectType.KNOWLEDGE_REFERENCE,
                target_id=seed.id.value,
            )
        )
        assert service.get(captured.id) == captured

    def test_unknown_knowledge_reference_is_rejected(self, service):
        with pytest.raises(KnowledgeReferenceNotFoundError):
            service.get(KnowledgeReferenceId())


class TestServiceDependencySimplification:
    def test_service_depends_only_on_its_own_repository(self):
        import inspect

        signature = inspect.signature(KnowledgeReferenceService.__init__)
        assert list(signature.parameters) == ["self", "repository"]
