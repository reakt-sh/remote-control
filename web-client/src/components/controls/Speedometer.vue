<template>
  <div class="speedometer">
    <div class="speed-label">Current Speed</div>
    <div class="speed-row">
      <div class="current-speed">{{ formattedSpeed }}</div>
      <div class="speed-unit">km/h</div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  currentSpeed: {
    type: Number,
    default: 0
  }
})

const formattedSpeed = computed(() => {
  return props.currentSpeed.toFixed(2)
})
</script>

<style scoped>
.speedometer {
  background: linear-gradient(135deg, #f5f7fa, #e4e8eb);
  border-radius: 10px;
  padding: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-direction: column;
  box-shadow: 0 2px 4px rgba(0,0,0,0.06);
  border: 1px solid #e0e4e7;
  width: 100%;
  max-width: 320px;
  margin: 0 auto;
}

.speed-label {
  font-size: 0.85rem;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  color: #60707d;
  margin-bottom: 6px;
}

.speed-row {
  display: flex;
  align-items: baseline;
  justify-content: center;
  gap: 8px;
}

.current-speed {
  font-size: 1.7rem;
  font-weight: bold;
  font-family: 'Segment7', monospace;
  color: #2c3e50;
}

.speed-unit {
  font-size: 1rem;
  color: #7f8c8d;
}

@media (max-width: 599px) {
  .speedometer {
    padding: 8px;
    max-width: 100%;
  }

  .current-speed {
    font-size: 1.5rem;
  }
}
</style>