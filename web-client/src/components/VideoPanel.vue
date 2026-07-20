<template>
  <div class="video-panels">
    <!-- Front camera -->
    <div class="video-panel">
      <div class="camera-label">Front Camera</div>
      <div class="video-container">
        <canvas ref="videoCanvasFront" class="video-feed"></canvas>
        <button
          class="fullscreen-btn"
          @click="toggleFullScreenFront"
          :title="isFullScreenFront ? 'Exit Full Screen' : 'Full Screen'"
        >
          <i :class="isFullScreenFront ? 'fa-solid fa-compress' : 'fa-solid fa-expand'"></i>
        </button>
      </div>
    </div>

    <!-- Rear camera -->
    <div class="video-panel">
      <div class="camera-label">Rear Camera</div>
      <div class="video-container">
        <canvas ref="videoCanvasRear" class="video-feed"></canvas>
        <button
          class="fullscreen-btn"
          @click="toggleFullScreenRear"
          :title="isFullScreenRear ? 'Exit Full Screen' : 'Full Screen'"
        >
          <i :class="isFullScreenRear ? 'fa-solid fa-compress' : 'fa-solid fa-expand'"></i>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { storeToRefs } from 'pinia'
import { useTrainStore } from '@/stores/trainStore'
import { useVideoPanel } from '@/composables/useVideoPanel'

const {
  frameRefFront,
  frameRefRear,
  last30_framesAverageLatency_front,
  last30_framesAverageLatency_rear,
  last1s_framesFPS_front,
  last1s_framesFPS_rear,
  last1s_bandwidthMbps_front,
  last1s_bandwidthMbps_rear,
  last_100_frame_latencies_front,
  last_100_frame_latencies_rear,
} = storeToRefs(useTrainStore())

const videoCanvasFront = ref(null)
const videoCanvasRear  = ref(null)

const {
  isFullScreen: isFullScreenFront,
  toggleFullScreen: toggleFullScreenFront,
  handleFrame: handleFrameFront,
} = useVideoPanel(videoCanvasFront, {
  latencyRef:              last30_framesAverageLatency_front,
  fpsRef:                  last1s_framesFPS_front,
  bandwidthRef:            last1s_bandwidthMbps_front,
  last100frameLatenciesRef: last_100_frame_latencies_front,
})

const {
  isFullScreen: isFullScreenRear,
  toggleFullScreen: toggleFullScreenRear,
  handleFrame: handleFrameRear,
} = useVideoPanel(videoCanvasRear, {
  latencyRef:              last30_framesAverageLatency_rear,
  fpsRef:                  last1s_framesFPS_rear,
  bandwidthRef:            last1s_bandwidthMbps_rear,
  last100frameLatenciesRef: last_100_frame_latencies_rear,
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
  gap: 8px;
  width: 100%;
}

.video-panel {
  flex: 1;
  min-width: 0;
  background: linear-gradient(135deg, #f5f5f5, #e0e0e0);
  border-radius: 5px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
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
  padding-top: 56.25%; /* 16:9 aspect ratio */
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

.fullscreen-btn {
  position: absolute;
  top: 12px;
  right: 12px;
  z-index: 10;
  background: rgba(30, 30, 30, 0.7);
  border: none;
  border-radius: 50%;
  width: 38px;
  height: 38px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  cursor: pointer;
  transition: background 0.2s;
  font-size: 1.3em;
}

.fullscreen-btn:hover {
  background: rgba(60, 60, 60, 0.85);
}

.fullscreen-btn i {
  pointer-events: none;
}
</style>