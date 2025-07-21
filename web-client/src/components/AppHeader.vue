<template>
  <header class="app-header">
    <h1>Remote Control System</h1>
    <ConnectionStatus />
  </header>
</template>

<script setup>
import ConnectionStatus from '@/components/ConnectionStatus.vue'
</script>

<style scoped>
.app-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 2rem;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
}

.app-header h1 {
  margin: 0;
  font-size: 1.8rem;
  font-weight: 600;
}

@media (max-width: 768px) {
  .app-header {
    padding: 1rem;
  }
  
  .app-header h1 {
    font-size: 1.4rem;
  }
}
</style>
