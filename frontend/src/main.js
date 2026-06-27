import { createApp } from "vue";
import { createRouter, createWebHistory } from "vue-router";
import App from "./App.vue";
import "./styles.css";

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: "/", component: () => import("./views/Dashboard.vue") },
    { path: "/stocks/:symbol", component: () => import("./views/StockDetail.vue") },
    { path: "/review", component: () => import("./views/MappingReview.vue") },
    { path: "/events", component: () => import("./views/Events.vue") },
    { path: "/jobs", component: () => import("./views/Jobs.vue") },
    { path: "/v2/events", component: () => import("./views/EventDashboardV2.vue") },
    { path: "/v2/explorer", component: () => import("./views/SupplyChainExplorer.vue") },
    { path: "/v2/validation", component: () => import("./views/ValidationPanel.vue") },

  ],
  scrollBehavior: () => ({ top: 0 }),
});

createApp(App).use(router).mount("#app");
