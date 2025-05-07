<template>
  <div class="video-panel">
    <h2 v-if="currentTrain">Live Camera: {{ currentTrain.name }}</h2>
    <div class="video-container">
      <div class="video-placeholder" v-if="!isConnected">
        <p>No video feed available</p>
      </div>
      <canvas v-else ref="videoCanvas" class="video-feed"></canvas>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue'
import { storeToRefs } from 'pinia'
import { useTrainStore } from '@/stores/trainStore'
import { Player } from 'broadwayjs'

const { currentTrain, isConnected, currentVideoFrame } = storeToRefs(useTrainStore())
const videoCanvas = ref(null)
let player = null

onMounted(() => {
  // Initialize Broadway.js Player
  player = new Player({
    useWorker: true, // Use Web Worker for decoding
    workerFile: '/scripts/broadway/Decoder.js',
    canvas: videoCanvas.value
  })
})

watch(currentVideoFrame, (newFrame) => {
  if (player && newFrame) {
    // Feed the new frame to the Broadway.js decoder
    player.decode(new Uint8Array(newFrame))
  }
})

onUnmounted(() => {
  if (player) {
    player.canvas = null // Detach the canvas
    player = null
  }
})
</script>

<style scoped>
.video-panel {
  background: white;
  border-radius: 5px;
  padding: 1rem;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

.video-container {
  position: relative;
  padding-top: 56.25%; /* 16:9 aspect ratio */
  background: #000;
  border-radius: 4px;
  overflow: hidden;
}

.video-placeholder {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
}

.video-feed {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
}
</style>