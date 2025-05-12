import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

// Define server IP and port as constants
const SERVER_IP = 'localhost'
const SERVER_PORT = 8000
const SERVER_URL = `http://${SERVER_IP}:${SERVER_PORT}`
const WS_URL = `ws://${SERVER_IP}:${SERVER_PORT}`
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


  const selectedTrain = computed(() => {
    return availableTrains.value[selectedTrainId.value] || null
  })
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
      availableTrains.value = data.trains
      console.log('Available trains:', availableTrains.value)
    } catch (error) {
      console.error('Error fetching trains:', error)
    }
  }

  function connectToServer() {
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
              currentVideoFrame.value = new Uint8Array(payload)
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
  }

  function sendCommand(action, value) {
    if (!isConnected.value || !webSocket.value) return

    const command = {
      action,
      value,
      timestamp: new Date().toISOString()
    }

    webSocket.value.send(JSON.stringify(command))
  }

  return {
    availableTrains,
    selectedTrainId,
    isConnected,
    telemetryData,
    selectedTrain,
    currentVideoFrame,
    remoteControlId,
    initializeRemoteControlId,
    fetchAvailableTrains,
    connectToServer,
    mappingToTrain,
    sendCommand
  }
})