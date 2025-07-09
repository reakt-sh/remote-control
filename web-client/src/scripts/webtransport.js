import { ref } from 'vue'
import { QUIC_URL } from '@/scripts/config'

export function useWebTransport(remoteControlId, messageHandler) {
  const isWTConnected = ref(false)
  const transport = ref(null)
  const bidistream = ref(null)

  async function connect() {
    if (isWTConnected.value) return

    if (transport.value) {
      await transport.value.close()
    }

    try {
      transport.value = new WebTransport(QUIC_URL)
      await transport.value.ready
      console.log('WebTransport connected:', QUIC_URL)
      isWTConnected.value = true

      bidistream.value = await transport.value.createBidirectionalStream()
      setupStreamReader()
      setupDatagramReader()
      await send(`REMOTE_CONTROL:${remoteControlId.value}`);
    } catch (error) {
      console.error('WT connection error:', error)
      isWTConnected.value = false
    }
  }

  async function disconnect() {
    if (transport.value) {
      await transport.value.close()
      isWTConnected.value = false
    }
  }

  async function send(message) {
    if (!isWTConnected.value || !bidistream.value) {
      console.log('WebTransport not connected')
    }

    try {
      const writer = bidistream.value.writable.getWriter();
      let data;
      if (typeof message === 'string') {
        data = new TextEncoder().encode(message);
      } else if (message instanceof Uint8Array) {
        data = message;
      } else {
        throw new Error('Unsupported message type');
      }
      await writer.write(data);
      writer.releaseLock();
      console.log('WebTransport message sent:', message);
    } catch (error) {
      console.error('Error sending WebTransport message:', error);
    }
  }

  function setupStreamReader() {
    const reader = bidistream.value.readable.getReader()
    const readChunk = async () => {
      const { value, done } = await reader.read()
      if (done) return

      const byteArray = new Uint8Array(value)
      messageHandler(byteArray[0], byteArray.slice(1))
      readChunk()
    }

    readChunk().catch(console.error)
  }

  function setupDatagramReader() {
    const reader = transport.value.datagrams.readable.getReader()
    const readChunk = async () => {
      const { value, done } = await reader.read()
      if (done) return

      messageHandler(value[0], value)
      readChunk()
    }
    readChunk().catch(console.error)
  }

  return {
    isWTConnected,
    connectWebTransport: connect,
    sendWtMessage: send,
    disconnectWebTransport: disconnect
  }
}