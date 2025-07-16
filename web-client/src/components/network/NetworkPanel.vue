<template>
  <div class="network-panel">
    <div class="network-grid">
      <TelemetryCard title="Web Client Network" icon="fas fa-globe">
        <div class="network-metrics">
          <div class="metric-item">
            <div class="metric-label">Download Speed</div>
            <div class="metric-value">
              {{ formatSpeed(webClientSpeeds.download) }}
              <span class="unit">Mbps</span>
            </div>
          </div>
          <div class="metric-item">
            <div class="metric-label">Upload Speed</div>
            <div class="metric-value">
              {{ formatSpeed(webClientSpeeds.upload) }}
              <span class="unit">Mbps</span>
            </div>
          </div>
          <button class="test-button" @click="testWebClientSpeed" :disabled="isTestingWebClient">
            <i class="fas fa-sync-alt" :class="{ 'fa-spin': isTestingWebClient }"></i>
            {{ isTestingWebClient ? 'Testing...' : 'Test Web Client' }}
          </button>
        </div>
      </TelemetryCard>

      <TelemetryCard title="Train Client Network" icon="fas fa-train">
        <div class="network-metrics">
          <div class="metric-item">
            <div class="metric-label">Download Speed</div>
            <div class="metric-value">
              {{ formatSpeed(trainClientSpeeds.download) }}
              <span class="unit">Mbps</span>
            </div>
          </div>
          <div class="metric-item">
            <div class="metric-label">Upload Speed</div>
            <div class="metric-value">
              {{ formatSpeed(trainClientSpeeds.upload) }}
              <span class="unit">Mbps</span>
            </div>
          </div>
          <button class="test-button" @click="testTrainClientSpeed" :disabled="isTestingTrainClient">
            <i class="fas fa-sync-alt" :class="{ 'fa-spin': isTestingTrainClient }"></i>
            {{ isTestingTrainClient ? 'Testing...' : 'Test Train Client' }}
          </button>
        </div>
      </TelemetryCard>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { storeToRefs } from 'pinia'
import { useTrainStore } from '@/stores/trainStore'
import TelemetryCard from '@/components/telemetry/TelemetryCard.vue'

const trainStore = useTrainStore()
const { telemetryData } = storeToRefs(trainStore)

const webClientSpeeds = ref({ download: 0, upload: 0 })
const trainClientSpeeds = ref({ download: 0, upload: 0 })
const isTestingWebClient = ref(false)
const isTestingTrainClient = ref(false)

function formatSpeed(speed) {
  if (speed === 0 || speed === null || speed === undefined) return 'N/A'
  return Number(speed).toFixed(2)
}

async function testWebClientSpeed() {
  isTestingWebClient.value = true
  try {
    // Simulate network speed test for web client
    // In a real implementation, this would use a WebSocket or API call
    await new Promise(resolve => setTimeout(resolve, 2000)) // Simulate 2s test
    webClientSpeeds.value = {
      download: Math.random() * 100 + 10, // Random value for demo
      upload: Math.random() * 50 + 5      // Random value for demo
    }
  } finally {
    isTestingWebClient.value = false
  }
}

async function testTrainClientSpeed() {
  isTestingTrainClient.value = true
  try {
    // Request train client network speeds from the server
    const response = await trainStore.sendCommand({
      instruction: 'TEST_NETWORK_SPEED',
      train_id: telemetryData.value.train_id
    })
    // Simulate response for demo purposes
    await new Promise(resolve => setTimeout(resolve, 2000)) // Simulate 2s test
    trainClientSpeeds.value = {
      download: response?.download || Math.random() * 80 + 10, // Random value for demo
      upload: response?.upload || Math.random() * 40 + 5      // Random value for demo
    }
  } finally {
    isTestingTrainClient.value = false
  }
}
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