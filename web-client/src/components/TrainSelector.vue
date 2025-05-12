<template>
  <div class="train-selector">
    <template v-if="Object.keys(availableTrains).length > 0">
      <h2>Select Train</h2>
      <select v-model="selectedTrainId" @change="handleTrainChange">
        <option disabled value="" hidden>Please choose one train to control</option>
        <option v-for="(train, id) in availableTrains" :value="id" :key="id">
          {{ train.name }} ({{ id }})
        </option>
      </select>
    </template>
    <transition name="fade">
      <div v-if="Object.keys(availableTrains).length === 0" class="no-train-msg">
        <span>🚂 No train is connected to the central server.</span>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { storeToRefs } from 'pinia'
import { useTrainStore } from '@/stores/trainStore'
import { onMounted } from 'vue'

const { availableTrains, selectedTrainId } = storeToRefs(useTrainStore())
const { fetchAvailableTrains, connectToServer, mappingToTrain, initializeRemoteControlId} = useTrainStore()

const handleTrainChange = () => {
  console.log('Here ', selectedTrainId.value)
  mappingToTrain(selectedTrainId.value)
}

onMounted(() => {
  initializeRemoteControlId()
  connectToServer()
  fetchAvailableTrains()
})
</script>

<style scoped>
.train-selector {
  background: white;
  padding: 1rem;
  border-radius: 5px;
  margin-bottom: 1rem;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

.train-selector select {
  width: 100%;
  padding: 0.5rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 1rem;
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