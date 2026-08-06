import { Link } from "react-router-dom";
import { useTranslation } from "../i18n";

/**
 * Application navigation region.
 *
 * Alpha Sprint 1A: added the Portfolio link alongside Dashboard, now
 * that Portfolio is a real product surface. Uses react-router-dom's own
 * Link (client-side routing), not the Foundation Link component (a
 * plain anchor, with no router integration) — this is shell wiring, not
 * page content.
 */
export function Navigation() {
  const { t } = useTranslation();

  return (
    <nav aria-label={t("shell.nav.ariaLabel")}>
      <Link to="/dashboard">{t("shell.nav.dashboard")}</Link>{" "}
      <Link to="/portfolio">{t("shell.nav.portfolio")}</Link>
    </nav>
  );
}
