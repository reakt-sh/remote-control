<template>
  <div v-if="telemetryData && telemetryData.battery_level" class="telemetry-value">
    <div class="battery-level" :style="{ width: telemetryData.battery_level + '%' }"
         :class="{ low: telemetryData.battery_level < 20 }">
    </div>
    <span>{{ telemetryData.battery_level }}%</span>
  </div>
  <div v-else class="telemetry-value">
    No battery data available
  </div>
</template>

<script setup>
import { storeToRefs } from 'pinia'
import { useTrainStore } from '@/stores/trainStore'

const { telemetryData } = storeToRefs(useTrainStore())
</script>

<style scoped>
.battery-level {
  height: 20px;
  background: var(--success-color);
  border-radius: 3px;
  margin-bottom: 0.3rem;
  transition: width 0.3s ease;
}

.battery-level.low {
  background: var(--danger-color);
}
</style>