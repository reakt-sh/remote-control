import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

// Define server IP and port as constants
const SERVER_IP = 'localhost'
const SERVER_PORT = 8000
const SERVER_URL = `http://${SERVER_IP}:${SERVER_PORT}`
const WS_URL = `ws://${SERVER_IP}:${SERVER_PORT}`

export const useTrainStore = defineStore('train', () => {
  const availableTrains = ref({})
  const selectedTrainId = ref('')
  const currentTrain = ref(null)
  const isConnected = ref(false)
  const webSocket = ref(null)
  const currentVideoFrame = ref(null) // Add this line


  const selectedTrain = computed(() => {
    return availableTrains.value[selectedTrainId.value] || null
  })

  async function fetchAvailableTrains() {
    try {
      const response = await fetch(`${SERVER_URL}/api/trains`)
      const data = await response.json()
      console.log('Available trains:', data)
      availableTrains.value = data.trains
      console.log('Available trains:', availableTrains.value)
      console.log('How does it look: ', availableTrains)
    } catch (error) {
      console.error('Error fetching trains:', error)
    }
  }

  function connectToTrain(trainId) {
    if (!trainId) return

    // Disconnect previous connection if exists
    if (webSocket.value) {
      webSocket.value.close()
      isConnected.value = false
    }

    selectedTrainId.value = trainId

    // Connect to WebSocket
    webSocket.value = new WebSocket(`${WS_URL}/ws/remote_control/${trainId}`)

    webSocket.value.onopen = () => {
      isConnected.value = true
      console.log('WebSocket connected')

      // Get initial train data
      currentTrain.value = { ...availableTrains.value[trainId] }
      console.log('Initial train data:', currentTrain.value)
      console.log(currentTrain.value.name)
    }

    webSocket.value.onmessage = (event) => {
      if (event.data instanceof ArrayBuffer) {
        // Store the raw frame data
        currentVideoFrame.value = new Uint8Array(event.data)
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
    currentTrain,
    isConnected,
    selectedTrain,
    currentVideoFrame, // Add this line
    fetchAvailableTrains,
    connectToTrain,
    sendCommand
  }
})