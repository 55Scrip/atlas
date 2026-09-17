"""Gross debt from a European filing, or a stated reason there is none.

Each case below is a real issuer's real tagging. Together they are the
argument for why this resolver is separate from the rest of normalization:
four of five filings look like they contain a debt figure, and only one
actually contains the figure Atlas's doctrine defines.
"""
from __future__ import annotations

from atlas.business_data_providers.esef.debt import DebtOutcome, resolve_gross_debt
from atlas.business_data_providers.esef.taxonomy import EsefTaxonomy

CURRENT = "ifrs-full_CurrentLiabilities"
NONCURRENT = "ifrs-full_NoncurrentLiabilities"


def taxonomy(current=(), noncurrent=(), anchors=()) -> EsefTaxonomy:
    return EsefTaxonomy(
        calculations={CURRENT: tuple((c, "1.0") for c in current),
                      NONCURRENT: tuple((c, "1.0") for c in noncurrent)},
        anchors=anchors,
    )


def values(**by_concept):
    return lambda concept: by_concept.get(concept)


# --- The case that works -----------------------------------------------

ASSA = taxonomy(
    current=("ifrs-full_CurrentBorrowingsAndCurrentPortionOfNoncurrentBorrowings",
             "ifrs-full_CurrentLeaseLiabilities", "ifrs-full_TradeAndOtherCurrentPayablesToTradeSuppliers"),
    noncurrent=("ifrs-full_LongtermBorrowings", "ifrs-full_NoncurrentLeaseLiabilities",
                "ifrs-full_DeferredTaxLiabilities"),
)
ASSA_VALUES = values(**{
    "ifrs-full_CurrentBorrowingsAndCurrentPortionOfNoncurrentBorrowings": 11_958e6,
    "ifrs-full_LongtermBorrowings": 54_989e6,
    "ifrs-full_CurrentLeaseLiabilities": 1_737e6,
    "ifrs-full_NoncurrentLeaseLiabilities": 4_817e6,
})


def test_borrowings_on_both_sides_with_leases_visible_resolve() -> None:
    """Assa Abloy. Verified against its 2024 annual report, which reports
    66,948 MSEK of loans -- the two balance-sheet lines, rounded once instead
    of twice."""
    result = resolve_gross_debt(ASSA, ASSA_VALUES)
    assert result.outcome is DebtOutcome.RESOLVED
    assert result.gross_debt == 66_947e6


def test_lease_liabilities_are_excluded_from_the_figure() -> None:
    """Doctrine excludes them, and they sit right beside the borrowings."""
    result = resolve_gross_debt(ASSA, ASSA_VALUES)
    assert result.gross_debt == 11_958e6 + 54_989e6
    assert all("Lease" not in concept for concept, _ in result.components)


# --- The four that do not ----------------------------------------------


def test_a_bucket_anchored_wider_than_leases_withholds() -> None:
    """Volvo. Bonds are tagged on both sides, so a naive rule returns
    143,611 MSEK against a real total near 236,791 -- and the missing part is
    `OtherLoans`, which the taxonomy declares also contains lease
    liabilities. Neither figure is the doctrine's."""
    volvo = taxonomy(
        current=("ifrs-full_CurrentBondsIssuedAndCurrentPortionOfNoncurrentBondsIssued",
                 "abvolvo_CurrentOtherLoans"),
        noncurrent=("ifrs-full_NoncurrentPortionOfNoncurrentBondsIssued",
                    "abvolvo_NoncurrentOtherLoans"),
        anchors=(("abvolvo_CurrentOtherLoans", "ifrs-full_CurrentLeaseLiabilities"),
                 ("abvolvo_CurrentOtherLoans", "ifrs-full_CurrentPortionOfLongtermBorrowings"),
                 ("abvolvo_NoncurrentOtherLoans", "ifrs-full_NoncurrentLeaseLiabilities"),
                 ("abvolvo_NoncurrentOtherLoans", "ifrs-full_LongtermBorrowings")),
    )
    result = resolve_gross_debt(volvo, values(**{
        "ifrs-full_CurrentBondsIssuedAndCurrentPortionOfNoncurrentBondsIssued": 46_641e6,
        "ifrs-full_NoncurrentPortionOfNoncurrentBondsIssued": 96_970e6,
        "abvolvo_CurrentOtherLoans": 51_648e6,
        "abvolvo_NoncurrentOtherLoans": 41_532e6,
    }))
    assert result.outcome is DebtOutcome.MIXED_WITH_EXCLUDED
    assert result.gross_debt is None


def test_the_bond_only_undercount_is_never_returned() -> None:
    """The specific wrong answer, named so it cannot come back."""
    volvo = taxonomy(
        current=("ifrs-full_CurrentBondsIssuedAndCurrentPortionOfNoncurrentBondsIssued",
                 "abvolvo_CurrentOtherLoans"),
        noncurrent=("ifrs-full_NoncurrentPortionOfNoncurrentBondsIssued",
                    "abvolvo_NoncurrentOtherLoans"),
        anchors=(("abvolvo_CurrentOtherLoans", "ifrs-full_CurrentLeaseLiabilities"),
                 ("abvolvo_NoncurrentOtherLoans", "ifrs-full_NoncurrentLeaseLiabilities")),
    )
    result = resolve_gross_debt(volvo, values(**{
        "ifrs-full_CurrentBondsIssuedAndCurrentPortionOfNoncurrentBondsIssued": 46_641e6,
        "ifrs-full_NoncurrentPortionOfNoncurrentBondsIssued": 96_970e6,
    }))
    assert result.gross_debt != 143_611e6
    assert result.gross_debt is None


def test_borrowings_with_no_lease_liability_anywhere_withholds() -> None:
    """Investor AB. Both sides use the right standard concepts, and its own
    annual report shows the figure behind them includes SEK 2,950m of lease
    liabilities -- because Investor gives leases no line of their own. The
    taxonomy cannot show that; the *absence* of any lease concept can."""
    investor = taxonomy(
        current=("ifrs-full_CurrentPortionOfLongtermBorrowings", "ifrs-full_TradeAndOtherCurrentPayables"),
        noncurrent=("ifrs-full_LongtermBorrowings", "ifrs-full_DeferredTaxLiabilities"),
    )
    result = resolve_gross_debt(investor, values(**{
        "ifrs-full_CurrentPortionOfLongtermBorrowings": 4_577e6,
        "ifrs-full_LongtermBorrowings": 94_389e6,
    }))
    assert result.outcome is DebtOutcome.LEASES_NOT_VISIBLE
    assert result.gross_debt is None


def test_one_side_alone_is_not_half_a_debt_figure() -> None:
    """Schneider tags long-term borrowings and nothing current."""
    schneider = taxonomy(
        current=("ifrs-full_TradeAndOtherCurrentPayables", "ifrs-full_OtherCurrentFinancialLiabilities"),
        noncurrent=("ifrs-full_LongtermBorrowings", "ifrs-full_NoncurrentLeaseLiabilities"),
    )
    result = resolve_gross_debt(schneider, values(**{
        "ifrs-full_LongtermBorrowings": 10_910e6,
        "ifrs-full_NoncurrentLeaseLiabilities": 1_000e6,
    }))
    assert result.outcome is DebtOutcome.ONE_SIDE_ONLY
    assert result.gross_debt is None


def test_debt_hidden_in_a_generic_bucket_withholds() -> None:
    """Atlas Copco tags no borrowings concept at all; its debt sits inside
    `OtherCurrentFinancialLiabilities`, which also holds things that are not
    debt. A generic bucket is not a debt figure."""
    atlas_copco = taxonomy(
        current=("ifrs-full_OtherCurrentFinancialLiabilities", "ifrs-full_CurrentProvisions"),
        noncurrent=("ifrs-full_OtherNoncurrentFinancialLiabilities", "ifrs-full_DeferredTaxLiabilities"),
    )
    result = resolve_gross_debt(atlas_copco, values(**{
        "ifrs-full_OtherCurrentFinancialLiabilities": 9_000e6,
        "ifrs-full_OtherNoncurrentFinancialLiabilities": 30_000e6,
    }))
    assert result.outcome is DebtOutcome.NOT_TAGGED
    assert result.gross_debt is None


def test_without_a_calculation_linkbase_nothing_is_claimed() -> None:
    """Completeness is the whole question, and the linkbase is the only thing
    that answers it."""
    result = resolve_gross_debt(EsefTaxonomy(), values())
    assert result.outcome is DebtOutcome.NO_TAXONOMY


def test_a_parent_is_never_summed_with_its_own_children() -> None:
    """Only the children of the liabilities roll-up are considered, so an
    undivided total and its parts can never both be counted."""
    mixed = taxonomy(
        current=("ifrs-full_CurrentBorrowingsAndCurrentPortionOfNoncurrentBorrowings",
                 "ifrs-full_CurrentLeaseLiabilities"),
        noncurrent=("ifrs-full_LongtermBorrowings", "ifrs-full_NoncurrentLeaseLiabilities"),
    )
    result = resolve_gross_debt(mixed, values(**{
        "ifrs-full_CurrentBorrowingsAndCurrentPortionOfNoncurrentBorrowings": 10.0,
        "ifrs-full_LongtermBorrowings": 90.0,
        "ifrs-full_Borrowings": 100.0,          # the undivided total, also filed
        "ifrs-full_CurrentLeaseLiabilities": 1.0,
        "ifrs-full_NoncurrentLeaseLiabilities": 2.0,
    }))
    assert result.gross_debt == 100.0           # 10 + 90, not 200


# --- Guard against the guard being removed -----------------------------


def test_every_withholding_says_why() -> None:
    """A silent withholding is almost as bad as a wrong number: the Case has
    to be able to tell the investor which evidence is missing, not merely
    that something is."""
    cases = [
        (taxonomy(current=("ifrs-full_OtherCurrentFinancialLiabilities",),
                  noncurrent=("ifrs-full_OtherNoncurrentFinancialLiabilities",)), values()),
        (taxonomy(current=("ifrs-full_CurrentPortionOfLongtermBorrowings",),
                  noncurrent=("ifrs-full_LongtermBorrowings",)),
         values(**{"ifrs-full_CurrentPortionOfLongtermBorrowings": 1.0,
                   "ifrs-full_LongtermBorrowings": 2.0})),
        (EsefTaxonomy(), values()),
    ]
    for tax, value_of in cases:
        result = resolve_gross_debt(tax, value_of)
        assert not result.resolved
        assert result.reason and len(result.reason) > 20
