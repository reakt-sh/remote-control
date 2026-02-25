<template>
  <div class="recorded-train-selector-container">
    <div class="recorded-train-selector-header">
      <h2 class="recorded-train-selector-title">Recorded Train Data</h2>

      <div class="header-actions">
        <div v-if="recordedTrains.length" class="selection-toolbar">
          <button class="toggle-select-btn" @click="toggleSelectionMode" :class="{ active: selectionMode }" :title="selectionMode ? 'Cancel' : 'Multi-Select'">
            <template v-if="!selectionMode">
              <i class="fas fa-list-check"></i>
              <span>Multi-Select</span>
            </template>
            <template v-else>
              <i class="fas fa-xmark" style="color: #dc2626;" aria-label="Cancel"></i>
            </template>
          </button>

          <div v-if="selectionMode" class="bulk-actions">
            <span class="selected-count">Selected: {{ selectedCount }}</span>
            <button class="bulk-delete-btn" @click="openBulkDeleteDialog" :disabled="selectedCount === 0">
              <i class="fas fa-trash-can"></i>
              Delete Selected
            </button>
          </div>
        </div>

        <button class="refresh-btn" @click="loadRecordedTrains" :disabled="loading">
          <i class="fas fa-rotate" :class="{ 'spinning': loading }"></i>
          Refresh
        </button>
      </div>
    </div>

    <transition name="fade" mode="out-in">
      <div v-if="loading" class="loading-state">
        <div class="loading-spinner"></div>
        <p>Loading recorded train data...</p>
      </div>
      <div v-else-if="recordedTrains.length > 0" class="train-carousel-container">
        <button 
          class="carousel-nav-btn left" 
          @click="scrollLeft" 
          :disabled="!canScrollLeft"
          v-show="recordedTrains.length > visibleCards"
        >
          <i class="fas fa-chevron-left"></i>
        </button>
        
        <div class="train-carousel" ref="trainCarousel" @scroll="updateScrollPosition">
          <div class="train-grid">
            <div
              v-for="train in recordedTrains"
              :key="train.trainId"
              class="train-card"
              :class="{ selected: isSelected(train.trainId) && selectionMode }"
              @click="onCardClick(train.trainId)"
            >
          <div class="train-card-gradient"></div>
          <div class="card-actions">
            <button 
              class="delete-btn" 
              @click.stop="confirmDeleteTrain(train.trainId)"
              :disabled="deletingTrainId === train.trainId"
              :title="`Delete ${train.trainId} recorded data`"
            >
              <div class="delete-btn-content">
                <i v-if="deletingTrainId !== train.trainId" class="fas fa-trash-can"></i>
                <div v-else class="delete-spinner"></div>
                <span class="delete-tooltip">Delete</span>
              </div>
            </button>
          </div>
          <div class="train-icon">
            <i class="fas fa-train"></i>
          </div>
          <div class="train-info">
            <div class="train-id-value">{{ formatTrainId(train.trainId) }}</div>
            <div class="train-stats">
              <div class="stat-item">
                <span class="stat-icon">📹</span>
                <span class="stat-value">{{ formatNumber(train.frameCount) }}</span>
              </div>
              <div class="stat-item">
                <span class="stat-icon">📊</span>
                <span class="stat-value">{{ formatNumber(train.telemetryCount) }}</span>
              </div>
              <div class="stat-item" v-if="train.duration">
                <span class="stat-icon">⏱️</span>
                <span class="stat-value">{{ formatDuration(train.duration) }}</span>
              </div>
              <div class="stat-item" v-if="train.lastUpdated">
                <span class="stat-icon">🕒</span>
                <span class="stat-value">{{ formatRelativeTime(train.lastUpdated) }}</span>
              </div>
            </div>
          </div>
            </div>
          </div>
        </div>
        
        <button 
          class="carousel-nav-btn right" 
          @click="scrollRight" 
          :disabled="!canScrollRight"
          v-show="recordedTrains.length > visibleCards"
        >
          <i class="fas fa-chevron-right"></i>
        </button>
      </div>
      <div v-else class="no-trains-message">
        <div class="no-trains-icon">
          <i class="fas fa-circle-info"></i>
        </div>
        <h3>No Recorded Data</h3>
        <p>No recorded train sessions found in local storage</p>
        <button class="retry-btn" @click="loadRecordedTrains">
          <i class="fas fa-rotate"></i>
          Check Again
        </button>
      </div>
    </transition>

    <!-- Delete Confirmation Dialog -->
    <div v-if="showDeleteDialog" class="delete-dialog-overlay" @click="cancelDelete">
      <div class="delete-dialog" @click.stop>
        <div class="delete-dialog-header">
          <div class="delete-dialog-icon">
            <i class="fas fa-circle-exclamation"></i>
          </div>
          <h3>Delete Recorded Data</h3>
          <button class="dialog-close-btn" @click="cancelDelete">
            <i class="fas fa-xmark"></i>
          </button>
        </div>
        <div class="delete-dialog-body">
          <template v-if="isBulkDelete">
            <p>Are you sure you want to delete <strong>{{ deleteTargets.length }}</strong> selected records?</p>
            <div class="ids-preview" v-if="deleteTargets.length">
              <div class="id-chip" v-for="id in previewDeleteIds" :key="id">{{ formatTrainId(id) }}</div>
              <div class="id-chip more" v-if="deleteTargets.length > previewDeleteLimit">+{{ deleteTargets.length - previewDeleteLimit }}</div>
            </div>
            <p class="delete-warning">This action cannot be undone and will permanently remove frames, telemetry, and data for all selected records.</p>
          </template>
          <template v-else>
            <p>Are you sure you want to delete all recorded data for <strong>{{ trainToDelete }}</strong>?</p>
            <p class="delete-warning">This action cannot be undone and will permanently remove all frames, telemetry, and sensor data.</p>
          </template>
        </div>
        <div class="delete-dialog-actions">
          <button class="cancel-btn" @click="cancelDelete">Cancel</button>
          <button class="confirm-delete-btn" @click="confirmDelete" :disabled="deletingTrainId || bulkDeleting">
            <i v-if="!deletingTrainId && !bulkDeleting" class="fas fa-trash-can"></i>
            <div v-else class="delete-spinner"></div>
            <span>{{ (deletingTrainId || bulkDeleting) ? 'Deleting...' : 'Delete' }}</span>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { useDataStorage } from '@/scripts/dataStorage'

const router = useRouter()
const dataStorage = useDataStorage()

const recordedTrains = ref([])
const loading = ref(false)
const trainCarousel = ref(null)
const scrollPosition = ref(0)
const visibleCards = ref(4) // Number of cards visible at once

// Delete dialog state
const showDeleteDialog = ref(false)
const trainToDelete = ref('')
const deletingTrainId = ref(null)

// Bulk selection state
const selectionMode = ref(false)
const selectedTrainIds = ref([])
const deleteTargets = ref([])
const bulkDeleting = ref(false)
const selectedCount = computed(() => selectedTrainIds.value.length)
const isBulkDelete = computed(() => deleteTargets.value.length > 0 && !trainToDelete.value)
const previewDeleteLimit = 6
const previewDeleteIds = computed(() => deleteTargets.value.slice(0, previewDeleteLimit))

// Computed properties for navigation
const canScrollLeft = computed(() => scrollPosition.value > 0)
const canScrollRight = computed(() => {
  if (!trainCarousel.value) return false
  const maxScroll = trainCarousel.value.scrollWidth - trainCarousel.value.clientWidth
  return scrollPosition.value < maxScroll
})

// Carousel navigation methods
const scrollLeft = () => {
  if (trainCarousel.value && canScrollLeft.value) {
    const cardWidth = 220 // Card width + gap
    const newPosition = Math.max(0, scrollPosition.value - cardWidth * 2)
    trainCarousel.value.scrollTo({
      left: newPosition,
      behavior: 'smooth'
    })
    scrollPosition.value = newPosition
  }
}

const scrollRight = () => {
  if (trainCarousel.value && canScrollRight.value) {
    const cardWidth = 220 // Card width + gap
    const maxScroll = trainCarousel.value.scrollWidth - trainCarousel.value.clientWidth
    const newPosition = Math.min(maxScroll, scrollPosition.value + cardWidth * 2)
    trainCarousel.value.scrollTo({
      left: newPosition,
      behavior: 'smooth'
    })
    scrollPosition.value = newPosition
  }
}

// Update scroll position when user scrolls manually
const updateScrollPosition = () => {
  if (trainCarousel.value) {
    scrollPosition.value = trainCarousel.value.scrollLeft
  }
}

// Update visible cards based on container width
const updateVisibleCards = () => {
  if (trainCarousel.value) {
    const containerWidth = trainCarousel.value.clientWidth
    const cardWidth = 220 // Card width + gap
    visibleCards.value = Math.floor(containerWidth / cardWidth)
  }
}

const loadRecordedTrains = async () => {
  loading.value = true
  try {
    const metadata = await dataStorage.getRecordedTrainsMetadata()
    recordedTrains.value = metadata
    await nextTick()
    updateVisibleCards()
    // Reset selection if list changes
    selectedTrainIds.value = []
    selectionMode.value = false
  } catch (error) {
    console.error('Failed to load recorded trains:', error)
  } finally {
    loading.value = false
  }
}

const selectRecordedTrain = (trainId) => {
  router.push(`/${trainId}/record`)
}

const toggleSelectionMode = () => {
  selectionMode.value = !selectionMode.value
  if (!selectionMode.value) {
    selectedTrainIds.value = []
  }
}

const isSelected = (trainId) => selectedTrainIds.value.includes(trainId)

const toggleSelectTrain = (trainId) => {
  if (isSelected(trainId)) {
    selectedTrainIds.value = selectedTrainIds.value.filter(id => id !== trainId)
  } else {
    selectedTrainIds.value = [...selectedTrainIds.value, trainId]
  }
}

const onCardClick = (trainId) => {
  if (selectionMode.value) {
    toggleSelectTrain(trainId)
  } else {
    selectRecordedTrain(trainId)
  }
}

// selection clearing is handled by exiting selection mode

// Delete methods
const confirmDeleteTrain = (trainId) => {
  deleteTargets.value = []
  trainToDelete.value = trainId
  showDeleteDialog.value = true
}

const cancelDelete = () => {
  showDeleteDialog.value = false
  trainToDelete.value = ''
  deletingTrainId.value = null
  deleteTargets.value = []
  bulkDeleting.value = false
}

const confirmDelete = async () => {
  // Bulk delete path
  if (isBulkDelete.value) {
    bulkDeleting.value = true
    try {
      for (const id of deleteTargets.value) {
        await dataStorage.deleteTrainDatabase(id)
      }

      // Update local list
      const toDeleteSet = new Set(deleteTargets.value)
      recordedTrains.value = recordedTrains.value.filter(train => !toDeleteSet.has(train.trainId))
      console.log(`✅ Successfully deleted ${deleteTargets.value.length} selected records`)

      // Reset selection
      selectedTrainIds.value = []
      selectionMode.value = false

      // Close dialog and refresh
      showDeleteDialog.value = false
      deleteTargets.value = []
      await loadRecordedTrains()
    } catch (error) {
      console.error('❌ Failed to delete selected records:', error)
    } finally {
      bulkDeleting.value = false
    }
    return
  }

  // Single delete path
  if (!trainToDelete.value) return
  deletingTrainId.value = trainToDelete.value
  try {
    await dataStorage.deleteTrainDatabase(trainToDelete.value)
    recordedTrains.value = recordedTrains.value.filter(train => train.trainId !== trainToDelete.value)
    console.log(`✅ Successfully deleted train data: ${trainToDelete.value}`)
    showDeleteDialog.value = false
    trainToDelete.value = ''
    await loadRecordedTrains()
  } catch (error) {
    console.error('❌ Failed to delete train data:', error)
  } finally {
    deletingTrainId.value = null
  }
}

const openBulkDeleteDialog = () => {
  if (selectedTrainIds.value.length === 0) return
  trainToDelete.value = ''
  deleteTargets.value = [...selectedTrainIds.value]
  showDeleteDialog.value = true
}

const formatNumber = (num) => {
  if (num >= 1000000) {
    return (num / 1000000).toFixed(1) + 'M'
  } else if (num >= 1000) {
    return (num / 1000).toFixed(1) + 'K'
  }
  return num.toString()
}

const formatTrainId = (trainId) => {
  if (trainId && trainId.length > 12) {
    return trainId.slice(-12)
  }
  return trainId
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

const formatRelativeTime = (timestamp) => {
  const now = Date.now()
  const diff = now - timestamp
  const minutes = Math.floor(diff / (1000 * 60))
  const hours = Math.floor(diff / (1000 * 60 * 60))
  const days = Math.floor(diff / (1000 * 60 * 60 * 24))
  
  if (days > 0) {
    return `${days}d ago`
  } else if (hours > 0) {
    return `${hours}h ago`
  } else if (minutes > 0) {
    return `${minutes}m ago`
  } else {
    return 'Just now'
  }
}

onMounted(() => {
  loadRecordedTrains()
  
  // Add scroll event listener
  if (trainCarousel.value) {
    trainCarousel.value.addEventListener('scroll', updateScrollPosition)
  }
  
  // Add resize event listener
  window.addEventListener('resize', updateVisibleCards)
})

// Cleanup event listeners
onUnmounted(() => {
  if (trainCarousel.value) {
    trainCarousel.value.removeEventListener('scroll', updateScrollPosition)
  }
  window.removeEventListener('resize', updateVisibleCards)
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

.header-actions {
  display: flex;
  align-items: center;
  gap: 0.75rem;
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

.refresh-btn i {
  font-size: 16px;
  transition: transform 0.5s ease;
}

.refresh-btn i.spinning {
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

.train-carousel-container {
  position: relative;
  display: flex;
  align-items: center;
  gap: 1rem;
}

.carousel-nav-btn {
  position: relative;
  z-index: 2;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  background: #1976d2;
  color: white;
  border: none;
  border-radius: 50%;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 4px 12px rgba(25, 118, 210, 0.3);
  flex-shrink: 0;
}

.carousel-nav-btn:hover:not(:disabled) {
  background: #1565c0;
  transform: scale(1.1);
  box-shadow: 0 6px 20px rgba(25, 118, 210, 0.4);
}

.carousel-nav-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
  transform: none;
}

.carousel-nav-btn i {
  font-size: 20px;
}

.train-carousel {
  flex: 1;
  overflow-x: auto;
  overflow-y: hidden;
  scroll-behavior: smooth;
  scrollbar-width: thin; /* Firefox */
  scrollbar-color: #1976d2 #e3f2fd; /* Firefox */
  padding-bottom: 0.5rem;
}

/* Custom scrollbar for WebKit browsers (Chrome, Safari, Edge) */
.train-carousel::-webkit-scrollbar {
  height: 8px;
}

.train-carousel::-webkit-scrollbar-track {
  background: #e3f2fd;
  border-radius: 10px;
}

.train-carousel::-webkit-scrollbar-thumb {
  background: #1976d2;
  border-radius: 10px;
  transition: background 0.2s ease;
}

.train-carousel::-webkit-scrollbar-thumb:hover {
  background: #1565c0;
}

.train-grid {
  display: flex;
  gap: 1rem;
  padding: 0.5rem 0;
}

.train-card {
  position: relative;
  background: white;
  border-radius: 16px;
  border: 1px solid #e8f4fd;
  padding: 1rem;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(25, 118, 210, 0.08);
  min-width: 200px;
  max-width: 200px;
  flex-shrink: 0;
}

.train-card:hover {
  transform: translateY(-6px);
  box-shadow: 0 20px 40px rgba(25, 118, 210, 0.2);
  border-color: #1976d2;
}

.train-card.selected {
  background: #fef2f2;
  border-color: #fecaca;
  box-shadow: 0 0 0 2px rgba(239, 68, 68, 0.15), 0 10px 30px rgba(239, 68, 68, 0.2);
}

.train-card-gradient {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: linear-gradient(90deg, #1976d2, #42a5f5, #81c784, #ffb74d);
  background-size: 200% 100%;
  animation: gradient-flow 3s ease infinite;
}

@keyframes gradient-flow {
  0%, 100% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
}

.train-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 12px;
  margin-bottom: 0.75rem;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
}

.train-icon i {
  font-size: 20px;
  color: white;
}

.train-info {
  margin-bottom: 1rem;
}

.train-id-value {
  font-size: 1rem;
  font-weight: 700;
  color: #2d3748;
  margin-bottom: 0.75rem;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.train-stats {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.8rem;
  padding: 0.25rem 0;
}

.stat-icon {
  font-size: 0.875rem;
  width: 16px;
  flex-shrink: 0;
}

.stat-value {
  color: #4a5568;
  font-weight: 600;
  font-size: 0.8rem;
}

/* removed .select-train-btn as card click navigates */

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

.no-trains-icon i {
  font-size: 40px;
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

.retry-btn i {
  font-size: 18px;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

/* Card Actions Container */
.card-actions {
  position: absolute;
  top: 0;
  right: 0;
  padding: 0.75rem;
  opacity: 0;
  transition: opacity 0.3s ease;
  z-index: 10;
}

.train-card:hover .card-actions {
  opacity: 1;
}

/* Professional Delete Button */
.delete-btn {
  position: relative;
  background: linear-gradient(135deg, #fff 0%, #f8fafc 100%);
  border: 2px solid transparent;
  border-radius: 10px;
  padding: 0.5rem;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 
    0 2px 8px rgba(0, 0, 0, 0.1),
    0 0 0 1px rgba(148, 163, 184, 0.1);
  backdrop-filter: blur(8px);
  overflow: hidden;
}

.delete-btn::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(135deg, #fee2e2 0%, #fecaca 100%);
  opacity: 0;
  transition: opacity 0.3s ease;
  border-radius: inherit;
}

.delete-btn:hover::before {
  opacity: 1;
}

.delete-btn:hover:not(:disabled) {
  transform: translateY(-2px) scale(1.05);
  box-shadow: 
    0 8px 25px rgba(239, 68, 68, 0.25),
    0 0 0 1px rgba(239, 68, 68, 0.2);
  border-color: rgba(239, 68, 68, 0.3);
}

.delete-btn:active:not(:disabled) {
  transform: translateY(-1px) scale(1.02);
}

.delete-btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
  transform: none;
}

.delete-btn-content {
  position: relative;
  z-index: 2;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
}

.delete-btn i {
  font-size: 16px;
  color: #64748b;
  transition: color 0.3s ease;
}

.delete-btn:hover:not(:disabled) i {
  color: #dc2626;
}

.delete-spinner {
  width: 14px;
  height: 14px;
  border: 2px solid rgba(239, 68, 68, 0.2);
  border-top: 2px solid #dc2626;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

/* Elegant Tooltip */
.delete-tooltip {
  position: absolute;
  top: 100%;
  left: 50%;
  transform: translateX(-50%) translateY(8px);
  background: rgba(30, 41, 59, 0.95);
  color: white;
  padding: 0.4rem 0.8rem;
  border-radius: 6px;
  font-size: 0.75rem;
  font-weight: 500;
  white-space: nowrap;
  opacity: 0;
  pointer-events: none;
  transition: all 0.3s ease;
  backdrop-filter: blur(8px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.delete-tooltip::before {
  content: '';
  position: absolute;
  bottom: 100%;
  left: 50%;
  transform: translateX(-50%);
  border: 4px solid transparent;
  border-bottom-color: rgba(30, 41, 59, 0.95);
}

.delete-btn:hover .delete-tooltip {
  opacity: 1;
  transform: translateX(-50%) translateY(4px);
}

/* Selection Toolbar */
.selection-toolbar {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.toggle-select-btn {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.6rem 1rem;
  background: #ffffff;
  color: #1f2937;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.toggle-select-btn.active {
  background: #eef2ff;
  border-color: #c7d2fe;
  color: #4338ca;
}

.toggle-select-btn:hover {
  background: #f9fafb;
}

.toggle-select-btn i {
  font-size: 16px;
}

.bulk-actions {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.selected-count {
  color: #4b5563;
  font-weight: 500;
}

/* removed unused .small-btn styles */

.bulk-delete-btn {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.6rem 1rem;
  background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
  color: white;
  border: none;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}

.bulk-delete-btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.bulk-delete-btn i {
  font-size: 16px;
}

/* Card selection visual handled by .train-card.selected */

/* Delete Dialog Styles */
.delete-dialog-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  backdrop-filter: blur(4px);
}

.delete-dialog {
  background: white;
  border-radius: 16px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  max-width: 500px;
  width: 90%;
  max-height: 90vh;
  overflow: auto;
  animation: dialogSlideIn 0.3s ease-out;
}

@keyframes dialogSlideIn {
  from {
    opacity: 0;
    transform: scale(0.9) translateY(-20px);
  }
  to {
    opacity: 1;
    transform: scale(1) translateY(0);
  }
}

.delete-dialog-header {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1.5rem 1.5rem 1rem 1.5rem;
  border-bottom: 1px solid #f1f5f9;
  position: relative;
}

.delete-dialog-icon {
  width: 48px;
  height: 48px;
  background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.delete-dialog-icon i {
  font-size: 24px;
  color: white;
}

.delete-dialog-header h3 {
  margin: 0;
  font-size: 1.25rem;
  font-weight: 600;
  color: #1f2937;
  flex: 1;
}

.dialog-close-btn {
  position: absolute;
  top: 1rem;
  right: 1rem;
  width: 32px;
  height: 32px;
  background: #f8fafc;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
}

.dialog-close-btn:hover {
  background: #e2e8f0;
}

.dialog-close-btn i {
  font-size: 16px;
  color: #64748b;
}

.delete-dialog-body {
  padding: 1rem 1.5rem 1.5rem 1.5rem;
}

.delete-dialog-body p {
  margin: 0 0 1rem 0;
  color: #374151;
  line-height: 1.5;
}

.ids-preview {
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem;
  margin: 0.5rem 0 0.75rem 0;
}

.id-chip {
  padding: 0.25rem 0.5rem;
  border-radius: 9999px;
  background: #f3f4f6;
  color: #374151;
  font-size: 0.75rem;
  border: 1px solid #e5e7eb;
}

.id-chip.more {
  background: #eef2ff;
  color: #4338ca;
  border-color: #c7d2fe;
}

.delete-dialog-body p:last-child {
  margin-bottom: 0;
}

.delete-warning {
  background: #fef2f2;
  border: 1px solid #fecaca;
  border-radius: 8px;
  padding: 0.75rem;
  color: #b91c1c !important;
  font-size: 0.875rem;
}

.delete-dialog-actions {
  display: flex;
  gap: 0.75rem;
  padding: 1rem 1.5rem 1.5rem 1.5rem;
  justify-content: flex-end;
}

.cancel-btn {
  padding: 0.75rem 1.5rem;
  background: #f8fafc;
  color: #475569;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.cancel-btn:hover {
  background: #e2e8f0;
  border-color: #cbd5e1;
}

.confirm-delete-btn {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1.5rem;
  background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
  color: white;
  border: none;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}

.confirm-delete-btn:hover:not(:disabled) {
  background: linear-gradient(135deg, #dc2626 0%, #b91c1c 100%);
  transform: translateY(-1px);
}

.confirm-delete-btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
  transform: none;
}

.confirm-delete-btn i {
  font-size: 16px;
}

@media (max-width: 768px) {
  .train-carousel-container {
    gap: 0.5rem;
  }
  
  .carousel-nav-btn {
    width: 32px;
    height: 32px;
  }
  
  .carousel-nav-btn i {
    font-size: 16px;
  }
  
  .train-grid {
    gap: 0.75rem;
  }
  
  .train-card {
    padding: 0.8rem;
    min-width: 160px;
    max-width: 160px;
  }
  
  .recorded-train-selector-header {
    flex-direction: column;
    gap: 1rem;
    align-items: stretch;
  }

  .header-actions {
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 0.5rem;
  }
  
  .train-icon {
    width: 32px;
    height: 32px;
  }
  
  .train-icon i {
    font-size: 16px;
  }
  
  .train-id-value {
    font-size: 0.9rem;
  }
  
  .stat-item {
    font-size: 0.75rem;
  }


  .card-actions {
    padding: 0.5rem;
    opacity: 1; /* Always visible on mobile */
  }

  .delete-btn {
    padding: 0.375rem;
  }

  .delete-btn-content {
    width: 20px;
    height: 20px;
  }

  .delete-btn i {
    font-size: 14px;
  }

  .delete-tooltip {
    display: none; /* Hide tooltip on mobile */
  }

  .delete-dialog {
    width: 95%;
    margin: 1rem;
  }

  .delete-dialog-header {
    padding: 1rem 1rem 0.75rem 1rem;
  }

  .delete-dialog-icon {
    width: 40px;
    height: 40px;
  }

  .delete-dialog-icon svg {
    width: 20px;
    height: 20px;
  }

  .delete-dialog-header h3 {
    font-size: 1.125rem;
  }

  .delete-dialog-body {
    padding: 0.75rem 1rem 1rem 1rem;
  }

  .delete-dialog-actions {
    padding: 0.75rem 1rem 1rem 1rem;
    flex-direction: column;
  }

  .cancel-btn,
  .confirm-delete-btn {
    width: 100%;
    justify-content: center;
  }
}
</style>
