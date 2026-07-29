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
  padding: 0.25rem 2rem;
  background: #1C3647; /* Indigo selected from the style guide REAKT */
  color: white;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
}

.app-header h1 {
  margin: 0;
  font-size: 1.1rem;
  font-weight: 600;
}

.clickable-title {
  cursor: pointer;
  transition: all 0.3s ease;
  padding: 0.15rem 0.4rem;
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
    padding: 0.2rem 1rem;
  }
  
  .app-header h1 {
    font-size: 0.85rem;
  }
  
  .header-controls {
    gap: 0.5rem;
  }
}
</style>
