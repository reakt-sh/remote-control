<template>
  <div class="driver-console">
    <DriveDirectionControls
      :direction="direction"
      @change="handleDirectionChange"
      @stop="handleStop"
    />
    <div class="control-divider" aria-hidden="true"></div>
    <!-- <LightControl @toggle="handleLightToggle" /> -->
    <!-- <HornControl @press="handleHornPress" @release="handleHornRelease" /> -->
    <SpeedControl
      :target-speed="targetSpeed"
      :max-speed="maxSpeed"
      @update:targetSpeed="onTargetSpeedChange"
      @change:targetSpeed="onTargetSpeedCommit"
    />
    <!-- <ScenarioTestPanel @scenarioStateChange="handleScenarioStateChange" /> -->
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { storeToRefs } from 'pinia'
import { useTrainStore } from '@/stores/trainStore'

import SpeedControl from './SpeedControl.vue'
import DriveDirectionControls from './DriveDirectionControls.vue'
// import LightControl from './LightControl.vue'
// import HornControl from './HornControl.vue'
// import VideoQuality from './VideoQuality.vue'
// import ScenarioTestPanel from './ScenarioTestPanel.vue'

const trainStore = useTrainStore()
const { telemetryData, direction } = storeToRefs(trainStore)

// State
const maxSpeed = ref(13)
const targetSpeed = ref(0)
const powerLevel = ref(0)
// const videoQuality = ref('medium')
// const isScenarioRunning = ref(false)

// Handlers
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

// function handleLightToggle(isOn) {
//   if (isOn) {
//     onHeadlightOn()
//   } else {
//     onHeadlightOff()
//   }
// }

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

// function onHeadlightOn() {
//   trainStore.sendCommand({
//     "instruction": 'HEADLIGHT_ON',
//     "train_id": telemetryData.value.train_id
//   })
// }

// function onHeadlightOff() {
//   trainStore.sendCommand({
//     "instruction": 'HEADLIGHT_OFF',
//     "train_id": telemetryData.value.train_id
//   })
// }

// function handleHornPress() {
//   trainStore.sendCommand({
//     "instruction": 'HORN_ON',
//     "train_id": telemetryData.value.train_id
//   })
// }

// function handleHornRelease() {
//   trainStore.sendCommand({
//     "instruction": 'HORN_OFF',
//     "train_id": telemetryData.value.train_id
//   })
// }

// function handleQualityChange(quality) {
//   trainStore.sendCommand({
//     "instruction": "CHANGE_VIDEO_QUALITY",
//     "train_id": telemetryData.value.train_id,
//     "quality": quality
//   })
// }

// function handleScenarioStateChange(running) {
//   isScenarioRunning.value = running
// }

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
  flex-direction: row;
  flex-wrap: wrap;
  align-items: center;
  justify-content: center;
  gap: 12px;
  /* Grow to consume whatever vertical space is left under the video panel,
     rather than only taking the height of its own content. */
  flex: 1 1 auto;
  min-height: 0;
  background: linear-gradient(135deg, #f5f7fa, #e8ecf1);
  color: #2c3e50;
  padding: 10px;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
  width: 100%;
  box-sizing: border-box;
  overflow-x: hidden;
  /* Establish a query container so child controls (direction/speed buttons)
     can size themselves off the panel's actual rendered size instead of the
     raw viewport. */
  container-type: size;
  container-name: control-panel;
}

.control-divider {
  width: 1px;
  align-self: stretch;
  margin: 4px 10px;
  background: rgba(44, 62, 80, 0.15);
}

/* Tablets/portrait: stop relying on a fixed row width, stack instead so
   nothing gets clipped regardless of the device's raw pixel width. */
@media (max-width: 899px), (orientation: portrait) {
  .driver-console {
    flex-direction: column;
    gap: 8px;
    padding: 8px;
    max-width: 100%;
  }

  .control-divider {
    width: 60%;
    height: 1px;
    margin: 2px 0;
    align-self: center;
  }
}

/* Phones */
@media (max-width: 599px) {
  .driver-console {
    gap: 4px;
    padding: 4px;
  }
}

</style>