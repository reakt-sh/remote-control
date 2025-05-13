<template>
  <div class="master-controller">
    <div class="mc-row">
      <div class="lever-container">
        <div
          class="lever"
          :style="{ transform: `translateY(${-leverPosition}px)` }"
          @mousedown="startDrag"
          @touchstart="startDrag"
        ></div>
      </div>
      <div class="labels">
        <span class="brake-label">BRAKE</span>
        <span class="neutral-label">NEUTRAL</span>
        <span class="power-label">POWER</span>
      </div>
    </div>
    <div class="notches">
      <div v-for="n in 8" :key="n" class="notch"></div>
    </div>
    <div class="power-indicator">
      <span>{{ powerLevel > 0 ? `P${powerLevel}` : `B${Math.abs(powerLevel)}` }}</span>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue';

const props = defineProps({
  powerLevel: {
    type: Number,
    default: 0
  }
});

const emit = defineEmits(['throttle-change', 'brake-change']);

const leverPosition = computed(() => {
  return props.powerLevel * 10;
});

const startDrag = (e) => {
  e.preventDefault();
  const startY = e.type === 'mousedown' ? e.clientY : e.touches[0].clientY;
  const startPower = props.powerLevel;

  const moveHandler = (moveEvent) => {
    const currentY = moveEvent.type === 'mousemove' ? moveEvent.clientY : moveEvent.touches[0].clientY;
    const diffY = startY - currentY;
    const newPower = Math.min(Math.max(startPower + Math.round(diffY / 10), -8), 8);

    if (newPower > 0) {
      emit('throttle-change', newPower);
    } else if (newPower < 0) {
      emit('brake-change', Math.abs(newPower));
    } else {
      emit('throttle-change', 0);
    }
  };

  const upHandler = () => {
    window.removeEventListener('mousemove', moveHandler);
    window.removeEventListener('touchmove', moveHandler);
    window.removeEventListener('mouseup', upHandler);
    window.removeEventListener('touchend', upHandler);
  };

  window.addEventListener('mousemove', moveHandler);
  window.addEventListener('touchmove', moveHandler);
  window.addEventListener('mouseup', upHandler);
  window.addEventListener('touchend', upHandler);
};
</script>

<style scoped>
.master-controller {
  position: relative;
  height: 300px;
  width: 260px;           /* Increased width for more space */
  background: #1a1a1a;
  border-radius: 15px;
  padding: 20px 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  box-shadow: inset 0 0 10px rgba(0,0,0,0.5);
}

.mc-row {
  display: flex;
  flex-direction: row;
  align-items: center;
  width: 100%;
  justify-content: space-between;
  position: relative;
}

.lever-container {
  position: relative;
  width: 60px;
  height: 200px;
  background: #333;
  border-radius: 30px;
  margin-bottom: 15px;
  overflow: hidden;
  box-shadow: inset 0 0 15px rgba(0,0,0,0.7);
  margin-left: 10px;
}

.lever {
  position: absolute;
  width: 80px;
  height: 40px;
  background: linear-gradient(to bottom, #555, #333);
  border-radius: 5px;
  left: -10px;
  top: 60%;
  cursor: ns-resize;
  z-index: 2;
  transition: transform 0.1s;
  border: 2px solid #222;
  box-shadow: 0 2px 5px rgba(0,0,0,0.5);
}

.labels {
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  height: 200px;
  min-width: 80px;
  margin-left: 24px;
  font-size: 14px;
  font-weight: bold;
  color: #777;
  text-align: left;
  align-items: flex-start;
}

.brake-label {
  color: #e74c3c;
}

.power-label {
  color: #2ecc71;
}

.power-indicator {
  margin-top: 10px;
  font-size: 18px;
  font-weight: bold;
  color: #f1c40f;
  background: #333;
  padding: 5px 15px;
  border-radius: 20px;
}

.notches {
  position: absolute;
  left: 50%;
  top: 20px;
  bottom: 20px;
  width: 2px;
  background: rgba(255,255,255,0.1);
  transform: translateX(-50%);
}

.notch {
  height: 25px;
  border-bottom: 1px solid rgba(255,255,255,0.05);
}
</style>