import "@testing-library/jest-dom/vitest";
import { cleanup } from "@testing-library/react";
import { afterEach } from "vitest";

afterEach(cleanup);

// --- Test-only ECharts world map registration ---
import * as echarts from "echarts";

// Force SVG renderer in tests to avoid region errors
import { use as echartsUse } from "echarts/core";
import { SVGRenderer } from "echarts/renderers";

+echartsUse([SVGRenderer]);

if (!echarts.getMap("world")) {
  const dummyWorld = {
      type: "FeatureCollection",
     features: [
      {
        type: "Feature",
        id: "DL", // region id
        properties: { name: "Dummyland" },
        geometry: {
          type: "Polygon",
          coordinates: [[[0,0],[10,0],[10,10],[0,10],[0,0]]],
        },
      },
      {
        type: "Feature",
        id: "EX",
        properties: { name: "Examplestan" },
        geometry: {
          type: "Polygon",
          coordinates: [[[20,20],[30,20],[30,30],[20,30],[20,20]]],
        },
      },
    ],
  };
  echarts.registerMap("world", dummyWorld);
  // ADD THIS LINE to match your component’s map name:
  echarts.registerMap("world110m", dummyWorld);
}