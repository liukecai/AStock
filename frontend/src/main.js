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
  ],
  scrollBehavior: () => ({ top: 0 }),
});

createApp(App).use(router).mount("#app");
