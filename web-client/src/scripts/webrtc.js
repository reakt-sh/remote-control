import { ref } from 'vue'
import { SERVER_URL } from '@/scripts/config'

export function useWebRTC(remoteControlId, messageHandler) {
  const isRTCConnected = ref(false)
  const peerConnection = ref(null)
  const videoDataChannel = ref(null)
  const commandsDataChannel = ref(null)
  const reconnectAttempts = ref(0)
  const maxReconnectAttempts = ref(5)
  const reconnectTimeout = ref(null)

  // Configuration for the RTCPeerConnection
  const rtcConfig = {
    iceServers: [
      { urls: 'stun:stun.l.google.com:19302' },
      { urls: 'stun:stun1.l.google.com:19302' }
    ],
    iceCandidatePoolSize: 10,
    iceTransportPolicy: 'all',  // Allow both STUN and TURN
    bundlePolicy: 'max-bundle',  // Bundle all streams
    rtcpMuxPolicy: 'require'  // Multiplex RTP and RTCP
  }

  async function connect() {
    if (isRTCConnected.value) {
      console.log('⚠️ WebRTC already connected')
      return
    }

    try {
      console.log('🔄 Initializing WebRTC connection...')

      // Create peer connection
      peerConnection.value = new RTCPeerConnection(rtcConfig)

      // Set up connection state handlers
      peerConnection.value.onconnectionstatechange = () => {
        console.log(`🔄 WebRTC Connection state: ${peerConnection.value.connectionState}`)
        
        if (peerConnection.value.connectionState === 'connected') {
          isRTCConnected.value = true
          reconnectAttempts.value = 0  // Reset reconnect counter on successful connection
          console.log('✅ WebRTC peer connection established')
        } else if (peerConnection.value.connectionState === 'disconnected') {
          isRTCConnected.value = false
          console.log('⚠️ WebRTC peer connection disconnected - attempting to reconnect...')
          attemptReconnect()
        } else if (peerConnection.value.connectionState === 'failed') {
          isRTCConnected.value = false
          console.log('❌ WebRTC peer connection failed - attempting to reconnect...')
          attemptReconnect()
        } else if (peerConnection.value.connectionState === 'closed') {
          isRTCConnected.value = false
          console.log('❌ WebRTC peer connection closed')
        }
      }

      peerConnection.value.oniceconnectionstatechange = () => {
        console.log(`🧊 ICE connection state: ${peerConnection.value.iceConnectionState}`)
        
        // Handle ICE connection failures
        if (peerConnection.value.iceConnectionState === 'failed') {
          console.log('🔧 ICE connection failed, attempting ICE restart...')
          restartIce()
        } else if (peerConnection.value.iceConnectionState === 'disconnected') {
          console.log('⚠️ ICE connection disconnected, monitoring...')
          // ICE might recover on its own, give it some time
        } else if (peerConnection.value.iceConnectionState === 'connected') {
          console.log('✅ ICE connected - DTLS handshake completed successfully')
        }
      }

      // Handle ICE candidates
      peerConnection.value.onicecandidate = async (event) => {
        if (event.candidate) {
          console.log('🧊 Sending ICE candidate to server')
          try {
            await fetch(`${SERVER_URL}/api/webrtc/ice-candidate`, {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json'
              },
              body: JSON.stringify({
                remote_control_id: remoteControlId.value,
                candidate: {
                  candidate: event.candidate.candidate,
                  sdpMid: event.candidate.sdpMid,
                  sdpMLineIndex: event.candidate.sdpMLineIndex,
                  component: event.candidate.component,
                  foundation: event.candidate.foundation,
                  ip: event.candidate.address || '',
                  port: event.candidate.port || 0,
                  priority: event.candidate.priority || 0,
                  protocol: event.candidate.protocol || 'udp',
                  type: event.candidate.type || 'host'
                }
              })
            })
          } catch (error) {
            console.error('❌ Error sending ICE candidate:', error)
          }
        }
      }

      // Handle incoming data channels
      peerConnection.value.ondatachannel = (event) => {
        const channel = event.channel
        console.log(`📡 Received data channel: ${channel.label}`)

        if (channel.label === 'video') {
          videoDataChannel.value = channel
          setupDataChannelHandlers(channel, 'video')
        } else if (channel.label === 'commands') {
          commandsDataChannel.value = channel
          setupDataChannelHandlers(channel, 'commands')
        }
      }

      // Request offer from server
      console.log('📡 Requesting WebRTC offer from server...')
      const offerResponse = await fetch(`${SERVER_URL}/api/webrtc/offer`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          remote_control_id: remoteControlId.value
        })
      })

      const offerData = await offerResponse.json()

      // Check for error status
      if (offerData.status === 'error') {
        const errorMsg = offerData.message || 'Unknown error from server'
        console.error('❌ Server returned error:', errorMsg)
        return
      }

      if (offerData.status !== 'success') {
        console.error('❌ Failed to get offer from server. Status:', offerData.status, 'Message:', offerData.message)
        return
      }

      // Check if offer exists
      if (!offerData.offer) {
        console.error('❌ No offer received from server. Response:', offerData)
        return
      }

      console.log('📥 Received offer from server')
      console.log('📋 Offer type:', offerData.offer.type)
      console.log('📋 Offer SDP length:', offerData.offer.sdp?.length || 0)

      // Verify the offer has required components
      if (!offerData.offer.sdp || !offerData.offer.type) {
        console.error('❌ Invalid offer format received from server:', offerData.offer)
        return
      }

      // Check for m= sections in the SDP
      const mSections = offerData.offer.sdp.split('\n').filter(line => line.startsWith('m='))
      console.log('📋 Offer has', mSections.length, 'm= sections')

      if (mSections.length === 0) {
        console.error('❌ Offer SDP has no m= sections!')
        console.error('SDP:', offerData.offer.sdp)

        if (peerConnection.value) {
          peerConnection.value.close()
          peerConnection.value = null
        }
        isRTCConnected.value = false
        return
      }

      // Set remote description (offer from server)
      try {
        await peerConnection.value.setRemoteDescription(
          new RTCSessionDescription(offerData.offer)
        )
        console.log('✅ Successfully set remote description')
      } catch (error) {
        console.error('❌ Failed to set remote description:', error)
        console.error('Problematic SDP:', offerData.offer.sdp)

        // Clean up on failure
        if (peerConnection.value) {
          peerConnection.value.close()
          peerConnection.value = null
        }
        isRTCConnected.value = false
        return
      }

      // Create answer
      const answer = await peerConnection.value.createAnswer()
      await peerConnection.value.setLocalDescription(answer)

      console.log('📤 Sending answer to server...')

      // Send answer to server
      const answerResponse = await fetch(`${SERVER_URL}/api/webrtc/answer`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          remote_control_id: remoteControlId.value,
          sdp: {
            type: answer.type,
            sdp: answer.sdp
          }
        })
      })

      const answerData = await answerResponse.json()
      if (answerData.status === 'success') {
        console.log('✅ Answer sent successfully, waiting for connection...')
    }

    } catch (error) {
      console.error('❌ Error establishing WebRTC connection:', error)
      isRTCConnected.value = false

      // Clean up any partially created connection
      if (peerConnection.value) {
        try {
          peerConnection.value.close()
        } catch (closeError) {
          console.error('❌ Error closing peer connection:', closeError)
        }
        peerConnection.value = null
      }

      if (videoDataChannel.value) {
        videoDataChannel.value = null
      }

      if (commandsDataChannel.value) {
        commandsDataChannel.value = null
      }
    }
  }

  function setupDataChannelHandlers(channel, label) {
    channel.onopen = () => {
      console.log(`✅ Data channel '${label}' opened, readyState: ${channel.readyState}`)
      
      // Configure buffering thresholds for better flow control
      if (label === 'video') {
        // Monitor buffer levels to detect network issues
        const checkBuffer = setInterval(() => {
          if (channel.readyState !== 'open') {
            clearInterval(checkBuffer)
            return
          }
          
          const buffered = channel.bufferedAmount || 0
          if (buffered > 4 * 1024 * 1024) {  // 4MB threshold
            console.warn(`⚠️ Video channel buffer high: ${(buffered / 1024 / 1024).toFixed(2)} MB`)
          }
        }, 5000)  // Check every 5 seconds
      }
    }

    channel.onclose = () => {
      console.log(`❌ Data channel '${label}' closed`)
    }

    channel.onerror = (error) => {
      console.error(`❌ Data channel '${label}' error:`, error)
    }

    channel.onbufferedamountlow = () => {
      console.debug(`📉 Data channel '${label}' buffer cleared`)
    }

    channel.onmessage = (event) => {
      try {
        // Handle binary data (video frames)
        if (event.data instanceof ArrayBuffer) {
          const byteArray = new Uint8Array(event.data)

          // Check if this is a keepalive message
          if (byteArray.length === 5 && 
              byteArray[0] === 0 && 
              String.fromCharCode(byteArray[1], byteArray[2], byteArray[3], byteArray[4]) === 'PING') {
            console.debug('💓 Received keepalive ping')
            // Send pong response
            if (label === 'video' && channel.readyState === 'open') {
              const pong = new Uint8Array([0, 80, 79, 78, 71])  // '\x00PONG'
              channel.send(pong)
              console.debug('💓 Sent keepalive pong')
            }
            return
          }

          messageHandler(byteArray[0], byteArray)
        } else if (event.data instanceof Blob) {
          // Convert Blob to ArrayBuffer
          event.data.arrayBuffer().then(buffer => {
            const byteArray = new Uint8Array(buffer)
            messageHandler(byteArray[0], byteArray)
          })
        } else {
          console.warn(`⚠️ Unexpected data type on channel '${label}':`, typeof event.data)
        }
      } catch (error) {
        console.error(`❌ Error processing message on channel '${label}':`, error)
      }
    }
  }

  async function attemptReconnect() {
    // Clear any existing reconnect timeout
    if (reconnectTimeout.value) {
      clearTimeout(reconnectTimeout.value)
    }

    if (reconnectAttempts.value >= maxReconnectAttempts.value) {
      console.error(`❌ Max reconnection attempts (${maxReconnectAttempts.value}) reached`)
      return
    }

    reconnectAttempts.value++
    const delay = Math.min(1000 * Math.pow(2, reconnectAttempts.value - 1), 10000)  // Exponential backoff, max 10s
    
    console.log(`🔄 Reconnection attempt ${reconnectAttempts.value}/${maxReconnectAttempts.value} in ${delay}ms...`)
    
    reconnectTimeout.value = setTimeout(async () => {
      try {
        await disconnect()
        await connect()
      } catch (error) {
        console.error('❌ Reconnection failed:', error)
      }
    }, delay)
  }

  async function restartIce() {
    if (!peerConnection.value) {
      console.warn('⚠️ Cannot restart ICE: no peer connection')
      return
    }

    try {
      console.log('🔄 Restarting ICE...')
      
      // Create a new offer with ICE restart
      const offer = await peerConnection.value.createOffer({ iceRestart: true })
      await peerConnection.value.setLocalDescription(offer)
      
      // Send the new offer to the server
      const response = await fetch(`${SERVER_URL}/api/webrtc/ice-restart`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          remote_control_id: remoteControlId.value,
          offer: {
            type: offer.type,
            sdp: offer.sdp
          }
        })
      })
      
      if (response.ok) {
        const data = await response.json()
        if (data.answer) {
          await peerConnection.value.setRemoteDescription(new RTCSessionDescription(data.answer))
          console.log('✅ ICE restart successful')
        }
      }
    } catch (error) {
      console.error('❌ ICE restart failed:', error)
    }
  }

  async function disconnect() {
    console.log('🔄 Disconnecting WebRTC...')

    // Clear reconnect timeout
    if (reconnectTimeout.value) {
      clearTimeout(reconnectTimeout.value)
      reconnectTimeout.value = null
    }

    // Close data channels
    if (videoDataChannel.value) {
      videoDataChannel.value.close()
      videoDataChannel.value = null
    }

    if (commandsDataChannel.value) {
      commandsDataChannel.value.close()
      commandsDataChannel.value = null
    }

    // Close peer connection
    if (peerConnection.value) {
      peerConnection.value.close()
      peerConnection.value = null
    }

    isRTCConnected.value = false
    reconnectAttempts.value = 0
    console.log('✅ WebRTC disconnected')
  }

  async function sendCommand(message) {
    if (!commandsDataChannel.value || commandsDataChannel.value.readyState !== 'open') {
      console.warn('⚠️ Commands data channel not open')
      return false
    }

    try {
      let data
      if (typeof message === 'string') {
        data = new TextEncoder().encode(message)
      } else if (message instanceof Uint8Array) {
        data = message
      } else {
        console.error('❌ Unsupported message type for WebRTC command:', typeof message)
        return false
      }

      commandsDataChannel.value.send(data)
      return true
    } catch (error) {
      console.error('❌ Error sending command via WebRTC:', error)
      return false
    }
  }

  return {
    isRTCConnected,
    connectWebRTC: connect,
    disconnectWebRTC: disconnect,
    sendRTCCommand: sendCommand
  }
}
