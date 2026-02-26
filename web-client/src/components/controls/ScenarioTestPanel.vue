<template>
  <div class="scenario-panel">
    <div class="top-controls">
      <div class="scenario-selector">
        <label for="scenario-select">Select Scenario:</label>
        <select 
          id="scenario-select"
          v-model="selectedScenario" 
          :disabled="isRunning"
          class="scenario-dropdown"
        >
          <option value="">-- Choose Scenario --</option>
          <option v-for="(value, key) in scenarios" :key="key" :value="key">
            {{ formatScenarioName(key) }}
          </option>
        </select>
      </div>

      <div class="control-section">
        <div :class="['status-indicator', isRunning ? 'running' : 'idle']">
          {{ isRunning ? 'RUNNING' : 'IDLE' }}
        </div>
        <div class="control-buttons">
          <button 
            @click="startScenario"
            :disabled="!selectedScenario || isRunning || !trainId"
            class="btn btn-start"
          >
            <span class="btn-icon">▶</span>
            Start
          </button>
          <button 
            @click="stopScenario"
            :disabled="!isRunning"
            class="btn btn-stop"
          >
            <span class="btn-icon">■</span>
            Stop
          </button>
        </div>
      </div>
    </div>

    <div v-if="isRunning || currentStep > 0" class="progress-section">
      <div class="progress-bar-container">
        <div class="progress-bar" :style="{ width: progress + '%' }"></div>
      </div>
      <div class="progress-info">
        <span>Step {{ currentStep }} / {{ totalSteps }}</span>
        <span>{{ progress.toFixed(0) }}%</span>
      </div>
      
      <!-- Command History and Timer Container -->
      <div class="history-timer-container">
        <!-- Command History -->
        <div class="command-history">
          <div class="history-label">Commands from Test Scenario</div>
          <div class="history-scroll-container" ref="historyScrollContainer">
            <div 
              v-for="(cmd, index) in commandHistory" 
              :key="index"
              :class="['history-item', { 'current': index === commandHistory.length - 1 && isRunning }]"
            >
              <span class="history-bullet">{{ index === commandHistory.length - 1 && isRunning ? '▶' : '✓' }}</span>
              <span class="history-text">{{ formatCommand(cmd) }}</span>
            </div>
            <div v-if="commandHistory.length === 0" class="history-empty">
              No commands executed yet
            </div>
          </div>
        </div>
        
        <!-- Stopwatch Timer for Wait Commands -->
        <div v-if="currentCommand && currentCommand[0] === 'wait' && remainingWaitTime > 0" class="timer-display">
          <div class="timer-label">Waiting</div>
          <div class="timer-circle">
            <svg class="timer-svg" viewBox="0 0 100 100">
              <circle class="timer-bg" cx="50" cy="50" r="45"></circle>
              <circle 
                class="timer-progress" 
                cx="50" 
                cy="50" 
                r="45"
                :style="{
                  strokeDashoffset: 283 - (283 * remainingWaitTime / currentCommand[1])
                }"
              ></circle>
            </svg>
            <div class="timer-value">{{ remainingWaitTime }}s</div>
          </div>
        </div>
      </div>
    </div>

    <div v-if="!trainId" class="warning-message">
      ⚠️ Please connect to a train first
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick } from 'vue'
import { storeToRefs } from 'pinia'
import { useTrainStore } from '@/stores/trainStore'
import scenarios from '@/scripts/scenario.js'

const emit = defineEmits(['scenarioStateChange'])

const trainStore = useTrainStore()
const { telemetryData } = storeToRefs(trainStore)

// State
const selectedScenario = ref('')
const isRunning = ref(false)
const currentStep = ref(0)
const totalSteps = ref(0)
const currentCommand = ref(null)
const commandHistory = ref([])
const remainingWaitTime = ref(0)
const historyScrollContainer = ref(null)
let executionTimeout = null
let countdownInterval = null

// Computed
const trainId = computed(() => telemetryData.value?.train_id)
const progress = computed(() => {
  if (totalSteps.value === 0) return 0
  return (currentStep.value / totalSteps.value) * 100
})

// Methods
function formatScenarioName(key) {
  return key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())
}

function formatCommand(command) {
  if (!command) return ''
  const [type, value] = command
  
  switch (type) {
    case 'status':
      return `Power ${value === 'POWER_ON' ? 'ON' : 'OFF'}`
    case 'direction':
      return `Direction: ${value}`
    case 'set_speed':
      return `Set Speed: ${value}`
    case 'wait':
      return `Waiting ${remainingWaitTime.value > 0 ? remainingWaitTime.value : value} seconds...`
    default:
      return command.join(': ')
  }
}

async function executeCommand(command) {
  const [type, value] = command
  
  switch (type) {
    case 'status':
      if (value === 'POWER_ON') {
        trainStore.sendCommand({
          instruction: 'POWER_ON',
          train_id: trainId.value
        })
      } else if (value === 'POWER_OFF') {
        trainStore.sendCommand({
          instruction: 'POWER_OFF',
          train_id: trainId.value
        })
      }
      break
      
    case 'direction':
      trainStore.sendCommand({
        instruction: 'CHANGE_DIRECTION',
        train_id: trainId.value,
        direction: value
      })
      break
      
    case 'set_speed':
      trainStore.sendCommand({
        instruction: 'CHANGE_TARGET_SPEED',
        train_id: trainId.value,
        target_speed: value
      })
      break
      
    case 'wait':
      // Wait is handled in the execution loop
      break
  }
}

async function executeScenario(commands) {
  totalSteps.value = commands.length
  currentStep.value = 0
  commandHistory.value = []
  
  for (let i = 0; i < commands.length; i++) {
    if (!isRunning.value) {
      break
    }
    
    const command = commands[i]
    currentCommand.value = command
    currentStep.value = i + 1
    
    const [type, value] = command
    
    // Add to history (exclude wait commands)
    if (type !== 'wait') {
      commandHistory.value.push(command)
    }
    
    // Execute the command
    await executeCommand(command)
    
    // If it's a wait command, delay before next command
    if (type === 'wait') {
      remainingWaitTime.value = value
      
      // Set up countdown interval
      countdownInterval = setInterval(() => {
        remainingWaitTime.value -= 1
        if (remainingWaitTime.value <= 0) {
          clearInterval(countdownInterval)
          countdownInterval = null
        }
      }, 1000)
      
      await new Promise(resolve => {
        executionTimeout = setTimeout(() => {
          if (countdownInterval) {
            clearInterval(countdownInterval)
            countdownInterval = null
          }
          remainingWaitTime.value = 0
          resolve()
        }, value * 1000)
      })
    } else {
      // Small delay between commands for stability
      await new Promise(resolve => {
        executionTimeout = setTimeout(resolve, 100)
      })
    }
  }
  
  // Scenario finished
  if (isRunning.value) {
    stopScenario()
  }
}

function startScenario() {
  if (!selectedScenario.value || !trainId.value) return
  
  const commands = scenarios[selectedScenario.value]
  if (!commands || commands.length === 0) return
  
  isRunning.value = true
  emit('scenarioStateChange', true)
  executeScenario(commands)
}

function stopScenario() {
  isRunning.value = false
  currentCommand.value = null
  remainingWaitTime.value = 0
  
  if (executionTimeout) {
    clearTimeout(executionTimeout)
    executionTimeout = null
  }
  
  if (countdownInterval) {
    clearInterval(countdownInterval)
    countdownInterval = null
  }
  
  emit('scenarioStateChange', false)
}

// Watchers
watch(trainId, (newId, oldId) => {
  // If train disconnects during scenario, stop it
  if (!newId && oldId && isRunning.value) {
    stopScenario()
  }
})

watch(commandHistory, async () => {
  // Auto-scroll to bottom when new command is added
  await nextTick()
  if (historyScrollContainer.value) {
    historyScrollContainer.value.scrollTop = historyScrollContainer.value.scrollHeight
  }
}, { deep: true })

// Cleanup on unmount
import { onUnmounted } from 'vue'
onUnmounted(() => {
  if (executionTimeout) {
    clearTimeout(executionTimeout)
  }
  if (countdownInterval) {
    clearInterval(countdownInterval)
  }
})
</script>

<style scoped>
.scenario-panel {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 12px;
  background: linear-gradient(135deg, #ffffff, #f8f9fa);
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  border: 2px solid #e0e0e0;
}

.top-controls {
  display: flex;
  gap: 12px;
  align-items: flex-start;
  justify-content: space-between;
}

.status-indicator {
  padding: 6px 14px;
  border-radius: 16px;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.5px;
  white-space: nowrap;
}

.status-indicator.idle {
  background-color: #95a5a6;
  color: white;
}

.status-indicator.running {
  background-color: #27ae60;
  color: white;
  animation: pulse 1.5s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.7; }
}

.scenario-selector {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 300px;
  max-width: 300px;
}

.scenario-selector label {
  font-size: 12px;
  font-weight: 600;
  color: #34495e;
}

.scenario-dropdown {
  padding: 8px 12px;
  border: 2px solid #bdc3c7;
  border-radius: 6px;
  font-size: 14px;
  background-color: white;
  cursor: pointer;
  transition: all 0.2s;
}

.scenario-dropdown:hover:not(:disabled) {
  border-color: #3498db;
}

.scenario-dropdown:disabled {
  background-color: #ecf0f1;
  cursor: not-allowed;
  opacity: 0.6;
}

.control-section {
  display: flex;
  flex-direction: row;
  gap: 8px;
  align-items: center;
}

.control-buttons {
  display: flex;
  gap: 6px;
}

.btn {
  flex: 1;
  padding: 8px 12px;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
}

.btn-icon {
  font-size: 12px;
}

.btn-start {
  background: linear-gradient(135deg, #27ae60, #229954);
  color: white;
}

.btn-start:hover:not(:disabled) {
  background: linear-gradient(135deg, #229954, #1e8449);
  transform: translateY(-1px);
  box-shadow: 0 4px 8px rgba(39, 174, 96, 0.3);
}

.btn-stop {
  background: linear-gradient(135deg, #e74c3c, #c0392b);
  color: white;
}

.btn-stop:hover:not(:disabled) {
  background: linear-gradient(135deg, #c0392b, #a93226);
  transform: translateY(-1px);
  box-shadow: 0 4px 8px rgba(231, 76, 60, 0.3);
}

.btn:disabled {
  background: #95a5a6;
  cursor: not-allowed;
  opacity: 0.5;
  transform: none;
}

.progress-section {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 8px;
  background-color: #f8f9fa;
  border-radius: 6px;
  border: 1px solid #dee2e6;
}

.progress-bar-container {
  width: 100%;
  height: 8px;
  background-color: #e0e0e0;
  border-radius: 4px;
  overflow: hidden;
}

.progress-bar {
  height: 100%;
  background: linear-gradient(90deg, #3498db, #2980b9);
  transition: width 0.3s ease;
  border-radius: 4px;
}

.progress-info {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: #7f8c8d;
  font-weight: 600;
}

.current-command {
  font-size: 13px;
  color: #2c3e50;
  padding: 8px;
  background-color: white;
  border-radius: 4px;
  border-left: 3px solid #3498db;
}

.current-command strong {
  color: #3498db;
}

.history-timer-container {
  display: flex;
  gap: 8px;
  align-items: center;
}

.timer-display {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  padding: 8px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 6px;
  box-shadow: 0 2px 6px rgba(102, 126, 234, 0.3);
  min-width: 80px;
}

.timer-label {
  font-size: 11px;
  font-weight: 600;
  color: white;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.timer-circle {
  position: relative;
  width: 50px;
  height: 50px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.timer-svg {
  position: absolute;
  width: 100%;
  height: 100%;
  transform: rotate(-90deg);
}

.timer-bg {
  fill: none;
  stroke: rgba(255, 255, 255, 0.2);
  stroke-width: 6;
}

.timer-progress {
  fill: none;
  stroke: #ffffff;
  stroke-width: 6;
  stroke-linecap: round;
  stroke-dasharray: 283;
  stroke-dashoffset: 0;
  transition: stroke-dashoffset 1s linear;
  filter: drop-shadow(0 0 4px rgba(255, 255, 255, 0.5));
}

.timer-value {
  position: relative;
  font-size: 16px;
  font-weight: 700;
  color: white;
  text-shadow: 0 1px 4px rgba(0, 0, 0, 0.3);
  font-variant-numeric: tabular-nums;
}

.command-history {
  display: flex;
  flex-direction: column;
  gap: 4px;
  flex: 1;
}

.history-label {
  font-size: 11px;
  font-weight: 700;
  color: #7f8c8d;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 2px;
}

.history-scroll-container {
  display: flex;
  flex-direction: column;
  gap: 3px;
  max-height: 90px;
  overflow-y: auto;
  padding-right: 4px;
}

.history-scroll-container::-webkit-scrollbar {
  width: 4px;
}

.history-scroll-container::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 2px;
}

.history-scroll-container::-webkit-scrollbar-thumb {
  background: #bdc3c7;
  border-radius: 2px;
}

.history-scroll-container::-webkit-scrollbar-thumb:hover {
  background: #95a5a6;
}

.history-item {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 6px;
  background-color: white;
  border-radius: 4px;
  border-left: 2px solid #95a5a6;
  font-size: 12px;
  color: #2c3e50;
  transition: all 0.3s ease;
}

.history-item.current {
  border-left-color: #3498db;
  background: linear-gradient(90deg, #ebf5fb 0%, white 100%);
  box-shadow: 0 2px 6px rgba(52, 152, 219, 0.2);
  animation: slideIn 0.3s ease;
}

@keyframes slideIn {
  from {
    transform: translateX(-10px);
    opacity: 0;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
}

.history-bullet {
  font-size: 10px;
  color: #95a5a6;
  min-width: 16px;
  text-align: center;
}

.history-item.current .history-bullet {
  color: #3498db;
  animation: pulse-bullet 1.5s ease-in-out infinite;
}

@keyframes pulse-bullet {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.6; transform: scale(1.2); }
}

.history-text {
  flex: 1;
  font-weight: 500;
}

.history-item.current .history-text {
  font-weight: 600;
  color: #2980b9;
}

.history-empty {
  padding: 12px;
  text-align: center;
  color: #95a5a6;
  font-size: 12px;
  font-style: italic;
  background-color: rgba(149, 165, 166, 0.1);
  border-radius: 6px;
}

.warning-message {
  padding: 10px;
  background-color: #fff3cd;
  border: 1px solid #ffc107;
  border-radius: 6px;
  color: #856404;
  font-size: 13px;
  text-align: center;
  font-weight: 500;
}

@media (max-width: 700px) {
  .scenario-panel {
    padding: 10px;
  }
  
  .top-controls {
    flex-direction: column;
    gap: 8px;
  }
  
  .control-section {
    flex-direction: column;
    align-items: stretch;
    gap: 6px;
  }
  
  .btn {
    padding: 6px 10px;
    font-size: 13px;
  }
}
</style>
