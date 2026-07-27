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
/* Sizing tokens for the whole row.
   - The clamp() *minimums* are the real touch guarantee: they keep every
     control at a comfortable finger size (>= 48px per WCAG 2.5.5 / mobile
     HIG) even when the panel is squeezed flat.
   - The preferred value now also tracks the panel's *width* (cqw), not just
     its height, because in landscape the panel is wide but short - relying on
     cqh alone is exactly why the buttons used to collapse to their minimum.
   - min(..., Ncqh) keeps the row from spilling out of a short panel. */
.drive-controls {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: clamp(10px, 4cqh, 22px);

  --btn-height: clamp(54px, min(9cqw, 34cqh), 96px);
  --arrow-width: clamp(112px, min(22cqw, 84cqh), 200px);
  --stop-width: clamp(112px, min(22cqw, 84cqh), 200px);
  --stop-height: clamp(54px, min(9cqw, 34cqh), 96px);
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
  /* Removes the ~300ms tap delay and the grey flash so presses feel
     immediate on touchscreens. */
  touch-action: manipulation;
  -webkit-tap-highlight-color: transparent;
  user-select: none;
}

/* Triangular / arrow-shaped direction buttons. */
.direction-button {
  width: var(--arrow-width);
  height: var(--btn-height);
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

/* Rectangular stop button, same height as direction buttons */
.stop-button {
  width: var(--stop-width);
  height: var(--stop-height);
  border-radius: 10px;
  z-index: 1;
  background: linear-gradient(145deg, #f0564a, #b8291f);
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
  font-size: clamp(0.75rem, 3.8cqh, 1.05rem);
}

.stop-button .label {
  font-size: clamp(0.82rem, 4.2cqh, 1.15rem);
}

/* Landscape has more headroom (the control panel gets a taller share of
   the viewport), so let the buttons scale up further before hitting their
   caps instead of staying capped at the portrait-friendly sizes. */
@media (orientation: landscape) {
  .drive-controls {
    gap: clamp(14px, 6cqh, 32px);
  }

  .direction-button {
    width: clamp(140px, 40cqh, 280px);
    height: clamp(68px, 22cqh, 150px);
  }

  .stop-button {
    width: clamp(140px, 40cqh, 280px);
    height: clamp(68px, 22cqh, 150px);
  }

  .label {
    font-size: clamp(0.95rem, 5cqh, 1.35rem);
  }

  .stop-button .label {
    font-size: clamp(1rem, 5.4cqh, 1.45rem);
  }
}
</style>
