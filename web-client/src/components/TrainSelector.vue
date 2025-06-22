<template>
  <div class="train-selector-container">
    <div class="train-selector-header">
      <h2 class="train-selector-title">Available Trains</h2>
      <div class="connection-status" :class="{ connected: availableTrains.length > 0 }">
        <span class="status-indicator"></span>
        {{ availableTrains.length > 0 ? 'Connected' : 'Disconnected' }}
      </div>
    </div>

    <transition name="fade" mode="out-in">
      <div v-if="availableTrains.length > 0" class="train-grid">
        <div
          v-for="id in availableTrains"
          :key="id"
          class="train-card"
          @click="selectTrain(id)"
        >
          <div class="train-card-gradient"></div>
          <div class="train-icon">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 2c-4.97 0-9 2.18-9 5v10c0 1.66 1.34 3 3 3h1v2h2v-2h6v2h2v-2h1c1.66 0 3-1.34 3-3V7c0-2.82-4.03-5-9-5zm0 2c3.87 0 7 1.79 7 3v2H5V7c0-1.21 3.13-3 7-3zm-7 5h14v8c0 .55-.45 1-1 1H6c-.55 0-1-.45-1-1V9zm3 3c-.83 0-1.5.67-1.5 1.5S7.17 15 8 15s1.5-.67 1.5-1.5S8.83 12 8 12zm8 0c-.83 0-1.5.67-1.5 1.5S15.17 15 16 15s1.5-.67 1.5-1.5S16.83 12 16 12z"/>
            </svg>
          </div>
          <div class="train-info">
            <div class="train-id">Train ID</div>
            <div class="train-id-value">{{ id }}</div>
          </div>
          <div class="select-train-btn">
            <span>Select</span>
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
        <h3>No Trains Connected</h3>
        <p>Please check your connection to the central server</p>
        <button class="retry-btn" @click="fetchAvailableTrains">
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor">
            <path d="M12 5V1L7 6l5 5V7c3.31 0 6 2.69 6 6s-2.69 6-6 6-6-2.69-6-6H4c0 4.42 3.58 8 8 8s8-3.58 8-8-3.58-8-8-8z"/>
          </svg>
          Retry Connection
        </button>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { storeToRefs } from 'pinia'
import { useTrainStore } from '@/stores/trainStore'
import { useRouter } from 'vue-router'

const { availableTrains } = storeToRefs(useTrainStore())
const router = useRouter()

const selectTrain = (id) => {
  router.push(`/${id}`)
}
</script>

<style scoped>
.train-selector-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem;
  background: #ffffff;
  border-radius: 16px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.08);
}

.train-selector-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
}

.train-selector-title {
  font-size: 1.75rem;
  font-weight: 700;
  color: #1a237e;
  margin: 0;
}

.connection-status {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.9rem;
  font-weight: 500;
  padding: 6px 12px;
  border-radius: 20px;
  background: #f5f5f5;
  color: #616161;
}

.connection-status.connected {
  background: #e8f5e9;
  color: #2e7d32;
}

.status-indicator {
  display: inline-block;
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: #9e9e9e;
}

.connected .status-indicator {
  background: #4caf50;
  box-shadow: 0 0 8px rgba(76, 175, 80, 0.6);
}

.train-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 1.5rem;
}

.train-card {
  position: relative;
  background: white;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
  transition: all 0.3s ease;
  cursor: pointer;
  border: 1px solid #e0e0e0;
  height: 220px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}

.train-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
  border-color: #5c6bc0;
}

.train-card-gradient {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 4px;
  background: linear-gradient(90deg, #3949ab, #5c6bc0);
}

.train-icon {
  padding: 1.5rem 1.5rem 0;
  color: #3949ab;
}

.train-icon svg {
  width: 40px;
  height: 40px;
}

.train-info {
  padding: 0 1.5rem;
}

.train-id {
  font-size: 0.85rem;
  font-weight: 500;
  color: #757575;
  margin-bottom: 4px;
}

.train-id-value {
  font-family: 'Roboto Mono', monospace;
  font-size: 1.1rem;
  font-weight: 600;
  color: #212121;
  word-break: break-all;
}

.select-train-btn {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 1.5rem;
  background: #f5f5f5;
  color: #3949ab;
  font-weight: 600;
  margin-top: auto;
  transition: all 0.2s ease;
}

.train-card:hover .select-train-btn {
  background: #3949ab;
  color: white;
}

.select-train-btn svg {
  width: 20px;
  height: 20px;
}

.no-trains-message {
  text-align: center;
  padding: 3rem 2rem;
  background: #fafafa;
  border-radius: 12px;
  border: 1px dashed #e0e0e0;
}

.no-trains-icon {
  margin-bottom: 1.5rem;
}

.no-trains-icon svg {
  width: 60px;
  height: 60px;
  color: #9e9e9e;
}

.no-trains-message h3 {
  font-size: 1.5rem;
  color: #424242;
  margin-bottom: 0.5rem;
}

.no-trains-message p {
  color: #757575;
  margin-bottom: 1.5rem;
}

.retry-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 10px 20px;
  background: #3949ab;
  color: white;
  border: none;
  border-radius: 6px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.retry-btn:hover {
  background: #303f9f;
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
  .train-selector-title {
    font-size: 1.5rem;
  }
}
</style>