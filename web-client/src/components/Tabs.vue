<template>
  <div class="tabs-container">
    <div class="tabs-header">
      <button
        v-for="tab in tabs"
        :key="tab.id"
        @click="activeTab = tab.id"
        :class="{ active: activeTab === tab.id }"
      >
        <i :class="tab.icon"></i>
        {{ tab.label }}
      </button>
    </div>
    <div class="tabs-content">
      <slot :name="activeTab"></slot>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const props = defineProps({
  tabs: {
    type: Array,
    required: true,
    default: () => [
      { id: 'control', label: 'Control', icon: 'fas fa-gamepad' },
      { id: 'telemetry', label: 'Telemetry', icon: 'fas fa-chart-line' }
    ]
  },
  initialTab: {
    type: String,
    default: 'control'
  }
})

const activeTab = ref(props.initialTab)
</script>

<style scoped>
.tabs-container {
  background: #1a1e24;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
}

.tabs-header {
  display: flex;
  background: linear-gradient(135deg, #2c3e50, #1a1e24);
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

.tabs-header button {
  flex: 1;
  padding: 15px 20px;
  background: transparent;
  border: none;
  color: rgba(255, 255, 255, 0.7);
  font-size: 14px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.tabs-header button:hover {
  color: #fff;
  background: rgba(255, 255, 255, 0.05);
}

.tabs-header button.active {
  color: #fff;
  background: rgba(0, 150, 255, 0.2);
  position: relative;
}

.tabs-header button.active::after {
  content: '';
  position: absolute;
  bottom: -1px;
  left: 0;
  right: 0;
  height: 3px;
  background: linear-gradient(90deg, #0096ff, #00d4ff);
}

.tabs-content {
  padding: 20px;
  background: #1a1e24;
  min-height: 300px;
}
</style>