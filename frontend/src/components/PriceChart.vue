<script setup>
import * as echarts from "echarts/core";
import { LineChart } from "echarts/charts";
import {
  GridComponent,
  LegendComponent,
  TooltipComponent,
} from "echarts/components";
import { CanvasRenderer } from "echarts/renderers";
import { onBeforeUnmount, onMounted, ref, watch } from "vue";

echarts.use([
  LineChart,
  GridComponent,
  LegendComponent,
  TooltipComponent,
  CanvasRenderer,
]);

const props = defineProps({ prices: { type: Array, default: () => [] } });
const root = ref();
let chart;

function average(items, window) {
  return items.map((_, index) => {
    if (index < window - 1) return "-";
    const values = items.slice(index - window + 1, index + 1);
    return +(values.reduce((sum, value) => sum + value, 0) / window).toFixed(2);
  });
}

function render() {
  if (!chart || !props.prices.length) return;
  const dates = props.prices.map((item) => item.trade_date.slice(5));
  const close = props.prices.map((item) => item.close);
  chart.setOption({
    animation: true,
    grid: { left: 12, right: 18, top: 26, bottom: 28, containLabel: true },
    tooltip: {
      trigger: "axis",
      backgroundColor: "#111c19",
      borderColor: "#2b3a35",
      textStyle: { color: "#eef5f1" },
    },
    legend: {
      data: ["收盘", "MA20", "MA60"],
      right: 10,
      textStyle: { color: "#8da099" },
    },
    xAxis: {
      type: "category",
      data: dates,
      boundaryGap: false,
      axisLine: { lineStyle: { color: "#30403a" } },
      axisLabel: { color: "#73867f", interval: 19 },
    },
    yAxis: {
      type: "value",
      scale: true,
      splitLine: { lineStyle: { color: "rgba(255,255,255,.05)" } },
      axisLabel: { color: "#73867f" },
    },
    series: [
      {
        name: "收盘",
        data: close,
        type: "line",
        showSymbol: false,
        lineStyle: { width: 2, color: "#c8ff5c" },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: "rgba(200,255,92,.24)" },
            { offset: 1, color: "rgba(200,255,92,0)" },
          ]),
        },
      },
      {
        name: "MA20",
        data: average(close, 20),
        type: "line",
        showSymbol: false,
        lineStyle: { width: 1.2, color: "#60a5fa" },
      },
      {
        name: "MA60",
        data: average(close, 60),
        type: "line",
        showSymbol: false,
        lineStyle: { width: 1.2, color: "#f5a45d" },
      },
    ],
  });
}

onMounted(() => {
  chart = echarts.init(root.value);
  render();
  window.addEventListener("resize", chart.resize);
});
watch(() => props.prices, render, { deep: true });
onBeforeUnmount(() => {
  window.removeEventListener("resize", chart?.resize);
  chart?.dispose();
});
</script>

<template><div ref="root" class="price-chart"></div></template>
