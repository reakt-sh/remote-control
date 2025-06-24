<template>
  <div id="app">
    <router-view />
  </div>
</template>

<script>
export default {
  name: 'App',
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