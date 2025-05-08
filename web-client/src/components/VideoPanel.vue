<template>
  <div class="video-panel">
    <h2 v-if="currentTrain">Live Camera: {{ currentTrain.name }}</h2>
    <div class="video-container">
      <canvas ref="videoCanvas" class="video-feed"></canvas>
    </div>
    <div v-if="loading" class="loading-overlay">
      Loading FFmpeg ({{ loadedPercentage }}%)...
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue'
import { storeToRefs } from 'pinia'
import { useTrainStore } from '@/stores/trainStore'
import { createFFmpeg, fetchFile } from '@ffmpeg/ffmpeg'

const { currentTrain, currentVideoFrame } = storeToRefs(useTrainStore())
const videoCanvas = ref(null)
const ffmpeg = ref(null)
const loading = ref(false)
const loadedPercentage = ref(0)
const recordedFrames = ref([])
const writeToFile = ref(true)
const numberofFramesToWrite = 900

// Initialize FFmpeg
onMounted(async () => {
  try {
    loading.value = true
    console.log('Initializing FFmpeg...')
    
    // Correct FFmpeg initialization
    ffmpeg.value = createFFmpeg({ 
      log: true,
      progress: ({ ratio }) => {
        loadedPercentage.value = Math.round(ratio * 100)
      }
    })
    
    await ffmpeg.value.load()
    console.log('FFmpeg initialized')
    
    // Set canvas dimensions
    if (videoCanvas.value) {
      videoCanvas.value.width = 1280
      videoCanvas.value.height = 720
    }
  } catch (error) {
    console.error('FFmpeg initialization failed:', error)
  } finally {
    loading.value = false
  }
})

watch(currentVideoFrame, async (newFrame) => {
  if (!newFrame || newFrame.length === 0) {
    console.warn('Invalid or empty frame data')
    return
  }

  if (!ffmpeg.value) {
    console.warn('FFmpeg not initialized yet')
    return
  }

  if (writeToFile.value) {
    recordedFrames.value.push(newFrame)
    if (recordedFrames.value.length > numberofFramesToWrite) {
      downloadRecordedFrames()
    }
  }

  try {
    // Write the frame to FFmpeg's virtual filesystem
    await ffmpeg.value.FS('writeFile', 'input.h264', await fetchFile(new Blob([newFrame])))
    
    // Decode the frame (simplified approach)
    await ffmpeg.value.run(
      '-i', 'input.h264',
      '-frames:v', '1',          // Process only one frame
      '-f', 'image2',            // Output as image
      '-pix_fmt', 'rgb24',       // Use RGB format
      'output.png'
    )
    
    // Read the decoded frame
    const data = ffmpeg.value.FS('readFile', 'output.png')
    const blob = new Blob([data.buffer], { type: 'image/png' })
    const url = URL.createObjectURL(blob)
    
    // Render to canvas
    const ctx = videoCanvas.value.getContext('2d')
    const img = new Image()
    img.onload = () => {
      ctx.drawImage(img, 0, 0, videoCanvas.value.width, videoCanvas.value.height)
      URL.revokeObjectURL(url)
    }
    img.src = url
    
  } catch (error) {
    console.error('Error decoding frame:', error)
  }
})

const downloadRecordedFrames = () => {
  const blob = new Blob(recordedFrames.value, { type: 'video/mp4' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = 'video-stream.mp4'
  a.click()
  URL.revokeObjectURL(url)
  recordedFrames.value = []
}

onUnmounted(() => {
  if (ffmpeg.value) {
    ffmpeg.value.exit()
    ffmpeg.value = null
  }
})
</script>

<style scoped>
.video-panel {
  background: white;
  border-radius: 5px;
  padding: 1rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  position: relative;
}

.video-container {
  position: relative;
  padding-top: 56.25%; /* 16:9 aspect ratio */
  background: #000;
  border-radius: 4px;
  overflow: hidden;
}

.video-feed {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.loading-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.2rem;
}
</style>