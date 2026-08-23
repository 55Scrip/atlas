import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { LanguageProvider } from "../i18n";
import { FitBadge } from "./FitBadge";

function renderBadge(rating: Parameters<typeof FitBadge>[0]["rating"]) {
  return render(
    <LanguageProvider>
      <FitBadge rating={rating} />
    </LanguageProvider>,
  );
}

describe("FitBadge", () => {
  it("renders the Swedish label for each rating (default language)", () => {
    renderBadge("excellent");
    expect(screen.getByText("Utmärkt passform")).toBeInTheDocument();
  });

  it("renders a distinct label for every one of the six ratings", () => {
    const ratings: Parameters<typeof FitBadge>[0]["rating"][] = [
      "excellent",
      "good",
      "neutral",
      "weak",
      "poor",
      "unavailable",
    ];
    const labels = new Set<string>();
    for (const rating of ratings) {
      const { unmount, container } = renderBadge(rating);
      labels.add(container.textContent ?? "");
      unmount();
    }
    expect(labels.size).toBe(ratings.length);
  });

  it("never renders a number -- only the qualitative label text", () => {
    renderBadge("good");
    expect(screen.queryByText(/\d/)).not.toBeInTheDocument();
  });
});
