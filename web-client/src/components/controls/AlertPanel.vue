<template>
  <div class="alert-panel">
    <div class="alert-header">
      <span class="alert-icon">⚠️</span>
      <h3>ALERTS</h3>
      <span class="alert-count">{{ activeAlerts.length }}</span>
    </div>
    
    <div class="alert-list">
      <div 
        v-for="(alert, index) in activeAlerts" 
        :key="index" 
        class="alert-item"
        :class="alert.severity"
      >
        <div class="alert-message">{{ alert.message }}</div>
        <button class="alert-ack" @click="acknowledgeAlert(index)">ACK</button>
      </div>
      <div v-if="activeAlerts.length === 0" class="no-alerts">
        NO ACTIVE ALERTS
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  activeAlerts: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['acknowledge-alert']);

const acknowledgeAlert = (index) => {
  emit('acknowledge-alert', index);
};
</script>

<style scoped>
.alert-panel {
  background: #1a1a1a;
  border-radius: 15px;
  padding: 15px;
  box-shadow: inset 0 0 10px rgba(0,0,0,0.5);
}

.alert-header {
  display: flex;
  align-items: center;
  gap: 10px;
  color: #777;
  font-size: 0.9rem;
  margin-bottom: 10px;
  border-bottom: 1px solid #333;
  padding-bottom: 10px;
}

.alert-icon {
  font-size: 1.2rem;
}

.alert-count {
  margin-left: auto;
  background: #333;
  padding: 2px 8px;
  border-radius: 10px;
  font-size: 0.8rem;
}

.alert-list {
  max-height: 200px;
  overflow-y: auto;
}

.alert-item {
  display: flex;
  align-items: center;
  padding: 8px;
  margin-bottom: 5px;
  border-radius: 5px;
  font-size: 0.8rem;
}

.alert-item.warning {
  background: rgba(241, 196, 15, 0.1);
  border-left: 3px solid #f1c40f;
}

.alert-item.error {
  background: rgba(231, 76, 60, 0.1);
  border-left: 3px solid #e74c3c;
}

.alert-item.critical {
  background: rgba(231, 76, 60, 0.2);
}

.alert-ack {
  background: #333;
  color: white;
  border: none;
  border-radius: 3px;
  padding: 3px 8px;
  font-size: 0.7rem;
  cursor: pointer;
  margin-left: 10px;
}

.alert-ack:hover {
  background: #444;
}

.no-alerts {
  text-align: center;
  color: #777;
  font-size: 0.8rem;
  padding: 10px;
}

@keyframes pulse {
  0% { opacity: 1; }
  50% { opacity: 0.7; }
  100% { opacity: 1; }
}
</style>