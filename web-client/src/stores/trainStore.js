import { defineStore } from 'pinia'
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useWebSocket } from '@/scripts/websocket'
import { useWebTransport } from '@/scripts/webtransport'
import { useWebRTC } from '@/scripts/webrtc'
import { useAssembler } from '@/scripts/assembler'
import { useNetworkSpeed } from '@/scripts/networkspeed'
import { useMqttClient } from '@/scripts/mqtt-paho'
import { useDataStorage } from '@/scripts/dataStorage'
import { SERVER_URL } from '@/scripts/config'


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
  notification: 21,
  download_start: 22,
  downloading: 23,
  download_end: 24,
  upload_start: 25,
  uploading: 26,
  upload_end: 27,
  rtt: 28,
  map_ack: 29,
  rtt_train: 30,
}


export const useTrainStore = defineStore('train', () => {
  const availableTrains = ref({})
  const selectedTrainId = ref('')
  const telemetryData = ref(null)
  const frameRef = ref(null)
  const remoteControlId = ref(null)
  const videoDatagramAssembler = ref(null)
  const keepaliveSequence = ref(0)
  const direction = ref('FORWARD')
  const isPoweredOn = ref(true)
  const router = useRouter()
  const download_start_time = ref(0)
  const download_end_time = ref(0)
  const total_downloaded_bytes = ref(0)
  const download_speed = ref(0)
  const upload_speed = ref(0)
  const networkspeed = ref(null)
  const telemetryHistory = ref([])

  // RTT measurements for clock offset calibration
  const rttMeasurements = ref([])
  const rttCalibrationInProgress = ref(false)
  const rttCalibrationCount = ref(10) // Number of RTT measurements to perform
  const rttCalibrationIndex = ref(0)
  const averageClockOffset = ref(0)

  const indexedDBStorageEnabled = ref(true)
  const commandCounter = ref(0)

  // Variables to calculate latency of last 30 frames
  const last30_latencyHistory = ref([])
  const last30_framesAverageLatency = ref(0)

  // Variables to calculate FPS of last 1 second
  const last1s_frameTimestamps = ref([])
  const last1s_framesFPS = ref(0)

  // Variables to calculate bandwidth used last 1 second
  const last1s_bytesHistory = ref([])
  const last1s_bandwidthMbps = ref(0)

  const {
    isWSConnected,
    connectWebSocket,
    sendWsCommand,
  } = useWebSocket(remoteControlId, handleWsMessage)

  const {
    isWTConnected,
    connectWebTransport,
    sendWtMessage,
  } = useWebTransport(remoteControlId, handleWtMessage)

  const {
    isRTCConnected,
    connectWebRTC,
  } = useWebRTC(remoteControlId, handleRtcMessage)

  const {
    isMqttConnected,
    connectMqtt,
    subscribeToTrain,
    unsubscribeFromTrain,
  } = useMqttClient(remoteControlId, handleMqttMessage)

  const dataStorage = useDataStorage("TrainDataStorage", 1)

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
      console.log('✅ Remote control ID initialized:', remoteControlId.value)
    }
  }
  async function fetchAvailableTrains() {
    try {
      const response = await fetch(`${SERVER_URL}/api/trains`)
      const data = await response.json()
      availableTrains.value = data
    } catch (error) {
      console.error('❌ Error fetching trains:', error)
    }
  }

  async function connectToServer() {
    await connectWebSocket()
    await connectWebTransport()
    await connectMqtt()  // Add MQTT connection

    try {
      await connectWebRTC()
      console.log('✅ WebRTC connection initiated')
    } catch (error) {
      console.error('❌ WebRTC connection failed:', error)
    }
    setInterval(sendKeepAliveWebTransport, 10000);
    networkspeed.value = new useNetworkSpeed(onNetworkSpeedCalculated)
  }

  async function mappingToTrain(trainId) {
    if (!trainId) return
    telemetryData.value = {}
    if (selectedTrainId.value !== trainId) {
      unsubscribeFromTrain(selectedTrainId.value)

      // also reset telemetry history
      telemetryHistory.value = []
    }
    selectedTrainId.value = trainId

    if (!videoDatagramAssembler.value) {
      videoDatagramAssembler.value = new useAssembler({
        maxFrames: 30,
        onFrameComplete: (completedFrame) => {
          frameRef.value = completedFrame.data
          if (indexedDBStorageEnabled.value) {
            // Store the frame data
            dataStorage.storeFrame({
              frameId: completedFrame.frameId,
              data: completedFrame.data,
              trainId: selectedTrainId.value,
              createdAt: completedFrame.created_at,
              receivedAt: completedFrame.received_at,
              latency: completedFrame.latency + averageClockOffset.value
            })
          }

          // Calculate average latency of last 30 frames
          if (last30_latencyHistory.value.length >= 30) {
            last30_latencyHistory.value.shift()
          }
          last30_latencyHistory.value.push(completedFrame.latency + averageClockOffset.value)
          const sumLatency = last30_latencyHistory.value.reduce((a, b) => a + b, 0)
          last30_framesAverageLatency.value = sumLatency / last30_latencyHistory.value.length

          // Calculate FPS over the last 1 second
          const currentTime = performance.now()
          last1s_frameTimestamps.value.push(currentTime)

          while (last1s_frameTimestamps.value.length > 0 && currentTime - last1s_frameTimestamps.value[0] > 1000) {
            last1s_frameTimestamps.value.shift()
          }
          last1s_framesFPS.value = last1s_frameTimestamps.value.length

          // Calculate bandwidth used over the last 1 second
          const frameSizeBytes = completedFrame.data.length
          last1s_bytesHistory.value.push({ timestamp: currentTime, size: frameSizeBytes })

          // Remove entries older than 1 second
          while (last1s_bytesHistory.value.length > 0 && currentTime - last1s_bytesHistory.value[0].timestamp > 1000) {
            last1s_bytesHistory.value.shift()
          }

          let totalBytes = last1s_bytesHistory.value.reduce((sum, entry) => sum + entry.size, 0)
          last1s_bandwidthMbps.value = (totalBytes * 8) / (1024 * 1024) // Convert to Mbps

        }
      })
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

        await response.json()
      } catch (error) {
        console.error('❌ Error assigning train to remote control:', error)
      }
    } else {
      console.error('Remote control ID is not initialized')
    }

    // Send a message through WebTransport to notify the server
    await sendWtMessage(`MAP_CONNECTION:${remoteControlId.value}:${trainId}`);

    // Subscribe to MQTT telemetry for this specific train
    subscribeToTrain(trainId)

    // Send multiple RTT messages to calibrate clock offset
    await performRTTCalibration()

    commandCounter.value = 0
  }

  async function performRTTCalibration() {
    console.log(`🔄 Starting RTT calibration with ${rttCalibrationCount.value} measurements...`)

    rttMeasurements.value = []
    rttCalibrationInProgress.value = true
    rttCalibrationIndex.value = 0

    // Send multiple RTT packets with delays between them
    for (let i = 0; i < rttCalibrationCount.value; i++) {
      rttCalibrationIndex.value = i + 1
      console.log(`📡 Sending RTT calibration packet ${i + 1}/${rttCalibrationCount.value}`)

      await sendRTT()

      // Wait 500ms between measurements to avoid overwhelming the connection
      if (i < rttCalibrationCount.value - 1) {
        await new Promise(resolve => setTimeout(resolve, 100))
      }
    }
  }

  function calculateAverageClockOffset() {
    if (rttMeasurements.value.length === 0) {
      console.warn('⚠️ No RTT measurements available for clock offset calculation')
      return
    }

    // Calculate average clock offset from all measurements
    const totalClockOffset = rttMeasurements.value.reduce((sum, measurement) => sum + measurement.clockOffset, 0)
    averageClockOffset.value = totalClockOffset / rttMeasurements.value.length
    averageClockOffset.value = Math.round(averageClockOffset.value)

    // Calculate statistics for analysis
    const roundTripTimes = rttMeasurements.value.map(m => m.roundTripTime)
    const avgRTT = roundTripTimes.reduce((sum, rtt) => sum + rtt, 0) / roundTripTimes.length
    const minRTT = Math.min(...roundTripTimes)
    const maxRTT = Math.max(...roundTripTimes)

    console.log(`📊 RTT Calibration Complete:`)
    console.log(`   Measurements: ${rttMeasurements.value.length}`)
    console.log(`   Average RTT: ${avgRTT.toFixed(1)} ms`)
    console.log(`   Min RTT: ${minRTT.toFixed(1)} ms`)
    console.log(`   Max RTT: ${maxRTT.toFixed(1)} ms`)
    console.log(`   Average Clock Offset: ${averageClockOffset.value.toFixed(1)} ms`)

    rttCalibrationInProgress.value = false
    console.log(`✅ Clock offset calibrated and set to: ${averageClockOffset.value.toFixed(1)} ms`)
  }

  async function sendCommand(command) {
    commandCounter.value += 1
    command["command_id"] = commandCounter.value
    command["remote_control_timestamp"] = Date.now()
    command["remote_control_id"] = remoteControlId.value

    switch (command.instruction) {
      case "POWER_ON": isPoweredOn.value = true; break
      case "POWER_OFF": isPoweredOn.value = false; break
      case "CHANGE_DIRECTION": direction.value = command.direction; break
    }

    // Convert command object to JSON and then to Uint8Array
    const jsonBytes = new TextEncoder().encode(JSON.stringify(command))
    const packet = new Uint8Array(1 + jsonBytes.length)
    packet[0] = PACKET_TYPE.command
    packet.set(jsonBytes, 1)

    try {
      // Try WebTransport first
      if (isWTConnected.value) {
        await sendWtMessage(packet)
        console.log('✅ Command sent via WebTransport')
      }
      // Fallback to WebSocket if WebTransport is not connected
      else if (isWSConnected.value) {
        sendWsCommand(packet)
        console.log('⚠️ Command sent via WebSocket (fallback)')
      } else {
        console.error('❌ Cannot send command: Neither WebTransport nor WebSocket is connected')
        throw new Error('No connection available to send command')
      }
    } catch (error) {
      console.error('❌ Command send error:', error)
    }
  }

  async function sendRTT() {
    console.log('Sending RTT packet to synchronize timestamps')
    const rttPacket = {
      type: "rtt",
      remote_control_timestamp: Date.now(),
      train_timestamp: 0
    };
    const packetData = new TextEncoder().encode(JSON.stringify(rttPacket));
    const packet = new Uint8Array(1 + packetData.length);
    packet[0] = PACKET_TYPE.rtt; // Set the first byte as PACKET_TYPE.rtt
    packet.set(packetData, 1);

    await sendWtMessage(packet)
  }

  async function sendRTT_Train(rttPacket) {
    console.log('📤 Sending RTT_Train packet:', rttPacket)
    const packetData = new TextEncoder().encode(JSON.stringify(rttPacket));
    const packet = new Uint8Array(1 + packetData.length);
    packet[0] = PACKET_TYPE.rtt_train; // Set the first byte as PACKET_TYPE.rtt_train
    packet.set(packetData, 1);

    console.log('📤 RTT_Train packet size:', packet.length, 'bytes')
    console.log('📤 RTT_Train packet type byte:', packet[0])
    
    try {
      await sendWtMessage(packet)
      console.log('✅ RTT_Train packet sent successfully')
    } catch (error) {
      console.error('❌ Failed to send RTT_Train packet:', error)
    }
  }

  async function handleWsMessage(packetType, payload) {
    switch (packetType) {
      case PACKET_TYPE.telemetry: {
        const jsonData =  JSON.parse(new TextDecoder().decode(payload))

        // get system timestamp
        const timestamp = Date.now()
        const latency = timestamp - jsonData.timestamp + averageClockOffset.value

        if (indexedDBStorageEnabled.value) {
          // Also store it to indexDB
          dataStorage.storeTelemetry({
            trainId: jsonData.train_id,
            data: jsonData,
            latency: latency,
          protocol: 'ws'
          })
        }

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
      case PACKET_TYPE.video: {
        videoDatagramAssembler.value.processPacket(payload)
        break
      }
    }
  }

  async function handleWtMessage(packetType, payload) {
    let jsonString = ""
    let jsonData = {}
    switch (packetType) {
      case PACKET_TYPE.telemetry: {
        try {
          jsonString = new TextDecoder().decode(payload)
          jsonData = JSON.parse(jsonString)

          // get system timestamp
          const timestamp = Date.now()
          const latency = timestamp - jsonData.timestamp + averageClockOffset.value

          if (indexedDBStorageEnabled.value) {
            // Also store it to indexDB
            dataStorage.storeTelemetry({
              trainId: jsonData.train_id,
              data: jsonData,
              latency: latency,
              protocol: 'wt'
            })
          }

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

        } catch (error) {
          console.error('❌ Error parsing telemetry data:', error)
        }
        break;
      }
      case PACKET_TYPE.video:
        videoDatagramAssembler.value.processPacket(payload)
        break
      case PACKET_TYPE.download_start: {
        download_start_time.value = performance.now()
        total_downloaded_bytes.value = payload.length + 1
        break
      }
      case PACKET_TYPE.downloading: {
        total_downloaded_bytes.value += payload.length + 1
        break
      }
      case PACKET_TYPE.download_end: {
        total_downloaded_bytes.value += payload.length + 1
        download_end_time.value = performance.now()
        const downloadDuration = (download_end_time.value - download_start_time.value) / 1000 // seconds
        const speedMbps = (total_downloaded_bytes.value * 8) / (1024 * 1024) / downloadDuration
        console.log(`Download speed calculated: ${speedMbps.toFixed(2)} Mbps`)
        break
      }
      case PACKET_TYPE.rtt: {
        try {
          jsonString = new TextDecoder().decode(payload)
          jsonData = JSON.parse(jsonString)

          // get system timestamp
          const currentTime = Date.now()
          const round_trip_time = currentTime - jsonData.remote_control_timestamp
          const one_way_latency = round_trip_time / 2
          const expected_train_receive_time = jsonData.remote_control_timestamp + one_way_latency
          const clock_offset = jsonData.train_timestamp - expected_train_receive_time + 30 // Adjust for processing time

          // Store this RTT measurement
          rttMeasurements.value.push({
            roundTripTime: round_trip_time,
            oneWayLatency: one_way_latency,
            clockOffset: clock_offset,
            remoteSentTime: jsonData.remote_control_timestamp,
            trainProcessedTime: jsonData.train_timestamp,
            remoteReceivedTime: currentTime
          })

          console.log(`📊 RTT Measurement ${rttMeasurements.value.length}/${rttCalibrationCount.value}:`)
          console.log(`   Round trip time: ${round_trip_time} ms`)
          console.log(`   One-way latency: ${one_way_latency.toFixed(1)} ms`)
          console.log(`   Clock offset: ${clock_offset.toFixed(1)} ms`)
        } catch (error) {
          console.error('❌ Error parsing RTT data:', error)
        }

        // If we've collected enough measurements, calculate the average
        if (rttMeasurements.value.length >= rttCalibrationCount.value) {
          calculateAverageClockOffset()
        }

        break
      }
      case PACKET_TYPE.rtt_train: {
        try {
          // Currently not used in the client
          console.log('📥 Received rtt_train packet from server: ', payload)
          jsonString = new TextDecoder().decode(payload)
          jsonData = JSON.parse(jsonString)
          console.log('📥 Parsed rtt_train data:', jsonData)
          jsonData["remote_control_timestamp"] = Date.now()
          jsonData["remote_control_id"] = remoteControlId.value
          console.log('📥 Updated rtt_train data with timestamp:', jsonData)
          await sendRTT_Train(jsonData)
        } catch (error) {
          console.error('❌ Error handling rtt_train packet:', error)
        }
        break
      }
    }
  }

  // Handler for WebRTC messages - reuses same logic as WebTransport
  function handleRtcMessage(packetType, payload) {
    // WebRTC uses the same packet format as WebTransport
    handleWtMessage(packetType, payload)
  }

  function handleMqttMessage(mqttMessage) {
    const { trainId, messageType, data } = mqttMessage

    switch (messageType) {
      case 'telemetry': {

        // get system timestamp
        const timestamp = Date.now()
        const latency = timestamp - data.timestamp + averageClockOffset.value

        if (indexedDBStorageEnabled.value) {
          // Also store it to indexDB
          dataStorage.storeTelemetry({
            trainId: trainId,
            data: data,
            latency: latency,
            protocol: 'mqtt'
          })
        }

        // Assign to telemetryData also Add to telemetry history
        telemetryData.value = data
        telemetryHistory.value.unshift({ ...data });

        // Update power and direction states
        if (data.status === 'running') {
          isPoweredOn.value = true
        } else {
          isPoweredOn.value = false
        }

        if (data.direction === 1) {
          direction.value = 'FORWARD'
        } else if (data.direction === -1) {
          direction.value = 'BACKWARD'
        }
        break
      }

      case 'status':
        console.log(`🔄 Train ${trainId} status update:`, data)
        // Handle status updates
        break

      case 'heartbeat':
        console.log(`💓 Train ${trainId} heartbeat:`, data)
        // Handle heartbeat messages
        break

      case 'onConnect':
        if (selectedTrainId.value) {
          subscribeToTrain(selectedTrainId.value)
        }
        break

      default:
        console.log(`❓ Unknown MQTT message type: ${messageType}`)
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

    sendWtMessage(packet)
  }

  async function onNetworkSpeedCalculated(downloadSpeed, uploadSpeed) {
    download_speed.value = downloadSpeed
    upload_speed.value = uploadSpeed
  }

  function setRTTCalibrationCount(count) {
    rttCalibrationCount.value = Math.max(1, Math.min(count, 20)) // Limit between 1 and 20
    console.log(`🔧 RTT calibration count set to: ${rttCalibrationCount.value}`)
  }

  return {
    availableTrains,
    selectedTrainId,
    telemetryData,
    frameRef,
    remoteControlId,
    isPoweredOn,
    direction,
    isWSConnected,
    isWTConnected,
    isRTCConnected,
    isMqttConnected,
    download_speed,
    upload_speed,
    networkspeed,
    telemetryHistory,
    rttCalibrationInProgress,
    rttMeasurements,
    rttCalibrationCount,
    last30_framesAverageLatency,
    last1s_framesFPS,
    last1s_bandwidthMbps,
    initializeRemoteControlId,
    fetchAvailableTrains,
    connectToServer,
    mappingToTrain,
    sendCommand,
    performRTTCalibration,
    setRTTCalibrationCount,
    // MQTT methods
    subscribeToTrain,
    unsubscribeFromTrain,
  }
})
