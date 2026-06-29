# Atlas Backend

The backend is the existing Python package under `atlas/`.

It owns deterministic investment reasoning, CLI orchestration, market context,
memory, timeline, and domain services. Future HTTP or worker processes should
import from `atlas/` rather than moving business logic into transport layers.

