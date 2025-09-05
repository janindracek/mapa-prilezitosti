import React from "react";
import ReactECharts from "echarts-for-react";

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
  console.debug('[formatChartValue] input:', x);
  if (x == null || Number.isNaN(x)) return "0";
  try {
    // Chart receives actual USD values, no additional scaling needed
    const millions = x / 1e6;
    console.debug('[formatChartValue] millions:', millions);
    
    if (millions >= 1) {
      const formatted = millions.toLocaleString("cs-CZ", { 
        minimumFractionDigits: 1, 
        maximumFractionDigits: 1 
      });
      console.debug('[formatChartValue] formatted:', formatted);
      return formatted; // Just return the number, unit added separately
    } else {
      // For values below 1 million, show 2 decimal places for better precision
      const formatted = millions.toLocaleString("cs-CZ", { 
        minimumFractionDigits: 2, 
        maximumFractionDigits: 2 
      });
      console.debug('[formatChartValue] small value with 2 decimals:', formatted);
      return formatted;
    }
  } catch (e) {
    console.debug('[formatChartValue] error:', e);
    return "0";
  }
}

export default function ProductBarChart({ 
  data = [], 
  title, 
  subtitle, 
  onSelect, 
  selectedId = null, 
  hs6Label = null, 
  czechTitleMode = 'cz',
  referenceData = { countryNames: {}, hs6Labels: {}, continents: {}, loading: false }
}) {
  // Use centralized reference data instead of loading independently
  const czechNames = referenceData.countryNames;

  const items = Array.isArray(data) ? data : [];
  console.debug('[ProductBarChart] input data:', items?.slice(0, 3));
  const seriesData = items
    .map((b) => {
      // Convert ISO3 country codes to Czech names if possible
      let displayName = b.name || b.id;
      const iso3 = String(b.id || b.name || '').toUpperCase();
      if (/^[A-Z]{3}$/.test(iso3) && czechNames[iso3]) {
        displayName = czechNames[iso3];
      }
      
      return {
        value: Number(b.value) || 0, // API returns values already in USD, no scaling needed
        id: b.id,
        value_fmt: null,
        name: displayName,
        itemStyle: b.id === selectedId
          ? { opacity: 1, borderWidth: 2, borderColor: "#222" }
          : { opacity: 0.8 },
      };
    })
    .sort((a, b) => b.value - a.value);  // Sort descending (largest first)
  
  console.debug('[ProductBarChart] processed seriesData:', seriesData?.slice(0, 3));
  
  // For horizontal bar chart: reverse arrays so largest values appear at top
  const categories = seriesData.map((d) => d.name).reverse();  
  const reversedSeriesData = [...seriesData].reverse();

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

  const option = {
    grid: { left: 8, right: 60, top: 8, bottom: 8, containLabel: true },
    tooltip: {
      trigger: "item",
      formatter: (p) => {
        const d = p?.data || {};
        // Try multiple ways to access the value
        const val = Number.isFinite(p.value) ? p.value : 
                   Number.isFinite(d.value) ? d.value : 
                   Number.isFinite(p.data?.value) ? p.data.value : 0;
        const formatted = formatChartValue(val);
        return `${d.name}<br/><b>${formatted} mil. USD</b>`;
      },
    },
    xAxis: {
      type: "value",
      axisLabel: {
        fontSize: 12,
        margin: 8,
        formatter: (v) => {
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
      },
    ],
  };

  const onEvents = onSelect
    ? {
        click: (params) => {
          const d = params?.data;
          if (d && d.id) onSelect(d.id);
        },
      }
    : undefined;

  return (
    <div style={{ border: "1px solid #eee", borderRadius: 6, padding: 12, background: "#fff" }}>
      <h2 style={{ fontFamily: "Montserrat", fontWeight: "bold", marginBottom: 6, fontSize: 18, color: "#008C00" }}>{resolvedTitle}</h2>
      {resolvedSubtitle && (
        <div style={{ marginBottom: 8, fontSize: 14, color: "#666", fontWeight: "normal", whiteSpace: "pre-line" }}>{resolvedSubtitle}</div>
      )}
      {items.length === 0 ? (
        <div style={{ padding: "6px 8px", color: "#666" }}>Vyberte signál pro zobrazení detailů</div>
      ) : (
        <ReactECharts
          option={option}
          notMerge={true}
          lazyUpdate={true}
          style={{ width: "100%", height }}
          onEvents={onEvents}
        />
      )}
    </div>
  );
}
