"""Since You Were Here -- Minimal State & Truthful Change Window.

The one new concept this sprint introduces: `last_viewed_at`, the
moment a user last successfully loaded the Daily Brief. Nothing else.
No snapshot of that visit's agenda, no counters, no duplicated event
history -- the timestamp exists only to define a comparison window
("since you were here" = any real per-item `since` timestamp on the
already-existing Daily Brief agenda that is newer than this one
value), computed fresh, client-side, against data this package never
touches.

This package owns exactly one table (`daily_brief_view_state`, one row
per `user_id`) and exposes exactly two operations: read the current
value, and set it to now. It reads no Case, no Decision, no Monitoring
result, no Business Fact -- it has no opinion about what "meaningful"
means; that judgment is entirely the existing Daily Brief agenda's own,
unmodified.
"""
