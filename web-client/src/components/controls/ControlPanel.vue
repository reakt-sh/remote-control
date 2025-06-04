<template>
  <div class="driver-console">
    <div class="control-panel">
      <!-- Left: Master controller -->
      <!-- <MasterController
        :speed="currentSpeed"
        :max-speed="maxSpeed"
        :power-level="powerLevel"
        @throttle-change="handleThrottleChange"
        @brake-change="handleBrakeChange"
      /> -->

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

      <!-- Right: Emergency controls -->
      <!-- <div class="emergency-panel">
        <EmergencyControls
          :emergency-brake-active="emergencyBrakeActive"
          @emergency-brake="activateEmergencyBrake"
          @reset-emergency="resetEmergency"
        />
      </div> -->
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue';
import { storeToRefs } from 'pinia';
import { useTrainStore } from '@/stores/trainStore';

import Speedometer from './Speedometer.vue';
import SystemStatus from './SystemStatus.vue';

const trainStore = useTrainStore();
const { telemetryData } = storeToRefs(trainStore);

const maxSpeed = ref(60);
const targetSpeed = ref(0);

const currentSpeed = computed(() => telemetryData.value?.speed || 0);
const systemStatus = computed(() => telemetryData.value?.status || "offline");
const batteryLevel = computed(() => telemetryData.value?.battery_level || 0);
const engineTemp = computed(() => telemetryData.value?.engine_temperature || 0);
const fuelLevel = computed(() => telemetryData.value?.fuel_level || 0);

function onTargetSpeedChange(val) {
  targetSpeed.value = val;
  console.log('onTargetSpeedChange: ', targetSpeed.value)
}

function onTargetSpeedCommit(val) {
  let data = {
    "instruction": "CHANGE_TARGET_SPEED",
    "train_id": telemetryData.value.train_id,
    "target_speed": val
  }
  trainStore.sendCommand(data);
}

watch(
  () => telemetryData.value?.train_id,
  (newTrainId, oldTrainId) => {
    if (newTrainId && newTrainId !== oldTrainId) {
      targetSpeed.value = telemetryData.value?.speed || 0;
    }
  }
);
</script>

<style scoped>
.driver-console {
  display: flex;
  flex-direction: column;
  height: auto;
  background: linear-gradient(135deg, #f5f5f5, #e0e0e0);
  color: #34495e;
  padding: 10px;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
  width: 100%;
  box-sizing: border-box;
}

.control-panel {
  display: grid;
  grid-template-columns: 1fr 2fr 1fr;
  gap: 10px;
  margin-bottom: 10px;
  width: 100%;
  box-sizing: border-box;
  align-items: center;
}

.indicators-panel {
  display: flex;
  margin-left: 340px;
  flex-direction: row;
  justify-content: center;
  align-items: stretch;
  gap: 4px;
  min-height: 360px;
  max-height: 360px;
}

.secondary-controls {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
}

.utility-controls {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.emergency-panel {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  justify-content: flex-start;
  padding-top: 20px;
  height: 350px;
  min-height: 80px;
  max-height: 350px;
}

.indicators-panel :deep(.system-status),
.indicators-panel :deep(.speedometer) {
  flex: 1 1 0;
  height: 100%;
  transform: scale(0.9);
  max-width: 400px;
  margin: 0;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.indicators-panel :deep(.system-status) {
  margin-top: 120px
}

@media (max-width: 1200px) {
  .control-panel {
    grid-template-columns: 1fr;
  }
}
</style>