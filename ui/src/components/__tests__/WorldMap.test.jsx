import { vi, describe, it, expect } from "vitest";
// Mock the library WorldMap actually uses so ECharts never runs
vi.mock("echarts-for-react", () => ({
  default: ({ option }) => (
    <div data-testid="echart" data-option={JSON.stringify(option)} />
  ),
}));

import React from "react";
import { render, screen } from "@testing-library/react";
import WorldMap from "../../components/WorldMap.jsx";

describe("WorldMap (placeholder)", () => {
  it("renders stats and top items", () => {
    const data = [
      { iso3: "CZE", name: "Czechia", value: 10 },
      { iso3: "DEU", name: "Germany", value: 20 },
      { iso3: "FRA", name: "France", value: 15 },
    ];
    render(<WorldMap data={data} metric="exports" />);
    const panel = screen.getByTestId("worldmap");
    expect(panel).toBeInTheDocument();
    const text = panel.textContent;
    expect(text).toContain("Regions: 3");
    expect(text).toContain("max: 20");
    // ECharts container rendered (mocked)
    expect(screen.getByTestId("echart")).toBeInTheDocument();
  });
});