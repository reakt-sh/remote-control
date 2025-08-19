<template>
  <div class="recorded-train-selector-container">
    <div class="recorded-train-selector-header">
      <h2 class="recorded-train-selector-title">Recorded Train Data</h2>
      <button class="refresh-btn" @click="loadRecordedTrains" :disabled="loading">
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" :class="{ 'spinning': loading }">
          <path d="M12 5V1L7 6l5 5V7c3.31 0 6 2.69 6 6s-2.69 6-6 6-6-2.69-6-6H4c0 4.42 3.58 8 8 8s8-3.58 8-8-3.58-8-8-8z"/>
        </svg>
        Refresh
      </button>
    </div>

    <transition name="fade" mode="out-in">
      <div v-if="loading" class="loading-state">
        <div class="loading-spinner"></div>
        <p>Loading recorded train data...</p>
      </div>
      <div v-else-if="recordedTrains.length > 0" class="train-grid">
        <div
          v-for="train in recordedTrains"
          :key="train.trainId"
          class="train-card"
          @click="selectRecordedTrain(train.trainId)"
        >
          <div class="train-card-gradient"></div>
          <div class="train-icon">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor">
              <path d="M18 3v2h-2V3H8v2H6V3H4v18h2v-2h2v2h8v-2h2v2h2V3h-2zM8 17c-.55 0-1-.45-1-1s.45-1 1-1 1 .45 1 1-.45 1-1 1zm8 0c-.55 0-1-.45-1-1s.45-1 1-1 1 .45 1 1-.45 1-1 1zm2-4H6V7h12v6z"/>
            </svg>
          </div>
          <div class="train-info">
            <div class="train-id">Train ID</div>
            <div class="train-id-value">{{ train.trainId }}</div>
            <div class="train-stats">
              <div class="stat-item">
                <span class="stat-label">Frames:</span>
                <span class="stat-value">{{ formatNumber(train.frameCount) }}</span>
              </div>
              <div class="stat-item">
                <span class="stat-label">Telemetry:</span>
                <span class="stat-value">{{ formatNumber(train.telemetryCount) }}</span>
              </div>
              <div class="stat-item">
                <span class="stat-label">Size:</span>
                <span class="stat-value">{{ train.totalSizeMB }} MB</span>
              </div>
              <div class="stat-item" v-if="train.duration">
                <span class="stat-label">Duration:</span>
                <span class="stat-value">{{ formatDuration(train.duration) }}</span>
              </div>
              <div class="stat-item" v-if="train.lastUpdated">
                <span class="stat-label">Last Updated:</span>
                <span class="stat-value">{{ formatDate(train.lastUpdated) }}</span>
              </div>
            </div>
          </div>
          <div class="select-train-btn">
            <span>View Records</span>
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor">
              <path d="M8.59 16.59L13.17 12 8.59 7.41 10 6l6 6-6 6-1.41-1.41z"/>
            </svg>
          </div>
        </div>
      </div>
      <div v-else class="no-trains-message">
        <div class="no-trains-icon">
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor">
            <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.42 0-8-3.58-8-8s3.58-8 8-8 8 3.58 8 8-3.58 8-8 8zm-1-13h2v6h-2zm0 8h2v2h-2z"/>
          </svg>
        </div>
        <h3>No Recorded Data</h3>
        <p>No recorded train sessions found in local storage</p>
        <button class="retry-btn" @click="loadRecordedTrains">
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor">
            <path d="M12 5V1L7 6l5 5V7c3.31 0 6 2.69 6 6s-2.69 6-6 6-6-2.69-6-6H4c0 4.42 3.58 8 8 8s8-3.58 8-8-3.58-8-8-8z"/>
          </svg>
          Check Again
        </button>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useDataStorage } from '@/scripts/dataStorage'

const router = useRouter()
const dataStorage = useDataStorage()

const recordedTrains = ref([])
const loading = ref(false)

const loadRecordedTrains = async () => {
  loading.value = true
  try {
    await dataStorage.init()
    const metadata = await dataStorage.getRecordedTrainsMetadata()
    recordedTrains.value = metadata
  } catch (error) {
    console.error('Failed to load recorded trains:', error)
  } finally {
    loading.value = false
  }
}

const selectRecordedTrain = (trainId) => {
  router.push(`/${trainId}/record`)
}

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
  loadRecordedTrains()
})
</script>

<style scoped>
.recorded-train-selector-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem;
  background: #ffffff;
  border-radius: 16px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.08);
  margin-top: 2rem;
}

.recorded-train-selector-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
}

.recorded-train-selector-title {
  font-size: 1.75rem;
  font-weight: 700;
  color: #1a237e;
  margin: 0;
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
  transform: translateY(-1px);
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

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 4rem 2rem;
  color: #666;
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

.train-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 1.5rem;
}

.train-card {
  position: relative;
  background: white;
  border-radius: 12px;
  border: 2px solid #e3f2fd;
  padding: 1.5rem;
  cursor: pointer;
  transition: all 0.3s ease;
  overflow: hidden;
}

.train-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 40px rgba(25, 118, 210, 0.15);
  border-color: #1976d2;
}

.train-card-gradient {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 4px;
  background: linear-gradient(90deg, #1976d2, #42a5f5);
}

.train-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 60px;
  height: 60px;
  background: linear-gradient(135deg, #1976d2, #42a5f5);
  border-radius: 12px;
  margin-bottom: 1rem;
}

.train-icon svg {
  width: 32px;
  height: 32px;
  color: white;
}

.train-info {
  margin-bottom: 1.5rem;
}

.train-id {
  font-size: 0.875rem;
  color: #666;
  margin-bottom: 0.25rem;
  font-weight: 500;
}

.train-id-value {
  font-size: 1.25rem;
  font-weight: 700;
  color: #1a237e;
  margin-bottom: 1rem;
}

.train-stats {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 0.5rem;
}

.stat-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.875rem;
}

.stat-label {
  color: #666;
  font-weight: 500;
}

.stat-value {
  color: #1976d2;
  font-weight: 600;
}

.select-train-btn {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  padding: 0.75rem 1rem;
  background: linear-gradient(135deg, #1976d2, #42a5f5);
  color: white;
  border-radius: 8px;
  font-weight: 600;
  transition: all 0.2s ease;
}

.select-train-btn:hover {
  background: linear-gradient(135deg, #1565c0, #1e88e5);
  transform: translateY(-1px);
}

.select-train-btn svg {
  width: 20px;
  height: 20px;
  transition: transform 0.2s ease;
}

.train-card:hover .select-train-btn svg {
  transform: translateX(4px);
}

.no-trains-message {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 4rem 2rem;
  text-align: center;
}

.no-trains-icon {
  width: 80px;
  height: 80px;
  background: #f5f5f5;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 1.5rem;
}

.no-trains-icon svg {
  width: 40px;
  height: 40px;
  color: #bbb;
}

.no-trains-message h3 {
  font-size: 1.5rem;
  font-weight: 600;
  color: #333;
  margin: 0 0 0.5rem 0;
}

.no-trains-message p {
  color: #666;
  margin-bottom: 2rem;
  font-size: 1rem;
}

.retry-btn {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 1rem 2rem;
  background: #1976d2;
  color: white;
  border: none;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}

.retry-btn:hover {
  background: #1565c0;
  transform: translateY(-2px);
}

.retry-btn svg {
  width: 18px;
  height: 18px;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

@media (max-width: 768px) {
  .train-grid {
    grid-template-columns: 1fr;
  }
  
  .recorded-train-selector-header {
    flex-direction: column;
    gap: 1rem;
    align-items: stretch;
  }
  
  .train-stats {
    grid-template-columns: 1fr;
  }
}
</style>
