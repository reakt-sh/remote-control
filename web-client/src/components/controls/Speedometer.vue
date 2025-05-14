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

// Visual range is 0-80, but functional max is 60
const visualMaxSpeed = 80;

const needleRotation = computed(() => {
  // Calculate ratio based on visual range (0-80)
  const ratio = Math.min(props.currentSpeed, props.maxSpeed) / visualMaxSpeed;
  return ratio * 180 - 90;
});

const formattedSpeed = computed(() => {
  return Math.round(props.currentSpeed).toString().padStart(3, '0');
});

const majorTicks = computed(() => {
  const tickCount = 4; // 0, 10, 20, ..., 80
  const ticks = [];
  for (let i = 0; i <= tickCount; i++) {
    const value = i * 10; // 0, 10, 20, ..., 80
    const angle = (value / visualMaxSpeed) * 180 - 90;
    const radius = 90; // Distance from center to numbers
    
    // Calculate position for numbers
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
        color: value <= 40 ? '#2ecc71' : value <= 60 ? '#f1c40f' : '#e74c3c'
      }
    });
  }
  return ticks;
});

const minorTicks = computed(() => {
  const majorTickCount = 4; // For 0-80 in steps of 10
  const minorTicksPerMajor = 5; // Results in ticks every 2 km/h (80/8/5 = 2)
  const ticks = [];
  for (let i = 0; i <= majorTickCount * minorTicksPerMajor; i++) {
    // Skip major ticks (they're already handled)
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
/* All the existing styles remain exactly the same */
.speedometer {
  background: #1a1a1a;
  border-radius: 15px;
  padding: 20px;
  display: flex;
  flex-direction: column;
  align-items: center;
  box-shadow: inset 0 0 10px rgba(0,0,0,0.5);
}

.gauge {
  width: 220px;
  height: 110px;
  position: relative;
  border: 4px solid #333;
  border-radius: 220px 220px 0 0;
  overflow: hidden;
  margin-bottom: 20px;
  background: #111;
}

.gauge::before {
  content: '';
  position: absolute;
  width: 100%;
  height: 100%;
  background: conic-gradient(
    #2ecc71 0deg, 
    #2ecc71 90deg,  /* 40/80*180 = 90deg for green range */
    #f1c40f 90deg,
    #f1c40f 135deg, /* 60/80*180 = 135deg for yellow range */
    #e74c3c 135deg,
    #e74c3c 180deg
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
  background: #fff;
}

.minor-tick {
  width: 1px;
  height: 10px;
  background: #aaa;
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
  background: #f1c40f;
  bottom: 0;
  left: 50%;
  transform-origin: bottom center;
  z-index: 3;
  box-shadow: 0 0 5px rgba(241, 196, 15, 0.7);
  transition: transform 0.5s cubic-bezier(0.175, 0.885, 0.32, 1.275);
}

.center {
  position: absolute;
  width: 20px;
  height: 20px;
  background: #111;
  border: 3px solid #f1c40f;
  border-radius: 50%;
  bottom: -10px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 4;
}

.speed-display {
  text-align: center;
  color: #fff;
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
  color: #f1c40f;
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
  color: #fff;
  background: #222;
  padding: 10px 10px 10px 10px;
  border-radius: 18px;
  margin-top: 10px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.18);
  position: relative;
}

.target-slider {
  width: 280px;         /* Similar to lever-container width */
  height: 55px;         /* Thumb height */
  background: #333;
  border-radius: 20px;
  box-shadow: inset 0 0 15px rgba(0,0,0,0.7);
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

/* Track styles */
.target-slider::-webkit-slider-runnable-track {
  width: 100%;
  height: 40px;
  background: #333;
  border-radius: 20px;
}
.target-slider::-moz-range-track {
  width: 100%;
  height: 40px;
  background: #333;
  border-radius: 20px;
}
.target-slider::-ms-fill-lower,
.target-slider::-ms-fill-upper {
  background: #333;
  border-radius: 20px;
}

/* Thumb styles */
.target-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 80px;
  height: 40px;
  background: linear-gradient(to right, #555, #333);
  border-radius: 5px;
  border: 2px solid #222;
  box-shadow: 0 2px 5px rgba(0,0,0,0.5);
  cursor: ew-resize;
  transition: background 0.2s;
  margin-top: 0; /* Center thumb on track */
}
.target-slider:focus::-webkit-slider-thumb {
  background: #666;
}

.target-slider::-moz-range-thumb {
  width: 80px;
  height: 40px;
  background: linear-gradient(to right, #555, #333);
  border-radius: 5px;
  border: 2px solid #222;
  box-shadow: 0 2px 5px rgba(0,0,0,0.5);
  cursor: ew-resize;
  transition: background 0.2s;
}
.target-slider:focus::-moz-range-thumb {
  background: #666;
}

.target-slider::-ms-thumb {
  width: 80px;
  height: 40px;
  background: linear-gradient(to right, #555, #333);
  border-radius: 5px;
  border: 2px solid #222;
  box-shadow: 0 2px 5px rgba(0,0,0,0.5);
  cursor: ew-resize;
  transition: background 0.2s;
}
.target-slider:focus::-ms-thumb {
  background: #666;
}

/* Remove outline on Firefox */
.target-slider::-moz-focus-outer {
  border: 0;
}

/* Value label above the slider thumb */
.target-speed {
  position: relative;
}
.target-speed-value {
  top: 0;
  max-width: 155px;
  margin-left: 58px;
  background: #596f72;
  color: #222;
  font-weight: bold;
  padding: 2px 10px;
  border-radius: 10px;
  font-size: 1.1em;
  box-shadow: 0 1px 4px rgba(0,0,0,0.12);
  pointer-events: none;
  z-index: 2;
}
</style>