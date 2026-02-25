<template>
  <div class="recorded-train-view">
    <AppHeader />

    <main class="recorded-train-main">
      <div class="recorded-train-header">
        <div class="header-info">
          <button class="back-btn" @click="goBack">
            <i class="fa-solid fa-arrow-left"></i>
            Back to Home
          </button>
          <div class="train-title">
            <h1>Train ID: {{ trainId }}</h1>
            <p v-if="trainMetadata">
              {{ formatNumber(trainMetadata.frameCount) }} frames,
              {{ formatNumber(trainMetadata.telemetryCount) }} telemetry records
              <span v-if="trainMetadata.duration"> • {{ formatDuration(trainMetadata.duration) }}</span>
            </p>
            <p v-if="trainMetadata" class="data-age">
              Recorded {{ formatTimeAgo(trainMetadata.startTime) }} • 
              {{ formatDate(trainMetadata.startTime) }}
            </p>
          </div>
        </div>
        <div class="header-actions">
          <button class="refresh-btn" @click="loadTrainData" :disabled="loading">
            <i class="fa-solid fa-rotate" :class="{ 'spinning': loading }"></i>
            Refresh
          </button>
        </div>
      </div>

      <div v-if="loading" class="loading-state">
        <div class="loading-spinner"></div>
        <p>Loading train data...</p>
      </div>

      <div v-else-if="!trainMetadata" class="error-state">
        <div class="error-icon">
          <i class="fa-solid fa-circle-exclamation"></i>
        </div>
        <h3>Train Data Not Found</h3>
        <p>No recorded data found for train {{ trainId }}</p>
        <button class="retry-btn" @click="goBack">
          Return to Home
        </button>
      </div>

      <div v-else class="recorded-train-content">
        <!-- Time Range Selector -->
        <div class="time-range-panel">
          <div class="time-controls">
            <div class="time-input-group">
              <label>Start Time:</label>
              <input
                type="datetime-local"
                step="1"
                v-model="startTimeInput"
                :max="endTimeInput"
                class="time-input"
              />
            </div>
            <div class="time-input-group">
              <label>End Time:</label>
              <input
                type="datetime-local"
                step="1"
                v-model="endTimeInput"
                :min="startTimeInput"
                class="time-input"
              />
            </div>
            <button class="apply-range-btn" @click="applyTimeRange">
              Apply Range
            </button>
            <button class="reset-range-btn" @click="resetTimeRange">
              Reset to Full Range
            </button>
          </div>
          <div class="time-info" v-if="selectedTimeRange.start && selectedTimeRange.end">
            <p>
              Selected: {{ formatDate(selectedTimeRange.start) }} - {{ formatDate(selectedTimeRange.end) }}
              ({{ formatDuration(selectedTimeRange.end - selectedTimeRange.start) }})
            </p>
          </div>
        </div>

        <!-- Video Player -->
        <div class="video-player-panel">
          <h3>Recorded Video Playback</h3>
          <div class="video-player-container">
            <div class="video-display">
              <canvas ref="videoCanvas" class="video-canvas"></canvas>
              <button
                class="fullscreen-btn"
                @click="toggleFullScreen"
                :title="isFullScreen ? 'Exit Full Screen' : 'Full Screen'"
              >
                <i class="fa-solid" :class="isFullScreen ? 'fa-compress' : 'fa-expand'"></i>
              </button>
              <div v-if="!isPlaying && !loadingVideo" class="play-overlay">
                <button class="play-btn" @click="startPlayback">
                  <i class="fa-solid fa-play"></i>
                  Play Recorded Video
                </button>
              </div>
              <div v-if="loadingVideo" class="loading-overlay">
                <div class="loading-spinner"></div>
                <p>Loading video frames...</p>
              </div>
            </div>
            <div class="video-controls">
              <div class="playback-controls">
                <button 
                  class="control-btn" 
                  @click="togglePlayback"
                  :disabled="!videoFrames.length"
                >
                  <i class="fa-solid" :class="isPlaying ? 'fa-pause' : 'fa-play'"></i>
                  {{ isPlaying ? 'Pause' : 'Play' }}
                </button>
                <button 
                  class="control-btn" 
                  @click="stopPlayback"
                  :disabled="!videoFrames.length"
                >
                  <i class="fa-solid fa-stop"></i>
                  Stop
                </button>
                <div class="frame-info">
                  <span>Frame {{ currentFrameIndex + 1 }} of {{ videoFrames.length }}</span>
                </div>
              </div>
              <div class="progress-container">
                <input
                  type="range"
                  class="progress-slider"
                  :min="0"
                  :max="Math.max(0, videoFrames.length - 1)"
                  v-model="currentFrameIndex"
                  @input="seekToFrame"
                  :disabled="!videoFrames.length"
                />
                <div class="time-display">
                  <span>{{ formatPlaybackTime(currentPlaybackTime) }}</span>
                  <span>/</span>
                  <span>{{ formatPlaybackTime(totalPlaybackTime) }}</span>
                </div>
              </div>
              <div class="control-settings">
                <div class="playback-speed">
                  <label>Speed:</label>
                  <select v-model="playbackSpeed" @change="updatePlaybackSpeed">
                    <option value="0.25">0.25x</option>
                    <option value="0.5">0.5x</option>
                    <option value="1">1x</option>
                    <option value="1.5">1.5x</option>
                    <option value="2">2x</option>
                    <option value="4">4x</option>
                  </select>
                </div>
                <div class="framerate-control">
                  <label>FPS:</label>
                  <select v-model="targetFramerate" @change="updateFramerate">
                    <option value="10">10 FPS</option>
                    <option value="15">15 FPS</option>
                    <option value="24">24 FPS</option>
                    <option value="30">30 FPS</option>
                    <option value="60">60 FPS</option>
                  </select>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Export Actions -->
        <div class="export-panel">
          <h3>Export Options</h3>
          <div class="export-grid">
            <div class="export-card">
              <div class="export-info">
                <h4>Video Frames</h4>
                <div class="export-stats">
                  {{ getFrameCountInRange() }} frames
                </div>
              </div>
              <button 
                class="export-btn"
                @click="exportVideo"
                :disabled="exporting.video"
              >
                <span v-if="exporting.video">Exporting...</span>
                <span v-else>Export Video</span>
              </button>
            </div>

            <div class="export-card">
              <div class="export-info">
                <h4>Video Frames + Metadata</h4>
                <div class="export-stats">
                  {{ getFrameCountInRange() }} frames
                </div>
              </div>
              <button 
                class="export-btn"
                @click="exportVideoMetadata"
                :disabled="exporting.videoMetadata"
              >
                <span v-if="exporting.videoMetadata">Exporting...</span>
                <span v-else>Export Metadata</span>
              </button>
            </div>

            <div class="export-card">
              <div class="export-info">
                <h4>Telemetry Data</h4>
                <div class="export-stats">
                  {{ getTelemetryCountInRange() }} records
                </div>
              </div>
              <button 
                class="export-btn"
                @click="exportTelemetry"
                :disabled="exporting.telemetry"
              >
                <span v-if="exporting.telemetry">Exporting...</span>
                <span v-else>Export Telemetry</span>
              </button>
            </div>

            <div class="export-card">
              <div class="export-info">
                <h4>Sensor Data</h4>
                <div class="export-stats">
                  {{ getSensorCountInRange() }} records
                </div>
              </div>
              <button 
                class="export-btn"
                @click="exportSensorData"
                :disabled="exporting.sensor"
              >
                <span v-if="exporting.sensor">Exporting...</span>
                <span v-else>Export Sensors</span>
              </button>
            </div>

            <div class="export-card">
              <div class="export-info">
                <h4>Latency Data</h4>
                <div class="export-stats">
                  Video & Telemetry latencies
                </div>
              </div>
              <button 
                class="export-btn"
                @click="exportLatency"
                :disabled="exporting.latency"
              >
                <span v-if="exporting.latency">Exporting...</span>
                <span v-else>Export Latency</span>
              </button>
            </div>

            <div class="export-card">
              <div class="export-info">
                <h4>WAN Data</h4>
                <div class="export-stats">
                  {{ getWanCountInRange() }} records
                </div>
              </div>
              <button 
                class="export-btn"
                @click="exportWanData"
                :disabled="exporting.wan"
              >
                <span v-if="exporting.wan">Exporting...</span>
                <span v-else>Export WAN</span>
              </button>
            </div>
          </div>
        </div>

        <!-- Data Management -->
        <div class="management-panel">
          <h3>Data Management</h3>
          <div class="management-actions">
            <button class="danger-btn" @click="confirmDelete = true">
              <i class="fa-solid fa-trash"></i>
              Delete Train Data
            </button>
          </div>
        </div>
      </div>
    </main>

    <!-- Delete Confirmation Modal -->
    <div v-if="confirmDelete" class="modal-overlay" @click="confirmDelete = false">
      <div class="modal-content" @click.stop>
        <h3>Confirm Deletion</h3>
        <p>Are you sure you want to delete all recorded data for Train {{ trainId }}? This action cannot be undone.</p>
        <div class="modal-actions">
          <button class="cancel-btn" @click="confirmDelete = false">Cancel</button>
          <button class="delete-btn" @click="deleteTrainData">Delete</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import AppHeader from '@/components/AppHeader.vue'
import { useDataStorage } from '@/scripts/dataStorage'
import { useVideoPanel } from '@/composables/useVideoPanel'

const route = useRoute()
const router = useRouter()
const dataStorage = useDataStorage()

const trainId = computed(() => route.params.trainId)

const loading = ref(false)
const trainMetadata = ref(null)
const confirmDelete = ref(false)

const exporting = ref({
  video: false,
  videoMetadata: false,
  telemetry: false,
  sensor: false,
  latency: false,
  wan: false
})

const frameCountInRange = ref(0)
const telemetryCountInRange = ref(0)
const sensorCountInRange = ref(0)
const wanCountInRange = ref(0)

const selectedTimeRange = ref({
  start: null,
  end: null
})

const startTimeInput = ref('')
const endTimeInput = ref('')

// Video player state
const videoCanvas = ref(null)
const videoFrames = ref([])
const currentFrameIndex = ref(0)
const isPlaying = ref(false)
const loadingVideo = ref(false)
const playbackSpeed = ref(1)
const targetFramerate = ref(30)
const playbackInterval = ref(null)

// Initialize video panel composable
const {
  isFullScreen,
  toggleFullScreen,
  handleFrame,
  updateCanvasSize
} = useVideoPanel(videoCanvas, {
  videoWidth: 1280,
  videoHeight: 720,
  maxQueueSize: 10
})

// Computed properties for video playback
const currentPlaybackTime = computed(() => {
  if (!videoFrames.value.length) return 0
  const currentFrame = videoFrames.value[currentFrameIndex.value]
  return currentFrame ? currentFrame.timestamp : 0
})

const totalPlaybackTime = computed(() => {
  if (!videoFrames.value.length) return 0
  const lastFrame = videoFrames.value[videoFrames.value.length - 1]
  const firstFrame = videoFrames.value[0]
  return lastFrame.timestamp - firstFrame.timestamp
})

// Helper function to format date for datetime-local input
const formatDateTimeLocal = (date) => {
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  const hours = String(date.getHours()).padStart(2, '0')
  const minutes = String(date.getMinutes()).padStart(2, '0')
  const seconds = String(date.getSeconds()).padStart(2, '0')
  
  return `${year}-${month}-${day}T${hours}:${minutes}:${seconds}`
}

// Video playback functions
const loadVideoFrames = async () => {
  loadingVideo.value = true
  try {
    const frames = await dataStorage.getFramesByTimeRange(
      trainId.value,
      selectedTimeRange.value.start,
      selectedTimeRange.value.end
    )
    
    // Sort frames by timestamp to ensure proper playback order
    videoFrames.value = frames.sort((a, b) => a.timestamp - b.timestamp)
    currentFrameIndex.value = 0
    
    console.log(`📹 Loaded ${videoFrames.value.length} video frames for playback`)
    
    // Ensure canvas is properly sized before loading first frame
    await updateCanvasSize()
    
    // Load first frame if available
    if (videoFrames.value.length > 0) {
      displayFrame(0)
    }
  } catch (error) {
    console.error('Failed to load video frames:', error)
    alert('Failed to load video frames for playback')
  } finally {
    loadingVideo.value = false
  }
}

const displayFrame = (frameIndex) => {
  if (frameIndex < 0 || frameIndex >= videoFrames.value.length) return
  
  const frame = videoFrames.value[frameIndex]
  if (frame && frame.data) {
    // Ensure canvas is properly sized before displaying frame
    if (frameIndex === 0) {
      // For the first frame, wait a bit for DOM to be ready then update canvas size
      setTimeout(() => {
        updateCanvasSize()
        handleFrame(frame.data)
      }, 50)
    } else {
      handleFrame(frame.data)
    }
    currentFrameIndex.value = frameIndex
  }
}

const startPlayback = async () => {
  if (!videoFrames.value.length) {
    await loadVideoFrames()
  }
  
  if (videoFrames.value.length > 0) {
    isPlaying.value = true
    playFrames()
  }
}

const togglePlayback = () => {
  if (isPlaying.value) {
    pausePlayback()
  } else {
    resumePlayback()
  }
}

const pausePlayback = () => {
  isPlaying.value = false
  if (playbackInterval.value) {
    clearTimeout(playbackInterval.value)
    playbackInterval.value = null
  }
}

const resumePlayback = () => {
  if (videoFrames.value.length > 0) {
    isPlaying.value = true
    playFrames()
  }
}

const stopPlayback = () => {
  pausePlayback()
  currentFrameIndex.value = 0
  if (videoFrames.value.length > 0) {
    displayFrame(0)
  }
}

const playFrames = () => {
  if (!isPlaying.value || currentFrameIndex.value >= videoFrames.value.length) {
    isPlaying.value = false
    return
  }
  
  displayFrame(currentFrameIndex.value)
  
  // Calculate delay between frames based on target framerate and speed
  const baseDelay = 1000 / targetFramerate.value // milliseconds per frame
  const adjustedDelay = baseDelay / playbackSpeed.value
  
  playbackInterval.value = setTimeout(() => {
    currentFrameIndex.value++
    if (currentFrameIndex.value >= videoFrames.value.length) {
      // End of video reached
      stopPlayback()
    } else {
      playFrames()
    }
  }, adjustedDelay)
}

const seekToFrame = () => {
  const frameIndex = parseInt(currentFrameIndex.value)
  displayFrame(frameIndex)
  
  // If playing, restart playback from new position
  if (isPlaying.value) {
    pausePlayback()
    resumePlayback()
  }
}

const updatePlaybackSpeed = () => {
  // If currently playing, restart with new speed
  if (isPlaying.value) {
    pausePlayback()
    resumePlayback()
  }
}

const updateFramerate = () => {
  // If currently playing, restart with new framerate
  if (isPlaying.value) {
    pausePlayback()
    resumePlayback()
  }
}

const formatPlaybackTime = (timestamp) => {
  if (!timestamp || !videoFrames.value.length) return '00:00'
  
  const firstFrameTime = videoFrames.value[0]?.timestamp || 0
  const relativeTime = Math.max(0, timestamp - firstFrameTime)
  const seconds = Math.floor(relativeTime / 1000)
  const minutes = Math.floor(seconds / 60)
  const remainingSeconds = seconds % 60
  
  return `${minutes.toString().padStart(2, '0')}:${remainingSeconds.toString().padStart(2, '0')}`
}

const loadTrainData = async () => {
  loading.value = true
  try {
    await dataStorage.init()
    const metadata = await dataStorage.getRecordedTrainMetadataByID(trainId.value)
    trainMetadata.value = metadata
    if (trainMetadata.value) {
      // Set default time range to full dataset
      resetTimeRange()
    }
  } catch (error) {
    console.error('Failed to load train data:', error)
  } finally {
    loading.value = false
  }
}

const resetTimeRange = () => {
  if (trainMetadata.value) {
    console.log('🔄 Resetting time range with metadata:', {
      startTime: trainMetadata.value.startTime,
      endTime: trainMetadata.value.endTime,
      startDate: new Date(trainMetadata.value.startTime).toISOString(),
      endDate: new Date(trainMetadata.value.endTime).toISOString(),
      frameCount: trainMetadata.value.frameCount,
      telemetryCount: trainMetadata.value.telemetryCount
    })
    
    selectedTimeRange.value.start = trainMetadata.value.startTime
    selectedTimeRange.value.end = trainMetadata.value.endTime
    
    // Convert UTC timestamps to local datetime strings for the input
    const startDate = new Date(trainMetadata.value.startTime)
    const endDate = new Date(trainMetadata.value.endTime)
    
    // Format for datetime-local input (local time)
    startTimeInput.value = formatDateTimeLocal(startDate)
    endTimeInput.value = formatDateTimeLocal(endDate)
    
    console.log('🕐 Time input values:', {
      startTimeInput: startTimeInput.value,
      endTimeInput: endTimeInput.value,
      timezone: Intl.DateTimeFormat().resolvedOptions().timeZone
    })
    
    // Update counts for the new time range
    updateCountsInRange()
    
    // Reset video player when time range resets
    stopPlayback()
    videoFrames.value = []
  }
}

const applyTimeRange = () => {
  // Convert from local datetime input to UTC timestamp
  const startDate = new Date(startTimeInput.value)
  const endDate = new Date(endTimeInput.value)
  
  selectedTimeRange.value.start = startDate.getTime()
  selectedTimeRange.value.end = endDate.getTime()
  
  console.log('🕐 Applied time range:', {
    inputStart: startTimeInput.value,
    inputEnd: endTimeInput.value,
    timestampStart: selectedTimeRange.value.start,
    timestampEnd: selectedTimeRange.value.end,
    utcStart: new Date(selectedTimeRange.value.start).toISOString(),
    utcEnd: new Date(selectedTimeRange.value.end).toISOString()
  })
  
  // Update counts for the new time range
  updateCountsInRange()
  
  // Reset video player when time range changes
  stopPlayback()
  videoFrames.value = []
}

const updateCountsInRange = async () => {
  try {
    if (!trainMetadata.value) {
      frameCountInRange.value = 0
      telemetryCountInRange.value = 0
      sensorCountInRange.value = 0
      wanCountInRange.value = 0
      return
    }

    // If no specific time range is selected, use total counts
    if (!selectedTimeRange.value.start || !selectedTimeRange.value.end) {
      frameCountInRange.value = trainMetadata.value?.frameCount || 0
      telemetryCountInRange.value = trainMetadata.value?.telemetryCount || 0
      sensorCountInRange.value = trainMetadata.value?.sensorCount || 0
      wanCountInRange.value = trainMetadata.value?.wanDataCount || 0
      return
    }

    console.log('🔍 Updating counts for time range:', {
      start: selectedTimeRange.value.start,
      end: selectedTimeRange.value.end,
      startDate: new Date(selectedTimeRange.value.start).toISOString(),
      endDate: new Date(selectedTimeRange.value.end).toISOString(),
      trainId: trainId.value
    })

    // If the selected range covers the entire dataset or beyond, use total counts
    const metadataStart = trainMetadata.value.startTime
    const metadataEnd = trainMetadata.value.endTime
    
    if (selectedTimeRange.value.start <= metadataStart && selectedTimeRange.value.end >= metadataEnd) {
      console.log('📊 Selected range covers entire dataset, using total counts')
      frameCountInRange.value = trainMetadata.value?.frameCount || 0
      telemetryCountInRange.value = trainMetadata.value?.telemetryCount || 0
      sensorCountInRange.value = trainMetadata.value?.sensorCount || 0
      wanCountInRange.value = trainMetadata.value?.wanDataCount || 0
      return
    }

    // Get counts for the selected time range
    const [frames, telemetry, sensorData, wanData] = await Promise.all([
      dataStorage.getFramesByTimeRange(
        trainId.value,
        selectedTimeRange.value.start,
        selectedTimeRange.value.end
      ).catch(error => {
        console.error('Error getting frames:', error)
        return []
      }),
      dataStorage.getTelemetryByTimeRange(
        trainId.value,
        selectedTimeRange.value.start,
        selectedTimeRange.value.end
      ).catch(error => {
        console.error('Error getting telemetry:', error)
        return []
      }),
      dataStorage.getSensorDataByTimeRange(
        trainId.value,
        selectedTimeRange.value.start,
        selectedTimeRange.value.end
      ).catch(error => {
        console.error('Error getting sensor data:', error)
        return []
      }),
      dataStorage.getWANDataByTimeRange(
        trainId.value,
        selectedTimeRange.value.start,
        selectedTimeRange.value.end
      ).catch(error => {
        console.error('Error getting WAN data:', error)
        return []
      })
    ])
    
    console.log('📊 Query results:', {
      frames: frames.length,
      telemetry: telemetry.length,
      sensorData: sensorData.length,
      wanData: wanData.length
    })
    
    frameCountInRange.value = frames.length
    telemetryCountInRange.value = telemetry.length
    sensorCountInRange.value = sensorData.length
    wanCountInRange.value = wanData.length
  } catch (error) {
    console.error('Failed to update counts in range:', error)
    // Fallback to total counts if there's an error
    frameCountInRange.value = trainMetadata.value?.frameCount || 0
    telemetryCountInRange.value = trainMetadata.value?.telemetryCount || 0
    sensorCountInRange.value = trainMetadata.value?.sensorCount || 0
    wanCountInRange.value = trainMetadata.value?.wanDataCount || 0
  }
}

const getFrameCountInRange = () => {
  return frameCountInRange.value
}

const getTelemetryCountInRange = () => {
  return telemetryCountInRange.value
}

const getSensorCountInRange = () => {
  return sensorCountInRange.value
}

const getWanCountInRange = () => {
  return wanCountInRange.value
}

const exportVideo = async () => {
  exporting.value.video = true
  try {
    await dataStorage.exportVideoFrames(
      trainId.value,
      selectedTimeRange.value.start,
      selectedTimeRange.value.end
    )
  } catch (error) {
    console.error('Failed to export video:', error)
    alert('Failed to export video data. Please try again.')
  } finally {
    exporting.value.video = false
  }
}

const exportVideoMetadata = async () => {
  exporting.value.videoMetadata = true
  try {
    await dataStorage.exportVideoFramesWithMetadata(
      trainId.value,
      selectedTimeRange.value.start,
      selectedTimeRange.value.end
    )
  } catch (error) {
    console.error('Failed to export video frames with metadata:', error)
    alert('Failed to export video frames with metadata. Please try again.')
  } finally {
    exporting.value.videoMetadata = false
  }
}

const exportTelemetry = async () => {
  exporting.value.telemetry = true
  try {
    await dataStorage.exportTelemetryData(
      trainId.value,
      selectedTimeRange.value.start,
      selectedTimeRange.value.end
    )
  } catch (error) {
    console.error('Failed to export telemetry:', error)
    alert('Failed to export telemetry data. Please try again.')
  } finally {
    exporting.value.telemetry = false
  }
}

const exportSensorData = async () => {
  exporting.value.sensor = true
  try {
    await dataStorage.exportSensorData(
      trainId.value,
      selectedTimeRange.value.start,
      selectedTimeRange.value.end
    )
  } catch (error) {
    console.error('Failed to export sensor data:', error)
    alert('Failed to export sensor data. Please try again.')
  } finally {
    exporting.value.sensor = false
  }
}

const exportLatency = async () => {
  exporting.value.latency = true
  try {
    await dataStorage.exportLatencyData(
      trainId.value,
      selectedTimeRange.value.start,
      selectedTimeRange.value.end
    )
  } catch (error) {
    console.error('Failed to export latency data:', error)
    alert('Failed to export latency data. Please try again.')
  } finally {
    exporting.value.latency = false
  }
}

const exportWanData = async () => {
  exporting.value.wan = true
  try {
    await dataStorage.exportWanData(
      trainId.value,
      selectedTimeRange.value.start,
      selectedTimeRange.value.end
    )
  } catch (error) {
    console.error('Failed to export WAN data:', error)
    alert('Failed to export WAN data. Please try again.')
  } finally {
    exporting.value.wan = false
  }
}

const deleteTrainData = async () => {
  try {
    await dataStorage.deleteTrainDatabase(trainId.value)
    confirmDelete.value = false
    router.push('/')
  } catch (error) {
    console.error('Failed to delete train data:', error)
    alert('Failed to delete train data. Please try again.')
  }
}

const goBack = () => {
  router.push('/')
}

// Utility functions
const formatNumber = (num) => {
  if (num >= 1000000) {
    return (num / 1000000).toFixed(1) + 'M'
  } else if (num >= 1000) {
    return (num / 1000).toFixed(1) + 'K'
  }
  return num.toString()
}

const formatDuration = (duration) => {
  const hours = Math.floor(duration / (1000 * 60 * 60))
  const minutes = Math.floor((duration % (1000 * 60 * 60)) / (1000 * 60))
  const seconds = Math.floor((duration % (1000 * 60)) / 1000)
  
  if (hours > 0) {
    return `${hours}h ${minutes}m ${seconds}s`
  } else if (minutes > 0) {
    return `${minutes}m ${seconds}s`
  } else {
    return `${seconds}s`
  }
}

const formatDate = (timestamp) => {
  return new Date(timestamp).toLocaleDateString() + ' ' + new Date(timestamp).toLocaleTimeString()
}

const formatTimeAgo = (timestamp) => {
  const now = Date.now()
  const diff = now - timestamp
  
  const seconds = Math.floor(diff / 1000)
  const minutes = Math.floor(seconds / 60)
  const hours = Math.floor(minutes / 60)
  const days = Math.floor(hours / 24)
  const weeks = Math.floor(days / 7)
  const months = Math.floor(days / 30)
  const years = Math.floor(days / 365)
  
  if (years > 0) {
    return years === 1 ? '1 year ago' : `${years} years ago`
  } else if (months > 0) {
    return months === 1 ? '1 month ago' : `${months} months ago`
  } else if (weeks > 0) {
    return weeks === 1 ? '1 week ago' : `${weeks} weeks ago`
  } else if (days > 0) {
    return days === 1 ? '1 day ago' : `${days} days ago`
  } else if (hours > 0) {
    return hours === 1 ? '1 hour ago' : `${hours} hours ago`
  } else if (minutes > 0) {
    return minutes === 1 ? '1 minute ago' : `${minutes} minutes ago`
  } else {
    return 'Just now'
  }
}

onMounted(() => {
  loadTrainData()
})

onUnmounted(() => {
  // Clean up video playback
  if (playbackInterval.value) {
    clearTimeout(playbackInterval.value)
  }
})
</script>

<style scoped>
.recorded-train-view {
  min-height: 100vh;
}

.recorded-train-main {
  max-width: 1400px;
  margin: 0 auto;
  padding: 2rem;
}

.recorded-train-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 2rem;
  background: white;
  padding: 2rem;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
}

.header-info {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.back-btn {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  background: transparent;
  color: #1976d2;
  border: 1px solid #1976d2;
  border-radius: 6px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  align-self: flex-start;
}

.back-btn:hover {
  background: #1976d2;
  color: white;
}

.back-btn i {
  font-size: 14px;
}

.train-title h1 {
  font-size: 2rem;
  font-weight: 700;
  color: #1a237e;
  margin: 0 0 0.5rem 0;
}

.train-title p {
  color: #666;
  margin: 0;
}

.train-title p.data-age {
  color: #888;
  font-size: 0.9rem;
  margin-top: 0.5rem;
}

.header-actions {
  display: flex;
  gap: 1rem;
}

.refresh-btn {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1.5rem;
  background: #1976d2;
  color: white;
  border: none;
  border-radius: 8px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.refresh-btn:hover:not(:disabled) {
  background: #1565c0;
}

.refresh-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.refresh-btn i {
  font-size: 14px;
  transition: transform 0.5s ease;
}

.refresh-btn i.spinning {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.loading-state, .error-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 4rem 2rem;
  text-align: center;
  background: white;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
}

.loading-state p, .error-state h3, .error-state p {
  color: #333;
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #e3f2fd;
  border-top: 4px solid #1976d2;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 1rem;
}

.error-icon {
  width: 80px;
  height: 80px;
  background: #f5f5f5;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 1.5rem;
}

.error-icon i {
  font-size: 40px;
  color: #f44336;
}

.recorded-train-content {
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

.time-range-panel, .export-panel, .management-panel {
  background: white;
  padding: 2rem;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
}

.time-range-panel h3, .export-panel h3, .management-panel h3 {
  font-size: 1.5rem;
  font-weight: 600;
  color: #1a237e;
  margin: 0 0 1.5rem 0;
}

.time-controls {
  display: flex;
  flex-wrap: wrap;
  gap: 1rem;
  align-items: flex-end;
}

.time-input-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.time-input-group label {
  font-weight: 500;
  color: #333;
}

.time-input {
  padding: 0.75rem;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 0.875rem;
  background: white;
  color: #333;
}

.apply-range-btn, .reset-range-btn {
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 6px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.apply-range-btn {
  background: #4caf50;
  color: white;
}

.apply-range-btn:hover {
  background: #45a049;
}

.reset-range-btn {
  background: #f0f0f0;
  color: #333;
  border: none;
}

.reset-range-btn:hover {
  background: #e0e0e0;
}

.time-info {
  margin-top: 1rem;
  padding: 1rem;
  background: #f8f9fa;
  border-radius: 6px;
  color: #666;
}

.video-player-panel {
  background: white;
  padding: 2rem;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
}

.video-player-panel h3 {
  font-size: 1.5rem;
  font-weight: 600;
  color: #1a237e;
  margin: 0 0 1.5rem 0;
}

.video-player-container {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.video-display {
  position: relative;
  width: 100%;
  background: #000;
  border-radius: 8px;
  overflow: hidden;
  aspect-ratio: 16/9;
}

.video-canvas {
  width: 100%;
  height: 100%;
  object-fit: contain;
  /* Prevent browser from applying smoothing/blur to the canvas */
  image-rendering: -webkit-optimize-contrast;
  image-rendering: -moz-crisp-edges;
  image-rendering: crisp-edges;
  image-rendering: pixelated;
}

.fullscreen-btn {
  position: absolute;
  top: 12px;
  right: 12px;
  z-index: 10;
  background: rgba(30, 30, 30, 0.7);
  border: none;
  border-radius: 50%;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  cursor: pointer;
  transition: background 0.2s;
}

.fullscreen-btn:hover {
  background: rgba(60, 60, 60, 0.85);
}

.fullscreen-btn i {
  font-size: 16px;
  pointer-events: none;
}

.play-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.3);
}

.play-btn {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 1rem 2rem;
  background: #1976d2;
  color: white;
  border: none;
  border-radius: 50px;
  font-size: 1.1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  box-shadow: 0 4px 12px rgba(25, 118, 210, 0.3);
}

.play-btn:hover {
  background: #1565c0;
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(25, 118, 210, 0.4);
}

.play-btn i {
  font-size: 20px;
}

.loading-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.8);
  color: white;
}

.loading-overlay .loading-spinner {
  width: 40px;
  height: 40px;
  border: 4px solid rgba(255, 255, 255, 0.3);
  border-top: 4px solid #1976d2;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 1rem;
}

.loading-overlay p {
  color: white;
  margin: 0;
}

.video-controls {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  padding: 1rem;
  background: #f8f9fa;
  border-radius: 8px;
}

.playback-controls {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.control-btn {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  background: #1976d2;
  color: white;
  border: none;
  border-radius: 6px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.control-btn:hover:not(:disabled) {
  background: #1565c0;
}

.control-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.control-btn i {
  font-size: 14px;
}

.frame-info {
  color: #666;
  font-weight: 500;
  margin-left: auto;
}

.control-settings {
  display: flex;
  gap: 1rem;
  align-items: center;
  justify-content: center;
}

.progress-container {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.progress-slider {
  width: 100%;
  height: 6px;
  background: #e0e0e0;
  border-radius: 3px;
  outline: none;
  cursor: pointer;
}

.progress-slider::-webkit-slider-thumb {
  appearance: none;
  width: 16px;
  height: 16px;
  background: #1976d2;
  border-radius: 50%;
  cursor: pointer;
}

.progress-slider::-moz-range-thumb {
  width: 16px;
  height: 16px;
  background: #1976d2;
  border-radius: 50%;
  cursor: pointer;
  border: none;
}

.time-display {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.875rem;
  color: #666;
}

.playback-speed, .framerate-control {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.playback-speed label, .framerate-control label {
  font-weight: 500;
  color: #333;
  min-width: 45px;
}

.playback-speed select, .framerate-control select {
  padding: 0.5rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  background: white;
  font-size: 0.875rem;
  min-width: 80px;
}

.export-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
}

.export-card {
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  padding: 1rem;
  transition: all 0.2s ease;
  background: white;
}

.export-card:hover {
  border-color: #1976d2;
  box-shadow: 0 4px 12px rgba(25, 118, 210, 0.1);
}

.export-info h4 {
  font-size: 1rem;
  font-weight: 600;
  color: #333;
  margin: 0 0 0.25rem 0;
}

.export-info p {
  color: #666;
  margin: 0 0 0.5rem 0;
  font-size: 0.875rem;
}

.export-stats {
  font-size: 0.75rem;
  color: #1976d2;
  font-weight: 500;
}

.export-btn {
  width: 100%;
  padding: 0.5rem 0.75rem;
  background: #1976d2;
  color: white;
  border: none;
  border-radius: 4px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  margin-top: 0.75rem;
  font-size: 0.875rem;
}

.export-btn:hover:not(:disabled) {
  background: #1565c0;
}

.export-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.management-actions {
  display: flex;
  gap: 1rem;
}

.danger-btn {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1.5rem;
  background: #f44336;
  color: white;
  border: none;
  border-radius: 6px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.danger-btn:hover {
  background: #d32f2f;
}

.danger-btn i {
  font-size: 14px;
}

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  border-radius: 12px;
  padding: 2rem;
  max-width: 400px;
  width: 90%;
  text-align: center;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
}

.modal-content h3 {
  color: #f44336;
  margin: 0 0 1rem 0;
}

.modal-content p {
  color: #666;
  margin: 0 0 2rem 0;
}

.modal-actions {
  display: flex;
  gap: 1rem;
  justify-content: center;
}

.cancel-btn, .delete-btn {
  padding: 0.75rem 2rem;
  border: none;
  border-radius: 6px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.cancel-btn {
  background: #f0f0f0;
  color: #333;
  border: none;
}

.cancel-btn:hover {
  background: #e0e0e0;
}

.delete-btn {
  background: #f44336;
  color: white;
}

.delete-btn:hover {
  background: #d32f2f;
}

.retry-btn {
  padding: 1rem 2rem;
  background: #1976d2;
  color: white;
  border: none;
  border-radius: 6px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.retry-btn:hover {
  background: #1565c0;
}

@media (max-width: 768px) {
  .recorded-train-header {
    flex-direction: column;
    gap: 1rem;
  }
  
  .time-controls {
    flex-direction: column;
    align-items: stretch;
  }
  
  .export-grid {
    grid-template-columns: 1fr;
  }

  .video-player-panel {
    padding: 1rem;
  }

  .playback-controls {
    flex-wrap: wrap;
    gap: 0.5rem;
  }

  .frame-info {
    margin-left: 0;
    order: -1;
    width: 100%;
    text-align: center;
  }

  .progress-container {
    order: 1;
  }

  .control-settings {
    flex-direction: column;
    gap: 0.5rem;
  }

  .playback-speed, .framerate-control {
    justify-content: center;
  }
}
</style>
