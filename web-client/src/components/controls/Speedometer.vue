<template>
  <div class="speedometer" :style="{ '--speed-ratio': speedRatio }">
    <svg
      class="gauge-svg"
      viewBox="0 0 200 120"
      xmlns="http://www.w3.org/2000/svg"
    >
      <!-- Background arc (full gauge track) -->
      <path
        d="M 20 100 A 80 80 0 0 1 180 100"
        fill="none"
        stroke="#e5e7eb"
        stroke-width="12"
        stroke-linecap="round"
      />

      <!-- Colored arc sections -->
      <path
        d="M 20 100 A 80 80 0 0 1 180 100"
        fill="none"
        stroke="url(#gaugeGradient)"
        stroke-width="12"
        stroke-linecap="round"
        :stroke-dasharray="dashArray"
        stroke-dashoffset="dashOffset"
        class="gauge-fill"
      />

      <!-- Gradient definition -->
      <defs>
        <linearGradient id="gaugeGradient" x1="0%" y1="0%" x2="100%" y2="0%">
          <stop offset="0%" stop-color="#22c55e" />
          <stop offset="50%" stop-color="#22c55e" />
          <stop offset="70%" stop-color="#eab308" />
          <stop offset="85%" stop-color="#f97316" />
          <stop offset="100%" stop-color="#ef4444" />
        </linearGradient>
      </defs>

      <!-- Tick marks -->
      <g class="ticks">
        <line
          v-for="tick in ticks"
          :key="tick.index"
          :x1="tick.x1"
          :y1="tick.y1"
          :x2="tick.x2"
          :y2="tick.y2"
          :stroke="tick.isMajor ? '#6b7280' : '#d1d5db'"
          :stroke-width="tick.isMajor ? 2 : 1"
          stroke-linecap="round"
        />
        <!-- Speed labels on major ticks -->
        <text
          v-for="tick in majorTicks"
          :key="'label-' + tick.index"
          :x="tick.labelX"
          :y="tick.labelY"
          fill="#6b7280"
          font-size="6.5"
          font-family="'Inter', 'Segoe UI', sans-serif"
          font-weight="600"
          text-anchor="middle"
          dominant-baseline="central"
        >{{ tick.value }}</text>
      </g>

      <!-- Needle -->
      <g class="needle-group">
        <line
          x1="100"
          y1="100"
          :x2="needleEnd.x"
          :y2="needleEnd.y"
          stroke="#374151"
          stroke-width="2.5"
          stroke-linecap="round"
          class="needle"
        />
        <!-- Needle counterweight -->
        <line
          x1="100"
          y1="100"
          :x2="needleCounter.x"
          :y2="needleCounter.y"
          stroke="#374151"
          stroke-width="2"
          stroke-linecap="round"
          opacity="0.3"
        />
      </g>

      <!-- Center dot -->
      <circle cx="100" cy="100" r="4.5" fill="#374151" />
      <circle cx="100" cy="100" r="2" fill="#ffffff" />

    </svg>

    <!-- Digital readout overlay -->
    <div class="digital-display">
      <div class="speed-value">{{ formattedSpeed }}</div>
      <div class="speed-unit">km/h</div>
      <div class="speed-label">Current Speed</div>
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

const MAX_SPEED = 13
const ARC_LENGTH = 251.2 // Approximate length of the arc path (80px radius, 180° arc)

const formattedSpeed = computed(() => {
  return props.currentSpeed.toFixed(1)
})

const speedRatio = computed(() => {
  return Math.min(props.currentSpeed / MAX_SPEED, 1)
})

// Arc path: (80 * PI) ≈ 251.33 for a semicircle of radius 80
const dashArray = computed(() => {
  return `${ARC_LENGTH} ${ARC_LENGTH}`
})

// eslint-disable-next-line no-unused-vars
const dashOffset = computed(() => {
  return ARC_LENGTH * (1 - speedRatio.value)
})

// Generate tick marks along the arc
const ticks = computed(() => {
  const cx = 100, cy = 100, r = 80
  const startAngle = -180 // degrees (left side)
  const endAngle = 0       // degrees (right side)
  const totalTicks = 20

  return Array.from({ length: totalTicks + 1 }, (_, i) => {
    const fraction = i / totalTicks
    const angle = startAngle + fraction * (endAngle - startAngle)
    const angleRad = (angle * Math.PI) / 180
    const isMajor = i % 4 === 0
    const tickLen = isMajor ? 8 : 4
    const innerR = r - tickLen

    return {
      index: i,
      isMajor,
      x1: cx + innerR * Math.cos(angleRad),
      y1: cy + innerR * Math.sin(angleRad),
      x2: cx + (r - 2) * Math.cos(angleRad),
      y2: cy + (r - 2) * Math.sin(angleRad),
    }
  })
})

const majorTicks = computed(() => {
  const cx = 100, cy = 100, r = 80
  const totalSteps = 5 // 0, 3, 6, 9, 12, 15

  return Array.from({ length: totalSteps + 1 }, (_, i) => {
    const fraction = i / totalSteps
    const angle = -180 + fraction * 180
    const angleRad = (angle * Math.PI) / 180
    const labelR = r - 14
    const value = Math.round(fraction * MAX_SPEED)

    return {
      index: i,
      value,
      labelX: cx + labelR * Math.cos(angleRad),
      labelY: cy + labelR * Math.sin(angleRad),
    }
  })
})

// Needle position
const needleEnd = computed(() => {
  const cx = 100, cy = 100, r = 72
  const angle = -180 + speedRatio.value * 180
  const angleRad = (angle * Math.PI) / 180

  return {
    x: cx + r * Math.cos(angleRad),
    y: cy + r * Math.sin(angleRad),
  }
})

const needleCounter = computed(() => {
  const cx = 100, cy = 100, r = 16
  const angle = -180 + speedRatio.value * 180
  const angleRad = (angle * Math.PI) / 180

  return {
    x: cx + r * Math.cos(angleRad + Math.PI),
    y: cy + r * Math.sin(angleRad + Math.PI),
  }
})
</script>

<style scoped>
.speedometer {
  --speed-ratio: 0;
  position: relative;
  width: 100%;
  max-width: 300px;
  margin: 0 auto;
  background: #ffffff;
  border-radius: 16px;
  padding: 16px 16px 20px;
  box-shadow:
    0 1px 3px rgba(0, 0, 0, 0.08),
    0 4px 12px rgba(0, 0, 0, 0.04);
  border: 1px solid #e5e7eb;
  overflow: hidden;
}

.gauge-svg {
  width: 100%;
  height: auto;
  display: block;
}

.gauge-fill {
  transition: stroke-dashoffset 0.6s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.ticks text {
  user-select: none;
}

.needle-group {
  transition: transform 0.6s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.needle {
  transition: all 0.6s cubic-bezier(0.34, 1.56, 0.64, 1);
}

/* Digital display overlay */
.digital-display {
  text-align: center;
  margin-top: -12px;
  position: relative;
  z-index: 2;
}

.speed-value {
  font-size: 2.2rem;
  font-weight: 700;
  font-family: 'Inter', 'Segoe UI', system-ui, -apple-system, sans-serif;
  color: #111827;
  line-height: 1;
  letter-spacing: -0.02em;
  transition: color 0.4s ease;
}

.speed-unit {
  font-size: 0.75rem;
  font-weight: 500;
  color: #6b7280;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  margin-top: 2px;
}

.speed-label {
  font-size: 1.0rem;
  font-weight: 500;
  color: #9ca3af;
  text-transform: uppercase;
  letter-spacing: 0.12em;
  margin-top: 4px;
}

/* Responsive adjustments */
@media (max-width: 599px) {
  .speedometer {
    padding: 12px 12px 16px;
    max-width: 100%;
  }

  .speed-value {
    font-size: 1.8rem;
  }

  .speed-unit {
    font-size: 0.65rem;
  }
}
</style>