<template>
  <div class="telemetry-card">
    <div class="card-header">
      <i :class="icon" v-if="icon"></i>
      <h3>{{ title }}</h3>
    </div>
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
  },
  icon: {
    type: String,
    default: ''
  }
})
</script>

<style scoped>
.telemetry-card {
  background: #fff;
  border-radius: 8px;
  overflow: hidden;
  border: 1px solid #e0e7ef;
  transition: all 0.3s ease;
}

.telemetry-card:hover {
  border-color: #0096ff;
  box-shadow: 0 5px 15px rgba(0, 150, 255, 0.08);
  transform: translateY(-2px);
}

.card-header {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 15px;
  background: #f3f7fa;
  border-bottom: 1px solid #e0e7ef;
}

.card-header h3 {
  margin: 0;
  font-size: 0.9rem;
  font-weight: 500;
  color: #222;
}

.card-header i {
  color: v-bind('iconColor || "#0096ff"');
  font-size: 0.9rem;
}

.card-content {
  padding: 15px;
}
</style>