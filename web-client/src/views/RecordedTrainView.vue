<template>
  <div class="recorded-train-view">
    <AppHeader />

    <main class="recorded-train-main">
      <div class="recorded-train-header">
        <div class="header-info">
          <button class="back-btn" @click="goBack">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor">
              <path d="M20 11H7.83l5.59-5.59L12 4l-8 8 8 8 1.41-1.41L7.83 13H20v-2z"/>
            </svg>
            Back to Home
          </button>
          <div class="train-title">
            <h1>Recorded Data: Train {{ trainId }}</h1>
            <p v-if="trainMetadata">
              {{ formatNumber(trainMetadata.frameCount) }} frames, 
              {{ formatNumber(trainMetadata.telemetryCount) }} telemetry records
              <span v-if="trainMetadata.duration"> • {{ formatDuration(trainMetadata.duration) }}</span>
            </p>
          </div>
        </div>
        <div class="header-actions">
          <button class="refresh-btn" @click="loadTrainData" :disabled="loading">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" :class="{ 'spinning': loading }">
              <path d="M12 5V1L7 6l5 5V7c3.31 0 6 2.69 6 6s-2.69 6-6 6-6-2.69-6-6H4c0 4.42 3.58 8 8 8s8-3.58 8-8-3.58-8-8-8z"/>
            </svg>
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
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor">
            <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.42 0-8-3.58-8-8s3.58-8 8-8 8 3.58 8 8-3.58 8-8 8zm-1-13h2v6h-2zm0 8h2v2h-2z"/>
          </svg>
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

        <!-- Export Actions -->
        <div class="export-panel">
          <h3>Export Options</h3>
          <div class="export-grid">
            <div class="export-card">
              <div class="export-info">
                <h4>Video Frames</h4>
                <p>Export H.264 video data</p>
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
                <h4>Telemetry Data</h4>
                <p>Export telemetry as JSON</p>
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
                <p>Export sensor data as JSON</p>
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
                <p>Export latency statistics as JSON</p>
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
          </div>
        </div>

        <!-- Data Management -->
        <div class="management-panel">
          <h3>Data Management</h3>
          <div class="management-actions">
            <button class="danger-btn" @click="confirmDelete = true">
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor">
                <path d="M6 19c0 1.1.9 2 2 2h8c1.1 0 2-.9 2-2V7H6v12zM19 4h-3.5l-1-1h-5l-1 1H5v2h14V4z"/>
              </svg>
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
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import AppHeader from '@/components/AppHeader.vue'
import { useDataStorage } from '@/scripts/dataStorage'

const route = useRoute()
const router = useRouter()
const dataStorage = useDataStorage()

const trainId = computed(() => route.params.trainId)

const loading = ref(false)
const trainMetadata = ref(null)
const confirmDelete = ref(false)

const exporting = ref({
  video: false,
  telemetry: false,
  sensor: false,
  latency: false
})

const frameCountInRange = ref(0)
const telemetryCountInRange = ref(0)
const sensorCountInRange = ref(0)

const selectedTimeRange = ref({
  start: null,
  end: null
})

const startTimeInput = ref('')
const endTimeInput = ref('')

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

const loadTrainData = async () => {
  loading.value = true
  try {
    await dataStorage.init()
    const metadata = await dataStorage.getRecordedTrainsMetadata()
    trainMetadata.value = metadata.find(train => train.trainId === trainId.value)
    
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
}

const updateCountsInRange = async () => {
  try {
    if (!trainMetadata.value) {
      frameCountInRange.value = 0
      telemetryCountInRange.value = 0
      sensorCountInRange.value = 0
      return
    }

    // If no specific time range is selected, use total counts
    if (!selectedTimeRange.value.start || !selectedTimeRange.value.end) {
      frameCountInRange.value = trainMetadata.value?.frameCount || 0
      telemetryCountInRange.value = trainMetadata.value?.telemetryCount || 0
      sensorCountInRange.value = trainMetadata.value?.sensorCount || 0
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
      return
    }

    // Get counts for the selected time range
    const [frames, telemetry, sensorData] = await Promise.all([
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
      })
    ])
    
    console.log('📊 Query results:', {
      frames: frames.length,
      telemetry: telemetry.length,
      sensorData: sensorData.length
    })
    
    frameCountInRange.value = frames.length
    telemetryCountInRange.value = telemetry.length
    sensorCountInRange.value = sensorData.length
  } catch (error) {
    console.error('Failed to update counts in range:', error)
    // Fallback to total counts if there's an error
    frameCountInRange.value = trainMetadata.value?.frameCount || 0
    telemetryCountInRange.value = trainMetadata.value?.telemetryCount || 0
    sensorCountInRange.value = trainMetadata.value?.sensorCount || 0
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

onMounted(() => {
  loadTrainData()
})
</script>

<style scoped>
.recorded-train-view {
  min-height: 100vh;
  background: #f8f9fa;
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

.back-btn svg {
  width: 16px;
  height: 16px;
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

.refresh-btn svg {
  width: 16px;
  height: 16px;
  transition: transform 0.5s ease;
}

.refresh-btn svg.spinning {
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

.error-icon svg {
  width: 40px;
  height: 40px;
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

.danger-btn svg {
  width: 16px;
  height: 16px;
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
}
</style>
