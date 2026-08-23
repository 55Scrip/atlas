"""Cross-layer consistency property tests for Decision Reliability
(Deliverable 12). Exhaustive over the closed vocabularies involved --
the same discipline `tests/unit/alpha/decision_explanation
/test_cross_layer_consistency.py` already established."""
from __future__ import annotations

from itertools import product

import pytest

from atlas.alpha.coverage.models import ConfidenceLevel
from atlas.alpha.decision_readiness.models import DecisionReadinessStatus
from atlas.alpha.decision_reliability.engine import classify_reliability
from atlas.alpha.decision_reliability.models import ReliabilityLevel
from atlas.alpha.evidence_quality.models import EvidenceQualityLevel

_LEVEL_ORDER = [
    ReliabilityLevel.UNKNOWN,
    ReliabilityLevel.UNAVAILABLE,
    ReliabilityLevel.LIMITED,
    ReliabilityLevel.MODERATE,
    ReliabilityLevel.HIGH,
]


class TestClassificationIsDeterministic:
    """Exhaustive over every (readiness, confidence, evidence_quality)
    combination this codebase's own closed vocabularies allow --
    identical inputs must always produce the identical level, and the
    result must always be a real `ReliabilityLevel` member."""

    @pytest.mark.parametrize(
        "readiness,confidence,evidence_quality",
        list(product(DecisionReadinessStatus, ConfidenceLevel, EvidenceQualityLevel)),
    )
    def test_classification_is_pure_and_always_a_real_level(self, readiness, confidence, evidence_quality):
        first = classify_reliability(readiness, confidence, evidence_quality)
        second = classify_reliability(readiness, confidence, evidence_quality)
        assert first == second
        assert first in _LEVEL_ORDER


class TestClassificationNeverContradictsReadinessFloorStates:
    """`UNKNOWN`/`UNAVAILABLE` readiness are floor states no amount of
    confidence or evidence quality can override -- exhaustive check
    that this holds for every real confidence/evidence-quality pair."""

    @pytest.mark.parametrize("confidence,evidence_quality", list(product(ConfidenceLevel, EvidenceQualityLevel)))
    def test_unknown_readiness_always_yields_unknown_reliability(self, confidence, evidence_quality):
        assert classify_reliability(DecisionReadinessStatus.UNKNOWN, confidence, evidence_quality) is ReliabilityLevel.UNKNOWN

    @pytest.mark.parametrize("confidence,evidence_quality", list(product(ConfidenceLevel, EvidenceQualityLevel)))
    def test_unavailable_readiness_always_yields_unavailable_reliability(self, confidence, evidence_quality):
        assert (
            classify_reliability(DecisionReadinessStatus.UNAVAILABLE, confidence, evidence_quality)
            is ReliabilityLevel.UNAVAILABLE
        )
