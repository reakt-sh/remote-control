import { ref } from 'vue'
import { WS_URL } from '@/scripts/config'


export function useWebSocket(remoteControlId, messageHandler) {
  const isConnected = ref(false)
  const webSocket = ref(null)

  async function connect() {
    if (isConnected.value) return

    if (webSocket.value) {
      webSocket.value.close()
    }

    webSocket.value = new WebSocket(`${WS_URL}/ws/remote_control/${remoteControlId.value}`)

    webSocket.value.onopen = () => {
      isConnected.value = true
      console.log('WebSocket connected')
    }

    webSocket.value.onmessage = async (event) => {
      if (event.data instanceof Blob) {
        try {
          const arrayBuffer = await event.data.arrayBuffer()
          const byteArray = new Uint8Array(arrayBuffer)
          messageHandler(byteArray[0], byteArray.slice(1))
        } catch (error) {
          console.error('WS message processing error:', error)
        }
      }
    }

    webSocket.value.onclose = () => {
      isConnected.value = false
      console.log('WebSocket disconnected')
    }

    webSocket.value.onerror = (error) => {
      console.error('WebSocket error:', error)
      isConnected.value = false
    }
  }

  function disconnect() {
    if (webSocket.value) {
      webSocket.value.close()
    }
  }

  function send(data) {
    if (!isConnected.value || !webSocket.value) {
      throw new Error('WebSocket not connected')
    }
    webSocket.value.send(data)
  }

  return {
    isConnected,
    connectWebSocket: connect,
    sendWsCommand: send,
    disconnectWebSocket: disconnect
  }
}