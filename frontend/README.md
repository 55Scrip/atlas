# Atlas Frontend

Sprint 36 established strict TypeScript configuration ahead of any interface,
so a future frontend could be added without changing backend architecture.

Atlas Alpha Build — Sprint 1, Commit 1 (Platform Bootstrap) added the first
runnable frontend: a minimal Vite + React + TypeScript application that
proves the full stack (Browser → Frontend → API → atlas/core → SQLite →
Response → Browser) works end-to-end. It calls the real `atlas/core` Case
API and renders the real response. It implements no product surface —
no Dashboard, no Decision Workspace, no Design System.

## Development

```
npm install
npm run dev
```

The dev server proxies `/api/*` to a backend running at `http://localhost:8000`
(see `vite.config.ts`). Start the backend separately:

```
.venv/bin/python -m uvicorn atlas.core.infrastructure.api.app:app --port 8000
```

