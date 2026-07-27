<template>
  <div class="drive-controls">
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
.drive-controls {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 22px;
}

.control-button {
  position: relative;
  border: none;
  cursor: pointer;
  font-family: inherit;
  font-weight: 700;
  letter-spacing: 0.5px;
  color: #dde4e8;
  transition: filter 0.15s ease, transform 0.15s ease;
}

/* Triangular / arrow-shaped direction buttons */
.direction-button {
  width: 120px;
  height: 58px;
  background: linear-gradient(145deg, #7a7f7a, #565e5b);
  box-shadow: 0 3px 8px rgba(0, 0, 0, 0.3);
}

.direction-button.reverse {
  clip-path: polygon(30% 0, 100% 0, 100% 100%, 30% 100%, 0 50%);
  padding-left: 20px;
}

.direction-button.forward {
  clip-path: polygon(0 0, 70% 0, 100% 50%, 70% 100%, 0 100%);
  padding-right: 20px;
}

.direction-button.active {
  background: linear-gradient(145deg, #22d432, #17a524);
  color: #eefbe4;
  box-shadow: 0 0 0 2px rgba(255, 255, 255, 0.15), 0 4px 14px rgba(21, 199, 36, 0.45);
}

/* Hexagonal stop button, centered above the arrows */
.stop-button {
  width: 86px;
  height: 86px;
  z-index: 1;
  background: linear-gradient(145deg, #f0564a, #b8291f);
  clip-path: polygon(25% 0, 75% 0, 100% 50%, 75% 100%, 25% 100%, 0 50%);
  box-shadow:
    0 4px 14px rgba(184, 41, 31, 0.5),
    inset 0 1px 1px rgba(255, 255, 255, 0.25);
  color: #fff;
}

.control-button:disabled {
  opacity: 0.4;
  cursor: not-allowed;
  transform: none;
  filter: none;
}

.control-button:not(:disabled):hover {
  filter: brightness(1.12);
  transform: translateY(-2px);
}

.control-button:not(:disabled):active {
  filter: brightness(0.95);
  transform: translateY(0);
}

.label {
  font-size: 0.72rem;
}

.stop-button .label {
  font-size: 0.85rem;
}

@media (max-width: 700px) {
  .drive-controls {
    gap: 14px;
  }

  .direction-button {
    width: 92px;
    height: 46px;
  }

  .stop-button {
    width: 66px;
    height: 66px;
  }

  .label {
    font-size: 0.6rem;
  }

  .stop-button .label {
    font-size: 0.7rem;
  }
}

@media (max-height: 700px) {
  .drive-controls {
    gap: 10px;
  }

  .direction-button {
    width: 80px;
    height: 38px;
  }

  .stop-button {
    width: 56px;
    height: 56px;
  }

  .label {
    font-size: 0.56rem;
  }

  .stop-button .label {
    font-size: 0.62rem;
  }
}
</style>
