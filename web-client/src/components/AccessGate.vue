<template>
  <div class="access-gate-overlay">
    <div class="access-gate-card">
      <div class="lock-icon">
        <i class="fas fa-lock"></i>
      </div>
      <h2>Access Restricted</h2>
      <p>This system is private. Please enter the access code to continue.</p>
      <form @submit.prevent="handleSubmit" class="access-form">
        <input
          v-model="inputCode"
          type="password"
          placeholder="Enter access code"
          class="access-input"
          :class="{ 'shake': showError }"
          autofocus
          ref="codeInput"
        />
        <p v-if="showError" class="error-message">Invalid code. Please try again.</p>
        <button type="submit" class="access-button" :disabled="!inputCode">
          <i class="fas fa-unlock-alt"></i> Unlock
        </button>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAccessStore } from '@/stores/accessStore'

const router = useRouter()
const accessStore = useAccessStore()
const inputCode = ref('')
const showError = ref(false)
const codeInput = ref(null)

function handleSubmit() {
  if (accessStore.checkCode(inputCode.value)) {
    accessStore.grantAccess()
    showError.value = false
    router.push('/')
  } else {
    showError.value = true
    inputCode.value = ''
    setTimeout(() => {
      codeInput.value?.focus()
    }, 100)
  }
}
</script>

<style scoped>
.access-gate-overlay {
  position: fixed;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
  z-index: 9999;
}

.access-gate-card {
  background: rgba(255, 255, 255, 0.95);
  border-radius: 20px;
  padding: 3rem 2.5rem;
  width: 100%;
  max-width: 400px;
  text-align: center;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  animation: fadeInUp 0.5s ease;
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.lock-icon {
  font-size: 3rem;
  color: #667eea;
  margin-bottom: 1rem;
}

.access-gate-card h2 {
  color: #1a1a2e;
  margin-bottom: 0.5rem;
  font-size: 1.5rem;
}

.access-gate-card p {
  color: #666;
  margin-bottom: 1.5rem;
  font-size: 0.9rem;
  line-height: 1.4;
}

.access-form {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.access-input {
  padding: 0.9rem 1rem;
  border: 2px solid #e0e0e0;
  border-radius: 12px;
  font-size: 1rem;
  outline: none;
  transition: border-color 0.3s ease;
  text-align: center;
  letter-spacing: 2px;
}

.access-input:focus {
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.15);
}

.access-input.shake {
  animation: shake 0.4s ease;
  border-color: #e74c3c;
}

@keyframes shake {
  0%, 100% { transform: translateX(0); }
  25% { transform: translateX(-8px); }
  50% { transform: translateX(8px); }
  75% { transform: translateX(-4px); }
}

.error-message {
  color: #e74c3c !important;
  font-size: 0.85rem !important;
  margin: -0.5rem 0 0 0 !important;
}

.access-button {
  padding: 0.9rem;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 12px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
}

.access-button:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
}

.access-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>