# Quick Start Guide: Using WebRTC for Video Streaming

## Step 1: Install Dependencies

### Train Client
```bash
cd train-client
pip install -r requirements-webrtc.txt
```

### Central Server
No additional dependencies needed - uses existing FastAPI/WebSocket infrastructure.

### Web Client  
No additional dependencies - uses browser's native WebRTC API.

## Step 2: Register WebRTC Endpoint (Central Server)

Add to `central-server/src/main.py`:

```python
from endpoints.webrtc_signaling import router as webrtc_router

# Add to your FastAPI app
app.include_router(webrtc_router)
```

## Step 3: Import WebRTC Client (Web Client)

In your Vue component or main application:

```javascript
import WebRTCClient from '@/scripts/webrtc.js'
import { useAssembler } from '@/scripts/assembler.js'

// Initialize assembler (same as QUIC/WebSocket)
const assembler = new useAssembler({
  maxFrames: 30,
  onFrameComplete: (frameData) => {
    // Decode and display video
    videoDecoder.enqueueFrame(frameData)
  }
})

// Create WebRTC client
const webrtcClient = new WebRTCClient(trainId, {
  onVideoPacket: (packet) => {
    // Process packet through same assembler
    assembler.processPacket(packet)
  },
  onConnectionStateChange: (state) => {
    console.log(`Connection: ${state}`)
  }
})

// Connect
await webrtcClient.connect()
```

## Step 4: Switch Protocol from Web Client

Send command to train to switch protocol:

```javascript
function switchToWebRTC() {
  const command = {
    instruction: 'SWITCH_PROTOCOL',
    protocol: 'WEBRTC'  // or 'QUIC' or 'WEBSOCKET'
  }
  
  // Send via existing command channel
  sendCommand(trainId, command)
}
```

## Step 5: Monitor Connection

```javascript
// Check connection status
console.log('Connected:', webrtcClient.isConnected)

// Get statistics
const stats = await webrtcClient.getStats()
console.log('Statistics:', stats)

// Monitor events
webrtcClient.onConnectionStateChange = (state) => {
  if (state === 'connected') {
    console.log('✅ WebRTC connected!')
  } else if (state === 'failed') {
    console.log('❌ WebRTC connection failed')
  }
}
```

## Example: Complete Integration

```javascript
// Example Vue component integration
export default {
  data() {
    return {
      trainId: 'your-train-id',
      currentProtocol: 'QUIC',
      webrtcClient: null,
      assembler: null
    }
  },
  
  mounted() {
    this.initializeVideoReceiver()
  },
  
  methods: {
    initializeVideoReceiver() {
      // Initialize assembler
      this.assembler = new useAssembler({
        onFrameComplete: (frameData) => {
          this.videoDecoder.enqueueFrame(frameData)
        }
      })
      
      // Initialize WebRTC client
      this.webrtcClient = new WebRTCClient(this.trainId, {
        onVideoPacket: (packet) => {
          this.assembler.processPacket(packet)
        },
        onConnectionStateChange: this.handleConnectionChange
      })
    },
    
    async switchToWebRTC() {
      // Connect WebRTC
      await this.webrtcClient.connect()
      
      // Tell train to switch
      this.sendCommand({
        instruction: 'SWITCH_PROTOCOL',
        protocol: 'WEBRTC'
      })
      
      this.currentProtocol = 'WEBRTC'
    },
    
    handleConnectionChange(state) {
      this.$emit('connection-state', state)
    }
  },
  
  beforeUnmount() {
    if (this.webrtcClient) {
      this.webrtcClient.close()
    }
  }
}
```

## Protocol Switching UI Example

```vue
<template>
  <div class="protocol-selector">
    <h3>Video Protocol</h3>
    <button 
      @click="switchProtocol('WEBSOCKET')"
      :class="{ active: currentProtocol === 'WEBSOCKET' }">
      WebSocket
    </button>
    <button 
      @click="switchProtocol('QUIC')"
      :class="{ active: currentProtocol === 'QUIC' }">
      QUIC
    </button>
    <button 
      @click="switchProtocol('WEBRTC')"
      :class="{ active: currentProtocol === 'WEBRTC' }">
      WebRTC
    </button>
    
    <div class="status">
      Status: {{ connectionStatus }}
    </div>
  </div>
</template>

<script>
export default {
  data() {
    return {
      currentProtocol: 'QUIC',
      connectionStatus: 'disconnected'
    }
  },
  
  methods: {
    async switchProtocol(protocol) {
      if (protocol === this.currentProtocol) return
      
      // Send command to train
      await this.sendCommand({
        instruction: 'SWITCH_PROTOCOL',
        protocol: protocol
      })
      
      // Update local state
      this.currentProtocol = protocol
      
      // Initialize appropriate client if needed
      if (protocol === 'WEBRTC') {
        await this.initWebRTC()
      }
    },
    
    async initWebRTC() {
      if (!this.webrtcClient) {
        this.webrtcClient = new WebRTCClient(this.trainId, {
          onVideoPacket: (packet) => {
            this.assembler.processPacket(packet)
          },
          onConnectionStateChange: (state) => {
            this.connectionStatus = state
          }
        })
      }
      
      await this.webrtcClient.connect()
    }
  }
}
</script>

<style scoped>
.protocol-selector button.active {
  background-color: #4CAF50;
  color: white;
}
</style>
```

## Testing

1. **Start Central Server**:
   ```bash
   cd central-server
   python src/main.py
   ```

2. **Start Train Client**:
   ```bash
   cd train-client
   python src/main.py
   ```

3. **Open Web Client**:
   ```
   http://localhost:8080
   ```

4. **Switch to WebRTC**:
   - Click "WebRTC" button in protocol selector
   - Monitor browser console for connection status
   - Video should stream via WebRTC data channel

## Debugging

### Check Signaling Connection
```javascript
console.log('Signaling:', webrtcClient.signalingWs.readyState)
// 1 = OPEN, 0 = CONNECTING, 2 = CLOSING, 3 = CLOSED
```

### Check Peer Connection
```javascript
console.log('Peer connection:', webrtcClient.pc.connectionState)
// "new", "connecting", "connected", "disconnected", "failed", "closed"
```

### Check Data Channel
```javascript
console.log('Data channel:', webrtcClient.dataChannel?.readyState)
// "connecting", "open", "closing", "closed"
```

### View Statistics
```javascript
const stats = await webrtcClient.getStats()
console.table(stats)
```

## Common Issues

### "No ICE candidates"
- Check firewall settings
- Verify STUN server accessibility
- May need TURN server for strict NAT

### "Connection timeout"
- Verify signaling WebSocket is connected
- Check train client is running
- Monitor signaling messages in browser console

### "Data channel not opening"
- Ensure both peers have compatible configurations
- Check for errors in peer connection setup
- Verify SDP offer/answer exchange completed

## Next Steps

- Add bandwidth monitoring
- Implement adaptive quality switching
- Add connection quality indicators
- Implement automatic protocol fallback
