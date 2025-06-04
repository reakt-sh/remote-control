<template>
  <div class="telemetry-panel">
    <h2>Telemetry Data</h2>
    <div class="telemetry-grid">
      <TelemetryCard title="Passenger Count">
        <div v-if="telemetryData && telemetryData.passenger_count !== undefined && telemetryData.passenger_count !== null">
          <PassengerCount :passenger-count="telemetryData.passenger_count" />
        </div>
        <div v-else class="telemetry-value no-data">
          N/A
        </div>
      </TelemetryCard>

      <TelemetryCard title="Updated at">
        <div class="timestamp-block">
          <div class="timestamp-label">Date:</div>
          <div class="timestamp-value">{{ formattedDate }}</div>
          <div class="timestamp-label">Time:</div>
          <div class="timestamp-value">{{ formattedTime }}</div>
        </div>
      </TelemetryCard>

      <TelemetryCard title="Network Signal">
        <div v-if="telemetryData && telemetryData.network_signal_strength !== undefined && telemetryData.network_signal_strength !== null" class="signal-bars">
          <div
            v-for="n in 5"
            :key="n"
            class="signal-bar"
            :class="{ active: n <= Math.round(telemetryData.network_signal_strength / 20) }"
            :style="{ height: `${8 + n * 3}px` }"
          ></div>
        </div>
        <div v-else class="no-data">
          No signal
        </div>
      </TelemetryCard>

      <TelemetryCard title="Location">
        <div v-if="telemetryData && telemetryData.location" class="telemetry-value text-ellipsis">
          {{ telemetryData.location }}
        </div>
        <div v-if="telemetryData && telemetryData.next_station" class="telemetry-subvalue text-ellipsis">
          Next: {{ telemetryData.next_station }}
        </div>
        <div v-else class="no-data">
          No location
        </div>
      </TelemetryCard>

      <TelemetryCard title="GPS">
        <div v-if="telemetryData && telemetryData.gps">
          <div class="gps-block">
            <div class="gps-label">Lon:</div>
            <div class="gps-value">{{ formatCoord(telemetryData.gps.longitude) }}</div>
            <div class="gps-label">Lat:</div>
            <div class="gps-value">{{ formatCoord(telemetryData.gps.latitude) }}</div>
          </div>
        </div>
        <div v-else class="no-data">
          No GPS
        </div>
      </TelemetryCard>

      <TelemetryCard title="Temperature">
        <div v-if="telemetryData && telemetryData.temperature" class="telemetry-value">
          {{ telemetryData.temperature }}<span class="unit">°C</span>
        </div>
        <div v-else class="no-data">
          No temp
        </div>
      </TelemetryCard>
    </div>
  </div>
</template>

<script setup>
import { storeToRefs } from 'pinia'
import { useTrainStore } from '@/stores/trainStore'
import TelemetryCard from './TelemetryCard.vue'
import PassengerCount from './PassengerCount.vue'
import { computed } from 'vue'

const { telemetryData } = storeToRefs(useTrainStore())

function pad(n) {
  return n < 10 ? '0' + n : n
}

const formattedDate = computed(() => {
  if (!telemetryData.value?.timestamp) return 'N/A'
  const ts = Number(telemetryData.value.timestamp)
  if (isNaN(ts)) return 'N/A'
  const date = new Date(ts)
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`
})

const formattedTime = computed(() => {
  if (!telemetryData.value?.timestamp) return 'N/A'
  const ts = Number(telemetryData.value.timestamp)
  if (isNaN(ts)) return 'N/A'
  const date = new Date(ts)
  return `${pad(date.getHours())}:${pad(date.getMinutes())}:${pad(date.getSeconds())}`
})

function formatCoord(val) {
  if (val === undefined || val === null || isNaN(Number(val))) return 'N/A'
  return Number(val).toFixed(4)
}
</script>

<style scoped>
.telemetry-panel {
  background: linear-gradient(135deg, #ffffff, #f1f5f9);
  border-radius: 8px;
  padding: 1rem;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.08);
  max-width: 100%;
  overflow: hidden;
}

.telemetry-panel h2 {
  font-size: 1.25rem;
  color: #1f2937;
  margin-bottom: 0.75rem;
  font-weight: 600;
}

.telemetry-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 0.75rem;
}

.telemetry-value {
  font-size: 1rem;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 0.25rem;
}

.text-ellipsis {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 100%;
}

.telemetry-value .unit {
  font-size: 0.75rem;
  color: #6b7280;
  margin-left: 0.2rem;
}

.telemetry-subvalue {
  font-size: 0.75rem;
  color: #6b7280;
}

.no-data {
  font-size: 0.75rem;
  color: #9ca3af;
  font-style: italic;
}

.timestamp-block {
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 0.25rem 0.75rem;
  align-items: center;
  background: #f8fafc;
  border-radius: 4px;
  padding: 0.5rem;
}

.timestamp-label {
  font-size: 0.75rem;
  color: #6b7280;
  font-weight: 500;
  text-align: right;
}

.timestamp-value {
  font-size: 0.875rem;
  font-weight: 600;
  color: #1f2937;
}

.gps-block {
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 0.25rem 0.75rem;
  align-items: center;
  background: #f8fafc;
  border-radius: 4px;
  padding: 0.5rem;
}

.gps-label {
  font-size: 0.75rem;
  color: #6b7280;
  font-weight: 500;
  text-align: right;
}

.gps-value {
  font-size: 0.875rem;
  font-weight: 600;
  color: #1f2937;
}

.signal-bars {
  display: flex;
  align-items: flex-end;
  height: 30px;
  gap: 3px;
  margin: 0.25rem 0;
}

.signal-bar {
  flex: 1;
  background: #e5e7eb;
  border-radius: 2px;
  transition: background 0.3s ease;
}

.signal-bar.active {
  background: linear-gradient(180deg, #10b981, #059669);
}

@media (max-width: 768px) {
  .telemetry-grid {
    grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  }
}

@media (max-width: 480px) {
  .telemetry-grid {
    grid-template-columns: 1fr;
  }
}
</style>