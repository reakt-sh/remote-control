# WebRTC Integration Guide

## Overview

WebRTC has been successfully integrated into the Remote Control system as an additional transport protocol alongside WebTransport and WebSocket. This provides improved real-time communication capabilities with NAT traversal support.

## Architecture

### Data Flow
1. **Train → Central Server (unchanged)**: Trains continue to send video data over QUIC to the central server
2. **Central Server → Web Client (new)**: The central server now relays video data to web clients via WebRTC data channels in addition to WebTransport
3. **Web Client**: Receives and assembles video data using the same assembler logic regardless of transport protocol

### Components

#### Central Server (Python)

1. **WebRTC Manager** (`managers/webrtc_manager.py`)
   - Manages WebRTC peer connections for each remote control client
   - Creates and manages data channels for video and command transmission
   - Handles ICE candidate exchange and connection lifecycle
   - Server acts as the offerer, creating data channels proactively

2. **Remote Control Manager** (`managers/remote_control_manager.py`)
   - Enhanced to integrate WebRTC support
   - Creates WebRTC peer connection when a new remote control connects
   - Provides methods to relay video data via WebRTC

3. **Server Controller** (`server_controller.py`)
   - Routes video data from trains to remote controls via both WebSocket and WebRTC
   - Provides WebRTC signaling endpoints integration

4. **API Endpoints** (`endpoints/remote_control_gateway.py`)
   - `POST /api/webrtc/offer`: Returns WebRTC offer for a remote control client
   - `POST /api/webrtc/answer`: Receives and processes the answer from the client
   - `POST /api/webrtc/ice-candidate`: Receives ICE candidates from the client

#### Web Client (JavaScript/Vue)

1. **WebRTC Service** (`scripts/webrtc.js`)
   - Establishes WebRTC peer connection with the server
   - Handles signaling (offer/answer/ICE candidate exchange)
   - Manages data channels for receiving video and commands
   - Uses same message handler interface as WebTransport

2. **Train Store** (`stores/trainStore.js`)
   - Integrates WebRTC connection alongside existing WebSocket, WebTransport, and MQTT
   - Reuses the same video assembler for all transport protocols
   - Handles messages from WebRTC using the same packet format

## Installation

### Central Server

1. Install dependencies:
```bash
cd central-server
pip install -r requirements.txt
```

The new dependencies include:
- `aiortc`: Python implementation of WebRTC
- `aioice`: ICE protocol support

### Web Client

No additional dependencies needed - WebRTC is natively supported by modern browsers.

## Usage

### Connection Flow

1. Web client connects to the server:
   ```javascript
   await connectToServer()  // Establishes WebSocket, WebTransport, WebRTC, and MQTT
   ```

2. WebRTC connection is established:
   - Client calls server's `/api/webrtc/offer` endpoint
   - Server creates peer connection and data channels, returns SDP offer
   - Client sets remote description and creates answer
   - Client sends answer to `/api/webrtc/answer`
   - ICE candidates are exchanged via `/api/webrtc/ice-candidate`

3. Once connected, video data flows:
   - Train sends video → QUIC → Central Server
   - Central Server relays video → WebRTC data channel → Web Client
   - Web Client assembles video frames using the same assembler

### Data Channels

The server creates two data channels:

1. **video**: For transmitting video frame packets
   - Unordered delivery for minimal latency
   - Binary data transmission

2. **commands**: For control commands (future use)
   - Can be used for bidirectional control signaling

## Configuration

### STUN Servers

The WebRTC client is configured with Google's public STUN servers:
```javascript
const rtcConfig = {
  iceServers: [
    { urls: 'stun:stun.l.google.com:19302' },
    { urls: 'stun:stun1.l.google.com:19302' }
  ]
}
```

For production deployments, consider:
- Using your own STUN servers
- Adding TURN servers for better NAT traversal

### Data Channel Configuration

Current settings optimize for low-latency video streaming:
- `ordered: false` - Packets can arrive out of order
- `maxRetransmits: 0` - No retransmissions for lost packets

These can be adjusted in `webrtc_manager.py`:
```python
channel = pc.createDataChannel(channel_name, ordered=False, maxRetransmits=0)
```

## Packet Format

WebRTC uses the same packet format as WebTransport and WebSocket:

```
[Packet Type (1 byte)][Payload (variable length)]
```

Packet types are defined in `globals.py` (server) and `trainStore.js` (client):
- `13`: Video data
- `16`: Command
- `17`: Telemetry
- `20`: Keepalive
- etc.

## Monitoring and Debugging

### Connection States

Monitor WebRTC connection state in browser console:
- `checking`: ICE connectivity checks in progress
- `connected`: Peer connection established
- `disconnected`: Connection lost
- `failed`: Connection failed

### Data Channel States

Monitor data channel states:
- `connecting`: Channel is being established
- `open`: Channel is ready for data transmission
- `closing`: Channel is being closed
- `closed`: Channel is closed

### Logs

Server logs show WebRTC activity:
```
WebRTC: Created peer connection for <remote_control_id>
WebRTC: Created data channel 'video' for <remote_control_id>
WebRTC: Connection state for <remote_control_id>: connected
```

## Benefits of WebRTC Integration

1. **NAT Traversal**: Built-in ICE support for peer-to-peer connections through NATs
2. **Low Latency**: Optimized for real-time communication
3. **Browser Native**: No special plugins or extensions required
4. **Fallback Option**: Provides redundancy alongside WebTransport
5. **Industry Standard**: Well-documented and widely supported protocol

## Future Enhancements

Potential improvements:
1. Add TURN server support for better NAT traversal
2. Implement bidirectional communication via command channel
3. Add connection quality metrics and statistics
4. Implement automatic protocol selection based on network conditions
5. Add support for multiple video streams

## Troubleshooting

### Connection fails
- Check firewall settings
- Verify STUN servers are reachable
- Check browser console for errors
- Verify server logs for connection attempts

### Video not displaying
- Check data channel state in console
- Verify packet types are being received
- Check assembler is processing packets
- Verify video decoder is initialized

### High latency
- Check ICE connection state
- Consider adjusting data channel configuration
- Monitor network conditions
- Check if TURN server is needed

## Testing

To test WebRTC integration:

1. Start the central server
2. Start a train client
3. Open web client in browser
4. Open browser DevTools console
5. Look for WebRTC connection logs
6. Verify video stream is received via WebRTC data channel

Expected console output:
```
🔄 Initializing WebRTC connection...
📡 Requesting WebRTC offer from server...
📥 Received offer from server
📤 Sending answer to server...
✅ Answer sent successfully, waiting for connection...
🧊 ICE connection state: checking
🧊 ICE connection state: connected
🔄 WebRTC Connection state: connected
✅ WebRTC peer connection established
📡 Received data channel: video
✅ Data channel 'video' opened
```
