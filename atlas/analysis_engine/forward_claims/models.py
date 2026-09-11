"""The canonical `ForwardClaim` model (Forward-Looking Evidence,
Stage 1).

**A `ForwardClaim` is not a `BusinessFact`, and must never become one.**
`BusinessFact` is a realized, structured observation -- what a company
*did*, extracted by exact key lookup from a filed statement, and
consumed directly by Growth's CAGR, Capital Allocation, FCF Yield and
Financial Risk. A `ForwardClaim` is what a company *said it expects*.
The two look almost identical in a database row and mean opposite
things to arithmetic:

    BusinessFact(kind=REVENUE, value=10e9, period="2027")
    ForwardClaim(subject=REVENUE, value_low=10e9, horizon_period="2027")

The first, fed to a growth calculation, is a realized data point. The
second is management's hope, and averaging it into a historical CAGR
would let a company raise Atlas's opinion of its own past simply by
being optimistic about its future. That is why this type is separate,
lives in its own package, shares no base class, and is imported by
nothing in the analysis or decision path -- a boundary
`tests/unit/analysis_engine/forward_claims/test_integration_safety.py`
enforces rather than trusts.

**A claim is the company's own current guidance for a company-level
measure** (Stage 1.2). Not any forward-looking number: a figure the
company *cites* -- its previously communicated guidance, a comparison
baseline -- is not guidance it is issuing, and a figure for part of the
company -- a segment, an acquired business, "these assets" -- is not
the measure `subject` names. Both can be perfectly grounded in one
clause and still be the wrong claim, and Stage 2.1 would compare either
one against the company's real guidance as if management had revised
it.

**Every claim carries the exact sentence it came from.** `source_text`
is the verbatim passage, never a paraphrase and never generated prose.
A claim whose passage cannot be located in its own source record is a
claim Atlas cannot defend, so extraction produces none.

**Time is two separate questions.** `reported_at` is when Atlas could
first have known the statement; `horizon_period` is the future period
the statement is about. Conflating them is precisely the failure this
package exists to prevent: FY2027 guidance issued in 2026 is evidence
available in 2026, and nothing here ever dates a claim from its
horizon.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from atlas.analysis_engine.business_data.sources import SourceKind
from atlas.analysis_engine.forward_claims.contracts import (
    ClaimBound,
    ClaimSubject,
    ClaimType,
    ClaimantRole,
    HorizonKind,
)

__all__ = ["ForwardClaim"]


@dataclass(frozen=True)
class ForwardClaim:
    """One forward-looking statement, grounded in one source record.

    `id` is deterministic --
    `f"{source_record_id}:{subject.value}:{horizon_kind.value}:{horizon_period}"`
    -- so the same corpus and the same rules always produce the same
    claims, and the same statement never yields two. The horizon kind is
    part of it (Stage 2.1) so a fiscal-year and a calendar-year claim
    from one sentence can never collapse into one identity.
    """

    id: str
    company: str

    claim_type: ClaimType
    subject: ClaimSubject
    """What the claim is about. Never the same axis as `claim_type`:
    "guidance about adjusted EBITDA", not "an EBITDA claim"."""

    bound: ClaimBound
    value_low: float
    value_high: float
    """`value_low == value_high` for a POINT. A LOWER_BOUND repeats its
    only stated number in both fields rather than inventing a ceiling;
    `bound` is the field that says which reading is correct, and a
    consumer that ignores it is misreading the claim by construction."""
    unit: str
    """Verbatim from the sentence's own scale word, normalized only in
    case (e.g. `"USD_BILLION"`). Never converted between scales."""
    value_text: str
    """The number exactly as management said it -- "$6.8 billion-$7.6
    billion". `value_low`/`value_high` are convenience; this is the
    evidence, and it is what a reviewer checks."""

    horizon_period: str
    """The future period the claim is about, as an explicit calendar
    year ("2027"). Relative horizons ("next year") are rejected during
    extraction rather than resolved: resolving one requires assuming a
    fiscal calendar the transcript metadata does not state."""
    horizon_kind: HorizonKind
    """Whether `horizon_period` is a fiscal year, a calendar year, or a
    year the speaker did not qualify. Read from the sentence's own
    wording, never inferred from the company."""
    horizon_text: str
    """The horizon exactly as stated -- "full year 2027"."""

    claimant_role: ClaimantRole
    stated_by: str
    """The speaker's own name, verbatim from the transcript record."""
    stated_by_title: str
    """The speaker's title, verbatim -- the field `claimant_role` was
    classified from, kept so a reviewer can check that classification
    rather than trust it."""

    source_record_id: str
    source_kind: SourceKind
    source_text: str
    """The verbatim sentence. Must be a substring of the source record's
    own content; extraction asserts this before constructing a claim."""

    reported_at: datetime
    """When Atlas could first have known this. Inherited from the source
    record's `published_at`, never derived from `horizon_period`."""
    extracted_at: datetime
    extractor_version: str
    """Which rule set produced this claim. Deterministic rules will
    change, and a claim from an older rule set must remain
    distinguishable from a newer one without re-reading the source."""
