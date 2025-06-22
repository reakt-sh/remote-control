<template>
    <div class="main-view">
        <header class="app-header">
            <h1>Remote Control System</h1>
            <ConnectionStatus />
        </header>

        <main class="app-main">
            <div class="train-control-panel">
                <VideoPanel />
                <TelemetryPanel />
                <ControlPanel class="full-width-panel" />
            </div>
        </main>
    </div>
</template>

<script setup>
import { onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import VideoPanel from '@/components/VideoPanel.vue'
import TelemetryPanel from '@/components/telemetry/TelemetryPanel.vue'
import ControlPanel from '@/components/controls/ControlPanel.vue'
import ConnectionStatus from '@/components/ConnectionStatus.vue'
// Import your mapping function from the store or utility
import { useTrainStore } from '@/stores/trainStore'

const route = useRoute()
const trainId = route.params.trainId

const { mappingToTrain } = useTrainStore()
const { fetchAvailableTrains, connectToServer, initializeRemoteControlId } = useTrainStore()


onMounted(() => {
  initializeRemoteControlId()
  connectToServer()
  fetchAvailableTrains()
  if (trainId) {
    mappingToTrain(trainId)
  }
})

// Optional: If you want to react to route changes while this view is active
watch(() => route.params.trainId, (newId) => {
  if (newId) {
    mappingToTrain(newId)
  }
})
</script>

<style scoped>
.app-main {
  flex: 1;
  padding: 1rem;
  max-width: 1400px;
  margin: 0 auto;
  width: 100%;
  min-height: 80vh;
  height: 100vh;           /* Set a fixed height for scrolling */
  overflow-y: auto;       /* Enable vertical scroll */
  box-sizing: border-box; /* Prevent overflow from padding */
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

@media (max-width: 1024px) {
  .train-control-panel {
    grid-template-columns: 1fr;
  }
  .full-width-panel {
    grid-column: 1;
  }
}
</style>