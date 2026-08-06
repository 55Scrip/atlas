import { LanguageSelector, useTranslation } from "../i18n";

/**
 * Placeholder for the application header region.
 *
 * This is a structural placeholder only — not an implementation of
 * UX-013A's Workspace Header component (anatomy, states, and behavior are
 * Design System component work, out of scope for the Application Shell).
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
    <header>
      <p>{t("shell.header.brand")}</p>
      <LanguageSelector />
    </header>
  );
}
