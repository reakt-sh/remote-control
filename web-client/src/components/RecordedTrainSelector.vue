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
      <div v-else-if="recordedTrains.length > 0" class="train-carousel-container">
        <button 
          class="carousel-nav-btn left" 
          @click="scrollLeft" 
          :disabled="!canScrollLeft"
          v-show="recordedTrains.length > visibleCards"
        >
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor">
            <path d="M15.41 7.41L14 6l-6 6 6 6 1.41-1.41L10.83 12z"/>
          </svg>
        </button>
        
        <div class="train-carousel" ref="trainCarousel" @scroll="updateScrollPosition">
          <div class="train-grid">
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
            <div class="train-id-value">{{ train.trainId }}</div>
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
          <div class="select-train-btn">
            <span>View Records</span>
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor">
              <path d="M8.59 16.59L13.17 12 8.59 7.41 10 6l6 6-6 6-1.41-1.41z"/>
            </svg>
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
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor">
            <path d="M8.59 16.59L13.17 12 8.59 7.41 10 6l6 6-6 6-1.41-1.41z"/>
          </svg>
        </button>
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
    await dataStorage.init()
    const metadata = await dataStorage.getRecordedTrainsMetadata()
    recordedTrains.value = metadata
    await nextTick()
    updateVisibleCards()
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

.carousel-nav-btn svg {
  width: 20px;
  height: 20px;
}

.train-carousel {
  flex: 1;
  overflow-x: auto;
  overflow-y: hidden;
  scroll-behavior: smooth;
  scrollbar-width: none; /* Firefox */
  -ms-overflow-style: none; /* Internet Explorer 10+ */
}

.train-carousel::-webkit-scrollbar {
  display: none; /* WebKit */
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

.train-icon svg {
  width: 20px;
  height: 20px;
  color: white;
}

.train-info {
  margin-bottom: 1rem;
}

.train-id {
  font-size: 0.75rem;
  color: #8e9aaf;
  margin-bottom: 0.25rem;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.5px;
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

.stat-label {
  color: #8e9aaf;
  font-weight: 500;
  font-size: 0.75rem;
}

.stat-value {
  color: #4a5568;
  font-weight: 600;
  font-size: 0.8rem;
}

.select-train-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  padding: 0.6rem 1rem;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-radius: 10px;
  font-weight: 600;
  font-size: 0.8rem;
  transition: all 0.3s ease;
  gap: 0.5rem;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
}

.select-train-btn:hover {
  background: linear-gradient(135deg, #5a67d8 0%, #6b46c1 100%);
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
}

.select-train-btn svg {
  width: 14px;
  height: 14px;
  transition: transform 0.3s ease;
}

.train-card:hover .select-train-btn svg {
  transform: translateX(3px);
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
  .train-carousel-container {
    gap: 0.5rem;
  }
  
  .carousel-nav-btn {
    width: 32px;
    height: 32px;
  }
  
  .carousel-nav-btn svg {
    width: 16px;
    height: 16px;
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
  
  .train-icon {
    width: 32px;
    height: 32px;
  }
  
  .train-icon svg {
    width: 16px;
    height: 16px;
  }
  
  .train-id-value {
    font-size: 0.9rem;
  }
  
  .stat-item {
    font-size: 0.75rem;
  }
  
  .select-train-btn {
    padding: 0.5rem 0.8rem;
    font-size: 0.75rem;
  }
}
</style>
