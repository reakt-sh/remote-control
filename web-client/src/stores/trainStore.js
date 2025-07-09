import { defineStore } from 'pinia'
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useWebSocket } from '@/scripts/websocket'
import { SERVER_URL, QUIC_URL } from '@/scripts/config'
// import { useWebTransport } from '@/scripts/webtransport'
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
  const webSocket = ref(null)
  const currentVideoFrame = ref(null)
  const remoteControlId = ref(null)
  const webTransport = ref(null)
  const bidistream = ref(null)
  const videoDatagramAssembler = ref(null)
  const keepaliveSequence = ref(0)
  const direction = ref('FORWARD')
  const isPoweredOn = ref(true)
  const router = useRouter()

  const {
    isConnected,
    connectWebSocket,
  } = useWebSocket(remoteControlId, handleWsMessage)

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
    await connectWebSocket()
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
    switch (command["instruction"]) {
      case "POWER_ON":
        isPoweredOn.value = true
        break
      case "POWER_OFF":
        isPoweredOn.value = false
        break
      case "CHANGE_DIRECTION":
        direction.value = command["direction"]
        break
    }
    console.log("sendCommand: isPoweredOn:", isPoweredOn.value)
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

  async function connectToWebTransport() {
    if (isConnected.value) {
      console.log('Already connected to WebTransport')
      return
    }
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
      let data;
      if (typeof message === 'string') {
        data = new TextEncoder().encode(message);
      } else if (message instanceof Uint8Array) {
        data = message;
      } else {
        throw new Error('Unsupported message type');
      }
      await writer.write(data);
      writer.releaseLock();
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
    isPoweredOn,
    direction,
    initializeRemoteControlId,
    fetchAvailableTrains,
    connectToServer,
    mappingToTrain,
    sendCommand
  }
})
