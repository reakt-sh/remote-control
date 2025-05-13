<!-- filepath: /home/rcd/Desktop/Workspace/TrainRemoteControl/web-client/src/components/telemetry/PassengerCount.vue -->
<template>
  <div class="passenger-count">
    <span v-if="passengerCount !== undefined && passengerCount !== null">
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
  font-size: 2rem;
  font-weight: bold;
  color: #2c3e50;
  text-align: center;
}
.no-data {
  font-size: 1rem;
  color: #bbb;
}
</style>