import { Link } from "react-router-dom";
import { useTranslation } from "../i18n";
import styles from "./Navigation.module.css";

/**
 * Application navigation region.
 *
 * Alpha Sprint 1A: added the Portfolio link alongside Dashboard, now
 * that Portfolio is a real product surface. Sprint 4: added History
 * alongside it. Visual Polish Sprint 1: styling only (Navigation.module.css)
 * — same links, same routes, same order. Uses react-router-dom's own Link
 * (client-side routing), not the Foundation Link component (a plain
 * anchor, with no router integration) — this is shell wiring, not page
 * content.
 */
export function Navigation() {
  const { t } = useTranslation();

  return (
    <nav aria-label={t("shell.nav.ariaLabel")} className={styles.nav}>
      <Link to="/daily-brief" className={styles.link}>
        {t("shell.nav.dailyBrief")}
      </Link>
      <Link to="/discovery" className={styles.link}>
        {t("shell.nav.discovery")}
      </Link>
      <Link to="/dashboard" className={styles.link}>
        {t("shell.nav.dashboard")}
      </Link>
      <Link to="/portfolio" className={styles.link}>
        {t("shell.nav.portfolio")}
      </Link>
      <Link to="/history" className={styles.link}>
        {t("shell.nav.history")}
      </Link>
    </nav>
  );
}
