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
          <div class="meter-fill" :style="{ width: `${batteryLevel}%` }"></div>
          <div class="meter-text">{{ batteryLevel }}%</div>
        </div>
      </div>
      
      <div class="status-item">
        <div class="status-label">ENGINE TEMP</div>
        <div class="status-value" :class="tempClass">{{ engineTemp }}°C</div>
      </div>
      
      <div class="status-item">
        <div class="status-label">FUEL</div>
        <div class="status-meter">
          <div class="meter-fill" :style="{ width: `${fuelLevel}%` }"></div>
          <div class="meter-text">{{ fuelLevel }}%</div>
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
  return {
    'status-online': props.systemStatus === 'RUNNING',
    'status-warning': props.systemStatus === 'STANDBY',
    'status-offline': props.systemStatus === 'OFFLINE'
  };
});

const tempClass = computed(() => {
  if (props.engineTemp > 100) return 'status-danger';
  if (props.engineTemp > 80) return 'status-warning';
  return 'status-normal';
});
</script>

<style scoped>
.system-status {
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
  height: 100%;
  background: linear-gradient(to right, #2ecc71, #f1c40f);
  transition: width 0.5s;
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