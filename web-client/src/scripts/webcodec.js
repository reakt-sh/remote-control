export class VideoDecoderWrapper {
  constructor(options) {
    this.maxQueueSize = options.maxQueueSize || 60
    this.onFrameDecoded = options.onFrameDecoded || (() => {})
    this.onError = options.onError || (() => {})

    this.frameQueue = []
    this.isRendering = false
    this.videoDecoder = null
    this.isClosed = false; // Add this line
    this.initializeDecoder()
  }

  initializeDecoder() {
    this.videoDecoder = new VideoDecoder({
      output: (frame) => this.handleDecodedFrame(frame),
      error: (error) => {
        this.onError(error)
      }
    })
    this.isClosed = false; // Reset flag when (re)initializing
    this.videoDecoder.configure({
      codec: 'avc1.42E01E'
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

    if (this.isClosed) {
      this.initializeDecoder()
    }

    const frameData = this.frameQueue.shift()
    try {
      this.videoDecoder.decode(new EncodedVideoChunk({
        type: 'key', // or 'delta' based on your stream
        timestamp: performance.now(),
        data: frameData,
      }))
    } catch (error) {
      console.error('Failed decoding frame ==> Waiting for next IDR frame')
      // this.onError(error)

      // re-initialize decoder while getting un-expected decode error
      this.initializeDecoder()
    }

    requestAnimationFrame(() => this.renderNextFrame())
  }

  handleDecodedFrame(frame) {
    this.onFrameDecoded(frame)
    frame.close()
  }

  cleanup() {
    if (this.videoDecoder && !this.isClosed) {
      this.videoDecoder.close()
      this.isClosed = true
      this.videoDecoder = null
    }
    this.frameQueue = []
    this.isRendering = false
  }
}