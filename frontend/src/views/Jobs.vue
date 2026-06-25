<template>
  <div class="jobs-page">
    <div class="jobs-header">
      <div class="jobs-title-group">
        <h1 class="jobs-title">
          <span class="title-icon">⚡</span>
          任务中心
        </h1>
        <p class="jobs-subtitle">调度任务状态监控 · 失败告警 · 手动触发</p>
      </div>
      <div class="header-actions">
        <div class="refresh-indicator" :class="{ spinning: isRefreshing }">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="23 4 23 10 17 10"></polyline>
            <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"></path>
          </svg>
        </div>
        <span class="last-updated" v-if="lastUpdated">{{ lastUpdated }}</span>
      </div>
    </div>

    <!-- Summary pills -->
    <div class="summary-bar">
      <div class="summary-pill" :class="{ active: statusFilter === '' }" @click="statusFilter = ''">
        全部 <span class="count">{{ jobs.length }}</span>
      </div>
      <div class="summary-pill success" :class="{ active: statusFilter === 'success' }" @click="statusFilter = 'success'">
        ✅ 成功 <span class="count">{{ statusCounts.success }}</span>
      </div>
      <div class="summary-pill running" :class="{ active: statusFilter === 'running' }" @click="statusFilter = 'running'">
        🔄 运行中 <span class="count">{{ statusCounts.running }}</span>
      </div>
      <div class="summary-pill failed" :class="{ active: statusFilter === 'failed' }" @click="statusFilter = 'failed'">
        ❌ 失败 <span class="count">{{ statusCounts.failed }}</span>
      </div>
    </div>

    <!-- Error state -->
    <div v-if="error" class="error-banner">
      <span class="error-icon">⚠️</span>
      {{ error }}
    </div>

    <!-- Empty state -->
    <div v-if="!isLoading && filteredJobs.length === 0 && !error" class="empty-state">
      <div class="empty-icon">📋</div>
      <p>暂无任务记录</p>
      <small>调度任务运行后将在此显示状态</small>
    </div>

    <!-- Jobs list -->
    <div class="jobs-list" v-if="filteredJobs.length > 0">
      <transition-group name="job-card">
        <div
          v-for="job in filteredJobs"
          :key="job.name"
          class="job-card"
          :class="[`status-${job.status}`, { expanded: expandedJobs.has(job.name) }]"
        >
          <!-- Card header -->
          <div class="job-card-header" @click="toggleExpand(job)">
            <div class="job-status-badge" :class="job.status">
              <span class="badge-dot"></span>
              {{ statusLabel(job.status) }}
            </div>

            <div class="job-main-info">
              <div class="job-name">{{ displayName(job.name) }}</div>
              <div class="job-meta">
                <span class="meta-item" v-if="job.finished_at">
                  <svg class="meta-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <circle cx="12" cy="12" r="10"></circle>
                    <polyline points="12 6 12 12 16 14"></polyline>
                  </svg>
                  {{ formatTime(job.finished_at) }}
                </span>
                <span class="meta-item next-run" v-if="job.next_run_time">
                  <svg class="meta-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <polygon points="5 3 19 12 5 21 5 3"></polygon>
                  </svg>
                  下次 {{ formatTime(job.next_run_time) }}
                </span>
                <span class="meta-item progress" v-if="job.progress_total > 0">
                  {{ job.progress_current }}/{{ job.progress_total }}
                </span>
              </div>
            </div>

            <!-- Progress bar (for running jobs) -->
            <div class="progress-bar-wrap" v-if="job.status === 'running' && job.progress_total > 0">
              <div
                class="progress-bar-fill"
                :style="{ width: progressPct(job) + '%' }"
              ></div>
              <span class="progress-label">{{ progressPct(job) }}%</span>
            </div>

            <!-- Actions -->
            <div class="job-actions" @click.stop>
              <button
                v-if="job.status !== 'running'"
                class="btn-retry"
                :class="{ loading: retryingJobs.has(job.name) }"
                :disabled="retryingJobs.has(job.name)"
                @click="retryJob(job.name)"
                title="手动重试此任务"
              >
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <polyline points="23 4 23 10 17 10"></polyline>
                  <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"></path>
                </svg>
                {{ retryingJobs.has(job.name) ? '触发中…' : '重试' }}
              </button>
              <div v-if="job.status === 'failed'" class="expand-hint">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <polyline :points="expandedJobs.has(job.name) ? '18 15 12 9 6 15' : '6 9 12 15 18 9'"></polyline>
                </svg>
              </div>
            </div>
          </div>

          <!-- Expanded failure details -->
          <transition name="expand">
            <div
              v-if="expandedJobs.has(job.name) && (job.message || Object.keys(job.details || {}).length)"
              class="job-details"
            >
              <div class="detail-row" v-if="job.message">
                <span class="detail-label">错误信息</span>
                <span class="detail-value error-text">{{ job.message }}</span>
              </div>
              <div class="detail-row" v-if="job.started_at">
                <span class="detail-label">开始时间</span>
                <span class="detail-value">{{ formatTime(job.started_at) }}</span>
              </div>
              <div class="detail-row" v-if="job.progress_total > 0">
                <span class="detail-label">进度</span>
                <span class="detail-value">{{ job.progress_current }} / {{ job.progress_total }}</span>
              </div>
              <template v-if="job.details && Object.keys(job.details).length">
                <div class="detail-row" v-for="(val, key) in job.details" :key="key">
                  <span class="detail-label">{{ key }}</span>
                  <span class="detail-value">{{ typeof val === 'object' ? JSON.stringify(val) : val }}</span>
                </div>
              </template>
            </div>
          </transition>
        </div>
      </transition-group>
    </div>

    <!-- Retry auth modal -->
    <div v-if="showAuthModal" class="auth-modal-overlay" @click.self="showAuthModal = false">
      <div class="auth-modal">
        <h3>需要管理员权限</h3>
        <p>手动触发任务需要管理员密钥</p>
        <input
          v-model="adminSecret"
          type="password"
          placeholder="Admin Secret"
          class="auth-input"
          @keyup.enter="confirmRetry"
        />
        <div class="auth-modal-actions">
          <button class="btn-cancel" @click="showAuthModal = false">取消</button>
          <button class="btn-confirm" @click="confirmRetry">确认触发</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { api } from '../api.js'
import { getAdminSecret } from '../adminAuth.js'

const jobs = ref([])
const error = ref('')
const isLoading = ref(true)
const isRefreshing = ref(false)
const lastUpdated = ref('')
const statusFilter = ref('')
const expandedJobs = ref(new Set())
const retryingJobs = ref(new Set())
const showAuthModal = ref(false)
const adminSecret = ref('')
const pendingRetryJob = ref('')

let pollInterval = null

const JOB_DISPLAY_NAMES = {
  market_update: '行情更新',
  signal_pipeline: '信号计算',
  rss_news_update: 'RSS 新闻采集',
  cninfo_update: '巨潮公告采集',
}

const STATUS_LABELS = {
  success: '成功',
  failed: '失败',
  running: '运行中',
  pending: '等待中',
  started: '启动中',
}

function displayName(name) {
  return JOB_DISPLAY_NAMES[name] || name
}

function statusLabel(status) {
  return STATUS_LABELS[status] || status
}

function formatTime(isoStr) {
  if (!isoStr) return '—'
  try {
    const d = new Date(isoStr)
    const now = new Date()
    const diff = now - d
    const diffMins = Math.floor(diff / 60000)
    const diffHours = Math.floor(diff / 3600000)
    const diffDays = Math.floor(diff / 86400000)
    if (diffMins < 1) return '刚刚'
    if (diffMins < 60) return `${diffMins} 分钟前`
    if (diffHours < 24) return `${diffHours} 小时前`
    if (diffDays < 7) return `${diffDays} 天前`
    return d.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
  } catch {
    return isoStr.slice(0, 16)
  }
}

function progressPct(job) {
  if (!job.progress_total) return 0
  return Math.round((job.progress_current / job.progress_total) * 100)
}

const filteredJobs = computed(() => {
  if (!statusFilter.value) return jobs.value
  return jobs.value.filter(j => j.status === statusFilter.value)
})

const statusCounts = computed(() => {
  const counts = { success: 0, running: 0, failed: 0, pending: 0 }
  for (const j of jobs.value) {
    if (j.status in counts) counts[j.status]++
  }
  return counts
})

function toggleExpand(job) {
  if (job.status === 'failed' || job.message) {
    const next = new Set(expandedJobs.value)
    if (next.has(job.name)) {
      next.delete(job.name)
    } else {
      next.add(job.name)
    }
    expandedJobs.value = next
  }
}

async function fetchJobs(silent = false) {
  if (!silent) isRefreshing.value = true
  try {
    const data = await api.getJobs()
    jobs.value = data
    // Auto-expand failed jobs
    const next = new Set(expandedJobs.value)
    for (const j of data) {
      if (j.status === 'failed') next.add(j.name)
    }
    expandedJobs.value = next
    error.value = ''
    lastUpdated.value = new Date().toLocaleTimeString('zh-CN')
  } catch (e) {
    error.value = e.message || '加载任务列表失败'
  } finally {
    isRefreshing.value = false
    isLoading.value = false
  }
}

function startPolling() {
  // Poll every 30s, or 5s if any job is running
  const hasRunning = jobs.value.some(j => j.status === 'running')
  const interval = hasRunning ? 5000 : 30000
  if (pollInterval) clearInterval(pollInterval)
  pollInterval = setInterval(() => {
    fetchJobs(true)
    startPolling() // re-schedule with potentially new interval
  }, interval)
}

async function retryJob(name) {
  const secret = getAdminSecret()
  if (!secret) {
    pendingRetryJob.value = name
    adminSecret.value = ''
    showAuthModal.value = true
    return
  }
  await doRetry(name, secret)
}

async function confirmRetry() {
  showAuthModal.value = false
  if (adminSecret.value && pendingRetryJob.value) {
    await doRetry(pendingRetryJob.value, adminSecret.value)
  }
}

async function doRetry(name, secret) {
  const next = new Set(retryingJobs.value)
  next.add(name)
  retryingJobs.value = next
  try {
    await api.retryJob(name, secret)
    // Refresh after short delay
    setTimeout(() => fetchJobs(true), 1500)
  } catch (e) {
    error.value = `触发失败: ${e.message}`
  } finally {
    const next2 = new Set(retryingJobs.value)
    next2.delete(name)
    retryingJobs.value = next2
  }
}

onMounted(async () => {
  await fetchJobs()
  startPolling()
})

onUnmounted(() => {
  if (pollInterval) clearInterval(pollInterval)
})
</script>

<style scoped>
.jobs-page {
  max-width: 900px;
  margin: 0 auto;
  padding: 2rem 1.5rem;
}

/* Header */
.jobs-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 2rem;
}

.jobs-title {
  font-size: 1.75rem;
  font-weight: 700;
  color: var(--color-text-primary, #f0f0f0);
  margin: 0 0 0.25rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.title-icon {
  font-size: 1.5rem;
}

.jobs-subtitle {
  font-size: 0.85rem;
  color: var(--color-text-secondary, #8b9cb0);
  margin: 0;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding-top: 0.25rem;
}

.refresh-indicator {
  width: 18px;
  height: 18px;
  color: var(--color-text-secondary, #8b9cb0);
  opacity: 0.6;
  transition: opacity 0.2s;
}

.refresh-indicator.spinning {
  opacity: 1;
  animation: spin 1s linear infinite;
}

.refresh-indicator svg {
  width: 100%;
  height: 100%;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.last-updated {
  font-size: 0.75rem;
  color: var(--color-text-secondary, #8b9cb0);
}

/* Summary bar */
.summary-bar {
  display: flex;
  gap: 0.75rem;
  flex-wrap: wrap;
  margin-bottom: 1.5rem;
}

.summary-pill {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.35rem 0.9rem;
  border-radius: 100px;
  font-size: 0.82rem;
  font-weight: 500;
  cursor: pointer;
  border: 1px solid rgba(255,255,255,0.08);
  background: rgba(255,255,255,0.04);
  color: var(--color-text-secondary, #8b9cb0);
  transition: all 0.2s;
  user-select: none;
}

.summary-pill:hover, .summary-pill.active {
  background: rgba(255,255,255,0.1);
  color: var(--color-text-primary, #f0f0f0);
  border-color: rgba(255,255,255,0.15);
}

.summary-pill.success.active { background: rgba(52, 211, 153, 0.15); border-color: rgba(52, 211, 153, 0.3); color: #34d399; }
.summary-pill.running.active { background: rgba(96, 165, 250, 0.15); border-color: rgba(96, 165, 250, 0.3); color: #60a5fa; }
.summary-pill.failed.active  { background: rgba(248, 113, 113, 0.15); border-color: rgba(248, 113, 113, 0.3); color: #f87171; }

.count {
  background: rgba(255,255,255,0.1);
  border-radius: 100px;
  padding: 0 0.5rem;
  font-size: 0.75rem;
}

/* Error banner */
.error-banner {
  background: rgba(248, 113, 113, 0.1);
  border: 1px solid rgba(248, 113, 113, 0.25);
  border-radius: 8px;
  padding: 0.75rem 1rem;
  color: #f87171;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 1rem;
  font-size: 0.9rem;
}

/* Empty state */
.empty-state {
  text-align: center;
  padding: 4rem 2rem;
  color: var(--color-text-secondary, #8b9cb0);
}

.empty-icon { font-size: 2.5rem; margin-bottom: 0.75rem; }
.empty-state p { font-size: 1rem; margin: 0 0 0.25rem; }
.empty-state small { font-size: 0.8rem; opacity: 0.7; }

/* Job cards */
.jobs-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.job-card {
  background: rgba(255,255,255,0.04);
  border: 1px solid rgba(255,255,255,0.07);
  border-radius: 12px;
  overflow: hidden;
  transition: border-color 0.2s, box-shadow 0.2s;
}

.job-card.status-failed {
  border-color: rgba(248, 113, 113, 0.2);
}

.job-card.status-running {
  border-color: rgba(96, 165, 250, 0.2);
}

.job-card.status-success {
  border-color: rgba(52, 211, 153, 0.1);
}

.job-card:hover {
  border-color: rgba(255,255,255,0.12);
  box-shadow: 0 4px 20px rgba(0,0,0,0.2);
}

.job-card-header {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem 1.25rem;
  cursor: default;
}

.status-failed .job-card-header {
  cursor: pointer;
}

/* Status badge */
.job-status-badge {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  font-size: 0.75rem;
  font-weight: 600;
  letter-spacing: 0.02em;
  text-transform: uppercase;
  white-space: nowrap;
  min-width: 70px;
}

.badge-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  flex-shrink: 0;
}

.job-status-badge.success { color: #34d399; }
.job-status-badge.success .badge-dot { background: #34d399; }
.job-status-badge.failed { color: #f87171; }
.job-status-badge.failed .badge-dot { background: #f87171; box-shadow: 0 0 8px rgba(248, 113, 113, 0.6); animation: pulse-red 2s infinite; }
.job-status-badge.running { color: #60a5fa; }
.job-status-badge.running .badge-dot { background: #60a5fa; animation: pulse-blue 1.5s infinite; }
.job-status-badge.pending, .job-status-badge.started { color: #a78bfa; }
.job-status-badge.pending .badge-dot, .job-status-badge.started .badge-dot { background: #a78bfa; }

@keyframes pulse-red {
  0%, 100% { box-shadow: 0 0 8px rgba(248, 113, 113, 0.6); }
  50% { box-shadow: 0 0 14px rgba(248, 113, 113, 0.9); }
}

@keyframes pulse-blue {
  0%, 100% { box-shadow: 0 0 8px rgba(96, 165, 250, 0.6); }
  50% { box-shadow: 0 0 14px rgba(96, 165, 250, 0.9); }
}

/* Job main info */
.job-main-info {
  flex: 1;
  min-width: 0;
}

.job-name {
  font-size: 0.95rem;
  font-weight: 600;
  color: var(--color-text-primary, #f0f0f0);
  margin-bottom: 0.2rem;
}

.job-meta {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  flex-wrap: wrap;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  font-size: 0.78rem;
  color: var(--color-text-secondary, #8b9cb0);
}

.meta-item.next-run { color: #a78bfa; }
.meta-item.progress { 
  background: rgba(255,255,255,0.06);
  padding: 0.1rem 0.5rem;
  border-radius: 100px;
}

.meta-icon {
  width: 12px;
  height: 12px;
  flex-shrink: 0;
}

/* Progress bar */
.progress-bar-wrap {
  flex: 0 0 140px;
  height: 6px;
  background: rgba(255,255,255,0.08);
  border-radius: 100px;
  position: relative;
  overflow: visible;
}

.progress-bar-fill {
  height: 100%;
  background: linear-gradient(90deg, #60a5fa, #a78bfa);
  border-radius: 100px;
  transition: width 0.4s ease;
}

.progress-label {
  position: absolute;
  top: -1.5rem;
  right: 0;
  font-size: 0.7rem;
  color: #60a5fa;
}

/* Actions */
.job-actions {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-shrink: 0;
}

.btn-retry {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.4rem 0.9rem;
  background: rgba(96, 165, 250, 0.12);
  border: 1px solid rgba(96, 165, 250, 0.25);
  border-radius: 8px;
  color: #60a5fa;
  font-size: 0.8rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-retry:hover:not(:disabled) {
  background: rgba(96, 165, 250, 0.2);
  border-color: rgba(96, 165, 250, 0.4);
}

.btn-retry:disabled, .btn-retry.loading {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-retry.loading svg { animation: spin 1s linear infinite; }

.btn-retry svg {
  width: 13px;
  height: 13px;
}

.expand-hint {
  color: var(--color-text-secondary, #8b9cb0);
  opacity: 0.5;
}

.expand-hint svg {
  width: 16px;
  height: 16px;
}

/* Details panel */
.job-details {
  border-top: 1px solid rgba(255,255,255,0.06);
  padding: 1rem 1.25rem;
  background: rgba(0,0,0,0.1);
}

.detail-row {
  display: flex;
  gap: 1rem;
  padding: 0.3rem 0;
  font-size: 0.82rem;
  border-bottom: 1px solid rgba(255,255,255,0.04);
}

.detail-row:last-child { border-bottom: none; }

.detail-label {
  flex: 0 0 80px;
  color: var(--color-text-secondary, #8b9cb0);
  font-weight: 500;
}

.detail-value {
  flex: 1;
  color: var(--color-text-primary, #f0f0f0);
  word-break: break-word;
}

.error-text {
  color: #f87171;
  font-family: monospace;
  font-size: 0.8rem;
}

/* Auth modal */
.auth-modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.6);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.auth-modal {
  background: #1a1f2e;
  border: 1px solid rgba(255,255,255,0.1);
  border-radius: 16px;
  padding: 2rem;
  width: 360px;
  box-shadow: 0 20px 60px rgba(0,0,0,0.5);
}

.auth-modal h3 {
  font-size: 1.1rem;
  font-weight: 700;
  color: var(--color-text-primary, #f0f0f0);
  margin: 0 0 0.5rem;
}

.auth-modal p {
  font-size: 0.85rem;
  color: var(--color-text-secondary, #8b9cb0);
  margin: 0 0 1.25rem;
}

.auth-input {
  width: 100%;
  padding: 0.6rem 0.9rem;
  background: rgba(255,255,255,0.06);
  border: 1px solid rgba(255,255,255,0.12);
  border-radius: 8px;
  color: var(--color-text-primary, #f0f0f0);
  font-size: 0.9rem;
  outline: none;
  margin-bottom: 1rem;
  box-sizing: border-box;
}

.auth-input:focus {
  border-color: rgba(96, 165, 250, 0.5);
}

.auth-modal-actions {
  display: flex;
  gap: 0.75rem;
  justify-content: flex-end;
}

.btn-cancel {
  padding: 0.5rem 1rem;
  background: transparent;
  border: 1px solid rgba(255,255,255,0.12);
  border-radius: 8px;
  color: var(--color-text-secondary, #8b9cb0);
  font-size: 0.85rem;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-cancel:hover {
  background: rgba(255,255,255,0.06);
}

.btn-confirm {
  padding: 0.5rem 1rem;
  background: rgba(96, 165, 250, 0.15);
  border: 1px solid rgba(96, 165, 250, 0.3);
  border-radius: 8px;
  color: #60a5fa;
  font-size: 0.85rem;
  cursor: pointer;
  font-weight: 600;
  transition: all 0.2s;
}

.btn-confirm:hover {
  background: rgba(96, 165, 250, 0.25);
}

/* Transitions */
.expand-enter-active, .expand-leave-active {
  transition: max-height 0.3s ease, opacity 0.2s ease;
  max-height: 500px;
  overflow: hidden;
}

.expand-enter-from, .expand-leave-to {
  max-height: 0;
  opacity: 0;
}

.job-card-enter-active, .job-card-leave-active {
  transition: opacity 0.3s, transform 0.3s;
}

.job-card-enter-from, .job-card-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}

@media (max-width: 640px) {
  .jobs-page { padding: 1rem; }
  .job-card-header { flex-wrap: wrap; gap: 0.75rem; }
  .progress-bar-wrap { display: none; }
}
</style>
