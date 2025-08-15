import Dexie from 'dexie'

/**
 * DataStorage - Simple utility for storing train data (frames, telemetry, sensor data) in IndexedDB
 * Uses Dexie.js for simplified IndexedDB operations
 */
class DataStorage {
  constructor(dbName = 'TrainDataStorage', version = 1) {
    // Initialize Dexie database
    this.db = new Dexie(dbName)
    
    // Define schema - can be extended for telemetry and sensor data
    this.db.version(version).stores({
      frames: '++id, frameId, timestamp, trainId, size, data, metadata',
      telemetry: '++id, timestamp, trainId, data, metadata',
      sensorData: '++id, sensorType, timestamp, trainId, data, metadata'
    })
    
    // Track storage stats
    this.stats = {
      totalFrames: 0,
      totalSize: 0,
      lastCleanup: Date.now()
    }
  }

  /**
   * Initialize the database connection
   */
  async init() {
    try {
      await this.db.open()
      console.log('✅ DataStorage initialized successfully')
      await this.updateStats()
    } catch (error) {
      console.error('❌ Failed to initialize DataStorage:', error)
      throw error
    }
  }

  /**
   * Store a single H.264 frame
   * @param {Object} frameData - Frame data object
   * @param {string} frameData.frameId - Unique frame identifier
   * @param {Uint8Array} frameData.data - Raw H.264 frame data
   * @param {string} frameData.trainId - Train identifier
   * @param {Object} frameData.metadata - Additional frame metadata
   */
  async storeFrame(frameData) {
    try {
      const frame = {
        frameId: frameData.frameId,
        timestamp: Date.now(),
        trainId: frameData.trainId || 'unknown',
        size: frameData.data.byteLength,
        data: frameData.data, // Dexie handles Uint8Array automatically
        metadata: frameData.metadata || {}
      }

      const id = await this.db.frames.add(frame)
      this.stats.totalFrames++
      this.stats.totalSize += frame.size

      console.log(`📦 Frame stored: ID=${id}, Size=${frame.size} bytes`)
      return id
    } catch (error) {
      console.error('❌ Failed to store frame:', error)
      throw error
    }
  }

  /**
   * Store telemetry data
   * @param {Object} telemetryData - Telemetry data object
   * @param {string} telemetryData.trainId - Train identifier
   * @param {Object} telemetryData.data - Telemetry data
   * @param {Object} telemetryData.metadata - Additional metadata
   */
  async storeTelemetry(telemetryData) {
    try {
      const telemetry = {
        timestamp: Date.now(),
        trainId: telemetryData.trainId || 'unknown',
        data: telemetryData.data,
        metadata: telemetryData.metadata || {}
      }

      const id = await this.db.telemetry.add(telemetry)
      console.log(`📊 Telemetry stored: ID=${id}`)
      return id
    } catch (error) {
      console.error('❌ Failed to store telemetry:', error)
      throw error
    }
  }

  /**
   * Store sensor data
   * @param {Object} sensorData - Sensor data object
   * @param {string} sensorData.sensorType - Type of sensor (imu, lidar, etc.)
   * @param {string} sensorData.trainId - Train identifier
   * @param {Object} sensorData.data - Sensor data
   * @param {Object} sensorData.metadata - Additional metadata
   */
  async storeSensorData(sensorData) {
    try {
      const sensor = {
        sensorType: sensorData.sensorType,
        timestamp: Date.now(),
        trainId: sensorData.trainId || 'unknown',
        data: sensorData.data,
        metadata: sensorData.metadata || {}
      }

      const id = await this.db.sensorData.add(sensor)
      console.log(`🔬 Sensor data stored: ID=${id}, Type=${sensor.sensorType}`)
      return id
    } catch (error) {
      console.error('❌ Failed to store sensor data:', error)
      throw error
    }
  }
  /**
   * Retrieve a frame by its ID
   * @param {number} id - Database ID of the frame
   */
  async getFrame(id) {
    try {
      const frame = await this.db.frames.get(id)
      if (frame) {
        console.log(`📥 Frame retrieved: ID=${id}, Size=${frame.size} bytes`)
      }
      return frame
    } catch (error) {
      console.error('❌ Failed to retrieve frame:', error)
      throw error
    }
  }

  /**
   * Retrieve telemetry by ID
   * @param {number} id - Database ID of the telemetry
   */
  async getTelemetry(id) {
    try {
      const telemetry = await this.db.telemetry.get(id)
      if (telemetry) {
        console.log(`📊 Telemetry retrieved: ID=${id}`)
      }
      return telemetry
    } catch (error) {
      console.error('❌ Failed to retrieve telemetry:', error)
      throw error
    }
  }

  /**
   * Retrieve sensor data by ID
   * @param {number} id - Database ID of the sensor data
   */
  async getSensorData(id) {
    try {
      const sensorData = await this.db.sensorData.get(id)
      if (sensorData) {
        console.log(`🔬 Sensor data retrieved: ID=${id}, Type=${sensorData.sensorType}`)
      }
      return sensorData
    } catch (error) {
      console.error('❌ Failed to retrieve sensor data:', error)
      throw error
    }
  }

  /**
   * Retrieve frames by train ID
   * @param {string} trainId - Train identifier
   * @param {number} limit - Maximum number of frames to retrieve (default: 100)
   */
  async getFramesByTrain(trainId, limit = 100) {
    try {
      const frames = await this.db.frames
        .where('trainId')
        .equals(trainId)
        .orderBy('timestamp')
        .limit(limit)
        .toArray()
      
      console.log(`📥 Retrieved ${frames.length} frames for train ${trainId}`)
      return frames
    } catch (error) {
      console.error('❌ Failed to retrieve frames by train:', error)
      throw error
    }
  }

  /**
   * Retrieve telemetry data by train ID
   * @param {string} trainId - Train identifier
   * @param {number} limit - Maximum number of records to retrieve (default: 100)
   */
  async getTelemetryByTrain(trainId, limit = 100) {
    try {
      const telemetry = await this.db.telemetry
        .where('trainId')
        .equals(trainId)
        .orderBy('timestamp')
        .limit(limit)
        .toArray()
      
      console.log(`📊 Retrieved ${telemetry.length} telemetry records for train ${trainId}`)
      return telemetry
    } catch (error) {
      console.error('❌ Failed to retrieve telemetry by train:', error)
      throw error
    }
  }

  /**
   * Retrieve sensor data by train ID and sensor type
   * @param {string} trainId - Train identifier
   * @param {string} sensorType - Type of sensor (optional)
   * @param {number} limit - Maximum number of records to retrieve (default: 100)
   */
  async getSensorDataByTrain(trainId, sensorType = null, limit = 100) {
    try {
      let query = this.db.sensorData.where('trainId').equals(trainId)
      
      if (sensorType) {
        query = query.and(item => item.sensorType === sensorType)
      }
      
      const sensorData = await query
        .orderBy('timestamp')
        .limit(limit)
        .toArray()
      
      console.log(`🔬 Retrieved ${sensorData.length} sensor records for train ${trainId}`)
      return sensorData
    } catch (error) {
      console.error('❌ Failed to retrieve sensor data by train:', error)
      throw error
    }
  }
  async getFramesByTimeRange(startTime, endTime) {
    try {
      const frames = await this.db.frames
        .where('timestamp')
        .between(startTime, endTime, true, true)
        .toArray()
      
      console.log(`📥 Retrieved ${frames.length} frames in time range`)
      return frames
    } catch (error) {
      console.error('❌ Failed to retrieve frames by time range:', error)
      throw error
    }
  }

  /**
   * Delete a frame by ID
   * @param {number} id - Database ID of the frame
   */
  async deleteFrame(id) {
    try {
      await this.db.frames.delete(id)
      console.log(`🗑️ Frame deleted: ID=${id}`)
    } catch (error) {
      console.error('❌ Failed to delete frame:', error)
      throw error
    }
  }

  /**
   * Delete all frames for a specific train
   * @param {string} trainId - Train identifier
   */
  async deleteFramesByTrain(trainId) {
    try {
      const count = await this.db.frames.where('trainId').equals(trainId).delete()
      console.log(`🗑️ Deleted ${count} frames for train ${trainId}`)
      await this.updateStats()
      return count
    } catch (error) {
      console.error('❌ Failed to delete frames by train:', error)
      throw error
    }
  }

  /**
   * Delete all data for a specific train (frames, telemetry, sensor data)
   * @param {string} trainId - Train identifier
   */
  async deleteAllDataByTrain(trainId) {
    try {
      const frameCount = await this.db.frames.where('trainId').equals(trainId).delete()
      const telemetryCount = await this.db.telemetry.where('trainId').equals(trainId).delete()
      const sensorCount = await this.db.sensorData.where('trainId').equals(trainId).delete()
      
      console.log(`🗑️ Deleted all data for train ${trainId}: ${frameCount} frames, ${telemetryCount} telemetry, ${sensorCount} sensor records`)
      await this.updateStats()
      return { frameCount, telemetryCount, sensorCount }
    } catch (error) {
      console.error('❌ Failed to delete all data by train:', error)
      throw error
    }
  }

  /**
   * Delete telemetry data for a specific train
   * @param {string} trainId - Train identifier
   */
  async deleteTelemetryByTrain(trainId) {
    try {
      const count = await this.db.telemetry.where('trainId').equals(trainId).delete()
      console.log(`🗑️ Deleted ${count} telemetry records for train ${trainId}`)
      return count
    } catch (error) {
      console.error('❌ Failed to delete telemetry by train:', error)
      throw error
    }
  }

  /**
   * Delete sensor data for a specific train
   * @param {string} trainId - Train identifier
   * @param {string} sensorType - Type of sensor (optional)
   */
  async deleteSensorDataByTrain(trainId, sensorType = null) {
    try {
      let query = this.db.sensorData.where('trainId').equals(trainId)
      
      if (sensorType) {
        query = query.and(item => item.sensorType === sensorType)
      }
      
      const count = await query.delete()
      console.log(`🗑️ Deleted ${count} sensor records for train ${trainId}`)
      return count
    } catch (error) {
      console.error('❌ Failed to delete sensor data by train:', error)
      throw error
    }
  }
  /**
   * Clean up old data (older than specified hours)
   * @param {number} hoursOld - Age threshold in hours (default: 24)
   */
  async cleanupOldData(hoursOld = 24) {
    try {
      const cutoffTime = Date.now() - (hoursOld * 60 * 60 * 1000)
      
      const frameCount = await this.db.frames.where('timestamp').below(cutoffTime).delete()
      const telemetryCount = await this.db.telemetry.where('timestamp').below(cutoffTime).delete()
      const sensorCount = await this.db.sensorData.where('timestamp').below(cutoffTime).delete()
      
      console.log(`🧹 Cleaned up old data (older than ${hoursOld} hours): ${frameCount} frames, ${telemetryCount} telemetry, ${sensorCount} sensor records`)
      await this.updateStats()
      this.stats.lastCleanup = Date.now()
      return { frameCount, telemetryCount, sensorCount }
    } catch (error) {
      console.error('❌ Failed to cleanup old data:', error)
      throw error
    }
  }

  /**
   * Get storage statistics
   */
  async getStats() {
    await this.updateStats()
    return {
      ...this.stats,
      totalSizeMB: (this.stats.totalSize / (1024 * 1024)).toFixed(2)
    }
  }

  /**
   * Update internal statistics
   */
  async updateStats() {
    try {
      this.stats.totalFrames = await this.db.frames.count()
      
      // Calculate total size (only frames have size data)
      const frames = await this.db.frames.toArray()
      this.stats.totalSize = frames.reduce((total, frame) => total + frame.size, 0)
    } catch (error) {
      console.error('❌ Failed to update stats:', error)
    }
  }

  /**
   * Clear all stored data (frames, telemetry, sensor data)
   */
  async clearAll() {
    try {
      await this.db.frames.clear()
      await this.db.telemetry.clear()
      await this.db.sensorData.clear()
      this.stats.totalFrames = 0
      this.stats.totalSize = 0
      console.log('🗑️ All data cleared')
    } catch (error) {
      console.error('❌ Failed to clear all data:', error)
      throw error
    }
  }

  /**
   * Close the database connection
   */
  async close() {
    try {
      this.db.close()
      console.log('✅ DataStorage connection closed')
    } catch (error) {
      console.error('❌ Failed to close DataStorage:', error)
    }
  }
}

// Export a composable function for Vue 3
export function useDataStorage(dbName, version) {
  const dataStorage = new DataStorage(dbName, version)
  
  return {
    // Database operations
    init: () => dataStorage.init(),
    
    // Frame operations
    storeFrame: (frameData) => dataStorage.storeFrame(frameData),
    getFrame: (id) => dataStorage.getFrame(id),
    getFramesByTrain: (trainId, limit) => dataStorage.getFramesByTrain(trainId, limit),
    getFramesByTimeRange: (start, end) => dataStorage.getFramesByTimeRange(start, end),
    deleteFrame: (id) => dataStorage.deleteFrame(id),
    deleteFramesByTrain: (trainId) => dataStorage.deleteFramesByTrain(trainId),
    
    // Telemetry operations
    storeTelemetry: (telemetryData) => dataStorage.storeTelemetry(telemetryData),
    getTelemetry: (id) => dataStorage.getTelemetry(id),
    getTelemetryByTrain: (trainId, limit) => dataStorage.getTelemetryByTrain(trainId, limit),
    deleteTelemetryByTrain: (trainId) => dataStorage.deleteTelemetryByTrain(trainId),
    
    // Sensor data operations
    storeSensorData: (sensorData) => dataStorage.storeSensorData(sensorData),
    getSensorData: (id) => dataStorage.getSensorData(id),
    getSensorDataByTrain: (trainId, sensorType, limit) => dataStorage.getSensorDataByTrain(trainId, sensorType, limit),
    deleteSensorDataByTrain: (trainId, sensorType) => dataStorage.deleteSensorDataByTrain(trainId, sensorType),
    
    // General management operations
    deleteAllDataByTrain: (trainId) => dataStorage.deleteAllDataByTrain(trainId),
    cleanupOldData: (hours) => dataStorage.cleanupOldData(hours),
    clearAll: () => dataStorage.clearAll(),
    
    // Utility operations
    getStats: () => dataStorage.getStats(),
    close: () => dataStorage.close(),
    
    // Direct access to the storage instance if needed
    storage: dataStorage
  }
}

// Export the class as well for direct usage
export { DataStorage }
