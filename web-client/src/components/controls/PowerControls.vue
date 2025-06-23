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
  background: linear-gradient(135deg, #f5f7fa, #e4e8eb);
  border-radius: 10px;
  padding: 14px; /* increased */
  display: flex;
  flex-direction: row;
  align-items: center;
  box-shadow: 0 2px 4px rgba(0,0,0,0.06);
  border: 1px solid #e0e4e7;
  max-width: 250px; /* increased from 105px */
  margin: 0 auto;
  gap: 16px; /* Add this line for more spacing */
}

.control-button {
  width: 64px;   /* increased from 40px */
  height: 64px;  /* increased from 40px */
  border-radius: 50%;
  border: none;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.3s ease;
  font-weight: bold;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.08);
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
  opacity: 0.1;
  cursor: not-allowed;
  transform: none !important;
}

.control-button:not(:disabled):hover {
  transform: translateY(-1px);
  box-shadow: 0 3px 6px rgba(0, 0, 0, 0.12);
}

.control-button:not(:disabled):active {
  transform: translateY(0.5px);
}

.icon {
  font-size: 1.6rem; /* increased from 1rem */
  margin-bottom: 4px;
}

.label {
  font-size: 0.7rem; /* increased from 0.45rem */
  text-transform: uppercase;
  letter-spacing: 1px;
}

.active {
  box-shadow: inset 0 0 6px rgba(0, 0, 0, 0.18);
}
</style>