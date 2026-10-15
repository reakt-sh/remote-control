<template>
  <div class="main-view">
    <AppHeader />

    <main class="app-main">
      <!-- <Tabs :tabs="tabs">
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
      </Tabs> -->
      <div class="control-tab">
        <VideoPanel />
        <ControlPanel />
      </div>
    </main>
  </div>
</template>

<script setup>
// import { ref } from 'vue'
import { useRoute } from 'vue-router'
import { onMounted, watch } from 'vue'
import AppHeader from '@/components/AppHeader.vue'
// import Tabs from '@/components/Tabs.vue'
import VideoPanel from '@/components/VideoPanel.vue'
// import TelemetryPanel from '@/components/telemetry/TelemetryPanel.vue'
import ControlPanel from '@/components/controls/ControlPanel.vue'
import { useTrainStore } from '@/stores/trainStore'
// import NetworkPanel from '@/components/network/NetworkPanel.vue'

const route = useRoute()
const trainId = route.params.trainId

const { mappingToTrain } = useTrainStore()
const { fetchAvailableTrains, connectToServer, initializeRemoteControlId } = useTrainStore()

// Temporarily disabled for conference demo - only showing video + control panel
// const tabs = ref([
//   { id: 'control', label: 'Control Center', icon: 'fas fa-gamepad' },
//   { id: 'telemetry', label: 'Telemetry Data', icon: 'fas fa-chart-line' },
//   { id: 'network', label: 'Network', icon: 'fas fa-network-wired' }
// ])

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

/* This view should feel like a full-screen activity: no reserved bottom
   space, and the control panel below the video grows to fill whatever
   room is left instead of leaving an empty gap. */
.app-main {
  padding: 4px 8px;
  min-height: 0;
}

.control-tab {
  display: flex;
  flex-direction: column;
  gap: 12px;
  height: 100%;
  min-height: 0;
}

@media (max-width: 900px), (orientation: portrait) {
  .control-tab {
    gap: 8px;
  }
}
</style>