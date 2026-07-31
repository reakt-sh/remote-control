import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

let nextId = 0

export const useNotificationStore = defineStore('notification', () => {
  const notifications = ref([])

  // Maximum number of visible notifications
  const MAX_VISIBLE = 5

  const visibleNotifications = computed(() => {
    return notifications.value.slice(0, MAX_VISIBLE)
  })

  const hasNotifications = computed(() => {
    return notifications.value.length > 0
  })

  /**
   * Add a notification to the queue.
   * @param {string} message - The notification message
   * @param {'error'|'warning'|'info'|'success'} severity - Severity level
   * @param {number} duration - Auto-dismiss duration in ms (0 = no auto-dismiss)
   * @returns {number} notification id
   */
  function addNotification(message, severity = 'warning', duration = 3000) {
    const id = ++nextId
    const notification = {
      id,
      message,
      severity,
      timestamp: Date.now(),
      dismissed: false,
      progress: 100, // for countdown animation
    }

    notifications.value.unshift(notification)

    // Trim excess notifications
    if (notifications.value.length > 20) {
      notifications.value = notifications.value.slice(0, 20)
    }

    // Auto-dismiss if duration > 0
    if (duration > 0) {
      const startTime = Date.now()
      const interval = setInterval(() => {
        const elapsed = Date.now() - startTime
        const remaining = Math.max(0, 100 - (elapsed / duration) * 100)
        const idx = notifications.value.findIndex(n => n.id === id)
        if (idx !== -1) {
          notifications.value[idx].progress = remaining
        }
      }, 50)

      setTimeout(() => {
        clearInterval(interval)
        dismissNotification(id)
      }, duration)
    }

    return id
  }

  function dismissNotification(id) {
    const idx = notifications.value.findIndex(n => n.id === id)
    if (idx !== -1) {
      notifications.value[idx].dismissed = true
      // Remove after animation completes
      setTimeout(() => {
        notifications.value = notifications.value.filter(n => n.id !== id)
      }, 300)
    }
  }

  function clearAll() {
    notifications.value.forEach(n => { n.dismissed = true })
    setTimeout(() => {
      notifications.value = []
    }, 300)
  }

  return {
    notifications,
    visibleNotifications,
    hasNotifications,
    addNotification,
    dismissNotification,
    clearAll,
  }
})