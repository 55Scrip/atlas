import { LanguageSelector, useTranslation } from "../i18n";

/**
 * Placeholder for the application header region.
 *
 * This is a structural placeholder only — not an implementation of
 * UX-013A's Workspace Header component (anatomy, states, and behavior are
 * Design System component work, out of scope for the Application Shell).
 * Visual Polish Sprint 1 gives it the shared token treatment (padding,
 * border, brand typography) so it reads consistently with every real
 * page's own Surface cards — a styling pass only, no new structure or
 * behavior.
 *
 * The language selector is real, product-facing UI (per the localization
 * design brief: "a small language selector in the global header,
 * top-right corner"), not a structural placeholder — it lives here ahead
 * of the rest of the Header's own design because the brief calls for it
 * specifically, not because Header's design work is otherwise done.
 */
export function Header() {
  const { t } = useTranslation();

  return (
    <header
      style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        gap: "var(--space-intra-section)",
        padding: "var(--space-intra-section) var(--space-workspace-margin)",
        borderBottom: "var(--width-border-hairline) solid var(--color-border-hairline)",
      }}
    >
      <p
        style={{
          margin: 0,
          fontFamily: "var(--type-family-display)",
          fontSize: "var(--type-size-h4)",
          letterSpacing: "0.04em",
          color: "var(--color-text-secondary)",
        }}
      >
        {t("shell.header.brand")}
      </p>
      <LanguageSelector />
    </header>
  );
}
