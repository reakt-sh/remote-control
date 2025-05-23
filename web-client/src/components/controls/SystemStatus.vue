<template>
  <div class="system-status">
    <div class="status-grid">
      <div class="status-item">
        <div class="status-label">STATUS</div>
        <div class="status-value" :class="statusClass">{{ systemStatus }}</div>
      </div>
      
      <div class="status-item">
        <div class="status-label">BATTERY</div>
        <div class="status-meter">
          <div class="meter-fill" :style="{ width: `${batteryLevel}%`, background: batteryFillColor }"></div>
          <div class="meter-text">{{ Number(batteryLevel).toFixed(2) }}%</div>
        </div>
      </div>
      
      <div class="status-item">
        <div class="status-label">ENGINE TEMP</div>
        <div class="status-value" :class="tempClass">{{ engineTemp }}°C</div>
      </div>
      
      <div class="status-item">
        <div class="status-label">FUEL</div>
        <div class="status-meter">
          <div class="meter-fill" :style="{ width: `${fuelLevel}%`, background: fuelFillColor }"></div>
          <div class="meter-text">{{ Number(fuelLevel).toFixed(2) }}%</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue';

const props = defineProps({
  systemStatus: {
    type: String,
    default: 'OFFLINE'
  },
  batteryLevel: {
    type: Number,
    default: 0
  },
  engineTemp: {
    type: Number,
    default: 0
  },
  fuelLevel: {
    type: Number,
    default: 0
  }
});

const statusClass = computed(() => {
  console.log("TheKing--> props.systemStatus = ", props.systemStatus);
  return {
    'status-online': props.systemStatus === 'running',
    'status-warning': props.systemStatus === 'standby',
    'status-offline': props.systemStatus === 'offline'
  };
});

const tempClass = computed(() => {
  if (props.engineTemp > 100) return 'status-danger';
  if (props.engineTemp > 80) return 'status-warning';
  return 'status-normal';
});

const batteryFillColor = computed(() => {
  // batteryLevel: 0 (red) to 100 (green)
  const percent = Math.max(0, Math.min(100, props.batteryLevel)) / 100;
  // Interpolate between red (low) and green (full)
  const r = Math.round(255 * (1 - percent));
  const g = Math.round(204 * percent); // 204 is green in #2ecc71
  const b = Math.round(71 * percent);  // 71 is blue in #2ecc71
  return `rgb(${r},${g},${b})`;
});

const fuelFillColor = computed(() => {
  const percent = Math.max(0, Math.min(100, props.fuelLevel)) / 100;
  const r = Math.round(255 * (1 - percent));
  const g = Math.round(204 * percent);
  const b = Math.round(71 * percent);
  return `rgb(${r},${g},${b})`;
});
</script>

<style scoped>
.system-status {
  margin-top: 200px;
  min-width: 300px;
  background: #1a1a1a;
  border-radius: 15px;
  padding: 15px;
  box-shadow: inset 0 0 10px rgba(0,0,0,0.5);
}

.panel-title {
  color: #777;
  font-size: 0.9rem;
  margin: 0 0 15px 0;
  text-align: center;
  letter-spacing: 1px;
}

.status-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 15px;
}

.status-item {
  display: flex;
  flex-direction: column;
}

.status-label {
  color: #777;
  font-size: 0.8rem;
  margin-bottom: 5px;
}

.status-value,
.status-meter {
  height: 20px;           /* Set the same height */
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0;             /* Remove extra padding */
  font-size: 0.85rem;     /* Make font size consistent */
  border-radius: 5px;
  box-sizing: border-box;
}

.status-value {
  background: #333;
  font-weight: bold;
  text-align: center;
}

.status-online {
  color: #2ecc71;
}

.status-warning {
  color: #f1c40f;
}

.status-danger {
  color: #e74c3c;
}

.status-offline {
  color: #777;
}

.status-normal {
  color: #fff;
}

.status-meter {
  background: #333;
  position: relative;
  overflow: hidden;
}

.meter-fill {
  position: absolute;
  left: 0;
  right: auto;
  top: 0;
  bottom: 0;
  height: 100%;
  /* background will be set dynamically */
  transition: width 0.5s, background 0.5s;
}

.meter-text {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.85rem;
  font-weight: bold;
  color: #000;
  pointer-events: none;
}
</style>