import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { LanguageProvider } from "../i18n";
import { SignalNatureBadge } from "./SignalNatureBadge";
import type { SignalNature } from "../status/statusTone";

function renderBadge(nature: SignalNature) {
  return render(
    <LanguageProvider>
      <SignalNatureBadge nature={nature} />
    </LanguageProvider>,
  );
}

describe("SignalNatureBadge", () => {
  it("renders the Swedish label for a change event", () => {
    renderBadge("change_event");
    expect(screen.getByText("Nytt")).toBeInTheDocument();
  });

  it("renders the Swedish label for a persistent condition", () => {
    renderBadge("persistent_condition");
    expect(screen.getByText("Pågående")).toBeInTheDocument();
  });

  it("renders a distinct label for each of the two natures", () => {
    const natures: SignalNature[] = ["change_event", "persistent_condition"];
    const labels = new Set<string>();
    for (const nature of natures) {
      const { unmount, container } = renderBadge(nature);
      labels.add(container.textContent ?? "");
      unmount();
    }
    expect(labels.size).toBe(2);
  });
});
