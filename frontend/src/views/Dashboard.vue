<script setup>
import { computed, onMounted, ref } from "vue";
import { api } from "../api";
import SignalListRow from "../components/SignalListRow.vue";

const data = ref({ signals: [], summary: {} });
const loading = ref(true);
const refreshing = ref(false);
const error = ref("");
const activeFilter = ref("全部");
const activeBoard = ref("全部");

const page = ref(1);
const limit = ref(10);
const jumpPage = ref("");
const totalPages = ref(0);
const totalSignals = ref(0);
const pageSizes = [10, 20, 50, 100];

const filters = ["全部", "主升浪信号", "趋势股", "观察"];
const boardFilters = ["全部", "沪A", "深A", "创业板", "科创板"];
const visibleSignals = computed(() => data.value.signals || []);

async function load() {
  loading.value = true;
  try {
    const res = await api.dashboard(
      page.value,
      limit.value,
      activeFilter.value,
      activeBoard.value
    );
    data.value = res;
    totalPages.value = res.pagination?.total_pages || 0;
    totalSignals.value = res.pagination?.total || 0;
  } catch (err) {
    error.value = err.message;
  } finally {
    loading.value = false;
  }
}

function setFilter(filter) {
  activeFilter.value = filter;
  page.value = 1;
  load();
}

function setBoard(board) {
  activeBoard.value = board;
  page.value = 1;
  load();
}

function changePage(delta) {
  const newPage = page.value + delta;
  if (newPage >= 1 && newPage <= totalPages.value) {
    page.value = newPage;
    jumpPage.value = "";
    load();
  }
}

function changePageSize() {
  page.value = 1;
  jumpPage.value = "";
  load();
}

function goToPage() {
  const target = Number.parseInt(jumpPage.value, 10);
  if (!Number.isInteger(target) || target < 1 || target > totalPages.value) {
    jumpPage.value = "";
    return;
  }
  if (target !== page.value) {
    page.value = target;
    load();
  }
  jumpPage.value = "";
}

async function refresh() {
  refreshing.value = true;
  try {
    await api.runPipeline();
    page.value = 1;
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
          <small>新闻热度 Z ≥ 3</small>
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
      <div class="filter-groups">
        <div class="filter-group">
          <span>信号</span>
          <div class="filters">
            <button
              v-for="filter in filters"
              :key="filter"
              :class="{ active: activeFilter === filter }"
              @click="setFilter(filter)"
            >
              {{ filter }}
            </button>
          </div>
        </div>
        <div class="filter-group">
          <span>板块</span>
          <div class="filters">
            <button
              v-for="board in boardFilters"
              :key="board"
              :class="{ active: activeBoard === board }"
              @click="setBoard(board)"
            >
              {{ board }}
            </button>
          </div>
        </div>
      </div>
    </div>

    <div class="signal-table">
      <div class="table-head">
        <span>标的</span><span>状态</span><span>趋势</span><span>舆情</span
        ><span>研究权重</span><span>综合分</span>
      </div>
      <SignalListRow
        v-for="item in visibleSignals"
        :key="item.symbol"
        :item="item"
      />
      <div v-if="!loading && !visibleSignals.length" class="empty-state">当前筛选下没有信号</div>
      <div v-if="totalSignals > 0" class="pagination">
        <div class="page-size">
          <span>每页</span>
          <select v-model.number="limit" aria-label="每页数量" @change="changePageSize">
            <option v-for="size in pageSizes" :key="size" :value="size">{{ size }} 条</option>
          </select>
        </div>
        <div class="page-controls">
          <button :disabled="page <= 1" @click="changePage(-1)">上一页</button>
          <span class="page-info">第 {{ page }} / {{ totalPages }} 页 · 共 {{ totalSignals }} 条</span>
          <button :disabled="page >= totalPages" @click="changePage(1)">下一页</button>
        </div>
        <form class="page-jump" @submit.prevent="goToPage">
          <span>跳至</span>
          <input
            v-model="jumpPage"
            type="number"
            inputmode="numeric"
            min="1"
            :max="totalPages"
            aria-label="跳转页码"
            placeholder="页码"
          />
          <button type="submit">跳转</button>
        </form>
      </div>
    </div>
  </section>
</template>
