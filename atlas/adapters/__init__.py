"""Adapters bridge legacy runtime data shapes to Blueprint-aligned domains.

Adapters are the only layer allowed to import both legacy modules and
`atlas.domains`/`atlas.shared`. They must stay deterministic, must not call
external APIs, and must not mutate persisted data.
"""
