<script setup>
import * as echarts from "echarts/core";
import { LineChart, CandlestickChart } from "echarts/charts";
import {
  GridComponent,
  LegendComponent,
  TooltipComponent,
} from "echarts/components";
import { CanvasRenderer } from "echarts/renderers";
import { onBeforeUnmount, onMounted, ref, watch } from "vue";

echarts.use([
  LineChart,
  CandlestickChart,
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
  
  // Candlestick data format in ECharts: [open, close, lowest, highest]
  const candlestickData = props.prices.map((item) => [
    item.open,
    item.close,
    item.low,
    item.high,
  ]);

  chart.setOption({
    animation: true,
    grid: { left: 12, right: 18, top: 26, bottom: 28, containLabel: true },
    tooltip: {
      trigger: "axis",
      backgroundColor: "#111c19",
      borderColor: "#2b3a35",
      textStyle: { color: "#eef5f1" },
      formatter: function (params) {
        if (!params || params.length === 0) return "";
        let result = `<div style="font-weight: bold; margin-bottom: 6px; font-size: 12px; color: #8da099;">${params[0].name}</div>`;
        params.forEach((item) => {
          if (item.seriesName === "K线") {
            const dataVal = item.value;
            if (Array.isArray(dataVal)) {
              const offset = dataVal.length >= 5 ? 1 : 0;
              const open = dataVal[offset];
              const close = dataVal[offset + 1];
              const low = dataVal[offset + 2];
              const high = dataVal[offset + 3];
              
              const isUp = close >= open;
              const colorStyle = `font-weight: bold; color: ${isUp ? '#c8ff5c' : '#ff8585'}`;
              
              result += `<div style="margin-bottom: 4px;">${item.marker}${item.seriesName}: <span style="${colorStyle}">${close}</span></div>`;
              result += `<div style="padding-left: 16px; font-size: 11px; color: #a5b3ae; line-height: 1.5; margin-bottom: 6px;">
                <div>开盘: <span style="color: #eef5f1;">${open}</span></div>
                <div>收盘: <span style="color: #eef5f1;">${close}</span></div>
                <div>最低: <span style="color: #eef5f1;">${low}</span></div>
                <div>最高: <span style="color: #eef5f1;">${high}</span></div>
              </div>`;
            }
          } else {
            const val = typeof item.value === 'number' ? item.value.toFixed(2) : item.value;
            result += `<div style="margin-bottom: 2px;">${item.marker}${item.seriesName}: <span style="font-weight: bold; color: #eef5f1;">${val}</span></div>`;
          }
        });
        return result;
      },
    },
    legend: {
      data: ["K线", "MA20", "MA60"],
      right: 10,
      textStyle: { color: "#8da099" },
    },
    xAxis: {
      type: "category",
      data: dates,
      boundaryGap: true,
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
        name: "K线",
        type: "candlestick",
        data: candlestickData,
        itemStyle: {
          color: "rgba(200, 255, 92, 0.45)",   // Semi-transparent lime green for rising
          color0: "rgba(255, 133, 133, 0.45)",  // Semi-transparent red for falling
          borderColor: "#c8ff5c",               // Lime green border and shadow lines for rising
          borderColor0: "#ff8585",              // Red border and shadow lines for falling
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
