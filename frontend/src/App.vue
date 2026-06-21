<script setup>
import { useRoute } from "vue-router";

const route = useRoute();
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
        <RouterLink to="/review">映射审核</RouterLink>
        <a href="/docs" target="_blank">API</a>
      </nav>
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
  </div>
</template>

