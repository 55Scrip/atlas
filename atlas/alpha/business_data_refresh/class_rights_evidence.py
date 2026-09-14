"""The write-side bridge for class economic-rights evidence: the one place
the SEC class-rights adapter is constructed, and where a parsed filing
becomes Atlas's persisted observations. (`atlas.business_data_providers`
has exactly one importer package.)

A filing is refused -- recorded as nothing -- when its instance does not
say it is the filing it was located as: another filer's CIK, a document
type other than the recorded form, or an amendment.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime

from atlas.alpha.class_rights_evidence.models import (
    ClassRightsFiling,
    ClassRightsObservation,
    EvidenceStrength,
    RightKind,
)
from atlas.business_data_providers.sec_edgar_class_rights import (
    RIGHTS_PARSER_VERSION,
    SecEdgarClassRightsProvider,
    parse_class_rights,
)

__all__ = ["RIGHTS_PARSER_VERSION", "RightsFilingRefused", "RightsFilingSource", "get_default_class_rights_provider",
           "rights_evidence_from_instance"]


def get_default_class_rights_provider() -> SecEdgarClassRightsProvider:
    return SecEdgarClassRightsProvider()


class RightsFilingRefused(Exception):
    """The instance is not the filing it was located as."""


@dataclass(frozen=True)
class RightsFilingSource:
    """Which filing an instance was fetched as -- from Atlas's own share
    evidence (issuer CIK, accession, form, filing date, instance URL)."""

    issuer_cik: str
    accession: str
    form: str
    filing_date: date
    instance_url: str


def rights_evidence_from_instance(
    source: RightsFilingSource, instance_xml: str, *, retrieved_at: datetime, recorded_at: datetime,
) -> tuple[ClassRightsFiling, tuple[ClassRightsObservation, ...]]:
    parsed = parse_class_rights(instance_xml)
    if parsed.entity_cik is None or int(parsed.entity_cik) != int(source.issuer_cik):
        raise RightsFilingRefused(f"{source.accession}: instance names CIK {parsed.entity_cik}, fetched as {source.issuer_cik}")
    if parsed.document_type != source.form:
        raise RightsFilingRefused(f"{source.accession}: document type {parsed.document_type}, located as {source.form}")
    if parsed.amendment:
        raise RightsFilingRefused(f"{source.accession}: an amendment")
    observations = tuple(
        ClassRightsObservation(
            issuer_cik=source.issuer_cik, accession=source.accession, form=source.form, filing_date=source.filing_date,
            observation_key=f.key, kind=RightKind(f.kind.value), strength=EvidenceStrength(f.strength.value),
            subject_member=f.subject_member, subject_label=f.subject_label, target_member=f.target_member,
            target_label=f.target_label, related_members=f.related_members, related_labels=f.related_labels,
            value=f.value, value_low=f.value_low, value_high=f.value_high, unit=f.unit, decimals=f.decimals,
            equity_kind=f.equity_kind, effective_from=f.effective_from, effective_to=f.effective_to,
            concept=f.concept, context_id=f.context_id, excerpt=f.excerpt, parser_version=RIGHTS_PARSER_VERSION,
            retrieved_at=retrieved_at, recorded_at=recorded_at,
        )
        for f in parsed.facts
    )
    filing = ClassRightsFiling(
        issuer_cik=source.issuer_cik, accession=source.accession, form=source.form, filing_date=source.filing_date,
        document_period_end=parsed.document_period_end, presented_from=parsed.presented_from,
        instance_url=source.instance_url, observations=len(observations), parser_version=RIGHTS_PARSER_VERSION,
        retrieved_at=retrieved_at, recorded_at=recorded_at,
    )
    return filing, observations
