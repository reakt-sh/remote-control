<template>
  <div class="horn-control">
    <button 
      class="horn-button"
      @mousedown="activateHorn"
      @mouseup="deactivateHorn"
      @touchstart="activateHorn"
      @touchend="deactivateHorn"
    >
      <span class="horn-icon">📢</span>
      <span class="horn-label">HORN</span>
    </button>
    
    <div class="horn-type">
      <label>TYPE:</label>
      <select v-model="hornType">
        <option value="short">SHORT</option>
        <option value="long">LONG</option>
        <option value="sequence">SEQUENCE</option>
      </select>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';

const hornActive = ref(false);
const hornType = ref('short');

const emit = defineEmits(['activate-horn', 'deactivate-horn']);

const activateHorn = () => {
  hornActive.value = true;
  emit('activate-horn', hornType.value);
};

const deactivateHorn = () => {
  hornActive.value = false;
  emit('deactivate-horn');
};
</script>

<style scoped>
.horn-control {
  background: #1a1a1a;
  border-radius: 15px;
  padding: 15px;
  display: flex;
  flex-direction: column;
  align-items: center;
  box-shadow: inset 0 0 10px rgba(0,0,0,0.5);
}

.horn-button {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  background: #f1c40f;
  border: none;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s;
  margin-bottom: 10px;
}

.horn-button:active {
  transform: scale(0.95);
  background: #f39c12;
  box-shadow: 0 0 15px rgba(241, 196, 15, 0.7);
}

.horn-icon {
  font-size: 2rem;
}

.horn-label {
  font-size: 0.8rem;
  font-weight: bold;
  text-transform: uppercase;
}

.horn-type {
  display: flex;
  align-items: center;
  gap: 5px;
  color: #777;
  font-size: 0.8rem;
}

.horn-type select {
  background: #333;
  color: white;
  border: none;
  border-radius: 5px;
  padding: 3px;
  font-size: 0.8rem;
}
</style>