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
      console.log('Available trains:', data)
      availableTrains.value = data.trains
      console.log('Available trains:', availableTrains.value)
      console.log('How does it look: ', availableTrains)
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

          // Store the raw frame data as Uint8Array
          currentVideoFrame.value = new Uint8Array(arrayBuffer)
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

    // Update the current train and selected train ID
    currentTrain.value = { ...availableTrains.value[trainId] }
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
    currentTrain,
    isConnected,
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