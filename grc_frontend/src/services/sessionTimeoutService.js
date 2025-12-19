/**
 * Session Timeout Service
 * Tracks session expiration and shows countdown popup before logout
 */

class SessionTimeoutService {
  constructor() {
    this.timeoutSeconds = 3600 // 1 hour in seconds
    this.warningSeconds = 5 // Show warning 5 seconds before expiration
    this.checkInterval = null
    this.warningInterval = null
    this.countdownInterval = null
    this.callbacks = {
      onWarning: null,
      onCountdown: null,
      onLogout: null
    }
    this.isWarningShown = false
    this.isCountingDown = false
  }

  /**
   * Initialize session timeout tracking
   */
  start() {
    // Clear any existing intervals
    this.stop()
    
    // Check session timeout every second
    this.checkInterval = setInterval(() => {
      this.checkSessionTimeout()
    }, 1000)
    
    console.log('⏰ Session timeout service started (1 hour timeout)')
  }

  /**
   * Stop session timeout tracking
   */
  stop() {
    if (this.checkInterval) {
      clearInterval(this.checkInterval)
      this.checkInterval = null
    }
    if (this.warningInterval) {
      clearInterval(this.warningInterval)
      this.warningInterval = null
    }
    if (this.countdownInterval) {
      clearInterval(this.countdownInterval)
      this.countdownInterval = null
    }
    this.isWarningShown = false
    this.isCountingDown = false
  }

  /**
   * Check if session is about to expire
   */
  checkSessionTimeout() {
    const accessToken = localStorage.getItem('access_token')
    if (!accessToken) {
      this.stop()
      return
    }

    try {
      // Decode JWT token to get login_time
      const tokenPayload = JSON.parse(atob(accessToken.split('.')[1]))
      const loginTime = tokenPayload.login_time || tokenPayload.iat || (Date.now() / 1000)
      
      const currentTime = Date.now() / 1000
      const elapsedTime = currentTime - loginTime
      const remainingTime = this.timeoutSeconds - elapsedTime

      // If less than warning seconds remain and warning not shown yet
      if (remainingTime <= this.warningSeconds && remainingTime > 0 && !this.isWarningShown) {
        this.showWarning(remainingTime)
      }

      // If session has expired
      if (remainingTime <= 0) {
        this.handleSessionExpired()
      }
    } catch (error) {
      console.error('❌ Error checking session timeout:', error)
    }
  }

  /**
   * Show warning popup with countdown
   */
  showWarning(remainingTime) {
    this.isWarningShown = true
    
    // Trigger warning callback
    if (this.callbacks.onWarning) {
      this.callbacks.onWarning()
    }

    // Start countdown
    this.startCountdown(Math.ceil(remainingTime))
  }

  /**
   * Start countdown timer
   */
  startCountdown(seconds) {
    if (this.isCountingDown) {
      return
    }
    
    this.isCountingDown = true
    let countdown = Math.min(seconds, this.warningSeconds)

    // Update countdown immediately
    if (this.callbacks.onCountdown) {
      this.callbacks.onCountdown(countdown)
    }

    // Update countdown every second
    this.countdownInterval = setInterval(() => {
      countdown--
      
      if (countdown > 0) {
        // Update countdown
        if (this.callbacks.onCountdown) {
          this.callbacks.onCountdown(countdown)
        }
      } else {
        // Countdown finished - logout
        this.handleSessionExpired()
      }
    }, 1000)
  }

  /**
   * Handle session expiration - logout user
   */
  handleSessionExpired() {
    console.log('⏰ Session expired - logging out')
    
    this.stop()

    // Trigger logout callback
    if (this.callbacks.onLogout) {
      this.callbacks.onLogout()
    } else {
      // Default logout behavior
      this.performLogout()
    }
  }

  /**
   * Perform logout
   */
  performLogout() {
    // Clear all auth data
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    localStorage.removeItem('user_id')
    localStorage.removeItem('user')
    localStorage.removeItem('user_email')
    localStorage.removeItem('user_name')
    localStorage.removeItem('is_logged_in')

    // Redirect to login
    if (window.location.pathname !== '/login') {
      window.location.href = '/login'
    }
  }

  /**
   * Register callbacks
   */
  onWarning(callback) {
    this.callbacks.onWarning = callback
  }

  onCountdown(callback) {
    this.callbacks.onCountdown = callback
  }

  onLogout(callback) {
    this.callbacks.onLogout = callback
  }

  /**
   * Get remaining session time in seconds
   */
  getRemainingTime() {
    const accessToken = localStorage.getItem('access_token')
    if (!accessToken) {
      return 0
    }

    try {
      const tokenPayload = JSON.parse(atob(accessToken.split('.')[1]))
      const loginTime = tokenPayload.login_time || tokenPayload.iat || (Date.now() / 1000)
      const currentTime = Date.now() / 1000
      const elapsedTime = currentTime - loginTime
      return Math.max(0, this.timeoutSeconds - elapsedTime)
    } catch (error) {
      console.error('❌ Error getting remaining time:', error)
      return 0
    }
  }
}

// Export singleton instance
const sessionTimeoutService = new SessionTimeoutService()
export default sessionTimeoutService

