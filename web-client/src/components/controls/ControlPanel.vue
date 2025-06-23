<template>
  <div class="driver-console">
    <div class="primary-controls">
      <PowerControls
        :is-running="isRunning"
        @start="handleStart"
        @stop="handleStop"
      />
      <DirectionControl
        :direction="currentDirection"
        @change="handleDirectionChange"
      />
    </div>

    <div class="primary-controls">
      <Speedometer
        :current-speed="currentSpeed"
        :max-speed="maxSpeed"
        :target-speed="targetSpeed"
        @update:targetSpeed="onTargetSpeedChange"
        @change:targetSpeed="onTargetSpeedCommit"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { storeToRefs } from 'pinia'
import { useTrainStore } from '@/stores/trainStore'

import Speedometer from './Speedometer.vue'
import DirectionControl from './DirectionControl.vue'
import PowerControls from './PowerControls.vue'

const trainStore = useTrainStore()
const { telemetryData } = storeToRefs(trainStore)

// State
const maxSpeed = ref(60)
const targetSpeed = ref(0)
const isRunning = ref(false)
const currentDirection = ref('forward')
const powerLevel = ref(0)

// Computed
const currentSpeed = computed(() => telemetryData.value?.speed || 0)

// Handlers
function handleStart() {
  isRunning.value = true
  trainStore.sendCommand({
    "instruction": 'POWER_ON',
    "train_id": telemetryData.value.train_id
  })
}

function handleStop() {
  isRunning.value = false
  targetSpeed.value = 0
  powerLevel.value = 0
  trainStore.sendCommand({
    "instruction": 'POWER_OFF',
    "train_id": telemetryData.value.train_id
  })
}

function handleDirectionChange(direction) {
  currentDirection.value = direction
  trainStore.sendCommand({
    "instruction": 'CHANGE_DIRECTION',
    "train_id": telemetryData.value.train_id,
    "direction": currentDirection.value == 'forward' ? 'FORWARD' : 'BACKWARD'
  })
}

function onTargetSpeedChange(val) {
  targetSpeed.value = val
}

function onTargetSpeedCommit(val) {
  trainStore.sendCommand({
    "instruction": "CHANGE_TARGET_SPEED",
    "train_id": telemetryData.value.train_id,
    "target_speed": val
  })
}

// Watchers
watch(
  () => telemetryData.value?.train_id,
  (newTrainId, oldTrainId) => {
    if (newTrainId && newTrainId !== oldTrainId) {
      targetSpeed.value = telemetryData.value?.speed || 0
    }
  }
)
</script>

<style scoped>
.driver-console {
  display: flex;
  flex-direction: row; /* Always side by side */
  height: 100%;
  background: linear-gradient(135deg, #f5f5f5, #e0e0e0);
  color: #34495e;
  padding: 8px;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.08);
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
  width: 100%;
  box-sizing: border-box;
  gap: 16px;
}

.primary-controls {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 5px;
  min-width: 150px;
  width: 150px;
  flex: 1 1 0;
}

/* Remove any @media queries that change flex-direction */
</style>