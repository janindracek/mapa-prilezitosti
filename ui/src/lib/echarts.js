// Tree-shaken ECharts build — import only the pieces the app actually uses.
// Replaces the wholesale `import * as echarts from "echarts"` (~1 MB) with the
// modular core + just the chart types, components and renderer we render.
//
// Used by WorldMap (map) and ProductBarChart (bar) via echarts-for-react/lib/core.
import * as echarts from "echarts/core";
import { MapChart, BarChart } from "echarts/charts";
import {
  TooltipComponent,
  VisualMapComponent,
  GridComponent,
} from "echarts/components";
import { CanvasRenderer } from "echarts/renderers";

echarts.use([
  MapChart,
  BarChart,
  TooltipComponent,
  VisualMapComponent,
  GridComponent,
  CanvasRenderer,
]);

export default echarts;
export { echarts };
