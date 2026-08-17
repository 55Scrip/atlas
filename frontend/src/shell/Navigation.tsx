import { NavLink } from "react-router-dom";
import { useTranslation } from "../i18n";
import styles from "./Navigation.module.css";

/**
 * Application navigation region.
 *
 * Alpha Sprint 1A: added the Portfolio link alongside Dashboard, now
 * that Portfolio is a real product surface. Sprint 4: added History
 * alongside it. Visual Polish Sprint 1: styling only (Navigation.module.css)
 * — same links, same routes, same order. Cross-Workspace Consistency
 * Cleanup: switched from plain `Link` to `NavLink` so the current
 * workspace is visually indicated (matches the approved Figma
 * reference, which always shows the active tab in primary text against
 * the rest in tertiary gray) — still react-router-dom's own component,
 * not the Foundation Link, since this is shell wiring, not page content.
 */
function navLinkClassName({ isActive }: { isActive: boolean }): string {
  return isActive ? `${styles.link!} ${styles.active!}` : styles.link!;
}

export function Navigation() {
  const { t } = useTranslation();

  return (
    <nav aria-label={t("shell.nav.ariaLabel")} className={styles.nav}>
      <NavLink to="/daily-brief" className={navLinkClassName}>
        {t("shell.nav.dailyBrief")}
      </NavLink>
      <NavLink to="/discovery" className={navLinkClassName}>
        {t("shell.nav.discovery")}
      </NavLink>
      <NavLink to="/dashboard" className={navLinkClassName}>
        {t("shell.nav.dashboard")}
      </NavLink>
      <NavLink to="/portfolio" className={navLinkClassName}>
        {t("shell.nav.portfolio")}
      </NavLink>
      <NavLink to="/watchlist" className={navLinkClassName}>
        {t("shell.nav.watchlist")}
      </NavLink>
      <NavLink to="/history" className={navLinkClassName}>
        {t("shell.nav.history")}
      </NavLink>
    </nav>
  );
}
