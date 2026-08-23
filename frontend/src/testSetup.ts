import "@testing-library/jest-dom/vitest";
import { afterEach } from "vitest";
import { cleanup } from "@testing-library/react";

// `globals: false` in vitest.config.ts (deliberate -- keeps test-only
// globals out of application code's own type space) means
// Testing Library's own auto-cleanup never registers itself; do it
// explicitly so component trees from one test never leak into the next.
afterEach(() => {
  cleanup();
});

// jsdom implements no scroll behavior at all -- `Element.prototype.
// scrollIntoView` is simply absent, which throws in any component (e.g.
// `CompanionPanel`) that calls it on mount/update. A no-op stub is the
// standard jsdom workaround; this is an environment gap, not something
// any individual component or test should work around for itself.
if (typeof Element !== "undefined" && !Element.prototype.scrollIntoView) {
  Element.prototype.scrollIntoView = () => {};
}
