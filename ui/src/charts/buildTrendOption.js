/**
 * Build a stable option-like object for a time series (year,value).
 * Input rows: [{ year:number|string, value:number }]
 * - Filters invalid rows
 * - Coerces year to number, sorts ascending
 * - Computes min/max for quick scaling
 */
export function buildTrendOption({ data = [] } = {}) {
  const rows = Array.isArray(data) ? data : [];
  const cleaned = rows
    .map((r) => {
      const y = Number(r.year);
      const v = typeof r.value === "number" ? r.value : Number(r.value);
      return { year: Number.isFinite(y) ? y : null, value: Number.isFinite(v) ? v : null };
    })
    .filter((r) => r.year !== null && r.value !== null)
    .sort((a, b) => a.year - b.year);

  const values = cleaned.map((r) => r.value);
  const min = values.length ? Math.min(...values) : 0;
  const max = values.length ? Math.max(...values) : 0;

  return {
    meta: { count: cleaned.length, min, max },
    series: cleaned, // [{year, value}]
  };
}