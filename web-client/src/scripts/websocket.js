import { ref } from 'vue'
import { WS_URL } from '@/scripts/config'


export function useWebSocket(remoteControlId, messageHandler) {
  const isWSConnected = ref(false)
  const webSocket = ref(null)

  async function connect() {
    if (isWSConnected.value) return

    if (webSocket.value) {
      webSocket.value.close()
    }

    webSocket.value = new WebSocket(`${WS_URL}/ws/remote_control/${remoteControlId.value}`)

    webSocket.value.onopen = () => {
      isWSConnected.value = true
      console.log('✅ WebSocket connected')
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
      isWSConnected.value = false
      console.log('❌ WebSocket disconnected')
    }

    webSocket.value.onerror = (error) => {
      console.error('❌ WebSocket error:', error)
      isWSConnected.value = false
    }
  }

  function disconnect() {
    if (webSocket.value) {
      webSocket.value.close()
    }
  }

  function send(data) {
    if (!isWSConnected.value || !webSocket.value) {
      console.log('❌ WebSocket not connected')
      return
    }
    webSocket.value.send(data)
  }

  return {
    isWSConnected,
    connectWebSocket: connect,
    sendWsCommand: send,
    disconnectWebSocket: disconnect
  }
}