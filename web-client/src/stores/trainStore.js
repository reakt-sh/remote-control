import { defineStore } from 'pinia'
import { ref } from 'vue'

// Define server IP and host for local development
// const SERVER = 'localhost'
// const SERVER_IP = '127.0.0.1'

// Define server IP and host for production
const SERVER = '209.38.218.207'
const SERVER_IP = '209.38.218.207'

// Define server ports, same for both local and production
const SERVER_PORT = 8000
const QUIC_PORT = 4437
const SERVER_URL = `https://${SERVER}:${SERVER_PORT}`
const WS_URL = `wss://${SERVER}:${SERVER_PORT}`
const QUIC_URL = `https://${SERVER_IP}:${QUIC_PORT}`

// Packet Types
const PACKET_TYPE = {
  video: 13,
  audio: 14,
  control: 15,
  command: 16,
  telemetry: 17,
  imu: 18,
  lidar: 19,
  keepalive: 20,
  notification: 21
}


export const useTrainStore = defineStore('train', () => {
  const availableTrains = ref({})
  const selectedTrainId = ref('')
  const telemetryData = ref(null)
  const isConnected = ref(false)
  const webSocket = ref(null)
  const currentVideoFrame = ref(null)
  const remoteControlId = ref(null)
  const webTransport = ref(null)
  const bidistream = ref(null)
  const videoDatagramAssembler = ref(null);
  const keepaliveSequence = ref(0);

  function generateUUID() {
    // RFC4122 version 4 compliant UUID
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
      const r = Math.random() * 16 | 0, v = c === 'x' ? r : (r & 0x3 | 0x8);
      return v.toString(16);
    });
  }

  function initializeRemoteControlId() {
    if(!remoteControlId.value) {
      remoteControlId.value = generateUUID()
      console.log('Remote control ID initialized:', remoteControlId.value)
    }
  }
  async function fetchAvailableTrains() {
    try {
      const response = await fetch(`${SERVER_URL}/api/trains`)
      const data = await response.json()
      console.log('Available trains:', data)
      availableTrains.value = data
      console.log('after write availableTrains :', availableTrains.value)
    } catch (error) {
      console.error('Error fetching trains:', error)
    }
  }

  async function connectToServer() {
    connectToWebTransport()
    connectToWebSocket()
  }

  async function mappingToTrain(trainId) {
    if (!trainId) return
    telemetryData.value = {}
    selectedTrainId.value = trainId
    // initialize video stream handler if not already initialized
    if (videoDatagramAssembler.value && videoDatagramAssembler.value.trainId !== trainId) {
      videoDatagramAssembler.value = null; // Reset if trainId changes
    }

    if (!videoDatagramAssembler.value && selectedTrainId.value) {
      videoDatagramAssembler.value = assembleVideoDatagram();
    }

    // Send a POST request to assign the train to the remote control
    if (remoteControlId.value) {
      const url = `${SERVER_URL}/api/remote_control/${remoteControlId.value}/train/${trainId}`

      try {
        const response = await fetch(url, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          }
        })

        if (!response.ok) {
          throw new Error(`Failed to assign train. Status: ${response.status}`)
        }

        const data = await response.json()
        console.log('Train assigned successfully:', data)
      } catch (error) {
        console.error('Error assigning train to remote control:', error)
      }
    } else {
      console.error('Remote control ID is not initialized')
    }

    // Send a message through WebTransport to notify the server
    if (webTransport.value) {
      sendWebTransportStream(`MAP_CONNECTION:${remoteControlId.value}:${trainId}`);
    } else {
      console.error('WebTransport is not connected');
    }
  }

  async function sendCommand(command) {
    if (!isConnected.value || !webSocket.value) {
      console.log("No Train Connected or No websocket Connection established")
      return
    }
    try {
      // Convert command object to JSON and then to Uint8Array
      const jsonString = JSON.stringify(command)
      const jsonBytes = new TextEncoder().encode(jsonString)

      // Create a new Uint8Array with the first byte as PACKET_TYPE.command
      const packet = new Uint8Array(1 + jsonBytes.length)
      packet[0] = PACKET_TYPE.command
      packet.set(jsonBytes, 1)

      //webSocket.value.send(packet)
      sendWebTransportStream(packet);
    } catch (error) {
      console.log(error)
    }
  }
  async function connectToWebSocket() {
    // Disconnect previous connection if exists
    if (webSocket.value) {
      webSocket.value.close()
      isConnected.value = false
    }

    // Connect to WebSocket
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
          const packetType = byteArray[0]
          const payload = byteArray.slice(1)
          let jsonData = {}
          let jsonString = ""
          switch (packetType) {
            case PACKET_TYPE.video:
              // This is now handled by WebTransport
              break
            case PACKET_TYPE.audio:
              console.log('Received audio data')
              break
            case PACKET_TYPE.control:
              console.log('Received control data')
              break
            case PACKET_TYPE.command:
              console.log('Received command data')
              break
            case PACKET_TYPE.telemetry:
              jsonString = new TextDecoder().decode(payload)
              jsonData = JSON.parse(jsonString)
              console.log('Received telemetry data:', jsonData)
              telemetryData.value = jsonData
              console.log('Train Name :', telemetryData.value.name)
              console.log('Train Battery :', telemetryData.value.battery_level)
              console.log('train status :', telemetryData.value.status)
              break
            case PACKET_TYPE.imu:
              console.log('Received IMU data')
              break
            case PACKET_TYPE.lidar:
              console.log('Received LiDAR data')
              break
            case PACKET_TYPE.keepalive:
              console.log('Keepalive packet received')
              break
            case PACKET_TYPE.notification:
              jsonString = new TextDecoder().decode(payload)
              jsonData = JSON.parse(jsonString)
              console.log('Notification packet received', jsonData)
              fetchAvailableTrains()
              break
            default:
              console.warn('Unknown packet type:', arrayBuffer[0])
          }
        } catch (error) {
          console.error('Error processing Blob data:', error)
        }
      } else {
        console.warn('Unexpected data type received:', typeof event.data)
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

  async function connectToWebTransport() {
    if (webTransport.value) {
        webTransport.value.close()
        webTransport.value = null
    }

    try {
        console.log('Connecting to WebTransport...')
        webTransport.value = new WebTransport(QUIC_URL);
        await webTransport.value.ready
        console.log('WebTransport connected')
        receiveWebTransportDatagrams();

        bidistream.value = await webTransport.value.createBidirectionalStream();
        receiveWebTransportStream();
        sendWebTransportStream(`REMOTE_CONTROL:${remoteControlId.value}`);
        setInterval(sendKeepAliveWebTransport, 10000);
    } catch (error) {
      console.error('WebTransport connection error:', error)
    }
  }

  async function receiveWebTransportStream()
  {
    const reader = bidistream.value.readable.getReader();
    // eslint-disable-next-line no-constant-condition
    while (true) {
      const { value, done } = await reader.read();
      if (done) {
        console.log('Stream closed');
        break;
      }
      console.log('Received from stream:', new TextDecoder().decode(value));
      const byteArray = new Uint8Array(value)
      const packetType = byteArray[0]
      const payload = byteArray.slice(1)
      let jsonString = ""
      let jsonData = {}
      switch (packetType) {
        case PACKET_TYPE.telemetry:
          try {
            jsonString = new TextDecoder().decode(payload)
            jsonData = JSON.parse(jsonString)
            console.log('WebTransport: Received telemetry data:', jsonData)
            telemetryData.value = jsonData
            break;
          } catch (error) {
            console.error('Error parsing telemetry data:', error)
            break;
          }

      }
      // Process the received data here
    }
  }

  async function sendWebTransportStream(message) {
    console.log('Sending WebTransport message:', message);
    if (!webTransport.value) {
      console.error('WebTransport is not connected');
      return;
    }
    try {
      const writer = bidistream.value.writable.getWriter();
      const data = new TextEncoder().encode(message);
      await writer.write(data);
      writer.releaseLock(); // Release the lock for future writes
      console.log('WebTransport message sent:', message);
    } catch (error) {
      console.error('Error sending WebTransport message:', error);
    }
  }

  function assembleVideoDatagram() {
    let currentFrame = [];
    let currentFrameId = -1;
    let expectedPackets = 0;
    let receivedPackets = 0;

    return {
      async processPacket(data) {
        try {
          // data[0] is packet_type
          const frameId = (data[1] << 24) | (data[2] << 16) | (data[3] << 8) | data[4];
          const numberOfPackets = (data[5] << 8) | data[6];
          const packetId = (data[7] << 8) | data[8];
          const payload = data.slice(45);

          if (frameId !== currentFrameId) {
            // New frame
            currentFrame = [];
            currentFrameId = frameId;
            expectedPackets = numberOfPackets;
            receivedPackets = 0;
          }

          currentFrame.push(...payload);
          receivedPackets += 1;

          if (packetId === numberOfPackets && receivedPackets === expectedPackets) {
            // Complete frame received
            currentVideoFrame.value = new Uint8Array(currentFrame);
            console.log('Received complete video frame over WebTransport Datagram');
            currentFrame = [];
          }

        } catch (e) {
          console.error('Error processing video packet:', e);
        }
      }
    };
  }

  async function receiveWebTransportDatagrams() {
    if (!webTransport.value) {
      console.error('WebTransport is not connected');
      return;
    }
    try {
      const datagram_reader = webTransport.value.datagrams.readable.getReader();
      console.log('Receiving WebTransport datagrams...');

      // eslint-disable-next-line no-constant-condition
      while (true) {
        const { value, done } = await datagram_reader.read();
        if (done) {
          console.log('WebTransport datagram stream closed');
          break;
        }
        if (value && value[0] === PACKET_TYPE.video) {
          videoDatagramAssembler.value.processPacket(value);
        } else {
          console.log('Received WebTransport datagram UNKNOWN PACKET');
        }
      }
      datagram_reader.releaseLock();
    } catch (error) {
      console.error('Error receiving WebTransport datagrams:', error);
    }
  }

  async function sendKeepAliveWebTransport() {
    const keepalivePacket = {
      type: "keepalive",
      protocol: "webtransport",
      remoteControlId: remoteControlId.value,
      timestamp: Date.now() / 1000, // seconds since epoch, similar to Python's time()
      sequence: keepaliveSequence.value++  // increment your sequence variable
    };
    const packetData = new TextEncoder().encode(JSON.stringify(keepalivePacket));
    const packet = new Uint8Array(1 + packetData.length);
    packet[0] = PACKET_TYPE.keepalive; // Set the first byte as PACKET_TYPE.keepalive
    packet.set(packetData, 1);

    sendWebTransportStream(packet); // your function to send over WebTransport
  }
  return {
    availableTrains,
    selectedTrainId,
    isConnected,
    telemetryData,
    currentVideoFrame,
    remoteControlId,
    initializeRemoteControlId,
    fetchAvailableTrains,
    connectToServer,
    mappingToTrain,
    sendCommand
  }
})