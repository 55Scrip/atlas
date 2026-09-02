"""Cross-venue issuer linking: proving that two distinct securities
belong to one issuer (Cross-Venue Issuer Linking sprint).

**Same issuer does not mean same security.** A confirmed link says only
"these instruments ultimately represent the same underlying company." It
never says they are economically interchangeable, and it never licenses
substituting one's price, currency or share class for the other's. That
distinction is why `IssuerLinkOutcome` describes *issuer-equivalence
confidence* and deliberately carries no notion of substitutability.

**The evidence Atlas actually has.** An availability audit found that the
SEC provider already stamps `sec_cik` into every fundamentals document's
metadata -- 1,571 stored records across 32 companies at the time of
writing -- and that nothing had ever read it. A CIK identifies a *filer*,
a legal reporting entity, which is exactly issuer identity. So the
`PROVEN` tier is reachable today, on data already ingested, without a new
provider or a single additional API call.

The live corpus contains exactly one provable cross-venue pair:
`GOOG` and `GOOGL` both resolve to CIK `0001652044` (Alphabet Inc).
They are two genuinely different securities -- Class C and Class A, with
different voting rights -- owned by one issuer. That pair is the worked
example this module is built against, precisely because its evidence is
real rather than hypothetical.

**What deliberately stays unreachable.** `VOLV-B`/`VOLVF`,
`TSMC`/`TSM` and Novo Nordisk's Copenhagen line all lack a shared
authoritative identifier: SEC knows the US-listed side and has never
heard of the native line. Those pairs evaluate to `INSUFFICIENT_EVIDENCE`
here, and that is the correct answer rather than a gap to be closed with
cleverness. A false issuer link contaminates financial statements,
business quality, valuation, recommendation, monitoring and historical
memory at once -- substantially worse than Unknown.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

__all__ = [
    "EvidenceStrength",
    "IssuerLinkOutcome",
    "IssuerLinkEvidence",
    "IssuerLinkAssessment",
    "EVIDENCE_KIND_STRENGTH",
    "evaluate_issuer_link",
    "cik_agreement_evidence",
    "legal_name_evidence",
    "provider_search_evidence",
]


class EvidenceStrength(str, Enum):
    """A closed hierarchy. Deliberately ordinal *names* rather than
    numbers: a numeric score invites a threshold, and a threshold is
    exactly how `Volvo AB` and `Volvo Car AB` -- returned by Alpha
    Vantage tied at match score 0.8000 -- end up merged."""

    #: An authoritative identifier for the same legal entity, or an
    #: official ADR-underlying mapping. Sufficient alone.
    PROVEN = "proven"
    #: An authoritative-but-indirect signal: an official provider issuer
    #: relationship, or a second identifier corroborating a first.
    #: Sufficient only in agreeing pairs.
    STRONG = "strong"
    #: Plausible and consistent, but not identifying: same legal name
    #: *and* same jurisdiction *and* compatible security metadata.
    #: Never sufficient alone -- it can only raise a question.
    SUPPORTING = "supporting"
    #: Resemblance. Fuzzy names, similar tickers, shared sector, provider
    #: match scores. Never contributes to a link at all.
    WEAK = "weak"
    #: Positive disagreement on something identifying. Outranks
    #: everything else, however much agreement accompanies it.
    CONTRADICTORY = "contradictory"


class IssuerLinkOutcome(str, Enum):
    """What Atlas concluded about one proposed pair."""

    #: Proven. The link may be made without asking anyone.
    AUTO_CONFIRMED = "auto_confirmed"
    #: Plausible but unproven. A human may confirm; Atlas may not decide.
    AMBIGUOUS = "ambiguous"
    #: Evidence exists and is all too weak to act on.
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"
    #: Atlas positively knows the candidate is wrong.
    CONTRADICTORY = "contradictory"
    #: Nothing to evaluate -- no candidate evidence at all.
    NO_MATCH = "no_match"
    #: No configured source could ever express this pair's identity.
    UNSUPPORTED = "unsupported"


#: The one place an evidence kind's strength is decided. A kind absent
#: from this table is treated as `WEAK`, so a new signal is powerless
#: until someone deliberately classifies it -- the safe default.
EVIDENCE_KIND_STRENGTH: dict[str, EvidenceStrength] = {
    # Authoritative regulatory identity.
    "SEC_CIK": EvidenceStrength.PROVEN,
    "LEI": EvidenceStrength.PROVEN,
    "EXPLICIT_ADR_UNDERLYING_MAPPING": EvidenceStrength.PROVEN,
    # A person who knows what they own. Establishes issuer relation only
    # -- never that the two securities are interchangeable.
    "USER_CONFIRMATION": EvidenceStrength.PROVEN,
    # Authoritative but indirect.
    "OFFICIAL_PROVIDER_ISSUER_ID": EvidenceStrength.STRONG,
    "ISIN_ISSUER_PREFIX": EvidenceStrength.STRONG,
    # Consistent, not identifying.
    "LEGAL_NAME_AND_JURISDICTION": EvidenceStrength.SUPPORTING,
    # Resemblance only.
    "COMPANY_NAME_SIMILARITY": EvidenceStrength.WEAK,
    "COMPANY_NAME_EXACT_MATCH": EvidenceStrength.WEAK,
    "TICKER_SIMILARITY": EvidenceStrength.WEAK,
    "SECTOR_MATCH": EvidenceStrength.WEAK,
    "PROVIDER_MATCH_SCORE": EvidenceStrength.WEAK,
}


@dataclass(frozen=True)
class IssuerLinkEvidence:
    """One observation about a proposed pair. `agrees=False` on an
    identifying kind is what produces `CONTRADICTORY`; `agrees=None`
    means the observation could not be made (one side had no value),
    which is silence rather than disagreement."""

    kind: str
    agrees: bool | None
    left_value: str | None = None
    right_value: str | None = None
    source: str = ""

    @property
    def strength(self) -> EvidenceStrength:
        if self.agrees is False and self.kind in _IDENTIFYING_KINDS:
            return EvidenceStrength.CONTRADICTORY
        return EVIDENCE_KIND_STRENGTH.get(self.kind, EvidenceStrength.WEAK)


#: Kinds whose *disagreement* is meaningful. Two different CIKs are two
#: different filers, full stop. Two different fuzzy names are not
#: evidence of anything -- `AB Volvo` and `Volvo AB` disagree textually
#: and are one company -- so a name mismatch must never be promoted to a
#: contradiction.
_IDENTIFYING_KINDS = frozenset(
    {"SEC_CIK", "LEI", "OFFICIAL_PROVIDER_ISSUER_ID", "EXPLICIT_ADR_UNDERLYING_MAPPING"}
)


@dataclass(frozen=True)
class IssuerLinkAssessment:
    """The decision plus the reasoning that produced it. Every automatic
    link must be explainable as "these securities belong to the same
    issuer because of this authoritative evidence" -- never "they look
    similar" -- so the evidence travels with the outcome."""

    outcome: IssuerLinkOutcome
    reason: str
    evidence: tuple[IssuerLinkEvidence, ...] = field(default_factory=tuple)

    @property
    def may_link(self) -> bool:
        return self.outcome is IssuerLinkOutcome.AUTO_CONFIRMED

    @property
    def needs_human(self) -> bool:
        return self.outcome is IssuerLinkOutcome.AMBIGUOUS

    def agreeing(self, strength: EvidenceStrength) -> tuple[IssuerLinkEvidence, ...]:
        return tuple(e for e in self.evidence if e.agrees is True and e.strength is strength)


def evaluate_issuer_link(evidence: tuple[IssuerLinkEvidence, ...]) -> IssuerLinkAssessment:
    """Pure and deterministic. Rules are checked in strict order, and
    the order itself encodes the sprint's governing preference: a
    contradiction is consulted before any amount of agreement, because
    wrong-company data is worse than missing data.

    Note that no quantity of `WEAK` evidence changes the outcome. That
    is the whole point -- accumulating resemblance is precisely how the
    `VOLVF`/`VLVOF` tie would have become a merge.
    """
    contradictions = tuple(e for e in evidence if e.strength is EvidenceStrength.CONTRADICTORY)
    if contradictions:
        names = ", ".join(sorted({e.kind for e in contradictions}))
        return IssuerLinkAssessment(
            outcome=IssuerLinkOutcome.CONTRADICTORY,
            reason=(
                f"An identifying signal positively disagrees ({names}). These are different "
                "legal entities; no amount of other agreement can outweigh this."
            ),
            evidence=evidence,
        )

    if not evidence:
        return IssuerLinkAssessment(
            outcome=IssuerLinkOutcome.NO_MATCH,
            reason="No candidate evidence was produced for this pair.",
            evidence=evidence,
        )

    agreeing = tuple(e for e in evidence if e.agrees is True)
    proven = tuple(e for e in agreeing if e.strength is EvidenceStrength.PROVEN)
    strong = tuple(e for e in agreeing if e.strength is EvidenceStrength.STRONG)
    supporting = tuple(e for e in agreeing if e.strength is EvidenceStrength.SUPPORTING)

    if proven:
        kinds = ", ".join(sorted({e.kind for e in proven}))
        return IssuerLinkAssessment(
            outcome=IssuerLinkOutcome.AUTO_CONFIRMED,
            reason=f"Both securities share the same authoritative issuer identity ({kinds}).",
            evidence=evidence,
        )

    if len({e.kind for e in strong}) >= 2:
        kinds = ", ".join(sorted({e.kind for e in strong}))
        return IssuerLinkAssessment(
            outcome=IssuerLinkOutcome.AUTO_CONFIRMED,
            reason=f"Two independent authoritative signals agree ({kinds}).",
            evidence=evidence,
        )

    if strong or supporting:
        return IssuerLinkAssessment(
            outcome=IssuerLinkOutcome.AMBIGUOUS,
            reason=(
                "The available evidence is consistent with these being one company but does not "
                "identify them as one. A person must confirm before Atlas links them."
            ),
            evidence=evidence,
        )

    return IssuerLinkAssessment(
        outcome=IssuerLinkOutcome.INSUFFICIENT_EVIDENCE,
        reason=(
            "Only resemblance is available -- names, tickers, sector or a provider match score. "
            "Resemblance never establishes that two securities are the same company."
        ),
        evidence=evidence,
    )


def cik_agreement_evidence(left_cik: str | None, right_cik: str | None) -> IssuerLinkEvidence:
    """The one `PROVEN` signal Atlas can build from data it already has.

    A CIK is assigned by the SEC to a *filer* -- a legal reporting
    entity -- so two securities reporting under one CIK are two
    instruments of one issuer. `GOOG` and `GOOGL` both carry
    `0001652044` in already-stored records.

    Zero-padded before comparison because SEC returns the same filer as
    both `0000320193` and `320193` depending on the endpoint; comparing
    those as strings would manufacture a contradiction out of
    formatting."""
    normalized_left = _normalize_cik(left_cik)
    normalized_right = _normalize_cik(right_cik)
    agrees = (
        None
        if normalized_left is None or normalized_right is None
        else normalized_left == normalized_right
    )
    return IssuerLinkEvidence(
        kind="SEC_CIK",
        agrees=agrees,
        left_value=normalized_left,
        right_value=normalized_right,
        source="sec_edgar",
    )


def _normalize_cik(value: str | None) -> str | None:
    if value is None:
        return None
    digits = value.strip().lstrip("0")
    return digits.zfill(10) if digits else None


def legal_name_evidence(
    left_name: str | None, right_name: str | None, *, same_jurisdiction: bool
) -> IssuerLinkEvidence:
    """`SUPPORTING` at best, and only when the jurisdiction also matches
    -- and even then it can raise a question, never settle one.

    Classified this way because name comparison was measured failing in
    both directions at once: too strict to see `AB Volvo` as `Volvo AB`,
    too weak to keep `Volvo AB` apart from `Volvo Car AB` if loosened.
    Note it is never `CONTRADICTORY`: a name mismatch is not evidence of
    difference, for the same reason."""
    if left_name is None or right_name is None:
        agrees: bool | None = None
    else:
        agrees = left_name.strip().casefold() == right_name.strip().casefold()
    kind = "LEGAL_NAME_AND_JURISDICTION" if same_jurisdiction else "COMPANY_NAME_EXACT_MATCH"
    return IssuerLinkEvidence(
        kind=kind, agrees=agrees, left_value=left_name, right_value=right_name, source="provider"
    )


def provider_search_evidence(match_score: str | float | None) -> IssuerLinkEvidence:
    """Provider symbol search is **discovery, not proof**. Alpha
    Vantage's `SYMBOL_SEARCH` for "Volvo" returned `VOLVF` (Volvo AB)
    and `VLVOF` (Volvo Car AB) tied at 0.8000 -- two different companies
    at identical confidence -- so a search result may propose a
    candidate and may never establish one. Always `WEAK`, whatever the
    score."""
    return IssuerLinkEvidence(
        kind="PROVIDER_MATCH_SCORE",
        agrees=True if match_score is not None else None,
        left_value=None,
        right_value=str(match_score) if match_score is not None else None,
        source="provider_symbol_search",
    )
