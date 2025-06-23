<template>
  <div class="telemetry-panel">
    <div class="panel-header">
      <h2><i class="fas fa-chart-line"></i> Telemetry Dashboard</h2>
      <div class="refresh-controls">
        <button class="panel-btn" @click="refreshTelemetry" title="Refresh Data">
          <i class="fas fa-sync-alt" :class="{ 'fa-spin': isRefreshing }"></i>
        </button>
      </div>
    </div>
    
    <div class="telemetry-grid">
      <TelemetryCard title="Passenger Count" icon="fas fa-users">
        <div v-if="telemetryData?.passenger_count !== undefined && telemetryData.passenger_count !== null">
          <PassengerCount :passenger-count="telemetryData.passenger_count" />
        </div>
        <div v-else class="telemetry-value no-data">
          <i class="fas fa-times-circle"></i> N/A
        </div>
      </TelemetryCard>

      <TelemetryCard title="System Status" icon="fas fa-heartbeat">
        <div class="status-grid">
          <div class="status-item">
            <div class="status-label">Updated</div>
            <div class="status-value">{{ formattedTime }}</div>
          </div>
          <div class="status-item">
            <div class="status-label">Signal</div>
            <div v-if="telemetryData?.network_signal_strength" class="signal-strength">
              <div class="signal-bars">
                <div v-for="n in 5" :key="n" class="signal-bar" 
                  :class="{ active: n <= Math.round(telemetryData.network_signal_strength / 20) }"></div>
              </div>
              <div class="signal-value">{{ telemetryData.network_signal_strength }}%</div>
            </div>
            <div v-else class="no-data">
              <i class="fas fa-times-circle"></i> No signal
            </div>
          </div>
        </div>
      </TelemetryCard>

      <TelemetryCard title="Location" icon="fas fa-map-marker-alt">
        <div v-if="telemetryData?.location" class="location-info">
          <div class="location-value">
            <i class="fas fa-location-arrow"></i> {{ telemetryData.location }}
          </div>
          <div v-if="telemetryData?.next_station" class="location-next">
            <i class="fas fa-arrow-right"></i> Next: {{ telemetryData.next_station }}
          </div>
          <div v-if="telemetryData?.gps" class="gps-coords">
            <div class="gps-coord">
              <i class="fas fa-longitude"></i> {{ formatCoord(telemetryData.gps.longitude) }}
            </div>
            <div class="gps-coord">
              <i class="fas fa-latitude"></i> {{ formatCoord(telemetryData.gps.latitude) }}
            </div>
          </div>
        </div>
        <div v-else class="no-data">
          <i class="fas fa-times-circle"></i> No location
        </div>
      </TelemetryCard>

      <TelemetryCard title="Environment" icon="fas fa-temperature-low">
        <div v-if="telemetryData?.temperature" class="environment-data">
          <div class="environment-item">
            <i class="fas fa-thermometer-half"></i> {{ telemetryData.temperature }}°C
          </div>
          <div v-if="telemetryData?.humidity" class="environment-item">
            <i class="fas fa-tint"></i> {{ telemetryData.humidity }}%
          </div>
        </div>
        <div v-else class="no-data">
          <i class="fas fa-times-circle"></i> No data
        </div>
      </TelemetryCard>

      <TelemetryCard title="System Health" icon="fas fa-heartbeat">
        <div class="health-metrics">
          <CircularProgress 
            v-if="telemetryData?.battery_level" 
            :value="telemetryData.battery_level" 
            label="Battery" 
            color="#4CAF50"
          />
          <CircularProgress 
            v-if="telemetryData?.fuel_level" 
            :value="telemetryData.fuel_level" 
            label="Fuel" 
            color="#2196F3"
          />
          <CircularProgress 
            v-if="telemetryData?.engine_temperature" 
            :value="telemetryData.engine_temperature" 
            :max="120"
            label="Engine Temp" 
            color="#FF5722"
          />
        </div>
      </TelemetryCard>

      <TelemetryCard title="Speed & Motion" icon="fas fa-tachometer-alt">
        <div v-if="telemetryData?.speed !== undefined" class="speed-metrics">
          <div class="speed-value">
            {{ telemetryData.speed }} <span class="unit">km/h</span>
          </div>
          <div v-if="telemetryData?.acceleration" class="acceleration">
            <i class="fas fa-bolt"></i> {{ telemetryData.acceleration }} m/s²
          </div>
        </div>
        <div v-else class="no-data">
          <i class="fas fa-times-circle"></i> No data
        </div>
      </TelemetryCard>
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { storeToRefs } from 'pinia'
import { useTrainStore } from '@/stores/trainStore'
import TelemetryCard from './TelemetryCard.vue'
import PassengerCount from './PassengerCount.vue'
import CircularProgress from './CircularProgress.vue'

const { telemetryData } = storeToRefs(useTrainStore())
const isRefreshing = ref(false)

const formattedTime = computed(() => {
  if (!telemetryData.value?.timestamp) return 'N/A'
  const ts = Number(telemetryData.value.timestamp)
  if (isNaN(ts)) return 'N/A'
  const date = new Date(ts)
  return `${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}:${date.getSeconds().toString().padStart(2, '0')}`
})

function formatCoord(val) {
  if (val === undefined || val === null || isNaN(Number(val))) return 'N/A'
  return Number(val).toFixed(4)
}

async function refreshTelemetry() {
  isRefreshing.value = true
  try {
    await useTrainStore().fetchTelemetryData()
  } finally {
    isRefreshing.value = false
  }
}
</script>

<style scoped>
.telemetry-panel {
  background: #f8fafc;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 5px 15px rgba(0, 0, 0, 0.08);
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px 20px;
  background: linear-gradient(135deg, #e3f0fa, #f8fafc);
  border-bottom: 1px solid #e0e7ef;
}

.panel-header h2 {
  margin: 0;
  font-size: 1rem;
  font-weight: 500;
  color: #222;
  display: flex;
  align-items: center;
  gap: 10px;
}

.refresh-controls {
  display: flex;
  gap: 10px;
}

.panel-btn {
  background: #e3f0fa;
  border: none;
  border-radius: 4px;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #0096ff;
  cursor: pointer;
  transition: all 0.2s;
}

.panel-btn:hover {
  background: #d0e7fa;
  color: #007acc;
}

.telemetry-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 15px;
  padding: 20px;
}

.status-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 15px;
}

.status-item {
  display: flex;
  flex-direction: column;
}

.status-label {
  font-size: 0.7rem;
  color: #7b8794;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 5px;
}

.status-value {
  font-size: 0.9rem;
  font-weight: 500;
  color: #222;
}

.signal-strength {
  display: flex;
  align-items: center;
  gap: 10px;
}

.signal-bars {
  display: flex;
  align-items: flex-end;
  height: 20px;
  gap: 2px;
}

.signal-bar {
  width: 4px;
  background: #e0e7ef;
  border-radius: 2px;
}

.signal-bar.active {
  background: linear-gradient(180deg, #4CAF50, #2E7D32);
}

.signal-value {
  font-size: 0.8rem;
  color: #7b8794;
}

.location-info {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.location-value, .location-next, .gps-coord {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.9rem;
}

.location-value {
  font-weight: 500;
  color: #222;
}

.location-next {
  color: #4b5563;
  font-size: 0.8rem;
}

.gps-coords {
  display: flex;
  flex-direction: column;
  gap: 5px;
  margin-top: 5px;
}

.gps-coord {
  font-size: 0.75rem;
  color: #7b8794;
}

.environment-data {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.environment-item {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 0.9rem;
  color: #222;
}

.health-metrics {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(80px, 1fr));
  gap: 15px;
  justify-items: center;
}

.speed-metrics {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 5px;
}

.speed-value {
  font-size: 1.5rem;
  font-weight: 600;
  color: #0096ff;
  background: none;
  -webkit-background-clip: unset;
  -webkit-text-fill-color: unset;
}

.unit {
  font-size: 0.8rem;
  color: #7b8794;
}

.acceleration {
  font-size: 0.8rem;
  color: #4b5563;
  display: flex;
  align-items: center;
  gap: 5px;
}

.no-data {
  font-size: 0.8rem;
  color: #b0b7c3;
  display: flex;
  align-items: center;
  gap: 5px;
}

@media (max-width: 768px) {
  .telemetry-grid {
    grid-template-columns: 1fr;
  }
}
</style>