<script setup>
import { computed, onMounted, ref } from "vue";
import { api } from "../api";

const loading = ref(false);
const rebuilding = ref(false);
const events = ref([]);
const totalEvents = ref(0);
const page = ref(1);
const limit = ref(15);
const totalPages = ref(0);
const selectedEvent = ref(null);
const error = ref("");
const successMsg = ref("");

// Filters
const activeCommodity = ref("");
const activeType = ref("");
const activeDirection = ref("");

const commodities = [
  { value: "", label: "全部商品" },
  { value: "tungsten", label: "钨" },
  { value: "WF6", label: "六氟化钨" },
  { value: "oil", label: "原油/石油" },
  { value: "copper", label: "铜" },
  { value: "gold", label: "黄金" },
  { value: "lithium", label: "锂" },
];

const eventTypes = [
  { value: "", label: "全部事件" },
  { value: "geo_conflict", label: "地缘冲突" },
  { value: "supply_shock", label: "供应冲击" },
  { value: "policy_change", label: "政策变化" },
  { value: "disruption", label: "意外中断" },
];

const directions = [
  { value: "", label: "全部方向" },
  { value: "benefit", label: "受益" },
  { value: "harm", label: "受损" },
];

// Instant analysis form
const formTitle = ref("");
const formSummary = ref("");
const formTime = ref(new Date().toISOString().slice(0, 19));
const analyzing = ref(false);

async function loadEvents() {
  loading.value = true;
  try {
    const res = await api.getEvents(
      page.value,
      limit.value,
      activeCommodity.value,
      activeType.value,
      activeDirection.value
    );
    events.value = res.events || [];
    totalPages.value = res.pagination?.total_pages || 0;
    totalEvents.value = res.pagination?.total || 0;
    
    // Select first event if none selected
    if (events.value.length > 0 && !selectedEvent.value) {
      await selectEvent(events.value[0].id);
    }
  } catch (err) {
    error.value = "加载事件失败: " + err.message;
  } finally {
    loading.value = false;
  }
}

async function selectEvent(id) {
  try {
    const detail = await api.getEvent(id);
    selectedEvent.value = detail;
  } catch (err) {
    error.value = "获取事件详情失败: " + err.message;
  }
}

async function handleAnalyze() {
  if (!formTitle.value.trim()) {
    error.value = "新闻标题不能为空";
    return;
  }
  error.value = "";
  analyzing.value = true;
  try {
    const res = await api.analyzeEvent(
      formTitle.value,
      formSummary.value,
      formTime.value
    );
    successMsg.value = "分析成功并存入数据库！";
    setTimeout(() => (successMsg.value = ""), 3000);
    formTitle.value = "";
    formSummary.value = "";
    // Reload and select this new event
    await loadEvents();
    if (res && res.id) {
      await selectEvent(res.id);
    }
  } catch (err) {
    error.value = "事件分析失败: " + err.message;
  } finally {
    analyzing.value = false;
  }
}

async function handleRebuild() {
  if (!confirm("确定要对系统中所有已有新闻重新运行事件提取与量化打分吗？此操作将重建事件索引。")) {
    return;
  }
  rebuilding.value = true;
  error.value = "";
  try {
    const res = await api.rebuildEvents();
    successMsg.value = `批量重建完成：已处理 ${res.processed} 条新闻，生成 ${res.events_created} 个商品事件。`;
    page.value = 1;
    selectedEvent.value = null;
    await loadEvents();
  } catch (err) {
    error.value = "批量重建失败: " + err.message;
  } finally {
    rebuilding.value = false;
  }
}

function setCommodity(val) {
  activeCommodity.value = val;
  page.value = 1;
  loadEvents();
}

function setType(val) {
  activeType.value = val;
  page.value = 1;
  loadEvents();
}

function setDirection(val) {
  activeDirection.value = val;
  page.value = 1;
  loadEvents();
}

function changePage(delta) {
  const newPage = page.value + delta;
  if (newPage >= 1 && newPage <= totalPages.value) {
    page.value = newPage;
    loadEvents();
  }
}

// Grouped stocks
const benefitedStocks = computed(() => {
  if (!selectedEvent.value?.stock_scores) return [];
  return selectedEvent.value.stock_scores.filter(s => s.direction === "benefit");
});

const harmedStocks = computed(() => {
  if (!selectedEvent.value?.stock_scores) return [];
  return selectedEvent.value.stock_scores.filter(s => s.direction === "harm");
});

function getCommodityLabel(val) {
  const matched = commodities.find(c => c.value === val);
  return matched ? matched.label : val;
}

function getEventTypeLabel(val) {
  const matched = eventTypes.find(e => e.value === val);
  return matched ? matched.label : val;
}

onMounted(loadEvents);
</script>

<template>
  <section class="hero">
    <div>
      <p class="eyebrow">EVENT-DRIVEN QUANT SYSTEM</p>
      <h1>新闻驱动，<br /><em>追踪显式因果链。</em></h1>
      <p class="hero-copy">
        通过知识库与事件映射规则，建立“新闻事件 → 商品冲击 → 产业链传导 → A股板块 → 股票暴露评分”的显式逻辑证据链。
      </p>
    </div>
    <button class="refresh-button" :disabled="rebuilding" @click="handleRebuild">
      <span>{{ rebuilding ? "正在重建索引…" : "批量重建历史事件" }}</span>
      <b>↗</b>
    </button>
  </section>

  <div v-if="error" class="error-banner">{{ error }}</div>
  <div v-if="successMsg" class="success-banner">{{ successMsg }}</div>

  <div class="events-container">
    <!-- Left Column: Controls & History -->
    <div class="left-panel">
      <!-- Instant Analysis Panel -->
      <div class="panel card">
        <h3 class="panel-title">即时分析新闻</h3>
        <form @submit.prevent="handleAnalyze" class="analysis-form">
          <div class="form-group">
            <label for="news-title">新闻标题 *</label>
            <input
              id="news-title"
              v-model="formTitle"
              type="text"
              placeholder="例如：六氟化钨现货吃紧，价格上涨..."
              required
            />
          </div>
          <div class="form-group">
            <label for="news-summary">摘要/内容</label>
            <textarea
              id="news-summary"
              v-model="formSummary"
              rows="3"
              placeholder="可选填详细新闻正文或关键词..."
            ></textarea>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label for="news-time">发布时间</label>
              <input id="news-time" v-model="formTime" type="text" />
            </div>
            <button type="submit" class="submit-btn" :disabled="analyzing">
              {{ analyzing ? "分析中..." : "触发分析" }}
            </button>
          </div>
        </form>
      </div>

      <!-- Events List Panel -->
      <div class="panel card list-card">
        <div class="panel-header">
          <h3 class="panel-title">历史分析事件 ({{ totalEvents }} 个)</h3>
          
          <!-- Filters -->
          <div class="filter-bar">
            <div class="select-wrapper">
              <select :value="activeCommodity" aria-label="筛选商品" @change="e => setCommodity(e.target.value)">
                <option v-for="c in commodities" :key="c.value" :value="c.value">
                  {{ c.label }}
                </option>
              </select>
            </div>
            <div class="select-wrapper">
              <select :value="activeType" aria-label="筛选类型" @change="e => setType(e.target.value)">
                <option v-for="t in eventTypes" :key="t.value" :value="t.value">
                  {{ t.label }}
                </option>
              </select>
            </div>
            <div class="select-wrapper">
              <select :value="activeDirection" aria-label="筛选影响" @change="e => setDirection(e.target.value)">
                <option v-for="d in directions" :key="d.value" :value="d.value">
                  {{ d.label }}
                </option>
              </select>
            </div>
          </div>
        </div>

        <div class="events-list">
          <div
            v-for="ev in events"
            :key="ev.id"
            class="event-item"
            :class="{ active: selectedEvent?.id === ev.id }"
            @click="selectEvent(ev.id)"
          >
            <div class="event-meta">
              <span class="badge type-badge" :class="ev.event_type">
                {{ getEventTypeLabel(ev.event_type) }}
              </span>
              <span class="badge comm-badge" v-for="c in ev.commodity_impacts" :key="c.commodity">
                {{ getCommodityLabel(c.commodity) }} · {{ c.impact_type === 'supply_shortage' ? '短缺' : c.impact_type === 'supply_disruption' ? '中断' : '政策' }}
              </span>
            </div>
            <h4 class="event-title">{{ ev.title }}</h4>
            <span class="event-date">{{ ev.published_at.slice(0, 16).replace('T', ' ') }}</span>
          </div>
          <div v-if="!loading && !events.length" class="empty-state">未找到匹配的事件</div>
        </div>

        <!-- Pagination -->
        <div v-if="totalPages > 1" class="list-pagination">
          <button :disabled="page <= 1" @click="changePage(-1)">上一页</button>
          <span>{{ page }} / {{ totalPages }}</span>
          <button :disabled="page >= totalPages" @click="changePage(1)">下一页</button>
        </div>
      </div>
    </div>

    <!-- Right Column: Detail & Causal Chain -->
    <div class="right-panel">
      <div v-if="selectedEvent" class="card detail-card">
        <!-- Event Detail Header -->
        <div class="detail-header">
          <div class="detail-meta">
            <span class="badge type-badge" :class="selectedEvent.event_type">
              {{ getEventTypeLabel(selectedEvent.event_type) }}
            </span>
            <span class="time-meta">{{ selectedEvent.published_at.replace('T', ' ').slice(0, 19) }}</span>
          </div>
          <h2>{{ selectedEvent.title }}</h2>
          <p class="summary-text" v-if="selectedEvent.summary">{{ selectedEvent.summary }}</p>
        </div>

        <!-- Visual Causal Chain -->
        <div class="causal-chain-panel">
          <h4 class="section-title">显式因果传导链</h4>
          <div class="causal-nodes">
            <!-- Node 1: Event -->
            <div class="causal-node node-event">
              <div class="node-icon">📢</div>
              <div class="node-body">
                <h5>新闻事件</h5>
                <p>{{ getEventTypeLabel(selectedEvent.event_type) }} (强度: {{ selectedEvent.intensity.toFixed(2) }})</p>
              </div>
            </div>
            <div class="node-connector">↓</div>

            <!-- Node 2: Commodity Impact -->
            <div class="causal-node node-commodity">
              <div class="node-icon">⛏️</div>
              <div class="node-body" v-for="impact in selectedEvent.commodity_impacts" :key="impact.commodity">
                <h5>商品冲击</h5>
                <p>{{ getCommodityLabel(impact.commodity) }} ({{ impact.impact_type }})</p>
              </div>
            </div>
            <div class="node-connector">↓</div>

            <!-- Node 3: Sectors -->
            <div class="causal-node node-sectors">
              <div class="node-icon">🏭</div>
              <div class="node-body">
                <h5>产业链环节</h5>
                <p>上游开采加工商受益 / 下游终端制造商承压成本</p>
              </div>
            </div>
          </div>
        </div>

        <!-- Stock Rankings tabs/lists -->
        <div class="stocks-impact-section">
          <h4 class="section-title">A股股票影响评分</h4>
          
          <div class="impact-columns">
            <!-- Benefited Stocks -->
            <div class="impact-col positive-col">
              <h5 class="col-title benefit-title">📈 受益标的排名</h5>
              <div class="stock-list-scores">
                <div v-for="stock in benefitedStocks" :key="stock.symbol" class="stock-score-card">
                  <div class="score-card-header">
                    <div class="stock-info">
                      <RouterLink :to="`/stocks/${stock.symbol}`" class="stock-name-link">
                        <strong>{{ stock.name }}</strong>
                      </RouterLink>
                      <small>{{ stock.symbol }} · {{ stock.industry }}</small>
                    </div>
                    <div class="total-score-badge benefit-badge">
                      {{ stock.event_score.toFixed(1) }} 分
                    </div>
                  </div>
                  
                  <!-- Breakdown Progress Bars -->
                  <div class="score-breakdown">
                    <div class="breakdown-item">
                      <span>事件冲击 (50%)</span>
                      <div class="progress-bar">
                        <span class="val">{{ stock.event_impact.toFixed(1) }}</span>
                        <div class="progress-fill fill-impact" :style="{ width: `${stock.event_impact}%` }"></div>
                      </div>
                    </div>
                    <div class="breakdown-item">
                      <span>行业暴露 (30%)</span>
                      <div class="progress-bar">
                        <span class="val">{{ stock.sector_exposure.toFixed(1) }}</span>
                        <div class="progress-fill fill-exposure" :style="{ width: `${stock.sector_exposure}%` }"></div>
                      </div>
                    </div>
                    <div class="breakdown-item">
                      <span>趋势强度 (20%)</span>
                      <div class="progress-bar">
                        <span class="val">{{ stock.trend_strength.toFixed(1) }}</span>
                        <div class="progress-fill fill-trend" :style="{ width: `${stock.trend_strength}%` }"></div>
                      </div>
                    </div>
                  </div>
                  
                  <p class="evidence-text">{{ stock.evidence }}</p>
                </div>
                <div v-if="!benefitedStocks.length" class="empty-col-state">暂无受益标的</div>
              </div>
            </div>

            <!-- Harmed Stocks -->
            <div class="impact-col negative-col">
              <h5 class="col-title harm-title">📉 受损标的排名</h5>
              <div class="stock-list-scores">
                <div v-for="stock in harmedStocks" :key="stock.symbol" class="stock-score-card harm-card">
                  <div class="score-card-header">
                    <div class="stock-info">
                      <RouterLink :to="`/stocks/${stock.symbol}`" class="stock-name-link">
                        <strong>{{ stock.name }}</strong>
                      </RouterLink>
                      <small>{{ stock.symbol }} · {{ stock.industry }}</small>
                    </div>
                    <div class="total-score-badge harm-badge">
                      {{ stock.event_score.toFixed(1) }} 分
                    </div>
                  </div>
                  
                  <!-- Breakdown Progress Bars -->
                  <div class="score-breakdown">
                    <div class="breakdown-item">
                      <span>事件冲击 (50%)</span>
                      <div class="progress-bar">
                        <span class="val">{{ stock.event_impact.toFixed(1) }}</span>
                        <div class="progress-fill fill-impact" :style="{ width: `${stock.event_impact}%` }"></div>
                      </div>
                    </div>
                    <div class="breakdown-item">
                      <span>行业暴露 (30%)</span>
                      <div class="progress-bar">
                        <span class="val">{{ stock.sector_exposure.toFixed(1) }}</span>
                        <div class="progress-fill fill-exposure" :style="{ width: `${stock.sector_exposure}%` }"></div>
                      </div>
                    </div>
                    <div class="breakdown-item">
                      <span>趋势强度 (20%)</span>
                      <div class="progress-bar">
                        <span class="val">{{ stock.trend_strength.toFixed(1) }}</span>
                        <div class="progress-fill fill-trend" :style="{ width: `${stock.trend_strength}%` }"></div>
                      </div>
                    </div>
                  </div>
                  
                  <p class="evidence-text">{{ stock.evidence }}</p>
                </div>
                <div v-if="!harmedStocks.length" class="empty-col-state">暂无受损标的</div>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <div v-else class="card empty-detail">
        <div class="empty-detail-content">
          <span>🔍</span>
          <p>在左侧选择或输入分析一个新闻事件，<br />查看其完整的产业链映射关系及量化暴露评分排名。</p>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.events-container {
  display: grid;
  grid-template-columns: 420px 1fr;
  gap: 24px;
  align-items: start;
  margin-top: 24px;
}

@media (max-width: 1000px) {
  .events-container {
    grid-template-columns: 1fr;
  }
}

.card {
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: 8px;
  padding: 24px;
  margin-bottom: 24px;
}

.panel-title {
  margin: 0 0 16px;
  font-size: 16px;
  font-weight: 600;
  color: var(--text);
  border-bottom: 1px solid var(--line);
  padding-bottom: 10px;
}

.analysis-form {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.form-group label {
  font-size: 11px;
  color: var(--muted);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.form-group input,
.form-group textarea,
.filter-bar select {
  background: var(--surface-2);
  border: 1px solid var(--line);
  color: var(--text);
  border-radius: 4px;
  padding: 10px 12px;
  font-size: 13px;
  outline: none;
  transition: border-color 0.2s;
}

.form-group input:focus,
.form-group textarea:focus {
  border-color: var(--lime);
}

.form-row {
  display: grid;
  grid-template-columns: 1.2fr 1fr;
  gap: 12px;
  align-items: end;
}

.submit-btn {
  background: var(--lime);
  color: #07100e;
  font-weight: 700;
  border: 0;
  border-radius: 4px;
  height: 38px;
  cursor: pointer;
  transition: opacity 0.2s;
}

.submit-btn:hover {
  opacity: 0.9;
}

.submit-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.panel-header {
  border-bottom: 1px solid var(--line);
  padding-bottom: 12px;
  margin-bottom: 16px;
}

.filter-bar {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
  margin-top: 10px;
}

.select-wrapper select {
  width: 100%;
  padding: 6px 10px;
  font-size: 11px;
  cursor: pointer;
}

.events-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
  max-height: 500px;
  overflow-y: auto;
}

.event-item {
  padding: 14px;
  border-radius: 6px;
  border: 1px solid transparent;
  background: rgba(255, 255, 255, 0.02);
  cursor: pointer;
  transition: all 0.2s;
}

.event-item:hover {
  background: rgba(255, 255, 255, 0.05);
  border-color: rgba(209, 235, 224, 0.1);
}

.event-item.active {
  background: rgba(200, 255, 92, 0.05);
  border-color: var(--lime);
}

.event-meta {
  display: flex;
  gap: 6px;
  margin-bottom: 8px;
}

.badge {
  font-size: 10px;
  padding: 2px 6px;
  border-radius: 3px;
  font-weight: 500;
}

.type-badge {
  background: rgba(128, 146, 139, 0.15);
  color: #c0d0c9;
}

.type-badge.geo_conflict {
  background: rgba(255, 133, 133, 0.15);
  color: #ff8585;
}

.type-badge.supply_shock {
  background: rgba(245, 164, 93, 0.15);
  color: var(--orange);
}

.type-badge.policy_change {
  background: rgba(200, 255, 92, 0.12);
  color: var(--lime);
}

.comm-badge {
  border: 1px solid rgba(200, 255, 92, 0.3);
  color: var(--lime);
  background: rgba(200, 255, 92, 0.05);
}

.event-title {
  margin: 0 0 8px;
  font-size: 13px;
  font-weight: 500;
  line-height: 1.4;
  color: var(--text);
}

.event-date {
  font-size: 11px;
  color: var(--muted);
}

.list-pagination {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 16px;
  padding-top: 12px;
  border-top: 1px solid var(--line);
  font-size: 12px;
}

.list-pagination button {
  background: transparent;
  border: 1px solid var(--line);
  color: var(--text);
  padding: 4px 10px;
  border-radius: 4px;
  cursor: pointer;
}

.list-pagination button:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.detail-card {
  padding: 32px;
}

.detail-header h2 {
  margin: 12px 0;
  font-size: 22px;
  line-height: 1.3;
}

.detail-meta {
  display: flex;
  align-items: center;
  gap: 12px;
}

.time-meta {
  font-size: 12px;
  color: var(--muted);
}

.summary-text {
  font-size: 14px;
  color: #a0b2aa;
  line-height: 1.6;
  background: rgba(255, 255, 255, 0.01);
  padding: 14px;
  border-left: 2px solid var(--line);
  margin-top: 12px;
}

.section-title {
  font-size: 14px;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: var(--lime);
  margin: 28px 0 16px;
  border-bottom: 1px solid var(--line);
  padding-bottom: 8px;
}

.causal-nodes {
  display: flex;
  flex-direction: column;
  align-items: center;
  background: rgba(0,0,0,0.15);
  border-radius: 8px;
  padding: 20px;
  border: 1px solid var(--line);
}

.causal-node {
  display: flex;
  align-items: center;
  gap: 14px;
  background: var(--surface-2);
  border: 1px solid var(--line);
  border-radius: 6px;
  padding: 12px 18px;
  width: 100%;
  max-width: 440px;
}

.node-icon {
  font-size: 22px;
}

.node-body h5 {
  margin: 0 0 4px;
  font-size: 12px;
  color: var(--muted);
}

.node-body p {
  margin: 0;
  font-size: 13px;
  font-weight: 500;
}

.node-connector {
  font-size: 18px;
  color: var(--line);
  margin: 6px 0;
  font-weight: bold;
}

.impact-columns {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}

@media (max-width: 900px) {
  .impact-columns {
    grid-template-columns: 1fr;
  }
}

.col-title {
  font-size: 14px;
  margin: 0 0 14px;
  font-weight: 600;
  padding-bottom: 6px;
  border-bottom: 1px solid var(--line);
}

.benefit-title {
  color: var(--lime);
}

.harm-title {
  color: #ff8585;
}

.stock-list-scores {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.stock-score-card {
  background: rgba(200, 255, 92, 0.02);
  border: 1px solid rgba(200, 255, 92, 0.15);
  border-radius: 6px;
  padding: 16px;
}

.stock-score-card.harm-card {
  background: rgba(255, 133, 133, 0.01);
  border: 1px solid rgba(255, 133, 133, 0.15);
}

.score-card-header {
  display: flex;
  justify-content: space-between;
  align-items: start;
  margin-bottom: 14px;
}

.stock-info {
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.stock-name-link {
  color: var(--text);
  font-size: 14px;
}

.stock-name-link:hover {
  color: var(--lime);
  text-decoration: underline;
}

.stock-info small {
  font-size: 11px;
  color: var(--muted);
}

.total-score-badge {
  font-size: 13px;
  font-weight: 700;
  padding: 4px 8px;
  border-radius: 4px;
}

.benefit-badge {
  background: rgba(200, 255, 92, 0.12);
  color: var(--lime);
  border: 1px solid rgba(200, 255, 92, 0.3);
}

.harm-badge {
  background: rgba(255, 133, 133, 0.12);
  color: #ff8585;
  border: 1px solid rgba(255, 133, 133, 0.3);
}

.score-breakdown {
  display: flex;
  flex-direction: column;
  gap: 8px;
  background: rgba(0,0,0,0.12);
  padding: 10px;
  border-radius: 4px;
  margin-bottom: 10px;
}

.breakdown-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 11px;
  color: var(--muted);
}

.progress-bar {
  position: relative;
  width: 120px;
  height: 6px;
  background: #172420;
  border-radius: 3px;
  overflow: visible;
}

.progress-bar .val {
  position: absolute;
  right: 128px;
  top: -4px;
  font-size: 10px;
  color: var(--text);
  font-weight: bold;
}

.progress-fill {
  height: 100%;
  border-radius: 3px;
}

.fill-impact { background: #f5a45d; }
.fill-exposure { background: #5dbcf5; }
.fill-trend { background: var(--lime); }

.evidence-text {
  font-size: 11px;
  color: #8fa098;
  margin: 8px 0 0;
  line-height: 1.5;
}

.empty-col-state {
  text-align: center;
  padding: 30px;
  color: var(--muted);
  font-size: 12px;
  border: 1px dashed var(--line);
  border-radius: 4px;
}

.empty-detail {
  display: grid;
  place-items: center;
  min-height: 400px;
}

.empty-detail-content {
  text-align: center;
  color: var(--muted);
}

.empty-detail-content span {
  font-size: 48px;
  display: block;
  margin-bottom: 16px;
}

.success-banner {
  padding: 12px 18px;
  border: 1px solid #3d8c47;
  background: #153219;
  color: #a3ffa8;
  margin-bottom: 22px;
  border-radius: 5px;
  font-size: 13px;
}
</style>
