<template>
  <div class="main-view">
    <AppHeader />

    <main class="app-main">
      <LiveTrainSelector />
    </main>
  </div>
</template>

<script setup>
import AppHeader from '@/components/AppHeader.vue'
import LiveTrainSelector from '@/components/LiveTrainSelector.vue'
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