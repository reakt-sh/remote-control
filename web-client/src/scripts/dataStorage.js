import Dexie from 'dexie'

/**
 * DataStorage - Hierarchical utility for storing train data (frames, telemetry, sensor data) in IndexedDB
 * Structure: TrainDataStorage -> train_id -> {frames, sensorData, telemetry}
 * Uses Dexie.js for simplified IndexedDB operations
 */
class DataStorage {
  constructor(baseDbName = 'TrainDataStorage', version = 1) {
    this.baseDbName = baseDbName
    this.version = version
    this.trainDatabases = new Map() // Cache for train-specific databases

    // Track storage stats across all trains
    this.stats = {
      totalFrames: 0,
      totalSize: 0,
      lastCleanup: Date.now(),
      trainCount: 0
    }
  }

  /**
   * Get or create a database for a specific train
   * @param {string} trainId - Train identifier
   */
  async getTrainDatabase(trainId) {
    if (!trainId) {
      throw new Error('Train ID is required')
    }

    // Check if database is already cached
    if (this.trainDatabases.has(trainId)) {
      return this.trainDatabases.get(trainId)
    }

    // Create new database for this train
    const dbName = `${this.baseDbName}_${trainId}`
    const db = new Dexie(dbName)

    // Define schema without trainId since each train has its own database
    db.version(this.version).stores({
      frames: '++id, frameId, timestamp, size, data, metadata, createdAt, latency',
      telemetry: '++id, timestamp, sequence_number, data, metadata',
      sensorData: '++id, sensorType, timestamp, data, metadata'
    })

    try {
      await db.open()
      this.trainDatabases.set(trainId, db)
      console.log(`✅ Train database initialized for ${trainId}: ${dbName}`)
      return db
    } catch (error) {
      console.error(`❌ Failed to initialize database for train ${trainId}:`, error)
      throw error
    }
  }

  /**
   * Initialize the storage system
   */
  async init() {
    try {
      console.log('✅ DataStorage system initialized successfully')
      await this.updateStats()
    } catch (error) {
      console.error('❌ Failed to initialize DataStorage:', error)
      throw error
    }
  }

  /**
   * Get list of all train databases
   */
  async getAvailableTrains() {
    try {
      const databases = await Dexie.getDatabaseNames()
      const trainIds = databases
        .filter(name => name.startsWith(this.baseDbName + '_'))
        .map(name => name.replace(this.baseDbName + '_', ''))

      console.log(`📋 Found ${trainIds.length} train databases:`, trainIds)
      return trainIds
    } catch (error) {
      console.error('❌ Failed to get available trains:', error)
      return []
    }
  }

  /**
   * Get detailed metadata for available recorded trains
   */
  async getRecordedTrainsMetadata() {
    try {
      const trainIds = await this.getAvailableTrains()
      const metadata = []

      for (const trainId of trainIds) {
        try {
          const db = await this.getTrainDatabase(trainId)
          const frameCount = await db.frames.count()
          const telemetryCount = await db.telemetry.count()
          const sensorCount = await db.sensorData.count()

          // Get first and last timestamps
          const firstFrame = await db.frames.orderBy('timestamp').first()
          const lastFrame = await db.frames.orderBy('timestamp').last()
          const firstTelemetry = await db.telemetry.orderBy('timestamp').first()
          const lastTelemetry = await db.telemetry.orderBy('timestamp').last()

          // Calculate data range
          const startTime = Math.min(
            firstFrame?.timestamp || Infinity,
            firstTelemetry?.timestamp || Infinity
          )
          const endTime = Math.max(
            lastFrame?.timestamp || 0,
            lastTelemetry?.timestamp || 0
          )

          // Calculate total size
          const frames = await db.frames.toArray()
          const totalSize = frames.reduce((total, frame) => total + frame.size, 0)

          metadata.push({
            trainId,
            frameCount,
            telemetryCount,
            sensorCount,
            totalSize,
            totalSizeMB: (totalSize / (1024 * 1024)).toFixed(2),
            startTime: startTime === Infinity ? null : startTime,
            endTime: endTime === 0 ? null : endTime,
            duration: (startTime !== Infinity && endTime !== 0) ? endTime - startTime : 0,
            lastUpdated: Math.max(lastFrame?.timestamp || 0, lastTelemetry?.timestamp || 0)
          })
        } catch (error) {
          console.warn(`⚠️ Failed to get metadata for train ${trainId}:`, error)
        }
      }

      return metadata.sort((a, b) => (b.lastUpdated || 0) - (a.lastUpdated || 0))
    } catch (error) {
      console.error('❌ Failed to get recorded trains metadata:', error)
      return []
    }
  }

  /**
   * Store a single H.264 frame
   * @param {Object} frameData - Frame data object
   * @param {string} frameData.frameId - Unique frame identifier
   * @param {Uint8Array} frameData.data - Raw H.264 frame data
   * @param {string} frameData.trainId - Train identifier
   * @param {number} frameData.createdAt - Creation timestamp
   * @param {number} frameData.latency - Frame latency
   * @param {Object} frameData.metadata - Additional frame metadata
   */
  async storeFrame(frameData) {
    try {
      if (!frameData.trainId) {
        throw new Error('Train ID is required for storing frames')
      }

      const db = await this.getTrainDatabase(frameData.trainId)

      const frame = {
        frameId: frameData.frameId,
        timestamp: Date.now(),
        size: frameData.data.byteLength,
        data: frameData.data, // Dexie handles Uint8Array automatically
        createdAt: frameData.createdAt || Date.now(),
        latency: frameData.latency || 0,
        metadata: frameData.metadata || {}
      }

      const id = await db.frames.add(frame)
      this.stats.totalFrames++
      this.stats.totalSize += frame.size

      console.log(`📦 Frame stored for train ${frameData.trainId}: ID=${id}, Size=${frame.size} bytes`)
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
   * @param {number} telemetryData.sequence_number - Sequence number
   * @param {Object} telemetryData.data - Telemetry data
   * @param {Object} telemetryData.metadata - Additional metadata
   */
  async storeTelemetry(telemetryData) {
    try {
      if (!telemetryData.trainId) {
        throw new Error('Train ID is required for storing telemetry')
      }

      const db = await this.getTrainDatabase(telemetryData.trainId)

      // check if this telemetry data is already stored
      // find existing telemetry data by sequence id in indexedDB (trainId is implicit since each train has its own DB)
      const existingTelemetry = await db.telemetry
        .where('sequence_number')
        .equals(telemetryData.data.sequence_number)
        .first()

      if (existingTelemetry) {
        existingTelemetry[telemetryData.protocol] = telemetryData.latency
        await db.telemetry.put(existingTelemetry)
        return existingTelemetry.id
      }

      const telemetry = {
        timestamp: Date.now(),
        sequence_number: telemetryData.data.sequence_number,
        data: telemetryData.data,
        metadata: telemetryData.metadata || {},
        mqtt: null,
        wt: null,
        ws: null
      }

      // update with new protocol and latency data
      telemetry[telemetryData.protocol] = telemetryData.latency

      const id = await db.telemetry.add(telemetry)
      console.log(`📊 Telemetry stored for train ${telemetryData.trainId}: ID=${id}`)
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
      if (!sensorData.trainId) {
        throw new Error('Train ID is required for storing sensor data')
      }

      const db = await this.getTrainDatabase(sensorData.trainId)

      const sensor = {
        sensorType: sensorData.sensorType,
        timestamp: Date.now(),
        data: sensorData.data,
        metadata: sensorData.metadata || {}
      }

      const id = await db.sensorData.add(sensor)
      console.log(`🔬 Sensor data stored for train ${sensorData.trainId}: ID=${id}, Type=${sensor.sensorType}`)
      return id
    } catch (error) {
      console.error('❌ Failed to store sensor data:', error)
      throw error
    }
  }
  /**
   * Retrieve a frame by its ID
   * @param {string} trainId - Train identifier
   * @param {number} id - Database ID of the frame
   */
  async getFrame(trainId, id) {
    try {
      if (!trainId) {
        throw new Error('Train ID is required for retrieving frames')
      }

      const db = await this.getTrainDatabase(trainId)
      const frame = await db.frames.get(id)
      if (frame) {
        console.log(`📥 Frame retrieved for train ${trainId}: ID=${id}, Size=${frame.size} bytes`)
      }
      return frame
    } catch (error) {
      console.error('❌ Failed to retrieve frame:', error)
      throw error
    }
  }

  /**
   * Retrieve telemetry by ID
   * @param {string} trainId - Train identifier
   * @param {number} id - Database ID of the telemetry
   */
  async getTelemetry(trainId, id) {
    try {
      if (!trainId) {
        throw new Error('Train ID is required for retrieving telemetry')
      }

      const db = await this.getTrainDatabase(trainId)
      const telemetry = await db.telemetry.get(id)
      if (telemetry) {
        console.log(`📊 Telemetry retrieved for train ${trainId}: ID=${id}`)
      }
      return telemetry
    } catch (error) {
      console.error('❌ Failed to retrieve telemetry:', error)
      throw error
    }
  }

  /**
   * Retrieve sensor data by ID
   * @param {string} trainId - Train identifier
   * @param {number} id - Database ID of the sensor data
   */
  async getSensorData(trainId, id) {
    try {
      if (!trainId) {
        throw new Error('Train ID is required for retrieving sensor data')
      }

      const db = await this.getTrainDatabase(trainId)
      const sensorData = await db.sensorData.get(id)
      if (sensorData) {
        console.log(`🔬 Sensor data retrieved for train ${trainId}: ID=${id}, Type=${sensorData.sensorType}`)
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
      if (!trainId) {
        throw new Error('Train ID is required')
      }

      const db = await this.getTrainDatabase(trainId)
      const frames = await db.frames
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
   * Retrieve all frames by train ID (no limit)
   * @param {string} trainId - Train identifier
   */
  async getAllFramesByTrain(trainId) {
    try {
      if (!trainId) {
        throw new Error('Train ID is required')
      }

      const db = await this.getTrainDatabase(trainId)
      const frames = await db.frames
        .orderBy('timestamp')
        .toArray()

      console.log(`📥 Retrieved all ${frames.length} frames for train ${trainId}`)
      return frames
    } catch (error) {
      console.error('❌ Failed to retrieve all frames by train:', error)
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
      if (!trainId) {
        throw new Error('Train ID is required')
      }

      const db = await this.getTrainDatabase(trainId)
      const telemetry = await db.telemetry
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
   * Retrieve all telemetry data by train ID (no limit)
   * @param {string} trainId - Train identifier
   */
  async getAllTelemetryByTrain(trainId) {
    try {
      if (!trainId) {
        throw new Error('Train ID is required')
      }

      const db = await this.getTrainDatabase(trainId)
      const telemetry = await db.telemetry
        .orderBy('timestamp')
        .toArray()

      console.log(`📊 Retrieved all ${telemetry.length} telemetry records for train ${trainId}`)
      return telemetry
    } catch (error) {
      console.error('❌ Failed to retrieve all telemetry by train:', error)
      throw error
    }
  }

  /**
   * Retrieve telemetry data by time range for a specific train
   * @param {string} trainId - Train identifier
   * @param {number} startTime - Start timestamp
   * @param {number} endTime - End timestamp
   */
  async getTelemetryByTimeRange(trainId, startTime, endTime) {
    try {
      if (!trainId) {
        throw new Error('Train ID is required')
      }

      const db = await this.getTrainDatabase(trainId)
      const telemetry = await db.telemetry
        .where('timestamp')
        .between(startTime, endTime, true, true)
        .toArray()

      console.log(`📊 Retrieved ${telemetry.length} telemetry records in time range for train ${trainId}`)
      return telemetry
    } catch (error) {
      console.error('❌ Failed to retrieve telemetry by time range:', error)
      throw error
    }
  }

  /**
   * Retrieve sensor data by time range for a specific train
   * @param {string} trainId - Train identifier
   * @param {number} startTime - Start timestamp
   * @param {number} endTime - End timestamp
   * @param {string} sensorType - Type of sensor (optional)
   */
  async getSensorDataByTimeRange(trainId, startTime, endTime, sensorType = null) {
    try {
      if (!trainId) {
        throw new Error('Train ID is required')
      }

      const db = await this.getTrainDatabase(trainId)
      let query = db.sensorData.where('timestamp').between(startTime, endTime, true, true)

      if (sensorType) {
        query = query.and(item => item.sensorType === sensorType)
      }

      const sensorData = await query.toArray()

      console.log(`🔬 Retrieved ${sensorData.length} sensor records in time range for train ${trainId}`)
      return sensorData
    } catch (error) {
      console.error('❌ Failed to retrieve sensor data by time range:', error)
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
      if (!trainId) {
        throw new Error('Train ID is required')
      }

      const db = await this.getTrainDatabase(trainId)
      let query = db.sensorData

      if (sensorType) {
        query = query.where('sensorType').equals(sensorType)
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
  /**
   * Retrieve frames by time range for a specific train
   * @param {string} trainId - Train identifier
   * @param {number} startTime - Start timestamp
   * @param {number} endTime - End timestamp
   */
  async getFramesByTimeRange(trainId, startTime, endTime) {
    try {
      if (!trainId) {
        throw new Error('Train ID is required')
      }

      const db = await this.getTrainDatabase(trainId)
      const frames = await db.frames
        .where('timestamp')
        .between(startTime, endTime, true, true)
        .toArray()

      console.log(`📥 Retrieved ${frames.length} frames in time range for train ${trainId}`)
      return frames
    } catch (error) {
      console.error('❌ Failed to retrieve frames by time range:', error)
      throw error
    }
  }

  /**
   * Delete a frame by ID
   * @param {string} trainId - Train identifier
   * @param {number} id - Database ID of the frame
   */
  async deleteFrame(trainId, id) {
    try {
      if (!trainId) {
        throw new Error('Train ID is required')
      }

      const db = await this.getTrainDatabase(trainId)
      await db.frames.delete(id)
      console.log(`🗑️ Frame deleted for train ${trainId}: ID=${id}`)
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
      if (!trainId) {
        throw new Error('Train ID is required')
      }

      const db = await this.getTrainDatabase(trainId)
      const count = await db.frames.clear()
      console.log(`🗑️ Deleted all frames for train ${trainId}`)
      await this.updateStats()
      return count
    } catch (error) {
      console.error('❌ Failed to delete frames by train:', error)
      throw error
    }
  }

  /**
   * Delete entire train database (all data for a train)
   * @param {string} trainId - Train identifier
   */
  async deleteTrainDatabase(trainId) {
    try {
      if (!trainId) {
        throw new Error('Train ID is required')
      }

      // Close the database if it's open
      if (this.trainDatabases.has(trainId)) {
        const db = this.trainDatabases.get(trainId)
        db.close()
        this.trainDatabases.delete(trainId)
      }

      // Delete the entire database
      const dbName = `${this.baseDbName}_${trainId}`
      await Dexie.delete(dbName)

      console.log(`🗑️ Deleted entire database for train ${trainId}`)
      await this.updateStats()
      return true
    } catch (error) {
      console.error('❌ Failed to delete train database:', error)
      throw error
    }
  }

  /**
   * Delete all data for a specific train (frames, telemetry, sensor data)
   * @param {string} trainId - Train identifier
   */
  async deleteAllDataByTrain(trainId) {
    try {
      if (!trainId) {
        throw new Error('Train ID is required')
      }

      const db = await this.getTrainDatabase(trainId)
      const frameCount = await db.frames.count()
      const telemetryCount = await db.telemetry.count()
      const sensorCount = await db.sensorData.count()

      await db.frames.clear()
      await db.telemetry.clear()
      await db.sensorData.clear()

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
      if (!trainId) {
        throw new Error('Train ID is required')
      }

      const db = await this.getTrainDatabase(trainId)
      const count = await db.telemetry.clear()
      console.log(`🗑️ Deleted all telemetry records for train ${trainId}`)
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
      if (!trainId) {
        throw new Error('Train ID is required')
      }

      const db = await this.getTrainDatabase(trainId)
      let count

      if (sensorType) {
        count = await db.sensorData.where('sensorType').equals(sensorType).delete()
        console.log(`🗑️ Deleted ${count} ${sensorType} sensor records for train ${trainId}`)
      } else {
        count = await db.sensorData.clear()
        console.log(`🗑️ Deleted all sensor records for train ${trainId}`)
      }

      return count
    } catch (error) {
      console.error('❌ Failed to delete sensor data by train:', error)
      throw error
    }
  }
  /**
   * Clean up old data (older than specified hours) for a specific train
   * @param {string} trainId - Train identifier
   * @param {number} hoursOld - Age threshold in hours (default: 24)
   */
  async cleanupOldDataByTrain(trainId, hoursOld = 24) {
    try {
      if (!trainId) {
        throw new Error('Train ID is required')
      }

      const db = await this.getTrainDatabase(trainId)
      const cutoffTime = Date.now() - (hoursOld * 60 * 60 * 1000)

      const frameCount = await db.frames.where('timestamp').below(cutoffTime).delete()
      const telemetryCount = await db.telemetry.where('timestamp').below(cutoffTime).delete()
      const sensorCount = await db.sensorData.where('timestamp').below(cutoffTime).delete()

      console.log(`🧹 Cleaned up old data for train ${trainId} (older than ${hoursOld} hours): ${frameCount} frames, ${telemetryCount} telemetry, ${sensorCount} sensor records`)
      return { frameCount, telemetryCount, sensorCount }
    } catch (error) {
      console.error('❌ Failed to cleanup old data by train:', error)
      throw error
    }
  }

  /**
   * Clean up old data (older than specified hours) for all trains
   * @param {number} hoursOld - Age threshold in hours (default: 24)
   */
  async cleanupOldData(hoursOld = 24) {
    try {
      const trainIds = await this.getAvailableTrains()
      let totalFrameCount = 0
      let totalTelemetryCount = 0
      let totalSensorCount = 0

      for (const trainId of trainIds) {
        const result = await this.cleanupOldDataByTrain(trainId, hoursOld)
        totalFrameCount += result.frameCount
        totalTelemetryCount += result.telemetryCount
        totalSensorCount += result.sensorCount
      }

      console.log(`🧹 Cleaned up old data across all trains (older than ${hoursOld} hours): ${totalFrameCount} frames, ${totalTelemetryCount} telemetry, ${totalSensorCount} sensor records`)
      await this.updateStats()
      this.stats.lastCleanup = Date.now()
      return { frameCount: totalFrameCount, telemetryCount: totalTelemetryCount, sensorCount: totalSensorCount }
    } catch (error) {
      console.error('❌ Failed to cleanup old data:', error)
      throw error
    }
  }

  /**
   * Get storage statistics across all trains
   */
  async getStats() {
    await this.updateStats()
    return {
      ...this.stats,
      totalSizeMB: (this.stats.totalSize / (1024 * 1024)).toFixed(2)
    }
  }

  /**
   * Get storage statistics for a specific train
   * @param {string} trainId - Train identifier
   */
  async getStatsByTrain(trainId) {
    try {
      if (!trainId) {
        throw new Error('Train ID is required')
      }

      const db = await this.getTrainDatabase(trainId)
      const frameCount = await db.frames.count()
      const telemetryCount = await db.telemetry.count()
      const sensorCount = await db.sensorData.count()

      // Calculate total size for this train
      const frames = await db.frames.toArray()
      const totalSize = frames.reduce((total, frame) => total + frame.size, 0)

      const stats = {
        trainId,
        frameCount,
        telemetryCount,
        sensorCount,
        totalSize,
        totalSizeMB: (totalSize / (1024 * 1024)).toFixed(2)
      }

      console.log(`📊 Stats for train ${trainId}:`, stats)
      return stats
    } catch (error) {
      console.error('❌ Failed to get stats by train:', error)
      throw error
    }
  }

  /**
   * Update internal statistics across all trains
   */
  async updateStats() {
    try {
      const trainIds = await this.getAvailableTrains()
      this.stats.trainCount = trainIds.length
      this.stats.totalFrames = 0
      this.stats.totalSize = 0

      for (const trainId of trainIds) {
        try {
          const trainStats = await this.getStatsByTrain(trainId)
          this.stats.totalFrames += trainStats.frameCount
          this.stats.totalSize += trainStats.totalSize
        } catch (error) {
          console.warn(`⚠️ Failed to get stats for train ${trainId}:`, error)
        }
      }
    } catch (error) {
      console.error('❌ Failed to update stats:', error)
    }
  }

  /**
   * Clear all stored data across all trains
   */
  async clearAll() {
    try {
      const trainIds = await this.getAvailableTrains()

      for (const trainId of trainIds) {
        await this.deleteTrainDatabase(trainId)
      }

      this.stats.totalFrames = 0
      this.stats.totalSize = 0
      this.stats.trainCount = 0
      console.log('🗑️ All train databases cleared')
    } catch (error) {
      console.error('❌ Failed to clear all data:', error)
      throw error
    }
  }

  /**
   * Close all database connections
   */
  async close() {
    try {
      for (const [trainId, db] of this.trainDatabases) {
        db.close()
        console.log(`✅ Closed database for train ${trainId}`)
      }
      this.trainDatabases.clear()
      console.log('✅ All DataStorage connections closed')
    } catch (error) {
      console.error('❌ Failed to close DataStorage:', error)
    }
  }

  /**
   * Export video frames as H.264 data within time range
   * @param {string} trainId - Train identifier
   * @param {number} startTime - Start timestamp (optional)
   * @param {number} endTime - End timestamp (optional)
   */
  async exportVideoFrames(trainId, startTime = null, endTime = null) {
    try {
      if (!trainId) {
        throw new Error('Train ID is required')
      }

      const db = await this.getTrainDatabase(trainId)
      let query = db.frames.orderBy('timestamp')

      if (startTime && endTime) {
        query = db.frames.where('timestamp').between(startTime, endTime, true, true)
      } else if (startTime) {
        query = db.frames.where('timestamp').aboveOrEqual(startTime)
      } else if (endTime) {
        query = db.frames.where('timestamp').belowOrEqual(endTime)
      }

      const frames = await query.toArray()
      
      // Create a combined H.264 stream
      let totalSize = 0
      frames.forEach(frame => totalSize += frame.data.byteLength)
      
      const combinedData = new Uint8Array(totalSize)
      let offset = 0
      
      frames.forEach(frame => {
        combinedData.set(frame.data, offset)
        offset += frame.data.byteLength
      })

      const blob = new Blob([combinedData], { type: 'video/h264' })
      const url = URL.createObjectURL(blob)
      
      // Download the file
      const link = document.createElement('a')
      link.href = url
      link.download = `train_${trainId}_video_${startTime || 'all'}_${endTime || 'all'}.h264`
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      URL.revokeObjectURL(url)

      console.log(`📹 Exported ${frames.length} video frames for train ${trainId}`)
      return { frameCount: frames.length, totalSize }
    } catch (error) {
      console.error('❌ Failed to export video frames:', error)
      throw error
    }
  }

  /**
   * Export telemetry data as JSON within time range
   * @param {string} trainId - Train identifier
   * @param {number} startTime - Start timestamp (optional)
   * @param {number} endTime - End timestamp (optional)
   */
  async exportTelemetryData(trainId, startTime = null, endTime = null) {
    try {
      if (!trainId) {
        throw new Error('Train ID is required')
      }

      const db = await this.getTrainDatabase(trainId)
      let query = db.telemetry.orderBy('timestamp')

      if (startTime && endTime) {
        query = db.telemetry.where('timestamp').between(startTime, endTime, true, true)
      } else if (startTime) {
        query = db.telemetry.where('timestamp').aboveOrEqual(startTime)
      } else if (endTime) {
        query = db.telemetry.where('timestamp').belowOrEqual(endTime)
      }

      const telemetryData = await query.toArray()
      
      const exportData = {
        trainId,
        exportTimestamp: Date.now(),
        timeRange: { startTime, endTime },
        recordCount: telemetryData.length,
        data: telemetryData
      }

      const jsonString = JSON.stringify(exportData, null, 2)
      const blob = new Blob([jsonString], { type: 'application/json' })
      const url = URL.createObjectURL(blob)
      
      // Download the file
      const link = document.createElement('a')
      link.href = url
      link.download = `train_${trainId}_telemetry_${startTime || 'all'}_${endTime || 'all'}.json`
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      URL.revokeObjectURL(url)

      console.log(`📊 Exported ${telemetryData.length} telemetry records for train ${trainId}`)
      return { recordCount: telemetryData.length }
    } catch (error) {
      console.error('❌ Failed to export telemetry data:', error)
      throw error
    }
  }

  /**
   * Export sensor data as JSON within time range
   * @param {string} trainId - Train identifier
   * @param {number} startTime - Start timestamp (optional)
   * @param {number} endTime - End timestamp (optional)
   * @param {string} sensorType - Sensor type (optional)
   */
  async exportSensorData(trainId, startTime = null, endTime = null, sensorType = null) {
    try {
      if (!trainId) {
        throw new Error('Train ID is required')
      }

      const db = await this.getTrainDatabase(trainId)
      let query = db.sensorData

      if (sensorType) {
        query = query.where('sensorType').equals(sensorType)
      }

      if (startTime && endTime) {
        query = query.and(item => item.timestamp >= startTime && item.timestamp <= endTime)
      } else if (startTime) {
        query = query.and(item => item.timestamp >= startTime)
      } else if (endTime) {
        query = query.and(item => item.timestamp <= endTime)
      }

      const sensorData = await query.toArray()
      
      const exportData = {
        trainId,
        sensorType: sensorType || 'all',
        exportTimestamp: Date.now(),
        timeRange: { startTime, endTime },
        recordCount: sensorData.length,
        data: sensorData
      }

      const jsonString = JSON.stringify(exportData, null, 2)
      const blob = new Blob([jsonString], { type: 'application/json' })
      const url = URL.createObjectURL(blob)
      
      // Download the file
      const link = document.createElement('a')
      link.href = url
      link.download = `train_${trainId}_sensor_${sensorType || 'all'}_${startTime || 'all'}_${endTime || 'all'}.json`
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      URL.revokeObjectURL(url)

      console.log(`🔬 Exported ${sensorData.length} sensor records for train ${trainId}`)
      return { recordCount: sensorData.length }
    } catch (error) {
      console.error('❌ Failed to export sensor data:', error)
      throw error
    }
  }
}

// Export a composable function for Vue 3
export function useDataStorage(baseDbName, version) {
  const dataStorage = new DataStorage(baseDbName, version)

  return {
    // Database operations
    init: () => dataStorage.init(),
    getAvailableTrains: () => dataStorage.getAvailableTrains(),
    getTrainDatabase: (trainId) => dataStorage.getTrainDatabase(trainId),

    // Frame operations
    storeFrame: (frameData) => dataStorage.storeFrame(frameData),
    getFrame: (trainId, id) => dataStorage.getFrame(trainId, id),
    getFramesByTrain: (trainId, limit) => dataStorage.getFramesByTrain(trainId, limit),
    getAllFramesByTrain: (trainId) => dataStorage.getAllFramesByTrain(trainId),
    getFramesByTimeRange: (trainId, start, end) => dataStorage.getFramesByTimeRange(trainId, start, end),
    deleteFrame: (trainId, id) => dataStorage.deleteFrame(trainId, id),
    deleteFramesByTrain: (trainId) => dataStorage.deleteFramesByTrain(trainId),

    // Telemetry operations
    storeTelemetry: (telemetryData) => dataStorage.storeTelemetry(telemetryData),
    getTelemetry: (trainId, id) => dataStorage.getTelemetry(trainId, id),
    getTelemetryByTrain: (trainId, limit) => dataStorage.getTelemetryByTrain(trainId, limit),
    getAllTelemetryByTrain: (trainId) => dataStorage.getAllTelemetryByTrain(trainId),
    getTelemetryByTimeRange: (trainId, start, end) => dataStorage.getTelemetryByTimeRange(trainId, start, end),
    deleteTelemetryByTrain: (trainId) => dataStorage.deleteTelemetryByTrain(trainId),

    // Sensor data operations
    storeSensorData: (sensorData) => dataStorage.storeSensorData(sensorData),
    getSensorData: (trainId, id) => dataStorage.getSensorData(trainId, id),
    getSensorDataByTrain: (trainId, sensorType, limit) => dataStorage.getSensorDataByTrain(trainId, sensorType, limit),
    getSensorDataByTimeRange: (trainId, start, end, sensorType) => dataStorage.getSensorDataByTimeRange(trainId, start, end, sensorType),
    deleteSensorDataByTrain: (trainId, sensorType) => dataStorage.deleteSensorDataByTrain(trainId, sensorType),

    // Train-specific management operations
    deleteAllDataByTrain: (trainId) => dataStorage.deleteAllDataByTrain(trainId),
    deleteTrainDatabase: (trainId) => dataStorage.deleteTrainDatabase(trainId),
    cleanupOldDataByTrain: (trainId, hours) => dataStorage.cleanupOldDataByTrain(trainId, hours),

    // General management operations
    cleanupOldData: (hours) => dataStorage.cleanupOldData(hours),
    clearAll: () => dataStorage.clearAll(),

    // Utility operations
    getStats: () => dataStorage.getStats(),
    getStatsByTrain: (trainId) => dataStorage.getStatsByTrain(trainId),
    close: () => dataStorage.close(),

    // Direct access to the storage instance if needed
    storage: dataStorage,

    // New metadata and export operations
    getRecordedTrainsMetadata: () => dataStorage.getRecordedTrainsMetadata(),
    exportVideoFrames: (trainId, startTime, endTime) => dataStorage.exportVideoFrames(trainId, startTime, endTime),
    exportTelemetryData: (trainId, startTime, endTime) => dataStorage.exportTelemetryData(trainId, startTime, endTime),
    exportSensorData: (trainId, startTime, endTime, sensorType) => dataStorage.exportSensorData(trainId, startTime, endTime, sensorType)
  }
}

// Export the class as well for direct usage
export { DataStorage }
