<script setup>
defineProps({
  title: { type: String, required: true },
  score: { type: Number, required: true },
  tone: { type: String, default: "neutral" },
  highlights: { type: Array, default: () => [] },
  neutralDelta: { type: Number, default: undefined },
});
</script>

<template>
  <article class="driver-panel" :class="`tone-${tone}`">
    <div class="driver-panel-header">
      <div>
        <span>{{ title }}</span>
        <strong>{{ Math.round(score) }}</strong>
      </div>
      <i><i :style="{ width: `${score}%` }"></i></i>
    </div>
    <ul class="driver-highlights">
      <li v-for="item in highlights" :key="item">{{ item }}</li>
    </ul>
    <small v-if="neutralDelta !== undefined" class="driver-neutral">
      行业偏差
      <span :class="{ positive: neutralDelta > 0, negative: neutralDelta < 0 }">
        {{ neutralDelta >= 0 ? "+" : "" }}{{ neutralDelta.toFixed(2) }}
      </span>
    </small>
  </article>
</template>
