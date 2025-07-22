<template>
  <div class="bitrate-control">
    <div class="control-header">
      <i class="fas fa-video"></i>
      <span class="control-label">Video Quality</span>
    </div>
    <div class="dropdown-container" ref="dropdownContainer">
      <button 
        class="dropdown-toggle"
        :class="{ active: isOpen }"
        @click="toggleDropdown"
        :disabled="disabled"
      >
        <span class="selected-value">{{ selectedOption.label }}</span>
        <i class="fas fa-chevron-down" :class="{ rotated: isOpen }"></i>
      </button>
      <div class="dropdown-menu" :class="{ show: isOpen }" :style="dropdownStyle">
        <div 
          v-for="option in options" 
          :key="option.value"
          class="dropdown-item"
          :class="{ selected: modelValue === option.value }"
          @click="selectOption(option)"
        >
          <div class="option-content">
            <span class="option-label">{{ option.label }}</span>
            <span class="option-description">{{ option.description }}</span>
          </div>
          <i v-if="modelValue === option.value" class="fas fa-check"></i>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'

const props = defineProps({
  modelValue: {
    type: String,
    default: 'medium'
  },
  disabled: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:modelValue', 'change'])

const isOpen = ref(false)
const dropdownContainer = ref(null)
const dropdownStyle = ref({})

const options = [
  {
    value: 'low',
    label: 'Low',
    description: '480p - Data Saver'
  },
  {
    value: 'medium',
    label: 'Medium',
    description: '720p - Balanced'
  },
  {
    value: 'high',
    label: 'High',
    description: '1080p - Best Quality'
  }
]

const selectedOption = computed(() => {
  return options.find(option => option.value === props.modelValue) || options[1]
})

async function toggleDropdown() {
  if (!props.disabled) {
    isOpen.value = !isOpen.value
    if (isOpen.value) {
      await nextTick()
      adjustDropdownPosition()
    }
  }
}

function adjustDropdownPosition() {
  if (!dropdownContainer.value) return
  
  const rect = dropdownContainer.value.getBoundingClientRect()
  const dropdownHeight = 180 // Approximate height of dropdown
  const viewportHeight = window.innerHeight
  const spaceBelow = viewportHeight - rect.bottom
  const spaceAbove = rect.top
  
  // Calculate center position to align with the component
  const centerLeft = rect.left + (rect.width / 2) - 90 // 90 is half of min-width (180px)
  
  if (spaceBelow < dropdownHeight && spaceAbove > dropdownHeight) {
    // Show dropdown above the button
    dropdownStyle.value = {
      left: `${centerLeft}px`,
      bottom: `${viewportHeight - rect.top}px`,
      width: '180px',
      top: 'auto'
    }
  } else {
    // Show dropdown below the button (default)
    dropdownStyle.value = {
      left: `${centerLeft}px`,
      top: `${rect.bottom + 4}px`,
      width: '180px',
      bottom: 'auto'
    }
  }
}

function selectOption(option) {
  if (!props.disabled && option.value !== props.modelValue) {
    emit('update:modelValue', option.value)
    emit('change', option.value)
  }
  isOpen.value = false
}

function closeDropdown(event) {
  if (!event.target.closest('.dropdown-container')) {
    isOpen.value = false
  }
}

onMounted(() => {
  document.addEventListener('click', closeDropdown)
})

onUnmounted(() => {
  document.removeEventListener('click', closeDropdown)
})
</script>

<style scoped>
.bitrate-control {
  background: #fff;
  border-radius: 12px;
  padding: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  border: 1px solid #e1e5e9;
  transition: box-shadow 0.2s ease;
  width: 100%;
  max-width: 200px;
  margin: 0 auto;
  box-sizing: border-box;
}

.bitrate-control:hover {
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
}

.control-header {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 10px;
}

.control-header i {
  color: #0096ff;
  font-size: 0.9rem;
}

.control-label {
  font-size: 0.8rem;
  font-weight: 600;
  color: #334155;
}

.dropdown-container {
  position: relative;
}

.dropdown-toggle {
  width: 100%;
  padding: 10px 12px;
  border: 2px solid #e2e8f0;
  border-radius: 8px;
  background: #fff;
  color: #334155;
  font-size: 0.85rem;
  font-weight: 500;
  cursor: pointer;
  display: flex;
  justify-content: space-between;
  align-items: center;
  transition: all 0.2s ease;
}

.dropdown-toggle:hover:not(:disabled) {
  border-color: #0096ff;
  box-shadow: 0 0 0 3px rgba(0, 150, 255, 0.1);
}

.dropdown-toggle.active {
  border-color: #0096ff;
  box-shadow: 0 0 0 3px rgba(0, 150, 255, 0.1);
}

.dropdown-toggle:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  background: #f8fafc;
}

.selected-value {
  font-weight: 600;
}

.dropdown-toggle i {
  transition: transform 0.2s ease;
  color: #64748b;
}

.dropdown-toggle i.rotated {
  transform: rotate(180deg);
}

.dropdown-menu {
  position: fixed;
  background: #fff;
  border: 2px solid #e2e8f0;
  border-radius: 8px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.15);
  z-index: 9999;
  opacity: 0;
  visibility: hidden;
  transform: translateY(-8px);
  transition: all 0.2s ease;
  min-width: 180px;
  max-height: 300px;
  overflow-y: auto;
}

.dropdown-menu.show {
  opacity: 1;
  visibility: visible;
  transform: translateY(0);
}

.dropdown-item {
  padding: 12px 16px;
  cursor: pointer;
  display: flex;
  justify-content: space-between;
  align-items: center;
  transition: background-color 0.15s ease;
  border-bottom: 1px solid #f1f5f9;
}

.dropdown-item:last-child {
  border-bottom: none;
}

.dropdown-item:hover {
  background: #f8fafc;
}

.dropdown-item.selected {
  background: #eff6ff;
  color: #0096ff;
}

.option-content {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.option-label {
  font-weight: 600;
  font-size: 0.9rem;
}

.option-description {
  font-size: 0.75rem;
  color: #64748b;
}

.dropdown-item.selected .option-description {
  color: #0096ff;
}

.dropdown-item i {
  color: #0096ff;
  font-size: 0.8rem;
}

@media (max-width: 768px) {
  .bitrate-control {
    padding: 12px;
  }
  
  .dropdown-toggle {
    padding: 10px 12px;
    font-size: 0.85rem;
  }
  
  .dropdown-item {
    padding: 10px 12px;
  }
}
</style>
