# Atlas Shared Packages

Canonical shared entities live in `atlas.shared`.

This top-level directory marks the shared package boundary for future generated
schemas, SDKs, or frontend-safe model projections. Runtime Python code should
continue importing from `atlas.shared`.

