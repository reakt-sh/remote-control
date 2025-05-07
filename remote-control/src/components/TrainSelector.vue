<template>
  <div class="train-selector">
    <h2>Select Train</h2>
    <select v-model="selectedTrainId" @change="handleTrainChange">
      <option value="">-- Select a train --</option>
      <option v-for="(train, id) in availableTrains" :value="id" :key="id">
        {{ train.name }} ({{ id }})
      </option>
    </select>
  </div>
</template>

<script setup>
import { storeToRefs } from 'pinia'
import { useTrainStore } from '@/stores/trainStore'
import { onMounted } from 'vue'

const { availableTrains, selectedTrainId } = storeToRefs(useTrainStore())
const { fetchAvailableTrains, connectToTrain } = useTrainStore()

const handleTrainChange = () => {
  console.log('Here ', selectedTrainId.value)
  connectToTrain(selectedTrainId.value)
}

onMounted(() => {
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
</style>