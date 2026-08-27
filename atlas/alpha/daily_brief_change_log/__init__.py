"""Daily Brief 2.0 -- the one new durable concept this sprint introduces:
a per-user log of investment-case changes Atlas has already told the
user about, captured once, durably, at the moment each change is first
observed.

Why this package exists (the problem it solves): every "did the
recommendation change" signal in `daily_brief_agenda` (Investment
Decision, Recommendation Conviction, Portfolio Decision, Change
Intelligence, Monitoring) is detected by diffing against a *previous-
computation cache* that is upserted to the *current* value on every
single agenda build -- see e.g. `investment_decision/service.py`'s own
`synthesize_for_case`. That means a real transition is visible for
exactly one `build_agenda()` call; the very next call (a page refresh,
a background prefetch, React StrictMode's own double-invoke) sees
"previous == current" and reports nothing, regardless of whether a
human ever actually saw it rendered. That is not a read-state problem
this package invents -- it is a real, pre-existing fragility this
package exists to fix, by capturing each eligible transition durably
the first time it is observed, independent of the upstream engines'
own transient diffing.

This package owns exactly one table (`daily_brief_change_log`, one row
per (user_id, ticker, reason_code, value, secondary_value) tuple ever
observed) and exposes three operations: record newly-observed eligible
changes (idempotent -- the natural key prevents duplicates), list the
still-live ones for a user, and mark a set of them seen. It reads the
already-built `DailyBriefAgenda` and nothing else; it has no opinion
about how that agenda itself is built, only about which of its already-
real facts are eligible to be remembered as "a change the user should
be told about" (see `eligibility.py`), and for how long a live entry
stays part of "what's new" before it archives out (see `store.py`'s own
`DEFAULT_ARCHIVE_AFTER`).

Eligibility, archival, and the per-entry NEW/SEEN lifecycle are the
whole of Daily Brief 2.0's product behavior; everything else in this
sprint is presentation of what this package already decided.
"""
