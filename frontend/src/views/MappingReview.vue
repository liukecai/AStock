<script setup>
import { onMounted, ref } from "vue";
import { api } from "../api";
import { adminAuth, getAdminSecret, openAdminDialog } from "../adminAuth";

const activeTab = ref("mappings"); // mappings, linkNews
const mappings = ref([]);
const pagination = ref({ page: 1, limit: 50, total: 0, totalPages: 0 });
const filterSymbol = ref("");
const recentNews = ref([]);

const toastMessage = ref("");
const loading = ref(false);

// Form data for linking
const selectedNewsId = ref("");
const targetSymbol = ref("");
const confidence = ref(1.0);

function showToast(msg) {
  toastMessage.value = msg;
  setTimeout(() => {
    if (toastMessage.value === msg) {
      toastMessage.value = "";
    }
  }, 3000);
}

async function loadMappings() {
  loading.value = true;
  try {
    const res = await api.getNewsLinks(pagination.value.page, pagination.value.limit, filterSymbol.value);
    mappings.value = res.links || [];
    pagination.value.totalPages = res.pagination?.total_pages || 0;
    pagination.value.total = res.pagination?.total || 0;
  } catch (err) {
    showToast(`加载映射失败：${err.message}`);
  } finally {
    loading.value = false;
  }
}

async function loadRecentNews() {
  loading.value = true;
  try {
    recentNews.value = await api.getRecentNews(50);
  } catch (err) {
    showToast(`加载新闻失败：${err.message}`);
  } finally {
    loading.value = false;
  }
}

function handleTabChange(tab) {
  activeTab.value = tab;
  if (tab === "mappings") {
    pagination.value.page = 1;
    loadMappings();
  } else {
    loadRecentNews();
  }
}

async function createLink(newsId, symbol, conf) {
  if (adminAuth.required && !adminAuth.authorized) {
    openAdminDialog();
    return;
  }
  if (!symbol || symbol.length !== 6) {
    showToast("请输入有效的六位股票代码！");
    return;
  }
  try {
    await api.createNewsLink(newsId, symbol, conf, "manual", getAdminSecret());
    showToast("关联映射创建成功！");
    targetSymbol.value = "";
    selectedNewsId.value = "";
    if (activeTab.value === "mappings") {
      loadMappings();
    } else {
      loadRecentNews();
    }
  } catch (err) {
    showToast(`关联失败：${err.message}`);
  }
}

async function deleteLink(newsId, symbol) {
  if (adminAuth.required && !adminAuth.authorized) {
    openAdminDialog();
    return;
  }
  if (!confirm(`确认要删除该股票 (${symbol}) 与新闻的映射关系吗？`)) {
    return;
  }
  try {
    await api.deleteNewsLink(newsId, symbol, getAdminSecret());
    showToast("映射删除成功！");
    loadMappings();
  } catch (err) {
    showToast(`删除映射失败：${err.message}`);
  }
}

async function updateConfidence(newsId, symbol, currentConf) {
  if (adminAuth.required && !adminAuth.authorized) {
    openAdminDialog();
    return;
  }
  const newConfStr = prompt("请输入新的置信度 (0.0 - 1.0):", currentConf);
  if (newConfStr === null) return;
  const newConf = parseFloat(newConfStr);
  if (isNaN(newConf) || newConf < 0 || newConf > 1) {
    showToast("请输入 0.0 到 1.0 之间的有效数字！");
    return;
  }
  try {
    await api.createNewsLink(newsId, symbol, newConf, "manual", getAdminSecret());
    showToast("置信度更新成功！");
    loadMappings();
  } catch (err) {
    showToast(`更新置信度失败：${err.message}`);
  }
}

function changePage(delta) {
  const newPage = pagination.value.page + delta;
  if (newPage >= 1 && newPage <= pagination.value.totalPages) {
    pagination.value.page = newPage;
    loadMappings();
  }
}

function openLinkForm(newsId) {
  selectedNewsId.value = selectedNewsId.value === newsId ? "" : newsId;
  targetSymbol.value = "";
  confidence.value = 1.0;
}

onMounted(() => {
  loadMappings();
});
</script>

<template>
  <div class="review-header">
    <p class="eyebrow">MAPPING AUDIT DESK</p>
    <h1>实体映射审查与校准</h1>
  </div>

  <div class="review-tabs">
    <button :class="{ active: activeTab === 'mappings' }" @click="handleTabChange('mappings')">
      已建映射关系审计
    </button>
    <button :class="{ active: activeTab === 'linkNews' }" @click="handleTabChange('linkNews')">
      近期新闻关联录入
    </button>
  </div>

  <!-- Tab 1: Mappings Audit -->
  <div v-if="activeTab === 'mappings'">
    <div class="review-form">
      <div class="form-group">
        <label>按股票代码筛选</label>
        <input
          v-model="filterSymbol"
          placeholder="例如: 600519"
          maxlength="6"
          @keyup.enter="pagination.page = 1; loadMappings()"
        />
      </div>
      <button class="btn" @click="pagination.page = 1; loadMappings()">筛选 / 查询</button>
      <button class="btn btn-secondary" @click="filterSymbol = ''; pagination.page = 1; loadMappings()">
        清空重置
      </button>
    </div>

    <div v-if="loading" class="page-loader">正在加载映射列表...</div>
    <div v-else class="review-table">
      <div class="review-row" style="border-bottom: 2px solid var(--line); font-weight: bold; color: #61736c; font-size: 11px;">
        <span>新闻标题 / 来源 / 发布时间</span>
        <span>匹配股票</span>
        <span>置信度</span>
        <span>匹配类型</span>
        <span style="text-align: right">操作项</span>
      </div>
      <div v-for="item in mappings" :key="item.news_id + '-' + item.symbol" class="review-row">
        <div class="review-row-news">
          <h4>{{ item.title }}</h4>
          <p>{{ item.source }} · {{ item.published_at.slice(5, 16).replace('T', ' ') }}</p>
        </div>
        <div>
          <b style="color: var(--lime)">{{ item.symbol }}</b>
        </div>
        <div class="review-row-confidence">{{ item.confidence.toFixed(2) }}</div>
        <div>
          <span class="review-row-type">{{ item.match_type }}</span>
        </div>
        <div class="review-row-actions">
          <button class="btn btn-secondary btn-sm" @click="updateConfidence(item.news_id, item.symbol, item.confidence)">
            修改权重
          </button>
          <button class="btn btn-danger btn-sm" @click="deleteLink(item.news_id, item.symbol)">
            断开关联
          </button>
        </div>
      </div>
      <div v-if="!mappings.length" class="empty-state">暂无符合条件的映射关联数据</div>
      <div v-if="pagination.totalPages > 1" class="pagination">
        <button :disabled="pagination.page <= 1" @click="changePage(-1)">上一页</button>
        <span class="page-info">第 {{ pagination.page }} 页 / 共 {{ pagination.totalPages }} 页 (共 {{ pagination.total }} 条)</span>
        <button :disabled="pagination.page >= pagination.totalPages" @click="changePage(1)">下一页</button>
      </div>
    </div>
  </div>

  <!-- Tab 2: Recent News Association -->
  <div v-if="activeTab === 'linkNews'">
    <div v-if="loading" class="page-loader">正在读取近期新闻...</div>
    <div v-else class="review-table">
      <div class="review-row" style="border-bottom: 2px solid var(--line); font-weight: bold; color: #61736c; font-size: 11px;">
        <span>新闻标题 / 来源 / 发布时间</span>
        <span style="grid-column: span 3; text-align: right">关联操作</span>
      </div>
      <template v-for="item in recentNews" :key="item.id">
        <div class="review-row">
          <div class="review-row-news" style="grid-column: span 4">
            <h4>{{ item.title }}</h4>
            <p>{{ item.source }} · {{ item.published_at.slice(5, 16).replace('T', ' ') }}</p>
            <small style="color: #63756e; font-size: 10px; display: block; margin-top: 4px;">ID: {{ item.id }}</small>
          </div>
          <div class="review-row-actions">
            <button class="btn btn-sm" @click="openLinkForm(item.id)">
              {{ selectedNewsId === item.id ? "取消" : "手动绑定股票" }}
            </button>
          </div>
        </div>
        <!-- Expandable Form for creating a link -->
        <div v-if="selectedNewsId === item.id" class="review-form" style="margin: 0; border-top: 0; border-bottom: 1px solid var(--line); background: var(--surface-2); padding: 16px 24px;">
          <div class="form-group">
            <label>股票代码 (6位)</label>
            <input v-model="targetSymbol" placeholder="例如: 600519" maxlength="6" />
          </div>
          <div class="form-group">
            <label>初始置信度 (0.0 - 1.0)</label>
            <input v-model="confidence" type="number" min="0" max="1" step="0.1" />
          </div>
          <button class="btn btn-sm" @click="createLink(item.id, targetSymbol, confidence)">
            确定关联
          </button>
        </div>
      </template>
      <div v-if="!recentNews.length" class="empty-state">最近 24 小时没有爬取到新闻</div>
    </div>
  </div>

  <!-- Toast Notification System -->
  <div v-if="toastMessage" class="toast-msg">{{ toastMessage }}</div>
</template>
