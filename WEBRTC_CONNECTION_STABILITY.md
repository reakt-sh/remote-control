# WebRTC Connection Stability Improvements

## Problem
WebRTC peer connections were disconnecting automatically after some time, showing:
- ICE connection state: disconnected
- WebRTC Connection state: disconnected
- Connection loss despite good network conditions

## Root Causes Identified
1. **No Keepalive Mechanism**: WebRTC connections can timeout without activity
2. **Buffer Overflow**: Data channel buffer filling up causes disconnection
3. **ICE Connection Failures**: No recovery mechanism for temporary network issues
4. **No Reconnection Logic**: Manual reconnection required after disconnection

## Solutions Implemented

### 1. Server-Side Keepalive (Python)
**File**: `central-server/src/managers/webrtc_manager.py`

- Added periodic keepalive pings every 5 seconds through the commands data channel
- Sends `\x00PING` message to keep the connection alive
- Tracks last activity time for each connection
- Automatic cleanup when connection closes

```python
# Keepalive task runs in background
async def keepalive_loop():
    while connection_active:
        await asyncio.sleep(5)
        channel.send(b'\x00PING')
```

### 2. Buffer Overflow Prevention (Python)
**File**: `central-server/src/managers/webrtc_manager.py`

- Monitor `bufferedAmount` before sending video data
- Drop frames when buffer exceeds 4MB threshold
- Prevents buffer overflow that causes disconnection
- Maintains low latency by prioritizing latest frames

```python
if channel.bufferedAmount > 4 * 1024 * 1024:
    logger.warning("Buffer full, dropping frame")
    return
```

### 3. Client-Side Reconnection (JavaScript)
**File**: `web-client/src/scripts/webrtc.js`

- Automatic reconnection with exponential backoff
- Up to 5 reconnection attempts
- Delays: 1s, 2s, 4s, 8s, 10s (max)
- Resets counter on successful connection

```javascript
async function attemptReconnect() {
    const delay = Math.min(1000 * Math.pow(2, attempts - 1), 10000)
    setTimeout(() => reconnect(), delay)
}
```

### 4. ICE Restart Capability (JavaScript & Python)
**File**: `web-client/src/scripts/webrtc.js` & `central-server/src/endpoints/remote_control_gateway.py`

- Detects ICE connection failures
- Creates new offer with `iceRestart: true`
- Server creates new answer
- Recovers from ICE failures without full reconnection

```javascript
const offer = await peerConnection.createOffer({ iceRestart: true })
```

### 5. Keepalive Response (JavaScript)
**File**: `web-client/src/scripts/webrtc.js`

- Detects keepalive PING messages
- Responds with PONG to confirm connection is alive
- Maintains bidirectional activity

```javascript
if (isPingMessage) {
    channel.send(new Uint8Array([0, 80, 79, 78, 71]))  // PONG
}
```

### 6. Enhanced RTCPeerConnection Configuration

**Client-Side**:
```javascript
{
    iceServers: [...],
    iceTransportPolicy: 'all',
    bundlePolicy: 'max-bundle',
    rtcpMuxPolicy: 'require'
}
```

**Server-Side**:
```python
config = RTCConfiguration(
    iceServers=[
        RTCIceServer(urls=["stun:stun.l.google.com:19302"]),
        RTCIceServer(urls=["stun:stun1.l.google.com:19302"])
    ]
)
```

### 7. Buffer Monitoring (JavaScript)
**File**: `web-client/src/scripts/webrtc.js`

- Monitors video channel buffer every 5 seconds
- Warns when buffer exceeds 4MB
- Helps diagnose network congestion issues

## Testing the Improvements

### Expected Behavior
1. **Connection Establishment**: 
   - Should see "✅ WebRTC peer connection established"
   - Data channels open successfully

2. **During Operation**:
   - Every 5 seconds: "💓 Received keepalive ping" and "💓 Sent keepalive pong"
   - Video data flows continuously
   - No disconnections under normal conditions

3. **Network Issues**:
   - Brief disruptions: ICE restart attempts automatically
   - Extended disruptions: Automatic reconnection (up to 5 attempts)
   - "🔄 Reconnection attempt X/5 in Yms..."

4. **Buffer Warnings**:
   - If you see "⚠️ Video channel buffer high", the system is dropping frames to prevent overflow
   - This is normal under high network load

### Console Logs to Monitor

**Healthy Connection**:
```
✅ WebRTC peer connection established
✅ Data channel 'video' opened, readyState: open
✅ Data channel 'commands' opened, readyState: open
💓 Received keepalive ping
💓 Sent keepalive pong
```

**ICE Issues (Auto-Recovering)**:
```
🧊 ICE connection state: failed
🔧 ICE connection failed, attempting ICE restart...
✅ ICE restart successful
```

**Connection Loss (Auto-Reconnecting)**:
```
⚠️ WebRTC peer connection disconnected - attempting to reconnect...
🔄 Reconnection attempt 1/5 in 1000ms...
✅ WebRTC peer connection established
```

## Performance Considerations

### Keepalive Overhead
- **Frequency**: Every 5 seconds
- **Size**: 5 bytes per ping/pong
- **Bandwidth**: ~16 bytes/sec (negligible)

### Frame Dropping
- Occurs when buffer > 4MB
- Prevents connection failure
- Maintains real-time performance
- Prioritizes latest frames over buffered ones

### Reconnection Impact
- Automatic reconnection takes 1-10 seconds
- Video stream interruption during reconnection
- Connection state indicator updates in UI

## Configuration Options

### Adjust Keepalive Interval
In `webrtc_manager.py`:
```python
await asyncio.sleep(5)  # Change from 5 to desired seconds
```

### Adjust Buffer Threshold
In `webrtc_manager.py`:
```python
max_buffer_size = 4 * 1024 * 1024  # Change 4MB threshold
```

### Adjust Reconnection Attempts
In `webrtc.js`:
```javascript
const maxReconnectAttempts = ref(5)  // Change max attempts
```

### Adjust Reconnection Delay
In `webrtc.js`:
```javascript
const delay = Math.min(1000 * Math.pow(2, attempts - 1), 10000)
// Adjust base (1000ms) or max (10000ms)
```

## Troubleshooting

### Still Experiencing Disconnections?

1. **Check Server Logs**:
   ```
   grep "WebRTC:" central-server.log
   ```
   Look for error messages or buffer warnings

2. **Check Client Console**:
   - Press F12 in browser
   - Look for connection state changes
   - Check if keepalive pings are being received

3. **Network Analysis**:
   - Use browser DevTools Network tab
   - Check for packet loss
   - Verify STUN server accessibility

4. **Firewall/NAT Issues**:
   - Ensure UDP ports are open
   - Consider adding TURN server if behind strict NAT
   - Test from different networks

### Adding TURN Server (Optional)

If still experiencing issues behind strict NAT/firewall:

**Server-Side**:
```python
config = RTCConfiguration(
    iceServers=[
        RTCIceServer(urls=["stun:stun.l.google.com:19302"]),
        RTCIceServer(
            urls=["turn:your-turn-server.com:3478"],
            username="user",
            credential="pass"
        )
    ]
)
```

**Client-Side**:
```javascript
const rtcConfig = {
    iceServers: [
        { urls: 'stun:stun.l.google.com:19302' },
        {
            urls: 'turn:your-turn-server.com:3478',
            username: 'user',
            credential: 'pass'
        }
    ]
}
```

## Summary

These improvements provide:
- ✅ **Keepalive mechanism** - Prevents idle timeout
- ✅ **Buffer overflow prevention** - Avoids disconnection from full buffers
- ✅ **Automatic reconnection** - Recovers from connection loss
- ✅ **ICE restart** - Handles network path changes
- ✅ **Better monitoring** - Visibility into connection health

The WebRTC connection should now remain stable for extended periods, even on mobile networks or with brief network disruptions.
