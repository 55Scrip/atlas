import { Link } from "react-router-dom";

/**
 * Placeholder for the application navigation region.
 *
 * Structural placeholder — the Dashboard (Sprint 1, Commit 6) is so far
 * the only product surface that exists, so it is the only link. Uses
 * react-router-dom's own Link (client-side routing), not the Foundation
 * Link component (a plain anchor, with no router integration) — this is
 * shell wiring, not Dashboard page content.
 */
export function Navigation() {
  return (
    <nav aria-label="Primary">
      <Link to="/dashboard">Dashboard</Link>
    </nav>
  );
}
