<template>
  <div class="driver-console">
    <div class="main-controls-wrapper">
      <!-- Left side: 2x2 Control Grid (60%) -->
      <div class="controls-grid">
        <div class="control-item control-item--power">
          <PowerControls
            @start="handleStart"
            @stop="handleStop"
          />
        </div>
        <div class="control-item control-item--direction">
          <DirectionControl
            :direction="direction"
            @change="handleDirectionChange"
          />
        </div>
        <div class="control-item control-item--light">
          <LightControl
            @toggle="handleLightToggle"
          />
        </div>
        <div class="control-item control-item--horn">
          <HornControl
            @press="handleHornPress"
            @release="handleHornRelease"
          />
        </div>
      </div>

      <!-- Right side: Speedometer (40%) -->
      <div class="speedometer-section">
        <Speedometer
          :current-speed="currentSpeed"
          :max-speed="maxSpeed"
          :target-speed="targetSpeed"
          :motor-mode="motorMode"
          @update:targetSpeed="onTargetSpeedChange"
          @change:targetSpeed="onTargetSpeedCommit"
        />
      </div>
    </div>

    <div class="scenario-controls">
      <ScenarioTestPanel
        @scenarioStateChange="handleScenarioStateChange"
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
import LightControl from './LightControl.vue'
import HornControl from './HornControl.vue'
// import VideoQuality from './VideoQuality.vue'
import ScenarioTestPanel from './ScenarioTestPanel.vue'

const trainStore = useTrainStore()
const { telemetryData, direction } = storeToRefs(trainStore)

// State
const maxSpeed = ref(13)
const targetSpeed = ref(0)
const powerLevel = ref(0)
// const videoQuality = ref('medium')
const isScenarioRunning = ref(false)

// Computed
const currentSpeed = computed(() => telemetryData.value?.speed || 0)
const motorMode = computed(() => telemetryData.value?.reaktor_motor_mode || '')

// Handlers
function handleStart() {
  trainStore.sendCommand({
    "instruction": 'POWER_ON',
    "train_id": telemetryData.value.train_id
  })
}

function handleStop() {
  targetSpeed.value = 0
  powerLevel.value = 0
  trainStore.sendCommand({
    "instruction": 'POWER_OFF',
    "train_id": telemetryData.value.train_id
  })
}

function handleDirectionChange(newDirection) {
  trainStore.sendCommand({
    "instruction": 'CHANGE_DIRECTION',
    "train_id": telemetryData.value.train_id,
    "direction": newDirection
  })
}

function handleLightToggle(isOn) {
  if (isOn) {
    onHeadlightOn()
  } else {
    onHeadlightOff()
  }
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

function onHeadlightOn() {
  trainStore.sendCommand({
    "instruction": 'HEADLIGHT_ON',
    "train_id": telemetryData.value.train_id
  })
}

function onHeadlightOff() {
  trainStore.sendCommand({
    "instruction": 'HEADLIGHT_OFF',
    "train_id": telemetryData.value.train_id
  })
}

function handleHornPress() {
  trainStore.sendCommand({
    "instruction": 'HORN_ON',
    "train_id": telemetryData.value.train_id
  })
}

function handleHornRelease() {
  trainStore.sendCommand({
    "instruction": 'HORN_OFF',
    "train_id": telemetryData.value.train_id
  })
}

// function handleQualityChange(quality) {
//   trainStore.sendCommand({
//     "instruction": "CHANGE_VIDEO_QUALITY",
//     "train_id": telemetryData.value.train_id,
//     "quality": quality
//   })
// }

function handleScenarioStateChange(running) {
  isScenarioRunning.value = running
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
  background: linear-gradient(135deg, #f5f7fa, #e8ecf1);
  color: #2c3e50;
  padding: 16px;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
  width: 100%;
  box-sizing: border-box;
}

.main-controls-wrapper {
  display: flex;
  gap: 20px;
  width: 100%;
  min-height: 400px;
  flex-wrap: nowrap;
  box-sizing: border-box;
}

/* Left side: 2x2 Control Grid (60%) */
.controls-grid {
  flex: 1;
  display: grid;
  grid-template-columns: 1fr 1fr;
  grid-template-rows: 1fr 1fr;
  gap: 16px;
  background: rgba(255, 255, 255, 0.6);
  padding: 16px;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  min-height: 400px;
}

.control-item {
  display: flex;
  align-items: center;
  justify-content: center;
  background: white;
  border-radius: 10px;
  padding: 0;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.08);
  min-height: 100px;
  overflow: hidden;
}

/* Right side: Speedometer (40%) */
.speedometer-section {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.6);
  padding: 20px;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  min-height: 400px;
}

.scenario-controls {
  display: flex;
  flex-direction: column;
  width: 100%;
  background: rgba(255, 255, 255, 0.6);
  padding: 16px;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  box-sizing: border-box;
}

/* Desktop layout: 40/60 split */
@media (min-width: 900px) {
  .main-controls-wrapper {
    flex-wrap: nowrap;
  }

  .controls-grid {
    flex: 1;
  }

  .speedometer-section {
    flex: 1;
  }
}

/* Tablet adjustments */
@media (min-width: 600px) and (max-width: 899px) {
  .main-controls-wrapper {
    gap: 2px;
    min-height: 220px;
    max-height: 220px;
  }

  .controls-grid {
    flex: 1;
    gap: 2px;
    padding: 2px;
    min-height: 200px;
    max-height: 200px;
  }

  .speedometer-section {
    flex: 1;
    padding: 2px;
    min-height: 200px;
    max-height: 200px;
  }

  .control-item {
    min-height: 80px;
    padding: 0;
  }
}

/* Mobile adjustments */
@media (max-width: 599px) {
  .driver-console {
    padding: 4px;
    max-width: 100%;
    overflow-x: hidden;
  }

  .main-controls-wrapper {
    flex-direction: column;
    gap: 4px;
    min-height: auto;
  }

  .controls-grid {
    width: 100%;
    gap: 4px;
    padding: 4px;
    min-height: 180px;
    max-height: none;
  }

  .speedometer-section {
    width: 100%;
    padding: 8px;
    min-height: 180px;
    max-height: none;
  }

  .control-item {
    min-height: 50px;
    padding: 0;
  }
  
  .scenario-controls {
    padding: 4px;
  }
}
</style>