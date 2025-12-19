<template>
  <div v-if="showPopup" class="session-timeout-overlay" @click.self="preventClose">
    <div class="session-timeout-popup">
      <div class="session-timeout-icon">
        <i class="fas fa-exclamation-triangle"></i>
      </div>
      <h2 class="session-timeout-title">Session About to Expire</h2>
      <p class="session-timeout-message">
        Your session will expire in <strong>{{ countdown }}</strong> second{{ countdown !== 1 ? 's' : '' }}.
      </p>
      <div class="session-timeout-countdown">
        <div class="countdown-number">{{ countdown }}</div>
      </div>
      <p class="session-timeout-warning">
        You will be logged out automatically for security purposes.
      </p>
    </div>
  </div>
</template>

<script>
import sessionTimeoutService from '../services/sessionTimeoutService.js'

export default {
  name: 'SessionTimeoutPopup',
  data() {
    return {
      showPopup: false,
      countdown: 5
    }
  },
  mounted() {
    // Register callbacks with session timeout service
    sessionTimeoutService.onWarning(() => {
      this.showPopup = true
    })

    sessionTimeoutService.onCountdown((seconds) => {
      this.countdown = seconds
    })

    sessionTimeoutService.onLogout(() => {
      this.showPopup = false
      this.handleLogout()
    })

    // Start the service if user is authenticated
    this.checkAuthAndStart()

    // Listen for auth changes
    window.addEventListener('authChanged', this.checkAuthAndStart)
    
    // Check periodically for auth changes (in case event doesn't fire)
    this.authCheckInterval = setInterval(() => {
      this.checkAuthAndStart()
    }, 5000)
  },
  beforeUnmount() {
    sessionTimeoutService.stop()
    window.removeEventListener('authChanged', this.checkAuthAndStart)
    if (this.authCheckInterval) {
      clearInterval(this.authCheckInterval)
    }
  },
  methods: {
    preventClose() {
      // Prevent closing by clicking overlay during countdown
      // User must wait for automatic logout
    },
    handleLogout() {
      // Perform logout
      sessionTimeoutService.performLogout()
    },
    checkAuthAndStart() {
      // Check authentication status and start/stop service accordingly
      const accessToken = localStorage.getItem('access_token')
      if (accessToken) {
        // User is authenticated - start service if not already running
        if (!sessionTimeoutService.checkInterval) {
          this.showPopup = false
          this.countdown = 5
          sessionTimeoutService.start()
        }
      } else {
        // User is not authenticated - stop service
        sessionTimeoutService.stop()
        this.showPopup = false
      }
    }
  },
  watch: {
    // Restart service when authentication status changes
    '$store.getters.isAuthenticated'(isAuthenticated) {
      if (isAuthenticated) {
        this.showPopup = false
        this.countdown = 5
        sessionTimeoutService.start()
      } else {
        sessionTimeoutService.stop()
        this.showPopup = false
      }
    }
  }
}
</script>

<style scoped>
.session-timeout-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.7);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 10000;
  animation: fadeIn 0.3s ease-in;
}

@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

.session-timeout-popup {
  background: white;
  border-radius: 12px;
  padding: 40px;
  max-width: 450px;
  width: 90%;
  text-align: center;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.3);
  animation: slideUp 0.3s ease-out;
}

@keyframes slideUp {
  from {
    transform: translateY(30px);
    opacity: 0;
  }
  to {
    transform: translateY(0);
    opacity: 1;
  }
}

.session-timeout-icon {
  font-size: 64px;
  color: #f59e0b;
  margin-bottom: 20px;
  animation: pulse 1s infinite;
}

@keyframes pulse {
  0%, 100% {
    transform: scale(1);
  }
  50% {
    transform: scale(1.1);
  }
}

.session-timeout-title {
  font-size: 24px;
  font-weight: 600;
  color: #1f2937;
  margin: 0 0 16px 0;
}

.session-timeout-message {
  font-size: 16px;
  color: #4b5563;
  margin: 0 0 24px 0;
  line-height: 1.5;
}

.session-timeout-message strong {
  color: #dc2626;
  font-size: 18px;
  font-weight: 700;
}

.session-timeout-countdown {
  margin: 30px 0;
}

.countdown-number {
  font-size: 72px;
  font-weight: 700;
  color: #dc2626;
  line-height: 1;
  animation: countdownPulse 1s infinite;
  font-family: 'Courier New', monospace;
}

@keyframes countdownPulse {
  0%, 100% {
    transform: scale(1);
    opacity: 1;
  }
  50% {
    transform: scale(1.15);
    opacity: 0.9;
  }
}

.session-timeout-warning {
  font-size: 14px;
  color: #6b7280;
  margin: 24px 0 0 0;
  line-height: 1.5;
}
</style>

