import React, { useEffect, useRef } from "react";
import * as echarts from "echarts";

/**
 * EChart — minimal, dependency-free wrapper around ECharts
 * - Uses SVG renderer (no canvas dep; test-friendly).
 * - Resizes with the window.
 * Props: { option, style }
 */
export default function EChart({ option, style }) {
  const ref = useRef(null);
  const chartRef = useRef(null);

  useEffect(() => {
    if (!ref.current) return;
    // init with SVG so JSDOM tests won't require canvas
    chartRef.current = echarts.init(ref.current, null, { renderer: "svg" });
    const handle = () => chartRef.current && chartRef.current.resize();
    window.addEventListener("resize", handle);
    return () => {
      window.removeEventListener("resize", handle);
      if (chartRef.current) {
        chartRef.current.dispose();
        chartRef.current = null;
      }
    };
  }, []);

  useEffect(() => {
    if (!chartRef.current || !option) return;
    chartRef.current.setOption(option, { notMerge: true, lazyUpdate: true });
  }, [option]);

  return (
    <div
      ref={ref}
      style={{
        width: "100%",
        minHeight: 260,
        ...style,
      }}
      data-testid="echart"
    />
  );
}