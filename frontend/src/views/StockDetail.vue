<script setup>
import { computed, onMounted, ref, watch } from "vue";
import { useRoute } from "vue-router";
import { api } from "../api";
import DecisionChainTimeline from "../components/DecisionChainTimeline.vue";
import DecisionSummaryCard from "../components/DecisionSummaryCard.vue";
import DriverBreakdownPanel from "../components/DriverBreakdownPanel.vue";
import EvidenceFeed from "../components/EvidenceFeed.vue";
import PriceChart from "../components/PriceChart.vue";
import ScoreRing from "../components/ScoreRing.vue";

const route = useRoute();
const data = ref(null);
const error = ref("");
const signal = computed(() => data.value?.signal || null);
const metrics = computed(() => signal.value?.metrics || {});

function formatSigned(value, digits = 2) {
  const num = Number(value || 0);
  return `${num > 0 ? "+" : ""}${num.toFixed(digits)}`;
}

function formatPercent(value, digits = 1) {
  return `${(Number(value || 0) * 100).toFixed(digits)}%`;
}

const dominantDriver = computed(() => {
  if (!signal.value) return "趋势主导";
  const sentimentImpact = Math.abs(metrics.value.sentiment || 0) * 100 + (signal.value.burst || 0) * 6;
  if (sentimentImpact >= signal.value.trend_score && sentimentImpact >= signal.value.volume_score) {
    return "新闻主导";
  }
  if (signal.value.volume_score >= signal.value.trend_score - 6) {
    return "量能确认";
  }
  return "趋势主导";
});

const decisionSummary = computed(() => {
  if (!signal.value) return "";
  const trendText = signal.value.trend_score >= 70 ? "趋势结构已成立" : "趋势结构仍在观察";
  const sentimentText =
    (metrics.value.sentiment || 0) > 0.15
      ? "近期舆情偏正"
      : (metrics.value.sentiment || 0) < -0.15
        ? "近期舆情承压"
        : "舆情暂时中性";
  const burstText =
    (signal.value.burst || 0) >= 3
      ? `热度抬升来自 ${metrics.value.mentions_today ?? 0} 条近期催化`
      : "热度尚未形成强确认";
  const conclusion =
    (signal.value.total_score || 0) >= 75
      ? "当前适合进入重点研究清单。"
      : "当前更适合维持观察，不宜强化结论。";
  return `${trendText}，${sentimentText}，${burstText}，${conclusion}`;
});

const summaryHighlights = computed(() => [
  {
    label: "主导因子",
    value: dominantDriver.value,
    note: "决定当前排序的第一驱动力",
  },
  {
    label: "热度确认",
    value: `Z ${(signal.value?.burst || 0).toFixed(1)}`,
    note: `今日提及 ${metrics.value.mentions_today ?? 0} 条`,
  },
  {
    label: "行业偏差",
    value:
      metrics.value.total_score_neutral !== undefined
        ? formatSigned(metrics.value.total_score_neutral)
        : "—",
    note: "相对行业均值的综合偏离",
  },
]);

const timelineSteps = computed(() => {
  if (!signal.value) return [];
  return [
    {
      title: "价格结构",
      value: `MA5 ${metrics.value.ma5 ?? "—"} / MA20 ${metrics.value.ma20 ?? "—"} / MA60 ${metrics.value.ma60 ?? "—"}`,
      note: `20 日动量 ${formatPercent(metrics.value.momentum20 || 0, 2)}`,
      tone: "trend",
    },
    {
      title: "情绪与新闻",
      value: `舆情 ${formatSigned(metrics.value.sentiment || 0)} · ${metrics.value.keywords?.slice(0, 2).join(" / ") || "暂无关键词"}`,
      note: `最近映射新闻 ${data.value?.news?.length ?? 0} 条`,
      tone: "news",
    },
    {
      title: "热度与量能",
      value: `量比 ${(metrics.value.volume_ratio || 0).toFixed(2)}x · 热度 Z ${(signal.value.burst || 0).toFixed(1)}`,
      note: `量能得分 ${Math.round(signal.value.volume_score || 0)} · 今日提及 ${metrics.value.mentions_today ?? 0} 条`,
      tone: "volume",
    },
    {
      title: "综合结论",
      value: `总分 ${Math.round(signal.value.total_score || 0)} · 研究上限 ${signal.value.research_weight_pct ?? 0}%`,
      note: signal.value.status,
      tone: "summary",
    },
  ];
});

const driverPanels = computed(() => {
  if (!signal.value) return [];
  return [
    {
      title: "趋势驱动",
      score: signal.value.trend_score || 0,
      tone: "trend",
      neutralDelta: metrics.value.trend_score_neutral,
      highlights: [
        `MA5 / MA20 / MA60：${metrics.value.ma5 ?? "—"} / ${metrics.value.ma20 ?? "—"} / ${metrics.value.ma60 ?? "—"}`,
        `20 日动量 ${formatPercent(metrics.value.momentum20 || 0, 2)}`,
        `价格结构${metrics.value.bullish ? "已" : "未"}形成多头确认`,
      ],
    },
    {
      title: "舆情驱动",
      score: signal.value.sentiment_score || 0,
      tone: "news",
      neutralDelta: metrics.value.sentiment_score_neutral,
      highlights: [
        `情绪值 ${formatSigned(metrics.value.sentiment || 0)}`,
        `关键词 ${metrics.value.keywords?.slice(0, 3).join(" / ") || "暂无关键词"}`,
        `关联新闻 ${data.value?.news?.length ?? 0} 条`,
      ],
    },
    {
      title: "量能与热度",
      score: signal.value.volume_score || 0,
      tone: "volume",
      neutralDelta: metrics.value.volume_score_neutral,
      highlights: [
        `量比 ${(metrics.value.volume_ratio || 0).toFixed(2)}x`,
        `热度 Z ${(signal.value.burst || 0).toFixed(1)}`,
        `今日提及 ${metrics.value.mentions_today ?? 0} 条`,
      ],
    },
  ];
});

async function load() {
  error.value = "";
  try {
    data.value = await api.stock(route.params.symbol);
  } catch (err) {
    error.value = err.message;
  }
}

onMounted(load);
watch(() => route.params.symbol, load);
</script>

<template>
  <div v-if="error" class="error-banner">{{ error }}</div>
  <div v-else-if="!data" class="page-loader">正在装载研究面板…</div>
  <template v-else>
    <div class="detail-heading">
      <div>
        <RouterLink to="/" class="back-link">← 返回信号台</RouterLink>
        <p class="eyebrow">{{ data.stock.industry }} · {{ data.stock.symbol }}</p>
        <h1>{{ data.stock.name }}</h1>
      </div>
      <div v-if="signal" class="detail-score">
        <ScoreRing :value="signal.total_score" :size="72" />
        <div>
          <span>综合评分</span>
          <strong>{{ signal.status }}</strong>
          <small v-if="metrics.total_score_neutral !== undefined" style="display: block; font-size: 11px; margin-top: 4px; color: var(--muted)">
            行业偏差:
            <span :class="{ positive: metrics.total_score_neutral > 0, negative: metrics.total_score_neutral < 0 }">
              {{ metrics.total_score_neutral >= 0 ? "+" : "" }}{{ metrics.total_score_neutral.toFixed(2) }}
            </span>
          </small>
        </div>
      </div>
    </div>

    <DecisionSummaryCard
      v-if="signal"
      :stock="data.stock"
      :signal="signal"
      :summary="decisionSummary"
      :dominant-driver="dominantDriver"
      :highlights="summaryHighlights"
    />

    <section class="detail-grid detail-grid-expanded">
      <article class="panel chart-panel">
        <div class="panel-title">
          <div><p class="eyebrow">PRICE STRUCTURE</p><h2>价格与均线</h2></div>
          <div class="last-price">
            <small>最新收盘</small><strong>¥ {{ metrics.close }}</strong>
          </div>
        </div>
        <PriceChart :prices="data.prices" />
      </article>

      <DecisionChainTimeline v-if="signal" :steps="timelineSteps" />
    </section>

    <section v-if="signal" class="driver-breakdown-grid">
      <DriverBreakdownPanel
        v-for="panel in driverPanels"
        :key="panel.title"
        :title="panel.title"
        :score="panel.score"
        :tone="panel.tone"
        :highlights="panel.highlights"
        :neutral-delta="panel.neutralDelta"
      />
    </section>

    <EvidenceFeed :items="data.news" />
  </template>
</template>
