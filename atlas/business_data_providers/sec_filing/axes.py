"""Which US-GAAP/SRT axis means what, decided against real filings.

The companion to `esef/dimensions.py`'s own `_AXIS_CLASS`: the same
`AxisClass` vocabulary, a different taxonomy. Every entry below was put
here because facts carrying that axis were counted in the four
benchmark 10-Ks (GOOGL, VST, MA, AMAT); nothing is classified on the
strength of its name alone.

**Exact QName, never a substring.** `srt:ConsolidationItemsAxis` and
`us-gaap:StatementBusinessSegmentsAxis` both contain segment-adjacent
words and mean opposite things, which is the same trap ESEF sets with
`SegmentConsolidationItemsAxis`. A substring rule gets the single most
important distinction here backwards.

**Everything unlisted is UNKNOWN, and most axes are.** 75 distinct axes
appear across four filings; 9 are classified. The rest -- derivative
instrument, debt instrument, award type, fair-value hierarchy, income
tax authority -- are preserved in full and classified as nothing,
because Atlas has no evidence about what summing them would mean.
"""
from __future__ import annotations

from atlas.business_data_providers.dimensional_evidence import AxisClass

__all__ = ["SEC_AXIS_CLASS", "classify_sec_axis"]

#: Exact axis QName to class. Counts are facts observed in the four
#: benchmark 10-K filings, recorded so a later reader can see the
#: evidence each entry rests on.
SEC_AXIS_CLASS: dict[str, AxisClass] = {
    # 606 facts, all four filings. The US-GAAP analogue of IFRS 8's
    # SegmentsAxis: the reportable parts of the business, as the filer
    # itself named them.
    "us-gaap:StatementBusinessSegmentsAxis": AxisClass.BUSINESS_SEGMENT,
    # 556 facts (AMAT, GOOGL, VST). The direct analogue of ESEF's
    # SegmentConsolidationItemsAxis, and classified the same way for the
    # same reason: its members are OperatingSegmentsMember,
    # CorporateAndReconcilingItemsMember, IntersegmentEliminationMember
    # -- a consolidation vocabulary, not a list of businesses.
    "srt:ConsolidationItemsAxis": AxisClass.CONSOLIDATION_SCOPE,
    "us-gaap:StatementEquityComponentsAxis": AxisClass.EQUITY_COMPONENT,   # 495
    "srt:ProductOrServiceAxis": AxisClass.PRODUCT_OR_SERVICE,              # 298
    "srt:StatementGeographicalAxis": AxisClass.GEOGRAPHY,                  # 84
    "us-gaap:StatementGeographicalAxis": AxisClass.GEOGRAPHY,
    "srt:ConsolidatedEntitiesAxis": AxisClass.LEGAL_ENTITY,                # 115
    "dei:LegalEntityAxis": AxisClass.LEGAL_ENTITY,
    "us-gaap:RestatementAxis": AxisClass.RESTATEMENT_BASIS,
}


def classify_sec_axis(axis_qname: str) -> AxisClass:
    """Exact lookup. An axis this table has never seen is UNKNOWN, which
    is the safe direction: a wrong class invites arithmetic across
    things that do not belong together, an unread one only withholds."""
    return SEC_AXIS_CLASS.get(axis_qname, AxisClass.UNKNOWN)
