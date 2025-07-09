export function useAssembler (frameRef) {
  let currentFrame = []
  let currentFrameId = -1
  let expectedPackets = 0
  let receivedPackets = 0

  return {
    processPacket(data) {
      try {
        const frameId = (data[1] << 24) | (data[2] << 16) | (data[3] << 8) | data[4]
        const numberOfPackets = (data[5] << 8) | data[6]
        const packetId = (data[7] << 8) | data[8]
        const payload = data.slice(45)

        if (frameId !== currentFrameId) {
          currentFrame = []
          currentFrameId = frameId
          expectedPackets = numberOfPackets
          receivedPackets = 0
        }

        currentFrame.push(...payload)
        receivedPackets += 1

        if (packetId === numberOfPackets && receivedPackets === expectedPackets) {
          frameRef.value = new Uint8Array(currentFrame)
          currentFrame = []
        }
      } catch (e) {
        console.error('Packet assembly error:', e)
      }
    }
  }
}