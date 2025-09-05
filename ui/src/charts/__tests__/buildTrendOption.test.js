import { describe, it, expect } from "vitest";
import { buildTrendOption } from "../../charts/buildTrendOption.js";

describe("buildTrendOption", () => {
  it("filters invalid rows, sorts by year, and reports min/max", () => {
    const data = [
      { year: "2021", value: 12 },
      { year: 2019, value: "7" },
      { year: 2020, value: 10 },
      { year: "x", value: 3 },   // invalid
      { year: 2022, value: NaN } // invalid
    ];
    const opt = buildTrendOption({ data });
    expect(opt.meta.count).toBe(3);
    expect(opt.series.map(r => r.year)).toEqual([2019, 2020, 2021]);
    expect(opt.meta.min).toBe(7);
    expect(opt.meta.max).toBe(12);
  });
});