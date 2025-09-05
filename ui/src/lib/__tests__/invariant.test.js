import { describe, it, expect, vi } from "vitest";
import { assertArray, toFiniteNumber } from "../../lib/invariant.js";

describe("invariant helpers", () => {
  it("assertArray returns [] and warns on non-array", () => {
    const spy = vi.spyOn(console, "warn").mockImplementation(() => {});
    const out = assertArray(123, "test.here");
    expect(Array.isArray(out)).toBe(true);
    expect(out.length).toBe(0);
    expect(spy).toHaveBeenCalled();
    spy.mockRestore();
  });

  it("toFiniteNumber parses numbers and rejects NaN", () => {
    expect(toFiniteNumber("42")).toBe(42);
    expect(toFiniteNumber(NaN)).toBeNull();
  });
});