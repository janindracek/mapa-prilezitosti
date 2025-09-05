import { describe, it, expect } from "vitest";
import { buildProductBarOption } from "../../charts/buildProductBarOption.js";

describe("buildProductBarOption", () => {
  it("filters invalid rows, sorts desc, and limits to topN", () => {
    const data = [
      { id: "a", name: "A", value: 12 },
      { id: "b", name: "B", value: "7" },
      { id: "c", name: "C", value: NaN }, // removed
      { id: "d", name: "D", value: 20 },
    ];
    const opt = buildProductBarOption({ data, topN: 2 });
    expect(opt.meta.count).toBe(3);
    expect(opt.meta.shown).toBe(2);
    expect(opt.series[0]).toMatchObject({ id: "d", value: 20 });
    expect(opt.series[1]).toMatchObject({ id: "a", value: 12 });
  });
});