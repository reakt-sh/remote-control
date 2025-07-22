<template>
  <div class="telemetry-panel">
    <div class="telemetry-grid">
      <TelemetryCard title="Passenger Count" icon="fas fa-users">
        <div v-if="telemetryData?.passenger_count !== undefined && telemetryData.passenger_count !== null">
          <PassengerCount :passenger-count="telemetryData.passenger_count" />
        </div>
        <div v-else class="telemetry-value no-data">
          <i class="fas fa-times-circle"></i> N/A
        </div>
      </TelemetryCard>

      <TelemetryCard title="System Status" icon="fas fa-heartbeat">
        <div class="status-grid">
          <div class="status-item">
            <div class="status-label">Updated</div>
            <div class="status-value">{{ formattedTime }}</div>
          </div>
          <div class="status-item">
            <div class="status-label">Signal</div>
            <div v-if="telemetryData?.network_signal_strength" class="signal-strength">
              <div class="signal-bars">
                <div v-for="n in 5" :key="n" class="signal-bar" 
                  :class="{ active: n <= Math.round(telemetryData.network_signal_strength / 20) }"></div>
              </div>
              <div class="signal-value">{{ telemetryData.network_signal_strength }}%</div>
            </div>
            <div v-else class="no-data">
              <i class="fas fa-times-circle"></i> No signal
            </div>
          </div>
        </div>
      </TelemetryCard>

      <TelemetryCard title="Location" icon="fas fa-map-marker-alt">
        <div v-if="telemetryData?.location" class="location-info">
          <div class="location-value">
            <i class="fas fa-location-arrow"></i> {{ telemetryData.location }}
          </div>
          <div v-if="telemetryData?.next_station" class="location-next">
            <i class="fas fa-arrow-right"></i> Next: {{ telemetryData.next_station }}
          </div>
          <div v-if="telemetryData?.gps" class="gps-coords">
            <div class="gps-coord">
              <i class="fas fa-longitude"></i> {{ formatCoord(telemetryData.gps.longitude) }}
            </div>
            <div class="gps-coord">
              <i class="fas fa-latitude"></i> {{ formatCoord(telemetryData.gps.latitude) }}
            </div>
          </div>
        </div>
        <div v-else class="no-data">
          <i class="fas fa-times-circle"></i> No location
        </div>
      </TelemetryCard>

      <TelemetryCard title="Environment" icon="fas fa-temperature-low">
        <div v-if="telemetryData?.temperature" class="environment-data">
          <div class="environment-item">
            <i class="fas fa-thermometer-half"></i> {{ telemetryData.temperature }}°C
          </div>
          <div v-if="telemetryData?.humidity" class="environment-item">
            <i class="fas fa-tint"></i> {{ telemetryData.humidity }}%
          </div>
        </div>
        <div v-else class="no-data">
          <i class="fas fa-times-circle"></i> No data
        </div>
      </TelemetryCard>

      <TelemetryCard title="System Health" icon="fas fa-heartbeat">
        <div class="health-metrics">
          <CircularProgress 
            :value="telemetryData?.battery_level ?? 0" 
            label="Battery" 
            color="#4CAF50"
          />
          <CircularProgress 
            :value="telemetryData?.fuel_level ?? 0" 
            label="Fuel" 
            color="#2196F3"
          />
          <CircularProgress 
            v-if="telemetryData?.engine_temperature !== undefined" 
            :value="telemetryData.engine_temperature" 
            :max="120"
            label="Engine Temp" 
            color="#FF5722"
          />
        </div>
      </TelemetryCard>

      <TelemetryCard title="Speed & Motion" icon="fas fa-tachometer-alt">
        <div v-if="telemetryData?.speed !== undefined" class="speed-metrics">
          <div class="speed-value">
            {{ telemetryData.speed }} <span class="unit">km/h</span>
          </div>
          <div v-if="telemetryData?.acceleration" class="acceleration">
            <i class="fas fa-bolt"></i> {{ telemetryData.acceleration }} m/s²
          </div>
        </div>
        <div v-else class="no-data">
          <i class="fas fa-times-circle"></i> No data
        </div>
      </TelemetryCard>
    </div>
    <TelemetryList :telemetry-data="telemetryHistory" />
  </div>
</template>

<script setup>
import { computed, watch } from 'vue';
import { storeToRefs } from 'pinia';
import { useTrainStore } from '@/stores/trainStore';
import TelemetryCard from './TelemetryCard.vue';
import PassengerCount from './PassengerCount.vue';
import CircularProgress from './CircularProgress.vue';
import TelemetryList from './TelemetryList.vue';

const { telemetryData, telemetryHistory } = storeToRefs(useTrainStore());


// Update history when new data arrives
watch(telemetryData, (newData) => {
  if (newData) {
    telemetryHistory.value.unshift({ ...newData });
  }
}, { deep: true });

const formattedTime = computed(() => {
  if (!telemetryData.value?.timestamp) return 'N/A'
  const ts = Number(telemetryData.value.timestamp)
  if (isNaN(ts)) return 'N/A'
  const date = new Date(ts)
  return `${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}:${date.getSeconds().toString().padStart(2, '0')}`
})

function formatCoord(val) {
  if (val === undefined || val === null || isNaN(Number(val))) return 'N/A'
  return Number(val).toFixed(4)
}

</script>

<style scoped>
.telemetry-panel {
  background: linear-gradient(135deg, #f8fafc 60%, #e3f0fa 100%);
  border-radius: 18px;
  overflow: hidden;
  box-shadow: 0 8px 32px rgba(0, 32, 128, 0.08), 0 1.5px 4px rgba(0,0,0,0.04);
  font-family: 'Inter', 'Segoe UI', Arial, sans-serif;
}

.telemetry-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  gap: 24px;
  padding: 32px 24px;
}

.telemetry-card {
  background: #fff;
  border-radius: 16px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
  padding: 24px 20px;
  transition: box-shadow 0.2s, transform 0.2s;
}
.telemetry-card:hover {
  box-shadow: 0 6px 24px rgba(0, 150, 255, 0.10);
  transform: translateY(-2px) scale(1.01);
}

.status-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 18px;
}

.status-item {
  display: flex;
  flex-direction: column;
}

.status-label {
  font-size: 0.8rem;
  color: #7b8794;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 4px;
}

.status-value {
  font-size: 1.1rem;
  font-weight: 600;
  color: #222;
}

.signal-strength {
  display: flex;
  align-items: center;
  gap: 12px;
}

.signal-bars {
  display: flex;
  align-items: flex-end;
  height: 22px;
  gap: 3px;
}

.signal-bar {
  width: 5px;
  height: 100%;
  background: #e0e7ef;
  border-radius: 2px;
  transition: background 0.2s;
}
.signal-bar.active {
  background: linear-gradient(180deg, #4CAF50, #2E7D32);
}

.signal-value {
  font-size: 0.9rem;
  color: #009688;
  font-weight: 500;
}

.location-info {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.location-value {
  font-weight: 600;
  color: #222;
  font-size: 1rem;
}

.location-next {
  color: #4b5563;
  font-size: 0.9rem;
}

.gps-coords {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-top: 6px;
}

.gps-coord {
  font-size: 0.85rem;
  color: #7b8794;
}

.environment-data {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.environment-item {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 1rem;
  color: #222;
}

.health-metrics {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(90px, 1fr));
  gap: 18px;
  justify-items: center;
}

.speed-metrics {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.speed-value {
  font-size: 2.1rem;
  font-weight: 700;
  color: #0096ff;
  letter-spacing: 1px;
}

.unit {
  font-size: 1rem;
  color: #7b8794;
  margin-left: 2px;
}

.acceleration {
  font-size: 0.95rem;
  color: #4b5563;
  display: flex;
  align-items: center;
  gap: 6px;
}

.no-data {
  font-size: 0.95rem;
  color: #b0b7c3;
  display: flex;
  align-items: center;
  gap: 7px;
}

@media (max-width: 900px) {
  .telemetry-grid {
    grid-template-columns: 1fr;
    padding: 18px 8px;
    gap: 18px;
  }
  .telemetry-card {
    padding: 18px 10px;
  }
}
</style>