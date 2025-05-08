<template>
  <button 
    class="control-button emergency" 
    @click="handleEmergencyStop"
  >
    <i class="fas fa-exclamation-triangle"></i> Emergency Stop
  </button>
</template>

<script setup>
import { useTrainStore } from '@/stores/trainStore'

const { sendCommand } = useTrainStore()

const handleEmergencyStop = () => {
  if (confirm('Are you sure you want to trigger emergency stop?')) {
    sendCommand('emergency_stop', true)
  }
}
</script>

<style scoped>
.control-button.emergency {
  background-color: var(--danger-color);
  color: white;
}
</style>