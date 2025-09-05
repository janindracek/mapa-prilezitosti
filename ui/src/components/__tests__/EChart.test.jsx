import React from "react";
import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import EChart from "../../components/EChart.jsx";

describe("EChart wrapper", () => {
  it("renders container and accepts an option", () => {
    const opt = { xAxis: { type: "category", data: ["A","B"] }, yAxis: {}, series: [{ type: "bar", data: [1,2] }] };
    render(<EChart option={opt} />);
    expect(screen.getByTestId("echart")).toBeInTheDocument();
  });
});