import { defineStore } from 'pinia'
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useWebSocket } from '@/scripts/websocket'
import { useWebTransport } from '@/scripts/webtransport'
import { SERVER_URL } from '@/scripts/config'
// import { useAssembler } from '@/scripts/assembler'

// Define server IP and host


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
  const currentVideoFrame = ref(null)
  const remoteControlId = ref(null)
  const videoDatagramAssembler = ref(null)
  const keepaliveSequence = ref(0)
  const direction = ref('FORWARD')
  const isPoweredOn = ref(true)
  const router = useRouter()

  const {
    connectWebSocket,
  } = useWebSocket(remoteControlId, handleWsMessage)

  const {
    connectWebTransport,
    sendWtMessage,
  } = useWebTransport(remoteControlId, handleWtMessage)

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
    await connectWebSocket()
    await connectWebTransport()
    setInterval(sendKeepAliveWebTransport, 10000);
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
    sendWtMessage(`MAP_CONNECTION:${remoteControlId.value}:${trainId}`);

  }

  async function sendCommand(command) {
    switch (command.instruction) {
      case "POWER_ON": isPoweredOn.value = true; break
      case "POWER_OFF": isPoweredOn.value = false; break
      case "CHANGE_DIRECTION": direction.value = command.direction; break
    }

    // Convert command object to JSON and then to Uint8Array
    const jsonString = JSON.stringify(command)
    const jsonBytes = new TextEncoder().encode(jsonString)
    try {
      const packet = new Uint8Array(1 + jsonBytes.length)
      packet[0] = PACKET_TYPE.command
      packet.set(new TextEncoder().encode(JSON.stringify(command)), 1)
      await sendWtMessage(packet)
    } catch (error) {
      console.error('Command send error:', error)
    }
  }

  async function handleWsMessage(packetType, payload) {
    switch (packetType) {
      case PACKET_TYPE.telemetry: {
        telemetryData.value = JSON.parse(new TextDecoder().decode(payload))
        break
      }
      case PACKET_TYPE.notification: {
        const notification = JSON.parse(new TextDecoder().decode(payload))
        if (notification.train_id === selectedTrainId.value && notification.event === 'disconnected') {
          router.push('/')
        }
        fetchAvailableTrains()
        break
      }
    }
  }

  function handleWtMessage(packetType, payload) {
    let jsonString = ""
    let jsonData = {}
    switch (packetType) {
      case PACKET_TYPE.telemetry:
        try {
          jsonString = new TextDecoder().decode(payload)
          jsonData = JSON.parse(jsonString)
          console.log('WebTransport: Received telemetry data:', jsonData)
          telemetryData.value = jsonData

          // also update isPoweredOn and direction

          if (jsonData.status === 'running'){
            isPoweredOn.value = true
          } else {
            isPoweredOn.value = false
          }

          if (jsonData.direction === 1) {
            direction.value = 'FORWARD'
          } else {
            direction.value = 'BACKWARD'
          }

          console.log("receiveWebTransportStream: isPoweredOn:", isPoweredOn.value)

          break;
        } catch (error) {
          console.error('Error parsing telemetry data:', error)
          break;
        }
      case PACKET_TYPE.video:
        videoDatagramAssembler.value.processPacket(payload)
        break
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

    sendWtMessage(packet)
    console.log('WebTransport keepalive sent:', keepalivePacket);
  }
  return {
    availableTrains,
    selectedTrainId,
    telemetryData,
    currentVideoFrame,
    remoteControlId,
    isPoweredOn,
    direction,
    initializeRemoteControlId,
    fetchAvailableTrains,
    connectToServer,
    mappingToTrain,
    sendCommand
  }
})
