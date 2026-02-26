<template>
  <div class="speedometer">
    <div class="speed-display">
      <div class="speed-row">
        <div class="current-speed">{{ formattedSpeed }}</div>
        <div class="speed-unit">km/h</div>
      </div>
      <div class="target-speed">
        <div class="target-speed-value">Target: {{ tempTargetSpeed }} km/h</div>
        <button class="toggle-input-btn" @click="toggleInputMode" :disabled="disabled" :title="showSlider ? 'Switch to button input' : 'Switch to slider input'">
          <i :class="showSlider ? 'fa-solid fa-toggle-on' : 'fa-solid fa-toggle-off'"></i>
        </button>
        <div v-if="showSlider" class="slider-container">
          <input
            type="range"
            min="0"
            :max="maxSpeed"
            :value="tempTargetSpeed"
            :disabled="disabled"
            @input="e => {tempTargetSpeed = Number(e.target.value); emit('update:targetSpeed', Number(e.target.value))}"
            @change="e => {tempTargetSpeed = Number(e.target.value); emit('change:targetSpeed', Number(e.target.value))}"
            class="target-slider"
          />
        </div>
        <div v-else class="target-speed-buttons">
          <div class="button-row">
            <button class="change-speed-button" :disabled="disabled" @click="changeTargetSpeed(-10)">-10</button>
            <button class="change-speed-button" :disabled="disabled" @click="changeTargetSpeed(-1)">-1</button>
            <button class="change-speed-button" :disabled="disabled" @click="changeTargetSpeed(1)">+1</button>
            <button class="change-speed-button" :disabled="disabled" @click="changeTargetSpeed(10)">+10</button>
          </div>
          <button class="done-btn" :disabled="disabled" @click="doneTargetSpeed">Apply</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue';

const props = defineProps({
  currentSpeed: {
    type: Number,
    default: 0
  },
  targetSpeed: {
    type: Number,
    default: 0
  },
  maxSpeed: {
    type: Number,
    default: 13
  },
  disabled: {
    type: Boolean,
    default: false
  }
});
const emit = defineEmits(['update:targetSpeed', 'change:targetSpeed']);

const tempTargetSpeed = ref(props.targetSpeed);

const formattedSpeed = computed(() => {
  return Math.round(props.currentSpeed).toString().padStart(3, '0');
});

const showSlider = ref(true);

function toggleInputMode() {
  showSlider.value = !showSlider.value;
}

function changeTargetSpeed(delta) {
  let newSpeed = tempTargetSpeed.value + delta;
  newSpeed = Math.max(0, Math.min(props.maxSpeed, newSpeed));
  tempTargetSpeed.value = newSpeed;
}

function doneTargetSpeed() {
  emit('update:targetSpeed', tempTargetSpeed.value);
  emit('change:targetSpeed', tempTargetSpeed.value);
}
</script>

<style scoped>
/* Base styles (mobile first) */
.speedometer {
  background: linear-gradient(135deg, #f5f7fa, #e4e8eb);
  border-radius: 10px;
  padding: 6px;
  display: flex;
  flex-direction: column;
  align-items: center;
  box-shadow: 0 2px 4px rgba(0,0,0,0.06);
  border: 1px solid #e0e4e7;
  max-width: 120px;
  margin: 0 auto;
}

.speed-display {
  text-align: center;
  color: #333;
  width: 100%;
}

.speed-row {
  display: flex;
  align-items: baseline;
  justify-content: center;
  gap: 4px;
  margin-bottom: 4px;
}

.current-speed {
  font-size: 0.8rem;
  font-weight: bold;
  font-family: 'Segment7', monospace;
  color: #2c3e50;
  margin-bottom: 0;
}

.speed-unit {
  font-size: 0.6rem;
  color: #7f8c8d;
  margin-bottom: 0;
}

.target-speed {
  position: relative;
  background: #f8f9fa;
  padding: 6px;
  border-radius: 6px;
  box-shadow: inset 0 1px 2px rgba(0,0,0,0.03);
  border: 1px solid #e0e4e7;
}

.target-speed-value {
  display: inline-block;
  background: #2c3e50;
  color: white;
  font-weight: 500;
  padding: 3px 8px;
  border-radius: 12px;
  font-size: 0.6em;
  margin-bottom: 6px;
  margin-right: 16px;
}

.toggle-input-btn {
  position: absolute;
  top: 4px;
  right: 4px;
  width: 14px;
  height: 14px;
  border-radius: 50%;
  border: none;
  background: transparent;
  color: #7f8c8d;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0;
  transition: all 0.2s;
  font-size: 0.6em;
}

.toggle-input-btn:hover {
  background: #e0e4e7;
  color: #2c3e50;
}

.slider-container {
  width: 100%;
  padding: 4px 0;
}

.target-slider {
  width: 100%;
  height: 4px;
  -webkit-appearance: none;
  appearance: none;
  background: #e0e4e7;
  border-radius: 2px;
  outline: none;
  margin: 4px 0;
}

.target-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 10px;
  height: 10px;
  background: #2c3e50;
  border-radius: 50%;
  cursor: pointer;
  transition: all 0.2s;
}

.target-slider::-webkit-slider-thumb:hover {
  transform: scale(1.1);
  background: #e67e22;
}

.target-speed-buttons {
  flex-direction: column;
  gap: 4px;
}

.button-row {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 2px;
  flex-wrap: wrap;
}

.change-speed-button {
  max-width: 22px;
  font-size: 0.6em;
  padding: 2px 4px;
  border-radius: 4px;
  border: 1px solid #d6dbdf;
  background: #f8f9fa;
  color: #2c3e50;
  cursor: pointer;
  transition: all 0.2s;
}

.done-btn {
  font-size: 0.6em;
  padding: 3px 8px;
  background: #27ae60;
  color: white;
  border-color: #219955;
  margin-top: 4px;
}

button:hover {
  background: #e0e4e7;
  border-color: #c8d1d9;
}

button:active {
  transform: scale(0.98);
}

/* Medium screens: iPad Portrait and similar */
@media (min-width: 430px) {
  .speedometer {
    max-width: 140px;
    padding: 10px;
  }
  
  .current-speed {
    font-size: 1rem;
  }
  
  .speed-unit {
    font-size: 0.65rem;
  }
  
  .target-speed {
    padding: 6px;
  }
  
  .target-speed-value {
    padding: 3px 8px;
  }
  
  .toggle-input-btn {
    width: 16px;
    height: 16px;
    top: 5px;
    right: 5px;
    font-size: 0.7em;
  }
  
  .button-row {
    gap: 3px;
  }
  
  .change-speed-button {
    max-width: 26px;
    font-size: 0.65em;
    padding: 3px 5px;
  }
  
  .done-btn {
    font-size: 0.65em;
    padding: 3px 8px;
  }
}

@media (min-width: 700px) {
  .speedometer {
    max-width: 300px;
    width: 300px;
    padding: 12px;
  }
  
  .current-speed {
    font-size: 1.8rem;
  }
  
  .speed-unit {
    font-size: 1.3rem;
  }
  
  .speed-row {
    gap: 16px;
    margin-bottom: 8px;
  }
  
  .target-speed {
    padding: 10px;
    border-radius: 14px;
  }
  
  .target-speed-value {
    font-size: 1.1em;
    padding: 12px 24px;
    border-radius: 20px;
    margin-bottom: 14px;
    margin-right: 28px;
  }
  
  .toggle-input-btn {
    width: 40px;
    height: 40px;
    top: 12px;
    right: 12px;
    font-size: 1.6em;
  }
  
  .target-slider {
    height: 9px;
    border-radius: 4px;
    margin: 11px 0;
  }
  
  .target-slider::-webkit-slider-thumb {
    width: 26px;
    height: 26px;
  }
  
  .button-row {
    gap: 8px;
    margin-bottom: 6px;
  }
  
  .change-speed-button {
    max-width: 100px;
    min-width: 45px;
    font-size: 1.1em;
    padding: 5px 16px;
    border-radius: 10px;
  }
  
  .done-btn {
    font-size: 1.2em;
    padding: 10px 22px;
    border-radius: 10px;
  }
}
</style>