"""Closed taxonomies for forward-looking claims (Forward-Looking
Evidence, Stage 1).

Every enum here is deliberately small. Stage 1's governing preference is
**fewer high-confidence types over broad weak extraction**: a member is
added only once the persisted transcript corpus proves it can be
recognised deterministically, without semantic interpretation. A concept
Atlas cannot recognise safely is absent rather than approximated.
"""
from __future__ import annotations

from enum import Enum

__all__ = ["ClaimType", "ClaimSubject", "ClaimBound", "ClaimantRole", "ClaimRejectionReason"]


class ClaimType(str, Enum):
    """What kind of statement this is -- never what it is about (that is
    `ClaimSubject`).

    **Only `GUIDANCE` is implemented in Stage 1.** The architecture audit
    also named CONTRACT, CAPACITY and COMMITMENT as candidates. Measured
    against the real corpus, none of the three can be recognised without
    reading meaning: "we signed an agreement with a hyperscaler" carries
    no deterministic value, unit or horizon, and a rule loose enough to
    catch it would also catch a sentence merely mentioning a contract.
    They are named here only in this docstring, not as members: an
    unreachable enum member reads as a capability Atlas has.
    """

    GUIDANCE = "guidance"
    """A company insider stating a forward expectation for a named
    financial measure, with a value and a future period. Deliberately
    not called FORECAST: Atlas produces forecasts, companies issue
    guidance, and the two must never share a name."""


class ClaimSubject(str, Enum):
    """What the claim is about. A closed set, matched against explicit
    surface forms -- an unmatched subject rejects the candidate rather
    than being stored as free text, because a subject Atlas cannot name
    is one it also cannot later compare against anything."""

    REVENUE = "revenue"
    ADJUSTED_EBITDA = "adjusted_ebitda"
    FREE_CASH_FLOW = "free_cash_flow"
    CAPITAL_EXPENDITURE = "capital_expenditure"


class ClaimBound(str, Enum):
    """How the stated value bounds the measure. "Between $6.8B and
    $7.6B" is not the same claim as "$6.8B", and flattening a range to
    one of its endpoints would silently invent precision management did
    not offer."""

    POINT = "point"
    RANGE = "range"
    LOWER_BOUND = "lower_bound"
    """"more than $10 billion", "at least $6 billion"."""
    UPPER_BOUND = "upper_bound"
    """"up to", "no more than"."""


class ClaimantRole(str, Enum):
    """Who made the statement. The distinction exists because an analyst
    asking "should we expect $7 billion?" and a CFO saying "we expect $7
    billion" are the same words and opposite evidence."""

    EXECUTIVE = "executive"
    ANALYST = "analyst"
    OPERATOR = "operator"
    UNKNOWN = "unknown"


class ClaimRejectionReason(str, Enum):
    """Why a candidate sentence produced no claim. Kept as real,
    inspectable output rather than a silent `continue`: "Atlas found no
    guidance in this call" and "Atlas has no transcript for this
    company" are materially different answers, and so are the reasons
    between them."""

    NOT_A_COMPANY_INSIDER = "not_a_company_insider"
    NO_FORWARD_MARKER = "no_forward_marker"
    HISTORICAL_STATEMENT = "historical_statement"
    NO_KNOWN_SUBJECT = "no_known_subject"
    NO_VALUE = "no_value"
    NO_EXPLICIT_FUTURE_PERIOD = "no_explicit_future_period"
    ATTRIBUTED_TO_A_THIRD_PARTY = "attributed_to_a_third_party"
