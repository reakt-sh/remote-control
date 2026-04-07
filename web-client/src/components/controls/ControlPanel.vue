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
  gap: 16px;
}

.main-controls-wrapper {
  display: flex;
  gap: 20px;
  width: 100%;
  min-height: 400px;
  flex-wrap: nowrap;
}

/* Left side: 2x2 Control Grid (60%) */
.controls-grid {
  flex: 0 0 40%;
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
  padding: 12px;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.08);
  transition: transform 0.2s ease, box-shadow 0.2s ease;
  min-height: 150px;
}

.control-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.12);
}

/* Right side: Speedometer (40%) */
.speedometer-section {
  flex: 0 0 40%;
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
}

/* Desktop layout: 40/60 split */
@media (min-width: 900px) {
  .main-controls-wrapper {
    flex-wrap: nowrap;
  }

  .controls-grid {
    flex: 0 0 40%;
  }

  .speedometer-section {
    flex: 0 0 40%;
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
    flex: 0 0 45%;
    gap: 2px;
    padding: 2px;
    min-height: 200px;
    max-height: 200px;
  }

  .speedometer-section {
    flex: 0 0 45%;
    padding: 2px;
    min-height: 200px;
    max-height: 200px;
  }

  .control-item {
    min-height: 120px;
    padding: 10px;
  }
}

/* Mobile adjustments */
@media (max-width: 599px) {
  .driver-console {
    padding: 8px;
  }

  .main-controls-wrapper {
    gap: 8px;
    min-height: 220px;
  }

  .controls-grid {
    flex: 0 0 48%;
    gap: 8px;
    padding: 8px;
    min-height: 220px;
  }

  .speedometer-section {
    flex: 0 0 48%;
    padding: 12px;
    min-height: 220px;
  }

  .control-item {
    min-height: 60px;
    padding: 6px;
  }
}
</style>