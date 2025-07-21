<template>
  <div class="telemetry-list">
    <div class="list-header">
      <h3>Telemetry History</h3>
      <div class="pagination-controls">
        <button @click="prevPage" :disabled="currentPage === 1">
          <i class="fas fa-chevron-left"></i>
        </button>
        <span>{{ currentPage }} / {{ totalPages }}</span>
        <button @click="nextPage" :disabled="currentPage === totalPages">
          <i class="fas fa-chevron-right"></i>
        </button>
      </div>
    </div>
    <div class="list-table">
      <div class="table-header">
        <div class="header-cell timestamp">Timestamp</div>
        <div class="header-cell location">Location</div>
        <div class="header-cell speed">Speed</div>
        <div class="header-cell gps">GPS</div>
        <div class="header-cell signal">Signal</div>
        <div class="header-cell temperature">Temp</div>
      </div>
      <div 
        v-for="item in paginatedData" 
        :key="item.timestamp" 
        class="table-row"
        @click="selectItem(item)"
      >
        <div class="table-cell timestamp">
          {{ formatTime(item.timestamp) }}
        </div>
        <div class="table-cell location">
          <i class="fas fa-map-marker-alt"></i> {{ item.location }}
        </div>
        <div class="table-cell speed">
          <i class="fas fa-tachometer-alt"></i> {{ item.speed }} km/h
        </div>
        <div class="table-cell gps">
          <i class="fas fa-globe"></i> {{ formatGPS(item.gps) }}
        </div>
        <div class="table-cell signal">
          <i class="fas fa-signal"></i> {{ item.network_signal_strength }}%
        </div>
        <div class="table-cell temperature">
          <i class="fas fa-thermometer-half"></i> {{ item.temperature }}°C
        </div>
      </div>
    </div>
    <TelemetryDetailModal 
      v-if="selectedItem" 
      :item="selectedItem" 
      @close="selectedItem = null"
    />
  </div>
</template>

<script setup>
import { ref, computed } from 'vue';
import TelemetryDetailModal from './TelemetryDetailModal.vue';

const props = defineProps({
  telemetryData: {
    type: Array,
    required: true,
  },
});

const itemsPerPage = 5;
const currentPage = ref(1);
const selectedItem = ref(null);

const sortedData = computed(() => {
  return [...props.telemetryData].sort((a, b) => b.timestamp - a.timestamp);
});

const totalPages = computed(() => {
  return Math.ceil(sortedData.value.length / itemsPerPage);
});

const paginatedData = computed(() => {
  const start = (currentPage.value - 1) * itemsPerPage;
  const end = start + itemsPerPage;
  return sortedData.value.slice(start, end);
});

function prevPage() {
  if (currentPage.value > 1) {
    currentPage.value--;
  }
}

function nextPage() {
  if (currentPage.value < totalPages.value) {
    currentPage.value++;
  }
}

function selectItem(item) {
  selectedItem.value = item;
}

function formatTime(timestamp) {
  const date = new Date(timestamp);
  return `${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}:${date.getSeconds().toString().padStart(2, '0')}`;
}

function formatGPS(gps) {
  if (!gps || !gps.latitude || !gps.longitude) return 'N/A';
  return `${Number(gps.latitude).toFixed(6)}, ${Number(gps.longitude).toFixed(6)}`;
}
</script>

<style scoped>
.telemetry-list {
  background: #fff;
  border-radius: 16px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  padding: 24px;
  margin-top: 24px;
}

.list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.list-header h3 {
  font-size: 1.2rem;
  color: #222;
  margin: 0;
}

.pagination-controls {
  display: flex;
  align-items: center;
  gap: 12px;
}

.pagination-controls button {
  background: none;
  border: none;
  cursor: pointer;
  color: #4b5563;
  font-size: 1rem;
}

.pagination-controls button:disabled {
  color: #b0b7c3;
  cursor: not-allowed;
}

.list-table {
  display: grid;
  grid-template-columns: 1fr 2fr 0.8fr 1.2fr 0.8fr 0.8fr;
  gap: 1px;
  background-color: #e0e7ef;
  border-radius: 8px;
  overflow: hidden;
}

.table-header, .table-row {
  display: contents;
}

.header-cell, .table-cell {
  padding: 12px 16px;
  background: #fff;
  display: flex;
  align-items: center;
  gap: 6px;
}

.header-cell {
  font-weight: 600;
  color: #4b5563;
  background: #f8fafc;
}

.table-cell {
  color: #4b5563;
  font-size: 0.9rem;
  cursor: pointer;
  transition: background 0.2s;
}

.table-row:hover .table-cell {
  background: #e3f0fa;
}

.table-cell i {
  color: #0096ff;
}

.timestamp {
  justify-content: flex-start;
}

.location {
  justify-content: flex-start;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.speed, .gps, .signal, .temperature {
  justify-content: center;
}
</style>
