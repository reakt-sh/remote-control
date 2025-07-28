<template>
  <div class="network-panel">
    <div class="network-grid">
      <TelemetryCard title="Train to Server (Iperf3)" icon="fas fa-train">
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

      <!-- OpenSpeedTest Results Display -->
      <TelemetryCard title="Remote Control to Server (OpenSpeedTest)" icon="fas fa-tachometer-alt">
        <div class="network-metrics">
          <div class="metric-item">
            <div class="metric-label">Download Speed</div>
            <div class="metric-value">
              {{ formatSpeed(openSpeedTestResults.downloadSpeed) }}
              <span class="unit">Mbps</span>
            </div>
          </div>
          <div class="metric-item">
            <div class="metric-label">Upload Speed</div>
            <div class="metric-value">
              {{ formatSpeed(openSpeedTestResults.uploadSpeed) }}
              <span class="unit">Mbps</span>
            </div>
          </div>
          <div class="metric-item">
            <div class="metric-label">Ping</div>
            <div class="metric-value">
              {{ openSpeedTestResults.ping || 'N/A' }}
              <span class="unit">ms</span>
            </div>
          </div>
          <div class="metric-item">
            <div class="metric-label">Jitter</div>
            <div class="metric-value">
              {{ openSpeedTestResults.jitter || 'N/A' }}
              <span class="unit">ms</span>
            </div>
          </div>
          <button class="test-button" @click="runSpeedTest()" :disabled="openSpeedTestResults.isRunning">
            <i class="fas fa-sync-alt" :class="{ 'fa-spin': openSpeedTestResults.isRunning }"></i>
            {{ openSpeedTestResults.isRunning ? 'Calculating...' : 'Re-Calculate' }}
          </button>
        </div>
        <!-- Hidden iframe for running the test -->
        <div class="hidden-iframe">
          <iframe
            :key="iframeKey"
            :src="iframeSource"
            width="800"
            height="600"
            frameborder="0"
          ></iframe>
        </div>
      </TelemetryCard>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted, onUnmounted } from 'vue'
import { storeToRefs } from 'pinia'
import { useTrainStore } from '@/stores/trainStore'
import TelemetryCard from '@/components/telemetry/TelemetryCard.vue'

const trainStore = useTrainStore()
const { telemetryData } = storeToRefs(trainStore)
const isTestingTrainClient = ref(false)

// OpenSpeedTest results
const openSpeedTestResults = ref({
  downloadSpeed: 0,
  uploadSpeed: 0,
  ping: 0,
  jitter: 0,
  downloadDataUsed: 0,
  uploadDataUsed: 0,
  timestamp: null,
  testType: '',
  isRunning: false,
  hasResults: false
})

// Use key-based approach for iframe reload
const iframeKey = ref(0)
const iframeSource = ref('') // Start with empty source

function formatSpeed(speed) {
    if (speed === 0 || speed === null || speed === undefined) return 'N/A'
    return Number(speed).toFixed(2)
}

// Function to run the speed test
function runSpeedTest() {
  console.log('Starting speed test...')
  
  // Increment key to force iframe reload
  iframeKey.value += 1
  
  // Set the iframe source to start the test
  iframeSource.value = 'https://speedtest.rtsys-lab.de/?Run'
  
  // Set running state and reset results
  openSpeedTestResults.value = {
    downloadSpeed: 0,
    uploadSpeed: 0,
    ping: 0,
    jitter: 0,
    downloadDataUsed: 0,
    uploadDataUsed: 0,
    timestamp: null,
    testType: '',
    isRunning: true,
    hasResults: false
  }
}

// Listen for postMessage from OpenSpeedTest iframe
function handleSpeedTestMessage(event) {
  // For security, verify origin in production
  if (event.origin !== 'https://speedtest.rtsys-lab.de') {
    console.log('Message from unexpected origin:', event.origin)
    return
  }
  
  console.log('Received message from OpenSpeedTest iframe:', event)
  
  if (event.data && event.data.type === 'openspeedtest-complete') {
    const results = event.data.data
    
    openSpeedTestResults.value = {
      downloadSpeed: results.downloadSpeed || 0,
      uploadSpeed: results.uploadSpeed || 0,
      ping: results.ping || 0,
      jitter: results.jitter || 0,
      downloadDataUsed: results.downloadDataUsed || 0,
      uploadDataUsed: results.uploadDataUsed || 0,
      timestamp: results.timestamp || new Date().toISOString(),
      testType: results.testType || 'full',
      isRunning: false,
      hasResults: true
    }
    
    console.log('OpenSpeedTest Results Updated:', openSpeedTestResults.value)
  }
}

async function send_network_measurement_request() {
    isTestingTrainClient.value = true
    trainStore.sendCommand({
        "instruction": 'CALCULATE_NETWORK_SPEED',
        "train_id": telemetryData.value.train_id
    })
}

// Lifecycle hooks
onMounted(() => {
  window.addEventListener('message', handleSpeedTestMessage)
})

onUnmounted(() => {
  window.removeEventListener('message', handleSpeedTestMessage)
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

/* Special styling for iframe reload button */
.iframe-reload-btn {
  margin-bottom: 16px;
  background: linear-gradient(90deg, #28a745, #20c997);
}

.iframe-reload-btn:hover {
  background: linear-gradient(90deg, #218838, #1eb584);
}

/* Hide the iframe container but keep it functional */
.hidden-iframe {
  position: fixed;
  top: 0;
  left: 0;
  width: 800px;
  height: 600px;
  opacity: 0;
  pointer-events: none;
  z-index: -1;
  overflow: hidden;
}

.hidden-iframe iframe {
  width: 100%;
  height: 100%;
}

@media (max-width: 900px) {
  .network-grid {
    grid-template-columns: 1fr;
    padding: 18px 8px;
    gap: 18px;
  }
}
</style>