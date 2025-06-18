<template>
  <div class="driver-console">
    <div class="control-panel">
      <!-- Left: Power and Direction Controls -->
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

      <!-- Center: Indicators -->
      <div class="indicators-panel">
        <Speedometer
          :current-speed="currentSpeed"
          :max-speed="maxSpeed"
          :target-speed="targetSpeed"
          @update:targetSpeed="onTargetSpeedChange"
          @change:targetSpeed="onTargetSpeedCommit"
        />
        <SystemStatus
          :system-status="systemStatus"
          :battery-level="batteryLevel"
          :engine-temp="engineTemp"
          :fuel-level="fuelLevel"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { storeToRefs } from 'pinia'
import { useTrainStore } from '@/stores/trainStore'

import Speedometer from './Speedometer.vue'
import SystemStatus from './SystemStatus.vue'
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
const emergencyBrakeActive = ref(false)

// Computed
const currentSpeed = computed(() => telemetryData.value?.speed || 0)
const systemStatus = computed(() => isRunning.value ? 'online' : 'offline')
const batteryLevel = computed(() => telemetryData.value?.battery_level || 0)
const engineTemp = computed(() => telemetryData.value?.engine_temperature || 0)
const fuelLevel = computed(() => telemetryData.value?.fuel_level || 0)

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

function handleThrottleChange(level) {
  powerLevel.value = level
  // Additional logic can be added here
}

function handleBrakeChange(level) {
  // Brake logic implementation
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
  flex-direction: column;
  height: 100%;
  background: linear-gradient(135deg, #f5f5f5, #e0e0e0);
  color: #34495e;
  padding: 20px;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
  width: 100%;
  box-sizing: border-box;
  gap: 20px;
}

.control-panel {
  display: grid;
  grid-template-columns: 1fr 2fr 1fr;
  gap: 20px;
  width: 100%;
  box-sizing: border-box;
  align-items: center;
}

.primary-controls {
  display: flex;
  flex-direction: column;
  gap: 20px;
  padding: 15px;
  background: rgba(255, 255, 255, 0.7);
  border-radius: 10px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.indicators-panel {
  display: flex;
  flex-direction: row;
  justify-content: center;
  align-items: center;
  gap: 20px;
  height: 360px;
}

@media (max-width: 1200px) {
  .control-panel {
    grid-template-columns: 1fr;
    grid-template-rows: auto auto auto;
  }
  
  .indicators-panel {
    order: -1;
    height: auto;
    flex-direction: column;
  }
}
</style>