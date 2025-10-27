<template>
  <div class="connection-status">
    <div class="status-indicator">
      <div class="status-dot" :class="{ connected: isWSConnected && isWTConnected && isRTCConnected && isMqttConnected }"></div>
    </div>
    <div class="connection-details">
      <div class="connection-item">
        <i class="fas fa-server"></i>
        <span :class="{ active: isWSConnected }">WS</span>
      </div>
      <div class="connection-item">
        <i class="fas fa-bolt"></i>
        <span :class="{ active: isWTConnected }">WT</span>
      </div>
      <div class="connection-item">
        <i class="fas fa-stream"></i>
        <span :class="{ active: isRTCConnected }">WRTC</span>
      </div>
      <div class="connection-item">
        <i class="fas fa-share-alt"></i>
        <span :class="{ active: isMqttConnected }">MQTT</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { storeToRefs } from 'pinia'
import { useTrainStore } from '@/stores/trainStore'

const { isWSConnected, isWTConnected, isMqttConnected, isRTCConnected } = storeToRefs(useTrainStore())
</script>

<style scoped>
.connection-status {
  display: flex;
  align-items: center;
  gap: 20px;
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  padding: 12px 20px;
  border-radius: 14px;
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.status-indicator {
  display: flex;
  align-items: center;
  gap: 10px;
}

.status-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background-color: #ff4757;
  box-shadow: 0 0 12px rgba(255, 71, 87, 0.5);
  animation: pulse-red 2s infinite;
}

.status-dot.connected {
  background-color: #2ed573;
  box-shadow: 0 0 12px rgba(46, 213, 115, 0.5);
  animation: pulse-green 2s infinite;
}

.status-text {
  font-size: 0.95rem;
  font-weight: 500;
  color: rgba(255, 255, 255, 0.9);
}

.connection-details {
  display: flex;
  gap: 16px;
}

.connection-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.8rem;
  color: rgba(255, 255, 255, 0.6);
  transition: color 0.3s ease;
}

.connection-item span.active {
  color: #2ed573;
  font-weight: 600;
}

.connection-item span:not(.active) {
  color: #ff4757;
  font-weight: 600;
}

.connection-item i {
  font-size: 0.75rem;
}

@keyframes pulse-red {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.5;
  }
}

@keyframes pulse-green {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.7;
  }
}

@media (max-width: 768px) {
  .connection-status {
    gap: 12px;
    padding: 6px 12px;
  }
  
  .connection-details {
    gap: 8px;
  }
  
  .status-text {
    font-size: 0.8rem;
  }
}
</style>