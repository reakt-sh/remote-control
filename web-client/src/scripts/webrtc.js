import { ref } from 'vue'
import { SERVER_URL } from '@/scripts/config'

export function useWebRTC(remoteControlId, messageHandler) {
  const isRTCConnected = ref(false)
  const peerConnection = ref(null)
  const videoDataChannel = ref(null)
  const commandsDataChannel = ref(null)

  // Configuration for the RTCPeerConnection
  const rtcConfig = {
    iceServers: [
      { urls: 'stun:stun.l.google.com:19302' },
      { urls: 'stun:stun1.l.google.com:19302' }
    ],
    iceCandidatePoolSize: 10
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
          console.log('✅ WebRTC peer connection established')
        } else if (peerConnection.value.connectionState === 'disconnected' || 
                   peerConnection.value.connectionState === 'failed' || 
                   peerConnection.value.connectionState === 'closed') {
          isRTCConnected.value = false
          console.log('❌ WebRTC peer connection lost')
        }
      }

      peerConnection.value.oniceconnectionstatechange = () => {
        console.log(`🧊 ICE connection state: ${peerConnection.value.iceConnectionState}`)
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
      if (offerData.status !== 'success') {
        throw new Error('Failed to get offer from server')
      }

      console.log('📥 Received offer from server')
      console.log('📋 Offer type:', offerData.offer.type)
      console.log('📋 Offer SDP length:', offerData.offer.sdp?.length || 0)
      
      // Verify the offer has required components
      if (!offerData.offer.sdp || !offerData.offer.type) {
        throw new Error('Invalid offer received: missing sdp or type')
      }

      // Check for m= sections in the SDP
      const mSections = offerData.offer.sdp.split('\n').filter(line => line.startsWith('m='))
      console.log('📋 Offer has', mSections.length, 'm= sections')
      
      if (mSections.length === 0) {
        console.error('❌ Offer SDP has no m= sections!')
        console.error('SDP:', offerData.offer.sdp)
        throw new Error('Invalid offer: no media sections')
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
        throw error
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
      throw error
    }
  }

  function setupDataChannelHandlers(channel, label) {
    channel.onopen = () => {
      console.log(`✅ Data channel '${label}' opened, readyState: ${channel.readyState}`)
    }

    channel.onclose = () => {
      console.log(`❌ Data channel '${label}' closed`)
    }

    channel.onerror = (error) => {
      console.error(`❌ Data channel '${label}' error:`, error)
    }

    channel.onmessage = (event) => {
      try {
        // Handle binary data (video frames)
        if (event.data instanceof ArrayBuffer) {
          const byteArray = new Uint8Array(event.data)
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

  async function disconnect() {
    console.log('🔄 Disconnecting WebRTC...')

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
        throw new Error('Unsupported message type')
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
