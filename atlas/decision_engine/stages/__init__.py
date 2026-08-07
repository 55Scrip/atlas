"""Decision Engine pipeline stages — one module per stage (Sprint Phase 4).

Every stage function is pure: an explicit typed input in, an explicit
typed result out, deterministic, no network call, no storage access, no
UI logic, no hidden global state, no current-time call. Time is passed
in explicitly wherever a stage needs it.
"""
from __future__ import annotations
