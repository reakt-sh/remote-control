<template>
  <div class="video-panels">
    <!-- Front camera -->
    <div
      class="video-column"
      :class="isForward ? 'video-column--big' : 'video-column--small'"
      :style="{ order: isForward ? 0 : 1 }"
    >
      <div class="video-panel">
        <div class="video-container">
          <canvas ref="videoCanvasFront" class="video-feed"></canvas>
        </div>
      </div>
      <!-- Fills the leftover space below the smaller (non-active-direction) panel -->
      <div v-if="!isForward" class="video-column__extra">
        <Speedometer :current-speed="currentSpeed" />
      </div>
    </div>

    <!-- Rear camera -->
    <div
      class="video-column"
      :class="isForward ? 'video-column--small' : 'video-column--big'"
      :style="{ order: isForward ? 1 : 0 }"
    >
      <div class="video-panel">
        <div class="video-container">
          <canvas ref="videoCanvasRear" class="video-feed"></canvas>
        </div>
      </div>
      <div v-if="isForward" class="video-column__extra">
        <Speedometer :current-speed="currentSpeed" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { storeToRefs } from 'pinia'
import { useTrainStore } from '@/stores/trainStore'
import { useVideoPanel } from '@/composables/useVideoPanel'
import Speedometer from '@/components/controls/Speedometer.vue'

const {
  frameRefFront,
  frameRefRear,
  direction,
  telemetryData,
  enableStatistics,
  last30_framesAverageLatency_front,
  last30_framesAverageLatency_rear,
  last1s_framesFPS_front,
  last1s_framesFPS_rear,
  last1s_bandwidthMbps_front,
  last1s_bandwidthMbps_rear,
  last_100_frame_latencies_front,
  last_100_frame_latencies_rear,
} = storeToRefs(useTrainStore())

// Front camera is the "big" feed while the train moves forward, rear camera
// takes over the big spot once the train switches to backward direction.
const isForward = computed(() => direction.value === 'FORWARD')

const currentSpeed = computed(() => telemetryData.value?.speed || 0)

const videoCanvasFront = ref(null)
const videoCanvasRear  = ref(null)

const {
  handleFrame: handleFrameFront,
} = useVideoPanel(videoCanvasFront, {
  latencyRef:              last30_framesAverageLatency_front,
  fpsRef:                  last1s_framesFPS_front,
  bandwidthRef:            last1s_bandwidthMbps_front,
  last100frameLatenciesRef: last_100_frame_latencies_front,
  enableStatisticsRef:      enableStatistics,
})

const {
  handleFrame: handleFrameRear,
} = useVideoPanel(videoCanvasRear, {
  latencyRef:              last30_framesAverageLatency_rear,
  fpsRef:                  last1s_framesFPS_rear,
  bandwidthRef:            last1s_bandwidthMbps_rear,
  last100frameLatenciesRef: last_100_frame_latencies_rear,
  enableStatisticsRef:      enableStatistics,
})

watch(frameRefFront, (newFrame) => {
  if (!newFrame || newFrame.length === 0) return
  handleFrameFront(newFrame)
})

watch(frameRefRear, (newFrame) => {
  if (!newFrame || newFrame.length === 0) return
  handleFrameRear(newFrame)
})
</script>

<style scoped>
.video-panels {
  display: flex;
  align-items: stretch;
  gap: 8px;
  width: 100%;
}

@media (max-width: 900px), (orientation: portrait) {
  .video-panels {
    gap: 4px;
  }
}

.video-column {
  display: flex;
  flex-direction: column;
  gap: 8px;
  min-width: 0;
}

/* Split the available width proportionally (roughly 81% / 19%, matching the
   previous 2000px / 470px sizing) instead of hard-coding pixel dimensions, so
   the panels scale with whatever display/container size they're rendered in. */
.video-column--big {
  flex: 81 1 0%;
}

.video-column--small {
  flex: 19 1 0%;
}

.video-panel {
  background: linear-gradient(135deg, #f5f5f5, #e0e0e0);
  border-radius: 5px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  transition: flex-grow 0.2s ease;
  min-width: 0;
  width: 100%;
  aspect-ratio: 16 / 9;
}

/* Fills the leftover height below the small panel (the column is stretched
   to match the big column's height, but the small panel itself is shorter
   since it keeps the same 16:9 ratio at a narrower width). */
.video-column__extra {
  flex: 1 1 auto;
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 0;
}

.camera-label {
  text-align: center;
  font-size: 0.75rem;
  font-weight: 600;
  color: #555;
  padding: 4px 0 2px;
  letter-spacing: 0.05em;
  text-transform: uppercase;
}

.video-container {
  position: relative;
  width: 100%;
  height: 100%;
  background: #000;
  border-radius: 4px;
  overflow: hidden;
}

.video-feed {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  max-width: 100%;
  max-height: 100%;
}
</style>