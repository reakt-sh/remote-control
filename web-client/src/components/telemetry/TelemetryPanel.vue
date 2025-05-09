<template>
  <div class="telemetry-panel">
    <h2>Telemetry Data</h2>
    <div class="telemetry-grid">
      <TelemetryCard title="Speed">
        <Speedometer />
      </TelemetryCard>

      <TelemetryCard title="Status">
        <StatusIndicator />
      </TelemetryCard>

      <TelemetryCard title="Brakes">
        <div v-if="currentTrain" class="telemetry-value" :class="{ warning: currentTrain.brake_status === 'applied' }">
          {{ currentTrain.brake_status }}
        </div>
        <div v-else class="telemetry-value">
          No brake data available
        </div>
      </TelemetryCard>

      <TelemetryCard title="Location">
        <div v-if="currentTrain" class="telemetry-value">
          {{ currentTrain.location }}
        </div>
        <div v-if="currentTrain" class="telemetry-subvalue">
          Next: {{ currentTrain.next_station }}
        </div>
        <div v-else>
          No location data available
        </div>
      </TelemetryCard>

      <TelemetryCard title="Battery">
        <BatteryIndicator />
      </TelemetryCard>

      <TelemetryCard title="Temperature">
        <div v-if="currentTrain" class="telemetry-value">
          {{ currentTrain.temperature }}<span class="unit">°C</span>
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
import Speedometer from './Speedometer.vue'
import StatusIndicator from './StatusIndicator.vue'
import BatteryIndicator from './BatteryIndicator.vue'

const { currentTrain } = storeToRefs(useTrainStore())
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

@media (max-width: 768px) {
  .telemetry-grid {
    grid-template-columns: 1fr;
  }
}
</style>