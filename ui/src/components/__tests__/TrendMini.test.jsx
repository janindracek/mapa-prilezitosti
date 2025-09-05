import React from "react";
import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import TrendMini from "../../components/TrendMini.jsx";

describe("TrendMini (placeholder)", () => {
  it("renders sparkline stats and title", () => {
    const data = [
      { year: 2019, value: 7 },
      { year: 2020, value: 10 },
      { year: 2021, value: 12 },
      { year: 2022, value: 15 },
    ];
    render(<TrendMini data={data} title="Exports trend" />);
    const panel = screen.getByTestId("trendmini");
    expect(panel).toBeInTheDocument();
    const text = panel.textContent;
    expect(text).toContain("Exports trend");
    expect(text).toContain("Points: 4");
    expect(text).toMatch(/min:\s*7/);
    expect(text).toMatch(/max:\s*15/);
  });

  it("handles empty data safely", () => {
    render(<TrendMini data={[]} title="Empty" />);
    const panel = screen.getByTestId("trendmini");
    expect(panel).toBeInTheDocument();
    expect(panel.textContent).toContain("No data");
  });
});