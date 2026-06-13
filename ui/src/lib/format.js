// Shared Czech (cs-CZ) number formatting for USD amounts and shares.
// Single source of truth — KeyData, OpportunityHeadline and others import from
// here so "mil./mld. USD" and decimal-comma rules never drift apart.

export function formatCzechUSD(x) {
  if (x == null || Number.isNaN(x)) return "—";
  if (x === 0) return "0 USD"; // a real zero is data, not a missing value
  try {
    const millions = x / 1e6;
    if (Math.abs(millions) >= 1000) {
      const billions = millions / 1000;
      const formatted = billions.toLocaleString("cs-CZ", {
        minimumFractionDigits: 1,
        maximumFractionDigits: 1,
      });
      return `${formatted} mld. USD`;
    } else if (Math.abs(millions) >= 1) {
      const formatted = millions.toLocaleString("cs-CZ", {
        minimumFractionDigits: 1,
        maximumFractionDigits: 1,
      });
      return `${formatted} mil. USD`;
    } else if (Math.abs(millions) >= 0.01) {
      const formatted = millions.toLocaleString("cs-CZ", {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
      });
      return `${formatted} mil. USD`;
    } else {
      // Tiny bases (< 10 000 USD) stay in plain USD ("1 343 USD"), so a huge
      // YoY like +81 570 % can show its honest base without rounding it away.
      const formatted = x.toLocaleString("cs-CZ", {
        minimumFractionDigits: 0,
        maximumFractionDigits: 0,
      });
      return `${formatted} USD`;
    }
  } catch {
    return String(x) + " USD";
  }
}

// Decimal share (0.3132) -> "31,3 %" (Czech typographic space before %).
export function formatPct1(decimalShare) {
  const n = Number(decimalShare);
  if (decimalShare == null || Number.isNaN(n)) return "—";
  return `${(n * 100).toLocaleString("cs-CZ", {
    minimumFractionDigits: 1,
    maximumFractionDigits: 1,
  })} %`;
}

// Percent-unit value -> "+15,3 %". yoy is an honest percent and can be HUGE
// (81569.9 = +81 569,9 % off a 1 343 USD base): cs-CZ thousands separators,
// 1 decimal for small values, 0 decimals once |pct| >= 100.
export function formatSignedPct(pct) {
  const n = Number(pct);
  if (pct == null || Number.isNaN(n)) return "—";
  const formatted = n.toLocaleString("cs-CZ", {
    minimumFractionDigits: 0,
    maximumFractionDigits: Math.abs(n) >= 100 ? 0 : 1,
  });
  return `${n > 0 ? "+" : ""}${formatted} %`;
}

// Two USD amounts in ONE shared unit, e.g. "0,12 → 1,10 mil. USD".
// The unit is picked from the larger of the two values. When the smaller
// value would round to "0,00" in that unit (tiny base under a huge YoY jump,
// e.g. 1 343 USD → 1,1 mil. USD), each side keeps its own unit instead.
export function formatUsdPair(prev, cur) {
  const p = Number(prev);
  const c = Number(cur);
  if (!Number.isFinite(p) || !Number.isFinite(c)) return "—";
  const ref = Math.max(Math.abs(p), Math.abs(c));
  const lo = Math.min(Math.abs(p), Math.abs(c));
  const useBillions = ref >= 1e9;
  const div = useBillions ? 1e9 : 1e6;
  if (lo > 0 && lo / div < 0.005) {
    return `${formatCzechUSD(p)} → ${formatCzechUSD(c)}`;
  }
  const unit = useBillions ? "mld. USD" : "mil. USD";
  const fmt = (x) =>
    (x / div).toLocaleString("cs-CZ", {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    });
  return `${fmt(p)} → ${fmt(c)} ${unit}`;
}
