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
      const { frameId, numberOfPackets, packetId, payload } = this._parsePacket(data)
      // Get or create frame state
      let frameState = this.frameBuffer.get(frameId)
      if (!frameState) {
        frameState = this._createFrameState(frameId, numberOfPackets)
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
      timestamp: (data[45] << 56) | (data[46] << 48) | (data[47] << 40) | (data[48] << 32) | (data[49] << 24) | (data[50] << 16) | (data[51] << 8) | data[52],
      payload: data.slice(53)
    }
  }

  /**
   * Create new frame state and manage buffer limits
   * @private
   */
  _createFrameState(frameId, numberOfPackets) {
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
      createdAt: Date.now()
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