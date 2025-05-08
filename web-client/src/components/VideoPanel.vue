<template>
  <div class="video-panel">
    <h2 v-if="currentTrain">Live Camera: {{ currentTrain.name }}</h2>
    <div class="video-container">
      <canvas ref="videoCanvas" class="video-feed"></canvas>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue'
import { storeToRefs } from 'pinia'
import { useTrainStore } from '@/stores/trainStore'
import { Player } from 'broadwayjs'

const { currentTrain, currentVideoFrame } = storeToRefs(useTrainStore())
const videoCanvas = ref(null)
let player = null
let recordedFrames = []
let writeToFile = true
let numberofFramesToWrite = 900


onMounted(() => {
  // do nothing
  console.log('videoCanvas after nextTick:', videoCanvas.value)
  console.log('Canvas context:', videoCanvas.value.getContext('2d'));
  console.log('Canvas dimensions:', videoCanvas.value.width, videoCanvas.value.height);
})

watch(currentVideoFrame, (newFrame) => {
  if (!newFrame || newFrame.length === 0) {
    console.warn('Invalid or empty frame data:', newFrame)
    return
  }

  if (writeToFile)
  {
    recordedFrames.push(newFrame)
    if (recordedFrames.length > numberofFramesToWrite) {
      const blob = new Blob(recordedFrames, { type: 'application/octet-stream' });
      const url = URL.createObjectURL(blob);

      // Create a download link
      const a = document.createElement('a');
      a.href = url;
      a.download = 'video-stream.h264';
      a.click();

      // Clean up
      URL.revokeObjectURL(url);
      recordedFrames = [];
    }
  }

  if (player == null) {
    console.log('Initializing Broadway.js Player...')
    videoCanvas.value.width = 640
    videoCanvas.value.height = 480

    player = new Player({
      useWorker: true,
      workerFile: '/scripts/broadway/Decoder.js',
      canvas: videoCanvas.value,
      webgl: true,
    })
    console.log('Player initialized:', player)
  }

  if (player) {
    console.log('New frame received with length:', newFrame.length)
    try {
      player.decode(newFrame)
      console.log('Frame decoded successfully')
    } catch (error) {
      console.error('Error decoding frame:', error)
    }
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
  border: 2px solid red;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
}
</style>