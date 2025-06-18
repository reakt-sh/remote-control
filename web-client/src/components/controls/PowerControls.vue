<template>
  <div class="power-controls">
    <button
      class="control-button start-button"
      :class="{ active: isRunning }"
      @click="handleStart"
      :disabled="isRunning"
    >
      <span class="icon">▶</span>
      <span class="label">START</span>
    </button>
    
    <button
      class="control-button stop-button"
      :class="{ active: !isRunning }"
      @click="handleStop"
      :disabled="!isRunning"
    >
      <span class="icon">■</span>
      <span class="label">STOP</span>
    </button>
  </div>
</template>

<script setup>
const emit = defineEmits(['start', 'stop'])
const props = defineProps({
  isRunning: {
    type: Boolean,
    default: false
  }
})

function handleStart() {
  if (!props.isRunning) {
    emit('start')
  }
}

function handleStop() {
  if (props.isRunning) {
    emit('stop')
  }
}
</script>

<style scoped>
.power-controls {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.control-button {
  position: relative;
  width: 120px;
  height: 120px;
  border-radius: 50%;
  border: none;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.3s ease;
  font-weight: bold;
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
}

.start-button {
  background: linear-gradient(145deg, #4CAF50, #81C784);
  color: white;
}

.stop-button {
  background: linear-gradient(145deg, #F44336, #E57373);
  color: white;
}

.control-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none !important;
}

.control-button:not(:disabled):hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 12px rgba(0, 0, 0, 0.15);
}

.control-button:not(:disabled):active {
  transform: translateY(1px);
}

.icon {
  font-size: 2.5rem;
  margin-bottom: 8px;
}

.label {
  font-size: 1rem;
  text-transform: uppercase;
  letter-spacing: 1px;
}

.active {
  box-shadow: inset 0 0 15px rgba(0, 0, 0, 0.2);
}
</style>