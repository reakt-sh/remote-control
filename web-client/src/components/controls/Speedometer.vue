<template>
  <div class="speedometer">
    <div class="gauge">
      <div class="ticks">
        <div v-for="tick in majorTicks" :key="tick.value"
             class="tick major-tick" :style="tick.style">
          <span class="tick-number" :style="tick.numberStyle">{{ tick.value * 2 }}</span>
        </div>
        <div v-for="tick in minorTicks" :key="tick.value"
             class="tick minor-tick" :style="tick.style"></div>
      </div>
      <div class="needle" :style="{ transform: `rotate(${needleRotation}deg)` }"></div>
      <div class="center"></div>
    </div>
    <div class="speed-display">
      <div class="speed-row">
        <div class="current-speed">{{ formattedSpeed }}</div>
        <div class="speed-unit">km/h</div>
      </div>
      <div class="target-speed">
        <div class="target-speed-value">Target: {{ tempTargetSpeed }} km/h</div>
        <button class="toggle-input-btn" @click="toggleInputMode" :title="showSlider ? 'Switch to button input' : 'Switch to slider input'">
          <i :class="showSlider ? 'fa-solid fa-toggle-on' : 'fa-solid fa-toggle-off'"></i>
        </button>
        <div v-if="showSlider" class="slider-container">
          <input
            type="range"
            min="0"
            :max="props.maxSpeed"
            :value="tempTargetSpeed"
            @input="e => {tempTargetSpeed = Number(e.target.value); emit('update:targetSpeed', Number(e.target.value))}"
            @change="e => {tempTargetSpeed = Number(e.target.value); emit('change:targetSpeed', Number(e.target.value))}"
            class="target-slider"
          />
        </div>
        <div v-else class="target-speed-buttons">
          <div class="button-row">
            <button class="change-speed-button" @click="changeTargetSpeed(-10)">-10</button>
            <button class="change-speed-button" @click="changeTargetSpeed(-1)">-1</button>
            <button class="change-speed-button" @click="changeTargetSpeed(1)">+1</button>
            <button class="change-speed-button" @click="changeTargetSpeed(10)">+10</button>
          </div>
          <button class="done-btn" @click="doneTargetSpeed">Apply</button>
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
    default: 60
  }
});
const emit = defineEmits(['update:targetSpeed', 'change:targetSpeed']);

const visualMaxSpeed = 80;
const tempTargetSpeed = ref(props.targetSpeed);

const needleRotation = computed(() => {
  const ratio = Math.min(props.currentSpeed, props.maxSpeed) / visualMaxSpeed;
  return ratio * 180 - 90;
});

const formattedSpeed = computed(() => {
  return Math.round(props.currentSpeed).toString().padStart(3, '0');
});

const majorTicks = computed(() => {
  const tickCount = 4;
  const ticks = [];
  for (let i = 0; i <= tickCount; i++) {
    const value = i * 10;
    const angle = (value / visualMaxSpeed) * 180 - 90;
    const radius = 90;
    
    const radian = (angle * Math.PI) / 180;
    const x = Math.cos(radian) * radius;
    const y = Math.sin(radian) * radius;
    
    ticks.push({
      value,
      style: {
        transform: `rotate(${angle}deg)`,
      },
      numberStyle: {
        transform: `translate(-50%, -50%) translate(${x}px, ${y}px) rotate(${-angle}deg)`,
        color: value <= 40 ? '#27ae60' : value <= 60 ? '#e67e22' : '#c0392b'
      }
    });
  }
  return ticks;
});

const minorTicks = computed(() => {
  const majorTickCount = 4;
  const minorTicksPerMajor = 5;
  const ticks = [];
  for (let i = 0; i <= majorTickCount * minorTicksPerMajor; i++) {
    if (i % minorTicksPerMajor === 0) continue;

    const value = (i / (majorTickCount * minorTicksPerMajor)) * visualMaxSpeed;
    const angle = (value / visualMaxSpeed) * 180 - 90;
    ticks.push({
      value: Math.round(value) * 2,
      style: {
        transform: `rotate(${angle}deg)`,
      }
    });
  }
  return ticks;
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

.gauge {
  width: 70px;
  height: 35px;
  position: relative;
  border: 2px solid #e0e4e7;
  border-radius: 120px 120px 0 0;
  overflow: hidden;
  margin-bottom: 8px;
  background: linear-gradient(135deg, #ffffff, #f8f9fa);
}

.gauge::before {
  content: '';
  position: absolute;
  width: 100%;
  height: 100%;
  background: conic-gradient(
    #27ae60 0deg, 
    #27ae60 90deg,
    #e67e22 90deg,
    #e67e22 135deg,
    #c0392b 135deg,
    #c0392b 180deg
  );
  clip-path: ellipse(100% 50% at 50% 100%);
  opacity: 0.3;
}

.ticks {
  position: absolute;
  width: 100%;
  height: 100%;
  z-index: 1;
}

.tick {
  position: absolute;
  left: 50%;
  bottom: 0;
  transform-origin: bottom center;
}

.major-tick {
  width: 2px;
  height: 8px;
  background: #333;
}

.minor-tick {
  width: 1px;
  height: 4px;
  background: #666;
}

.tick-number {
  position: absolute;
  font-size: 6px;
  font-weight: bold;
  text-align: center;
  width: 12px;
  height: 12px;
  line-height: 12px;
  left: 50%;
  top: 50%;
  transform-origin: center center;
}

.needle {
  position: absolute;
  width: 2px;
  height: 30px;
  background: #e67e22;
  bottom: 0;
  left: 50%;
  transform-origin: bottom center;
  z-index: 3;
  box-shadow: 0 0 2px rgba(230, 126, 34, 0.7);
  transition: transform 0.5s cubic-bezier(0.175, 0.885, 0.32, 1.275);
}

.center {
  position: absolute;
  width: 8px;
  height: 8px;
  background: linear-gradient(135deg, #ffffff, #f8f9fa);
  border: 1px solid #e67e22;
  border-radius: 50%;
  bottom: -4px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 4;
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
  margin-right: 16px; /* Add spacing between label and toggle button */
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
    max-width: 180px;
    padding: 14px;
  }
  
  .gauge {
    width: 120px;
    height: 60px;
    margin-bottom: 12px;
  }
  
  .major-tick {
    height: 10px;
  }
  
  .minor-tick {
    height: 6px;
  }
  
  .tick-number {
    font-size: 8px;
    width: 16px;
    height: 16px;
    line-height: 16px;
  }
  
  .needle {
    height: 48px;
  }
  
  .center {
    width: 12px;
    height: 12px;
    bottom: -5px;
  }
  
  .current-speed {
    font-size: 1.3rem;
  }
  
  .speed-unit {
    font-size: 0.7rem;
  }
  
  .target-speed {
    padding: 8px;
  }
  
  .target-speed-value {
    padding: 4px 10px;
  }
  
  .toggle-input-btn {
    width: 18px;
    height: 18px;
    top: 6px;
    right: 6px;
    font-size: 0.8em;
  }
  
  .button-row {
    gap: 4px;
  }
  
  .change-speed-button {
    max-width: 30px;
    font-size: 0.7em;
    padding: 4px 6px;
  }
  
  .done-btn {
    font-size: 0.7em;
    padding: 4px 10px;
  }
}

@media (min-width: 700px) {
  .speedometer {
    max-width: 340px;
    width: 340px;
    padding: 10px;
  }
  .gauge {
    width: 260px;
    height: 130px;
    margin-bottom: 24px;
    border-radius: 260px 260px 0 0;
  }
  .major-tick {
    height: 20px;
    width: 3px;
  }
  .minor-tick {
    height: 12px;
    width: 2px;
  }
  .tick-number {
    font-size: 18px;
    width: 36px;
    height: 36px;
    line-height: 36px;
  }
  .needle {
    height: 110px;
    width: 4px;
  }
  .center {
    width: 28px;
    height: 28px;
    bottom: -12px;
  }
  .current-speed {
    font-size: 2rem;
  }
  .speed-unit {
    font-size: 1.5rem;
  }
  .speed-row {
    gap: 18px;
    margin-bottom: 18px;
  }
  .target-speed {
    padding: 24px;
    border-radius: 16px;
  }
  .target-speed-value {
    font-size: 1.3em;
    padding: 16px 32px;
    border-radius: 24px;
    margin-bottom: 18px;
    margin-right: 32px;
  }
  .toggle-input-btn {
    width: 48px;
    height: 48px;
    top: 16px;
    right: 16px;
    font-size: 2em;
  }
  .target-slider {
    height: 10px;
    border-radius: 4px;
    margin: 12px 0;
  }
  .target-slider::-webkit-slider-thumb {
    width: 30px;
    height: 30px;
  }
  .button-row {
    gap: 10px;
    margin-bottom: 5px;
  }
  .change-speed-button {
    max-width: 120px;
    min-width: 50px;
    font-size: 1.3em;
    padding: 6px 15px;
    border-radius: 12px;
  }
  .done-btn {
    font-size: 1.4em;
    padding: 12px 28px;
    border-radius: 12px;
  }
}
</style>