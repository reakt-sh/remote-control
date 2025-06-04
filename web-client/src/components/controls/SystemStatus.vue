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
  const percent = Math.max(0, Math.min(100, props.batteryLevel)) / 100;
  const r = Math.round(255 * (1 - percent));
  const g = Math.round(204 * percent);
  const b = Math.round(71 * percent);
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
  background: linear-gradient(135deg, #debcbc, #88b48f);
  border-radius: 15px;
  padding: 15px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
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
  color: #555;
  font-size: 0.8rem;
  margin-bottom: 5px;
}

.status-value,
.status-meter {
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0;
  font-size: 0.85rem;
  border-radius: 5px;
  box-sizing: border-box;
}

.status-value {
  background: #e0e0e0;
  font-weight: bold;
  text-align: center;
}

.status-online {
  color: #27ae60;
}

.status-warning {
  color: #e67e22;
}

.status-danger {
  color: #c0392b;
}

.status-offline {
  color: #7f8c8d;
}

.status-normal {
  color: #34495e;
}

.status-meter {
  background: #e0e0e0;
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
  color: #333;
  pointer-events: none;
}
</style>