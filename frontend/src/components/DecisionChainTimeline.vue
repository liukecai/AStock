<script setup>
defineProps({
  steps: { type: Array, default: () => [] },
});
</script>

<template>
  <section class="panel">
    <div class="panel-title">
      <div>
        <p class="eyebrow">DECISION CHAIN</p>
        <h2>决策链</h2>
      </div>
    </div>
    <div class="decision-timeline">
      <article
        v-for="(step, index) in steps"
        :key="step.title"
        class="decision-step"
        :class="`tone-${step.tone || 'neutral'}`"
      >
        <div class="decision-step-index">{{ index + 1 }}</div>
        <div>
          <span>{{ step.title }}</span>
          <strong>{{ step.value }}</strong>
          <p>{{ step.note }}</p>
        </div>
      </article>
    </div>
  </section>
</template>
