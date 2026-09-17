"""European filing evidence, taken from the filings themselves.

Atlas's European holdings had no fundamentals because no connected source
reached their venues. The source that does is the one the issuers are already
required to publish: ESEF, the EU's machine-readable annual report format.
It is public, free, permanent, carries a real publication date, and belongs to
nobody -- which is what a durable evidence store needs and what a commercial
feed, whose data must be deleted when a contract ends, cannot offer.

The cost is that ESEF is a filing, not a product. Issuers tag the primary
statements with IFRS concepts where one fits and with their own extension
concepts where one does not, and the tagging differs company by company. The
whole of this package is about reading that safely:

* `source` finds and retrieves filings and their taxonomy packages.
* `taxonomy` reads the calculation roll-ups and the ESMA anchoring relations
  that say what an extension concept means.
* `normalization` turns tagged facts into the fields Atlas's evaluators read,
  using standard concepts first and anchoring second -- never a label guess.
* `debt` is separate because gross debt is where a plausible wrong answer is
  easiest to produce and most damaging. See its own docstring.

Nothing here decides anything. It produces evidence; Atlas's analysis remains
the only thing that draws conclusions from it.
"""
from atlas.business_data_providers.esef.debt import DebtResolution, resolve_gross_debt
from atlas.business_data_providers.esef.normalization import NormalizedPeriod, normalize_filing
from atlas.business_data_providers.esef.source import (
    EsefFiling,
    EsefSourceError,
    annual_filings,
    fetch_facts,
    fetch_package,
    lei_for_isin,
)
from atlas.business_data_providers.esef.taxonomy import EsefTaxonomy, read_taxonomy

__all__ = [
    "DebtResolution",
    "EsefFiling",
    "EsefSourceError",
    "EsefTaxonomy",
    "annual_filings",
    "fetch_facts",
    "fetch_package",
    "lei_for_isin",
    "NormalizedPeriod",
    "normalize_filing",
    "read_taxonomy",
    "resolve_gross_debt",
]
