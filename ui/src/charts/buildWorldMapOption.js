/**
 * Build a stable option-like object for a world heatmap.
 * Input: [{ iso3: "CZE", name?: "Czechia", value: 12.3 }, ...]
 * - Filters invalid values
 * - Normalizes names/codes
 * - Computes min/max for a legend scale
 */

import { assertArray, toFiniteNumber } from "../lib/invariant.js";
export function buildWorldMapOption({ data = [], metric = "value" } = {}) {
  const rows = assertArray(data, "buildWorldMapOption.data");
  const cleaned = rows
    .map((r) => {
      const code = String(r.iso3 ?? r.code ?? "").toUpperCase();
      const name = String(r.name ?? r.label ?? code);
      const v = toFiniteNumber(r.value ?? r[metric], "world.value");
      return { code, name, value: v };
    })
    .filter((r) => r.code && r.value !== null);

  const values = cleaned.map((r) => r.value);
  const min = values.length ? Math.min(...values) : 0;
  const max = values.length ? Math.max(...values) : 0;

  return {
    meta: { metric, count: cleaned.length, min, max },
    series: {
      // shape matches what a chart component would expect later
      type: "map",
      map: "world",
      data: cleaned.map((r) => ({ name: r.name, code: r.code, value: r.value })),
    },
  };
}