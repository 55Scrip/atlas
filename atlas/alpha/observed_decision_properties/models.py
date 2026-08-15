"""`ObservedDecisionProperty` -- the product-safe projection of one
`RecognizedPattern` (Sprint 12's Level 0/1 contract, Sprint 13's
implementation).

Not a domain aggregate: no identity beyond its content, never
persisted, recomputed fresh on every call -- the same status Sprint
10/11 established for `RecognizedPattern`/`RecognizedStrategySignature`
themselves (see this package's own `__init__.py` for why: the real
history's own growth has already been shown, empirically, to change
membership at every checkpoint, so no stable identity would be honest
here either).

Every field is either a direct read of already-real data or a small,
documented, deterministic derivation over it -- never an inference, a
statistic, or a generated statement. See `service.py` for exactly how
each field is derived.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class ObservedPropertyScope(str, Enum):
    """Sprint 12 Phase 5/7: one generic object cannot safely claim one
    generic scope -- `SameSubjectAndTypeStrategy` is inherently scoped
    to one company; `SameConfidenceStrategy` is inherently portfolio-
    wide. This field makes that distinction explicit and mandatory on
    every property, never left implicit in prose."""

    SINGLE_COMPANY = "single_company"
    PORTFOLIO_WIDE = "portfolio_wide"


@dataclass(frozen=True)
class ObservedDecisionProperty:
    """One product-safe, evidence-backed, Level 0/1 observation about
    the investor's own recorded Decision history.

    `property_type` reuses the recognition strategy's own already-
    stable, already-documented `name` string
    (`SameSubjectAndTypeStrategy.name`/`SameConfidenceStrategy.name`)
    verbatim -- not a raw Python class name, and not a new vocabulary
    invented at this layer (Sprint 13 Phase 4).
    """

    property_type: str
    factual_description: str
    scope: ObservedPropertyScope
    observed_count: int
    total_eligible_decisions: int
    proportion: float
    supporting_decision_ids: tuple[str, ...]
    first_observed_at: datetime
    last_observed_at: datetime
    outcome_aware: bool
    sample_size_warning: bool
