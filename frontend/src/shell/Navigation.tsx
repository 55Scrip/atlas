import { NavLink } from "react-router-dom";
import { useTranslation } from "../i18n";
import styles from "./Navigation.module.css";

/**
 * Application navigation region.
 *
 * Alpha Sprint 1A: added the Portfolio link. Sprint 4: added History
 * alongside it. Visual Polish Sprint 1: styling only (Navigation.module.css)
 * — same links, same routes, same order. Cross-Workspace Consistency
 * Cleanup: switched from plain `Link` to `NavLink` so the current
 * workspace is visually indicated (matches the approved Figma
 * reference, which always shows the active tab in primary text against
 * the rest in tertiary gray) — still react-router-dom's own component,
 * not the Foundation Link, since this is shell wiring, not page content.
 *
 * Alpha Integration Fix (One Product Pass): the Dashboard tab is
 * removed. The Alpha Product Integration Review found it produced no
 * fact or computation not already owned by Portfolio, Daily Brief, or
 * History -- every section on it was a rollup ending in a link away
 * from Dashboard itself, it was not the app's actual landing page, and
 * no other page linked into it. The five remaining tabs each now match
 * one doctrine question exactly: Daily Brief (what changed), Discovery
 * (what has Atlas found), Portfolio (what I own), Watchlist (what is
 * Atlas monitoring), History (what happened previously).
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
