<template>
  <div class="login-container">
    <!-- Left Side - Product Information & Charts -->
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
          <h1>Third Party Risk Management Platform</h1>
          <p>Comprehensive TPRM solution integrating RFP management, vendor lifecycle, contract management, SLA monitoring, and business continuity planning. Streamline vendor onboarding, automate risk assessments, ensure compliance, and maintain business resilience with our AI-powered platform.</p>
        </div>
      </div>
      
      <!-- Feature Cards -->
      <div class="feature-cards">
        <div class="feature-card">
          <div class="feature-icon">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M16 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path>
              <circle cx="8.5" cy="7" r="4"></circle>
              <line x1="20" y1="8" x2="20" y2="14"></line>
              <line x1="23" y1="11" x2="17" y2="11"></line>
            </svg>
          </div>
          <div class="feature-content">
            <h3>Complete vendor lifecycle management from onboarding to offboarding</h3>
          </div>
        </div>
        
        <div class="feature-card">
          <div class="feature-icon">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
              <polyline points="14,2 14,8 20,8"></polyline>
              <line x1="16" y1="13" x2="8" y2="13"></line>
              <line x1="16" y1="17" x2="8" y2="17"></line>
              <polyline points="10,9 9,9 8,9"></polyline>
            </svg>
          </div>
          <div class="feature-content">
            <h3>Intelligent RFP management with 9-phase workflow automation</h3>
          </div>
        </div>
        
        <div class="feature-card">
          <div class="feature-icon">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M3 3v18h18"></path>
              <path d="M18.7 8l-5.1 5.2-2.8-2.7L7 14.3"></path>
            </svg>
          </div>
          <div class="feature-content">
            <h3>AI-powered risk analysis with automated contract processing</h3>
          </div>
        </div>
      </div>
      
      <!-- Summary Cards with Chart -->
      <div class="summary-section">
        <div class="summary-card">
          <div class="summary-header">
            <h3>BCP/DRP Framework</h3>
            <div class="trend-indicator positive">
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect>
            <path d="M7 11V7a5 5 0 0 1 10 0v4"></path>
                <path d="M12 11v4"></path>
                <path d="M12 7v.01"></path>
          </svg>
            </div>
          </div>
          <div class="description-text">
            <p>Advanced risk scoring calculations with automated impact assessment, recovery time objectives, and business continuity metrics for comprehensive disaster recovery planning.</p>
        </div>
      </div>
      
        <div class="summary-card">
          <div class="summary-header">
            <h3>Contract Management</h3>
            <div class="score-value">
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                <polyline points="14,2 14,8 20,8"></polyline>
                <line x1="16" y1="13" x2="8" y2="13"></line>
                <line x1="16" y1="17" x2="8" y2="17"></line>
                <polyline points="10,9 9,9 8,9"></polyline>
              </svg>
            </div>
          </div>
          <div class="description-text">
            <p>Intelligent contract comparison engine with automated clause analysis, risk assessment, compliance tracking, and performance benchmarking across vendor agreements.</p>
          </div>
        </div>
      </div>
      
      <!-- Bottom Features -->
      <div class="bottom-features">
        <div class="feature-item">
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect>
            <path d="M7 11V7a5 5 0 0 1 10 0v4"></path>
          </svg>
          <span>ISO 22301 Framework</span>
        </div>
        <div class="feature-item">
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="10"></circle>
            <polyline points="12 6 12 12 16 14"></polyline>
          </svg>
          <span>AES-256 Encryption</span>
        </div>
      </div>
      </div>
      
    <!-- Right Side - Login Form -->
    <div class="right-panel">
      <div class="login-card">
      <div class="login-header">
        <h1>Welcome Back</h1>
          <p>Sign in to your account</p>
      </div>
      
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
      
      <form @submit.prevent="handleLogin" class="login-form">
        <!-- Username Input -->
        <div class="form-group">
          <label for="username">
            <svg class="input-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
              <circle cx="12" cy="7" r="4"></circle>
            </svg>
            Username
          </label>
          <input
            id="username"
            v-model="username"
            type="text"
            class="form-input"
            placeholder="Enter your username"
            :disabled="loading"
            required
            autocomplete="username"
          />
        </div>
        
        <!-- Password Input -->
        <div class="form-group">
          <label for="password">
            <svg class="input-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect>
              <path d="M7 11V7a5 5 0 0 1 10 0v4"></path>
            </svg>
            Password
          </label>
          <div class="password-input-wrapper">
            <input
              id="password"
              v-model="password"
              :type="showPassword ? 'text' : 'password'"
              class="form-input"
              placeholder="Enter your password"
              :disabled="loading"
              required
              autocomplete="current-password"
            />
            <button
              type="button"
              @click="showPassword = !showPassword"
              class="password-toggle"
              :disabled="loading"
              :aria-label="showPassword ? 'Hide password' : 'Show password'"
            >
              <svg v-if="showPassword" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"></path>
                <line x1="1" y1="1" x2="23" y2="23"></line>
              </svg>
              <svg v-else xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path>
                <circle cx="12" cy="12" r="3"></circle>
              </svg>
            </button>
          </div>
        </div>
        
        <!-- Submit Button -->
        <button
          type="submit"
          :disabled="loading || !username || !password"
          class="btn btn-primary btn-full"
        >
          <span v-if="loading" class="btn-content">
            <svg class="spinner" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            Authenticating...
          </span>
          <span v-else class="btn-content">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4"></path>
              <polyline points="10 17 15 12 10 7"></polyline>
              <line x1="15" y1="12" x2="3" y2="12"></line>
            </svg>
            Sign In
          </span>
        </button>
      </form>
      
      <!-- Info Section -->
      <div class="login-info">
        <div class="info-item">
          <svg class="info-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"></path>
            <polyline points="22,6 12,13 2,6"></polyline>
          </svg>
          <span>TPRM reuses your authenticated GRC session</span>
        </div>
        <div class="info-item">
          <svg class="info-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path>
          </svg>
          <span>Security policies match your GRC account posture</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { mapActions, mapGetters } from 'vuex'
import permissionsService from '@/services/permissionsService'

export default {
  name: 'LoginView',
  
  data() {
    return {
      username: '',
      password: '',
      showPassword: false,
      loading: false,
      alert: {
        message: '',
        type: ''
      }
    }
  },
  
  computed: {
    ...mapGetters('auth', ['isAuthenticated', 'currentUser'])
  },
  
  async mounted() {
    // If already authenticated, redirect to home
    if (this.isAuthenticated && this.currentUser) {
      this.showAlert('Already logged in, redirecting...', 'success')
      const targetRoute = await this.getPostLoginRoute()
      setTimeout(() => {
        this.$router.push(targetRoute)
      }, 1000)
    }
  },
  
  methods: {
    ...mapActions('auth', ['login']),

    async getPostLoginRoute() {
      try {
        const hasVendorRegistration = await permissionsService.checkPermission('vendor_create')
        return hasVendorRegistration ? '/vendor-registration' : '/'
      } catch (error) {
        console.error('LoginView: Failed to resolve post-login route', error)
        return '/'
      }
    },
    
    async handleLogin() {
      if (!this.username || !this.password) {
        this.showAlert('Please enter both username and password', 'error')
        return
      }
      
      this.loading = true
      this.clearAlert()
      
      try {
        const result = await this.login({
          username: this.username,
          password: this.password
        })
        
        if (result.success) {
          this.showAlert(result.message || 'Login successful! Redirecting...', 'success')
          const targetRoute = await this.getPostLoginRoute()
          setTimeout(() => {
            this.$router.push(targetRoute)
          }, 1000)
        } else {
          this.showAlert(result.error || 'Login failed. Please check your credentials.', 'error')
        }
      } catch (error) {
        console.error('Login error:', error)
        this.showAlert('An unexpected error occurred. Please try again.', 'error')
      } finally {
        this.loading = false
      }
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
  }
}
</script>

<style scoped>
.login-container {
  min-height: 100vh;
  display: flex;
  background: #f8fafc;
  position: relative;
  overflow: hidden;
}

/* Left Panel - Product Information & Charts */
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
  background: rgba(224, 8, 8, 0.15);
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

/* Summary Section */
.summary-section {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1.5rem;
  margin-bottom: 2rem;
  z-index: 2;
  position: relative;
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
  color: white;
}

.trend-indicator svg {
  width: 20px;
  height: 20px;
  color: white;
}

.score-value {
  color: white;
  font-size: 1.2rem;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
}

.score-value svg {
  width: 24px;
  height: 24px;
  color: white;
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

.description-text {
  margin-top: 1rem;
}

.description-text p {
  color: rgba(255, 255, 255, 0.85);
  font-size: 0.9rem;
  font-weight: 400;
  line-height: 1.5;
  margin: 0;
  text-align: left;
}

/* Bottom Features */
.bottom-features {
  display: flex;
  gap: 2rem;
  z-index: 2;
  position: relative;
}

.feature-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: rgba(255, 255, 255, 0.8);
  font-size: 0.85rem;
  font-weight: 500;
}

.feature-item svg {
  width: 16px;
  height: 16px;
  color: #60a5fa;
}

/* Right Panel - Login Form */
.right-panel {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2rem;
  background: #f8fafc;
}

.login-card {
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

.login-header {
  text-align: center;
  margin-bottom: 2.5rem;
}

.login-header h1 {
  color: #1a202c;
  margin-bottom: 0.5rem;
  font-size: 2rem;
  font-weight: 700;
  letter-spacing: -0.02em;
}

.login-header p {
  color: #718096;
  font-size: 0.95rem;
  font-weight: 500;
}

/* Alert Transitions */
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

/* Form Styles */
.login-form {
  margin-bottom: 2rem;
}

.form-group {
  margin-bottom: 1.75rem;
}

.form-group label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.75rem;
  color: #2d3748;
  font-weight: 600;
  font-size: 0.9rem;
  letter-spacing: 0.01em;
}

.input-icon {
  width: 18px;
  height: 18px;
  color: #667eea;
}

.form-input {
  width: 100%;
  padding: 0.95rem 1.1rem;
  border: 2px solid #374151;
  border-radius: 14px;
  font-size: 1rem;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  background: #f7fafc;
  color: #2d3748;
  font-weight: 500;
}

.form-input::placeholder {
  color: #a0aec0;
  font-weight: 400;
}

.form-input:hover {
  border-color: #4b5563;
  background: #fff;
}

.form-input:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 4px rgba(102, 126, 234, 0.1);
  background: white;
  transform: translateY(-1px);
}

.form-input:disabled {
  background: #edf2f7;
  opacity: 0.6;
  cursor: not-allowed;
}

.password-input-wrapper {
  position: relative;
}

.password-toggle {
  position: absolute;
  right: 1rem;
  top: 50%;
  transform: translateY(-50%);
  background: none;
  border: none;
  cursor: pointer;
  padding: 0.5rem;
  border-radius: 8px;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  justify-content: center;
}

.password-toggle svg {
  width: 20px;
  height: 20px;
  color: #718096;
  transition: color 0.2s ease;
}

.password-toggle:hover:not(:disabled) {
  background: rgba(102, 126, 234, 0.1);
}

.password-toggle:hover:not(:disabled) svg {
  color: #667eea;
}

.password-toggle:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Button Styles */
.btn {
  padding: 0;
  border: none;
  border-radius: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  text-decoration: none;
  display: inline-block;
  text-align: center;
  position: relative;
  overflow: hidden;
}

.btn-primary {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
}

.btn-primary::before {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(135deg, #764ba2 0%, #667eea 100%);
  opacity: 0;
  transition: opacity 0.3s ease;
}

.btn-primary:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(102, 126, 234, 0.5);
}

.btn-primary:hover:not(:disabled)::before {
  opacity: 1;
}

.btn-primary:active:not(:disabled) {
  transform: translateY(0);
  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
}

.btn-full {
  width: 100%;
  font-size: 1.05rem;
  margin-top: 0.5rem;
}

.btn-content {
  position: relative;
  z-index: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.75rem;
  padding: 1rem 1.5rem;
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

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none !important;
  box-shadow: none !important;
}

/* Alert Styles */
.alert {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem 1.25rem;
  border-radius: 14px;
  margin-bottom: 1.5rem;
  font-weight: 500;
  font-size: 0.95rem;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.alert-icon {
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  flex-shrink: 0;
  font-weight: 700;
  font-size: 1rem;
}

.alert-text {
  flex: 1;
}

.alert-success {
  background: linear-gradient(135deg, #d4f8d4 0%, #a7f3d0 100%);
  color: #065f46;
  border: 1px solid #86efac;
}

.alert-success .alert-icon {
  background: #10b981;
  color: white;
}

.alert-error {
  background: linear-gradient(135deg, #fecdd3 0%, #fca5a5 100%);
  color: #991b1b;
  border: 1px solid #fca5a5;
}

.alert-error .alert-icon {
  background: #ef4444;
  color: white;
}

.alert-info {
  background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%);
  color: #1e40af;
  border: 1px solid #93c5fd;
}

.alert-info .alert-icon {
  background: #3b82f6;
  color: white;
}

/* Info Section */
.login-info {
  border-top: 2px solid #e2e8f0;
  padding-top: 2rem;
  margin-top: 1rem;
}

.info-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 1.25rem;
  color: #4a5568;
  font-size: 0.9rem;
  font-weight: 500;
  padding: 0.75rem;
  border-radius: 10px;
  transition: all 0.2s ease;
  flex-direction: row;
  flex-wrap: nowrap;
}

.info-item:hover {
  background: #f7fafc;
  transform: translateX(4px);
}

.info-icon {
  width: 20px;
  height: 20px;
  color: #667eea;
  flex-shrink: 0;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.info-item:last-child {
  margin-bottom: 0;
}

.info-item span {
  display: inline-flex;
  align-items: center;
  white-space: nowrap;
  line-height: 1.2;
}

/* Responsive Design */
@media (max-width: 1024px) {
  .login-container {
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
  
  .summary-section {
    grid-template-columns: 1fr;
    gap: 1rem;
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
  
  .login-card {
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
  
  .summary-section {
    display: none;
  }
  
  .bottom-features {
    display: none;
  }
  
  .login-card {
    padding: 1.5rem;
    border-radius: 20px;
  }
  
  .login-header h1 {
    font-size: 1.75rem;
  }
  
  .login-header p {
    font-size: 0.875rem;
  }
  
  .form-input {
    padding: 0.875rem 1rem;
  }
  
  .btn-content {
    padding: 0.875rem 1.25rem;
    font-size: 0.95rem;
  }
}

@media (max-width: 400px) {
  .login-card {
    padding: 1.25rem;
  }
  
  .login-header h1 {
    font-size: 1.5rem;
  }
  
  .form-group {
    margin-bottom: 1.5rem;
  }
}

/* Print styles */
@media print {
  .login-container {
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
