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
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  padding: 15px;
  background: rgba(255, 255, 255, 0.7);
  border-radius: 10px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.direction-label {
  font-size: 1rem;
  font-weight: bold;
  text-transform: uppercase;
  letter-spacing: 1px;
  color: #555;
}

.direction-buttons {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.direction-button {
  width: 120px;
  height: 60px;
  border: none;
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.3s ease;
  font-weight: bold;
  background: #ECEFF1;
  color: #546E7A;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.direction-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
}

.direction-button:active {
  transform: translateY(1px);
}

.direction-button.active {
  background: #2196F3;
  color: white;
  box-shadow: inset 0 0 10px rgba(0, 0, 0, 0.2);
}

.icon {
  font-size: 1.5rem;
  margin-bottom: 4px;
}

.text {
  font-size: 0.8rem;
  text-transform: uppercase;
  letter-spacing: 1px;
}
</style>