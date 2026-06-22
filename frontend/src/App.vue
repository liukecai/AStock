<script setup>
import { onMounted, ref } from "vue";
import { useRoute } from "vue-router";
import {
  adminAuth,
  authorizeAdmin,
  bootstrapAdminAuth,
  closeAdminDialog,
  logoutAdmin,
  openAdminDialog,
} from "./adminAuth";

const route = useRoute();
const secret = ref("");

async function submitAdminAuth() {
  if (!secret.value.trim()) {
    adminAuth.error = "请输入管理口令";
    return;
  }
  try {
    await authorizeAdmin(secret.value.trim());
    secret.value = "";
  } catch {}
}

onMounted(() => {
  bootstrapAdminAuth();
});
</script>

<template>
  <div class="app-shell">
    <header class="topbar">
      <RouterLink to="/" class="brand">
        <span class="brand-mark">AQ</span>
        <span>
          <strong>A-Quant</strong>
          <small>INSIGHT</small>
        </span>
      </RouterLink>
      <nav>
        <RouterLink to="/">信号台</RouterLink>
        <RouterLink to="/events">事件驱动</RouterLink>
        <RouterLink to="/review">映射审核</RouterLink>
        <a href="/docs" target="_blank">API</a>
      </nav>
      <div class="admin-actions">
        <button
          v-if="adminAuth.required"
          class="admin-auth-button"
          :class="{ authorized: adminAuth.authorized }"
          @click="adminAuth.authorized ? logoutAdmin() : openAdminDialog()"
        >
          {{ adminAuth.authorized ? "已授权" : "管理授权" }}
        </button>
      </div>
      <div class="market-state">
        <i></i>
        <span>研究模式</span>
      </div>
    </header>
    <main :class="{ detail: route.path !== '/' }">
      <RouterView />
    </main>
    <footer>
      <span>A-Quant Insight · 趋势与信息的交叉验证</span>
      <span>仅供量化研究，不构成投资建议</span>
    </footer>

    <div v-if="adminAuth.dialogOpen" class="admin-auth-overlay" @click.self="closeAdminDialog">
      <section class="admin-auth-dialog">
        <p class="eyebrow">ADMIN AUTHORIZATION</p>
        <h2>输入管理口令</h2>
        <p class="admin-auth-copy">写操作已受保护。完成授权后，才能触发重新计算、映射修改和事件重建。</p>
        <input
          v-model="secret"
          type="password"
          autocomplete="current-password"
          placeholder="管理口令"
          @keyup.enter="submitAdminAuth"
        />
        <p v-if="adminAuth.error" class="admin-auth-error">{{ adminAuth.error }}</p>
        <div class="admin-auth-buttons">
          <button class="admin-auth-cancel" @click="closeAdminDialog">取消</button>
          <button class="admin-auth-confirm" :disabled="adminAuth.loading" @click="submitAdminAuth">
            {{ adminAuth.loading ? "校验中…" : "确认授权" }}
          </button>
        </div>
      </section>
    </div>
  </div>
</template>
