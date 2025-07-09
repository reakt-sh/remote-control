// src/composables/useVideoPanel.js

import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import { VideoDecoderWrapper } from '@/scripts/webcodec'

export function useVideoPanel(canvasRef, options = {}) {
  const {
    videoWidth = 1280,
    videoHeight = 720,
    maxQueueSize = 60
  } = options

  const isFullScreen = ref(false)
  let videoDecoder = null

  function initializeDecoder() {
    videoDecoder = new VideoDecoderWrapper({
      maxQueueSize,
      onFrameDecoded: (frame) => renderFrameToCanvas(frame),
      onError: (error) => console.error('VideoDecoder error:', error)
    })
  }

  function renderFrameToCanvas(frame) {
    const ctx = canvasRef.value.getContext('2d')
    if (!ctx) {
      console.error('Canvas context is null')
      return
    }

    // Clear the canvas with black background
    ctx.fillStyle = 'black'
    ctx.fillRect(0, 0, canvasRef.value.width, canvasRef.value.height)

    // Draw the video frame centered and scaled to maintain aspect ratio
    const scale = Math.min(
      canvasRef.value.width / frame.displayWidth,
      canvasRef.value.height / frame.displayHeight
    )

    const scaledWidth = frame.displayWidth * scale
    const scaledHeight = frame.displayHeight * scale
    const offsetX = (canvasRef.value.width - scaledWidth) / 2
    const offsetY = (canvasRef.value.height - scaledHeight) / 2

    ctx.drawImage(
      frame,
      offsetX,
      offsetY,
      scaledWidth,
      scaledHeight
    )
  }

  async function updateCanvasSize() {
    await nextTick()
    if (!canvasRef.value) return

    const container = canvasRef.value.parentElement
    const containerWidth = container.clientWidth
    const containerHeight = container.clientHeight
    const videoAspect = videoWidth / videoHeight
    const containerAspect = containerWidth / containerHeight

    let displayWidth, displayHeight

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
    canvasRef.value.style.width = `${displayWidth}px`
    canvasRef.value.style.height = `${displayHeight}px`
    canvasRef.value.width = videoWidth
    canvasRef.value.height = videoHeight
  }

  function toggleFullScreen() {
    const container = canvasRef.value.parentElement
    if (!document.fullscreenElement) {
      container.requestFullscreen()
      isFullScreen.value = true
    } else {
      document.exitFullscreen()
      isFullScreen.value = false
    }
  }

  function handleFullscreenChange() {
    isFullScreen.value = !!document.fullscreenElement
  }

  onMounted(() => {
    initializeDecoder()
    updateCanvasSize()
    window.addEventListener('resize', updateCanvasSize)
    document.addEventListener('fullscreenchange', handleFullscreenChange)
  })

  onUnmounted(() => {
    if (videoDecoder) {
      videoDecoder.cleanup()
    }
    window.removeEventListener('resize', updateCanvasSize)
    document.removeEventListener('fullscreenchange', handleFullscreenChange)
  })

  return {
    isFullScreen,
    updateCanvasSize,
    toggleFullScreen,
    handleFrame: (frameData) => {
      if (videoDecoder) {
        videoDecoder.enqueueFrame(frameData)
      }
    }
  }
}