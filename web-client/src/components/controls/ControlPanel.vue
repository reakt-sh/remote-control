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

// Components
import Speedometer from './Speedometer.vue';
import SystemStatus from './SystemStatus.vue';
// import MasterController from './MasterController.vue';
// import EmergencyControls from './EmergencyControls.vue';
// import LightingControls from './LightingControls.vue';
// import DoorControls from './DoorControls.vue';
// import CommunicationPanel from './CommunicationPanel.vue';
// import HornControl from './HornControl.vue';
// import AlertPanel from './AlertPanel.vue';

const trainStore = useTrainStore();
const { telemetryData } = storeToRefs(trainStore);

// State
const maxSpeed = ref(60); // km/h
const targetSpeed = ref(0);
// const powerLevel = ref(0);
// const emergencyBrakeActive = ref(false);
// const headlightsOn = ref(true);
// const taillightsOn = ref(true);
// const doorsOpen = ref(false);
// const radioActive = ref(false);
// const activeAlerts = ref([]);

// Computed
const currentSpeed = computed(() => telemetryData.value?.speed || 0);
const systemStatus = computed(() => telemetryData.value?.status || "offline");
const batteryLevel = computed(() => telemetryData.value?.battery_level || 0);
const engineTemp = computed(() => telemetryData.value?.engine_temperature || 0);
const fuelLevel = computed(() => telemetryData.value?.fuel_level || 0);
// const hasDoors = computed(() => telemetryData.value?.has_doors || false);

// Methods
// const handleThrottleChange = (level) => {
//   powerLevel.value = level;
//   // Send command to backend
// };

// const handleBrakeChange = (level) => {
//   // Handle brake application
//   console.log(level)
// };

// const activateEmergencyBrake = () => {
//   emergencyBrakeActive.value = true;
//   // Send emergency command
// };

// const resetEmergency = () => {
//   emergencyBrakeActive.value = false;
//   // Reset emergency state
// };

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
  () => telemetryData.value?.train_id, // or selectedTrainId if you have it in this component
  (newTrainId, oldTrainId) => {
    if (newTrainId && newTrainId !== oldTrainId) {
      // Set targetSpeed to the current speed of the new train
      targetSpeed.value = telemetryData.value?.speed || 0;
    }
  }
);

// Other methods...
</script>

<style scoped>
.driver-console {
  display: flex;
  flex-direction: column;
  height: auto;
  background: #2c3e50;
  color: #ecf0f1;
  padding: 10px;           /* Reduced padding */
  border-radius: 8px;      /* Slightly smaller radius */
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.18); /* Lighter shadow */
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
  width: 100%;
  box-sizing: border-box;
}

.control-panel {
  display: grid;
  grid-template-columns: 1fr 2fr 1fr;
  gap: 10px;               /* Reduced gap */
  margin-bottom: 10px;     /* Reduced margin */
  width: 100%;
  box-sizing: border-box;
  align-items: center;     /* Vertically center items */
  min-height: unset;       /* Remove any min-height if set */
}

.indicators-panel {
  display: flex;
  margin-left: 340px;
  flex-direction: row;
  justify-content: center;
  align-items: stretch;      /* Make children take full height */
  gap: 4px;                  /* Reduce gap between them */
  min-height: 360px;
  max-height: 360px;
}

.secondary-controls {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;                /* Reduced gap */
}

.utility-controls {
  display: flex;
  flex-direction: column;
  gap: 8px;                /* Reduced gap */
}

.emergency-panel {
  display: flex;
  flex-direction: column;
  align-items: flex-end; /* Align to the right */
  justify-content: flex-start; /* Or center, if you prefer */
  padding-top: 20px;
  height: 350px;             /* Set a fixed height for both */
  min-height: 80px;
  max-height: 350px;
}

.indicators-panel :deep(.system-status),
.indicators-panel :deep(.speedometer) {
  flex: 1 1 0;
  height: 100%;              /* Force same height */
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