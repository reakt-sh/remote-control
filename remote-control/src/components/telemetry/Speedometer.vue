<template>
  <div>
    <div class="telemetry-value">
      {{ currentTrain.speed }}<span class="unit">km/h</span>
    </div>
    <div class="speedometer">
      <div class="speedometer-track">
        <div class="speedometer-progress" 
             :style="{ width: (currentTrain.speed / currentTrain.max_speed) * 100 + '%' }">
        </div>
      </div>
      <div class="speedometer-markers">
        <span>0</span>
        <span>{{ currentTrain.max_speed / 2 }}</span>
        <span>{{ currentTrain.max_speed }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { storeToRefs } from 'pinia'
import { useTrainStore } from '@/stores/trainStore'

const { currentTrain } = storeToRefs(useTrainStore())
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