"""Proves ATLAS-022's Phase 10 claim: adding a second, differently-shaped
data source requires zero changes to validation, normalization,
versioning, or Business Analysis -- only a new `BusinessDataProvider`
implementation.

`AlternateProvider` below is deliberately built differently from
`StaticBusinessDataProvider` (computed on the fly from a template
rather than an in-memory tuple, standing in for "a provider backed by a
real, different transport") to prove the pipeline does not secretly
depend on anything about *how* a provider is implemented -- only that
it returns `RawBusinessDocument` tuples.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from atlas.analysis_engine.business import evaluate_business_analysis
from atlas.analysis_engine.business_data.models import RawBusinessDocument
from atlas.analysis_engine.business_data.pipeline import IngestedRecord, ingest
from atlas.analysis_engine.business_data.providers import BusinessDataProvider
from tests.unit.analysis_engine._fixtures import run_minimal
from tests.unit.analysis_engine.business_data._fixtures import EVALUATED_AT


@dataclass(frozen=True)
class AlternateProvider:
    """A second, independently-built `BusinessDataProvider` -- computes
    its one document from a template at call time rather than storing
    a tuple, simulating a provider backed by a real transport this
    sprint does not build. Structurally unrelated to
    `StaticBusinessDataProvider` beyond implementing the same one
    method."""

    template_identifier: str

    def fetch(self, *, company_identifier: str, evaluated_at: datetime) -> tuple[RawBusinessDocument, ...]:
        return (
            RawBusinessDocument(
                identifier=f"{self.template_identifier}-{company_identifier}",
                company=company_identifier,
                source_kind="press_release",
                published_at=evaluated_at,
                provider_id="alternate_provider",
                raw_reference=f"alt://{company_identifier}",
                content_hash="alt-hash",
                language="en",
            ),
        )


class TestASecondProviderRequiresNoDownstreamChanges:
    def test_alternate_provider_conforms_to_the_same_protocol(self):
        provider = AlternateProvider(template_identifier="release")
        assert isinstance(provider, BusinessDataProvider)

    def test_alternate_provider_output_flows_through_the_identical_pipeline(self):
        provider = AlternateProvider(template_identifier="release")
        documents = provider.fetch(company_identifier="ASML", evaluated_at=EVALUATED_AT)
        result = ingest(documents[0], evaluated_at=EVALUATED_AT)
        assert isinstance(result, IngestedRecord)
        assert result.record.company == "ASML"

    def test_alternate_provider_output_flows_into_business_analysis_unchanged(self):
        """The whole point: neither `evaluate_business_analysis`'s
        signature nor `BusinessAnalysisResult`'s shape needed to change
        to accept a record from a wholly different provider
        implementation."""
        provider = AlternateProvider(template_identifier="release")
        documents = provider.fetch(company_identifier="ASML", evaluated_at=EVALUATED_AT)
        ingested = ingest(documents[0], evaluated_at=EVALUATED_AT)
        assert isinstance(ingested, IngestedRecord)

        _, decision_output = run_minimal()
        result = evaluate_business_analysis(
            decision_output.business_evaluation,
            business_records=(ingested.record,),
            evaluated_at=EVALUATED_AT,
        )
        assert result.available_business_records == (ingested.record.id,)
