<template>
  <header class="app-header">
    <h1 @click="goToHome" class="clickable-title">Remote Control System</h1>
    <div class="header-controls">
      <ConnectionStatus />
    </div>
  </header>
</template>

<script setup>
import ConnectionStatus from '@/components/ConnectionStatus.vue'
import { useRouter } from 'vue-router'

const router = useRouter()

function goToHome() {
  router.push('/')
}
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

.clickable-title {
  cursor: pointer;
  transition: all 0.3s ease;
  padding: 0.25rem 0.5rem;
  border-radius: 8px;
}

.clickable-title:hover {
  background: rgba(255, 255, 255, 0.1);
  transform: translateY(-1px);
}

.header-controls {
  display: flex;
  align-items: center;
  gap: 1rem;
}

@media (max-width: 768px) {
  .app-header {
    padding: 1rem;
  }
  
  .app-header h1 {
    font-size: 1.4rem;
  }
  
  .header-controls {
    gap: 0.5rem;
  }
}
</style>
