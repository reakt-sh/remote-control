<template>
  <div class="telemetry-card">
    <h3>{{ title }}</h3>
    <slot></slot>
  </div>
</template>

<script setup>
defineProps({
  title: {
    type: String,
    required: true
  }
})
</script>

<style scoped>
.telemetry-card {
  background: #f9f9f9;
  padding: 1rem;
  border-radius: 5px;
  border-left: 4px solid var(--secondary-color);
}

.telemetry-card h3 {
  font-size: 0.9rem;
  color: var(--text-light);
  margin-bottom: 0.5rem;
}
</style>