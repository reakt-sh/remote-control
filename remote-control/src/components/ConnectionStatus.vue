<template>
  <div class="connection-status" :class="{ connected: isConnected }">
    {{ isConnected ? 'CONNECTED' : 'DISCONNECTED' }}
  </div>
</template>

<script setup>
import { storeToRefs } from 'pinia'
import { useTrainStore } from '@/stores/trainStore'

const { isConnected } = storeToRefs(useTrainStore())
</script>

<style scoped>
.connection-status {
  padding: 0.5rem 1rem;
  border-radius: 20px;
  font-weight: bold;
  font-size: 0.8rem;
  background-color: #e74c3c;
  color: white;
}

.connection-status.connected {
  background-color: var(--success-color);
}
</style>