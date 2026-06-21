<script setup>
import { computed } from "vue";

const props = defineProps({
  value: { type: Number, required: true },
  size: { type: Number, default: 54 },
});
const style = computed(() => ({
  width: `${props.size}px`,
  height: `${props.size}px`,
  background: `conic-gradient(var(--lime) ${props.value * 3.6}deg, rgba(255,255,255,.08) 0deg)`,
}));
</script>

<template>
  <div class="score-ring" :style="style">
    <div>{{ Math.round(value) }}</div>
  </div>
</template>

