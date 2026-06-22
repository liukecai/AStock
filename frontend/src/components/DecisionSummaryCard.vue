<script setup>
import ScoreRing from "./ScoreRing.vue";

defineProps({
  stock: { type: Object, required: true },
  signal: { type: Object, required: true },
  summary: { type: String, required: true },
  dominantDriver: { type: String, required: true },
  highlights: { type: Array, default: () => [] },
});
</script>

<template>
  <section class="decision-summary-card panel">
    <div class="decision-summary-header">
      <div>
        <p class="eyebrow">DECISION SUMMARY</p>
        <div class="decision-summary-title">
          <div>
            <small class="decision-summary-kicker">{{ stock.industry }} · {{ stock.symbol }}</small>
            <h2>研究结论摘要</h2>
          </div>
          <span class="status-pill" :class="signal.status">{{ signal.status }}</span>
        </div>
        <p class="decision-summary-copy">{{ summary }}</p>
      </div>

      <div class="decision-summary-score">
        <ScoreRing :value="signal.total_score" :size="84" />
        <div>
          <span>综合分</span>
          <strong>{{ Math.round(signal.total_score) }}</strong>
          <small>{{ dominantDriver }} · 研究上限 {{ signal.research_weight_pct ?? 0 }}%</small>
        </div>
      </div>
    </div>

    <div class="decision-highlight-list">
      <article v-for="item in highlights" :key="item.label">
        <span>{{ item.label }}</span>
        <strong>{{ item.value }}</strong>
        <small>{{ item.note }}</small>
      </article>
    </div>
  </section>
</template>
