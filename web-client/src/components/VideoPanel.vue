<template>
  <div class="video-panel">
    <div class="video-container">
      <canvas ref="videoCanvas" class="video-feed"></canvas>
      <button class="fullscreen-btn" @click="toggleFullScreen" :title="isFullScreen ? 'Exit Full Screen' : 'Full Screen'">
        <i :class="isFullScreen ? 'fa-solid fa-compress' : 'fa-solid fa-expand'"></i>
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { storeToRefs } from 'pinia'
import { useTrainStore } from '@/stores/trainStore'

const { currentVideoFrame } = storeToRefs(useTrainStore())
const videoCanvas = ref(null)
let videoDecoder = null
let recordedFrames = []
let writeToFile = false
let numberofFramesToWrite = 900
let videoWidth = 640
let videoHeight = 480
let displayWidth = 0
let displayHeight = 0
const frameQueue = []
const MAX_QUEUE_SIZE = 60 // Maximum frames to keep in the queue
let isRendering = false
const isFullScreen = ref(false)

onMounted(() => {
  updateCanvasSize()
  window.addEventListener('resize', updateCanvasSize)
  // Initialize the WebCodecs VideoDecoder with codec configuration
  videoDecoder = new VideoDecoder({
    output: (frame) => renderFrame(frame),
    error: (error) => console.error('VideoDecoder error:', error),
  })

  // Configure the VideoDecoder with the codec settings
  videoDecoder.configure({
    codec: 'avc1.42E01E',
    codedWidth: videoWidth,
    codedHeight: videoHeight,
  })

  // Listen for fullscreen change to update state
  document.addEventListener('fullscreenchange', handleFullscreenChange)
})

async function updateCanvasSize() {
  await nextTick()
  const container = videoCanvas.value.parentElement
  const containerWidth = container.clientWidth
  const containerHeight = container.clientHeight
  const videoAspect = videoWidth / videoHeight
  const containerAspect = containerWidth / containerHeight

  if (containerAspect > videoAspect) {
    // Container is wider than video - letterbox on sides
    displayHeight = containerHeight
    displayWidth = displayHeight * videoAspect
  } else {
    // Container is taller than video - letterbox on top/bottom
    displayWidth = containerWidth
    displayHeight = displayWidth / videoAspect
  }

  // Set canvas dimensions to match container
  videoCanvas.value.style.width = `${displayWidth}px`
  videoCanvas.value.style.height = `${displayHeight}px`
  videoCanvas.value.width = videoWidth
  videoCanvas.value.height = videoHeight
}

watch(currentVideoFrame, (newFrame) => {
  if (!newFrame || newFrame.length === 0) {
    console.warn('Invalid or empty frame data:', newFrame)
    return
  }

  if (writeToFile) {
    recordedFrames.push(newFrame)
    if (recordedFrames.length > numberofFramesToWrite) {
      const blob = new Blob(recordedFrames, { type: 'application/octet-stream' })
      const url = URL.createObjectURL(blob)

      // Create a download link
      const a = document.createElement('a')
      a.href = url
      a.download = 'video-stream.h264'
      a.click()

      // Clean up
      URL.revokeObjectURL(url)
      recordedFrames = []
    }
  }

  if (videoDecoder) {
    try {
      // Enqueue the frame for decoding
      frameQueue.push(newFrame)
      console.log('Frame enqueued, current queue size:', frameQueue.length)
      if (!isRendering) {
        isRendering = true
        requestAnimationFrame(renderNextFrame)
      }
    } catch (error) {
      console.error('Error decoding frame:', error)
    }
  }
})

function renderNextFrame() {
  if (frameQueue.length === 0) {
    isRendering = false
    return
  }
   // Drop frames if queue is too large to maintain real-time playback
  if (frameQueue.length > MAX_QUEUE_SIZE) {
    frameQueue.splice(0, frameQueue.length - 1)
    console.warn('Dropped frames to maintain real-time playback')
  }

  const frameData = frameQueue.shift()
  if (videoDecoder) {
    try {
      videoDecoder.decode(new EncodedVideoChunk({
        type: 'key', // or 'delta', as appropriate
        timestamp: performance.now(),
        data: frameData,
      }))
    } catch (error) {
      console.error('Error decoding frame:', error)
    }
  }
  requestAnimationFrame(renderNextFrame)

}

function renderFrame(frame) {
  const ctx = videoCanvas.value.getContext('2d')
  if (!ctx) {
    console.error('Canvas context is null')
    return
  }

  // Clear the canvas with black background
  ctx.fillStyle = 'black'
  ctx.fillRect(0, 0, videoCanvas.value.width, videoCanvas.value.height)

  // Draw the video frame centered and scaled to maintain aspect ratio
  const scale = Math.min(
    videoCanvas.value.width / frame.displayWidth,
    videoCanvas.value.height / frame.displayHeight
  )

  const scaledWidth = frame.displayWidth * scale
  const scaledHeight = frame.displayHeight * scale
  const offsetX = (videoCanvas.value.width - scaledWidth) / 2
  const offsetY = (videoCanvas.value.height - scaledHeight) / 2

  ctx.drawImage(
    frame,
    offsetX,
    offsetY,
    scaledWidth,
    scaledHeight
  )

  frame.close()
}

function toggleFullScreen() {
  const container = videoCanvas.value.parentElement
  if (!document.fullscreenElement) {
    container.requestFullscreen()
    isFullScreen.value = true
  } else {
    document.exitFullscreen()
    isFullScreen.value = false
  }
}

// Listen for fullscreen change to update state
function handleFullscreenChange() {
  isFullScreen.value = !!document.fullscreenElement
}

onUnmounted(() => {
  if (videoDecoder) {
    videoDecoder.close()
    videoDecoder = null
  }
  window.removeEventListener('resize', updateCanvasSize)
  document.removeEventListener('fullscreenchange', handleFullscreenChange)
})
</script>

<style scoped>
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