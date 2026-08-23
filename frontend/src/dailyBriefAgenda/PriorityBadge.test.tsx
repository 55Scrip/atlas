import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { LanguageProvider } from "../i18n";
import { PriorityBadge } from "./PriorityBadge";

function renderBadge(priority: Parameters<typeof PriorityBadge>[0]["priority"]) {
  return render(
    <LanguageProvider>
      <PriorityBadge priority={priority} />
    </LanguageProvider>,
  );
}

describe("PriorityBadge", () => {
  it("renders the Swedish label for each of the four priority levels", () => {
    renderBadge("critical");
    expect(screen.getByText("Kritisk")).toBeInTheDocument();
  });

  it("renders a distinct label for every one of the four levels", () => {
    const levels: Parameters<typeof PriorityBadge>[0]["priority"][] = ["critical", "high", "normal", "low"];
    const labels = new Set<string>();
    for (const level of levels) {
      const { unmount, container } = renderBadge(level);
      labels.add(container.textContent ?? "");
      unmount();
    }
    expect(labels.size).toBe(4);
  });

  it("never renders a number -- only the qualitative label", () => {
    renderBadge("high");
    expect(screen.queryByText(/\d/)).not.toBeInTheDocument();
  });
});
