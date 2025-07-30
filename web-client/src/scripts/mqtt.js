import { ref } from 'vue'
import mqtt from 'mqtt'

/**
 * MQTT Client for Web Browser using MQTT over WebSocket
 * Subscribes to train telemetry data from MQTT broker
 */
export function useMqttClient(messageHandler) {
  const isMqttConnected = ref(false)
  const mqttClient = ref(null)
  const subscriptions = ref(new Set())
  
  // MQTT Broker Configuration
  const MQTT_CONFIG = {
    // Use WebSocket connection for browser compatibility
    brokerUrl: 'ws://localhost:9001', // WebSocket port for MQTT broker
    options: {
      clientId: `web-client-${Math.random().toString(16).substr(2, 8)}`,
      clean: true,
      connectTimeout: 4000,
      reconnectPeriod: 1000,
      keepalive: 60,
    }
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
      
      mqttClient.value = mqtt.connect(MQTT_CONFIG.brokerUrl, MQTT_CONFIG.options)

      // Connection successful
      mqttClient.value.on('connect', () => {
        isMqttConnected.value = true
        console.log('✅ MQTT connected successfully')
        
        // Subscribe to default topics after connection
        subscribeToTrainTelemetry()
      })

      // Handle incoming messages
      mqttClient.value.on('message', (topic, message) => {
        try {
          const payload = message.toString()
          console.log(`📨 MQTT message received on topic ${topic}:`, payload)
          
          // Parse topic to extract train_id and message type
          const topicParts = topic.split('/')
          if (topicParts.length >= 3) {
            const trainId = topicParts[1]
            const messageType = topicParts[2]
            
            // Parse JSON payload
            const data = JSON.parse(payload)
            
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
        } catch (error) {
          console.error('Error processing MQTT message:', error)
        }
      })

      // Handle connection errors
      mqttClient.value.on('error', (error) => {
        console.error('❌ MQTT connection error:', error)
        isMqttConnected.value = false
      })

      // Handle disconnection
      mqttClient.value.on('close', () => {
        console.log('🔌 MQTT connection closed')
        isMqttConnected.value = false
      })

      // Handle reconnection
      mqttClient.value.on('reconnect', () => {
        console.log('🔄 MQTT reconnecting...')
      })

      // Handle offline status
      mqttClient.value.on('offline', () => {
        console.log('📴 MQTT client offline')
        isMqttConnected.value = false
      })

    } catch (error) {
      console.error('Failed to create MQTT client:', error)
      isMqttConnected.value = false
    }
  }

  /**
   * Disconnect from MQTT broker
   */
  function disconnect() {
    if (mqttClient.value && isMqttConnected.value) {
      mqttClient.value.end()
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
  function subscribe(topic, qos = 1) {
    if (!mqttClient.value || !isMqttConnected.value) {
      console.warn('Cannot subscribe: MQTT client not connected')
      return false
    }

    mqttClient.value.subscribe(topic, { qos }, (error) => {
      if (error) {
        console.error(`❌ Failed to subscribe to ${topic}:`, error)
      } else {
        subscriptions.value.add(topic)
        console.log(`✅ Subscribed to MQTT topic: ${topic}`)
      }
    })

    return true
  }

  /**
   * Unsubscribe from a specific MQTT topic
   */
  function unsubscribe(topic) {
    if (!mqttClient.value || !isMqttConnected.value) {
      console.warn('Cannot unsubscribe: MQTT client not connected')
      return false
    }

    mqttClient.value.unsubscribe(topic, (error) => {
      if (error) {
        console.error(`❌ Failed to unsubscribe from ${topic}:`, error)
      } else {
        subscriptions.value.delete(topic)
        console.log(`🚫 Unsubscribed from MQTT topic: ${topic}`)
      }
    })

    return true
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
    if (!mqttClient.value || !isMqttConnected.value) {
      console.warn('Cannot publish: MQTT client not connected')
      return false
    }

    const payload = typeof message === 'string' ? message : JSON.stringify(message)

    mqttClient.value.publish(topic, payload, { qos }, (error) => {
      if (error) {
        console.error(`❌ Failed to publish to ${topic}:`, error)
      } else {
        console.log(`📤 Published to MQTT topic ${topic}:`, payload)
      }
    })

    return true
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
      clientId: MQTT_CONFIG.options.clientId,
      brokerUrl: MQTT_CONFIG.brokerUrl,
      subscriptions: Array.from(subscriptions.value),
      subscriptionCount: subscriptions.value.size
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
