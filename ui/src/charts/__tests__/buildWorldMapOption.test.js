import { describe, it, expect } from "vitest";
import { buildWorldMapOption } from "../../charts/buildWorldMapOption.js";

describe("buildWorldMapOption", () => {
  it("filters invalid values and computes min/max", () => {
    const data = [
      { iso3: "CZE", name: "Czechia", value: 10 },
      { iso3: "DEU", name: "Germany", value: "20" },
      { iso3: "FRA", name: "France", value: NaN },
      { iso3: "", name: "Nowhere", value: 5 },
    ];
    const opt = buildWorldMapOption({ data, metric: "value" });
    expect(opt.meta.count).toBe(2);
    expect(opt.meta.min).toBe(10);
    expect(opt.meta.max).toBe(20);
    expect(opt.series.data.every(d => Number.isFinite(d.value))).toBe(true);
  });
});
