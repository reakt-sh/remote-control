<template>
  <div class="info-panel">
    <!-- Column 1: NTP clock offsets -->
    <div class="info-col">
      <div class="info-row">
        <span class="info-label">Train NTP offset</span>
        <span class="info-value">{{ ntpTrain }} <span class="info-unit">ms</span></span>
      </div>
      <div class="info-row">
        <span class="info-label">Remote NTP offset</span>
        <span class="info-value">{{ ntpRemote }} <span class="info-unit">ms</span></span>
      </div>
    </div>

    <div class="info-divider" aria-hidden="true"></div>

    <!-- Column 2: GNSS position -->
    <div class="info-col">
      <div class="info-row">
        <span class="info-label">Latitude</span>
        <span class="info-value">{{ lat }} <span class="info-unit">&deg;</span></span>
      </div>
      <div class="info-row">
        <span class="info-label">Longitude</span>
        <span class="info-value">{{ lon }} <span class="info-unit">&deg;</span></span>
      </div>
    </div>

    <div class="info-divider" aria-hidden="true"></div>

    <!-- Column 3: Electrical -->
    <div class="info-col">
      <div class="info-row">
        <span class="info-label">Voltage</span>
        <span class="info-value">{{ voltage }} <span class="info-unit">V</span></span>
      </div>
      <div class="info-row">
        <span class="info-label">Current</span>
        <span class="info-value">{{ current }} <span class="info-unit">A</span></span>
      </div>
    </div>

    <div class="info-divider" aria-hidden="true"></div>

    <!-- Column 4: Power / Energy -->
    <div class="info-col">
      <div class="info-row">
        <span class="info-label">Power</span>
        <span class="info-value">{{ power }} <span class="info-unit">W</span></span>
      </div>
      <div class="info-row">
        <span class="info-label">Energy</span>
        <span class="info-value">{{ energy }} <span class="info-unit">Wh</span></span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { storeToRefs } from 'pinia'
import { useTrainStore } from '@/stores/trainStore'

const trainStore = useTrainStore()
const { telemetryData, train_ntp_offset, remote_control_ntp_offset } =
  storeToRefs(trainStore)

const fmt = (value, decimals = 2) =>
  value === null || value === undefined || value === 0.0 ? 'N/A' : Number(value).toFixed(decimals)

const ntpTrain = computed(() => fmt(train_ntp_offset.value, 3))
const ntpRemote = computed(() => fmt(remote_control_ntp_offset.value, 3))

const lat = computed(() => fmt(telemetryData.value?.latitude, 4))
const lon = computed(() => fmt(telemetryData.value?.longitude, 4))

const voltage = computed(() => fmt(telemetryData.value?.voltage_v))
const current = computed(() => fmt(telemetryData.value?.current_a))
const power = computed(() => fmt(telemetryData.value?.power_w))
const energy = computed(() => fmt(telemetryData.value?.energy_wh))
</script>

<style scoped>
.info-panel {
  display: flex;
  align-items: stretch;
  gap: 10px;
  /* Deliberately narrower than the app header (~45 px incl. logo + padding) */
  height: 36px;
  min-height: 0;
  padding: 3px 10px;
  box-sizing: border-box;
  width: 100%;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06);
  font-family: 'Be Vietnam Pro', sans-serif;
}

.info-col {
  /* Two-column grid: labels in col 1, value+unit in col 2.
     Every value in a column starts at the same grid line (col 2 start), so
     the two rows line up vertically even when the labels differ in width. */
  display: grid;
  grid-template-columns: max-content 1fr;
  column-gap: 10px;
  row-gap: 3px;
  flex: 1 1 0;
  min-width: 0;
}

.info-row {
  display: contents; /* let label / value become direct grid items of .info-col */
}

.info-label {
  font-size: 0.55rem;
  font-weight: 600;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  white-space: nowrap;
  line-height: 1;
  text-align: right;
}

.info-value {
  font-size: 0.62rem;
  font-weight: 700;
  color: #0f172a;
  font-variant-numeric: tabular-nums;
  line-height: 1;
}

.info-unit {
  font-size: 0.55rem;
  color: #94a3b8;
  margin-left: 2px;
  white-space: nowrap;
  line-height: 1;
}

.info-divider {
  width: 1px;
  align-self: stretch;
  margin: 0 6px;
  background: rgba(100, 116, 139, 0.2);
}

/* Tablets / portrait: wrap into two rows of two columns, drop fixed height */
@media (max-width: 900px), (orientation: portrait) {
  .info-panel {
    height: auto;
    min-height: 0;
    flex-wrap: wrap;
    padding: 4px 8px;
    gap: 8px;
  }
  .info-col {
    flex: 0 0 50%;
    min-width: 0;
  }
  .info-divider {
    display: none;
  }
}

/* Phones: stack all columns vertically */
@media (max-width: 599px) {
  .info-panel {
    flex-direction: column;
    height: auto;
    gap: 6px;
    padding: 4px 8px;
  }
  .info-col {
    flex: 0 0 auto;
    width: 100%;
    gap: 3px;
  }
  .info-divider {
    display: none;
  }
}
</style>
