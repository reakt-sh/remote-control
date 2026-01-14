// src/composables/useVideoPanel.js

import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import { VideoDecoderWrapper } from '@/scripts/webcodec'

export function useVideoPanel(canvasRef, options = {}) {
  const {
    videoWidth = 1280,
    videoHeight = 720,
    maxQueueSize = 60,
    latencyRef = null,
    fpsRef = null
  } = options

  const isFullScreen = ref(false)
  let videoDecoder = null
  let isCanvasInitialized = false

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

    // Only update canvas size if not initialized yet
    if (!isCanvasInitialized) {
      updateCanvasSize()
      isCanvasInitialized = true
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

    // Helper to stack overlays bottom-left, one after another (upwards)
    const drawOverlayBL = (text) => {
      ctx.font = 'bold 20px Arial'
      const padding = 12
      const textMetrics = ctx.measureText(text)
      const boxWidth = textMetrics.width + padding * 2
      const boxHeight = 32
      const boxX = 10
      // use a persistent y that moves upward as we draw additional rows
      if (typeof drawOverlayBL.nextY !== 'number') {
        drawOverlayBL.nextY = canvasRef.value.height - 10
      }
      const boxY = drawOverlayBL.nextY - boxHeight

      // background
      ctx.fillStyle = 'rgba(0, 0, 0, 0.7)'
      ctx.fillRect(boxX, boxY, boxWidth, boxHeight)

      // text
      ctx.fillStyle = '#00ff00'
      ctx.fillText(text, boxX + padding, boxY + boxHeight - 8)

      // move up for next overlay (with small gap)
      drawOverlayBL.nextY = boxY - 6
    }

    // Draw overlays in bottom-left: latency then FPS stacked above
    if (latencyRef && latencyRef.value > 0) {
      const latency = latencyRef.value.toFixed(1)
      drawOverlayBL(`Average Latency (last 30 frames): ${latency} ms`)
    }

    if (fpsRef && fpsRef.value > 0) {
      const fps = fpsRef.value.toFixed(1)
      drawOverlayBL(`FPS (last 1s): ${fps}`)
    }
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
    
    // Set the actual canvas resolution to match the video resolution
    // This ensures crisp rendering without scaling artifacts
    canvasRef.value.width = videoWidth
    canvasRef.value.height = videoHeight

    // Force a redraw to prevent blurriness
    const ctx = canvasRef.value.getContext('2d')
    if (ctx) {
      // Disable image smoothing for crisp pixel-perfect rendering
      ctx.imageSmoothingEnabled = false
      ctx.webkitImageSmoothingEnabled = false
      ctx.mozImageSmoothingEnabled = false
      ctx.msImageSmoothingEnabled = false
    }
    
    // Mark as initialized
    isCanvasInitialized = true
  }

  function handleResize() {
    isCanvasInitialized = false
    updateCanvasSize()
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
    // Reset initialization and update canvas size when fullscreen changes
    isCanvasInitialized = false
    setTimeout(() => updateCanvasSize(), 100)
  }

  onMounted(() => {
    initializeDecoder()
    updateCanvasSize()
    window.addEventListener('resize', handleResize)
    document.addEventListener('fullscreenchange', handleFullscreenChange)
  })

  onUnmounted(() => {
    if (videoDecoder) {
      videoDecoder.cleanup()
    }
    window.removeEventListener('resize', handleResize)
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