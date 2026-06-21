<script setup>
import { computed, onMounted, ref } from "vue";
import { api } from "../api";
import ScoreRing from "../components/ScoreRing.vue";

const data = ref({ signals: [], summary: {} });
const loading = ref(true);
const refreshing = ref(false);
const error = ref("");
const activeFilter = ref("全部");

const filters = ["全部", "主升浪信号", "趋势股", "观察"];
const visibleSignals = computed(() =>
  activeFilter.value === "全部"
    ? data.value.signals
    : data.value.signals.filter((item) => item.status === activeFilter.value),
);

async function load() {
  try {
    data.value = await api.dashboard();
  } catch (err) {
    error.value = err.message;
  } finally {
    loading.value = false;
  }
}

async function refresh() {
  refreshing.value = true;
  try {
    await api.runPipeline();
    await load();
  } finally {
    refreshing.value = false;
  }
}

onMounted(load);
</script>

<template>
  <section class="hero">
    <div>
      <p class="eyebrow">DAILY SIGNAL DESK · {{ data.signal_date || "等待数据" }}</p>
      <h1>穿过噪声，<br /><em>只看共振。</em></h1>
      <p class="hero-copy">
        趋势确认方向，舆情识别催化，量能判断可信度。结果不是答案，而是一张更干净的研究清单。
      </p>
    </div>
    <button class="refresh-button" :disabled="refreshing" @click="refresh">
      <span>{{ refreshing ? "计算中…" : "重新计算信号" }}</span>
      <b>↗</b>
    </button>
  </section>

  <div v-if="error" class="error-banner">{{ error }}</div>
  <section class="summary-grid" :class="{ loading }">
    <article>
      <span>覆盖标的</span>
      <strong>{{ data.summary.stock_count ?? "—" }}</strong>
      <small>今日候选池</small>
    </article>
    <article>
      <span>趋势成立</span>
      <strong>{{ data.summary.bullish_count ?? "—" }}</strong>
      <small>多头结构确认</small>
    </article>
    <article>
      <span>舆情异动</span>
      <strong>{{ data.summary.hot_count ?? "—" }}</strong>
      <small>Burst ≥ 3</small>
    </article>
    <article class="accent">
      <span>平均评分</span>
      <strong>{{ data.summary.average_score ?? "—" }}</strong>
      <small>趋势 × 舆情 × 量能</small>
    </article>
  </section>

  <section class="signal-section">
    <div class="section-heading">
      <div>
        <p class="eyebrow">SIGNAL RANKING</p>
        <h2>今日信号排序</h2>
      </div>
      <div class="filters">
        <button
          v-for="filter in filters"
          :key="filter"
          :class="{ active: activeFilter === filter }"
          @click="activeFilter = filter"
        >
          {{ filter }}
        </button>
      </div>
    </div>

    <div class="signal-table">
      <div class="table-head">
        <span>标的</span><span>状态</span><span>趋势</span><span>舆情</span
        ><span>热度</span><span>综合分</span>
      </div>
      <RouterLink
        v-for="item in visibleSignals"
        :key="item.symbol"
        :to="`/stocks/${item.symbol}`"
        class="signal-row"
      >
        <div class="stock-identity">
          <b>{{ item.name }}</b>
          <small>{{ item.symbol }} · {{ item.industry }}</small>
        </div>
        <div><span class="status-pill" :class="item.status">{{ item.status }}</span></div>
        <div class="metric-cell">
          <b>{{ Math.round(item.trend_score) }}</b>
          <i><i :style="{ width: `${item.trend_score}%` }"></i></i>
        </div>
        <div class="sentiment-cell">
          <span :class="{ positive: item.metrics.sentiment > 0 }">
            {{ item.metrics.sentiment > 0 ? "+" : "" }}{{ item.metrics.sentiment.toFixed(2) }}
          </span>
          <small>{{ item.metrics.keywords.slice(0, 2).join(" · ") || "中性" }}</small>
        </div>
        <div class="burst-cell">
          <b>{{ item.burst.toFixed(1) }}×</b>
          <small>{{ item.metrics.mentions_today }} 条提及</small>
        </div>
        <ScoreRing :value="item.total_score" />
      </RouterLink>
      <div v-if="!loading && !visibleSignals.length" class="empty-state">当前筛选下没有信号</div>
    </div>
  </section>
</template>

