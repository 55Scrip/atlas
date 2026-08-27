"""Development-only tooling for the Atlas Alpha app.

Everything under this package is invoked deliberately, by an operator,
via `python -m atlas.dev.<module>` -- never wired into application
startup, a FastAPI route, or any other automatic trigger (the same
"explicit maintenance entry point" convention `atlas/alpha/portfolio
/cli.py` already established). Every command here refuses to run
unless `ATLAS_ENV` is unset or `"development"` -- see `atlas.dev.guard`.
"""
