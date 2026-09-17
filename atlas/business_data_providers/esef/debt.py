"""Gross debt, or nothing.

Every other field in this package can be wrong by being absent. Debt is the
one that can be wrong by being present, and Volvo is the proof. Its balance
sheet tags bonds on both sides -- 46,641 MSEK current, 96,970 MSEK
non-current -- so a rule that looks for a current concept and a non-current
concept finds both, concludes it has the whole picture, and returns
143,611 MSEK. Volvo's interest-bearing total is about 236,791 MSEK. The rest
sits in two concepts the company invented, `CurrentOtherLoans` and
`NoncurrentOtherLoans`, which that rule never looked for.

A 39% under-count would have read as a debt burden near 5.4x instead of 8.9x:
a different band, a different risk level, and nothing anywhere to suggest a
number was missing. Withholding is safe. Under-counting confidently is not.

So this resolver never asks "did I find a current and a non-current concept".
It asks the calculation linkbase for **every** child of current and
non-current liabilities, decides for each whether it is interest-bearing, and
refuses unless it can account for all of them:

1. A child is debt only if it is a standard borrowings concept, or an
   extension that anchoring proves is a borrowings concept.
2. If any debt child is a bucket that anchoring shows also contains lease
   liabilities, the doctrine-excluded part cannot be separated -- withhold.
3. Both sides are required, exactly as `sec_edgar` requires. One side alone
   is never half a number; it is no number.
4. A parent is never summed with its own children.

Atlas's doctrine, which this follows rather than sets, lives in
`business_data_providers/sec_edgar.py`: current plus non-current
interest-bearing debt when both are known, a single total concept as the
fallback, and operating leases excluded (the US-GAAP tags it reads --
`LongTermDebtCurrent`, `LongTermDebtNoncurrent`, `LongTermDebt` -- exclude
them).
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from atlas.business_data_providers.esef.taxonomy import EsefTaxonomy

__all__ = ["DebtOutcome", "DebtResolution", "resolve_gross_debt",
           "CURRENT_BORROWINGS", "NONCURRENT_BORROWINGS", "TOTAL_BORROWINGS", "LEASE_CONCEPTS"]

#: Standard IFRS borrowings concepts, by side. Membership is what makes a
#: concept debt; nothing is matched on its name.
CURRENT_BORROWINGS: frozenset[str] = frozenset({
    "ifrs-full_CurrentBorrowingsAndCurrentPortionOfNoncurrentBorrowings",
    "ifrs-full_CurrentPortionOfLongtermBorrowings",
    "ifrs-full_ShorttermBorrowings",
    "ifrs-full_CurrentBondsIssuedAndCurrentPortionOfNoncurrentBondsIssued",
    "ifrs-full_CurrentCommercialPapersIssued",
})
NONCURRENT_BORROWINGS: frozenset[str] = frozenset({
    "ifrs-full_LongtermBorrowings",
    "ifrs-full_NoncurrentPortionOfNoncurrentBorrowings",
    "ifrs-full_NoncurrentPortionOfNoncurrentBondsIssued",
})
#: Used only as the single-total fallback, never added to the two sides.
TOTAL_BORROWINGS: frozenset[str] = frozenset({"ifrs-full_Borrowings"})
#: Excluded by doctrine. Also the tripwire: a debt bucket that anchoring shows
#: contains one of these is a bucket Atlas cannot safely take apart.
LEASE_CONCEPTS: frozenset[str] = frozenset({
    "ifrs-full_LeaseLiabilities",
    "ifrs-full_CurrentLeaseLiabilities",
    "ifrs-full_NoncurrentLeaseLiabilities",
})

_CURRENT_LIABILITIES = "ifrs-full_CurrentLiabilities"
_NONCURRENT_LIABILITIES = "ifrs-full_NoncurrentLiabilities"


class DebtOutcome(str, Enum):
    """What the resolver established. Only `RESOLVED` carries a figure."""

    RESOLVED = "RESOLVED"
    #: A debt bucket mixes in liabilities doctrine excludes, and the parts are
    #: not separately tagged. The Volvo case.
    MIXED_WITH_EXCLUDED = "MIXED_WITH_EXCLUDED"
    #: Only one of the two sides is tagged. Schneider.
    ONE_SIDE_ONLY = "ONE_SIDE_ONLY"
    #: No borrowings concept on either side; debt is inside a generic bucket
    #: that also holds things which are not debt. Atlas Copco.
    NOT_TAGGED = "NOT_TAGGED"
    #: The filing tags borrowings but no lease liability anywhere. Under IFRS 16
    #: a lessee has them, so they are inside some other line -- possibly the
    #: borrowings line itself. Investor AB.
    LEASES_NOT_VISIBLE = "LEASES_NOT_VISIBLE"
    #: No calculation linkbase, so completeness cannot be established at all.
    NO_TAXONOMY = "NO_TAXONOMY"


@dataclass(frozen=True)
class DebtResolution:
    outcome: DebtOutcome
    reason: str
    gross_debt: float | None = None
    #: Every concept that contributed, so the figure can be explained later.
    components: tuple[tuple[str, float], ...] = ()
    #: Debt-bearing children the resolver could not value or interpret.
    unresolved: tuple[str, ...] = ()

    @property
    def resolved(self) -> bool:
        return self.outcome is DebtOutcome.RESOLVED


def _is_borrowing(concept: str, side: frozenset[str], taxonomy: EsefTaxonomy) -> bool:
    """Whether `concept` is interest-bearing debt on this side of the sheet.

    Standard concepts are decided by membership. An extension is decided by
    anchoring in either direction: a bucket that *contains* borrowings, or a
    slice that is *part of* borrowings, is debt either way -- what differs is
    whether it can be used, which `resolve_gross_debt` decides next.
    """
    if concept in side:
        return True
    if not taxonomy.is_extension(concept):
        return False
    related = taxonomy.standards_narrower_than(concept) | taxonomy.standards_wider_than(concept)
    return bool(related & (side | TOTAL_BORROWINGS))


def resolve_gross_debt(
    taxonomy: EsefTaxonomy,
    value_of,
) -> DebtResolution:
    """Atlas gross debt for one balance-sheet date, or a reason there is none.

    `value_of(concept) -> float | None` supplies the reported figure for a
    concept at the date in question; the resolver never reads facts itself, so
    the same rule is testable without a filing.
    """
    if not taxonomy.calculations:
        return DebtResolution(DebtOutcome.NO_TAXONOMY,
                              "no calculation linkbase, so debt completeness cannot be established")

    components: list[tuple[str, float]] = []
    unresolved: list[str] = []
    found_any = False

    for parent, side in ((_CURRENT_LIABILITIES, CURRENT_BORROWINGS),
                         (_NONCURRENT_LIABILITIES, NONCURRENT_BORROWINGS)):
        side_total = 0.0
        side_found = False
        for child in taxonomy.children(parent):
            if not _is_borrowing(child, side, taxonomy):
                continue
            found_any = True
            # The tripwire. A bucket declared to contain lease liabilities
            # holds something doctrine excludes, and the filing does not tag
            # the parts, so no arithmetic here can separate them.
            contains = taxonomy.standards_narrower_than(child)
            if contains & LEASE_CONCEPTS:
                return DebtResolution(
                    DebtOutcome.MIXED_WITH_EXCLUDED,
                    f"{child} is declared wider than {sorted(contains & LEASE_CONCEPTS)}, "
                    "which doctrine excludes, and its components are not separately tagged",
                    unresolved=(child,),
                )
            value = value_of(child)
            if value is None:
                unresolved.append(child)
                continue
            components.append((child, value))
            side_total += value
            side_found = True
        if side_found:
            _ = side_total   # kept per-side for readability; summed below

    if unresolved:
        return DebtResolution(
            DebtOutcome.NOT_TAGGED,
            f"borrowings concepts present but unreported at this date: {sorted(unresolved)}",
            unresolved=tuple(sorted(unresolved)),
        )
    if not found_any:
        return DebtResolution(
            DebtOutcome.NOT_TAGGED,
            "no borrowings concept among the children of current or non-current "
            "liabilities -- debt is inside a generic bucket that also holds non-debt",
        )

    # Investor AB tags `LongtermBorrowings` and `CurrentPortionOfLongtermBorrowings`
    # -- both standard, both sides present -- and the figure behind them includes
    # SEK 2,950m of lease liabilities, because Investor gives leases no line of
    # their own. Its own annual report says so; the taxonomy cannot, since the
    # concepts used are exactly the right ones and only the value is broader.
    #
    # What the filing does reveal is the absence: under IFRS 16 a lessee carries
    # lease liabilities, so a balance sheet that tags borrowings and tags no lease
    # liability anywhere has put them somewhere unnamed. Assa Abloy tags both and
    # its borrowings are lease-exclusive, verified against its annual report
    # (66,948 MSEK, matching to a rounding unit). That difference is visible, and
    # it is the only thing that separates the two cases.
    if not any(value_of(concept) is not None for concept in LEASE_CONCEPTS):
        return DebtResolution(
            DebtOutcome.LEASES_NOT_VISIBLE,
            "borrowings are tagged but no lease liability is, so leases are inside "
            "some other line and the borrowings figure cannot be shown to exclude them",
            components=tuple(components),
        )

    current_side = [c for c in components if _side_of(c[0], taxonomy) == "current"]
    noncurrent_side = [c for c in components if _side_of(c[0], taxonomy) == "noncurrent"]
    if not current_side or not noncurrent_side:
        side = "current" if not current_side else "non-current"
        return DebtResolution(
            DebtOutcome.ONE_SIDE_ONLY,
            f"no {side} borrowings tagged; one side alone is not half a debt figure",
            components=tuple(components),
        )

    return DebtResolution(
        DebtOutcome.RESOLVED,
        "current + non-current interest-bearing borrowings, leases excluded",
        gross_debt=sum(value for _, value in components),
        components=tuple(components),
    )


def _side_of(concept: str, taxonomy: EsefTaxonomy) -> str:
    if concept in CURRENT_BORROWINGS:
        return "current"
    if concept in NONCURRENT_BORROWINGS:
        return "noncurrent"
    related = taxonomy.standards_narrower_than(concept) | taxonomy.standards_wider_than(concept)
    if related & CURRENT_BORROWINGS:
        return "current"
    if related & NONCURRENT_BORROWINGS:
        return "noncurrent"
    # An extension anchored only to the undivided total: attribute by the
    # liabilities parent it actually hangs under.
    for parent, label in ((_CURRENT_LIABILITIES, "current"), (_NONCURRENT_LIABILITIES, "noncurrent")):
        if concept in taxonomy.children(parent):
            return label
    return "unknown"
