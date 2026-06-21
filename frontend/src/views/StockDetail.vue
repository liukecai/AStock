<script setup>
import { computed, onMounted, ref, watch } from "vue";
import { useRoute } from "vue-router";
import { api } from "../api";
import PriceChart from "../components/PriceChart.vue";
import ScoreRing from "../components/ScoreRing.vue";

const route = useRoute();
const data = ref(null);
const error = ref("");
const metrics = computed(() => data.value?.signal?.metrics || {});

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
      <div v-if="data.signal" class="detail-score">
        <ScoreRing :value="data.signal.total_score" :size="72" />
        <div>
          <span>综合评分</span>
          <strong>{{ data.signal.status }}</strong>
        </div>
      </div>
    </div>

    <section class="detail-grid">
      <article class="panel chart-panel">
        <div class="panel-title">
          <div><p class="eyebrow">PRICE STRUCTURE</p><h2>价格与均线</h2></div>
          <div class="last-price">
            <small>最新收盘</small><strong>¥ {{ metrics.close }}</strong>
          </div>
        </div>
        <PriceChart :prices="data.prices" />
      </article>

      <aside class="panel factor-panel">
        <p class="eyebrow">FACTOR SNAPSHOT</p>
        <h2>因子快照</h2>
        <div class="factor">
          <span>趋势强度</span><b>{{ data.signal?.trend_score ?? "—" }}</b>
          <i><i :style="{ width: `${data.signal?.trend_score || 0}%` }"></i></i>
        </div>
        <div class="factor">
          <span>舆情得分</span><b>{{ data.signal?.sentiment_score ?? "—" }}</b>
          <i><i :style="{ width: `${data.signal?.sentiment_score || 0}%` }"></i></i>
        </div>
        <div class="factor">
          <span>量能得分</span><b>{{ data.signal?.volume_score ?? "—" }}</b>
          <i><i :style="{ width: `${data.signal?.volume_score || 0}%` }"></i></i>
        </div>
        <dl>
          <div><dt>MA 5 / 20 / 60</dt><dd>{{ metrics.ma5 }} / {{ metrics.ma20 }} / {{ metrics.ma60 }}</dd></div>
          <div><dt>20日动量</dt><dd :class="{ positive: metrics.momentum20 > 0 }">{{ (metrics.momentum20 * 100).toFixed(2) }}%</dd></div>
          <div><dt>量比</dt><dd>{{ metrics.volume_ratio }}×</dd></div>
          <div><dt>新闻热度</dt><dd>{{ data.signal?.burst }}×</dd></div>
        </dl>
      </aside>
    </section>

    <section class="panel news-panel">
      <div class="panel-title">
        <div><p class="eyebrow">INFORMATION FLOW</p><h2>近期信息流</h2></div>
        <span class="news-count">{{ data.news.length }} 条</span>
      </div>
      <div class="news-list">
        <article v-for="item in data.news" :key="item.published_at + item.title">
          <time>{{ item.published_at.slice(5, 16).replace("T", " ") }}</time>
          <div>
            <h3>
              <a
                v-if="item.url"
                :href="item.url"
                target="_blank"
                rel="noopener noreferrer"
              >{{ item.title }} ↗</a>
              <template v-else>{{ item.title }}</template>
            </h3>
            <p>
              {{ item.source }} · {{ item.event_type }} ·
              {{ item.keywords.join(" / ") || "未命中情绪词" }}
            </p>
            <p v-if="item.summary" class="news-summary">{{ item.summary }}</p>
          </div>
          <span class="news-score" :class="{ positive: item.sentiment > 0, negative: item.sentiment < 0 }">
            {{ item.sentiment > 0 ? "+" : "" }}{{ item.sentiment.toFixed(2) }}
          </span>
        </article>
      </div>
    </section>
  </template>
</template>
