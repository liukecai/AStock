<script setup>
import { ref, onMounted } from 'vue';
import { apiV2 } from '../api';

const events = ref([]);
const loading = ref(true);
const error = ref('');
const page = ref(1);
const hasNext = ref(false);

async function loadEvents() {
  loading.value = true;
  error.value = '';
  try {
    const res = await apiV2.getEvents(page.value);
    if (res.success) {
      events.value = res.data;
      hasNext.value = res.meta.has_next;
    } else {
      error.value = res.error?.message || '加载失败';
    }
  } catch (e) {
    error.value = e.message;
  } finally {
    loading.value = false;
  }
}

const uploadText = ref('');
const uploading = ref(false);

async function doUpload() {
  if (!uploadText.value) return;
  uploading.value = true;
  try {
    const res = await apiV2.uploadPrivateText(uploadText.value);
    if (res.success) {
      alert("提取成功并已生成私有事件！");
      uploadText.value = '';
      loadEvents(); // Reload the list
    } else {
      alert("上传失败: " + res.error?.message);
    }
  } catch (e) {
    alert("上传失败: " + e.message);
  } finally {
    uploading.value = false;
  }
}

onMounted(() => loadEvents());
</script>

<template>
  <div class="dashboard-v2">
    <header class="page-header">
      <h1>Event Dashboard</h1>
      <p>探索事件及推理影响路径</p>
    </header>

    <div class="upload-zone">
      <h3>主动知识喂入 (私有研报/纪要)</h3>
      <textarea v-model="uploadText" placeholder="粘贴一段研报文本，系统将即时提取并推理影响..." rows="3"></textarea>
      <button @click="doUpload" :disabled="uploading">{{ uploading ? '提取中...' : '提交分析' }}</button>
    </div>
    
    <div v-if="error" class="error-state">
      <h3>加载错误</h3>
      <p>{{ error }}</p>
      <button @click="loadEvents">重试</button>
    </div>
    
    <div v-else-if="loading && events.length === 0" class="loading-state skeleton">
      <!-- Skeleton loader -->
      <div v-for="i in 5" :key="i" class="skeleton-row"></div>
    </div>
    
    <div v-else-if="events.length === 0" class="empty-state">
      <p>暂无符合条件的事件</p>
    </div>
    
    <div v-else class="event-list">
      <div v-for="ev in events" :key="ev.id" class="event-card">
        <h3>{{ ev.title }}</h3>
        <div class="meta">
          <span class="badge">{{ ev.event_type }}</span>
          <span class="time">{{ ev.published_at }}</span>
          <span class="intensity" v-if="ev.intensity">强度: {{ ev.intensity.toFixed(2) }}</span>
          <span class="direction" v-if="ev.direction">方向: {{ ev.direction }}</span>
        </div>
        <p class="summary">{{ ev.summary }}</p>
      </div>
      
      <div class="pagination">
        <button :disabled="page <= 1" @click="page--; loadEvents()">上一页</button>
        <span>第 {{ page }} 页</span>
        <button :disabled="!hasNext" @click="page++; loadEvents()">下一页</button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.dashboard-v2 { padding: 20px; max-width: 1200px; margin: 0 auto; }
.page-header h1 { font-size: 1.5rem; margin-bottom: 5px; }
.page-header p { color: #888; margin-top: 0; }
.upload-zone { background: var(--surface); padding: 15px; border-radius: 8px; margin-bottom: 20px; border: 1px dashed var(--border); }
.upload-zone h3 { margin: 0 0 10px; font-size: 1rem; }
.upload-zone textarea { width: 100%; padding: 10px; background: var(--bg); color: var(--text); border: 1px solid var(--border); border-radius: 6px; margin-bottom: 10px; resize: vertical; }
.upload-zone button { padding: 8px 16px; border-radius: 4px; }
.event-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 15px;
  margin-bottom: 15px;
}
.event-card h3 { margin: 0 0 10px; font-size: 1.1rem; }
.meta { display: flex; gap: 10px; margin-bottom: 10px; font-size: 0.85rem; color: #aaa; align-items: center; }
.badge { background: #333; padding: 2px 6px; border-radius: 4px; }
.summary { font-size: 0.95rem; color: #ccc; line-height: 1.5; }
.pagination { display: flex; gap: 15px; justify-content: center; margin-top: 20px; align-items: center; }
.skeleton-row { height: 100px; background: #222; margin-bottom: 15px; border-radius: 8px; animation: pulse 1.5s infinite; }
@keyframes pulse { 0% { opacity: 0.6; } 50% { opacity: 1; } 100% { opacity: 0.6; } }
</style>
