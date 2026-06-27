<script setup>
import { ref, onMounted, onBeforeUnmount, nextTick } from 'vue';
import { apiV2 } from '../api';
import * as echarts from 'echarts/core';
import { GraphChart } from 'echarts/charts';
import { TooltipComponent, TitleComponent, LegendComponent } from 'echarts/components';
import { SVGRenderer } from 'echarts/renderers';

echarts.use([GraphChart, TooltipComponent, TitleComponent, LegendComponent, SVGRenderer]);
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

const chartContainer = ref(null);
let chartInstance = null;
const graphNodes = ref(new Map()); // id -> node obj
const graphLinks = ref(new Map()); // id -> link obj

onMounted(() => {
  window.addEventListener('resize', handleResize);
});

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize);
  if (chartInstance) {
    chartInstance.dispose();
  }
});

function handleResize() {
  if (chartInstance) chartInstance.resize();
}

function initChart() {
  if (!chartInstance && chartContainer.value) {
    chartInstance = echarts.init(chartContainer.value, null, { renderer: 'svg' });
    chartInstance.on('click', (params) => {
      if (params.dataType === 'node') {
        expandNode(params.data.id);
      }
    });
  }
}

function updateChart() {
  if (!chartInstance) return;
  const nodes = Array.from(graphNodes.value.values());
  const links = Array.from(graphLinks.value.values());
  
  const option = {
    tooltip: {
      formatter: function (params) {
        if (params.dataType === 'node') {
          return `${params.data.name}<br/>Type: ${params.data.category}`;
        } else {
          return `${params.data.sourceName} -> ${params.data.targetName}<br/>Relation: ${params.data.label.formatter}`;
        }
      }
    },
    series: [
      {
        type: 'graph',
        layout: 'force',
        data: nodes,
        links: links,
        roam: true,
        label: {
          show: true,
          position: 'right',
          formatter: '{b}'
        },
        edgeLabel: {
          show: true,
          formatter: function (x) {
            return x.data.relationType;
          },
          fontSize: 10
        },
        force: {
          repulsion: 300,
          edgeLength: 100
        },
        itemStyle: {
          borderColor: '#fff',
          borderWidth: 2,
          shadowBlur: 10,
          shadowColor: 'rgba(0,0,0,0.3)'
        },
        lineStyle: {
          color: 'source',
          curveness: 0.2,
          width: 2
        }
      }
    ]
  };
  chartInstance.setOption(option);
}

function getColorByCategory(type) {
  const t = (type || '').toLowerCase();
  const colors = {
    'commodity': '#5470c6',
    'product': '#91cc75',
    'industry': '#fac858',
    'sector': '#fac858',
    'company': '#ee6666',
    'concept': '#73c0de'
  };
  return colors[t] || '#999';
}

async function viewGraph(entity) {
  searchResults.value = []; // Hide search results
  search.value = entity.name;
  graphNodes.value.clear();
  graphLinks.value.clear();
  
  // Add root node first so that graphNodes.size > 0, which makes the v-show container visible
  graphNodes.value.set(entity.entity_id, {
    id: entity.entity_id,
    name: entity.name,
    category: entity.entity_type,
    symbolSize: 40,
    itemStyle: { color: getColorByCategory(entity.entity_type) }
  });
  
  // Wait for the DOM to update so the container actually has dimensions
  await nextTick();
  initChart();
  if (chartInstance) {
    chartInstance.resize();
  }
  
  await expandNode(entity.entity_id);
}

async function expandNode(entityId) {
  try {
    chartInstance.showLoading();
    const res = await apiV2.getEntityNeighbors(entityId);
    if (res.success && res.data) {
      res.data.forEach(rel => {
        // Add neighbor node
        if (!graphNodes.value.has(rel.neighbor_id)) {
          graphNodes.value.set(rel.neighbor_id, {
            id: rel.neighbor_id,
            name: rel.neighbor_name,
            category: rel.neighbor_type,
            symbolSize: 20,
            itemStyle: { color: getColorByCategory(rel.neighbor_type) }
          });
        }
        
        // Add link
        const linkId = rel.relation_id;
        if (!graphLinks.value.has(linkId)) {
          graphLinks.value.set(linkId, {
            id: linkId,
            source: rel.source_entity_id,
            target: rel.target_entity_id,
            sourceName: rel.direction === 'outgoing' ? graphNodes.value.get(rel.source_entity_id)?.name : rel.neighbor_name,
            targetName: rel.direction === 'outgoing' ? rel.neighbor_name : graphNodes.value.get(rel.target_entity_id)?.name,
            relationType: rel.relation_type,
            label: { show: true, formatter: rel.relation_type }
          });
        }
      });
      updateChart();
    }
  } finally {
    chartInstance.hideLoading();
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
    
    <div class="results" v-if="searchResults.length > 0 || (loading && !search)">
      <div v-if="loading">搜索中...</div>
      <div v-else-if="searchResults.length === 0 && search" class="empty">无结果</div>
      <div v-for="entity in searchResults" :key="entity.entity_id" class="entity-card" @click="viewGraph(entity)">
        <h3>{{ entity.name }} <span class="type-badge">{{ entity.entity_type }}</span></h3>
        <span class="action-hint">点击查看图谱</span>
      </div>
    </div>

    <!-- ECharts Container -->
    <div class="graph-container" v-show="graphNodes.size > 0">
      <div class="graph-legend">
        <span>节点类型说明：</span>
        <span class="legend-item" style="color: #5470c6">● 基础商品 (commodity)</span>
        <span class="legend-item" style="color: #91cc75">● 产品 (product)</span>
        <span class="legend-item" style="color: #fac858">● 产业 (industry)</span>
        <span class="legend-item" style="color: #ee6666">● 公司 (company)</span>
        <span class="legend-item" style="color: #73c0de">● 概念 (concept)</span>
      </div>
      <div ref="chartContainer" style="width: 100%; height: 600px;"></div>
    </div>
  </div>
</template>

<style scoped>
.explorer-v2 { padding: 20px; max-width: 1200px; margin: 0 auto; display: flex; flex-direction: column; min-height: 80vh; }
.search-box { display: flex; gap: 10px; margin-bottom: 20px; }
.search-box input { flex: 1; padding: 10px; border-radius: 6px; border: 1px solid var(--border); background: var(--bg); color: var(--text); }
.search-box button { padding: 10px 20px; border-radius: 6px; cursor: pointer; }
.entity-card { background: var(--surface); padding: 15px; border-radius: 8px; border: 1px solid var(--border); margin-bottom: 10px; cursor: pointer; transition: all 0.2s; display: flex; justify-content: space-between; align-items: center; }
.entity-card:hover { border-color: var(--primary); transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,0.1); }
.type-badge { font-size: 0.8rem; background: #333; padding: 2px 6px; border-radius: 4px; margin-left: 10px; font-weight: normal; }
.action-hint { font-size: 0.85rem; color: #888; }
.graph-container { margin-top: 20px; border: 1px solid var(--border); border-radius: 8px; background: var(--surface); overflow: hidden; flex: 1; display: flex; flex-direction: column; }
.graph-legend { padding: 15px; border-bottom: 1px solid var(--border); font-size: 0.9rem; display: flex; gap: 15px; flex-wrap: wrap; }
.legend-item { display: inline-block; font-weight: bold; }

</style>
