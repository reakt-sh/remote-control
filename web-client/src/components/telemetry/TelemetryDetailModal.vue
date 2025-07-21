<template>
  <div class="modal-overlay" @click.self="closeModal">
    <div class="modal-content">
      <div class="modal-header">
        <h3>Telemetry Details</h3>
        <button @click="closeModal" class="close-button">
          <i class="fas fa-times"></i>
        </button>
      </div>
      <div class="modal-body">
        <div class="detail-row">
          <span class="detail-label">Timestamp:</span>
          <span class="detail-value">{{ formatTime(item.timestamp) }}</span>
        </div>
        <div class="detail-row">
          <span class="detail-label">Location:</span>
          <span class="detail-value">{{ item.location }}</span>
        </div>
        <div class="detail-row">
          <span class="detail-label">Next Station:</span>
          <span class="detail-value">{{ item.next_station }}</span>
        </div>
        <div class="detail-row">
          <span class="detail-label">Speed:</span>
          <span class="detail-value">{{ item.speed }} km/h</span>
        </div>
        <div class="detail-row">
          <span class="detail-label">Passengers:</span>
          <span class="detail-value">{{ item.passenger_count }}</span>
        </div>
        <div class="detail-row">
          <span class="detail-label">Temperature:</span>
          <span class="detail-value">{{ item.temperature }}°C</span>
        </div>
        <div class="detail-row">
          <span class="detail-label">Battery Level:</span>
          <span class="detail-value">{{ item.battery_level }}%</span>
        </div>
        <div class="detail-row">
          <span class="detail-label">Engine Temperature:</span>
          <span class="detail-value">{{ item.engine_temperature }}°C</span>
        </div>
        <div class="detail-row">
          <span class="detail-label">Fuel Level:</span>
          <span class="detail-value">{{ item.fuel_level }}%</span>
        </div>
        <div class="detail-row">
          <span class="detail-label">GPS:</span>
          <span class="detail-value">
            {{ item.gps.latitude }}, {{ item.gps.longitude }}
          </span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
const props = defineProps({
  item: {
    type: Object,
    required: true,
  },
});

const emit = defineEmits(['close']);

function closeModal() {
  emit('close');
}

function formatTime() {
  const date = new Date(props.item.timestamp);
  return `${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}:${date.getSeconds().toString().padStart(2, '0')}`;
}
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.modal-content {
  background: #fff;
  border-radius: 16px;
  width: 90%;
  max-width: 600px;
  max-height: 80vh;
  overflow-y: auto;
  padding: 24px;
  box-shadow: 0 8px 32px rgba(0, 32, 128, 0.2);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.modal-header h3 {
  font-size: 1.3rem;
  color: #222;
  margin: 0;
}

.close-button {
  background: none;
  border: none;
  cursor: pointer;
  color: #7b8794;
  font-size: 1.2rem;
}

.modal-body {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.detail-row {
  display: flex;
  justify-content: space-between;
  padding: 8px 0;
  border-bottom: 1px solid #f0f4f8;
}

.detail-label {
  font-weight: 600;
  color: #4b5563;
}

.detail-value {
  color: #222;
}
</style>
