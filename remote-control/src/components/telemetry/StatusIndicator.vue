<template>
  <div v-if="currentTrain" class="telemetry-value status" :class="currentTrain.status">
    {{ currentTrain.status }}
  </div>
  <div v-else class="telemetry-value status">
    No status available
  </div>
</template>

<script setup>
import { storeToRefs } from 'pinia'
import { useTrainStore } from '@/stores/trainStore'

const { currentTrain } = storeToRefs(useTrainStore())
</script>

<style scoped>
.status.running {
  color: var(--success-color);
}

.status.stopped {
  color: var(--warning-color);
}

.status.emergency {
  color: var(--danger-color);
}
</style>