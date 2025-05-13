<template>
  <div class="speedometer">
    <div class="gauge">
      <div class="ticks">
        <div v-for="tick in ticks" :key="tick.value" 
             class="tick" :style="tick.style"></div>
      </div>
      <div class="needle" :style="{ transform: `rotate(${needleRotation}deg)` }"></div>
      <div class="center"></div>
    </div>
    <div class="speed-display">
      <div class="current-speed">{{ formattedSpeed }}</div>
      <div class="speed-unit">km/h</div>
      <div class="target-speed">TARGET: {{ props.targetSpeed }}
        <input
          type="range"
          min="0"
          max="60"
          :value="props.targetSpeed"
          @input="e => emit('update:targetSpeed', Number(e.target.value))"
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
    default: 120
  }
});
const emit = defineEmits(['update:targetSpeed']);

const needleRotation = computed(() => {
  const ratio = props.currentSpeed / props.maxSpeed;
  return ratio * 180 - 90;
});

const formattedSpeed = computed(() => {
  return Math.round(props.currentSpeed).toString().padStart(3, '0');
});

const ticks = computed(() => {
  const tickCount = 12;
  const ticks = [];
  for (let i = 0; i <= tickCount; i++) {
    const value = Math.round((i / tickCount) * props.maxSpeed);
    const angle = (i / tickCount) * 180 - 90;
    ticks.push({
      value,
      style: {
        transform: `rotate(${angle}deg)`,
        color: value <= 80 ? '#2ecc71' : value <= 100 ? '#f1c40f' : '#e74c3c'
      }
    });
  }
  return ticks;
});
</script>

<style scoped>
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
    #2ecc71 80deg, 
    #f1c40f 80deg,
    #f1c40f 100deg,
    #e74c3c 100deg,
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
  width: 2px;
  height: 15px;
  background: #fff;
  transform-origin: bottom center;
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

.current-speed {
  font-size: 3rem;
  font-weight: bold;
  font-family: 'Segment7', monospace;
  color: #f1c40f;
  margin-bottom: -10px;
}

.speed-unit {
  font-size: 1.2rem;
  opacity: 0.7;
  margin-bottom: 5px;
}

.target-speed {
  font-size: 1rem;
  color: #777;
  background: #333;
  padding: 5px 10px;
  border-radius: 15px;
}

.target-slider {
  width: 100%;
  margin-top: 8px;
  accent-color: #f1c40f;
}
</style>