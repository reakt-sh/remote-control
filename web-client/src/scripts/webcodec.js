export class VideoDecoderWrapper {
  constructor(options) {
    this.videoWidth = options.videoWidth || 640
    this.videoHeight = options.videoHeight || 480
    this.maxQueueSize = options.maxQueueSize || 60
    this.onFrameDecoded = options.onFrameDecoded || (() => {})
    this.onError = options.onError || (() => {})

    this.frameQueue = []
    this.isRendering = false
    this.videoDecoder = null
    this.initializeDecoder()
  }

  initializeDecoder() {
    this.videoDecoder = new VideoDecoder({
      output: (frame) => this.handleDecodedFrame(frame),
      error: (error) => {
        console.error('VideoDecoder error:', error)
        this.onError(error)
      }
    })

    this.videoDecoder.configure({
      codec: 'avc1.42E01E',
      codedWidth: this.videoWidth,
      codedHeight: this.videoHeight,
    })
  }

  enqueueFrame(frameData) {
    if (!frameData || frameData.length === 0) {
      console.warn('Invalid frame data received')
      return
    }

    this.frameQueue.push(frameData)

    // Drop frames if queue is too large to maintain real-time playback
    if (this.frameQueue.length > this.maxQueueSize) {
      this.frameQueue.splice(0, this.frameQueue.length - 1)
      console.warn('Dropped frames to maintain real-time playback')
    }

    if (!this.isRendering) {
      this.isRendering = true
      this.renderNextFrame()
    }
  }

  renderNextFrame() {
    if (this.frameQueue.length === 0) {
      this.isRendering = false
      return
    }

    const frameData = this.frameQueue.shift()
    try {
      this.videoDecoder.decode(new EncodedVideoChunk({
        type: 'key', // or 'delta' based on your stream
        timestamp: performance.now(),
        data: frameData,
      }))
    } catch (error) {
      console.error('Error decoding frame:', error)
      this.onError(error)
    }

    requestAnimationFrame(() => this.renderNextFrame())
  }

  handleDecodedFrame(frame) {
    this.onFrameDecoded(frame)
    frame.close()
  }

  cleanup() {
    if (this.videoDecoder) {
      this.videoDecoder.close()
      this.videoDecoder = null
    }
    this.frameQueue = []
    this.isRendering = false
  }
}