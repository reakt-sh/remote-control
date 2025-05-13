<template>
  <div class="emergency-controls">
    <div class="emergency-header">
      <span class="warning-icon">!</span>
      <h3>EMERGENCY CONTROLS</h3>
    </div>
    
    <button 
      class="emergency-button"
      :class="{ active: emergencyBrakeActive }"
      @click="activateEmergency"
    >
      <span class="button-icon">🛑</span>
      <span class="button-label">EMERGENCY BRAKE</span>
    </button>
    
    <button 
      class="reset-button"
      :disabled="!emergencyBrakeActive"
      @click="resetEmergency"
    >
      RESET SYSTEM
    </button>
    
    <div class="emergency-status" :class="{ active: emergencyBrakeActive }">
      {{ emergencyBrakeActive ? 'EMERGENCY BRAKE ENGAGED' : 'SYSTEM NORMAL' }}
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';

const emergencyBrakeActive = ref(false);
const emit = defineEmits(['emergency-brake', 'reset-emergency']);

const activateEmergency = () => {
  emergencyBrakeActive.value = true;
  emit('emergency-brake');
};

const resetEmergency = () => {
  emergencyBrakeActive.value = false;
  emit('reset-emergency');
};
</script>

<style scoped>
.emergency-controls {
  background: #1a1a1a;
  border-radius: 15px;
  padding: 15px;
  display: flex;
  flex-direction: column;
  gap: 15px;
  box-shadow: inset 0 0 10px rgba(0,0,0,0.5);
}

.emergency-header {
  display: flex;
  align-items: center;
  gap: 10px;
  color: #777;
  font-size: 0.9rem;
}

.warning-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 25px;
  height: 25px;
  background: #e74c3c;
  color: white;
  border-radius: 50%;
  font-weight: bold;
}

.emergency-button {
  padding: 15px;
  background: #e74c3c;
  color: white;
  border: none;
  border-radius: 10px;
  font-weight: bold;
  cursor: pointer;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 5px;
  transition: all 0.3s;
  text-transform: uppercase;
}

.emergency-button:hover {
  background: #c0392b;
}

.emergency-button.active {
  background: #c0392b;
  box-shadow: 0 0 15px rgba(231, 76, 60, 0.7);
}

.button-icon {
  font-size: 2rem;
}

.button-label {
  font-size: 0.9rem;
}

.reset-button {
  padding: 10px;
  background: #333;
  color: #ecf0f1;
  border: none;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.3s;
  text-transform: uppercase;
  font-size: 0.8rem;
}

.reset-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.reset-button:not(:disabled):hover {
  background: #444;
}

.emergency-status {
  text-align: center;
  padding: 8px;
  background: #333;
  border-radius: 5px;
  font-size: 0.8rem;
  color: #2ecc71;
  transition: all 0.3s;
}

.emergency-status.active {
  background: #e74c3c;
  color: white;
  font-weight: bold;
}
</style>