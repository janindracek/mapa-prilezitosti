/**
 * Build a stable option-like object for a simple bar chart.
 * Input rows: [{ id?:string|number, name:string, value:number }]
 * - Filters invalid rows
 * - Sorts descending by value
 * - Returns top N (default 10)
 */
import { assertArray, toFiniteNumber } from "../lib/invariant.js";

export function buildProductBarOption({ data = [], topN = 10 } = {}) {
  const rows = assertArray(data, "buildProductBarOption.data");
  const cleaned = rows
    .map((r, i) => {
      const id = String(r.id ?? i);
      const name = String(r.name ?? r.label ?? `Item ${i + 1}`);
      const v = toFiniteNumber(r.value, "product.value");
      return { id, name, value: v };
    })
    .filter((r) => r.value !== null);

  cleaned.sort((a, b) => (b.value ?? 0) - (a.value ?? 0));
  const top = cleaned.slice(0, topN);

  return {
    meta: {
      count: cleaned.length,
      shown: top.length,
      max: top.length ? top[0].value : 0,
      min: top.length ? top[top.length - 1].value : 0,
    },
    series: top, // simple array the component will render
  };
}