<template>
  <header class="app-header">
    <div class="header-brand" @click="goToHome">
      <img
        src="/assets/Logo_reakt_wei.png"
        alt="REAKT Logo"
        class="header-logo"
      />
      <div class="header-title-group">
        <span class="header-title">Remote Control</span>
      </div>
    </div>
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
  padding: 0.4rem 2rem;
  background: #1C3647;
  color: white;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.15);
  user-select: none;
}

.header-brand {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  cursor: pointer;
  transition: opacity 0.2s ease;
}

.header-brand:hover {
  opacity: 0.85;
}

.header-logo {
  height: 32px;
  width: auto;
  display: block;
}

.header-title-group {
  display: flex;
  flex-direction: column;
  line-height: 1.2;
}

.header-title {
  font-size: 1rem;
  font-weight: 600;
  letter-spacing: 0.02em;
}

.header-subtitle {
  font-size: 0.65rem;
  font-weight: 400;
  opacity: 0.7;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.header-controls {
  display: flex;
  align-items: center;
  gap: 1rem;
}

@media (max-width: 768px) {
  .app-header {
    padding: 0.3rem 1rem;
  }

  .header-logo {
    height: 26px;
  }

  .header-title {
    font-size: 0.85rem;
  }

  .header-subtitle {
    font-size: 0.55rem;
  }

  .header-controls {
    gap: 0.5rem;
  }
}
</style>