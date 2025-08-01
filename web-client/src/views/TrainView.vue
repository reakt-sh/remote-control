<template>
  <div class="main-view">
    <AppHeader />

    <main class="app-main">
      <Tabs :tabs="tabs">
        <template #control>
          <div class="control-tab">
            <VideoPanel />
            <ControlPanel />
          </div>
        </template>
        <template #telemetry>
          <TelemetryPanel />
        </template>
        <template #network>
          <NetworkPanel />
        </template>
      </Tabs>
    </main>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRoute } from 'vue-router'
import { onMounted, watch } from 'vue'
import AppHeader from '@/components/AppHeader.vue'
import Tabs from '@/components/Tabs.vue'
import VideoPanel from '@/components/VideoPanel.vue'
import TelemetryPanel from '@/components/telemetry/TelemetryPanel.vue'
import ControlPanel from '@/components/controls/ControlPanel.vue'
import { useTrainStore } from '@/stores/trainStore'
import NetworkPanel from '@/components/network/NetworkPanel.vue'

const route = useRoute()
const trainId = route.params.trainId

const { mappingToTrain } = useTrainStore()
const { fetchAvailableTrains, connectToServer, initializeRemoteControlId } = useTrainStore()

const tabs = ref([
  { id: 'control', label: 'Control Center', icon: 'fas fa-gamepad' },
  { id: 'telemetry', label: 'Telemetry Data', icon: 'fas fa-chart-line' },
  { id: 'network', label: 'Network', icon: 'fas fa-network-wired' }
])

onMounted(() => {
  initializeRemoteControlId()
  connectToServer()
  fetchAvailableTrains()
  if (trainId) {
    mappingToTrain(trainId)
  }
})

watch(() => route.params.trainId, (newId) => {
  if (newId) {
    mappingToTrain(newId)
  }
})
</script>

<style scoped>

.control-tab {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 20px;
}

@media (max-width: 1300px) {
  .control-tab {
    grid-template-columns: 1fr;
  }
}
</style>