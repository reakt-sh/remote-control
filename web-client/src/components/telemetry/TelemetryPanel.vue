<template>
  <div class="telemetry-panel">
    <h2>Telemetry Data</h2>
    <div class="telemetry-grid">
      <TelemetryCard title="Passenger Count">
        <div v-if="telemetryData && telemetryData.passenger_count !== undefined && telemetryData.passenger_count !== null">
          <PassengerCount :passenger-count="telemetryData.passenger_count" />
        </div>
        <div v-else class="telemetry-value">
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

      <TelemetryCard title="Brakes">
        <div v-if="telemetryData && telemetryData.brake_status" class="telemetry-value" :class="{ warning: telemetryData.brake_status === 'applied' }">
          {{ telemetryData.brake_status }}
        </div>
        <div v-else class="telemetry-value">
          No brake data available
        </div>
      </TelemetryCard>

      <TelemetryCard title="Location">
        <div v-if="telemetryData && telemetryData.location" class="telemetry-value">
          {{ telemetryData.location }}
        </div>
        <div v-if="telemetryData && telemetryData.next_station" class="telemetry-subvalue">
          Next: {{ telemetryData.next_station }}
        </div>
        <div v-else>
          No location data available
        </div>
      </TelemetryCard>

      <TelemetryCard title="Battery">
        <BatteryIndicator />
      </TelemetryCard>

      <TelemetryCard title="Temperature">
        <div v-if="telemetryData && telemetryData.temperature" class="telemetry-value">
          {{ telemetryData.temperature }}<span class="unit">°C</span>
        </div>
        <div v-else>
          No temperature data available
        </div>
      </TelemetryCard>
    </div>
  </div>
</template>

<script setup>
import { storeToRefs } from 'pinia'
import { useTrainStore } from '@/stores/trainStore'
import TelemetryCard from './TelemetryCard.vue'
import BatteryIndicator from './BatteryIndicator.vue'
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
  return `${date.getFullYear()}:${pad(date.getMonth() + 1)}:${pad(date.getDate())}`
})

const formattedTime = computed(() => {
  if (!telemetryData.value?.timestamp) return 'N/A'
  const ts = Number(telemetryData.value.timestamp)
  if (isNaN(ts)) return 'N/A'
  const date = new Date(ts)
  return `${pad(date.getHours())}:${pad(date.getMinutes())}:${pad(date.getSeconds())}`
})
</script>

<style scoped>
.telemetry-panel {
  background: white;
  border-radius: 5px;
  padding: 1rem;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

.telemetry-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  grid-gap: 1rem;
}

.telemetry-value {
  font-size: 1.5rem;
  font-weight: bold;
  margin-bottom: 0.5rem;
}

.telemetry-value .unit {
  font-size: 1rem;
  color: var(--text-light);
  margin-left: 0.2rem;
}

.telemetry-subvalue {
  font-size: 0.8rem;
  color: var(--text-light);
}

.warning {
  color: var(--warning-color);
}

.timestamp-block {
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 2px 12px;
  align-items: center;
  background: #f8f9fa;
  border-radius: 8px;
  padding: 10px 14px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.04);
}

.timestamp-label {
  font-size: 1rem;
  color: #888;
  font-weight: 500;
  text-align: right;
}

.timestamp-value {
  font-size: 1.15rem;
  font-weight: bold;
  color: #222;
  letter-spacing: 1px;
}

@media (max-width: 768px) {
  .telemetry-grid {
    grid-template-columns: 1fr;
  }
}
</style>