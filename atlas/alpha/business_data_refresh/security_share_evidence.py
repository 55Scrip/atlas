"""The write-side bridge for security-level share-class evidence: the one
place the SEC share-class adapter is constructed, and where its parsed,
provider-shaped filing becomes Atlas's persisted observations.

Lives here because `atlas.business_data_providers` has exactly one
importer package (`tests/test_architecture_boundaries.py`); the operator
command reaches the adapter only through this module.

A filing is refused (recorded as nothing) when its instance does not say it
is the filing it was fetched as: another filer's CIK, a non-annual document
type, or an amendment. Refusal is reported, never guessed around.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime

from atlas.alpha.security_share_evidence.models import (
    SecurityShareCountObservation,
    SecurityShareFiling,
    ShareClassLinkKind,
)
from atlas.business_data_providers.sec_edgar_share_classes import (
    CLASS_AXIS,
    PARSER_VERSION,
    FetchedInstance,
    LinkKind,
    SecEdgarShareClassProvider,
    exchange_mic,
    parse_share_class_filing,
)

__all__ = [
    "PARSER_VERSION",
    "FilingRefused",
    "ShareClassFilingSource",
    "get_default_share_class_provider",
    "evidence_from_instance",
]


def get_default_share_class_provider() -> SecEdgarShareClassProvider:
    return SecEdgarShareClassProvider()


class FilingRefused(Exception):
    """The instance is not the annual filing it was fetched as."""


@dataclass(frozen=True)
class ShareClassFilingSource:
    """Which filing an instance was fetched as -- from Atlas's own stored
    SEC statements (CIK, accession, form, filing date), never from the
    instance being checked."""

    issuer_cik: str
    accession: str
    form: str
    filing_date: date


def _link_kind(kind: LinkKind) -> ShareClassLinkKind:
    return ShareClassLinkKind(kind.value)


def evidence_from_instance(
    source: ShareClassFilingSource,
    fetched: FetchedInstance,
    *,
    recorded_at: datetime,
) -> tuple[SecurityShareFiling, tuple[SecurityShareCountObservation, ...]]:
    parsed = parse_share_class_filing(fetched.instance_xml)
    if parsed.entity_cik is None or int(parsed.entity_cik) != int(source.issuer_cik):
        raise FilingRefused(f"{source.accession}: instance names CIK {parsed.entity_cik}, fetched as {source.issuer_cik}")
    if parsed.document_type not in SecEdgarShareClassProvider.annual_forms or parsed.document_type != source.form:
        raise FilingRefused(f"{source.accession}: document type {parsed.document_type}, stored as {source.form}")
    if parsed.amendment:
        raise FilingRefused(f"{source.accession}: an amendment")
    observations = tuple(
        SecurityShareCountObservation(
            issuer_cik=source.issuer_cik, accession=source.accession, form=source.form,
            filing_date=source.filing_date, fiscal_period=parsed.fiscal_period,
            document_period_end=parsed.document_period_end, period_end=fact.period_end, class_axis=CLASS_AXIS,
            class_member=fact.class_member, shares=fact.shares, conflict=fact.conflict,
            source_concept=fact.source_concept, context_id=fact.context_id, link_kind=_link_kind(fact.link_kind),
            cover_title=fact.cover.title if fact.cover else None,
            cover_symbol=fact.cover.symbol if fact.cover else None,
            cover_exchange=fact.cover.exchange if fact.cover else None,
            cover_mic=exchange_mic(fact.cover.exchange) if fact.cover else None,
            parser_version=PARSER_VERSION, recorded_at=recorded_at,
        )
        for fact in parsed.facts
    )
    kinds = [o.link_kind for o in observations]
    filing = SecurityShareFiling(
        issuer_cik=source.issuer_cik, accession=source.accession, form=source.form,
        filing_date=source.filing_date, fiscal_period=parsed.fiscal_period,
        document_period_end=parsed.document_period_end, instance_url=fetched.instance_url,
        cover_rows=len(parsed.cover_rows),
        dimensioned_cover_rows=sum(1 for r in parsed.cover_rows if r.class_member is not None),
        observations=len(observations),
        proven=kinds.count(ShareClassLinkKind.PROVEN_BY_SHARED_DIMENSION),
        ambiguous=kinds.count(ShareClassLinkKind.AMBIGUOUS),
        no_link=kinds.count(ShareClassLinkKind.NO_LINK),
        conflicts=sum(1 for o in observations if o.conflict),
        parser_version=PARSER_VERSION, processed_at=recorded_at,
    )
    return filing, observations
