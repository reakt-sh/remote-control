<template>
  <div class="circular-progress">
    <svg class="progress-ring" :width="size" :height="size">
      <circle
        class="progress-ring-circle"
        stroke-width="8"
        fill="transparent"
        :r="radius"
        :cx="size / 2"
        :cy="size / 2"
        :stroke="backgroundColor"
      />
      <circle
        class="progress-ring-circle"
        stroke-width="8"
        fill="transparent"
        :r="radius"
        :cx="size / 2"
        :cy="size / 2"
        :stroke="color"
        :stroke-dasharray="circumference"
        :stroke-dashoffset="strokeDashoffset"
        stroke-linecap="round"
      />
    </svg>
    <div class="progress-content">
      <div class="progress-value">{{ Math.round(progressValue) }}%</div>
      <div class="progress-label">{{ label }}</div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  value: {
    type: Number,
    default: 0
  },
  max: {
    type: Number,
    default: 100
  },
  label: {
    type: String,
    default: ''
  },
  color: {
    type: String,
    default: '#0096ff'
  },
  backgroundColor: {
    type: String,
    default: 'rgba(255, 255, 255, 0.1)'
  },
  size: {
    type: Number,
    default: 80
  }
})

const radius = computed(() => props.size / 2 - 8)
const circumference = computed(() => radius.value * 2 * Math.PI)
const progressValue = computed(() => (props.value / props.max) * 100)
const strokeDashoffset = computed(() => circumference.value - (progressValue.value / 100) * circumference.value)
</script>

<style scoped>
.circular-progress {
  position: relative;
  width: v-bind('props.size + "px"');
  height: v-bind('props.size + "px"');
}

.progress-ring {
  transform: rotate(-90deg);
}

.progress-content {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.progress-value {
  font-size: 1rem;
  font-weight: 600;
  color: #222;
}

.progress-label {
  font-size: 0.7rem;
  color: #7b8794;
  text-transform: uppercase;
  margin-top: 2px;
}
</style>