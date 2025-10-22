/**
 * WebRTC Client for Train Video Streaming
 * 
 * Handles WebRTC peer connection establishment and video data reception
 * via data channels for the train remote control system.
 */

export class WebRTCClient {
  constructor(trainId, options = {}) {
    this.trainId = trainId
    this.onVideoPacket = options.onVideoPacket || (() => {})
    this.onConnectionStateChange = options.onConnectionStateChange || (() => {})
    this.onError = options.onError || (() => {})
    
    // WebRTC components
    this.pc = null
    this.dataChannel = null
    this.signalingWs = null
    
    // Configuration
    this.iceServers = options.iceServers || [
      { urls: 'stun:stun.l.google.com:19302' },
      { urls: 'stun:stun1.l.google.com:19302' },
      { urls: 'stun:stun2.l.google.com:19302' }
    ]
    
    // State
    this.isConnected = false
    this.reconnectAttempts = 0
    this.maxReconnectAttempts = 5
    
    // Statistics
    this.stats = {
      packetsReceived: 0,
      bytesReceived: 0,
      framesReceived: 0,
      lastPacketTime: null
    }
    
    console.log(`WebRTC client initialized for train ${trainId}`)
  }
  
  /**
   * Connect to signaling server and establish WebRTC connection
   */
  async connect() {
    try {
      console.log(`Connecting to WebRTC signaling for train ${this.trainId}`)
      
      // Construct signaling URL
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
      const signalingUrl = `${protocol}//${window.location.host}/webrtc/web/${this.trainId}`
      
      // Connect to signaling server
      this.signalingWs = new WebSocket(signalingUrl)
      
      this.signalingWs.onopen = () => {
        console.log('Connected to WebRTC signaling server')
      }
      
      this.signalingWs.onmessage = async (event) => {
        await this.handleSignalingMessage(JSON.parse(event.data))
      }
      
      this.signalingWs.onerror = (error) => {
        console.error('Signaling WebSocket error:', error)
        this.onError(error)
      }
      
      this.signalingWs.onclose = () => {
        console.log('Signaling WebSocket closed')
        this.handleDisconnect()
      }
      
    } catch (error) {
      console.error('Error connecting to WebRTC:', error)
      this.onError(error)
      throw error
    }
  }
  
  /**
   * Create RTCPeerConnection
   */
  createPeerConnection() {
    const config = {
      iceServers: this.iceServers
    }
    
    this.pc = new RTCPeerConnection(config)
    
    // Connection state monitoring
    this.pc.onconnectionstatechange = () => {
      console.log(`WebRTC connection state: ${this.pc.connectionState}`)
      this.onConnectionStateChange(this.pc.connectionState)
      
      if (this.pc.connectionState === 'connected') {
        this.isConnected = true
        this.reconnectAttempts = 0
      } else if (this.pc.connectionState === 'failed' || this.pc.connectionState === 'closed') {
        this.isConnected = false
        this.handleDisconnect()
      }
    }
    
    // ICE connection state
    this.pc.oniceconnectionstatechange = () => {
      console.log(`ICE connection state: ${this.pc.iceConnectionState}`)
    }
    
    // ICE gathering state
    this.pc.onicegatheringstatechange = () => {
      console.log(`ICE gathering state: ${this.pc.iceGatheringState}`)
    }
    
    // ICE candidate handling
    this.pc.onicecandidate = (event) => {
      if (event.candidate) {
        console.log('Sending ICE candidate to train')
        this.sendSignalingMessage({
          type: 'ice',
          candidate: event.candidate.candidate,
          sdpMid: event.candidate.sdpMid,
          sdpMLineIndex: event.candidate.sdpMLineIndex
        })
      }
    }
    
    // Data channel handling
    this.pc.ondatachannel = (event) => {
      console.log(`Data channel received: ${event.channel.label}`)
      this.setupDataChannel(event.channel)
    }
    
    console.log('RTCPeerConnection created')
  }
  
  /**
   * Set up data channel event handlers
   */
  setupDataChannel(channel) {
    this.dataChannel = channel
    
    this.dataChannel.onopen = () => {
      console.log(`Data channel '${channel.label}' opened`)
      this.isConnected = true
    }
    
    this.dataChannel.onclose = () => {
      console.log(`Data channel '${channel.label}' closed`)
      this.isConnected = false
    }
    
    this.dataChannel.onerror = (error) => {
      console.error('Data channel error:', error)
      this.onError(error)
    }
    
    this.dataChannel.onmessage = (event) => {
      this.handleDataChannelMessage(event.data)
    }
  }
  
  /**
   * Handle incoming signaling messages
   */
  async handleSignalingMessage(message) {
    const { type } = message
    
    try {
      if (type === 'ready') {
        console.log('Train is ready for WebRTC connection')
        
      } else if (type === 'offer') {
        console.log('Received offer from train')
        
        // Create peer connection if not exists
        if (!this.pc) {
          this.createPeerConnection()
        }
        
        // Set remote description
        await this.pc.setRemoteDescription(new RTCSessionDescription({
          type: 'offer',
          sdp: message.sdp
        }))
        
        // Create and send answer
        const answer = await this.pc.createAnswer()
        await this.pc.setLocalDescription(answer)
        
        this.sendSignalingMessage({
          type: 'answer',
          sdp: this.pc.localDescription.sdp
        })
        
        console.log('Answer sent to train')
        
      } else if (type === 'ice') {
        console.log('Received ICE candidate from train')
        
        if (this.pc) {
          await this.pc.addIceCandidate(new RTCIceCandidate({
            candidate: message.candidate,
            sdpMid: message.sdpMid,
            sdpMLineIndex: message.sdpMLineIndex
          }))
        }
        
      } else if (type === 'error') {
        console.error('Signaling error:', message.message)
        this.onError(new Error(message.message))
      }
      
    } catch (error) {
      console.error('Error handling signaling message:', error)
      this.onError(error)
    }
  }
  
  /**
   * Handle incoming data channel messages
   */
  handleDataChannelMessage(data) {
    try {
      // Update statistics
      this.stats.packetsReceived++
      this.stats.lastPacketTime = Date.now()
      
      if (data instanceof ArrayBuffer) {
        const bytes = new Uint8Array(data)
        this.stats.bytesReceived += bytes.length
        
        // Check packet type (first byte)
        const packetType = bytes[0]
        
        if (packetType === 13) { // Video packet
          this.onVideoPacket(bytes)
        } else if (packetType === 20) { // Keepalive
          console.debug('Received keepalive packet')
        } else if (packetType === 17) { // Telemetry
          console.debug('Received telemetry packet')
        }
        
      } else if (typeof data === 'string') {
        // Handle JSON messages
        const message = JSON.parse(data)
        console.log('Received message:', message)
      }
      
    } catch (error) {
      console.error('Error handling data channel message:', error)
    }
  }
  
  /**
   * Send signaling message to train via WebSocket
   */
  sendSignalingMessage(message) {
    if (this.signalingWs && this.signalingWs.readyState === WebSocket.OPEN) {
      this.signalingWs.send(JSON.stringify(message))
    } else {
      console.warn('Signaling WebSocket not ready')
    }
  }
  
  /**
   * Send message via data channel
   */
  sendDataChannelMessage(data) {
    if (this.dataChannel && this.dataChannel.readyState === 'open') {
      this.dataChannel.send(data)
      return true
    } else {
      console.warn('Data channel not ready')
      return false
    }
  }
  
  /**
   * Handle disconnection and attempt reconnection
   */
  handleDisconnect() {
    console.log('WebRTC connection lost')
    
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++
      console.log(`Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts})`)
      
      setTimeout(() => {
        this.connect().catch(error => {
          console.error('Reconnection failed:', error)
        })
      }, 2000 * this.reconnectAttempts) // Exponential backoff
    }
  }
  
  /**
   * Get connection statistics
   */
  async getStats() {
    if (!this.pc) {
      return this.stats
    }
    
    try {
      const rtcStats = await this.pc.getStats()
      const enhancedStats = { ...this.stats }
      
      rtcStats.forEach(report => {
        if (report.type === 'data-channel') {
          enhancedStats.dataChannelState = report.state
          enhancedStats.messagesReceived = report.messagesReceived
          enhancedStats.messagesSent = report.messagesSent
          enhancedStats.bytesReceived = report.bytesReceived
          enhancedStats.bytesSent = report.bytesSent
        }
      })
      
      return enhancedStats
    } catch (error) {
      console.error('Error getting stats:', error)
      return this.stats
    }
  }
  
  /**
   * Close the WebRTC connection
   */
  close() {
    console.log('Closing WebRTC connection')
    
    if (this.dataChannel) {
      this.dataChannel.close()
      this.dataChannel = null
    }
    
    if (this.pc) {
      this.pc.close()
      this.pc = null
    }
    
    if (this.signalingWs) {
      this.signalingWs.close()
      this.signalingWs = null
    }
    
    this.isConnected = false
  }
}

// Export for use in other modules
export default WebRTCClient
