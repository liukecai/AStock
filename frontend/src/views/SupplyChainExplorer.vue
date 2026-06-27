<script setup>
import { ref } from 'vue';
import { apiV2 } from '../api';

const search = ref('');
const searchResults = ref([]);
const loading = ref(false);

const nlQuery = ref('');
const chatLoading = ref(false);
const chatIntent = ref(null);

async function doChatQuery() {
  if (!nlQuery.value) return;
  chatLoading.value = true;
  try {
    const res = await apiV2.chatQuery(nlQuery.value);
    if (res.success) {
      chatIntent.value = res.data.intent;
      // Auto-fill normal search if entity found
      if (res.data.intent.entity_names?.length > 0) {
        search.value = res.data.intent.entity_names[0];
        doSearch();
      }
    }
  } finally {
    chatLoading.value = false;
  }
}

async function doSearch() {
  if (!search.value) return;
  loading.value = true;
  try {
    const res = await apiV2.searchEntities(search.value);
    if (res.success) {
      searchResults.value = res.data;
    }
  } finally {
    loading.value = false;
  }
}
</script>

<template>
  <div class="explorer-v2">
    <header class="page-header">
      <h1>Supply Chain Explorer</h1>
      <p>探索实体关系与产业图谱</p>
    </header>

    <div class="chat-box">
      <input v-model="nlQuery" @keyup.enter="doChatQuery" placeholder="输入自然语言查询 (如: '查询六氟化钨相关的短缺事件')" />
      <button @click="doChatQuery" :disabled="chatLoading">智能查询</button>
    </div>
    <div v-if="chatIntent" class="chat-intent">
      解析意图: <span class="badge">{{ chatIntent.event_type }}</span>
      <span v-for="entity in chatIntent.entity_names" :key="entity" class="badge entity">{{ entity }}</span>
    </div>
    
    <div class="search-box">
      <input v-model="search" @keyup.enter="doSearch" placeholder="搜索实体名称 (如: 六氟化钨)" />
      <button @click="doSearch" :disabled="loading">搜索</button>
    </div>
    
    <div class="results">
      <div v-if="loading">搜索中...</div>
      <div v-else-if="searchResults.length === 0 && search" class="empty">无结果</div>
      <div v-for="entity in searchResults" :key="entity.entity_id" class="entity-card">
        <h3>{{ entity.name }} <span class="type-badge">{{ entity.entity_type }}</span></h3>
      </div>
    </div>
  </div>
</template>

<style scoped>
.explorer-v2 { padding: 20px; max-width: 1200px; margin: 0 auto; }
.search-box { display: flex; gap: 10px; margin-bottom: 20px; }
.search-box input { flex: 1; padding: 10px; border-radius: 6px; border: 1px solid var(--border); background: var(--bg); color: var(--text); }
.search-box button { padding: 10px 20px; border-radius: 6px; }
.entity-card { background: var(--surface); padding: 15px; border-radius: 8px; border: 1px solid var(--border); margin-bottom: 10px; }
.type-badge { font-size: 0.8rem; background: #333; padding: 2px 6px; border-radius: 4px; margin-left: 10px; font-weight: normal; }
</style>
