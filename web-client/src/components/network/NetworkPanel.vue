<template>
  <div class="network-panel">
    <div class="network-grid">
      <TelemetryCard title="Train to Server" icon="fas fa-train">
        <div class="network-metrics">
          <div class="metric-item">
            <div class="metric-label">Download Speed</div>
            <div class="metric-value">
              {{ formatSpeed(telemetryData?.download_speed) }}
              <span class="unit">Mbps</span>
            </div>
          </div>
          <div class="metric-item">
            <div class="metric-label">Upload Speed</div>
            <div class="metric-value">
              {{ formatSpeed(telemetryData?.upload_speed) }}
              <span class="unit">Mbps</span>
            </div>
          </div>
          <button class="test-button" @click="send_network_measurement_request()" :disabled="isTestingTrainClient">
            <i class="fas fa-sync-alt" :class="{ 'fa-spin': isTestingTrainClient }"></i>
            {{ isTestingTrainClient ? 'Calculating...' : 'Re-Calculate' }}
          </button>
        </div>
      </TelemetryCard>

      <TelemetryCard title="Remote Control to Server" icon="fas fa-globe">
        <div class="network-metrics">
          <div class="metric-item">
            <div class="metric-label">Download Speed</div>
            <div class="metric-value">
              {{ formatSpeed(download_speed) }}
              <span class="unit">Mbps</span>
            </div>
          </div>
          <div class="metric-item">
            <div class="metric-label">Upload Speed</div>
            <div class="metric-value">
              {{ formatSpeed(upload_speed) }}
              <span class="unit">Mbps</span>
            </div>
          </div>
          <button class="test-button" @click="networkspeed.runFullTest(); isTestingWebClient = true" :disabled="isTestingWebClient">
            <i class="fas fa-sync-alt" :class="{ 'fa-spin': isTestingWebClient }"></i>
            {{ isTestingWebClient ? 'Calculating...' : 'Re-Calculate' }}
          </button>
        </div>
      </TelemetryCard>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { storeToRefs } from 'pinia'
import { useTrainStore } from '@/stores/trainStore'
import TelemetryCard from '@/components/telemetry/TelemetryCard.vue'

const trainStore = useTrainStore()
const { networkspeed, telemetryData, download_speed, upload_speed } = storeToRefs(trainStore)
const isTestingWebClient = ref(false)
const isTestingTrainClient = ref(false)

function formatSpeed(speed) {
    if (speed === 0 || speed === null || speed === undefined) return 'N/A'
    return Number(speed).toFixed(2)
}

function send_network_measurement_request() {
    isTestingTrainClient.value = true
    trainStore.sendCommand({
        "instruction": 'CALCULATE_NETWORK_SPEED',
        "train_id": telemetryData.value.train_id
    })
}

watch(download_speed, () => {
    isTestingWebClient.value = false
})

watch(
  () => telemetryData.value?.download_speed,
  (newVal, oldVal) => {
    if (newVal !== oldVal && newVal !== undefined) {
      isTestingTrainClient.value = false
    }
  }
)
</script>

<style scoped>
.network-panel {
  background: linear-gradient(135deg, #f8fafc 60%, #e3f0fa 100%);
  border-radius: 18px;
  overflow: hidden;
  box-shadow: 0 8px 32px rgba(0, 32, 128, 0.08), 0 1.5px 4px rgba(0,0,0,0.04);
  font-family: 'Inter', 'Segoe UI', Arial, sans-serif;
}

.network-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  gap: 24px;
  padding: 32px 24px;
}

.network-metrics {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.metric-item {
  display: flex;
  flex-direction: column;
}

.metric-label {
  font-size: 0.8rem;
  color: #7b8794;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 4px;
}

.metric-value {
  font-size: 1.5rem;
  font-weight: 700;
  color: #0096ff;
  display: flex;
  align-items: baseline;
  gap: 4px;
}

.unit {
  font-size: 0.9rem;
  color: #7b8794;
}

.test-button {
  background: linear-gradient(90deg, #0096ff, #00d4ff);
  color: #fff;
  border: none;
  border-radius: 8px;
  padding: 10px 16px;
  font-size: 0.9rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  gap: 8px;
  justify-content: center;
}

.test-button:hover:not(:disabled) {
  background: linear-gradient(90deg, #007acc, #00b8ff);
  transform: translateY(-1px);
}

.test-button:disabled {
  background: #b0b7c3;
}

.test-button .fa-spin {
  animation: fa-spin 1s infinite linear;
}

@media (max-width: 900px) {
  .network-grid {
    grid-template-columns: 1fr;
    padding: 18px 8px;
    gap: 18px;
  }
}
</style>