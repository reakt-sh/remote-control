<template>
  <button
    class="control-button"
    :class="[type, { active }]"
    @click="handleClick"
    :disabled="disabled"
  >
    <i class="fas" :class="icon"></i> {{ label }}
  </button>
</template>

<script setup>
import { useTrainStore } from '@/stores/trainStore'

const props = defineProps({
  action: {
    type: String,
    required: true
  },
  value: {
    type: [String, Number, Boolean],
    required: true
  },
  label: {
    type: String,
    required: true
  },
  icon: {
    type: String,
    required: true
  },
  type: {
    type: String,
    required: true
  },
  active: {
    type: Boolean,
    default: false
  },
  disabled: {
    type: Boolean,
    default: false
  }
})

const { sendCommand } = useTrainStore()

const handleClick = () => {
  sendCommand(props.action, props.value)
}
</script>

<style scoped>
.control-button {
  padding: 1rem;
  border: none;
  border-radius: 5px;
  font-weight: bold;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
}

.control-button i {
  margin-right: 0.5rem;
}

.control-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 2px 5px rgba(0,0,0,0.1);
}

.control-button:active {
  transform: translateY(0);
}

.control-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.control-button.accelerate {
  background-color: var(--success-color);
  color: white;
}

.control-button.decelerate {
  background-color: var(--warning-color);
  color: white;
}

.control-button.brake {
  background-color: #e67e22;
  color: white;
}

.control-button.brake.active {
  background-color: var(--danger-color);
}

.control-button.start {
  background-color: var(--info-color);
  color: white;
}

.control-button.shutdown {
  background-color: var(--dark-color);
  color: white;
}
</style>