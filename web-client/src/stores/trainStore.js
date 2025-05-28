import { defineStore } from 'pinia'
import { ref } from 'vue'

// Define server IP and port as constants
const SERVER = 'localhost'
const SERVER_PORT = 8000
const SERVER_URL = `http://${SERVER}:${SERVER_PORT}`
const WS_URL = `ws://${SERVER}:${SERVER_PORT}`
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

  function initializeRemoteControlId() {
    if(!remoteControlId.value) {
      remoteControlId.value = crypto.randomUUID()
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

  async function mappingToTrain(trainId) {
    if (!trainId) return
    telemetryData.value = {}
    selectedTrainId.value = trainId

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
      await sendWebTransportMessage(`MAP_CONNECTION:${remoteControlId.value}:${trainId}`);
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

      webSocket.value.send(packet)
    } catch (error) {
      console.log(error)
    }
  }

  async function connectToWebTransport() {
    if (webTransport.value) {
        webTransport.value.close()
        webTransport.value = null
    }

    try {
        console.log('Connecting to WebTransport...')
        webTransport.value = new WebTransport("https://127.0.0.1:4437");
        webTransport.value.ondatagram = (event) => {
            const message = new TextDecoder().decode(event.data);
            console.log('Received WebTransport datagram:', message);
            // Handle the received message here
        }

        await webTransport.value.ready
        console.log('WebTransport connected')

        sendWebTransportMessage(`REMOTE_CONTROL:${remoteControlId.value}`);
        receiveWebTransportDatagrams()
    } catch (error) {
      console.error('WebTransport connection error:', error)
    }
  }

  async function sendWebTransportMessage(message) {
    console.log('Sending WebTransport message:', message);
    if (!webTransport.value) {
      console.error('WebTransport is not connected');
      return;
    }
    try {
      // Create a bidirectional stream
      const stream = await webTransport.value.createBidirectionalStream();
      const writer = stream.writable.getWriter();
      const data = new TextEncoder().encode(message);
      await writer.write(data);
      await writer.close();
      console.log('WebTransport message sent:', message);

      console.log('WebTransport: get reader from stream');
      const reader = stream.readable.getReader();
      console.log('WebTransport: Waiting for response from stream...');
      const { value, done } = await reader.read();
      console.log('WebTransport: received response from stream:', value, 'done:', done);
      if (done) {
        console.log('WebTransport stream closed');
      } else {
        console.log('Received response from WebTransport:', new TextDecoder().decode(value));
      }
    } catch (error) {
      console.error('Error sending WebTransport message:', error);
    }
  }

  async function receiveWebTransportDatagrams() {
    if (!webTransport.value) {
      console.error('WebTransport is not connected');
      return;
    }
    try {
      console.log('Receiving WebTransport datagrams...');
      const reader = webTransport.value.datagrams.readable.getReader();

      // eslint-disable-next-line no-constant-condition
      while (true) {
        console.log('Waiting for WebTransport datagram...');
        const { value, done } = await reader.read();
        console.log('Received WebTransport datagram:', value, 'done:', done);
        if (done) {
          console.log('WebTransport datagram stream closed');
          break;
        }
        if (value) {
          // value is a Uint8Array
          // Handle the datagram here (decode, parse, etc.)
          const message = new TextDecoder().decode(value);
          console.log('Received WebTransport datagram:', message);
          // You can dispatch, commit, or update state here as needed
        }
      }
      reader.releaseLock();
    } catch (error) {
      console.error('Error receiving WebTransport datagrams:', error);
    }
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