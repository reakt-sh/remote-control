<template>
  <div>
    <div v-if="telemetryData && telemetryData.speed" class="telemetry-value">
      {{ telemetryData.speed }}<span class="unit">km/h</span>
    </div>
    <div v-if="telemetryData && telemetryData.speed" class="speedometer">
      <div class="speedometer-track">
        <div class="speedometer-progress"
             :style="{ width: (telemetryData.speed / telemetryData.max_speed) * 100 + '%' }">
        </div>
      </div>
      <div class="speedometer-markers">
        <span>0</span>
        <span>{{ telemetryData.max_speed / 2 }}</span>
        <span>{{ telemetryData.max_speed }}</span>
      </div>
    </div>
    <div v-else>
      <p>No train data available</p>
    </div>
  </div>
</template>



<script setup>
import { storeToRefs } from 'pinia'
import { useTrainStore } from '@/stores/trainStore'

const { telemetryData } = storeToRefs(useTrainStore())
</script>

<style scoped>
.speedometer {
  margin-top: 0.5rem;
}

.speedometer-track {
  height: 8px;
  background: #eee;
  border-radius: 4px;
  overflow: hidden;
  margin-bottom: 0.3rem;
}

.speedometer-progress {
  height: 100%;
  background: var(--secondary-color);
  transition: width 0.3s ease;
}

.speedometer-markers {
  display: flex;
  justify-content: space-between;
  font-size: 0.7rem;
  color: var(--text-light);
}
</style>