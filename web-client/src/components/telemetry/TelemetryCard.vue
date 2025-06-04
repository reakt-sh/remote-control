<template>
  <div class="telemetry-card">
    <h3>{{ title }}</h3>
    <div class="card-content">
      <slot></slot>
    </div>
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
  background: #ffffff;
  padding: 0.75rem;
  border-radius: 6px;
  border-left: 3px solid #3b82f6;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.08);
  overflow: hidden;
}

.telemetry-card h3 {
  font-size: 0.875rem;
  color: #4b5563;
  margin-bottom: 0.5rem;
  font-weight: 500;
}

.card-content {
  max-width: 100%;
  overflow: hidden;
}
</style>