export function useAssembler (frameRef) {
  let currentFrameId = -1
  let expectedPackets = 0
  let receivedPackets = 0
  let packetBuffer = []

  return {
    processPacket(data) {
      try {
        const frameId = (data[1] << 24) | (data[2] << 16) | (data[3] << 8) | data[4]
        const numberOfPackets = (data[5] << 8) | data[6]
        const packetId = (data[7] << 8) | data[8]
        const payload = data.slice(45)

        // New frame: reset buffer
        if (frameId !== currentFrameId) {
          packetBuffer = new Array(numberOfPackets)
          currentFrameId = frameId
          expectedPackets = numberOfPackets
          receivedPackets = 0
        }

        // Store payload at correct index (packetId - 1)
        if (!packetBuffer[packetId - 1]) {
          packetBuffer[packetId - 1] = payload
          receivedPackets += 1
        }

        // Assemble frame when all packets received
        if (receivedPackets === expectedPackets) {
          const frameData = new Uint8Array(packetBuffer.reduce((acc, part) => acc.concat(Array.from(part)), []))
          frameRef.value = frameData
          packetBuffer = []
        }
      } catch (e) {
        console.error('Packet assembly error:', e)
      }
    }
  }
}