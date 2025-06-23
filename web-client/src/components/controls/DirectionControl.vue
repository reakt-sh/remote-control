<template>
  <div class="direction-control">
    <div class="direction-label">DIRECTION</div>
    <div class="direction-buttons">
      <button
        class="direction-button forward"
        :class="{ active: direction === 'forward' }"
        @click="setDirection('forward')"
      >
        <span class="icon">↑</span>
        <span class="text">FORWARD</span>
      </button>
      <button
        class="direction-button reverse"
        :class="{ active: direction === 'reverse' }"
        @click="setDirection('reverse')"
      >
        <span class="icon">↓</span>
        <span class="text">REVERSE</span>
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'

const emit = defineEmits(['change'])
const props = defineProps({
  direction: {
    type: String,
    default: 'forward',
    validator: (value) => ['forward', 'reverse'].includes(value)
  }
})

const direction = ref(props.direction)

watch(() => props.direction, (newVal) => {
  direction.value = newVal
})

function setDirection(newDirection) {
  if (newDirection !== direction.value) {
    direction.value = newDirection
    emit('change', newDirection)
  }
}
</script>

<style scoped>
.direction-control {
  background: linear-gradient(135deg, #f5f7fa, #e4e8eb);
  border-radius: 10px;
  padding: 14px; /* increased */
  display: flex;
  flex-direction: column;
  align-items: center;
  box-shadow: 0 2px 4px rgba(0,0,0,0.06);
  border: 1px solid #e0e4e7;
  max-width: 180px; /* increased from 105px */
  margin: 0 auto;
}

.direction-label {
  font-size: 0.8rem; /* increased from 0.45rem */
  font-weight: bold;
  text-transform: uppercase;
  letter-spacing: 1px;
  color: #555;
}

.direction-buttons {
  display: flex;
  flex-direction: column;
  gap: 8px; /* increased */
}

.direction-button {
  width: 70px;   /* increased from 40px */
  height: 48px;  /* increased from 20px */
  border: none;
  border-radius: 6px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.3s ease;
  font-weight: bold;
  background: #ECEFF1;
  color: #546E7A;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.08);
}

.direction-button:hover {
  transform: translateY(-1px);
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.10);
}

.direction-button:active {
  transform: translateY(0.5px);
}

.direction-button.active {
  background: #2196F3;
  color: white;
  box-shadow: inset 0 0 4px rgba(0, 0, 0, 0.18);
}

.icon {
  font-size: 1.1rem; /* increased from 0.7rem */
  margin-bottom: 2px;
}

.text {
  font-size: 0.6rem; /* increased from 0.35rem */
  text-transform: uppercase;
  letter-spacing: 1px;
}
</style>