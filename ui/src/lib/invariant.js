// Minimal guard helpers (no deps). They never throw; they coerce + warn.
// Use them to keep render paths crash-free.

export function assertArray(value, where = "value") {
  if (Array.isArray(value)) return value;
  console.warn(`[invariant] expected array at ${where}, got:`, value);
  return [];
}

export function toFiniteNumber(value, where = "value") {
  const n = typeof value === "number" ? value : Number(value);
  if (Number.isFinite(n)) return n;
  console.warn(`[invariant] expected finite number at ${where}, got:`, value);
  return null;
}