<template>
  <div class="main-view">
    <header class="app-header">
      <h1>Remote Control System</h1>
      <ConnectionStatus />
    </header>

    <main class="app-main">
      <TrainSelector />
    </main>
  </div>
</template>

<script setup>
import ConnectionStatus from '@/components/ConnectionStatus.vue'
import TrainSelector from '@/components/TrainSelector.vue'
import { useTrainStore } from '@/stores/trainStore'
import { onMounted } from 'vue'

const { fetchAvailableTrains, connectToServer, initializeRemoteControlId } = useTrainStore()

onMounted(() => {
  initializeRemoteControlId()
  connectToServer()
  fetchAvailableTrains()
})

</script>

<style scoped>

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