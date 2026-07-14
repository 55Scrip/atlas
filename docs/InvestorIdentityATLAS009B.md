# ATLAS-009B — Investor Identity

**Status:** Implemented, pending review.
**Scope:** Establishes exactly one durable Investor Identity per local data store, reused across every conversation and process invocation against that store — correcting `Decision.user_id`, which was previously populated from `ConversationSession.session_id`, a value re-randomized on every process invocation. The prerequisite capability identified by ATLAS-010-P's revised feasibility assessment.
**Depends on:** ATLAS-009B-D's authoritative Investor Identity definition. Does not touch `Decision`, `ReflectionResponse`, authentication, or `ConversationSession`'s own lifecycle.

---

## 1. Purpose

`Decision.user_id: UserId` has existed as a required field since API-001, but its only production population site, `ConversationOrchestrator._handle_decision`, passed `session.session_id` — a fresh random UUID generated on every `ConversationSession()` construction, i.e. every `conversation/cli.py` process invocation. Two separate conversations against the same `ATLAS_HOME` database therefore produced Decisions with two different, unrelated `user_id` values. This increment gives the system a durable, stable answer instead.

## 2. The Defect, and Why It Blocked ATLAS-010

Discovered while investigating ATLAS-010 (Reflection History), whose own domain definition requires retrieval "only by the investor who owns the underlying Reflection Responses, never cross-investor." Scoping naively by the existing `user_id` would not have prevented a cross-investor leak — it would have actively hidden an investor's own prior history from themselves, since their own past conversations would appear to belong to different "investors." The revised ATLAS-010-P feasibility assessment identified this durable-identity gap as the smallest prerequisite capability, deferred to its own increment. This is that increment.

## 3. Investor Identity Domain Model

```python
@dataclass(frozen=True)
class InvestorIdentity:
    user_id: UserId
    established_at: datetime

    @classmethod
    def register(cls, *, clock: Callable[[], datetime] = _utc_now) -> InvestorIdentity:
        return cls(user_id=UserId(uuid.uuid4()), established_at=clock())
```

Reuses the existing `UserId` value object (`atlas/core/domain/decision/value_objects.py`) rather than introducing a parallel identity type — Investor Identity needed a durable *source* for a value type that already existed, not a new one. `InvestorIdentity` carries no separate id of its own; it is resolved, never looked up by key.

## 4. Persistence: One Row, Enforced at the Schema Level

```python
investor_identity_table = Table(
    "investor_identity",
    metadata,
    Column("id", String, primary_key=True),   # always the literal "singleton"
    Column("user_id", String, nullable=False),
    Column("established_at", String, nullable=False),
)
```

The fixed-literal primary key enforces "exactly one Investor Identity per data store" at the database level — a second INSERT raises `IntegrityError`, not just a convention application code must remember. The table lives in the same SQLite file as `decisions`, `reflection_responses`, etc., so copying or moving the `.db` file carries the identity with it automatically, with no path/machine derivation of any kind.

## 5. `InvestorIdentityRepository`: One Method, Not Get/Add

```python
class InvestorIdentityRepository(Protocol):
    def resolve(self, clock: Callable[[], datetime] = ...) -> UserId:
        ...
```

An early draft of this plan proposed a generic `get`/`add` pair with the atomic resolve-and-reconcile logic living in the *application* layer as a bare `Engine`-typed function — rejected on review before implementation: it inverted the domain → application → infrastructure dependency direction (application importing SQLAlchemy table objects), and the generic pair was never actually called independently by the one real production workflow. `resolve()` is the single verb this capability needs: read on the common path, atomically write-and-reconcile on first use.

`SqlAlchemyInvestorIdentityRepository.resolve()` (infrastructure layer) is the **only** place in this increment that touches `decisions_table` directly, bypassing `DecisionRepository`:

```python
def resolve(self, clock: Callable[[], datetime] = _utc_now) -> UserId:
    with self._engine.begin() as connection:
        row = connection.execute(select(...)).mappings().first()
        if row is not None:
            return UserId(uuid.UUID(row["user_id"]))
        identity = InvestorIdentity.register(clock=clock)
        connection.execute(insert(investor_identity_table).values(...))
        connection.execute(update(decisions_table).values(user_id=str(identity.user_id)))
        return identity.user_id
```

This is a deliberate, disclosed exception to "always go through a repository," justified solely by atomicity (§7): composing two independently-transactional repositories here would leave a real crash window between the InvestorIdentity INSERT and the Decision-reconciliation UPDATE. One `engine.begin()` block spanning both statements makes first-use succeed or fail as a single unit. `DecisionRepository`'s own public surface (`add`/`get`/`list_all`) is completely unchanged.

## 6. The Shared, Store-Level Bootstrap Boundary

```python
# atlas/core/application/investor_identity/composition.py
def resolve_investor_identity(engine: Engine) -> UserId:
    create_investor_identity_table(engine)
    create_decision_table(engine)
    return SqlAlchemyInvestorIdentityRepository(engine).resolve()
```

This is the one shared entry point any composition root calls — today's conversation, or a future Reflection History / bootstrap CLI. It guarantees both tables it needs exist first (both idempotent `metadata.create_all` calls), so no caller needs to coordinate table creation. It imports no SQLAlchemy table objects and issues no raw statements itself; those stay entirely in the infrastructure layer. An early draft wired resolution directly into `conversation/composition.py` instead — rejected on review before implementation: it made Investor Identity's bootstrap implicitly dependent on a conversation having run, when the domain chapter treats it as belonging to the data store itself.

`conversation/composition.py` is now one *caller* of this shared function:

```python
def build_conversation_orchestrator(engine: Engine) -> ConversationOrchestrator:
    investor_id = resolve_investor_identity(engine)
    ...
    return ConversationOrchestrator(..., investor_id=investor_id)
```

## 7. Atomicity, Idempotency, and Failure Behavior

- **First-use initialization and legacy Decision reconciliation happen in one transaction.** A crash mid-transaction rolls back entirely — the next call, from any caller, retries the full first-use path from scratch. No partial state (an InvestorIdentity row with unreconciled Decisions) is ever observable.
- **Every existing Decision in the store is reassigned**, unconditionally, to the newly-resolved identity — safe specifically because of the single-investor-per-store invariant: every Decision already in a given store definitionally belongs to that store's one investor, so there is no per-row ambiguity to resolve. Old session-derived `user_id` values were never meaningful identities; there is nothing worth preserving about them.
- **Idempotent by construction.** Once an `InvestorIdentity` row exists, every later `resolve()` call is a pure `SELECT` — it never re-runs the reconciliation `UPDATE`, verified directly by a test that inserts a Decision *after* the first `resolve()` call and confirms a second call leaves it untouched.
- **Concurrent processes against the same store** are disclosed, not solved: the fixed-literal primary key means a losing concurrent INSERT raises `IntegrityError`, allowed to propagate rather than being silently caught — not a supported scenario for this single-investor local CLI.

## 8. `ConversationOrchestrator` and `ConversationSession`

`ConversationOrchestrator.__init__` gains one new required parameter, `investor_id: UserId`, stored as `self._investor_id`. The single line at `orchestrator.py`'s Decision-commit site changes:

```python
# Before
user_id=session.session_id,
# After
user_id=self._investor_id.value,
```

`ConversationSession.session_id` — its field, default factory, and every other use site — is completely untouched. This is a single-line substitution of *which* identity feeds `Decision.user_id`, not a change to session lifecycle. A dedicated test confirms two separate conversations against the same engine still produce two distinct `session_id` values, while their Decisions share one `user_id`.

## 9. Copy/Move and Future Compatibility

Copying or moving the `.db` file carries `investor_identity` with it automatically — nothing is derived from path, machine, or `ATLAS_HOME`. Two stores copied from one another resolve to the same `UserId` with no additional step, and nothing here implies they stay in sync afterward; no synchronization mechanism is built.

**Stated honestly:** the fixed-literal singleton primary key is a schema-level commitment to exactly one Investor Identity per store, matching this increment's current, single-investor-local scope. A future multi-investor system would require evolving this persistence schema itself — not merely substituting a new implementation behind today's `resolve()` signature while keeping the singleton table shape. This increment does not design that evolution; it keeps today's schema small and isolated so a future migration has as little to unwind as possible.

## 10. Folder Structure

```
atlas/core/domain/investor_identity/
    entity.py, repository.py

atlas/core/infrastructure/persistence/investor_identity/
    table.py, sqlalchemy_repository.py

atlas/core/application/investor_identity/
    composition.py

tests/unit/domain/investor_identity/
tests/unit/infrastructure/persistence/investor_identity/
tests/unit/application/investor_identity/
tests/unit/application/conversation/test_investor_identity_integration.py
```

Two disclosed touches to existing files: `conversation/composition.py` (calls the shared resolver, passes result to the orchestrator) and `conversation/orchestrator.py` (accepts `investor_id`, uses it instead of `session.session_id` at the Decision-commit site). No new CLI, no new REST endpoint. `conversation/cli.py`, `decision_coach/`, `reflection_response/`, and every read-only CLI are untouched.

## 11. Test Summary

19 new tests, regression-clean:

- **`test_entity.py`** (4) — `register()` construction, fresh `UserId` per call, clock-sourced `established_at`, immutability.
- **`test_sqlalchemy_repository.py`** (7) — fresh-store initialization (returns a `UserId`, persists exactly one row, leaves no Decisions to reconcile); legacy reconciliation (three Decisions with distinct random `user_id` values all reconciled to one); idempotent fast path (second call returns the same value; a Decision inserted after the first call is never touched by a second call).
- **`test_composition.py`** (5) — store-level boundary (resolves against a bare engine, creates its own required tables, repeated calls idempotent — no `ConversationSession` anywhere in these tests); structural AST-import checks confirming the application layer imports no SQLAlchemy Core constructs, reusing this codebase's `tests/test_config_sprint195.py::_config_imports()` precedent rather than a source-text search.
- **`test_investor_identity_integration.py`** (3) — two separate `build_conversation_orchestrator(engine)` calls (simulating two process invocations) produce Decisions with the same `user_id`; `ConversationSession.session_id` values remain distinct across them; a store with pre-existing legacy session-derived Decisions has all of them, plus the new one, reconciled to one shared value on first post-increment use.
- **Manual verification:** ran `conversation/cli.py`'s `run()` twice against a fresh `ATLAS_HOME`, confirmed identical `user_id` via direct SQLite query; ran it once against a hand-built legacy fixture database (two Decisions with distinct random `user_id` values, mimicking pre-increment data) and confirmed all three Decisions shared one `user_id` afterward.

**Regression:** full repository suite: **7,663 passed, 3 skipped** (7,644 pre-existing + 19 new). Scoped lint: clean. Whole-repo `ruff check .` count unchanged at 1,202.

## 12. Architectural Decisions

1. **`InvestorIdentityRepository` has exactly one method, `resolve()`** — not `get`/`add`. The single operation this capability performs is "resolve, establishing if necessary," not independent verbs a caller could combine into some other control flow.
2. **The atomic transaction lives entirely in the infrastructure layer** (`SqlAlchemyInvestorIdentityRepository.resolve()`), not the application layer — corrected from an earlier draft that put raw `Engine`-typed SQL in `atlas/core/application/investor_identity/`.
3. **A single shared, store-level bootstrap function** (`investor_identity/composition.py::resolve_investor_identity`) — not owned by `conversation/composition.py` — so a future Reflection History or bootstrap CLI can call the identical function against the same engine.
4. **The legacy-reconciliation `UPDATE` has no `WHERE` clause, by design** — safe only because of the preserved single-investor-per-store invariant; every row in a given store already belongs to that store's one investor.
5. **The fixed-literal `"singleton"` primary key** enforces "exactly one Investor Identity per store" at the schema level, not just by application-code discipline.

## 13. Anything That Feels Overengineered

Nothing. The one deliberate deviation (a repository method touching another aggregate's table) is disclosed and narrowly scoped to exactly the atomicity requirement that necessitates it.

## 14. What Can Be Simplified

Nothing further at this stage.

## 15. Genuine Risks / Unresolved Questions

- **A future multi-investor persistence evolution is out of scope and disclosed, not solved** — the singleton schema would need to change, not just the function behind it.
- **Reconciliation is silent** — no CLI output announces that existing Decisions were reassigned. Acceptable as a one-time, behind-the-scenes correctness fix.
- **No retrieval surface for Investor Identity itself** — nothing lets an investor inspect their own resolved `UserId` today.
- **Multi-process concurrency is disclosed, not solved** — acceptable for a single-investor local CLI tool with no concurrent-access design anywhere else in this codebase either.

## 16. Future Backlog

- ATLAS-010 (Reflection History) can now be revisited: `Decision.user_id` is durable, so an owner-scoped read (`list_all_for_owner(user_id: UserId)` or equivalent) is buildable without the ownership gap that previously blocked it.
- A retrieval interface letting an investor inspect their own resolved Investor Identity — not required by this increment.
- Carried forward, unaffected by this increment: the retrieval interface ATLAS-009-D anticipates for Reflection Response, re-evaluating `reasoning_link`'s placement and permanence, a REST API layer for the Core Loop, the shared structured Error Contract, the brittle hard-coded test-count assertion in `README.md`/`tests/test_release_candidate.py`.
