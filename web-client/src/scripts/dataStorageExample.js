/**
 * Example usage of DataStorage with TrainStore
 * This file demonstrates how to integrate data storage into your existing application
 */

import { useDataStorage } from './dataStorage'

// Example integration with your existing train store
export function useDataStorageIntegration() {
  // Initialize data storage
  const dataStorage = useDataStorage('TrainDataStorage', 1)
  
  // Initialize the storage when needed
  const initStorage = async () => {
    try {
      await dataStorage.init()
      console.log('✅ Data storage ready')
      
      // Optional: Set up automatic cleanup (run every hour)
      setInterval(async () => {
        await dataStorage.cleanupOldData(24) // Keep data for 24 hours
      }, 60 * 60 * 1000) // Run every hour
      
    } catch (error) {
      console.error('❌ Failed to initialize data storage:', error)
    }
  }

  // Store a frame from your video assembler
  const storeVideoFrame = async (frameData, trainId) => {
    try {
      const frameInfo = {
        frameId: `frame_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
        data: frameData, // Your Uint8Array H.264 data
        trainId: trainId,
        metadata: {
          source: 'video_assembler',
          protocol: 'webtransport',
          timestamp: Date.now()
        }
      }
      
      const id = await dataStorage.storeFrame(frameInfo)
      return id
    } catch (error) {
      console.error('❌ Failed to store video frame:', error)
    }
  }

  // Store telemetry data
  const storeTelemetryData = async (telemetryData, trainId) => {
    try {
      const telemetryInfo = {
        trainId: trainId,
        data: telemetryData,
        metadata: {
          source: 'mqtt',
          protocol: 'mqtt',
          timestamp: Date.now()
        }
      }
      
      const id = await dataStorage.storeTelemetry(telemetryInfo)
      return id
    } catch (error) {
      console.error('❌ Failed to store telemetry data:', error)
    }
  }

  // Store sensor data (IMU, LiDAR, etc.)
  const storeSensorData = async (sensorType, sensorData, trainId) => {
    try {
      const sensorInfo = {
        sensorType: sensorType, // 'imu', 'lidar', etc.
        trainId: trainId,
        data: sensorData,
        metadata: {
          source: 'sensor',
          protocol: 'webtransport',
          timestamp: Date.now()
        }
      }
      
      const id = await dataStorage.storeSensorData(sensorInfo)
      return id
    } catch (error) {
      console.error('❌ Failed to store sensor data:', error)
    }
  }

  // Get frames for playback or analysis
  const getTrainFrames = async (trainId, limit = 50) => {
    try {
      return await dataStorage.getFramesByTrain(trainId, limit)
    } catch (error) {
      console.error('❌ Failed to get train frames:', error)
      return []
    }
  }

  // Get telemetry history
  const getTrainTelemetry = async (trainId, limit = 100) => {
    try {
      return await dataStorage.getTelemetryByTrain(trainId, limit)
    } catch (error) {
      console.error('❌ Failed to get train telemetry:', error)
      return []
    }
  }

  // Get sensor data
  const getTrainSensorData = async (trainId, sensorType = null, limit = 100) => {
    try {
      return await dataStorage.getSensorDataByTrain(trainId, sensorType, limit)
    } catch (error) {
      console.error('❌ Failed to get train sensor data:', error)
      return []
    }
  }

  // Get storage statistics for monitoring
  const getStorageInfo = async () => {
    try {
      const stats = await dataStorage.getStats()
      console.log('📊 Storage Stats:', {
        totalFrames: stats.totalFrames,
        totalSizeMB: stats.totalSizeMB,
        lastCleanup: new Date(stats.lastCleanup).toLocaleString()
      })
      return stats
    } catch (error) {
      console.error('❌ Failed to get storage stats:', error)
      return null
    }
  }

  return {
    initStorage,
    storeVideoFrame,
    storeTelemetryData,
    storeSensorData,
    getTrainFrames,
    getTrainTelemetry,
    getTrainSensorData,
    getStorageInfo,
    dataStorage // Direct access to all storage methods
  }
}

// Example usage in your trainStore.js:
/*
import { useDataStorageIntegration } from '@/scripts/frameStorageExample'

// In your store setup:
const { initStorage, storeVideoFrame, storeTelemetryData, storeSensorData } = useDataStorageIntegration()

// Initialize storage when connecting to server
async function connectToServer() {
  await connectWebSocket()
  await connectWebTransport()
  await connectMqtt()
  await initStorage() // Add this line
  setInterval(sendKeepAliveWebTransport, 10000)
  networkspeed.value = new useNetworkSpeed(onNetworkSpeedCalculated)
}

// Store frames when they're complete in your assembler
const videoDatagramAssembler = new useAssembler({
  maxFrames: 30,
  onFrameComplete: async (completedFrame) => {
    frameRef.value = completedFrame.data
    recordFrameLatency(completedFrame.frameId, completedFrame.latency, completedFrame.created_at)
    
    // Store the frame data
    await storeVideoFrame(completedFrame.data, selectedTrainId.value)
  }
})

// Store telemetry data in MQTT handler
function handleMqttMessage(mqttMessage) {
  const { trainId, messageType, data } = mqttMessage

  switch (messageType) {
    case 'telemetry': {
      // ... existing telemetry handling ...
      
      // Store telemetry to IndexedDB
      storeTelemetryData(data, trainId)
      break
    }
  }
}

// Store sensor data when received
function handleWtMessage(packetType, payload) {
  switch (packetType) {
    case PACKET_TYPE.imu:
      const imuData = JSON.parse(new TextDecoder().decode(payload))
      storeSensorData('imu', imuData, selectedTrainId.value)
      break
      
    case PACKET_TYPE.lidar:
      const lidarData = JSON.parse(new TextDecoder().decode(payload))
      storeSensorData('lidar', lidarData, selectedTrainId.value)
      break
  }
}
*/
