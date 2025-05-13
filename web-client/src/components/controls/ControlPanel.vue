<template>
  <div class="driver-console">
    <div class="control-panel">
      <!-- Left: Master controller -->
      <MasterController 
        :speed="currentSpeed"
        :max-speed="maxSpeed"
        :power-level="powerLevel"
        @throttle-change="handleThrottleChange"
        @brake-change="handleBrakeChange"
      />

      <!-- Center: Indicators -->
      <div class="indicators-panel">
        <Speedometer
          :current-speed="currentSpeed"
          :max-speed="maxSpeed"
          :target-speed="targetSpeed"
          @update:targetSpeed="val => targetSpeed = val"
        />
        <SystemStatus 
          :status="systemStatus"
          :battery-level="batteryLevel"
          :engine-temp="engineTemp"
          :fuel-level="fuelLevel"
        />
      </div>

      <!-- Right: Emergency controls -->
      <div class="emergency-panel">
        <EmergencyControls 
          :emergency-brake-active="emergencyBrakeActive"
          @emergency-brake="activateEmergencyBrake"
          @reset-emergency="resetEmergency"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue';
import { storeToRefs } from 'pinia';
import { useTrainStore } from '@/stores/trainStore';

// Components
import MasterController from './MasterController.vue';
import Speedometer from './Speedometer.vue';
import SystemStatus from './SystemStatus.vue';
import EmergencyControls from './EmergencyControls.vue';
// import LightingControls from './LightingControls.vue';
// import DoorControls from './DoorControls.vue';
// import CommunicationPanel from './CommunicationPanel.vue';
// import HornControl from './HornControl.vue';
// import AlertPanel from './AlertPanel.vue';

const { telemetryData } = storeToRefs(useTrainStore());

// State
const currentSpeed = ref(0);
const targetSpeed = ref(0);
const maxSpeed = ref(120); // km/h
const powerLevel = ref(0);
const emergencyBrakeActive = ref(false);
// const headlightsOn = ref(true);
// const taillightsOn = ref(true);
// const doorsOpen = ref(false);
// const radioActive = ref(false);
// const activeAlerts = ref([]);

// Computed
const systemStatus = computed(() => telemetryData.value?.status || 'offline');
const batteryLevel = computed(() => telemetryData.value?.battery || 0);
const engineTemp = computed(() => telemetryData.value?.engine_temp || 0);
const fuelLevel = computed(() => telemetryData.value?.fuel || 0);
// const hasDoors = computed(() => telemetryData.value?.has_doors || false);

// Methods
const handleThrottleChange = (level) => {
  powerLevel.value = level;
  // Send command to backend
};

const handleBrakeChange = (level) => {
  // Handle brake application
  console.log(level)
};

const activateEmergencyBrake = () => {
  emergencyBrakeActive.value = true;
  // Send emergency command
};

const resetEmergency = () => {
  emergencyBrakeActive.value = false;
  // Reset emergency state
};

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
  flex-direction: row;
  justify-content: center;
  align-items: stretch;      /* Make children take full height */
  gap: 4px;                  /* Reduce gap between them */
  height: 400px;             /* Set a fixed height for both */
  min-height: 80px;
  max-height: 280px;
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
  height: 100%;
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

@media (max-width: 1200px) {
  .control-panel {
    grid-template-columns: 1fr;
  }
}
</style>