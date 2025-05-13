<template>
  <div class="communication-panel">
    <h3 class="panel-title">COMMUNICATION</h3>
    
    <div class="radio-controls">
      <div class="radio-display">
        <div class="radio-frequency">{{ frequency }}</div>
        <div class="radio-channel">CHANNEL: {{ channel }}</div>
      </div>
      
      <div class="radio-buttons">
        <button class="radio-button" @click="adjustFrequency(-0.1)">-</button>
        <button class="radio-button transmit" 
                @mousedown="startTransmit" 
                @mouseup="stopTransmit"
                @touchstart="startTransmit"
                @touchend="stopTransmit">
          TX
        </button>
        <button class="radio-button" @click="adjustFrequency(0.1)">+</button>
      </div>
    </div>
    
    <div class="communication-log">
      <div class="log-header">COMM LOG</div>
      <div class="log-messages">
        <div v-for="(message, index) in messages" :key="index" class="log-message">
          [{{ message.time }}] {{ message.text }}
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';

const frequency = ref(161.475);
const channel = ref(12);
const transmitting = ref(false);
const messages = ref([
  { time: '10:23:45', text: 'Dispatch: Train 245 proceed to station Alpha' },
  { time: '10:24:10', text: 'You: Copy, proceeding to Alpha' },
  { time: '10:28:33', text: 'Dispatch: Be advised of signal at Charlie' }
]);

// const formattedFrequency = computed(() => {
//   return frequency.value.toFixed(3);
// });

const adjustFrequency = (change) => {
  frequency.value = Math.max(150, Math.min(170, frequency.value + change));
  channel.value = Math.floor((frequency.value - 150) / 0.2) + 1;
};

const startTransmit = () => {
  transmitting.value = true;
  emit('radio-transmit', true);
};

const stopTransmit = () => {
  transmitting.value = false;
  emit('radio-transmit', false);
};

const emit = defineEmits(['radio-transmit']);
</script>

<style scoped>
.communication-panel {
  background: #1a1a1a;
  border-radius: 15px;
  padding: 15px;
  box-shadow: inset 0 0 10px rgba(0,0,0,0.5);
}

.panel-title {
  color: #777;
  font-size: 0.9rem;
  margin: 0 0 15px 0;
  text-align: center;
  letter-spacing: 1px;
}

.radio-controls {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
  background: #333;
  padding: 10px;
  border-radius: 10px;
}

.radio-display {
  display: flex;
  flex-direction: column;
}

.radio-frequency {
  font-size: 1.5rem;
  font-family: 'Segment7', monospace;
  color: #f1c40f;
}

.radio-channel {
  font-size: 0.8rem;
  color: #777;
}

.radio-buttons {
  display: flex;
  gap: 5px;
}

.radio-button {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: #444;
  color: white;
  border: none;
  font-size: 1.2rem;
  font-weight: bold;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s;
}

.radio-button:hover {
  background: #555;
}

.radio-button.transmit {
  background: #e74c3c;
  width: 50px;
  height: 50px;
  font-size: 1.5rem;
}

.radio-button.transmit:hover {
  background: #c0392b;
}

.communication-log {
  background: #111;
  border-radius: 5px;
  padding: 10px;
}

.log-header {
  color: #777;
  font-size: 0.8rem;
  margin-bottom: 5px;
  border-bottom: 1px solid #333;
  padding-bottom: 3px;
}

.log-messages {
  max-height: 100px;
  overflow-y: auto;
  font-size: 0.8rem;
}

.log-message {
  margin-bottom: 5px;
  color: #ccc;
}

.log-message:last-child {
  margin-bottom: 0;
}
</style>