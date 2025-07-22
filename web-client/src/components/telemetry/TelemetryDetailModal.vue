<template>
  <div class="modal-overlay" @click.self="closeModal">
    <div class="modal-content">
      <div class="modal-header">
        <div>
          <h3>Telemetry Snapshot</h3>
          <span class="timestamp">{{ formatTime(item.timestamp) }}</span>
        </div>
        <button @click="closeModal" class="close-button">
          <i class="fas fa-times"></i>
        </button>
      </div>
      <div class="modal-body">
        <div class="detail-grid">
          <!-- Train Information -->
          <div class="detail-card">
            <h4><i class="fas fa-train"></i> Train Information</h4>
            <div class="info-row">
              <span class="label">Name</span>
              <span class="value">{{ item.name }}</span>
            </div>
            <div class="info-row">
              <span class="label">Train ID</span>
              <span class="value">{{ item.train_id }}</span>
            </div>
            <div class="info-row">
              <span class="label">Status</span>
              <span class="value">{{ item.status }}</span>
            </div>
            <div class="info-row">
              <span class="label">Direction</span>
              <span class="value">{{ item.direction }}</span>
            </div>
          </div>

          <!-- Location & Movement -->
          <div class="detail-card">
            <h4><i class="fas fa-map-marked-alt"></i> Location & Movement</h4>
            <div class="info-row">
              <span class="label">Location</span>
              <span class="value">{{ item.location }}</span>
            </div>
            <div class="info-row">
              <span class="label">Next Station</span>
              <span class="value">{{ item.next_station }}</span>
            </div>
            <div class="info-row">
              <span class="label">GPS</span>
              <span class="value">{{ item.gps.latitude.toFixed(6) }}, {{ item.gps.longitude.toFixed(6) }}</span>
            </div>
            <div class="info-row">
              <span class="label">Speed</span>
              <span class="value">{{ item.speed }} km/h</span>
            </div>
            <div class="info-row">
              <span class="label">Max Speed</span>
              <span class="value">{{ item.max_speed }} km/h</span>
            </div>
            <div class="info-row">
              <span class="label">Brake Status</span>
              <span class="value">{{ item.brake_status }}</span>
            </div>
          </div>

          <!-- System Health -->
          <div class="detail-card">
            <h4><i class="fas fa-heartbeat"></i> System Health</h4>
            <div class="health-metrics">
              <div class="metric-item">
                <span class="label">Battery</span>
                <div class="progress-bar">
                  <div class="progress" :style="{ width: item.battery_level + '%' }"></div>
                </div>
              </div>
              <div class="metric-item">
                <span class="label">Fuel</span>
                <div class="progress-bar">
                  <div class="progress" :style="{ width: item.fuel_level + '%' }"></div>
                </div>
              </div>
            </div>
          </div>

          <!-- Environment -->
          <div class="detail-card">
            <h4><i class="fas fa-thermometer-three-quarters"></i> Environment</h4>
            <div class="info-row">
              <span class="label">Cabin Temp.</span>
              <span class="value">{{ item.temperature }}°C</span>
            </div>
            <div class="info-row">
              <span class="label">Engine Temp.</span>
              <span class="value">{{ item.engine_temperature }}°C</span>
            </div>
          </div>

          <!-- Passengers -->
          <div class="detail-card">
            <h4><i class="fas fa-users"></i> Passengers</h4>
            <div class="info-row">
              <span class="label">Passenger Count</span>
              <span class="value">{{ item.passenger_count }}</span>
            </div>
          </div>

          <!-- Network & Connectivity -->
          <div class="detail-card">
            <h4><i class="fas fa-broadcast-tower"></i> Network</h4>
            <div class="info-row">
              <span class="label">Signal Strength</span>
              <span class="value">{{ item.network_signal_strength }}%</span>
            </div>
            <div class="info-row">
              <span class="label">Download Speed</span>
              <span class="value">{{ item.download_speed }} kbps</span>
            </div>
            <div class="info-row">
              <span class="label">Upload Speed</span>
              <span class="value">{{ item.upload_speed }} kbps</span>
            </div>
            <div class="info-row">
              <span class="label">Video Stream</span>
              <span class="value">{{ item.video_stream_url }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
const props = defineProps({
  item: {
    type: Object,
    required: true,
  },
});

const emit = defineEmits(['close']);

function closeModal() {
  emit('close');
}

function formatTime() {
  const date = new Date(props.item.timestamp);
  return `${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}:${date.getSeconds().toString().padStart(2, '0')}`;
}
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.6);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
  backdrop-filter: blur(5px);
}

.modal-content {
  background: #f8fafc;
  border-radius: 20px;
  width: 90%;
  max-width: 900px;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: 0 10px 40px rgba(0, 32, 128, 0.2);
  display: flex;
  flex-direction: column;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 24px 32px;
  border-bottom: 1px solid #e0e7ef;
}

.modal-header h3 {
  font-size: 1.6rem;
  font-weight: 700;
  color: #1e293b;
  margin: 0;
}

.modal-header .timestamp {
  font-size: 0.9rem;
  color: #64748b;
}

.close-button {
  background: #e2e8f0;
  border: none;
  border-radius: 50%;
  width: 36px;
  height: 36px;
  display: flex;
  justify-content: center;
  align-items: center;
  cursor: pointer;
  color: #475569;
  font-size: 1rem;
  transition: background 0.2s, color 0.2s;
}

.close-button:hover {
  background: #0096ff;
  color: #fff;
}

.modal-body {
  padding: 32px;
  flex-grow: 1;
}

.detail-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  gap: 24px;
}

.detail-card {
  background: #fff;
  border-radius: 16px;
  padding: 24px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
}

.detail-card h4 {
  font-size: 1.1rem;
  font-weight: 600;
  color: #334155;
  margin-top: 0;
  margin-bottom: 20px;
  display: flex;
  align-items: center;
  gap: 10px;
}

.detail-card h4 i {
  color: #0096ff;
}

.info-row {
  display: flex;
  justify-content: space-between;
  padding: 10px 0;
  border-bottom: 1px solid #f1f5f9;
}

.info-row:last-child {
  border-bottom: none;
}

.info-row .label {
  font-weight: 500;
  color: #64748b;
}

.info-row .value {
  font-weight: 600;
  color: #1e293b;
}

.health-metrics {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.metric-item {
  display: grid;
  grid-template-columns: 80px 1fr;
  align-items: center;
  gap: 12px;
}

.progress-bar {
  width: 100%;
  height: 8px;
  background: #e2e8f0;
  border-radius: 4px;
  overflow: hidden;
}

.progress {
  height: 100%;
  background: linear-gradient(90deg, #4ade80, #22c55e);
  border-radius: 4px;
  transition: width 0.3s;
}

@media (max-width: 768px) {
  .modal-content {
    width: 95%;
    max-width: none;
  }
  
  .detail-grid {
    grid-template-columns: 1fr;
    gap: 16px;
  }
  
  .modal-header {
    padding: 20px;
  }
  
  .modal-body {
    padding: 20px;
  }
}
</style>
