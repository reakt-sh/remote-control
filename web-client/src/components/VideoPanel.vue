<template>
  <div class="video-panel">
    <h2 v-if="telemetryData && telemetryData.name">Live Camera: {{ telemetryData.name }}</h2>
    <div class="video-container">
      <canvas ref="videoCanvas" class="video-feed"></canvas>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { storeToRefs } from 'pinia'
import { useTrainStore } from '@/stores/trainStore'

const { telemetryData, currentVideoFrame } = storeToRefs(useTrainStore())
const videoCanvas = ref(null)
let videoDecoder = null
let recordedFrames = []
let writeToFile = false
let numberofFramesToWrite = 900
let key_frame_found = null
let sps_pps = null
let videoWidth = 640
let videoHeight = 480
let displayWidth = 0
let displayHeight = 0
const frameQueue = []
let isRendering = false

onMounted(() => {
  updateCanvasSize()
  window.addEventListener('resize', updateCanvasSize)

  key_frame_found = false
  sps_pps = null

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
      let nal_type = newFrame[4] & 0x1F;
      let frame_type = 'delta';

      if (nal_type === 5) {
        frame_type = 'key'
        if (sps_pps === null) {
          console.log('SPS PPS not found, skipping frame')
          return
        }
        const combinedFrame = new Uint8Array(sps_pps.length + newFrame.length)
        combinedFrame.set(sps_pps, 0)
        combinedFrame.set(newFrame, sps_pps.length)
        newFrame = combinedFrame
      }

      if (nal_type === 7) {
        sps_pps = newFrame
        console.log('SPS PPS found')
        return
      }

      if (frame_type === 'key') {
        key_frame_found = true
      }

      if (key_frame_found === true) {
        frameQueue.push(newFrame)
        if (!isRendering) {
          isRendering = true
          requestAnimationFrame(renderNextFrame)
        }
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
  const frameData = frameQueue.shift()
  if (videoDecoder) {
    try {
      videoDecoder.decode(new EncodedVideoChunk({
        type: 'key', // or 'delta', as appropriate
        timestamp: performance.now(),
        data: new Uint8Array(frameData),
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

onUnmounted(() => {
  if (videoDecoder) {
    videoDecoder.close()
    videoDecoder = null
  }
  window.removeEventListener('resize', updateCanvasSize)
})
</script>

<style scoped>
.video-panel {
  background: white;
  border-radius: 5px;
  padding: 1rem;
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
</style>