<template>
  <div class="otp-container">
    <!-- Left Side - Security Information & Charts -->
    <div class="left-panel">
    <!-- Background decoration -->
    <div class="background-decoration">
      <div class="circle circle-1"></div>
      <div class="circle circle-2"></div>
      <div class="circle circle-3"></div>
        <div class="chart-lines">
          <div class="line line-1"></div>
          <div class="line line-2"></div>
          <div class="line line-3"></div>
        </div>
    </div>
    
      <!-- Product Header -->
      <div class="product-header">
      <div class="logo-section">
          <div class="logo-text">
            <span class="logo-main">TPRM</span>
          </div>
        </div>
        <div class="product-info">
          <h1>TPRM Security Gateway</h1>
          <p>Secure access to your Third Party Risk Management platform. Multi-factor authentication ensures only authorized users can access vendor data, contract information, risk assessments, and compliance reports.</p>
        </div>
      </div>
      
      <!-- Security Feature Cards -->
      <div class="feature-cards">
        <div class="feature-card">
          <div class="feature-icon">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect>
              <path d="M7 11V7a5 5 0 0 1 10 0v4"></path>
          </svg>
        </div>
          <div class="feature-content">
            <h3>Protected access to vendor risk assessments and compliance data</h3>
          </div>
      </div>
      
        <div class="feature-card">
          <div class="feature-icon">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M9 12l2 2 4-4"></path>
              <path d="M21 12c-1 0-3-1-3-3s2-3 3-3 3 1 3 3-2 3-3 3"></path>
            </svg>
          </div>
          <div class="feature-content">
            <h3>Secure RFP management and contract lifecycle workflows</h3>
          </div>
        </div>
        
        <div class="feature-card">
          <div class="feature-icon">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="10"></circle>
              <line x1="4.93" y1="4.93" x2="19.07" y2="19.07"></line>
            </svg>
          </div>
          <div class="feature-content">
            <h3>Encrypted BCP/DRP planning and SLA monitoring systems</h3>
          </div>
        </div>
      </div>
      
      <!-- Encryption Criteria Card -->
      <div class="encryption-card">
        <div class="encryption-header">
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect>
            <path d="M7 11V7a5 5 0 0 1 10 0v4"></path>
          </svg>
          <h3>Encryption Criteria</h3>
        </div>
        <div class="encryption-content">
          <div class="encryption-note">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect>
              <path d="M7 11V7a5 5 0 0 1 10 0v4"></path>
            </svg>
            <span>Your code is encrypted and secure</span>
          </div>
          <div class="encryption-note">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="10"></circle>
              <line x1="4.93" y1="4.93" x2="19.07" y2="19.07"></line>
            </svg>
            <span>Never share this code with anyone</span>
          </div>
          <div class="encryption-note">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path>
              <line x1="12" y1="9" x2="12" y2="13"></line>
              <line x1="12" y1="17" x2="12.01" y2="17"></line>
            </svg>
            <span>Maximum 3 attempts allowed</span>
          </div>
        </div>
        <div class="otp-process">
          <p>OTP is automatically sent to your registered email address using AES-256 encryption. The verification code expires in 10 minutes for maximum security.</p>
        </div>
      </div>
    </div>
    
    <!-- Right Side - OTP Form -->
    <div class="right-panel">
      <div class="otp-card">
      <div class="otp-header">
        <h1>Verify Your Identity</h1>
        <p>Enter the 6-digit code sent to your email</p>
        <div class="user-info" v-if="otpUser">
          <svg class="email-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"></path>
            <polyline points="22,6 12,13 2,6"></polyline>
          </svg>
          <span class="email-mask">{{ maskedEmail }}</span>
        </div>
      </div>
      
      <form @submit.prevent="handleVerifyOtp" class="otp-form">
        <!-- Alert Messages -->
        <transition name="alert-fade">
          <div v-if="alert.message" :class="['alert', `alert-${alert.type}`]">
            <div class="alert-icon">
              <span v-if="alert.type === 'success'">✓</span>
              <span v-else-if="alert.type === 'error'">✕</span>
              <span v-else>ℹ</span>
            </div>
            <span class="alert-text">{{ alert.message }}</span>
          </div>
        </transition>
        
        <!-- OTP Input -->
        <div class="form-group">
          <label for="otp">
            <svg class="input-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect>
              <path d="M7 11V7a5 5 0 0 1 10 0v4"></path>
            </svg>
            Verification Code
          </label>
          <div class="otp-input-container">
            <input
              v-for="(digit, index) in otpDigits"
              :key="index"
              :ref="'otpInput' + index"
              v-model="otpDigits[index]"
              type="text"
              inputmode="numeric"
              pattern="[0-9]"
              maxlength="1"
              class="otp-digit"
              :disabled="loading"
              @input="handleOtpInput(index, $event)"
              @keydown="handleKeyDown(index, $event)"
              @paste="handlePaste($event)"
            />
          </div>
        </div>
        
        <!-- Timer -->
        <transition name="timer-fade">
          <div class="timer-container" v-if="timeRemaining > 0">
            <svg class="timer-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="10"></circle>
              <polyline points="12 6 12 12 16 14"></polyline>
            </svg>
            <span class="timer-text">Code expires in <strong>{{ formatTime(timeRemaining) }}</strong></span>
          </div>
        </transition>
        
        <!-- Submit Button -->
        <button
          type="submit"
          :disabled="loading || !isOtpComplete"
          class="btn btn-primary btn-full"
        >
          <span v-if="loading" class="btn-content">
            <svg class="spinner" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            Verifying...
          </span>
          <span v-else class="btn-content">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="20 6 9 17 4 12"></polyline>
            </svg>
            Verify Code
          </span>
        </button>
        
        <!-- Resend Button -->
        <button
          type="button"
          @click="handleResendOtp"
          :disabled="loading || resendCooldown > 0"
          class="btn btn-secondary btn-full"
        >
          <span v-if="resendCooldown > 0" class="btn-content">
            <svg class="spinner-slow" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="1 4 1 10 7 10"></polyline>
              <polyline points="23 20 23 14 17 14"></polyline>
              <path d="M20.49 9A9 9 0 0 0 5.64 5.64L1 10m22 4l-4.64 4.36A9 9 0 0 1 3.51 15"></path>
            </svg>
            Resend in {{ resendCooldown }}s
          </span>
          <span v-else-if="loading" class="btn-content">
            <svg class="spinner" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            Sending...
          </span>
          <span v-else class="btn-content">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="22" y1="2" x2="11" y2="13"></line>
              <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
            </svg>
            Resend Code
          </span>
        </button>
      </form>
      
      <!-- Back to Login -->
      <div class="back-to-login">
        <button @click="backToLogin" class="btn-link">
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="19" y1="12" x2="5" y2="12"></line>
            <polyline points="12 19 5 12 12 5"></polyline>
          </svg>
          Back to Login
        </button>
      </div>
      
        </div>
    </div>
  </div>
</template>

<script>
import { mapActions, mapGetters } from 'vuex'
import permissionsService from '@/services/permissionsService'

export default {
  name: 'OtpVerificationView',
  
  data() {
    return {
      otpDigits: ['', '', '', '', '', ''],
      loading: false,
      alert: {
        message: '',
        type: ''
      },
      timeRemaining: 600, // 10 minutes in seconds
      timer: null,
      resendCooldown: 0,
      resendTimer: null
    }
  },
  
  computed: {
    ...mapGetters('auth', ['otpUser', 'requiresOtp']),
    
    isOtpComplete() {
      return this.otpDigits.every(digit => digit !== '')
    },
    
    otpCode() {
      return this.otpDigits.join('')
    },
    
    maskedEmail() {
      if (!this.otpUser?.email) return ''
      const email = this.otpUser.email
      const [localPart, domain] = email.split('@')
      const maskedLocal = localPart.length > 2 
        ? localPart.slice(0, 2) + '*'.repeat(localPart.length - 2)
        : localPart
      return `${maskedLocal}@${domain}`
    }
  },
  
  methods: {
    ...mapActions('auth', ['verifyOtp', 'resendOtp']),

    async getPostLoginRoute() {
      try {
        const token = localStorage.getItem('session_token')
        if (!token) {
          console.warn('No session token available, defaulting to home page')
          return '/'
        }
        
        // Get user ID from localStorage (user object has 'userid' field)
        let userId = null
        try {
          const currentUser = JSON.parse(localStorage.getItem('current_user') || '{}')
          userId = currentUser.userid || currentUser.id || currentUser.user_id
        } catch (e) {
          console.error('Error getting user ID:', e)
        }
        
        // Use role-based routing service
        const roleRoutingService = await import('@/services/roleRoutingService')
        return await roleRoutingService.getPostLoginRoute(token, userId)
      } catch (error) {
        console.error('OtpVerification: Failed to resolve post-login route', error)
        return '/'
      }
    },
    
    async handleVerifyOtp() {
      if (!this.isOtpComplete) return
      
      this.loading = true
      this.clearAlert()
      
      try {
        const result = await this.verifyOtp(this.otpCode)
        
        if (result.success) {
          this.showAlert('Login successful! Redirecting...', 'success')
          const targetRoute = await this.getPostLoginRoute()
          setTimeout(() => {
            // Redirect based on role and registration status
            this.$router.push(targetRoute)
          }, 1500)
        } else {
          this.showAlert(result.error || 'Invalid OTP. Please try again.', 'error')
          this.clearOtp()
        }
      } catch (error) {
        this.showAlert('Verification failed. Please try again.', 'error')
        console.error('OTP verification error:', error)
        this.clearOtp()
      } finally {
        this.loading = false
      }
    },
    
    async handleResendOtp() {
      if (this.resendCooldown > 0) return
      
      this.loading = true
      this.clearAlert()
      
      try {
        const result = await this.resendOtp()
        
        if (result.success) {
          this.showAlert(result.message || 'New OTP sent successfully!', 'success')
          this.startResendCooldown()
          this.resetTimer()
        } else {
          this.showAlert(result.error || 'Failed to resend OTP', 'error')
        }
      } catch (error) {
        this.showAlert('Failed to resend code. Please try again.', 'error')
        console.error('Resend OTP error:', error)
      } finally {
        this.loading = false
      }
    },
    
    handleOtpInput(index, event) {
      const value = event.target.value.replace(/[^0-9]/g, '')
      
      if (value) {
        this.otpDigits[index] = value
        // Move to next input
        if (index < 5) {
          this.$refs['otpInput' + (index + 1)][0].focus()
        }
      }
    },
    
    handleKeyDown(index, event) {
      if (event.key === 'Backspace' && !this.otpDigits[index] && index > 0) {
        this.$refs['otpInput' + (index - 1)][0].focus()
      } else if (event.key === 'ArrowLeft' && index > 0) {
        this.$refs['otpInput' + (index - 1)][0].focus()
      } else if (event.key === 'ArrowRight' && index < 5) {
        this.$refs['otpInput' + (index + 1)][0].focus()
      }
    },
    
    handlePaste(event) {
      event.preventDefault()
      const pastedData = event.clipboardData.getData('text').replace(/[^0-9]/g, '')
      
      if (pastedData.length === 6) {
        for (let i = 0; i < 6; i++) {
          this.otpDigits[i] = pastedData[i]
        }
      }
    },
    
    clearOtp() {
      this.otpDigits = ['', '', '', '', '', '']
      this.$refs.otpInput0[0].focus()
    },
    
    backToLogin() {
      this.$store.commit('auth/CLEAR_AUTH')
      this.$router.push('/login')
    },
    
    startTimer() {
      this.timer = setInterval(() => {
        if (this.timeRemaining > 0) {
          this.timeRemaining--
        } else {
          this.clearTimer()
          this.showAlert('Code has expired. Please request a new one.', 'error')
        }
      }, 1000)
    },
    
    clearTimer() {
      if (this.timer) {
        clearInterval(this.timer)
        this.timer = null
      }
    },
    
    resetTimer() {
      this.clearTimer()
      this.timeRemaining = 600
      this.startTimer()
    },
    
    startResendCooldown() {
      this.resendCooldown = 30
      this.resendTimer = setInterval(() => {
        if (this.resendCooldown > 0) {
          this.resendCooldown--
        } else {
          clearInterval(this.resendTimer)
          this.resendTimer = null
        }
      }, 1000)
    },
    
    formatTime(seconds) {
      const minutes = Math.floor(seconds / 60)
      const remainingSeconds = seconds % 60
      return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`
    },
    
    showAlert(message, type) {
      this.alert = { message, type }
      if (type === 'success') {
        setTimeout(() => {
          this.clearAlert()
        }, 3000)
      }
    },
    
    clearAlert() {
      this.alert = { message: '', type: '' }
    }
  },
  
  mounted() {
    // Check if we have OTP user data and requiresOtp flag
    if (!this.otpUser || !this.requiresOtp) {
      console.log('No OTP user found, redirecting to login')
      this.$router.push('/login')
      return
    }
    
    console.log('OTP verification for user:', this.otpUser.username)
    
    // Focus first input
    this.$nextTick(() => {
      if (this.$refs.otpInput0 && this.$refs.otpInput0[0]) {
        this.$refs.otpInput0[0].focus()
      }
    })
    
    // Start countdown timer
    this.startTimer()
  },
  
  beforeUnmount() {
    this.clearTimer()
    if (this.resendTimer) {
      clearInterval(this.resendTimer)
    }
  }
}
</script>

<style scoped>
* {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

.otp-container {
  min-height: 100vh;
  display: flex;
  background: #f8fafc;
  position: relative;
  overflow: hidden;
}

/* Left Panel - Security Information & Charts */
.left-panel {
  flex: 1;
  background: linear-gradient(135deg, #1e3a8a 0%, #1e40af 100%);
  position: relative;
  display: flex;
  flex-direction: column;
  padding: 3rem;
  overflow: hidden;
}

/* Background decoration */
.background-decoration {
  position: absolute;
  inset: 0;
  overflow: hidden;
  pointer-events: none;
}

.circle {
  position: absolute;
  border-radius: 50%;
  background: rgba(230, 17, 17, 0.15);
  backdrop-filter: blur(20px);
}

.circle-1 {
  width: 200px;
  height: 200px;
  top: -50px;
  right: -50px;
  animation: float 20s ease-in-out infinite;
}

.circle-2 {
  width: 150px;
  height: 150px;
  bottom: -30px;
  left: -30px;
  animation: float 15s ease-in-out infinite reverse;
}

.circle-3 {
  width: 100px;
  height: 100px;
  top: 60%;
  right: 20%;
  animation: float 25s ease-in-out infinite;
}

.chart-lines {
  position: absolute;
  inset: 0;
  pointer-events: none;
}

.line {
  position: absolute;
  background: rgba(239, 68, 68, 0.2);
  border-radius: 2px;
}

.line-1 {
  width: 2px;
  height: 100px;
  top: 20%;
  left: 10%;
  transform: rotate(15deg);
}

.line-2 {
  width: 1px;
  height: 80px;
  top: 40%;
  right: 15%;
  transform: rotate(-20deg);
}

.line-3 {
  width: 1.5px;
  height: 60px;
  bottom: 30%;
  left: 20%;
  transform: rotate(45deg);
}

@keyframes float {
  0%, 100% {
    transform: translateY(0) translateX(0);
  }
  50% {
    transform: translateY(-20px) translateX(20px);
  }
}

/* Product Header */
.product-header {
  margin-bottom: 3rem;
  z-index: 2;
  position: relative;
}

.logo-section {
  display: flex;
  justify-content: flex-start;
  margin-bottom: 2rem;
}

.logo-text {
  position: relative;
  display: flex;
  align-items: baseline;
  gap: 0.5rem;
}

.logo-main {
  font-size: 2.5rem;
  font-weight: 800;
  color: white;
  letter-spacing: -0.02em;
}

.logo-accent {
  font-size: 2.5rem;
  font-weight: 800;
  color: #60a5fa;
  letter-spacing: -0.02em;
}

.logo-dot {
  position: absolute;
  top: -8px;
  right: -12px;
  width: 8px;
  height: 8px;
  background: #ef4444;
  border-radius: 50%;
}

.logo-check {
  position: absolute;
  bottom: -5px;
  right: -8px;
  width: 16px;
  height: 16px;
  background: #22c55e;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.logo-check::after {
  content: '✓';
  color: white;
  font-size: 10px;
  font-weight: bold;
}

.product-info h1 {
  color: white;
  margin-bottom: 1rem;
  font-size: 2.25rem;
  font-weight: 700;
  letter-spacing: -0.02em;
  line-height: 1.2;
}

.product-info p {
  color: rgba(255, 255, 255, 0.9);
  font-size: 1rem;
  font-weight: 400;
  line-height: 1.6;
  max-width: 90%;
}

/* Feature Cards */
.feature-cards {
  display: flex;
  flex-direction: row;
  gap: 1rem;
  margin-bottom: 2rem;
  z-index: 2;
  position: relative;
}

.feature-card {
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(20px);
  border-radius: 12px;
  padding: 1.5rem;
  border: 1px solid rgba(255, 255, 255, 0.15);
  transition: all 0.3s ease;
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  gap: 1rem;
  flex: 1;
}

.feature-card:hover {
  transform: translateY(-2px);
  background: rgba(255, 255, 255, 0.15);
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
}

.feature-icon {
  width: 24px;
  height: 24px;
  color: white;
  flex-shrink: 0;
}

.feature-content h3 {
  color: white;
  font-size: 0.95rem;
  font-weight: 500;
  margin: 0;
  line-height: 1.4;
}

/* Encryption Criteria Card */
.encryption-card {
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(20px);
  border-radius: 12px;
  padding: 1.5rem;
  border: 1px solid rgba(255, 255, 255, 0.15);
  margin-bottom: 2rem;
  z-index: 2;
  position: relative;
  transition: all 0.3s ease;
}

.encryption-card:hover {
  transform: translateY(-2px);
  background: rgba(255, 255, 255, 0.15);
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
}

.encryption-header {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 1.5rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.2);
}

.encryption-header svg {
  width: 24px;
  height: 24px;
  color: #ef4444;
}

.encryption-header h3 {
  color: white;
  font-size: 1.1rem;
  font-weight: 600;
  margin: 0;
}

.encryption-content {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  margin-bottom: 1.5rem;
}

.encryption-note {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem;
  background: rgba(239, 68, 68, 0.1);
  border: 1px solid rgba(239, 68, 68, 0.3);
  border-radius: 8px;
  color: #ef4444;
  font-size: 0.9rem;
  font-weight: 500;
  transition: all 0.3s ease;
}

.encryption-note:hover {
  background: rgba(239, 68, 68, 0.15);
  transform: translateX(4px);
}

.encryption-note svg {
  width: 18px;
  height: 18px;
  color: #ef4444;
  flex-shrink: 0;
}

.otp-process {
  padding: 1rem;
  background: rgba(102, 126, 234, 0.1);
  border: 1px solid rgba(102, 126, 234, 0.3);
  border-radius: 8px;
}

.otp-process p {
  color: rgba(255, 255, 255, 0.9);
  font-size: 0.85rem;
  font-weight: 400;
  line-height: 1.5;
  margin: 0;
  text-align: left;
}

.summary-card {
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(20px);
  border-radius: 12px;
  padding: 1.5rem;
  border: 1px solid rgba(255, 255, 255, 0.15);
  transition: all 0.3s ease;
}

.summary-card:hover {
  transform: translateY(-2px);
  background: rgba(255, 255, 255, 0.15);
}

.summary-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.summary-header h3 {
  color: white;
  font-size: 0.9rem;
  font-weight: 600;
  margin: 0;
}

.trend-indicator {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  font-size: 0.8rem;
  font-weight: 600;
}

.trend-indicator.positive {
  color: #22c55e;
}

.trend-indicator svg {
  width: 12px;
  height: 12px;
}

.score-value {
  color: white;
  font-size: 1.2rem;
  font-weight: 700;
}

.mini-chart {
  height: 40px;
  display: flex;
  align-items: center;
}

.chart-svg {
  width: 100%;
  height: 100%;
  color: #60a5fa;
}

.chart-line {
  stroke: currentColor;
  fill: none;
  stroke-linecap: round;
  stroke-linejoin: round;
}

.chart-dot {
  fill: currentColor;
}

.progress-ring {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 40px;
}

.progress-svg {
  width: 40px;
  height: 40px;
  transform: rotate(-90deg);
}

.progress-bg {
  fill: none;
  stroke: rgba(255, 255, 255, 0.2);
  stroke-width: 2;
}

.progress-bar {
  fill: none;
  stroke: #22c55e;
  stroke-width: 2;
  stroke-linecap: round;
  transition: stroke-dasharray 0.3s ease;
}


/* Right Panel - OTP Form */
.right-panel {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2rem;
  background: #f8fafc;
}

.otp-card {
  background: white;
  border-radius: 24px;
  padding: 3rem;
  box-shadow: 0 25px 50px rgba(0, 0, 0, 0.1);
  width: 100%;
  max-width: 420px;
  border: 2px solid #374151;
  position: relative;
  animation: slideUp 0.6s ease-out;
}

@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateY(30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.otp-header {
  text-align: center;
  margin-bottom: 2.5rem;
}

.otp-header h1 {
  color: #1a202c;
  margin-bottom: 0.75rem;
  font-size: 2rem;
  font-weight: 700;
  letter-spacing: -0.5px;
}

.otp-header p {
  color: #64748b;
  font-size: 1rem;
  margin-bottom: 1.25rem;
  line-height: 1.5;
}

.user-info {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.75rem;
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%);
  padding: 1rem;
  border-radius: 12px;
  border: 1px solid rgba(102, 126, 234, 0.2);
  margin-top: 1rem;
}

.email-icon {
  width: 20px;
  height: 20px;
  color: #667eea;
  flex-shrink: 0;
}

.email-mask {
  color: #667eea;
  font-weight: 600;
  font-size: 0.95rem;
}

.otp-form {
  margin-bottom: 2rem;
}

.form-group {
  margin-bottom: 1.5rem;
}

.form-group label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: #334155;
  font-size: 0.9rem;
  font-weight: 600;
  margin-bottom: 1rem;
}

.input-icon {
  width: 18px;
  height: 18px;
  color: #667eea;
}

.otp-input-container {
  display: flex;
  justify-content: center;
  gap: 0.75rem;
  margin-bottom: 1.5rem;
}

.otp-digit {
  width: 3.5rem;
  height: 3.5rem;
  text-align: center;
  font-size: 1.75rem;
  font-weight: 700;
  border: 2px solid #374151;
  border-radius: 12px;
  background: white;
  color: #1a202c;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.otp-digit:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 4px rgba(102, 126, 234, 0.15);
  background: white;
  transform: scale(1.05);
}

.otp-digit:disabled {
  background: #f8fafc;
  opacity: 0.7;
  cursor: not-allowed;
}

.otp-digit:not(:placeholder-shown) {
  border-color: #667eea;
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.05) 0%, rgba(118, 75, 162, 0.05) 100%);
}

.timer-container {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  padding: 0.875rem;
  background: linear-gradient(135deg, rgba(255, 107, 107, 0.1) 0%, rgba(255, 152, 0, 0.1) 100%);
  border-radius: 10px;
  margin-bottom: 1.5rem;
  border: 1px solid rgba(255, 107, 107, 0.2);
}

.timer-icon {
  width: 18px;
  height: 18px;
  color: #ef4444;
  animation: tick 1s ease-in-out infinite;
}

@keyframes tick {
  0%, 100% {
    transform: rotate(0deg);
  }
  25% {
    transform: rotate(-10deg);
  }
  75% {
    transform: rotate(10deg);
  }
}

.timer-text {
  color: #dc2626;
  font-weight: 500;
  font-size: 0.95rem;
}

.timer-text strong {
  font-weight: 700;
  font-size: 1rem;
}

/* Transitions */
.alert-fade-enter-active, .alert-fade-leave-active {
  transition: all 0.3s ease;
}

.alert-fade-enter-from {
  opacity: 0;
  transform: translateY(-10px);
}

.alert-fade-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}

.timer-fade-enter-active, .timer-fade-leave-active {
  transition: all 0.3s ease;
}

.timer-fade-enter-from {
  opacity: 0;
  transform: scale(0.95);
}

.timer-fade-leave-to {
  opacity: 0;
  transform: scale(0.95);
}

.btn {
  padding: 0.875rem 1.75rem;
  border: none;
  border-radius: 12px;
  font-weight: 600;
  font-size: 1rem;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  text-decoration: none;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  text-align: center;
  position: relative;
  overflow: hidden;
}

.btn::before {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(45deg, transparent, rgba(255, 255, 255, 0.3), transparent);
  transform: translateX(-100%);
  transition: transform 0.6s;
}

.btn:hover::before {
  transform: translateX(100%);
}

.btn-primary {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
}

.btn-primary:hover:not(:disabled) {
  box-shadow: 0 6px 20px rgba(102, 126, 234, 0.5);
  transform: translateY(-2px);
}

.btn-primary:active:not(:disabled) {
  transform: translateY(0);
}

.btn-secondary {
  background: linear-gradient(135deg, #6b7280 0%, #4b5563 100%);
  color: white;
  box-shadow: 0 4px 15px rgba(107, 114, 128, 0.3);
}

.btn-secondary:hover:not(:disabled) {
  box-shadow: 0 6px 20px rgba(107, 114, 128, 0.4);
  transform: translateY(-2px);
}

.btn-full {
  width: 100%;
  padding: 1rem;
  margin-bottom: 1rem;
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none !important;
  box-shadow: none !important;
}

.btn-content {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.625rem;
}

.btn-content svg {
  width: 20px;
  height: 20px;
}

.spinner {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

.spinner-slow {
  animation: spin 2s linear infinite;
}

.back-to-login {
  text-align: center;
  margin-bottom: 2rem;
}

.btn-link {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  background: none;
  border: none;
  color: #667eea;
  cursor: pointer;
  font-size: 0.95rem;
  font-weight: 600;
  padding: 0.75rem 1rem;
  border-radius: 8px;
  transition: all 0.3s ease;
}

.btn-link svg {
  width: 18px;
  height: 18px;
  transition: transform 0.3s ease;
}

.btn-link:hover {
  background: rgba(102, 126, 234, 0.1);
  color: #5568d3;
}

.btn-link:hover svg {
  transform: translateX(-4px);
}


.alert {
  display: flex;
  align-items: center;
  gap: 0.875rem;
  padding: 1rem 1.25rem;
  border-radius: 12px;
  margin-bottom: 1.5rem;
  font-weight: 500;
  font-size: 0.95rem;
  animation: slideDown 0.3s ease-out;
}

@keyframes slideDown {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.alert-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  flex-shrink: 0;
  font-weight: 700;
  font-size: 0.875rem;
}

.alert-success {
  background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%);
  color: #155724;
  border: 1px solid #c3e6cb;
}

.alert-success .alert-icon {
  background: #28a745;
  color: white;
}

.alert-error {
  background: linear-gradient(135deg, #f8d7da 0%, #f5c6cb 100%);
  color: #721c24;
  border: 1px solid #f5c6cb;
}

.alert-error .alert-icon {
  background: #dc3545;
  color: white;
}

.alert-info {
  background: linear-gradient(135deg, #d1ecf1 0%, #bee5eb 100%);
  color: #0c5460;
  border: 1px solid #bee5eb;
}

.alert-info .alert-icon {
  background: #17a2b8;
  color: white;
}

/* Responsive Design */
@media (max-width: 1024px) {
  .otp-container {
    flex-direction: column;
  }
  
  .left-panel {
    flex: 0 0 auto;
    min-height: 40vh;
    padding: 2rem;
  }
  
  .right-panel {
    flex: 1;
    padding: 2rem;
  }
  
  .encryption-card {
    padding: 1.25rem;
  }
  
  .encryption-content {
    gap: 0.5rem;
  }
  
  .product-info h1 {
    font-size: 2rem;
  }
}

@media (max-width: 768px) {
  .left-panel {
    padding: 1.5rem;
  }
  
  .product-info h1 {
    font-size: 1.75rem;
  }
  
  .product-info p {
    font-size: 0.95rem;
  }
  
  .right-panel {
    padding: 1rem;
  }
  
  .otp-card {
    padding: 2rem;
  }
  
  .feature-cards {
    gap: 0.75rem;
    flex-direction: column;
  }
  
  .feature-card {
    padding: 1rem;
    flex: none;
  }
}

@media (max-width: 640px) {
  .left-panel {
    padding: 1rem;
    min-height: 30vh;
  }
  
  .product-info h1 {
    font-size: 1.5rem;
  }
  
  .product-info p {
    font-size: 0.9rem;
  }
  
  .encryption-card {
    display: none;
  }
  
  
  .otp-card {
    padding: 1.5rem;
    border-radius: 20px;
  }
  
  .otp-header h1 {
    font-size: 1.75rem;
  }
  
  .otp-input-container {
    gap: 0.5rem;
  }
  
  .otp-digit {
    width: 2.75rem;
    height: 2.75rem;
    font-size: 1.5rem;
  }
}

@media (max-width: 480px) {
  .otp-card {
    padding: 1.25rem;
  }
  
  .otp-header h1 {
    font-size: 1.5rem;
  }
  
  .otp-header p {
    font-size: 0.9rem;
  }
  
  .otp-input-container {
    gap: 0.4rem;
  }
  
  .otp-digit {
    width: 2.5rem;
    height: 2.5rem;
    font-size: 1.35rem;
  }
  
}

/* Print styles */
@media print {
  .otp-container {
    background: white;
  }
  
  .left-panel {
    display: none;
  }
  
  .background-decoration {
    display: none;
  }
}
</style>

