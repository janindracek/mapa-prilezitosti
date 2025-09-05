import React from "react";
import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import ProductBarChart from "../../components/ProductBarChart.jsx";

describe("ProductBarChart (placeholder)", () => {
  it("renders counts and visible bars", () => {
    const data = [
      { id: "p1", name: "Engines", value: 30 },
      { id: "p2", name: "Batteries", value: 18 },
      { id: "p3", name: "Sensors", value: 12 },
    ];
    render(<ProductBarChart data={data} title="Top exports" />);
    const panel = screen.getByTestId("productbar");
    expect(panel).toBeInTheDocument();
    const text = panel.textContent;
    expect(text).toContain("Items: 3/3");
    expect(text).toContain("max: 30");
    expect(text).toContain("Top exports");
  });
});