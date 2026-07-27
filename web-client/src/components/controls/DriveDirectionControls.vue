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
  gap: clamp(10px, 4cqh, 22px);
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

/* Triangular / arrow-shaped direction buttons.
   Sized off the control panel's own height (cqh) so they scale up to fill
   leftover space on tall/short screens alike, instead of relying on fixed
   viewport breakpoints. */
.direction-button {
  width: clamp(78px, 25cqh, 180px);
  height: clamp(38px, 12cqh, 90px);
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
  width: clamp(56px, 17.5cqh, 130px);
  height: clamp(56px, 17.5cqh, 130px);
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
  font-size: clamp(0.56rem, 3cqh, 0.85rem);
}

.stop-button .label {
  font-size: clamp(0.62rem, 3.4cqh, 0.9rem);
}

/* Landscape has more headroom (the control panel gets a taller share of
   the viewport), so let the buttons scale up further before hitting their
   caps instead of staying capped at the portrait-friendly sizes. */
@media (orientation: landscape) {
  .drive-controls {
    gap: clamp(12px, 5cqh, 28px);
  }

  .direction-button {
    width: clamp(90px, 30cqh, 230px);
    height: clamp(46px, 15cqh, 115px);
  }

  .stop-button {
    width: clamp(66px, 21cqh, 165px);
    height: clamp(66px, 21cqh, 165px);
  }

  .label {
    font-size: clamp(0.62rem, 3.6cqh, 1rem);
  }

  .stop-button .label {
    font-size: clamp(0.68rem, 4cqh, 1.05rem);
  }
}
</style>
