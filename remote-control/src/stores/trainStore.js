import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useTrainStore = defineStore('train', () => {
  const availableTrains = ref({})
  const selectedTrainId = ref('')
  const currentTrain = ref(null)
  const isConnected = ref(false)
  const socket = ref(null)

  const selectedTrain = computed(() => {
    return availableTrains.value[selectedTrainId.value] || null
  })

  async function fetchAvailableTrains() {
    try {
      const response = await fetch('http://localhost:8000/api/trains')
      const data = await response.json()
      availableTrains.value = data.trains
    } catch (error) {
      console.error('Error fetching trains:', error)
    }
  }

  function connectToTrain(trainId) {
    if (!trainId) return

    // Disconnect previous connection if exists
    if (socket.value) {
      socket.value.close()
      isConnected.value = false
    }

    selectedTrainId.value = trainId

    // Connect to WebSocket
    socket.value = new WebSocket(`ws://localhost:8000/ws/${trainId}`)

    socket.value.onopen = () => {
      isConnected.value = true
      console.log('WebSocket connected')

      // Get initial train data
      currentTrain.value = { ...availableTrains.value[trainId] }
    }

    socket.value.onmessage = (event) => {
      const message = JSON.parse(event.data)
      if (message.type === 'telemetry') {
        currentTrain.value = { ...message.data }
      }
    }

    socket.value.onclose = () => {
      isConnected.value = false
      console.log('WebSocket disconnected')
    }

    socket.value.onerror = (error) => {
      console.error('WebSocket error:', error)
      isConnected.value = false
    }
  }

  function sendCommand(action, value) {
    if (!isConnected.value || !socket.value) return

    const command = {
      action,
      value,
      timestamp: new Date().toISOString()
    }

    socket.value.send(JSON.stringify(command))
  }

  return {
    availableTrains,
    selectedTrainId,
    currentTrain,
    isConnected,
    selectedTrain,
    fetchAvailableTrains,
    connectToTrain,
    sendCommand
  }
})