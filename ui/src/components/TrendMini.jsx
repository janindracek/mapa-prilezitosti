import React, { useMemo, useState } from "react";
import { buildTrendOption } from "../charts/buildTrendOption.js";

/**
 * TrendMini — SVG sparkline with area + hover tooltip (no deps)
 * Props:
 *  - data: [{ year, value }]
 *  - title?: string
 *  - height?: number
 *  - width?: number
 */
export default function TrendMini({ data = [], title = "Trend", height = 80, width = 320 }) {
  const opt = buildTrendOption({ data });
  const [hover, setHover] = useState(null);

  const pad = 8;
  const w = Math.max(width, 120);
  const h = Math.max(height, 60);
  const cw = w - pad * 2;
  const ch = h - pad * 2;

  const series = opt.series;

  const years = Array.isArray(series) ? series.map(d => d.year) : [];
  const values = Array.isArray(series) ? series.map(d => d.value) : [];
  const minYear = years.length ? Math.min(...years) : 0;
  const maxYear = years.length ? Math.max(...years) : 1;
  const minVal  = values.length ? Math.min(...values) : 0;
  const maxVal  = values.length ? Math.max(...values) : 1;
  const xSpan = maxYear - minYear || 1;
  const ySpan = maxVal - minVal || 1;

  const toX = (year) => pad + ((year - minYear) / xSpan) * cw;
  const toY = (val)  => pad + ch - ((val - minVal) / ySpan) * ch;

  // Build polyline & area path
  const { points, areaPath } = useMemo(() => {
    if (!Array.isArray(series) || series.length === 0) return { points: "", areaPath: "" };
    const pts = series.map(d => [toX(d.year), toY(d.value)]);
    const pointsStr = pts.map(([x,y]) => `${x},${y}`).join(" ");
    const area = `M ${pts[0][0]} ${pad+ch} ` + pts.map(([x,y]) => `L ${x} ${y}`).join(" ")
               + ` L ${pts[pts.length-1][0]} ${pad+ch} Z`;
    return { points: pointsStr, areaPath: area };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [w, h, pad, ch, minYear, maxYear, minVal, maxVal, JSON.stringify(series)]);

  // After hooks are declared, we can early-return for empty series
  if (series.length === 0) {
    return (
      <div data-testid="trendmini" style={{ border: "1px solid #eee", borderRadius: 6, padding: 12, width: w, background: "#fff" }}>
        <div style={{ fontFamily: "Montserrat", fontWeight: "bold", marginBottom: 6, fontSize: 18, color: "#008C00" }}>{title} (SVG)</div>
        <div style={{ fontSize: 12, opacity: 0.8 }}>No data</div>
      </div>
    );
  }

  // Simple hover: find nearest point by x
  const handleMove = (evt) => {
    const svg = evt.currentTarget;
    const rect = svg.getBoundingClientRect();
    const x = evt.clientX - rect.left - pad;
    if (x < 0 || x > cw) return setHover(null);
    const t = x / cw; // 0..1 across
    const year = Math.round(minYear + t * (maxYear - minYear));
    // snap to nearest existing year
    let best = null, bestDx = Infinity;
    for (const d of series) {
      const dx = Math.abs(d.year - year);
      if (dx < bestDx) { bestDx = dx; best = d; }
    }
    setHover(best);
  };

  const handleLeave = () => setHover(null);

  // Min/Mid/Max year ticks
  const tickYears = [minYear, Math.round((minYear + maxYear) / 2), maxYear]
    .filter((v, i, a) => a.indexOf(v) === i)
    .map((y) => ({ x: toX(y), y: h - 2, label: String(y) }));

  return (
    <div data-testid="trendmini" style={{ border: "1px solid #eee", borderRadius: 6, padding: 12, width: w, background: "#fff" }}>
      <div style={{ fontFamily: "Montserrat", fontWeight: "bold", marginBottom: 6, fontSize: 18, color: "#008C00" }}>{title} (SVG)</div>
      <svg
        role="img"
        aria-label={`${title} sparkline`}
        width={w}
        height={h}
        onMouseMove={handleMove}
        onMouseLeave={handleLeave}
        style={{ display: "block" }}
      >
        <rect x="0" y="0" width={w} height={h} fill="#ffffff" stroke="none" />
        {/* area */}
        <path d={areaPath} fill="#dbe5ff" stroke="none" />
        {/* line */}
        <polyline points={points} fill="none" stroke="#2f6fed" strokeWidth="2" strokeLinejoin="round" strokeLinecap="round" />
        {/* points */}
        {series.map(d => (
          <circle key={d.year} cx={toX(d.year)} cy={toY(d.value)} r="2" fill="#2f6fed" />
        ))}
        {/* x-axis ticks */}
        {tickYears.map((t) => (
          <text key={t.label} x={t.x} y={t.y} fontSize="10" textAnchor="middle" fill="#555">
            {t.label}
          </text>
        ))}
        {/* hover marker */}
        {hover && (
          <>
            <line x1={toX(hover.year)} y1={pad} x2={toX(hover.year)} y2={pad+ch} stroke="#94a3b8" strokeDasharray="3,3" />
            <circle cx={toX(hover.year)} cy={toY(hover.value)} r="3" fill="#2f6fed" stroke="#fff" strokeWidth="1" />
          </>
        )}
      </svg>
      <div style={{ fontSize: 12, opacity: 0.8, marginTop: 6 }}>
        Points: {opt.meta.count} | min: {minVal} | max: {maxVal} {hover ? `| ${hover.year}: ${hover.value}` : ""}
      </div>
    </div>
  );
}