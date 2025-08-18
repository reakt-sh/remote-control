<template>
  <header class="app-header">
    <h1>Remote Control System</h1>
    <div class="header-controls">
      <button @click="exportLatencyData" class="export-btn" title="Export Latency Data">
        <i class="fas fa-download"></i>
        <span>Export Data</span>
      </button>
      <button @click="exportVideoData" class="export-btn video-export" title="Export Video">
        <i class="fas fa-video"></i>
        <span>Export Video</span>
      </button>
      <ConnectionStatus />
    </div>
  </header>
</template>

<script setup>
import ConnectionStatus from '@/components/ConnectionStatus.vue'
import { useTrainStore } from '@/stores/trainStore'

const { exportToJson, exportVideo } = useTrainStore()

function exportLatencyData() {
  exportToJson()
}

function exportVideoData() {
  exportVideo()
}
</script>

<style scoped>
.app-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 2rem;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
}

.app-header h1 {
  margin: 0;
  font-size: 1.8rem;
  font-weight: 600;
}

.header-controls {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.export-btn {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  background: rgba(255, 255, 255, 0.1);
  color: white;
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 8px;
  cursor: pointer;
  font-size: 0.9rem;
  transition: all 0.3s ease;
  backdrop-filter: blur(10px);
}

.export-btn:hover {
  background: rgba(255, 255, 255, 0.2);
  border-color: rgba(255, 255, 255, 0.3);
  transform: translateY(-1px);
}

.export-btn:active {
  transform: translateY(0);
}

.export-btn.video-export {
  background: linear-gradient(135deg, #ff6b6b 0%, #ee5a24 100%);
}

.export-btn.video-export:hover {
  background: linear-gradient(135deg, #ff5252 0%, #ff3d00 100%);
}

.export-btn i {
  font-size: 0.8rem;
}

@media (max-width: 768px) {
  .app-header {
    padding: 1rem;
  }
  
  .app-header h1 {
    font-size: 1.4rem;
  }
  
  .header-controls {
    gap: 0.5rem;
  }
  
  .export-btn span {
    display: none;
  }
  
  .export-btn {
    padding: 0.5rem;
  }
}
</style>
