<template>
  <div id="app">
    <AccessGate v-if="showAccessGate" />
    <router-view v-else />
  </div>
</template>

<script>
import AccessGate from '@/components/AccessGate.vue'
import { useAccessStore } from '@/stores/accessStore'

export default {
  name: 'App',
  components: { AccessGate },
  computed: {
    showAccessGate() {
      const store = useAccessStore()
      return !store.isGranted
    }
  },
  mounted() {
    if (screen.orientation && screen.orientation.lock) {
      screen.orientation.lock('portrait').catch(() => {
        // Some browsers (like iOS Safari) do not support this API
        // You can show a message or ignore
      });
    }
  }
}
</script>
