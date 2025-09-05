import { describe, it, expect } from "vitest";
import { COUNTRIES, YEARS, METRICS } from "../../lib/options.js";

describe("options", () => {
  it("are non-empty and have sensible types", () => {
    expect(COUNTRIES.length).toBeGreaterThan(0);
    expect(YEARS.length).toBeGreaterThan(0);
    expect(METRICS.length).toBeGreaterThan(0);
    expect(Array.isArray(COUNTRIES)).toBe(true);
    expect(YEARS.every((y) => Number.isFinite(Number(y)))).toBe(true);
    expect(METRICS.every((m) => typeof m === "string")).toBe(true);
  });
});