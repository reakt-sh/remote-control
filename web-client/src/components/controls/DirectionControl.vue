<template>
  <div class="direction-control">
    <div class="direction-label">DIRECTION</div>
    <div class="direction-buttons">
      <button
        class="direction-button forward"
        :class="{ active: direction === 'FORWARD' }"
        :disabled="disabled"
        @click="setDirection('FORWARD')"
      >
        <span class="icon">↑</span>
      </button>
      <button
        class="direction-button reverse"
        :class="{ active: direction === 'BACKWARD' }"
        :disabled="disabled"
        @click="setDirection('BACKWARD')"
      >
        <span class="icon">↓</span>
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
    default: 'FORWARD',
    validator: (value) => ['FORWARD', 'BACKWARD'].includes(value)
  },
  disabled: {
    type: Boolean,
    default: false
  }
})

const direction = ref(props.direction)

watch(() => props.direction, (newVal) => {
  direction.value = newVal
})

function setDirection(newDirection) {
  if (newDirection !== direction.value && !props.disabled) {
    direction.value = newDirection
    emit('change', newDirection)
  }
}
</script>

<style scoped>
.direction-control {
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

.direction-label {
  font-size: 0.55rem;
  font-weight: bold;
  text-transform: uppercase;
  letter-spacing: 1px;
  color: #555;
  margin-bottom: 2px;
}

.direction-buttons {
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.direction-button {
  width: 60px;
  height: 24px;
  border: none;
  border-radius: 6px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.3s ease;
  font-weight: bold;
  background: #a3a6a1;
  color: #546E7A;
  box-shadow: 0 2px 8px rgba(0,0,0,0.18);
}

.direction-button:hover {
  transform: translateY(-1px);
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.10);
}

.direction-button:active {
  transform: translateY(0.5px);
}

.direction-button.active {
  background: #15c724;
  color: rgb(220, 229, 199);
  box-shadow: 0 4px 16px rgba(33,150,243,0.25), 0 2px 8px rgba(0,0,0,0.18); /* Add blue glow and keep base shadow */
}

.icon {
  font-size: 1.2rem;
}

@media (min-width: 700px) {
  .direction-control {
    max-width: 180px;
    padding: 6px;
  }
  .direction-label {
    font-size: 0.65rem;
    margin-bottom: 3px;
  }
  .direction-buttons {
    gap: 4px;
  }
  .direction-button {
    width: 70px;
    height: 28px;
  }
  .icon {
    font-size: 1.4rem;
  }
}

@media (max-height: 700px) {
  .direction-control {
    max-width: 100px;
    padding: 3px;
  }
  .direction-label {
    font-size: 0.45rem;
    margin-bottom: 1px;
  }
  .direction-buttons {
    gap: 2px;
  }
  .direction-button {
    width: 36px;
    height: 18px;
  }
  .icon {
    font-size: 0.9rem;
  }
}
</style>