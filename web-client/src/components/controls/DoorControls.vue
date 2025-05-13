<template>
  <div class="door-controls">
    <h3 class="panel-title">DOOR CONTROLS</h3>
    
    <div class="door-grid">
      <div class="door-control">
        <label class="door-label">LEFT DOORS</label>
        <div class="door-buttons">
          <button class="door-button open" @click="openLeftDoors">OPEN</button>
          <button class="door-button close" @click="closeLeftDoors">CLOSE</button>
        </div>
        <div class="door-status" :class="{ open: leftDoorsOpen }">
          {{ leftDoorsOpen ? 'OPEN' : 'CLOSED' }}
        </div>
      </div>
      
      <div class="door-control">
        <label class="door-label">RIGHT DOORS</label>
        <div class="door-buttons">
          <button class="door-button open" @click="openRightDoors">OPEN</button>
          <button class="door-button close" @click="closeRightDoors">CLOSE</button>
        </div>
        <div class="door-status" :class="{ open: rightDoorsOpen }">
          {{ rightDoorsOpen ? 'OPEN' : 'CLOSED' }}
        </div>
      </div>
    </div>
    
    <div class="door-mode">
      <label class="mode-label">DOOR MODE:</label>
      <select class="mode-select" v-model="doorMode">
        <option value="manual">MANUAL</option>
        <option value="auto">AUTOMATIC</option>
        <option value="platform">PLATFORM</option>
      </select>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';

const leftDoorsOpen = ref(false);
const rightDoorsOpen = ref(false);
const doorMode = ref('manual');

const emit = defineEmits([
  'open-left-doors',
  'close-left-doors',
  'open-right-doors',
  'close-right-doors',
  'door-mode-change'
]);

const openLeftDoors = () => {
  leftDoorsOpen.value = true;
  emit('open-left-doors');
};

const closeLeftDoors = () => {
  leftDoorsOpen.value = false;
  emit('close-left-doors');
};

const openRightDoors = () => {
  rightDoorsOpen.value = true;
  emit('open-right-doors');
};

const closeRightDoors = () => {
  rightDoorsOpen.value = false;
  emit('close-right-doors');
};
</script>

<style scoped>
.door-controls {
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

.door-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 15px;
  margin-bottom: 15px;
}

.door-control {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.door-label {
  color: #777;
  font-size: 0.8rem;
  margin-bottom: 8px;
}

.door-buttons {
  display: flex;
  gap: 5px;
  margin-bottom: 8px;
}

.door-button {
  padding: 5px 10px;
  border: none;
  border-radius: 5px;
  font-size: 0.7rem;
  font-weight: bold;
  cursor: pointer;
  transition: all 0.3s;
}

.door-button.open {
  background: #2ecc71;
  color: white;
}

.door-button.open:hover {
  background: #27ae60;
}

.door-button.close {
  background: #e74c3c;
  color: white;
}

.door-button.close:hover {
  background: #c0392b;
}

.door-status {
  padding: 3px 10px;
  border-radius: 10px;
  font-size: 0.7rem;
  font-weight: bold;
  background: #333;
  color: #e74c3c;
}

.door-status.open {
  background: #2ecc71;
  color: white;
}

.door-mode {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  margin-top: 10px;
}

.mode-label {
  color: #777;
  font-size: 0.8rem;
}

.mode-select {
  background: #333;
  color: white;
  border: none;
  border-radius: 5px;
  padding: 5px;
  font-size: 0.8rem;
}
</style>