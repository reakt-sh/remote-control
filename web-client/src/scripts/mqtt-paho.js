import { ref } from 'vue'
import { Client, Message } from 'paho-mqtt'
import { MQTT_BROKER_URL } from '@/scripts/config'

/**
 * MQTT Client for Web Browser using Paho MQTT JavaScript library
 */
export function useMqttClient(remoteControlId, messageHandler) {
  const isMqttConnected = ref(false)
  const mqttClient = ref(null)
  const subscriptions = ref(new Set())

  // Parse MQTT broker URL to extract host, port, and path
  const brokerConfig = parseBrokerUrl(MQTT_BROKER_URL)

  console.log('🔗 MQTT Broker Config:', brokerConfig)

  /**
   * Parse MQTT broker URL
   */
  function parseBrokerUrl(url) {
    try {
      const urlObj = new URL(url)
      return {
        host: urlObj.hostname,
        port: parseInt(urlObj.port) || (urlObj.protocol === 'wss:' ? 8084 : 8083),
        path: urlObj.pathname || '/mqtt',
        useSSL: urlObj.protocol === 'wss:'
      }
    } catch (error) {
      console.error('Failed to parse MQTT broker URL:', error)
      // Fallback configuration
      return {
        host: 'localhost',
        port: 8083,
        path: '/mqtt',
        useSSL: false
      }
    }
  }

  /**
   * Connect to MQTT broker using Paho MQTT
   */
  async function connect() {
    if (isMqttConnected.value) {
      console.log('MQTT client already connected')
      return
    }

    try {
      // Use existing remoteControlId as client ID
      const clientId = remoteControlId.value
      console.log(`🔌 Connecting to MQTT broker at ${brokerConfig.host}:${brokerConfig.port}${brokerConfig.path}`)
      console.log(`📋 Using client ID: ${clientId}`)

      // Create Paho MQTT client
      mqttClient.value = new Client(
        brokerConfig.host,
        brokerConfig.port,
        brokerConfig.path,
        clientId
      )

      // Set up event handlers
      mqttClient.value.onConnectionLost = onConnectionLost
      mqttClient.value.onMessageArrived = onMessageArrived

      // Connection options
      const connectOptions = {
        useSSL: brokerConfig.useSSL,
        cleanSession: true,
        keepAliveInterval: 30,
        timeout: 10,
        onSuccess: onConnect,
        onFailure: onConnectFailure,
        reconnect: true
      }

      // Connect to broker
      mqttClient.value.connect(connectOptions)

    } catch (error) {
      console.error('❌ Failed to create MQTT client:', error)
      isMqttConnected.value = false
    }
  }

  /**
   * Handle successful connection
   */
  function onConnect() {
    isMqttConnected.value = true
    console.log('✅ MQTT client connected successfully')

    // on connect callback
    if (messageHandler) {
      messageHandler({
        train_id: 'null',
        messageType: 'onConnect',
        status: 'connected',
        timestamp: Date.now()
      })
    }
  }

  /**
   * Handle connection failure
   */
  function onConnectFailure(error) {
    console.error('❌ MQTT connection failed:', error)
    isMqttConnected.value = false
  }

  /**
   * Handle connection lost
   */
  function onConnectionLost(responseObject) {
    isMqttConnected.value = false
    if (responseObject.errorCode !== 0) {
      console.log('🔌 MQTT connection lost:', responseObject.errorMessage)
    }

    // Automatic reconnection is handled by Paho MQTT library
    console.log('🔄 MQTT will attempt to reconnect automatically...')
  }

  /**
   * Handle incoming MQTT messages
   */
  function onMessageArrived(message) {
    try {
      const topic = message.destinationName
      const payload = message.payloadString

      // Parse topic to extract train_id and message type
      handleMqttMessage(topic, payload)

    } catch (error) {
      console.error('Error processing MQTT message:', error)
    }
  }

  /**
   * Handle parsed MQTT messages
   */
  function handleMqttMessage(topic, payload) {
    // Parse topic to extract train_id and message type
    const topicParts = topic.split('/')
    try {
      if (topicParts[0] == "captnfoerdeareal")
      {
        const messageType = topicParts[2]
        if (messageHandler) {
          messageHandler({
            topic,
            trainId: '',
            messageType,
            data: payload,
            timestamp: Date.now()
          })
        }
        return
      }
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
    } catch (error) {
      console.error('Error handling MQTT message:', error)
    }
  }

  /**
   * Disconnect from MQTT broker
   */
  function disconnect() {
    if (mqttClient.value && isMqttConnected.value) {
      mqttClient.value.disconnect()
      isMqttConnected.value = false
      subscriptions.value.clear()
      console.log('🔌 MQTT client disconnected')
    }
  }

  /**
   * Subscribe to a specific MQTT topic
   */
  function subscribe(topic, qos = 1) {
    if (!mqttClient.value || !isMqttConnected.value) {
      console.warn('Cannot subscribe: MQTT client not connected')
      return false
    }

    try {
      mqttClient.value.subscribe(topic, {
        qos: qos,
        onSuccess: () => {
          subscriptions.value.add(topic)
          console.log(`✅ Subscribed to MQTT topic: ${topic}`)
        },
        onFailure: (error) => {
          console.error(`❌ Failed to subscribe to ${topic}:`, error)
        }
      })
      return true
    } catch (error) {
      console.error(`❌ Failed to subscribe to ${topic}:`, error)
      return false
    }
  }

  /**
   * Unsubscribe from a specific MQTT topic
   */
  function unsubscribe(topic) {
    if (!mqttClient.value || !isMqttConnected.value) {
      console.warn('Cannot unsubscribe: MQTT client not connected')
      return false
    }

    try {
      mqttClient.value.unsubscribe(topic, {
        onSuccess: () => {
          subscriptions.value.delete(topic)
          console.log(`🚫 Unsubscribed from MQTT topic: ${topic}`)
        },
        onFailure: (error) => {
          console.error(`❌ Failed to unsubscribe from ${topic}:`, error)
        }
      })
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
      "captnfoerdeareal/wan/CAU-8388"
    ]

    topics.forEach(topic => subscribe(topic))
  }

  /**
   * Unsubscribe from telemetry from a specific train
   */
  function unsubscribeFromTrain(trainId) {
    const topics = [
      `train/${trainId}/telemetry`,
      `captnfoerdeareal/wan/CAU-8388`
    ]

    topics.forEach(topic => unsubscribe(topic))
  }

  /**
   * Publish a message to MQTT broker
   */
  function publish(topic, messagePayload, qos = 1, retained = false) {
    if (!mqttClient.value || !isMqttConnected.value) {
      console.warn('Cannot publish: MQTT client not connected')
      return false
    }

    try {
      const payload = typeof messagePayload === 'string' ? messagePayload : JSON.stringify(messagePayload)

      const message = new Message(payload)
      message.destinationName = topic
      message.qos = qos
      message.retained = retained

      mqttClient.value.send(message)
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
      brokerConfig: brokerConfig,
      subscriptions: Array.from(subscriptions.value),
      subscriptionCount: subscriptions.value.size,
      clientId: mqttClient.value?.clientId || null,
      connectionType: 'Paho MQTT'
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

    // Publishing methods
    publish,
    sendCommandToTrain,

    // Utility methods
    getConnectionInfo,
    isConnected
  }
}

export default useMqttClient
