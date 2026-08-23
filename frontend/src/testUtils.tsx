import type { ReactElement } from "react";
import { render } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { LanguageProvider } from "./i18n";

/** Sprint 13 — every screen reads copy through `useTranslation()`
 * (`LanguageProvider`) and several use `react-router-dom` hooks
 * (`MemoryRouter`); this wraps both once so individual test files
 * don't have to repeat the same two providers.
 *
 * `path` (e.g. `"/decisions/:decisionId/workspace"`) is only needed
 * when `ui` itself calls `useParams()` -- without a matching `<Route>`
 * pattern in the tree, `useParams()` always returns `{}`, even inside
 * a `MemoryRouter`, since params are extracted from route *matching*,
 * not from the current location alone. */
export function renderWithProviders(
  ui: ReactElement,
  { route = "/", path = "*" }: { route?: string; path?: string } = {},
) {
  return render(
    <MemoryRouter initialEntries={[route]}>
      <LanguageProvider>
        <Routes>
          <Route path={path} element={ui} />
        </Routes>
      </LanguageProvider>
    </MemoryRouter>,
  );
}
