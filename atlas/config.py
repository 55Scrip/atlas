"""Process-wide configuration roots.

Historically this module owned exactly one thing -- `BASE_DIR` and the
database paths derived from it -- and every other setting in the
codebase is read with a plain `os.environ.get(...)` at its point of use
(see `atlas/ai/provider.py`'s own note about that deliberate choice).
That convention is unchanged here: this module does **not** become a
settings framework, and no caller is expected to import a config object.

**Calibration Phase 8 addition: `.env` is now actually read.** The
development deployment kept `ALPHA_VANTAGE_API_KEY` in a `.env` file at
the repository root, but nothing in this codebase ever loaded that file
-- `python-dotenv` is not a dependency, and every key is a bare
`os.environ.get`. The key was therefore invisible to the backend, which
is not a cosmetic gap: `AlphaVantageMarketDataProvider` is the only
implementer of `business_data.providers.CompanyProfileProvider`, so it
is the sole source of identity candidates for
`CanonicalSecurityIdentityGate`. With no key its profile leg raises
`MissingRequiredField`, the gate sees zero candidates and returns
`NO_MATCH`, and `business_data_refresh.service.refresh_company_data`
short-circuits *before* its fundamentals loop -- meaning SEC EDGAR,
which is free, keyless, and the only source of financial statements,
is never called for any company at all.

`load_local_env` is deliberately the smallest thing that closes that
gap:

- **Never overrides an already-set variable.** A real exported
  environment variable (CI, a container, an operator's shell) always
  wins over the file, so this can never silently shadow a deployment's
  own configuration.
- **No new dependency.** A `KEY=VALUE` scan, not a dotenv parser: no
  interpolation, no `export` keyword handling, no multi-line values.
  Anything it does not understand is skipped rather than guessed at.
- **Absent file is normal, not an error.** Most deployments set real
  environment variables and have no `.env` at all.

It runs once, at import of this module, which every backend entry point
already reaches transitively through the database configuration --
`atlas.core.infrastructure.api.app` also imports it explicitly so the
API's own entry point does not depend on that indirection.
"""
from pathlib import Path
import os

BASE_DIR = Path(os.environ.get("ATLAS_HOME", Path.cwd())).resolve()
DATABASE_DIR = BASE_DIR / "database"
DATABASE_PATH = DATABASE_DIR / "atlas.db"

#: The one file `load_local_env` reads. Repository-root `.env`, resolved
#: through `BASE_DIR` so `ATLAS_HOME` keeps working for callers that
#: already rely on it for the database path.
LOCAL_ENV_PATH = BASE_DIR / ".env"


def load_local_env(path: Path | None = None) -> tuple[str, ...]:
    """Populate `os.environ` from a local `.env` file, without ever
    overwriting a variable that is already set.

    Returns the names of the variables this call actually introduced --
    names only, never values, so a caller may log or assert on the
    result without putting a secret in a log line. An absent file
    returns `()`.
    """
    env_path = LOCAL_ENV_PATH if path is None else path
    try:
        raw = env_path.read_text(encoding="utf-8")
    except (FileNotFoundError, NotADirectoryError, IsADirectoryError, PermissionError, UnicodeDecodeError):
        return ()

    applied: list[str] = []
    for line in raw.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        name, _, value = stripped.partition("=")
        name = name.strip()
        if not name or name in os.environ:
            # Already set wins -- see this module's docstring.
            continue
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
            value = value[1:-1]
        os.environ[name] = value
        applied.append(name)
    return tuple(applied)


load_local_env()
