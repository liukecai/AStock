<script setup>
import { computed } from "vue";

const props = defineProps({
  items: { type: Array, default: () => [] },
  groupByPriority: { type: Boolean, default: true },
});

function priorityOf(item) {
  const sentiment = Math.abs(item.sentiment || 0);
  return sentiment >= 0.35 || (item.confidence || 0) >= 0.9 ? "关键驱动新闻" : "一般关联新闻";
}

function formatSentiment(value) {
  const num = Number(value || 0);
  return `${num > 0 ? "+" : ""}${num.toFixed(2)}`;
}

const groups = computed(() => {
  if (!props.groupByPriority) {
    return [{ title: "证据流", items: props.items }];
  }

  const ordered = [
    { title: "关键驱动新闻", items: [] },
    { title: "一般关联新闻", items: [] },
  ];

  for (const item of props.items) {
    const group = ordered.find((entry) => entry.title === priorityOf(item));
    group.items.push(item);
  }

  return ordered.filter((entry) => entry.items.length);
});
</script>

<template>
  <section class="panel news-panel">
    <div class="panel-title">
      <div>
        <p class="eyebrow">EVIDENCE FLOW</p>
        <h2>证据流</h2>
      </div>
      <span class="news-count">{{ items.length }} 条</span>
    </div>

    <div class="evidence-groups">
      <div v-for="group in groups" :key="group.title" class="evidence-group">
        <div class="evidence-group-title">{{ group.title }}</div>
        <div class="news-list">
          <article v-for="item in group.items" :key="item.published_at + item.title">
            <time>{{ item.published_at.slice(5, 16).replace("T", " ") }}</time>
            <div>
              <div class="evidence-meta">
                <span>{{ item.source }}</span>
                <span>{{ item.event_type || "未分类" }}</span>
                <span>{{ item.match_type || "默认映射" }}</span>
                <span>置信 {{ (item.confidence ?? 0).toFixed(2) }}</span>
              </div>
              <h3>
                <a
                  v-if="item.url"
                  :href="item.url"
                  target="_blank"
                  rel="noopener noreferrer"
                >{{ item.title }} ↗</a>
                <template v-else>{{ item.title }}</template>
              </h3>
              <p>{{ item.keywords?.join(" / ") || "未命中关键词" }}</p>
              <p v-if="item.summary" class="news-summary">{{ item.summary }}</p>
            </div>
            <span class="news-score" :class="{ positive: item.sentiment > 0, negative: item.sentiment < 0 }">
              {{ formatSentiment(item.sentiment) }}
            </span>
          </article>
        </div>
      </div>
    </div>
  </section>
</template>
