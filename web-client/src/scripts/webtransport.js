import { ref } from 'vue'
import { QUIC_URL } from '@/scripts/config'

export function useWebTransport(remoteControlId, messageHandler) {
  const isWTConnected = ref(false)
  const transport = ref(null)
  const bidistream = ref(null)
  
  // Reconnection configuration and state
  const maxRetryAttempts = 5
  const baseRetryDelay = 1000 // 1 second
  const maxRetryDelay = 30000 // 30 seconds
  let retryCount = 0
  let reconnectTimeout = null
  let isReconnecting = false
  let shouldReconnect = true

  async function attemptReconnect() {
    if (!shouldReconnect || isReconnecting) return

    isReconnecting = true
    retryCount++

    if (retryCount > maxRetryAttempts) {
      console.error('❌ Max reconnection attempts reached. Giving up.')
      isReconnecting = false
      return
    }

    // Calculate exponential backoff delay
    const delay = Math.min(baseRetryDelay * Math.pow(2, retryCount - 1), maxRetryDelay)
    console.log(`🔄 Attempting reconnection ${retryCount}/${maxRetryAttempts} in ${delay}ms...`)

    reconnectTimeout = setTimeout(async () => {
      try {
        await connect(true) // Pass true to indicate this is a reconnection attempt
        isReconnecting = false
        retryCount = 0 // Reset retry count on successful connection
      } catch (error) {
        console.error('❌ Reconnection attempt failed:', error)
        isReconnecting = false
        attemptReconnect() // Try again
      }
    }, delay)
  }

  async function connect(isReconnectAttempt = false) {
    if (isWTConnected.value || (isReconnecting && !isReconnectAttempt)) return

    if (!isReconnectAttempt) {
      shouldReconnect = true // Enable auto-reconnect for manual connections
    }

    if (transport.value) {
      await transport.value.close()
    }

    try {
      transport.value = new WebTransport(QUIC_URL)

      // Handle connection closed event
      transport.value.closed.then(() => {
        console.log('❌ WebTransport connection closed')
        isWTConnected.value = false
        if (shouldReconnect && !isReconnecting) {
          attemptReconnect()
        }
      }).catch((error) => {
        console.error('❌ WebTransport connection lost:', error)
        isWTConnected.value = false
        if (shouldReconnect && !isReconnecting) {
          attemptReconnect()
        }
      })

      await transport.value.ready
      console.log('✅ WebTransport connected:', QUIC_URL)
      isWTConnected.value = true

      bidistream.value = await transport.value.createBidirectionalStream()
      setupStreamReader()
      setupDatagramReader()
      await send(`REMOTE_CONTROL:${remoteControlId.value}`);
    } catch (error) {
      console.error('❌ WT connection error:', error)
      isWTConnected.value = false
      if (shouldReconnect && !isReconnecting && !isReconnectAttempt) {
        attemptReconnect()
      }
      throw error // Re-throw for reconnection attempts to handle properly
    }
  }

  async function disconnect() {
    // Stop auto-reconnection
    shouldReconnect = false
    
    // Cancel any pending reconnection attempts
    if (reconnectTimeout) {
      clearTimeout(reconnectTimeout)
      reconnectTimeout = null
    }
    
    // Reset state
    isReconnecting = false
    retryCount = 0
    
    if (transport.value) {
      await transport.value.close()
      isWTConnected.value = false
    }
  }

  async function send(message) {
    if (!isWTConnected.value || !bidistream.value) {
      const error = 'WebTransport not connected'
      console.log('❌', error)
      return
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
    } catch (error) {
      console.error('❌ Error sending WebTransport message:', error);
      // Check if connection is lost
      if (error.name === 'WebTransportError' && error.message.includes('Connection lost')) {
        isWTConnected.value = false
        if (shouldReconnect && !isReconnecting) {
          attemptReconnect()
        }
      }
      throw error // Re-throw the error so callers know it failed
    }
  }

  function setupStreamReader() {
    const reader = bidistream.value.readable.getReader()
    const readChunk = async () => {
      try {
        const { value, done } = await reader.read()
        if (done) {
          console.log('❌ WebTransport stream ended')
          isWTConnected.value = false
          if (shouldReconnect && !isReconnecting) {
            attemptReconnect()
          }
          return
        }

        const byteArray = new Uint8Array(value)
        messageHandler(byteArray[0], byteArray.slice(1))
        readChunk()
      } catch (error) {
        console.error('❌ WebTransport stream read error:', error)
        isWTConnected.value = false
        if (shouldReconnect && !isReconnecting) {
          attemptReconnect()
        }
      }
    }

    readChunk().catch((error) => {
      console.error('❌ WebTransport stream reader error:', error)
      isWTConnected.value = false
      if (shouldReconnect && !isReconnecting) {
        attemptReconnect()
      }
    })
  }

  function setupDatagramReader() {
    const reader = transport.value.datagrams.readable.getReader()
    const readChunk = async () => {
      try {
        const { value, done } = await reader.read()
        if (done) {
          console.log('❌ WebTransport datagram stream ended')
          return
        }

        messageHandler(value[0], value)
        readChunk()
      } catch (error) {
        console.error('❌ WebTransport datagram read error:', error)
        isWTConnected.value = false
        if (shouldReconnect && !isReconnecting) {
          attemptReconnect()
        }
      }
    }

    readChunk().catch((error) => {
      console.error('❌ WebTransport datagram reader error:', error)
      isWTConnected.value = false
      if (shouldReconnect && !isReconnecting) {
        attemptReconnect()
      }
    })
  }

  // Manual reconnection function (useful for forcing a reconnection)
  async function forceReconnect() {
    shouldReconnect = true
    retryCount = 0
    if (isWTConnected.value) {
      await disconnect()
    }
    await connect()
  }

  // Get current retry status
  function getRetryStatus() {
    return {
      isReconnecting,
      retryCount,
      maxRetryAttempts,
      shouldReconnect
    }
  }

  return {
    isWTConnected,
    connectWebTransport: connect,
    sendWtMessage: send,
    disconnectWebTransport: disconnect,
    forceReconnect,
    getRetryStatus
  }
}