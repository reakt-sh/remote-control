<template>
  <div class="video-panel">
    <div class="video-container">
      <canvas ref="videoCanvas" class="video-feed"></canvas>
      <button
        class="fullscreen-btn"
        @click="toggleFullScreen"
        :title="isFullScreen ? 'Exit Full Screen' : 'Full Screen'"
      >
        <i :class="isFullScreen ? 'fa-solid fa-compress' : 'fa-solid fa-expand'"></i>
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { storeToRefs } from 'pinia'
import { useTrainStore } from '@/stores/trainStore'
import { useVideoPanel } from '@/composables/useVideoPanel'

const { frameRef } = storeToRefs(useTrainStore())
const videoCanvas = ref(null)

const {
  isFullScreen,
  toggleFullScreen,
  handleFrame
} = useVideoPanel(videoCanvas)

watch(frameRef, (newFrame) => {
  if (!newFrame || newFrame.length === 0) {
    console.warn('Invalid or empty frame data:', newFrame)
    return
  }
  handleFrame(newFrame)
})
</script>

<style scoped>
/* Existing styles remain the same */
.video-panel {
  background: linear-gradient(135deg, #f5f5f5, #e0e0e0);
  border-radius: 5px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
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