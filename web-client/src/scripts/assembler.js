/**
 * Frame assembler with ring buffer support for handling out-of-order packets
 * across multiple frames. Maintains state for up to 30 frames.
 * 
 * Features:
 * - Ring buffer for last 30 frames
 * - Out-of-order packet handling
 * - Automatic frame eviction when complete or when buffer is full
 * - Efficient memory management
 */

export class useAssembler {
  /**
   * @param {Object} options Configuration options
   * @param {number} options.maxFrames Maximum frames to track (default: 30)
   * @param {Function} options.onFrameComplete Callback when frame is complete
   */
  constructor({ maxFrames = 30, onFrameComplete } = {}) {
    this.maxFrames = maxFrames
    this.onFrameComplete = onFrameComplete
    this.frameBuffer = new Map()
    this.frameOrderQueue = []
    
    // Pre-create reusable objects for performance
    this.textDecoder = new TextDecoder()
    this.tempDataView = null
    this.tempUint8Array = new Uint8Array(36) // For train_id extraction
  }

  /**
   * Process an incoming packet
   * @param {Uint8Array} data Raw packet data
   */
  processPacket(data) {
    try {
      const { frameId, numberOfPackets, packetId, payload, timestamp } = this._parsePacket(data)
      // Get or create frame state
      let frameState = this.frameBuffer.get(frameId)
      if (!frameState) {
        frameState = this._createFrameState(frameId, numberOfPackets, timestamp)
      }

      // Store payload if not already received
      if (!frameState.packetBuffer[packetId - 1]) {
        frameState.packetBuffer[packetId - 1] = payload
        frameState.receivedPackets++

        // Check for frame completion
        if (frameState.receivedPackets === frameState.expectedPackets) {
          this._handleCompleteFrame(frameState)
        }
      }
    } catch (e) {
      console.error('Packet processing error:', e)
    }
  }

  /**
   * Parse packet header and extract metadata (optimized version)
   * @private
   */
  _parsePacket(data) {
    // Extract frame ID using bit operations (fastest)
    const frameId = (data[1] << 24) | (data[2] << 16) | (data[3] << 8) | data[4]
    
    // Extract packet counts and ID
    const numberOfPackets = (data[5] << 8) | data[6]
    const packetId = (data[7] << 8) | data[8]
    
    // Extract train_id efficiently by copying only the needed bytes
    this.tempUint8Array.set(data.subarray(9, 45))
    let trainIdEnd = 36
    // Find the first null byte or end of array
    for (let i = 0; i < 36; i++) {
      if (this.tempUint8Array[i] === 0) {
        trainIdEnd = i
        break
      }
    }
    const train_id = this.textDecoder.decode(this.tempUint8Array.subarray(0, trainIdEnd))
    
    // Fast timestamp parsing using direct memory access
    const timestamp = this._parseTimestampFast(data, 45)
    
    return {
      frameId,
      numberOfPackets,
      packetId,
      train_id,
      timestamp,
      payload: data.subarray(53) // Use subarray instead of slice for better performance
    }
  }

  /**
   * Optimized 64-bit timestamp parsing
   * @private
   */
  _parseTimestampFast(data, offset) {
    // Try little-endian interpretation first (most common)
    const b0 = data[offset]
    const b1 = data[offset + 1]
    const b2 = data[offset + 2]
    const b3 = data[offset + 3]
    const b4 = data[offset + 4]
    const b5 = data[offset + 5]
    const b6 = data[offset + 6]
    const b7 = data[offset + 7]


    // Try big-endian: most significant bytes first
    const highBE = (b0 << 24) | (b1 << 16) | (b2 << 8) | b3
    const lowBE = (b4 << 24) | (b5 << 16) | (b6 << 8) | b7
    const timestampBE = (highBE * 0x100000000) + (lowBE >>> 0)
    return timestampBE
  }

  /**
   * Create new frame state and manage buffer limits
   * @private
   */
  _createFrameState(frameId, numberOfPackets, timestamp) {
    // Evict oldest frame if buffer is full
    if (this.frameBuffer.size >= this.maxFrames) {
      const oldestFrameId = this.frameOrderQueue.shift()
      this.frameBuffer.delete(oldestFrameId)
    }

    const frameState = {
      frameId,
      expectedPackets: numberOfPackets,
      receivedPackets: 0,
      packetBuffer: new Array(numberOfPackets),
      createdAt: timestamp
    }

    this.frameBuffer.set(frameId, frameState)
    this.frameOrderQueue.push(frameId)

    return frameState
  }

  /**
   * Handle completed frame assembly (optimized)
   * @private
   */
  _handleCompleteFrame(frameState) {
    // Calculate frame reconstruction latency
    const currentTime = Date.now()
    const frameLatency = currentTime - frameState.createdAt

    // Pre-calculate total size for better memory allocation
    let totalSize = 0
    for (let i = 0; i < frameState.packetBuffer.length; i++) {
      if (frameState.packetBuffer[i]) {
        totalSize += frameState.packetBuffer[i].length
      }
    }

    // Allocate frame data once with correct size
    const frameData = new Uint8Array(totalSize)
    let offset = 0
    
    // Copy packets in order with single allocation
    for (let i = 0; i < frameState.packetBuffer.length; i++) {
      const packet = frameState.packetBuffer[i]
      if (packet) {
        frameData.set(packet, offset)
        offset += packet.length
      }
    }

    // Remove from buffer and queue
    this.frameBuffer.delete(frameState.frameId)
    this.frameOrderQueue = this.frameOrderQueue.filter(id => id !== frameState.frameId)

    // Notify completion
    if (this.onFrameComplete) {
      this.onFrameComplete({
        frameId: frameState.frameId,
        data: frameData,
        latency: frameLatency
      })
    }
  }

  /**
   * Get current frame states (for debugging/monitoring)
   */
  getFrameStates() {
    return Array.from(this.frameBuffer.values()).map(state => ({
      frameId: state.frameId,
      progress: `${state.receivedPackets}/${state.expectedPackets}`,
      age: Date.now() - state.createdAt
    }))
  }
}