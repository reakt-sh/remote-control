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
   * Parse packet header and extract metadata
   * @private
   */
  _parsePacket(data) {
    return {
      frameId: (data[1] << 24) | (data[2] << 16) | (data[3] << 8) | data[4],
      numberOfPackets: (data[5] << 8) | data[6],
      packetId: (data[7] << 8) | data[8],
      train_id: new TextDecoder().decode(data.slice(9, 45)).replace(/\0/g, '').trim(),
      timestamp: this._parseTimestamp(data, 45),
      payload: data.slice(53)
    }
  }

  /**
   * Parse 64-bit timestamp from packet data
   * @private
   */
  _parseTimestamp(data, offset) {
    const view = new DataView(data.buffer, data.byteOffset + offset, 8)
    const high = view.getUint32(0, false) // Big-endian, first 4 bytes
    const low = view.getUint32(4, false)  // Big-endian, last 4 bytes
    return (high * 0x100000000) + low
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
   * Handle completed frame assembly
   * @private
   */
  _handleCompleteFrame(frameState) {
    // Calculate frame reconstruction latency
    const currentTime = Date.now()
    const frameLatency = currentTime - frameState.createdAt
    // log both timestamp, created at and now, and latency
    console.log(`🎬 Frame ${frameState.frameId} reconstructed - Created At: ${frameState.createdAt}, Now: ${currentTime}, Latency: ${frameLatency}ms`)

    // Concatenate all packets in order
    const frameData = new Uint8Array(
      frameState.packetBuffer.reduce(
        (acc, part) => acc.concat(Array.from(part)),
        []
      )
    )

    // Remove from buffer and queue
    this.frameBuffer.delete(frameState.frameId)
    this.frameOrderQueue = this.frameOrderQueue.filter(id => id !== frameState.frameId)

    // Notify completion
    if (this.onFrameComplete) {
      this.onFrameComplete({
        frameId: frameState.frameId,
        data: frameData,
        timestamp: frameState.createdAt
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