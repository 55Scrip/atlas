"""Zero-Effort Portfolio Onboarding: the one small progress table that
makes the already-existing background enrichment task observable.

Deliberately minimal, per explicit product direction to avoid over-
engineering this: one table, no job queue, no retry policy, no generic
"job" abstraction. `enrich_holdings` (`atlas.alpha.business_data_refresh
.bulk`) updates one row per ticker in place as it works through a batch
the background task it already schedules today runs unchanged; a new
polling endpoint (`GET /enrichment-progress/{batch_id}`) is a plain read
of that table.
"""
