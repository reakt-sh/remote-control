<template>
  <div class="horn-control">
    <!-- SVG Symbol Definition -->
    <svg style="display: none;">
      <symbol id="horn-icon" viewBox="0 0 24 24">
        <g class="horn-icon">
          <path d="M3 9v6h4l5 5V4L7 9H3z" fill="currentColor"/>
          <path class="wave wave-1" d="M15.54 8.46a5 5 0 0 1 0 7.07" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round"/>
          <path class="wave wave-2" d="M17.07 6.93a8 8 0 0 1 0 10.14" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round"/>
          <path class="wave wave-3" d="M18.364 5.636a11 11 0 0 1 0 12.728" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round"/>
        </g>
      </symbol>
    </svg>

    <button 
      ref="hornBtn"
      class="horn-btn" 
      type="button" 
      :aria-pressed="isPressed.toString()"
      :disabled="disabled"
      @mousedown="handlePressStart"
      @mouseup="handlePressEnd"
      @mouseleave="handlePressEnd"
      @touchstart.passive="handlePressStart"
      @touchend="handlePressEnd"
      @touchcancel="handlePressEnd"
      @keydown="handleKeyDown"
      @keyup="handleKeyUp"
    >
      <svg class="horn-btn__icon" width="32px" height="32px" aria-hidden="true">
        <use href="#horn-icon"/>
      </svg>
      <span class="horn-btn__sr">Horn</span>
    </button>
  </div>
</template>

<script setup>
import { ref, onUnmounted } from 'vue'

const emit = defineEmits(['press', 'release', 'hold'])

const props = defineProps({
  disabled: {
    type: Boolean,
    default: false
  }
})

const isPressed = ref(false)
const hornBtn = ref(null)
const holdInterval = ref(null)

function handlePressStart() {
  if (props.disabled || isPressed.value) return
  
  isPressed.value = true
  emit('press')
  
  // Start sending hold/reset commands every 100ms
  holdInterval.value = setInterval(() => {
    if (isPressed.value) {
      emit('hold')
    }
  }, 100)
}

function handlePressEnd() {
  if (props.disabled || !isPressed.value) return
  // Clear the interval
  if (holdInterval.value) {
    clearInterval(holdInterval.value)
    holdInterval.value = null
  }
  isPressed.value = false
  emit('release')
}

function handleKeyDown(event) {
  if (props.disabled) return
  
  // Activate on Space or Enter key
  if ((event.key === ' ' || event.key === 'Enter') && !isPressed.value) {
    event.preventDefault() // Prevent page scroll on space
    handlePressStart(event)
  }
}

function handleKeyUp(event) {
  if (props.disabled) return
  
  // Deactivate on Space or Enter key release
  if (event.key === ' ' || event.key === 'Enter') {
    event.preventDefault()
    handlePressEnd(event)
  }
}

// Cleanup on component unmount
onUnmounted(() => {
  if (holdInterval.value) {
    clearInterval(holdInterval.value)
  }
})
</script>

<style scoped>
* {
  box-sizing: border-box;
}

.horn-control {
  /* Variables for horn button accent - amber/orange */
  --horn-hue: 38;
  --horn-sat: 95%;
  --horn-light: 55%;
  --horn-color: hsl(var(--horn-hue), var(--horn-sat), var(--horn-light));
  --trans-dur: 0.3s;
  --trans-timing: ease-in-out;
  --trans-timing2: cubic-bezier(0.42, -1.84, 0.42, 1.84);
  --trans-timing3: cubic-bezier(0.42, 0, 0.42, 1.84);
  
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 0;
  min-height: 7em;
}

/* Horn Button - Round Shape */
.horn-btn {
  background-color: transparent;
  background-image: linear-gradient(
    hsl(223, 10%, 80%),
    hsl(223, 10%, 85%)
  );
  border: none;
  border-radius: 50%;
  box-shadow:
    0 0 0 0.125em hsla(var(--horn-hue), var(--horn-sat), 50%, 0),
    0 0 0.25em hsl(223, 10%, 55%) inset,
    0 0.125em 0.125em hsl(223, 10%, 90%);
  cursor: pointer;
  margin: auto;
  outline: transparent;
  position: relative;
  width: 6em;
  height: 6em;
  transition: box-shadow var(--trans-dur) var(--trans-timing);
  -webkit-tap-highlight-color: transparent;
}

.horn-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.horn-btn:focus-visible {
  box-shadow:
    0 0 0 0.125em hsla(var(--horn-hue), var(--horn-sat), 50%, 1),
    0 0 0.25em hsl(223, 10%, 55%) inset,
    0 0.125em 0.125em hsl(223, 10%, 90%);
}

.horn-btn:before,
.horn-btn:after {
  border-radius: inherit;
  content: "";
  display: block;
  position: absolute;
}

/* Outer shadow layer */
.horn-btn:before {
  background-image: linear-gradient(
    hsl(223, 10%, 80%)
  );
  box-shadow: 0 0.4em 0.4em 0.13em hsla(0, 0%, 0%, 0.3);
  top: 0.85em;
  left: 0.85em;
  width: 4.3em;
  height: 4.3em;
  transition:
    box-shadow var(--trans-dur) var(--trans-timing2),
    transform var(--trans-dur) var(--trans-timing2);
}

/* Inner button surface */
.horn-btn:after {
  background-color: hsl(223, 10%, 75%);
  background-image: linear-gradient(
    hsla(223, 10%, 90%, 0),
    hsl(223, 10%, 90%)
  );
  box-shadow:
    0 0.0625em 0 hsl(223, 10%, 90%) inset,
    0 -0.0625em 0 hsl(223, 10%, 90%) inset,
    0 0 0 0 hsla(var(--horn-hue), var(--horn-sat), var(--horn-light), 0.1) inset;
  top: 1.7em;
  left: 1.7em;
  width: 2.6em;
  height: 2.6em;
  transition:
    background-color var(--trans-dur) var(--trans-timing),
    box-shadow var(--trans-dur) var(--trans-timing),
    transform var(--trans-dur) var(--trans-timing2);
}

/* Horn Icon */
.horn-btn__icon {
  display: block;
  position: absolute;
  top: calc(50% - 1em);
  left: calc(50% - 1em);
  width: 2em;
  height: 2em;
  transition: filter var(--trans-dur) var(--trans-timing);
  z-index: 1;
}

.horn-btn__icon :deep(.horn-icon) {
  color: hsl(223, 10%, 70%);
  transition: color var(--trans-dur) var(--trans-timing);
}

.horn-btn__icon :deep(.wave) {
  opacity: 0;
  transform-origin: center;
  transition: opacity 0.2s var(--trans-timing);
}

.horn-btn__sr {
  overflow: hidden;
  position: absolute;
  width: 1px;
  height: 1px;
}

/* Pressed State - Active Horn */
.horn-btn[aria-pressed="true"]:before,
.horn-btn[aria-pressed="true"]:after,
.horn-btn[aria-pressed="true"] .horn-btn__icon {
  transform: scale(0.95);
}

.horn-btn[aria-pressed="true"]:before {
  box-shadow: 0 0.375em 0.375em 0 hsla(0, 0%, 0%, 0.3);
  transition-timing-function: var(--trans-timing3);
}

.horn-btn[aria-pressed="true"]:after {
  background-color: hsl(var(--horn-hue), var(--horn-sat), 60%);
  box-shadow:
    0 0.0625em 0 hsla(var(--horn-hue), var(--horn-sat), var(--horn-light), 0.5) inset,
    0 -0.0625em 0 hsla(var(--horn-hue), var(--horn-sat), var(--horn-light), 0.5) inset,
    0 0 1em 0.5em hsla(var(--horn-hue), var(--horn-sat), var(--horn-light), 0.2) inset,
    0 0 2em 1em hsla(var(--horn-hue), var(--horn-sat), var(--horn-light), 0.3);
  transition-timing-function: var(--trans-timing), var(--trans-timing), var(--trans-timing3);
}

.horn-btn[aria-pressed="true"] .horn-btn__icon {
  filter: drop-shadow(0 0 0.5em var(--horn-color));
}

.horn-btn[aria-pressed="true"] .horn-btn__icon :deep(.horn-icon) {
  color: var(--horn-color);
}

/* Animated sound waves */
.horn-btn[aria-pressed="true"] :deep(.wave) {
  opacity: 1;
  animation: wave-pulse 1s ease-in-out infinite;
}

.horn-btn[aria-pressed="true"] :deep(.wave-1) {
  animation-delay: 0s;
}

.horn-btn[aria-pressed="true"] :deep(.wave-2) {
  animation-delay: 0.15s;
}

.horn-btn[aria-pressed="true"] :deep(.wave-3) {
  animation-delay: 0.3s;
}

@keyframes wave-pulse {
  0%, 100% {
    opacity: 0.3;
    transform: scale(1);
  }
  50% {
    opacity: 1;
    transform: scale(1.1);
  }
}

/* Disabled state */
.horn-btn:disabled:before,
.horn-btn:disabled:after {
  opacity: 0.5;
}

.horn-btn:disabled .horn-btn__icon {
  opacity: 0.5;
}

/* Tablet adjustments - smaller button */
@media (min-width: 600px) and (max-width: 899px) {
  .horn-control {
    padding: 0;
    min-height: 5em;
  }

  .horn-btn {
    width: 4.5em;
    height: 4.5em;
  }

  .horn-btn:before {
    box-shadow: 0 0.3em 0.3em 0.08em hsla(0, 0%, 0%, 0.3);
    top: 0.65em;
    left: 0.65em;
    width: 3.2em;
    height: 3.2em;
  }

  .horn-btn:after {
    top: 1.3em;
    left: 1.3em;
    width: 1.9em;
    height: 1.9em;
  }

  .horn-btn__icon {
    width: 1.3em;
    height: 1.3em;
    top: calc(50% - 0.65em);
    left: calc(50% - 0.65em);
  }
}

/* Mobile adjustments - even smaller button */
@media (max-width: 599px) {
  .horn-control {
    padding: 0;
    min-height: 3.5em;
  }

  .horn-btn {
    width: 3.2em;
    height: 3.2em;
  }

  .horn-btn:before {
    box-shadow: 0 0.2em 0.2em 0.05em hsla(0, 0%, 0%, 0.3);
    top: 0.5em;
    left: 0.5em;
    width: 2.2em;
    height: 2.2em;
  }

  .horn-btn:after {
    top: 0.95em;
    left: 0.95em;
    width: 1.3em;
    height: 1.3em;
  }

  .horn-btn__icon {
    width: 1em;
    height: 1em;
    top: calc(50% - 0.5em);
    left: calc(50% - 0.5em);
  }
}
</style>
