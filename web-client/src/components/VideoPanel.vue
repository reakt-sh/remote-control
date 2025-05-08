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

const { currentTrain, currentVideoFrame } = storeToRefs(useTrainStore())
const videoCanvas = ref(null)
let videoDecoder = null
let recordedFrames = []
let writeToFile = false
let numberofFramesToWrite = 900
let key_frame_found = null
let sps_pps = null

onMounted(() => {
  console.log('videoCanvas:', videoCanvas.value)
  console.log('Canvas context:', videoCanvas.value.getContext('2d'))
  console.log('Canvas dimensions:', videoCanvas.value.width, videoCanvas.value.height)
  key_frame_found = false;
  sps_pps = null;

  // Initialize the WebCodecs VideoDecoder with codec configuration
  videoDecoder = new VideoDecoder({
    output: (frame) => renderFrame(frame),
    error: (error) => console.error('VideoDecoder error:', error),
  })

  // Configure the VideoDecoder with the codec settings
  videoDecoder.configure({
    codec: 'avc1.42E01E', // H.264 codec string
    //codec: 'avc1.64001f',
    codedWidth: 640, // Replace with the actual video width
    codedHeight: 480, // Replace with the actual video height
  })

  console.log('VideoDecoder initialized and configured:', videoDecoder)
})

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
        const combinedFrame = new Uint8Array(sps_pps.length + newFrame.length);
        combinedFrame.set(sps_pps, 0);
        combinedFrame.set(newFrame, sps_pps.length);
        newFrame = combinedFrame;
      }

      if (nal_type === 7) {
        sps_pps = newFrame;
        console.log('SPS PPS found');
        return;
      }

      if (frame_type === 'key')
      {
        key_frame_found = true;
      }

      if (key_frame_found === true) {
        console.log('Trying to decode: ',frame_type, newFrame.length)
        videoDecoder.decode(new EncodedVideoChunk({
          type: frame_type,
          timestamp: performance.now(),
          data: new Uint8Array(newFrame),
        }))
      }
    } catch (error) {
      console.error('Error decoding frame:', error)
    }
  }
})

function renderFrame(frame) {
  const ctx = videoCanvas.value.getContext('2d')
  if (!ctx) {
    console.error('Canvas context is null')
    return
  }

  // Draw the decoded frame onto the canvas
  ctx.drawImage(frame, 0, 0, videoCanvas.value.width, videoCanvas.value.height)

  // Close the frame to release resources
  frame.close()
}

onUnmounted(() => {
  if (videoDecoder) {
    videoDecoder.close()
    videoDecoder = null
    console.log('VideoDecoder closed')
  }
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
</style>