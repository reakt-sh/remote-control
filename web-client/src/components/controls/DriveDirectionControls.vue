<template>
  <div class="drive-direction-controls">
    <button
      class="control-button direction-button reverse"
      :class="{ active: direction === 'BACKWARD' }"
      :disabled="disabled"
      @click="setDirection('BACKWARD')"
    >
      <span class="label">BACKWARD</span>
    </button>

    <button
      class="control-button stop-button"
      :disabled="disabled"
      @click="handleStop"
    >
      <span class="label">STOP</span>
    </button>

    <button
      class="control-button direction-button forward"
      :class="{ active: direction === 'FORWARD' }"
      :disabled="disabled"
      @click="setDirection('FORWARD')"
    >
      <span class="label">FORWARD</span>
    </button>
  </div>
</template>

<script setup>
const emit = defineEmits(['change', 'stop'])

const props = defineProps({
  direction: {
    type: String,
    default: 'FORWARD',
    validator: (value) => ['FORWARD', 'BACKWARD'].includes(value)
  },
  disabled: {
    type: Boolean,
    default: false
  }
})

function setDirection(newDirection) {
  if (newDirection !== props.direction && !props.disabled) {
    emit('change', newDirection)
  }
}

function handleStop() {
  if (!props.disabled) {
    emit('stop')
  }
}
</script>

<style scoped>
.drive-direction-controls {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  width: 100%;
  max-width: 520px;
  padding: 10px;
  border-radius: 10px;
  background: linear-gradient(135deg, #f5f7fa, #e4e8eb);
  border: 1px solid #e0e4e7;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.06);
}

.control-button {
  min-width: 110px;
  height: 52px;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 700;
  letter-spacing: 0.5px;
  transition: all 0.2s ease;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
}

.direction-button {
  background: #a3a6a1;
  color: #2f3f46;
}

.direction-button.active {
  background: #15c724;
  color: #e8f4d1;
  box-shadow: 0 3px 10px rgba(21, 199, 36, 0.35);
}

.stop-button {
  background: linear-gradient(145deg, #f44336, #e57373);
  color: #fff;
}

.control-button:disabled {
  opacity: 0.4;
  cursor: not-allowed;
  transform: none;
}

.control-button:not(:disabled):hover {
  transform: translateY(-1px);
}

.control-button:not(:disabled):active {
  transform: translateY(0);
}

.label {
  font-size: 0.8rem;
}

@media (max-width: 700px) {
  .drive-direction-controls {
    gap: 6px;
    padding: 6px;
  }

  .control-button {
    min-width: 84px;
    height: 42px;
  }

  .label {
    font-size: 0.68rem;
  }
}

@media (max-height: 700px) {
  .control-button {
    min-width: 72px;
    height: 34px;
  }

  .label {
    font-size: 0.62rem;
  }
}
</style>
