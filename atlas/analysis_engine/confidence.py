"""Confidence (ATLAS-020, Phase 9's counterpart concept).

Confidence answers "how trustworthy is Atlas's own analysis" -- it is
**not** investor confidence (`atlas.core.domain.decision.value_objects
.Confidence`, the investor's own 0-100 self-report at decision time,
which Atlas stores and never interprets) and it is **not** Conviction
(`conviction.py`'s "how strongly does the available analysis support an
investment conclusion").

This module deliberately defines no new type. Confidence already has a
real, canonical, categorical implementation --
`atlas.decision_engine.contracts.EvidenceCoverageLevel` (`NOT_APPLICABLE`
/ `NONE` / `PARTIAL` / `FULL`), computed once, inside
`atlas.decision_engine.stages.business_evaluation`, from real Evidence
coverage over an Investment Case's Observations. `atlas.alpha
.case_intelligence` already reuses this exact type verbatim as its own
`confidence` field (ATLAS-017). This module exists only to name that
relationship explicitly for `atlas.analysis_engine`'s own consumers, so
a future stage reaches for `EvidenceCoverageLevel` instead of inventing
a second confidence scale.
"""
from __future__ import annotations

from atlas.decision_engine.contracts import EvidenceCoverageLevel

#: The canonical Confidence type. Import this name from
#: `atlas.analysis_engine.confidence` rather than reaching into
#: `atlas.decision_engine.contracts` directly, so every future
#: Confidence-typed field in this package cites one, discoverable
#: source.
Confidence = EvidenceCoverageLevel

__all__ = ["Confidence"]
