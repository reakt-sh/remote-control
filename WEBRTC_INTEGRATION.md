# WebRTC Integration for Train Remote Control System

This document describes the WebRTC implementation for video streaming in the train remote control project.

## Overview

WebRTC (Web Real-Time Communication) has been integrated as an additional protocol option alongside QUIC and WebSocket for video transmission. WebRTC provides low-latency peer-to-peer communication with built-in NAT traversal capabilities.

## Architecture

### Components

1. **Train Client** (`train-client/src/network_worker_webrtc.py`)
   - Manages WebRTC peer connection
   - Sends video data via unreliable data channels
   - Handles signaling via WebSocket

2. **Central Server** (`central-server/src/endpoints/webrtc_signaling.py`)
   - WebRTC signaling server
   - Coordinates connection establishment between train and web clients
   - Forwards SDP offers/answers and ICE candidates

3. **Web Client** (`web-client/src/scripts/webrtc.js`)
   - Receives video packets via WebRTC data channels
   - Handles peer connection management
   - Processes incoming video frames

## Installation

### Train Client

Install WebRTC dependencies:

```bash
cd train-client
pip install -r requirements-webrtc.txt
```

Required packages:
- `aiortc>=1.5.0` - Python WebRTC implementation
- `av>=10.0.0` - Video/audio processing
- `pylibsrtp>=0.8.0` - SRTP support

### Central Server

The signaling endpoint needs to be registered in the main FastAPI application:

```python
# In central-server/src/main.py
from endpoints.webrtc_signaling import router as webrtc_router

app.include_router(webrtc_router)
```

### Web Client

Import the WebRTC client in your application:

```javascript
import WebRTCClient from './scripts/webrtc.js'
```

## Usage

### Switching Protocols

Users can switch between protocols dynamically by sending a command:

```javascript
// From web client
sendCommand({
  instruction: 'SWITCH_PROTOCOL',
  protocol: 'WEBRTC'  // or 'QUIC' or 'WEBSOCKET'
})
```

### Train Client Configuration

In `base_client.py`, the protocol is configured via:

```python
self.protocol_for_media = "WEBRTC"  # Options: "WEBSOCKET", "QUIC", "WEBRTC"
```

### Web Client Integration

```javascript
// Create WebRTC client
const webrtcClient = new WebRTCClient(trainId, {
  onVideoPacket: (packet) => {
    // Process video packet (same format as QUIC/WebSocket)
    assembler.processPacket(packet)
  },
  onConnectionStateChange: (state) => {
    console.log('WebRTC state:', state)
  },
  onError: (error) => {
    console.error('WebRTC error:', error)
  }
})

// Connect
await webrtcClient.connect()

// Get statistics
const stats = await webrtcClient.getStats()
console.log('Packets received:', stats.packetsReceived)

// Close connection
webrtcClient.close()
```

## Packet Format

WebRTC uses the **same packet format** as QUIC and WebSocket for compatibility:

```
Header (53 bytes):
- [0]      : Packet type (1 byte) = 13 for video
- [1:5]    : Frame ID (4 bytes, big-endian)
- [5:7]    : Number of packets (2 bytes, big-endian)
- [7:9]    : Packet ID (2 bytes, big-endian)
- [9:45]   : Train client ID (36 bytes, UTF-8 padded)
- [45:53]  : Timestamp (8 bytes, big-endian)
- [53:]    : Payload (video data chunk)
```

Maximum packet size: 1000 bytes (including header)

## WebRTC Configuration

### ICE Servers

Default STUN servers (configured in `globals.py`):
- `stun:stun.l.google.com:19302`
- `stun:stun1.l.google.com:19302`
- `stun:stun2.l.google.com:19302`

### Data Channel Settings

Video data channel:
- **Ordered**: False (allows out-of-order delivery)
- **Max Retransmits**: 0 (no retransmissions for real-time)
- **Reliability**: Unreliable (similar to UDP/QUIC datagram)

## Signaling Flow

1. **Train Client**:
   - Connects to signaling server via WebSocket
   - Creates peer connection and data channel
   - Generates and sends SDP offer

2. **Signaling Server**:
   - Receives offer from train
   - Forwards offer to connected web clients

3. **Web Client**:
   - Receives offer
   - Creates peer connection
   - Generates and sends SDP answer

4. **ICE Negotiation**:
   - Both peers exchange ICE candidates
   - Server forwards candidates between peers

5. **Connection Established**:
   - Data channel opens
   - Video packets start flowing

## API Endpoints

### WebRTC Signaling Endpoints

#### Train Client Signaling
```
WebSocket: /webrtc/train/{train_client_id}
```

Messages:
- `{"type": "offer", "sdp": "..."}`
- `{"type": "ice", "candidate": "...", "sdpMid": "...", "sdpMLineIndex": 0}`

#### Web Client Signaling
```
WebSocket: /webrtc/web/{train_client_id}
```

Messages:
- `{"type": "answer", "sdp": "..."}`
- `{"type": "ice", "candidate": "...", "sdpMid": "...", "sdpMLineIndex": 0}`

#### Status Endpoint
```
GET /webrtc/status/{train_client_id}
```

Response:
```json
{
  "trainClientId": "uuid",
  "trainConnected": true,
  "webClientsConnected": 2,
  "status": "active"
}
```

## Advantages of WebRTC

1. **Low Latency**: Direct peer-to-peer communication when possible
2. **NAT Traversal**: Built-in STUN/TURN support for firewall traversal
3. **Browser Native**: No browser plugins required
4. **Adaptive**: Built-in congestion control and bandwidth estimation
5. **Secure**: Mandatory encryption (DTLS/SRTP)

## Comparison with Other Protocols

| Feature | WebRTC | QUIC | WebSocket |
|---------|--------|------|-----------|
| Latency | Very Low | Low | Medium |
| NAT Traversal | Excellent | Good | Poor |
| Setup Complexity | High | Medium | Low |
| Browser Support | Native | Limited | Excellent |
| Reliability | Configurable | Configurable | Reliable |
| Ordering | Configurable | In-order | In-order |

## Troubleshooting

### Connection Issues

1. **Check ICE connectivity**:
   ```javascript
   console.log('ICE state:', webrtcClient.pc.iceConnectionState)
   ```

2. **Verify signaling**:
   - Check WebSocket connection to signaling server
   - Monitor browser console for signaling messages

3. **Firewall/NAT**:
   - Ensure STUN servers are reachable
   - Configure TURN server if needed for strict NAT

### Performance Issues

1. **Monitor data channel**:
   ```javascript
   const stats = await webrtcClient.getStats()
   console.log('Bytes received:', stats.bytesReceived)
   ```

2. **Check packet loss**:
   - Enable debug logging in `network_worker_webrtc.py`
   - Monitor frame completion rates

### Debug Logging

Enable detailed logging:

**Train Client**:
```python
logger.setLevel("DEBUG")
```

**Web Client**:
```javascript
// Browser console shows all WebRTC events
```

## Future Enhancements

1. **TURN Server Integration**: Add TURN server for better NAT traversal
2. **Media Tracks**: Use native video tracks instead of data channels
3. **Simulcast**: Multiple quality streams for adaptive bitrate
4. **Recording**: Server-side recording of WebRTC streams
5. **Screen Sharing**: Additional track for train operator screen

## References

- [WebRTC API (MDN)](https://developer.mozilla.org/en-US/docs/Web/API/WebRTC_API)
- [aiortc Documentation](https://aiortc.readthedocs.io/)
- [RFC 8831 - WebRTC Data Channels](https://datatracker.ietf.org/doc/html/rfc8831)

## Support

For issues or questions about WebRTC integration:
1. Check logs for error messages
2. Verify all dependencies are installed
3. Test with simple STUN connectivity first
4. Monitor network conditions and bandwidth

## License

Same as the main project license.
