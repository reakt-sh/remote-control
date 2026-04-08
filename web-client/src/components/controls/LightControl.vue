<template>
  <div class="light-control">
    <div class="light-label">HEADLIGHT</div>
    <div class="switch-wrapper">
      <label class="switch">
        <input
          type="checkbox"
          class="switch__input"
          :checked="isOn"
          :disabled="disabled"
          @change="toggleLight"
        />
        <span class="switch__label">Toggle Light</span>
        <span class="switch__lever">
          <span class="switch__lever-half-top"></span>
          <span class="switch__lever-half-bottom"></span>
        </span>
        <span class="switch__lever-shadow"></span>
      </label>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const emit = defineEmits(['toggle'])

const props = defineProps({
  disabled: {
    type: Boolean,
    default: false
  },
  initialState: {
    type: Boolean,
    default: false
  }
})

const isOn = ref(props.initialState)

function toggleLight(event) {
  if (!props.disabled) {
    isOn.value = event.target.checked
    emit('toggle', isOn.value)
  }
}
</script>

<style scoped>
.light-control {
  background: linear-gradient(135deg, #f5f7fa, #e4e8eb);
  border-radius: 10px;
  padding: 4px;
  display: flex;
  flex-direction: column;
  align-items: center;
  box-shadow: 0 2px 4px rgba(0,0,0,0.06);
  border: 1px solid #e0e4e7;
  max-width: 180px;
  margin: 0 auto;
}

.light-label {
  font-size: 0.6rem;
  font-weight: bold;
  text-transform: uppercase;
  letter-spacing: 1px;
  color: #555;
  margin-bottom: 2px;
}

.switch-wrapper {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 4px;
}

/* 3D Switch Styles */
.switch,
.switch__input {
  -webkit-tap-highlight-color: transparent;
}

.switch {
  background-color: hsl(223, 10%, 90%);
  border-radius: 0.25em;
  box-shadow:
    0 2em 1em hsl(223, 10%, 70%) inset,
    0 0.1em 0 hsl(223, 10%, 90%) inset,
    0 0 0.3em hsla(223, 10%, 10%, 0.5);
  position: relative;
  transition:
    background-color 0.3s cubic-bezier(0.83, 0, 0.17, 1),
    box-shadow 0.3s cubic-bezier(0.83, 0, 0.17, 1);
  width: 2em;
  height: 3.5em;
}

.switch__input,
.switch__lever,
.switch__lever-half-top,
.switch__lever-half-bottom,
.switch__lever-shadow,
.switch__lever-shadow:before,
.switch__lever-shadow:after {
  display: block;
}

.switch__input,
.switch__label,
.switch__lever-half-top,
.switch__lever-half-bottom,
.switch__lever-shadow,
.switch__lever-shadow:before,
.switch__lever-shadow:after {
  position: absolute;
}

.switch__input {
  cursor: pointer;
  width: 100%;
  height: 100%;
  -webkit-appearance: none;
  appearance: none;
  z-index: 1;
}

.switch__input:disabled {
  cursor: not-allowed;
  opacity: 0.5;
}

.switch__label {
  overflow: hidden;
  width: 1px;
  height: 1px;
}

.switch__lever,
.switch__lever-shadow {
  pointer-events: none;
}

.switch__lever {
  background-color: hsla(223, 10%, 80%);
  border-radius: 0.15em;
  box-shadow:
    0 0 0.15em hsl(223, 10%, 10%) inset,
    0.5em 0 0.3em hsl(223, 10%, 90%) inset;
  margin: 0.25em;
  position: relative;
  transition:
    background-color 0.3s cubic-bezier(0.83, 0, 0.17, 1),
    box-shadow 0.3s cubic-bezier(0.83, 0, 0.17, 1);
  width: calc(100% - 0.5em);
  height: calc(100% - 0.5em);
}

.switch__lever:before {
  background-image: linear-gradient(hsla(223, 10%, 10%, 0), hsla(223, 10%, 10%, 0.2));
  border-radius: inherit;
  content: "";
  display: block;
  width: 100%;
  height: 100%;
}

.switch__lever-half-top,
.switch__lever-half-bottom {
  display: flex;
  justify-content: center;
  left: 0.08em;
  padding: 0.3em;
  width: calc(100% - 0.16em);
  height: calc(50% - 0.08em);
  transition:
    background-color 0.3s cubic-bezier(0.83, 0, 0.17, 1),
    transform 0.3s cubic-bezier(0.83, 0, 0.17, 1);
}

.switch__lever-half-top {
  background-color: hsl(223, 10%, 85%);
  border-radius: 0.15em 0.15em 0 0;
  bottom: 50%;
  transform-origin: 50% 100%;
}

.switch__lever-half-top:before,
.switch__lever-half-bottom:before {
  content: "";
  display: block;
  transition:
    background-color 0.3s cubic-bezier(0.83, 0, 0.17, 1),
    box-shadow 0.3s cubic-bezier(0.83, 0, 0.17, 1);
}

.switch__lever-half-top:before {
  border-radius: 50%;
  box-shadow:
    0 0 0 0.08em hsl(223, 10%, 65%) inset,
    0 0.15em 0 hsl(223, 10%, 90%) inset,
    0 0.08em 0 hsl(223, 10%, 90%);
  width: 0.5em;
  height: 0.5em;
}

.switch__lever-half-bottom {
  background-color: hsl(223, 10%, 90%);
  border-radius: 0 0 0.15em 0.15em;
  align-items: flex-end;
  top: 50%;
  transform: rotateX(-35deg);
  transform-origin: 50% 0;
}

.switch__lever-half-bottom:before {
  background-color: hsl(133, 10%, 45%);
  box-shadow:
    0 0.08em 0 hsl(133, 10%, 30%) inset,
    0 -0.04em 0 hsl(223, 10%, 90%) inset,
    0 0 0.3em hsla(133, 90%, 45%, 0);
  width: 0.15em;
  height: 0.6em;
}

.switch__lever-shadow {
  border-radius: 0.15em;
  overflow: hidden;
  top: 0.3em;
  right: 0;
  width: 3em;
  height: calc(100% - 0.15em);
}

.switch__lever-shadow:before,
.switch__lever-shadow:after {
  background-color: hsla(223, 10%, 10%, 0.15);
  content: "";
  left: 1em;
  width: 2em;
  height: 50%;
  transition:
    background-color 0.3s cubic-bezier(0.83, 0, 0.17, 1),
    transform 0.3s cubic-bezier(0.83, 0, 0.17, 1);
}

.switch__lever-shadow:before {
  border-radius: 1em 0 0 0 / 0.6em 0 0 0;
  transform-origin: 0 100%;
}

.switch__lever-shadow:after {
  border-radius: 0.15em;
  bottom: 0;
  transform: skewX(-10deg);
  transform-origin: 0 0;
}

/* `:checked` state (ON) */
.switch__input:checked ~ .switch__lever .switch__lever-half-top {
  background-color: hsl(223, 10%, 70%);
  transform: rotateX(35deg);
}

.switch__input:checked ~ .switch__lever .switch__lever-half-top:before {
  box-shadow:
    0 0 0 0.08em hsl(223, 10%, 55%) inset,
    0 0.15em 0 hsl(223, 10%, 80%) inset,
    0 0.08em 0 hsl(223, 10%, 80%);
}

.switch__input:checked ~ .switch__lever .switch__lever-half-bottom {
  background-color: hsl(223, 10%, 85%);
  transform: rotateX(0);
}

.switch__input:checked ~ .switch__lever .switch__lever-half-bottom:before {
  background-color: hsl(48, 90%, 55%);
  box-shadow:
    0 0.08em 0 hsl(48, 90%, 40%) inset,
    0 -0.04em 0 hsl(223, 10%, 90%) inset,
    0 0 0.5em hsla(48, 90%, 55%, 1),
    0 0 0.8em hsla(48, 90%, 55%, 0.8);
}

.switch__input:checked ~ .switch__lever-shadow:before {
  transform: rotate(-10deg);
}

.switch__input:checked ~ .switch__lever-shadow:after {
  transform: skewX(0) scaleY(0.85);
}

/* Tablet adjustments - smaller switch */
@media (min-width: 600px) and (max-width: 899px) {
  .light-control {
    padding: 3px;
    max-width: 140px;
  }

  .light-label {
    font-size: 0.5rem;
    margin-bottom: 2px;
  }

  .switch-wrapper {
    padding: 3px;
  }

  .switch {
    width: 1.7em;
    height: 3em;
  }

  .switch__lever-half-top:before {
    width: 0.4em;
    height: 0.4em;
  }

  .switch__lever-half-bottom:before {
    width: 0.13em;
    height: 0.5em;
  }
}

/* Mobile adjustments - even smaller switch */
@media (max-width: 599px) {
  .light-control {
    padding: 2px;
    max-width: 100px;
  }

  .light-label {
    font-size: 0.45rem;
    margin-bottom: 1px;
  }

  .switch-wrapper {
    padding: 2px;
  }

  .switch {
    width: 1.4em;
    height: 2.5em;
  }

  .switch__lever-half-top:before {
    width: 0.35em;
    height: 0.35em;
  }

  .switch__lever-half-bottom:before {
    width: 0.11em;
    height: 0.45em;
  }
}
</style>
