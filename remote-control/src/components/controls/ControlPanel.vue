<template>
  <div class="control-panel">
    <h2>Train Controls</h2>
    <div class="control-buttons">
      <ControlButton 
        action="accelerate" 
        value="5" 
        label="Accelerate" 
        icon="fa-arrow-up" 
        type="accelerate" 
      />
      <ControlButton 
        action="decelerate" 
        value="5" 
        label="Decelerate" 
        icon="fa-arrow-down" 
        type="decelerate" 
      />
      <ControlButton 
        action="brake" 
        :value="true" 
        label="Apply Brakes" 
        icon="fa-stop" 
        type="brake" 
        :active="currentTrain.brake_status === 'applied'"
      />
      <EmergencyStop />
      <ControlButton 
        action="start" 
        :value="true" 
        label="Start Engine" 
        icon="fa-play" 
        type="start" 
        :disabled="currentTrain.status === 'running'"
      />
      <ControlButton 
        action="shutdown" 
        :value="true" 
        label="Shutdown" 
        icon="fa-power-off" 
        type="shutdown" 
        :disabled="currentTrain.status !== 'running'"
      />
    </div>
  </div>
</template>

<script setup>
import { storeToRefs } from 'pinia'
import { useTrainStore } from '@/stores/trainStore'
import ControlButton from './ControlButton.vue'
import EmergencyStop from './EmergencyStop.vue'

const { currentTrain } = storeToRefs(useTrainStore())
</script>

<style scoped>
.control-panel {
  grid-column: 1 / -1;
  background: white;
  border-radius: 5px;
  padding: 1rem;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

.control-buttons {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  grid-gap: 1rem;
}

@media (max-width: 1024px) {
  .control-buttons {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .control-buttons {
    grid-template-columns: 1fr;
  }
}
</style>