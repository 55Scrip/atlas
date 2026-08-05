import { Link } from "react-router-dom";

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
  return (
    <nav aria-label="Primary">
      <Link to="/dashboard">Dashboard</Link> <Link to="/portfolio">Portfolio</Link>
    </nav>
  );
}
