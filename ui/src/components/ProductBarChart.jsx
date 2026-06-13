import React, { useMemo } from "react";
import ReactEChartsCore from "echarts-for-react/lib/core";
import echarts from "../lib/echarts.js";

/**
 * Props:
 *  - data: [{ id, name, value, value_fmt }]
 *  - title?: string
 *  - onSelect?: (id: string) => void
 */

// SINGLE SOURCE OF TRUTH for formatting chart values
// Uses EXACTLY the same logic as KeyData.jsx formatCzechUSD()
// Input: raw API value in thousands USD (e.g., 116264)  
// Output: formatted display string (e.g., "116,3")
function formatChartValue(x) {
  if (x == null || Number.isNaN(x)) return "0";
  try {
    // Chart receives actual USD values, no additional scaling needed
    const millions = x / 1e6;
    if (millions >= 1) {
      // Just return the number, unit added separately
      return millions.toLocaleString("cs-CZ", { minimumFractionDigits: 1, maximumFractionDigits: 1 });
    }
    // For values below 1 million, show 2 decimal places for better precision
    return millions.toLocaleString("cs-CZ", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  } catch {
    return "0";
  }
}

// Percent with 1 decimal in cs-CZ, e.g. 31.32 -> "31,3 %"
function formatPercentValue(v) {
  const n = Number(v);
  if (!Number.isFinite(n)) return "—";
  return `${n.toLocaleString("cs-CZ", { minimumFractionDigits: 1, maximumFractionDigits: 1 })} %`;
}

export default function ProductBarChart({
  data = [],
  title,
  subtitle,
  onSelect,
  selectedId = null,
  hs6Label = null,
  czechTitleMode = 'cz',
  referenceData = { countryNames: {}, hs6Labels: {}, continents: {}, loading: false },
  // Peer-benchmark mode: bars encode CZ share of each country's imports (%)
  // instead of USD, with a dashed group-median markLine. Falls back to the
  // USD encoding when records carry no `share` field (older API).
  shareMode = false,
  peerMedian = null
}) {
  // Use centralized reference data instead of loading independently
  const czechNames = referenceData.countryNames;

  const items = Array.isArray(data) ? data : [];

  // Auto height so labels never overlap; minimum height for empty/small lists
  const height = Math.max(220, 28 * Math.max(1, items.length) + 40);

  const resolvedTitle = (() => {
    if (title) return title; // explicit title wins
    if (items.length === 0) return "No data";
    const hs6Text = hs6Label ? `HS6 ${hs6Label}` : "";
    const base = czechTitleMode === 'peers'
      ? "Top importéři v benchmarkové skupině"
      : "Top 10 importérů z Česka";
    return `${base}${hs6Text ? ` — ${hs6Text}` : ''}`;
  })();

  const resolvedSubtitle = (() => {
    // If we have a meaningful subtitle (not null, undefined, or empty string), use it
    if (subtitle && subtitle.trim()) return subtitle; 
    if (items.length === 0) return null;
    return "Celkový český export do jednotlivých zemí (seřazeno sestupně)\nHodnoty: objem exportu v USD";
  })();

  // Memoized: the option holds formatter closures, which echarts-for-react
  // deep-compares by reference — a fresh option per render forced a full
  // setOption/redraw (re-animation) on every parent re-render.
  const option = useMemo(() => {
    const rows = Array.isArray(data) ? data : [];
    // Use the share encoding only when the API actually sent shares —
    // otherwise degrade gracefully to the USD encoding.
    const hasShares = rows.some((b) => Number.isFinite(Number(b?.share)));
    const useShareEncoding = shareMode && hasShares;

    const seriesData = rows
      .map((b) => {
        // Convert ISO3 country codes to Czech names if possible
        let displayName = b.name || b.id;
        const iso3 = String(b.id || b.name || '').toUpperCase();
        if (/^[A-Z]{3}$/.test(iso3) && czechNames[iso3]) {
          displayName = czechNames[iso3];
        }

        const usd = Number(b.value) || 0; // API returns values already in USD
        const shareVal = Number.isFinite(Number(b?.share)) ? Number(b.share) : null;

        return {
          value: useShareEncoding ? (shareVal != null ? shareVal * 100 : 0) : usd,
          usd,
          share: shareVal,
          id: b.id,
          value_fmt: b.value_fmt ?? null,
          name: displayName,
          itemStyle: b.id === selectedId
            ? { opacity: 1, borderWidth: 2, borderColor: "#222" }
            : { opacity: 0.8 },
        };
      })
      .sort((a, b) => b.value - a.value);  // Sort descending (largest first)

    // For horizontal bar chart: reverse arrays so largest values appear at top
    const categories = seriesData.map((d) => d.name).reverse();
    const reversedSeriesData = [...seriesData].reverse();

    const medianPct = Number.isFinite(Number(peerMedian)) ? Number(peerMedian) * 100 : null;

    return {
      grid: { left: 8, right: 60, top: 8, bottom: 8, containLabel: true },
      tooltip: {
        trigger: "item",
        formatter: (p) => {
          const d = p?.data || {};
          if (useShareEncoding) {
            const shareTxt = d.share != null ? formatPercentValue(d.share * 100) : "—";
            const exportTxt = d.value_fmt ? `${d.value_fmt} USD` : `${formatChartValue(d.usd)} mil. USD`;
            return `${d.name}: <b>${shareTxt}</b> podíl ČR na importu • export ${exportTxt}`;
          }
          // Try multiple ways to access the value
          const val = Number.isFinite(p.value) ? p.value :
                     Number.isFinite(d.value) ? d.value :
                     Number.isFinite(p.data?.value) ? p.data.value : 0;
          const formatted = formatChartValue(val);
          const shareSuffix = d.share != null ? ` • podíl ${formatPercentValue(d.share * 100)}` : "";
          return `${d.name}<br/><b>${formatted} mil. USD</b>${shareSuffix}`;
        },
      },
      xAxis: {
        type: "value",
        axisLabel: {
          fontSize: 12,
          margin: 8,
          hideOverlap: true, // tick labels are long ("1 000,0 mil.") and collided
          formatter: (v) => {
            if (useShareEncoding) return formatPercentValue(v);
            // Use same formatting function as tooltip for consistency
            const formatted = formatChartValue(v);
            return `${formatted} mil.`; // Always show as millions for simplicity
          },
        },
      },
      yAxis: { type: "category", data: categories, axisTick: { show: false } },
      series: [
        {
          type: "bar",
          data: reversedSeriesData,
          label: { show: false },
          itemStyle: { borderRadius: [2, 2, 2, 2] },
          emphasis: { focus: "series" },
          // Dashed vertical line at the peer-group median share. z above the
          // bars (default series z=2) so it isn't hidden behind the many bars
          // that extend past the median.
          ...(useShareEncoding && medianPct != null ? {
            markLine: {
              symbol: 'none',
              silent: true,
              animation: false,
              z: 10,
              lineStyle: { type: 'dashed', color: '#b45309', width: 2, opacity: 1 },
              label: {
                show: true,
                formatter: `medián ${formatPercentValue(medianPct)}`,
                position: 'insideEndTop',
                fontSize: 11,
                fontWeight: 'bold',
                color: '#b45309',
              },
              data: [{ name: 'medián', xAxis: medianPct }],
            },
          } : {}),
        },
      ],
    };
  }, [data, selectedId, czechNames, shareMode, peerMedian]);

  // Memoized for the same reason as option — changed onEvents makes
  // echarts-for-react dispose() and rebuild the whole chart.
  const onEvents = useMemo(() => onSelect
    ? {
        click: (params) => {
          const d = params?.data;
          if (d && d.id) onSelect(d.id);
        },
      }
    : undefined, [onSelect]);

  return (
    <div style={{ border: "1px solid #eee", borderRadius: 6, padding: 12, background: "#fff" }}>
      <h2 style={{ fontFamily: "Montserrat", fontWeight: "bold", marginBottom: 6, fontSize: 18, color: "#008C00" }}>{resolvedTitle}</h2>
      {resolvedSubtitle && (
        <div style={{ marginBottom: 8, fontSize: 14, color: "#666", fontWeight: "normal", whiteSpace: "pre-line" }}>{resolvedSubtitle}</div>
      )}
      {items.length === 0 ? (
        <div style={{ padding: "6px 8px", color: "#666" }}>Vyberte signál pro zobrazení detailů</div>
      ) : (
        <ReactEChartsCore
          echarts={echarts}
          option={option}
          notMerge={true}
          lazyUpdate={false}
          style={{ width: "100%", height }}
          onEvents={onEvents}
        />
      )}
    </div>
  );
}
