<template>
  <div class="control-view">
    <header class="app-header">
      <h1>Remote Control System</h1>
      <ConnectionStatus />
    </header>

    <main class="app-main">
      <TrainSelector />

      <div v-if="selectedTrainId && availableTrains.length !== 0" class="train-control-panel">
        <VideoPanel />
        <TelemetryPanel />
        <ControlPanel class="full-width-panel" />
      </div>
    </main>
  </div>
</template>

<script setup>
import { storeToRefs } from 'pinia'
import { useTrainStore } from '@/stores/trainStore'
import ConnectionStatus from '@/components/ConnectionStatus.vue'
import TrainSelector from '@/components/TrainSelector.vue'
import VideoPanel from '@/components/VideoPanel.vue'
import TelemetryPanel from '@/components/telemetry/TelemetryPanel.vue'
import ControlPanel from '@/components/controls/ControlPanel.vue'

const { selectedTrainId, availableTrains } = storeToRefs(useTrainStore())
</script>

<style scoped>
.control-view {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  height: 100vh;
  overflow: hidden; /* No scroll on the root */
}

.app-header {
  background-color: var(--primary-color);
  color: white;
  padding: 1rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  box-shadow: 0 2px 5px rgba(0,0,0,0.1);
}

.app-header h1 {
  font-size: 1.5rem;
}

.app-main {
  flex: 1;
  padding: 1rem;
  max-width: 1400px;
  margin: 0 auto;
  width: 100%;
  height: 0; /* Required for flex children to allow overflow */
  min-height: 0;
  overflow-y: auto; /* SPA scroll here */
}

.train-control-panel {
  display: grid;
  grid-template-columns: 2fr 1fr;
  grid-gap: 1rem;
  margin-top: 1rem;
  width: 100%;
}

.full-width-panel {
  grid-column: 1 / -1;
}

.train-control-panel,
.video-panel,
.telemetry-panel,
.control-panel {
  overflow: hidden;
}

@media (max-width: 1024px) {
  .train-control-panel {
    grid-template-columns: 1fr;
  }
  .full-width-panel {
    grid-column: 1;
  }
}
</style>