<script setup>
import { computed } from "vue";
import ScoreRing from "./ScoreRing.vue";

const props = defineProps({
  item: { type: Object, required: true },
});

function formatSigned(value, digits = 2) {
  const num = Number(value || 0);
  return `${num > 0 ? "+" : ""}${num.toFixed(digits)}`;
}

const dominantDriver = computed(() => {
  const item = props.item;
  const sentimentImpact = Math.abs(item.metrics?.sentiment || 0) * 100 + (item.burst || 0) * 6;
  const trend = item.trend_score || 0;
  const volume = item.volume_score || 0;

  if (sentimentImpact >= trend && sentimentImpact >= volume) {
    return { label: "新闻主导", tone: "news" };
  }
  if (volume >= trend - 6) {
    return { label: "量能确认", tone: "volume" };
  }
  return { label: "趋势主导", tone: "trend" };
});

const summaryLine = computed(() => {
  const item = props.item;
  return [
    `趋势 ${Math.round(item.trend_score || 0)}`,
    `舆情 ${formatSigned(item.metrics?.sentiment || 0)}`,
    `量能 ${Math.round(item.volume_score || 0)}`,
  ].join(" · ");
});

const catalystLine = computed(() => {
  const item = props.item;
  const keywords = item.metrics?.keywords?.slice(0, 3).join(" / ") || "暂无明确关键词";
  return `最近驱动：${keywords}`;
});

const burstLine = computed(() => {
  const item = props.item;
  return `热度 Z ${(item.burst || 0).toFixed(1)} · 今日提及 ${item.metrics?.mentions_today ?? 0} 条 · 研究上限 ${item.research_weight_pct ?? 0}%`;
});

const sentimentClass = computed(() => ({
  positive: (props.item.metrics?.sentiment || 0) > 0,
  negative: (props.item.metrics?.sentiment || 0) < 0,
}));
</script>

<template>
  <RouterLink :to="`/stocks/${item.symbol}`" class="signal-row-card">
    <div class="signal-row-main">
      <div class="stock-identity">
        <div class="stock-name">
          <b>{{ item.name }}</b>
          <span class="board-badge" :class="`board-${item.market_board}`">
            {{ item.market_board }}
          </span>
          <span class="driver-badge" :class="`driver-${dominantDriver.tone}`">
            {{ dominantDriver.label }}
          </span>
        </div>
        <small>{{ item.symbol }} · {{ item.industry }}</small>
      </div>

      <div class="signal-status-block">
        <span class="status-pill" :class="item.status">{{ item.status }}</span>
        <small>研究权重 {{ item.research_weight_pct }}%</small>
      </div>

      <div class="metric-cell">
        <b>{{ Math.round(item.trend_score) }}</b>
        <i><i :style="{ width: `${item.trend_score}%` }"></i></i>
      </div>

      <div class="sentiment-cell">
        <span :class="sentimentClass">
          {{ formatSigned(item.metrics?.sentiment || 0) }}
        </span>
        <small>{{ item.metrics?.keywords?.slice(0, 2).join(" · ") || "中性" }}</small>
      </div>

      <div class="burst-cell">
        <b>{{ item.research_weight_pct }}%</b>
        <small>Z {{ (item.burst || 0).toFixed(1) }} · {{ item.metrics?.mentions_today ?? 0 }} 条</small>
      </div>

      <ScoreRing :value="item.total_score" />
    </div>

    <div class="signal-row-summary">
      <p>{{ summaryLine }}</p>
      <p>{{ catalystLine }}</p>
      <p>{{ burstLine }}</p>
    </div>
  </RouterLink>
</template>
