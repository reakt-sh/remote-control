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
        <div class="target-speed-value">Target: {{ props.targetSpeed }} km/h</div>
        <input
          type="range"
          min="0"
          :max="props.maxSpeed"
          :value="props.targetSpeed"
          @input="e => emit('update:targetSpeed', Number(e.target.value))"
          @change="e => emit('change:targetSpeed', Number(e.target.value))"
          class="target-slider"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue';

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
</script>

<style scoped>
.speedometer {
  background: #f5f5f5;
  border-radius: 15px;
  padding: 20px;
  display: flex;
  flex-direction: column;
  align-items: center;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.gauge {
  width: 220px;
  height: 110px;
  position: relative;
  border: 4px solid #ccc;
  border-radius: 220px 220px 0 0;
  overflow: hidden;
  margin-bottom: 20px;
  background: #ffffff;
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
  height: 15px;
  background: #333;
}

.minor-tick {
  width: 1px;
  height: 10px;
  background: #666;
}

.tick-number {
  position: absolute;
  font-size: 12px;
  font-weight: bold;
  text-align: center;
  width: 20px;
  height: 20px;
  line-height: 20px;
  left: 50%;
  top: 50%;
  transform-origin: center center;
}

.needle {
  position: absolute;
  width: 3px;
  height: 80px;
  background: #e67e22;
  bottom: 0;
  left: 50%;
  transform-origin: bottom center;
  z-index: 3;
  box-shadow: 0 0 5px rgba(230, 126, 34, 0.7);
  transition: transform 0.5s cubic-bezier(0.175, 0.885, 0.32, 1.275);
}

.center {
  position: absolute;
  width: 20px;
  height: 20px;
  background: #ffffff;
  border: 3px solid #e67e22;
  border-radius: 50%;
  bottom: -10px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 4;
}

.speed-display {
  text-align: center;
  color: #333;
}

.speed-row {
  display: flex;
  align-items: baseline;
  justify-content: center;
  gap: 10px;
}

.current-speed {
  font-size: 3rem;
  font-weight: bold;
  font-family: 'Segment7', monospace;
  color: #e67e22;
  margin-bottom: 0;
}

.speed-unit {
  font-size: 1.2rem;
  opacity: 0.7;
  margin-bottom: 0;
}

.target-speed {
  font-size: 1rem;
  min-width: 300px;
  color: #333;
  background: #e0e0e0;
  padding: 10px 10px 10px 10px;
  border-radius: 18px;
  margin-top: 10px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  position: relative;
}

.target-slider {
  width: 280px;
  height: 55px;
  background: #e0e0e0;
  border-radius: 20px;
  box-shadow: inset 0 0 15px rgba(0,0,0,0.2);
  margin: 0 auto;
  margin-top: 5px;
  display: block;
  padding: 0;
  outline: none;
  -webkit-appearance: none;
  appearance: none;
  position: relative;
  cursor: pointer;
}

.target-slider::-webkit-slider-runnable-track {
  width: 100%;
  height: 40px;
  background: #e0e0e0;
  border-radius: 20px;
}
.target-slider::-moz-range-track {
  width: 100%;
  height: 40px;
  background: #e0e0e0;
  border-radius: 20px;
}
.target-slider::-ms-fill-lower,
.target-slider::-ms-fill-upper {
  background: #e0e0e0;
  border-radius: 20px;
}

.target-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 80px;
  height: 40px;
  background: linear-gradient(to right, #ccc, #aaa);
  border-radius: 5px;
  border: 2px solid #999;
  box-shadow: 0 2px 5px rgba(0,0,0,0.2);
  cursor: ew-resize;
  transition: background 0.2s;
  margin-top: 0;
}
.target-slider:focus::-webkit-slider-thumb {
  background: #999;
}

.target-slider::-moz-range-thumb {
  width: 80px;
  height: 40px;
  background: linear-gradient(to right, #ccc, #aaa);
  border-radius: 5px;
  border: 2px solid #999;
  box-shadow: 0 2px 5px rgba(0,0,0,0.2);
  cursor: ew-resize;
  transition: background 0.2s;
}
.target-slider:focus::-moz-range-thumb {
  background: #999;
}

.target-slider::-ms-thumb {
  width: 80px;
  height: 40px;
  background: linear-gradient(to right, #ccc, #aaa);
  border-radius: 5px;
  border: 2px solid #999;
  box-shadow: 0 2px 5px rgba(0,0,0,0.2);
  cursor: ew-resize;
  transition: background 0.2s;
}
.target-slider:focus::-ms-thumb {
  background: #999;
}

.target-slider::-moz-focus-outer {
  border: 0;
}

.target-speed {
  position: relative;
}
.target-speed-value {
  top: 0;
  max-width: 155px;
  margin-left: 58px;
  background: #d0d6d6;
  color: #333;
  font-weight: bold;
  padding: 2px 10px;
  border-radius: 10px;
  font-size: 1.1em;
  box-shadow: 0 1px 4px rgba(0,0,0,0.1);
  pointer-events: none;
  z-index: 2;
}
</style>