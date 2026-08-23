"""Evidence Timeline (Atlas Intelligence -- Evidence Timeline &
Historical Understanding).

Captures, persists, and compares point-in-time snapshots of Coverage &
Confidence, Stance, and Evidence Quality's own signals for a Case -- the
one real gap `atlas.analysis_engine.investment_case_change`'s own
"History v1" mechanism never covered, since it predates all three. Also
tracks **Source Evidence History** (Deliverable 2) -- new financial
periods/facts becoming known, kept structurally separate from **Atlas
Analysis History** (Atlas's own conclusions changing) via two distinct
types (`SourceEvidenceEvent` vs. `EvidenceTransition`), never one mixed
list. See `engine.py`'s own module docstring for the full audit and
derivation rules.

**Deliverable 13 -- Stance Change Audit, resolved.** Sprint 2 left open
whether `Stance` needed its own dedicated persistence to support literal
transitions ("Maintain → Review"). Investigated fresh from disk: neither
`atlas.analysis_engine.investment_case_change`'s own `AnalyticalSnapshot`
(it excludes every investor-evidence-derived signal by design -- see
that module's own "Investor Model boundary" docstring) nor any other
existing infrastructure captures a Case's historical Stance. **This
package already is that lightweight persistence** -- `EvidenceSnapshot
.stance_level` has captured the real `StanceLevel` at every real capture
since this package first shipped, and `compare_evidence_snapshots`'s own
`_stance_transition` already detects exact before/after transitions
(`STANCE_CHANGED`, `previous_state`/`current_state` preserved verbatim)
whenever two real, persisted snapshots genuinely differ. No second,
Stance-only historical subsystem was built, and none is needed: a
dedicated Stance store would duplicate exactly what this package's own
shared `EvidenceSnapshot` already provides, at the cost of a second
table and a second capture/compare pair to keep in sync with this one.
The one real limitation, stated honestly: Stance history only exists
from the moment this package first captured a snapshot for a given
Case -- a Case whose Stance changed before that point has no recorded
prior state, and `is_baseline=True` (never a fabricated "Maintain")
correctly reports that.
"""
from __future__ import annotations

from .engine import capture_evidence_snapshot, compare_evidence_snapshots, derive_staleness_date, is_material_transition, material_transitions
from .models import EvidenceHistory, EvidenceSnapshot, EvidenceTransition, EvidenceTransitionCategory, SourceEvidenceEvent

__all__ = [
    "capture_evidence_snapshot",
    "compare_evidence_snapshots",
    "is_material_transition",
    "material_transitions",
    "derive_staleness_date",
    "EvidenceHistory",
    "EvidenceSnapshot",
    "EvidenceTransition",
    "EvidenceTransitionCategory",
    "SourceEvidenceEvent",
]
