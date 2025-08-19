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
          <h3>Time Range Selection</h3>
          <div class="time-controls">
            <div class="time-input-group">
              <label>Start Time:</label>
              <input
                type="datetime-local"
                v-model="startTimeInput"
                :max="endTimeInput"
                class="time-input"
              />
            </div>
            <div class="time-input-group">
              <label>End Time:</label>
              <input
                type="datetime-local"
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
              <div class="export-icon video">
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M17 10.5V7c0-.55-.45-1-1-1H4c-.55 0-1 .45-1 1v10c0 .55.45 1 1 1h12c.55 0 1-.45 1-1v-3.5l4 4v-11l-4 4z"/>
                </svg>
              </div>
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
              <div class="export-icon telemetry">
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zM9 17H7v-7h2v7zm4 0h-2V7h2v10zm4 0h-2v-4h2v4z"/>
                </svg>
              </div>
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
              <div class="export-icon sensor">
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>
                </svg>
              </div>
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
              <div class="export-icon combined">
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M14 2H6c-1.1 0-1.99.9-1.99 2L4 20c0 1.1.89 2 2 2h12c1.1 0 2-.9 2-2V8l-6-6zm4 18H6V4h7v5h5v11z"/>
                </svg>
              </div>
              <div class="export-info">
                <h4>Complete Dataset</h4>
                <p>Export all data types</p>
                <div class="export-stats">
                  Full dataset
                </div>
              </div>
              <button 
                class="export-btn"
                @click="exportAllData"
                :disabled="exporting.all"
              >
                <span v-if="exporting.all">Exporting...</span>
                <span v-else>Export All</span>
              </button>
            </div>
          </div>
        </div>

        <!-- Data Preview -->
        <div class="preview-panel">
          <h3>Data Preview</h3>
          <div class="preview-tabs">
            <button 
              v-for="tab in previewTabs" 
              :key="tab.id"
              :class="['tab-btn', { active: activeTab === tab.id }]"
              @click="activeTab = tab.id"
            >
              {{ tab.label }}
            </button>
          </div>
          
          <div class="preview-content">
            <div v-if="activeTab === 'overview'" class="overview-preview">
              <div class="stats-grid">
                <div class="stat-card">
                  <h4>Video Frames</h4>
                  <div class="stat-number">{{ formatNumber(trainMetadata.frameCount) }}</div>
                  <div class="stat-detail">{{ trainMetadata.totalSizeMB }} MB</div>
                </div>
                <div class="stat-card">
                  <h4>Telemetry Records</h4>
                  <div class="stat-number">{{ formatNumber(trainMetadata.telemetryCount) }}</div>
                  <div class="stat-detail">JSON data</div>
                </div>
                <div class="stat-card">
                  <h4>Sensor Records</h4>
                  <div class="stat-number">{{ formatNumber(trainMetadata.sensorCount) }}</div>
                  <div class="stat-detail">Multiple types</div>
                </div>
                <div class="stat-card">
                  <h4>Recording Duration</h4>
                  <div class="stat-number">{{ formatDuration(trainMetadata.duration) }}</div>
                  <div class="stat-detail">{{ formatDate(trainMetadata.startTime) }}</div>
                </div>
              </div>
            </div>
            
            <div v-else-if="activeTab === 'frames'" class="frames-preview">
              <p>Frame data preview will be implemented based on your specific needs</p>
            </div>
            
            <div v-else-if="activeTab === 'telemetry'" class="telemetry-preview">
              <p>Telemetry data preview will be implemented based on your specific needs</p>
            </div>
            
            <div v-else-if="activeTab === 'sensors'" class="sensors-preview">
              <p>Sensor data preview will be implemented based on your specific needs</p>
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
const activeTab = ref('overview')

const exporting = ref({
  video: false,
  telemetry: false,
  sensor: false,
  all: false
})

const selectedTimeRange = ref({
  start: null,
  end: null
})

const startTimeInput = ref('')
const endTimeInput = ref('')

const previewTabs = [
  { id: 'overview', label: 'Overview' },
  { id: 'frames', label: 'Video Frames' },
  { id: 'telemetry', label: 'Telemetry' },
  { id: 'sensors', label: 'Sensors' }
]

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
    selectedTimeRange.value.start = trainMetadata.value.startTime
    selectedTimeRange.value.end = trainMetadata.value.endTime
    
    startTimeInput.value = new Date(trainMetadata.value.startTime).toISOString().slice(0, 16)
    endTimeInput.value = new Date(trainMetadata.value.endTime).toISOString().slice(0, 16)
  }
}

const applyTimeRange = () => {
  selectedTimeRange.value.start = new Date(startTimeInput.value).getTime()
  selectedTimeRange.value.end = new Date(endTimeInput.value).getTime()
}

const getFrameCountInRange = () => {
  // This would need to be calculated based on the actual data
  // For now, return the total count or a placeholder
  return trainMetadata.value?.frameCount || 0
}

const getTelemetryCountInRange = () => {
  // This would need to be calculated based on the actual data
  return trainMetadata.value?.telemetryCount || 0
}

const getSensorCountInRange = () => {
  // This would need to be calculated based on the actual data
  return trainMetadata.value?.sensorCount || 0
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

const exportAllData = async () => {
  exporting.value.all = true
  try {
    // Export all data types sequentially
    await Promise.all([
      dataStorage.exportVideoFrames(trainId.value, selectedTimeRange.value.start, selectedTimeRange.value.end),
      dataStorage.exportTelemetryData(trainId.value, selectedTimeRange.value.start, selectedTimeRange.value.end),
      dataStorage.exportSensorData(trainId.value, selectedTimeRange.value.start, selectedTimeRange.value.end)
    ])
  } catch (error) {
    console.error('Failed to export all data:', error)
    alert('Failed to export all data. Please try again.')
  } finally {
    exporting.value.all = false
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

.time-range-panel, .export-panel, .preview-panel, .management-panel {
  background: white;
  padding: 2rem;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
}

.time-range-panel h3, .export-panel h3, .preview-panel h3, .management-panel h3 {
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
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 1.5rem;
}

.export-card {
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  padding: 1.5rem;
  transition: all 0.2s ease;
}

.export-card:hover {
  border-color: #1976d2;
  box-shadow: 0 4px 12px rgba(25, 118, 210, 0.1);
}

.export-icon {
  width: 48px;
  height: 48px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 1rem;
}

.export-icon.video {
  background: linear-gradient(135deg, #e91e63, #f06292);
}

.export-icon.telemetry {
  background: linear-gradient(135deg, #2196f3, #64b5f6);
}

.export-icon.sensor {
  background: linear-gradient(135deg, #ff9800, #ffb74d);
}

.export-icon.combined {
  background: linear-gradient(135deg, #9c27b0, #ba68c8);
}

.export-icon svg {
  width: 24px;
  height: 24px;
  color: white;
}

.export-info h4 {
  font-size: 1.125rem;
  font-weight: 600;
  color: #333;
  margin: 0 0 0.5rem 0;
}

.export-info p {
  color: #666;
  margin: 0 0 1rem 0;
}

.export-stats {
  font-size: 0.875rem;
  color: #1976d2;
  font-weight: 500;
}

.export-btn {
  width: 100%;
  padding: 0.75rem 1rem;
  background: #1976d2;
  color: white;
  border: none;
  border-radius: 6px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  margin-top: 1rem;
}

.export-btn:hover:not(:disabled) {
  background: #1565c0;
}

.export-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.preview-tabs {
  display: flex;
  gap: 1rem;
  margin-bottom: 1.5rem;
  border-bottom: 1px solid #e0e0e0;
}

.tab-btn {
  padding: 0.75rem 1rem;
  background: transparent;
  border: none;
  border-bottom: 2px solid transparent;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  color: #666;
}

.tab-btn.active {
  color: #1976d2;
  border-bottom-color: #1976d2;
}

.tab-btn:hover {
  color: #1976d2;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1.5rem;
}

.stat-card {
  padding: 1.5rem;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  text-align: center;
}

.stat-card h4 {
  font-size: 0.875rem;
  font-weight: 500;
  color: #666;
  margin: 0 0 0.5rem 0;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.stat-number {
  font-size: 2rem;
  font-weight: 700;
  color: #1976d2;
  margin-bottom: 0.25rem;
}

.stat-detail {
  font-size: 0.875rem;
  color: #666;
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
  
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .preview-tabs {
    flex-wrap: wrap;
  }
}
</style>
