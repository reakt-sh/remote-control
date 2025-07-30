import { ref } from 'vue'
import { MQTT_BROKER_URL } from '@/scripts/config'

/**
 * MQTT Client for Web Browser using native WebSocket implementation
 * This avoids Babel compatibility issues with the mqtt library
 */
export function useMqttClient(messageHandler) {
  const isMqttConnected = ref(false)
  const wsConnection = ref(null)
  const subscriptions = ref(new Set())
  
  // MQTT Broker Configuration - using WebSocket directly
  const MQTT_CONFIG = {
    // Use WebSocket connection for browser compatibility
    brokerUrl: MQTT_BROKER_URL, // WebSocket endpoint for MQTT broker
    reconnectDelay: 3000,
    keepAliveInterval: 30000,
  }

  /**
   * Connect to MQTT broker via WebSocket
   */
  async function connect() {
    if (isMqttConnected.value) {
      console.log('MQTT client already connected')
      return
    }

    try {
      console.log(`Connecting to MQTT broker at ${MQTT_CONFIG.brokerUrl}`)
      
      wsConnection.value = new WebSocket(MQTT_CONFIG.brokerUrl, ['mqtt'])

      // Connection successful
      wsConnection.value.onopen = () => {
        isMqttConnected.value = true
        console.log('✅ MQTT WebSocket connected successfully')

        // Start keep-alive mechanism
        startKeepAlive()
      }

      // Handle incoming messages
      wsConnection.value.onmessage = (event) => {
        try {
          // For now, simulate MQTT message format
          // In a real implementation, you'd parse the MQTT protocol
          const message = JSON.parse(event.data)
          console.log(`📨 MQTT message received:`, message)
          
          if (message.topic && message.payload) {
            handleMqttMessage(message.topic, message.payload)
          }
        } catch (error) {
          console.error('Error processing MQTT message:', error)
        }
      }

      // Handle connection errors
      wsConnection.value.onerror = (error) => {
        console.error('❌ MQTT WebSocket connection error:', error)
        isMqttConnected.value = false
      }

      // Handle disconnection
      wsConnection.value.onclose = () => {
        console.log('� MQTT WebSocket connection closed')
        isMqttConnected.value = false
        
        // Attempt reconnection
        setTimeout(() => {
          if (!isMqttConnected.value) {
            console.log('🔄 Attempting MQTT reconnection...')
            connect()
          }
        }, MQTT_CONFIG.reconnectDelay)
      }

    } catch (error) {
      console.error('Failed to create MQTT WebSocket connection:', error)
      isMqttConnected.value = false
    }
  }

  /**
   * Handle parsed MQTT messages
   */
  function handleMqttMessage(topic, payload) {
    // Parse topic to extract train_id and message type
    const topicParts = topic.split('/')
    if (topicParts.length >= 3) {
      const trainId = topicParts[1]
      const messageType = topicParts[2]
      
      // Parse JSON payload
      let data
      try {
        data = typeof payload === 'string' ? JSON.parse(payload) : payload
      } catch (e) {
        console.error('Failed to parse MQTT payload:', e)
        return
      }
      
      // Call the message handler with structured data
      if (messageHandler) {
        messageHandler({
          topic,
          trainId,
          messageType,
          data,
          timestamp: Date.now()
        })
      }
    }
  }

  /**
   * Start keep-alive mechanism
   */
  function startKeepAlive() {
    const keepAliveTimer = setInterval(() => {
      if (isMqttConnected.value && wsConnection.value) {
        try {
          // Send ping message
          const pingMessage = JSON.stringify({
            type: 'ping',
            timestamp: Date.now()
          })
          wsConnection.value.send(pingMessage)
        } catch (error) {
          console.error('Failed to send keep-alive ping:', error)
          clearInterval(keepAliveTimer)
        }
      } else {
        clearInterval(keepAliveTimer)
      }
    }, MQTT_CONFIG.keepAliveInterval)
  }

  /**
   * Disconnect from MQTT broker
   */
  function disconnect() {
    if (wsConnection.value && isMqttConnected.value) {
      wsConnection.value.close()
      isMqttConnected.value = false
      subscriptions.value.clear()
      console.log('🔌 MQTT client disconnected')
    }
  }

  /**
   * Subscribe to train telemetry topics
   */
  function subscribeToTrainTelemetry() {
    const topics = [
      'train/+/telemetry',    // All train telemetry
      'train/+/status',       // All train status updates
      'train/+/heartbeat'     // All train heartbeats
    ]

    topics.forEach(topic => subscribe(topic))
  }

  /**
   * Subscribe to a specific MQTT topic
   */
  function subscribe(train_id, qos = 1) {
    if (!wsConnection.value || !isMqttConnected.value) {
      console.warn('Cannot subscribe: MQTT client not connected')
      return false
    }
    const topic = `train/${train_id}/telemetry` // Example topic format
    try {
      const subscribeMessage = JSON.stringify({
        type: 'subscribe',
        topic: topic,
        qos: qos
      })
      
      wsConnection.value.send(subscribeMessage)
      subscriptions.value.add(topic)
      console.log(`✅ Subscribed to MQTT topic: ${topic}`)
      return true
    } catch (error) {
      console.error(`❌ Failed to subscribe to ${topic}:`, error)
      return false
    }
  }

  /**
   * Unsubscribe from a specific MQTT topic
   */
  function unsubscribe(train_id) {
    if (!wsConnection.value || !isMqttConnected.value) {
      console.warn('Cannot unsubscribe: MQTT client not connected')
      return false
    }
    const topic = `train/${train_id}/telemetry` // Example topic format
    try {
      const unsubscribeMessage = JSON.stringify({
        type: 'unsubscribe',
        topic: topic
      })
      
      wsConnection.value.send(unsubscribeMessage)
      subscriptions.value.delete(topic)
      console.log(`🚫 Unsubscribed from MQTT topic: ${topic}`)
      return true
    } catch (error) {
      console.error(`❌ Failed to unsubscribe from ${topic}:`, error)
      return false
    }
  }

  /**
   * Subscribe to telemetry from a specific train
   */
  function subscribeToTrain(trainId) {
    const topics = [
      `train/${trainId}/telemetry`,
      `train/${trainId}/status`,
      `train/${trainId}/heartbeat`
    ]

    topics.forEach(topic => subscribe(topic))
  }

  /**
   * Unsubscribe from telemetry from a specific train
   */
  function unsubscribeFromTrain(trainId) {
    const topics = [
      `train/${trainId}/telemetry`,
      `train/${trainId}/status`,
      `train/${trainId}/heartbeat`
    ]

    topics.forEach(topic => unsubscribe(topic))
  }

  /**
   * Publish a message to MQTT broker (for commands)
   */
  function publish(topic, message, qos = 1) {
    if (!wsConnection.value || !isMqttConnected.value) {
      console.warn('Cannot publish: MQTT client not connected')
      return false
    }

    try {
      const payload = typeof message === 'string' ? message : JSON.stringify(message)
      const publishMessage = JSON.stringify({
        type: 'publish',
        topic: topic,
        payload: payload,
        qos: qos
      })

      wsConnection.value.send(publishMessage)
      console.log(`📤 Published to MQTT topic ${topic}:`, payload)
      return true
    } catch (error) {
      console.error(`❌ Failed to publish to ${topic}:`, error)
      return false
    }
  }

  /**
   * Send command to a specific train via MQTT
   */
  function sendCommandToTrain(trainId, command) {
    const topic = `commands/${trainId}/control`
    return publish(topic, command)
  }

  /**
   * Get connection status and statistics
   */
  function getConnectionInfo() {
    return {
      connected: isMqttConnected.value,
      brokerUrl: MQTT_CONFIG.brokerUrl,
      subscriptions: Array.from(subscriptions.value),
      subscriptionCount: subscriptions.value.size,
      connectionType: 'WebSocket'
    }
  }

  /**
   * Check if connected to MQTT broker
   */
  function isConnected() {
    return isMqttConnected.value
  }

  return {
    // Connection state
    isMqttConnected,
    
    // Connection methods
    connectMqtt: connect,
    disconnectMqtt: disconnect,
    
    // Subscription methods
    subscribe,
    unsubscribe,
    subscribeToTrain,
    unsubscribeFromTrain,
    subscribeToTrainTelemetry,
    
    // Publishing methods
    publish,
    sendCommandToTrain,
    
    // Utility methods
    getConnectionInfo,
    isConnected
  }
}

/**
 * Simple MQTT message formatter for telemetry data
 */
export function formatMqttTelemetryMessage(mqttMessage) {
  const { trainId, messageType, data, timestamp } = mqttMessage
  
  return {
    train_id: trainId,
    message_type: messageType,
    timestamp: timestamp,
    data: data,
    // Convert to format expected by existing components
    speed: data.speed,
    status: data.status,
    location: data.location,
    battery_level: data.battery_level,
    temperature: data.temperature,
    // Add all other telemetry fields
    ...data
  }
}

/**
 * MQTT Topic utilities
 */
export const MqttTopics = {
  // Telemetry topics
  TRAIN_TELEMETRY: (trainId) => `train/${trainId}/telemetry`,
  TRAIN_STATUS: (trainId) => `train/${trainId}/status`,
  TRAIN_HEARTBEAT: (trainId) => `train/${trainId}/heartbeat`,
  
  // Command topics
  TRAIN_COMMANDS: (trainId) => `commands/${trainId}/control`,
  
  // Wildcard topics
  ALL_TRAIN_TELEMETRY: 'train/+/telemetry',
  ALL_TRAIN_STATUS: 'train/+/status',
  ALL_TRAIN_HEARTBEAT: 'train/+/heartbeat',
}

export default useMqttClient
