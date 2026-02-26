<template>
  <div class="power-controls">
    <button
      class="control-button start-button"
      :class="{ active: !isPoweredOn }"
      @click="handleStart"
      :disabled="isPoweredOn || disabled"
    >
      <span class="icon">▶</span>
      <span class="label">START</span>
    </button>

    <button
      class="control-button stop-button"
      :class="{ active: isPoweredOn }"
      @click="handleStop"
      :disabled="!isPoweredOn || disabled"
    >
      <span class="icon">■</span>
      <span class="label">STOP</span>
    </button>
  </div>
</template>

<script setup>
import { storeToRefs } from 'pinia'
import { useTrainStore } from '@/stores/trainStore'

const trainStore = useTrainStore()
const { isPoweredOn } = storeToRefs(trainStore)
const emit = defineEmits(['start', 'stop'])

defineProps({
  disabled: {
    type: Boolean,
    default: false
  }
})

function handleStart() {
    emit('start')
}

function handleStop() {
    emit('stop')
}
</script>

<style scoped>
.power-controls {
  background: linear-gradient(135deg, #f5f7fa, #e4e8eb);
  border-radius: 10px;
  padding: 8px; /* reduced for height */
  display: flex;
  flex-direction: row;
  align-items: center;
  box-shadow: 0 2px 4px rgba(0,0,0,0.06);
  border: 1px solid #e0e4e7;
  max-width: 250px; /* increased from 105px */
  margin: 0 auto;
  gap: 12px; /* reduced for height */
}

.control-button {
  width: 58px;   /* increased button size */
  height: 58px;  /* increased button size */
  border-radius: 50%;
  border: none;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.3s ease;
  font-weight: bold;
  /* Enhanced shadow for better visibility */
  box-shadow: 0 4px 16px rgba(0,0,0,0.18), 0 1.5px 4px rgba(0,0,0,0.10);
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
  font-size: 1.5rem; /* increased */
  margin-bottom: 2px;
}

.label {
  font-size: 0.65rem; /* increased */
  text-transform: uppercase;
  letter-spacing: 1px;
}

.active {
  /* Stronger inset shadow when active */
  box-shadow: 0 4px 16px rgba(0,0,0,0.18), 0 1.5px 4px rgba(0,0,0,0.10), inset 0 0 12px rgba(0,0,0,0.22);
}

@media (min-width: 700px) {
  .power-controls {
    max-width: 240px;
    gap: 14px;
    padding: 10px;
  }
  .control-button {
    width: 62px;
    height: 62px;
  }
  .icon {
    font-size: 1.6rem;
    margin-bottom: 5px;
  }
  .label {
    font-size: 0.75rem;
  }
}

@media (max-height: 700px) {
  .power-controls {
    max-width: 180px;
    padding: 8px;
    gap: 8px;
  }
  .control-button {
    width: 40px;
    height: 40px;
  }
  .icon {
    font-size: 1rem;
    margin-bottom: 2px;
  }
  .label {
    font-size: 0.5rem;
  }
}
</style>