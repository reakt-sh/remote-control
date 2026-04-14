<template>
  <div class="live-train-selector-container">
    <div class="live-train-selector-header">
      <h2 class="live-train-selector-title">Available Live Trains</h2>
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
            <i class="fas fa-train"></i>
          </div>
          <div class="train-info">
            <div class="train-id">Train ID</div>
            <div class="train-id-value">{{ id }}</div>
          </div>
          <div class="select-train-btn">
            <span>Select</span>
            <i class="fas fa-chevron-right"></i>
          </div>
        </div>
      </div>
      <div v-else class="no-trains-message">
        <div class="no-trains-icon">
          <i class="fas fa-info-circle"></i>
        </div>
        <h3>No Trains Connected</h3>
        <p>Please check your connection to the central server</p>
        <button class="retry-btn" @click="fetchAvailableTrains">
          <i class="fas fa-sync-alt"></i>
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
const { fetchAvailableTrains } = useTrainStore()
const router = useRouter()

const selectTrain = (id) => {
  router.push(`/${id}`)
}
</script>

<style scoped>
.live-train-selector-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem;
  background: #ffffff;
  border-radius: 16px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.08);
}

.live-train-selector-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
}

.live-train-selector-title {
  font-size: 1.75rem;
  font-weight: 700;
  color: #1a237e;
  margin: 0;
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

.train-icon i {
  font-size: 40px;
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

.select-train-btn i {
  font-size: 20px;
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

.no-trains-icon i {
  font-size: 60px;
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

@media (max-width: 768px) {
  .live-train-selector-container {
    padding: 0.625rem;
    border-radius: 10px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.06);
  }

  .live-train-selector-header {
    margin-bottom: 0.75rem;
  }

  .live-train-selector-title {
    font-size: 1.125rem;
  }

  .train-grid {
    grid-template-columns: 1fr;
    gap: 0.625rem;
  }

  .train-card {
    height: 130px;
    border-radius: 10px;
  }

  .train-card-gradient {
    height: 2px;
  }

  .train-icon {
    padding: 0.75rem 0.75rem 0;
  }

  .train-icon i {
    font-size: 24px;
  }

  .train-info {
    padding: 0 0.75rem;
  }

  .train-id {
    font-size: 0.7rem;
    margin-bottom: 3px;
  }

  .train-id-value {
    font-size: 0.85rem;
  }

  .select-train-btn {
    padding: 8px 0.75rem;
    font-size: 0.8125rem;
  }

  .select-train-btn i {
    font-size: 14px;
  }

  .no-trains-message {
    padding: 1.5rem 0.75rem;
    border-radius: 10px;
  }

  .no-trains-icon {
    margin-bottom: 1rem;
  }

  .no-trains-icon i {
    font-size: 40px;
  }

  .no-trains-message h3 {
    font-size: 1.125rem;
    margin-bottom: 0.375rem;
  }

  .no-trains-message p {
    font-size: 0.8125rem;
    margin-bottom: 0.875rem;
  }

  .retry-btn {
    padding: 0.625rem 1.25rem;
    font-size: 0.8125rem;
    border-radius: 6px;
    gap: 6px;
  }

  .retry-btn i {
    font-size: 14px;
  }
}
</style>
