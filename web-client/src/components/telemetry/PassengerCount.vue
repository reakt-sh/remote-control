<template>
  <div class="passenger-count">
    <span v-if="passengerCount !== undefined && passengerCount !== null" class="count">
      {{ passengerCount }}
    </span>
    <span v-else class="no-data">No data</span>
  </div>
</template>

<script setup>
defineProps({
  passengerCount: {
    type: [Number, String],
    default: null
  }
});
</script>

<style scoped>
.passenger-count {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 40px;
}

.count {
  font-size: 1.5rem;
  font-weight: 700;
  color: #1f2937;
}

.no-data {
  font-size: 0.75rem;
  color: #9ca3af;
  font-style: italic;
}
</style>