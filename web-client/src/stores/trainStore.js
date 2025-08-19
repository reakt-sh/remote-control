import { defineStore } from 'pinia'
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useWebSocket } from '@/scripts/websocket'
import { useWebTransport } from '@/scripts/webtransport'
import { useAssembler } from '@/scripts/assembler'
import { useNetworkSpeed } from '@/scripts/networkspeed'
import { useMqttClient } from '@/scripts/mqtt-paho'
import { useLatencyTracker } from '@/scripts/latencyTracker'
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

  const {
    isWSConnected,
    connectWebSocket,
  } = useWebSocket(remoteControlId, handleWsMessage)

  const {
    isWTConnected,
    connectWebTransport,
    sendWtMessage,
  } = useWebTransport(remoteControlId, handleWtMessage)

  const {
    isMqttConnected,
    connectMqtt,
    subscribeToTrain,
    unsubscribeFromTrain,
  } = useMqttClient(remoteControlId, handleMqttMessage)

  const {
    recordFrameLatency,
    recordLatency,
    exportToJson,
    clearData,
    setClockOffset,
  } = useLatencyTracker()

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

      // also reset latency data
      clearData()
    }
    selectedTrainId.value = trainId

    if (!videoDatagramAssembler.value) {
      videoDatagramAssembler.value = new useAssembler({
        maxFrames: 30,
        onFrameComplete: (completedFrame) => {
          frameRef.value = completedFrame.data
          recordFrameLatency(completedFrame.frameId, completedFrame.latency, completedFrame.created_at)
          // Store the frame data
          dataStorage.storeFrame({
            frameId: completedFrame.frameId,
            data: completedFrame.data,
            trainId: selectedTrainId.value,
            createdAt: completedFrame.created_at,
            latency: completedFrame.latency
          })
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
    const averageClockOffset = totalClockOffset / rttMeasurements.value.length

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
    console.log(`   Average Clock Offset: ${averageClockOffset.toFixed(1)} ms`)

    // Set the calibrated clock offset
    setClockOffset(averageClockOffset)

    rttCalibrationInProgress.value = false
    console.log(`✅ Clock offset calibrated and set to: ${averageClockOffset.toFixed(1)} ms`)
  }

  async function sendCommand(command) {
    switch (command.instruction) {
      case "POWER_ON": isPoweredOn.value = true; break
      case "POWER_OFF": isPoweredOn.value = false; break
      case "CHANGE_DIRECTION": direction.value = command.direction; break
    }

    // Convert command object to JSON and then to Uint8Array
    const jsonBytes = new TextEncoder().encode(JSON.stringify(command))
    try {
      const packet = new Uint8Array(1 + jsonBytes.length)
      packet[0] = PACKET_TYPE.command
      packet.set(jsonBytes, 1)
      await sendWtMessage(packet)
    } catch (error) {
      console.error('Command send error:', error)
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

  async function handleWsMessage(packetType, payload) {
    switch (packetType) {
      case PACKET_TYPE.telemetry: {
        const jsonData =  JSON.parse(new TextDecoder().decode(payload))

        // get system timestamp
        const timestamp = Date.now()
        const latency = timestamp - jsonData.timestamp

        // Record latency data
        recordLatency('websocket', latency, jsonData.sequence_number, jsonData.timestamp)

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

          // get system timestamp
          const timestamp = Date.now()
          const latency = timestamp - jsonData.timestamp

          // Record latency data
          recordLatency('webtransport', latency, jsonData.sequence_number, jsonData.timestamp)

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

          break;
        } catch (error) {
          console.error('❌ Error parsing telemetry data:', error)
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

        // If we've collected enough measurements, calculate the average
        if (rttMeasurements.value.length >= rttCalibrationCount.value) {
          calculateAverageClockOffset()
        }

        break
      }
    }
  }

  function handleMqttMessage(mqttMessage) {
    const { trainId, messageType, data } = mqttMessage

    switch (messageType) {
      case 'telemetry': {

        // get system timestamp
        const timestamp = Date.now()
        const latency = timestamp - data.timestamp

        // Record latency data
        recordLatency('mqtt', latency, data.sequence_number, data.timestamp)

        // Also store it to indexDB
        dataStorage.storeTelemetry({
          trainId: trainId,
          data: data,
          createdAt: timestamp,
          latency: latency,
          sequenceNumber: data.sequence_number
        })

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

  /**
   * Export video frames from the selected train as H.264 file
   */
  async function exportVideo() {
    try {
      if (!selectedTrainId.value) {
        alert('Please select a train first before exporting video.')
        return false
      }

      console.log(`🎬 Starting video export for train ${selectedTrainId.value}...`)

      // Get all frames for the selected train
      const frames = await dataStorage.getAllFramesByTrain(selectedTrainId.value)

      if (frames.length === 0) {
        alert('No video frames found for the selected train. Please wait for some video data to be received.')
        return false
      }

      console.log(`📦 Found ${frames.length} frames for train ${selectedTrainId.value}`)

      // Sort frames by timestamp to ensure correct order
      frames.sort((a, b) => a.timestamp - b.timestamp)

      // Calculate total size for progress tracking
      const totalSize = frames.reduce((total, frame) => total + frame.data.byteLength, 0)
      console.log(`📊 Total video data size: ${(totalSize / (1024 * 1024)).toFixed(2)} MB`)

      // Merge all frame data into a single Uint8Array
      const mergedData = new Uint8Array(totalSize)
      let offset = 0

      for (const frame of frames) {
        mergedData.set(new Uint8Array(frame.data), offset)
        offset += frame.data.byteLength
      }

      console.log(`✅ Merged ${frames.length} frames into single H.264 file`)

      // Create blob and download
      const blob = new Blob([mergedData], { type: 'video/h264' })
      const url = window.URL.createObjectURL(blob)

      const link = document.createElement('a')
      link.style.display = 'none'
      link.href = url
      const timestamp = new Date().toISOString().replace(/[:.]/g, '-').split('T')[0] + '_' + new Date().toISOString().replace(/[:.]/g, '-').split('T')[1].split('.')[0]
      link.download = `Train_${timestamp}_${selectedTrainId.value}_video.h264`

      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)

      // Clean up the URL object
      window.URL.revokeObjectURL(url)

      console.log(`🎉 Video export completed: Train_${timestamp}_${selectedTrainId.value}_video.h264`)
      return true

    } catch (error) {
      console.error('❌ Failed to export video:', error)
      alert('Failed to export video. Please check the console for details.')
      return false
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
    isMqttConnected,
    download_speed,
    upload_speed,
    networkspeed,
    telemetryHistory,
    rttCalibrationInProgress,
    rttMeasurements,
    rttCalibrationCount,
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
    // Latency tracking
    exportToJson,
    // Video export
    exportVideo
  }
})
