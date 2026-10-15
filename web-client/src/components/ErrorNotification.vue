<template>
  <Teleport to="body">
    <div class="notification-container" :class="{ 'has-notifications': store.hasNotifications }">
      <TransitionGroup name="notification-slide" tag="div" class="notification-list">
        <div
          v-for="notification in store.visibleNotifications"
          :key="notification.id"
          class="notification-toast"
          :class="[
            `severity-${notification.severity}`,
            { 'is-dismissed': notification.dismissed }
          ]"
          role="alert"
          @click="store.dismissNotification(notification.id)"
        >
          <div class="notification-icon">
            <i :class="iconFor(notification.severity)"></i>
          </div>

          <div class="notification-content">
            <div class="notification-header">
              <span class="notification-severity-label">{{ labelFor(notification.severity) }}</span>
              <span class="notification-time">{{ formatTime(notification.timestamp) }}</span>
            </div>
            <p class="notification-message">{{ notification.message }}</p>
          </div>

          <button
            class="notification-close"
            @click.stop="store.dismissNotification(notification.id)"
            aria-label="Dismiss notification"
          >
            <i class="fas fa-times"></i>
          </button>

          <!-- Progress bar for auto-dismiss countdown -->
          <div
            class="notification-progress"
            :style="{ width: notification.progress + '%' }"
          ></div>
        </div>
      </TransitionGroup>
    </div>
  </Teleport>
</template>

<script setup>
import { useNotificationStore } from '@/stores/notificationStore'

const store = useNotificationStore()

function iconFor(severity) {
  const icons = {
    error: 'fas fa-exclamation-circle',
    warning: 'fas fa-exclamation-triangle',
    info: 'fas fa-info-circle',
    success: 'fas fa-check-circle',
  }
  return icons[severity] || icons.info
}

function labelFor(severity) {
  const labels = {
    error: 'Error',
    warning: 'Warning',
    info: 'Information',
    success: 'Success',
  }
  return labels[severity] || labels.info
}

function formatTime(timestamp) {
  const date = new Date(timestamp)
  return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })
}
</script>

<style scoped>
.notification-container {
  position: fixed;
  top: 56px;
  left: 0;
  z-index: 9999;
  pointer-events: none;
  padding: 8px 16px 16px;
  width: 420px;
  max-width: calc(100vw - 32px);
  max-height: calc(100vh - 64px);
  overflow: hidden;
}

.notification-container.has-notifications {
  pointer-events: auto;
}

.notification-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.notification-toast {
  position: relative;
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 14px 16px;
  padding-bottom: 18px;
  border-radius: 12px;
  background: rgba(30, 30, 40, 0.95);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.08);
  box-shadow:
    0 8px 32px rgba(0, 0, 0, 0.4),
    0 2px 8px rgba(0, 0, 0, 0.2),
    inset 0 1px 0 rgba(255, 255, 255, 0.05);
  cursor: pointer;
  transition: transform 0.25s ease, box-shadow 0.25s ease;
  overflow: hidden;
}

.notification-toast:hover {
  transform: translateX(4px);
  box-shadow:
    0 12px 40px rgba(0, 0, 0, 0.5),
    0 4px 12px rgba(0, 0, 0, 0.3),
    inset 0 1px 0 rgba(255, 255, 255, 0.08);
}

.notification-toast:active {
  transform: translateX(2px) scale(0.98);
}

/* Severity-based accent colors */
.notification-toast.severity-error {
  border-left: 4px solid #ff4757;
  background: linear-gradient(135deg, rgba(255, 71, 87, 0.12), rgba(30, 30, 40, 0.95) 60%);
}

.notification-toast.severity-warning {
  border-left: 4px solid #ffa502;
  background: linear-gradient(135deg, rgba(255, 165, 2, 0.12), rgba(30, 30, 40, 0.95) 60%);
}

.notification-toast.severity-info {
  border-left: 4px solid #3498db;
  background: linear-gradient(135deg, rgba(52, 152, 219, 0.12), rgba(30, 30, 40, 0.95) 60%);
}

.notification-toast.severity-success {
  border-left: 4px solid #2ed573;
  background: linear-gradient(135deg, rgba(46, 213, 115, 0.12), rgba(30, 30, 40, 0.95) 60%);
}

.notification-icon {
  flex-shrink: 0;
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 10px;
  font-size: 1.1rem;
}

.severity-error .notification-icon {
  background: rgba(255, 71, 87, 0.2);
  color: #ff4757;
}

.severity-warning .notification-icon {
  background: rgba(255, 165, 2, 0.2);
  color: #ffa502;
}

.severity-info .notification-icon {
  background: rgba(52, 152, 219, 0.2);
  color: #3498db;
}

.severity-success .notification-icon {
  background: rgba(46, 213, 115, 0.2);
  color: #2ed573;
}

.notification-content {
  flex: 1;
  min-width: 0;
}

.notification-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 4px;
}

.notification-severity-label {
  font-size: 0.7rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: rgba(255, 255, 255, 0.5);
}

.notification-time {
  font-size: 0.65rem;
  color: rgba(255, 255, 255, 0.3);
  font-variant-numeric: tabular-nums;
}

.notification-message {
  font-size: 0.85rem;
  line-height: 1.5;
  color: rgba(255, 255, 255, 0.9);
  word-break: break-word;
  margin: 0;
  padding-right: 4px;
}

.notification-close {
  flex-shrink: 0;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  background: rgba(255, 255, 255, 0.06);
  color: rgba(255, 255, 255, 0.4);
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.7rem;
  transition: background 0.2s, color 0.2s;
  margin-top: 2px;
}

.notification-close:hover {
  background: rgba(255, 255, 255, 0.12);
  color: rgba(255, 255, 255, 0.8);
}

/* Progress bar */
.notification-progress {
  position: absolute;
  bottom: 0;
  left: 0;
  height: 3px;
  opacity: 0.3;
  transition: width 0.1s linear;
}

.severity-error .notification-progress {
  background: #ff4757;
}

.severity-warning .notification-progress {
  background: #ffa502;
}

.severity-info .notification-progress {
  background: #3498db;
}

.severity-success .notification-progress {
  background: #2ed573;
}

/* Transition animations */
.notification-slide-enter-active {
  transition: all 0.4s cubic-bezier(0.16, 1, 0.3, 1);
}

.notification-slide-leave-active {
  transition: all 0.3s ease-in;
}

.notification-slide-enter-from {
  opacity: 0;
  transform: translateX(-100%) scale(0.9);
}

.notification-slide-leave-to {
  opacity: 0;
  transform: translateX(-80%) scale(0.9);
}

/* Mobile responsiveness */
@media (max-width: 480px) {
  .notification-container {
    padding: 8px;
    width: 100%;
    max-width: 100vw;
  }

  .notification-toast {
    padding: 12px 14px;
    padding-bottom: 16px;
    border-radius: 10px;
  }

  .notification-icon {
    width: 30px;
    height: 30px;
    font-size: 0.95rem;
  }

  .notification-message {
    font-size: 0.8rem;
  }
}
</style>