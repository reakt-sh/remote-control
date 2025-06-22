<template>
  <div class="train-selector">
    <template v-if="availableTrains.length > 0">
      <h2>Select Train</h2>
      <div class="train-grid">
        <div
          v-for="id in availableTrains"
          :key="id"
          class="train-card"
          @click="selectTrain(id)"
        >
          <div class="train-icon">🚆</div>
          <div class="train-id">Train</div>
          <div class="train-id-value">{{ id }}</div>
        </div>
      </div>
    </template>
    <transition name="fade">
      <div v-if="availableTrains.length === 0" class="no-train-msg">
        <span>🚂 No train is connected to the central server.</span>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { storeToRefs } from 'pinia'
import { useTrainStore } from '@/stores/trainStore'
import { useRouter } from 'vue-router'
import { onMounted } from 'vue'

const { availableTrains } = storeToRefs(useTrainStore())
const { fetchAvailableTrains, connectToServer, initializeRemoteControlId } = useTrainStore()
const router = useRouter()

const selectTrain = (id) => {
  router.push(`/${id}`)
}

onMounted(() => {
  initializeRemoteControlId()
  connectToServer()
  fetchAvailableTrains()
})
</script>

<style scoped>
.train-selector {
  background: linear-gradient(135deg, #f5f5f5, #e0e0e0);
  padding: 1rem;
  border-radius: 5px;
  margin-bottom: 1rem;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

.train-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 1.5rem;
  margin-top: 1rem;
  justify-items: center;
}

.train-card {
  width: 240px;
  height: 180px;
  background: #fff;
  border-radius: 10px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.08);
  padding: 2rem 1.5rem;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: box-shadow 0.2s, transform 0.2s;
  border: 2px solid transparent;
}
.train-card:hover {
  box-shadow: 0 4px 16px rgba(0,0,0,0.16);
  border-color: #1976d2;
  transform: translateY(-4px) scale(1.03);
}
.train-icon {
  font-size: 2.5rem;
  margin-bottom: 1rem;
}
.train-id {
  font-weight: 600;
  font-size: 1.1rem;
  color: #1976d2;
}
.train-id-value {
  font-family: monospace;
  font-size: 0.95rem;
  color: #333;
  margin-top: 0.5rem;
  word-break: break-all;
}

.no-train-msg {
  margin-top: 1rem;
  padding: 1rem;
  background: #ffeaea;
  color: #b71c1c;
  border: 1px solid #ffbdbd;
  border-radius: 4px;
  text-align: center;
  font-weight: bold;
  font-size: 1.1rem;
  animation: pulse 1.2s infinite alternate;
}

@keyframes pulse {
  from { box-shadow: 0 0 0 0 #ffbdbd; }
  to { box-shadow: 0 0 10px 4px #ffbdbd; }
}

.fade-enter-active, .fade-leave-active {
  transition: opacity 0.5s;
}
.fade-enter-from, .fade-leave-to {
  opacity: 0;
}
</style>