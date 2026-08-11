import type { ReactNode } from "react";
import { Text } from "../typography/Text";

export type AsyncStatus<T> =
  | { kind: "loading" }
  | { kind: "error"; message?: string }
  | { kind: "loaded"; data: T };

interface AsyncSectionProps<T> {
  status: AsyncStatus<T>;
  loadingLabel: string;
  errorLabel: (message: string | undefined) => string;
  children: (data: T) => ReactNode;
}

/**
 * Workspace Migration (Foundation extraction) — the one loading/error
 * presentation every independently-fetched section on every workspace
 * already implements ad hoc today (Daily Brief, Discovery, Portfolio's
 * four fetches, Investment Case's ~13 fetches). `AsyncSection` renders
 * nothing itself when `loaded` — it hands the real data straight to
 * `children`, so callers keep full control over their own layout; this
 * component owns only the loading/error text, never a spinner graphic
 * or skeleton (no such component exists in this design system, and
 * none should be introduced here — a plain, calm status line matches
 * every existing page's own established pattern).
 *
 * Deliberately three states only (`loading` / `error` / `loaded`),
 * matching the shape the large majority of existing fetches already
 * use. A section's own *empty* state (zero items once loaded) is not
 * modeled here — that is real content the section itself decides how
 * to render, not a generic "nothing here" placeholder this component
 * could speak to honestly on the section's behalf.
 */
export function AsyncSection<T>({ status, loadingLabel, errorLabel, children }: AsyncSectionProps<T>) {
  if (status.kind === "loading") {
    return (
      <Text role="status" aria-live="polite">
        {loadingLabel}
      </Text>
    );
  }
  if (status.kind === "error") {
    return (
      <Text color="tertiary" role="alert">
        {errorLabel(status.message)}
      </Text>
    );
  }
  return <>{children(status.data)}</>;
}
