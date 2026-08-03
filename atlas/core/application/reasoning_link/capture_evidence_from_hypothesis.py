"""Composite application service: Evidence captured against a Hypothesis
(ATLAS-001 Core Loop, step 5 of 10).

Verifies the referenced Hypothesis exists (reusing Hypothesis's own
existing HypothesisNotFoundError, not a duplicate), then reuses the
existing, unmodified EvidenceService to construct the Evidence, and
records the HypothesisEvidenceLink atomically. Never writes to
HypothesisRepository or modifies Evidence's own construction path.

Atlas Alpha, Evidence Sprint 1: Evidence now mandatorily anchors to an
Observation (see atlas.core.application.evidence.capture_evidence). This
Core Loop step has no way to derive one from a Hypothesis alone —
Hypothesis is "a freestanding, unanchored belief" (see
atlas.core.domain.interpretation.entity's own module docstring) and does
not itself carry a reference back to the Observation/Interpretation it
may have originated from. The caller must therefore supply the
originating Observation's id directly, exactly as
`test_core_loop_end_to_end.py` already can (it has the real Observation
from step 2 in scope by the time this step runs). This is a required,
genuine caller-supplied value, not a fabricated one.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime

from atlas.core.application.evidence.capture_evidence import (
    CaptureEvidenceRequest,
    EvidenceService,
)
from atlas.core.domain.evidence.entity import Evidence
from atlas.core.domain.hypothesis.exceptions import HypothesisNotFoundError
from atlas.core.domain.hypothesis.repository import HypothesisRepository
from atlas.core.domain.hypothesis.value_objects import HypothesisId
from atlas.core.domain.reasoning_link.entity import HypothesisEvidenceLink
from atlas.core.domain.reasoning_link.repository import HypothesisEvidenceLinkRepository


@dataclass(frozen=True)
class CaptureEvidenceFromHypothesisRequest:
    hypothesis_id: uuid.UUID
    observation_id: uuid.UUID
    statement: str
    direction: str
    observed_at: datetime
    source: str | None = None
    note: str | None = None


@dataclass(frozen=True)
class CaptureEvidenceFromHypothesisResult:
    evidence: Evidence
    link: HypothesisEvidenceLink


class CaptureEvidenceFromHypothesisService:
    def __init__(
        self,
        hypothesis_repository: HypothesisRepository,
        evidence_service: EvidenceService,
        link_repository: HypothesisEvidenceLinkRepository,
    ) -> None:
        self._hypotheses = hypothesis_repository
        self._evidence_service = evidence_service
        self._links = link_repository

    def capture(
        self, request: CaptureEvidenceFromHypothesisRequest
    ) -> CaptureEvidenceFromHypothesisResult:
        hypothesis_id = HypothesisId(request.hypothesis_id)

        if self._hypotheses.get(hypothesis_id) is None:
            raise HypothesisNotFoundError(f"No Hypothesis found with id {hypothesis_id}")

        evidence = self._evidence_service.capture(
            CaptureEvidenceRequest(
                observation_id=request.observation_id,
                statement=request.statement,
                direction=request.direction,
                observed_at=request.observed_at,
                source=request.source,
                note=request.note,
            )
        )
        link = HypothesisEvidenceLink.capture(
            hypothesis_id=hypothesis_id, evidence_id=evidence.id
        )
        self._links.add(link)
        return CaptureEvidenceFromHypothesisResult(evidence=evidence, link=link)
