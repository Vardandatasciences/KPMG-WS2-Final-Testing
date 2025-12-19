<template>
  <div class="login-page">
    <!-- Background Elements -->
    <div class="background-overlay"></div>
    <div class="background-shapes">
      <div class="shape shape-1"></div>
      <div class="shape shape-2"></div>
      <div class="shape shape-3"></div>
    </div>
    
    <!-- Main Content -->
    <div class="login-content">
      <!-- Left Section - Branding -->
      <div class="branding-section">
        <div class="branding-content">
          <div class="logo-section">
            <div>
              <img :src="logo" alt="RiskaVaire Logo" class="logo-image" />
            </div>
          </div>
          
          <div class="hero-content">
            <h2 class="hero-title">Advanced Governance, Risk & Compliance</h2>
            <p class="hero-description">
              Empower your organization with cutting-edge governance, risk management, and compliance tools designed for the modern enterprise. Our comprehensive platform delivers unparalleled control, real-time visibility, and AI-powered automation—aligning IT with business objectives and helping you stay ahead of regulatory change.
            </p>
            
            <div class="features-list">
              <div class="feature-item">
                <div class="feature-icon">
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" stroke="currentColor" stroke-width="2"/>
                    <path d="m9 12 2 2 4-4" stroke="currentColor" stroke-width="2"/>
                  </svg>
                  <div class="feature-tick">
                    <svg width="8" height="8" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <path d="m9 12 2 2 4-4" stroke="currentColor" stroke-width="3"/>
                    </svg>
                  </div>
                </div>
                <div class="feature-content">
                  <span>Enterprise-grade security with multi-layer protection</span>
                </div>
              </div>
              
              <div class="feature-item">
                <div class="feature-icon">
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" stroke="currentColor" stroke-width="2"/>
                    <polyline points="14 2 14 8 20 8" stroke="currentColor" stroke-width="2"/>
                    <line x1="16" y1="13" x2="8" y2="13" stroke="currentColor" stroke-width="2"/>
                    <path d="m9 16 2 2 4-4" stroke="currentColor" stroke-width="2"/>
                  </svg>
                  <div class="feature-tick">
                    <svg width="8" height="8" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <path d="m9 12 2 2 4-4" stroke="currentColor" stroke-width="3"/>
                    </svg>
                  </div>
                </div>
                <div class="feature-content">
                  <span>Automated compliance reporting and real-time monitoring</span>
                </div>
              </div>
              
              <div class="feature-item">
                <div class="feature-icon">
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <line x1="18" y1="20" x2="18" y2="10" stroke="currentColor" stroke-width="2"/>
                    <line x1="12" y1="20" x2="12" y2="4" stroke="currentColor" stroke-width="2"/>
                    <line x1="6" y1="20" x2="6" y2="14" stroke="currentColor" stroke-width="2"/>
                    <circle cx="18" cy="8" r="2" stroke="currentColor" stroke-width="2"/>
                    <circle cx="12" cy="2" r="2" stroke="currentColor" stroke-width="2"/>
                    <circle cx="6" cy="12" r="2" stroke="currentColor" stroke-width="2"/>
                  </svg>
                  <div class="feature-tick">
                    <svg width="8" height="8" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <path d="m9 12 2 2 4-4" stroke="currentColor" stroke-width="3"/>
                    </svg>
                  </div>
                </div>
                <div class="feature-content">
                  <span>Advanced risk analytics with predictive insights</span>
                </div>
              </div>
            </div>
          </div>
          
          <div class="trust-badges">
            <div class="badge">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <rect x="3" y="11" width="18" height="11" rx="2" ry="2" stroke="currentColor" stroke-width="2"/>
                <circle cx="12" cy="16" r="1" stroke="currentColor" stroke-width="2"/>
                <path d="m8 16 2-2 4 2" stroke="currentColor" stroke-width="2"/>
              </svg>
              <span>AES-256 Encryption</span>
            </div>
            <div class="badge">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
                <polyline points="12 6 12 12 16 14" stroke="currentColor" stroke-width="2"/>
                <circle cx="18" cy="6" r="2" fill="currentColor"/>
              </svg>
              <span>24/7 Monitoring</span>
            </div>
          </div>
        </div>
      </div>
      
      <!-- Right Section - Login Form -->
      <div class="form-section">
        <div class="form-container">
          <div class="form-header">
            <h3>
              
              Welcome Back
            </h3>
            <p>Sign in to your GRC dashboard</p>
          </div>
          
          <!-- MFA Step (only shown if MFA is enabled) -->
          <div v-if="MFA_ENABLED && showMfaStep" class="mfa-step">
            <div class="mfa-header">
              <h3>Verify Your Identity</h3>
              <p>Enter the 6-digit code sent to your email</p>
            </div>
            
            <!-- Email Display Box -->
            <div class="mfa-email-box">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" class="email-icon">
                <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z" stroke="currentColor" stroke-width="2"/>
                <polyline points="22,6 12,13 2,6" stroke="currentColor" stroke-width="2"/>
              </svg>
              <span>{{ emailMasked }}</span>
            </div>
            
            <form @submit.prevent="verifyOtp" class="mfa-form">
              <!-- 6 Individual OTP Input Boxes -->
              <div class="otp-input-container">
                <label class="otp-label">Verification Code</label>
                <div class="otp-boxes">
                  <input
                    v-for="(digit, index) in otpDigits"
                    :key="index"
                    :ref="el => { if (el) otpInputRefs[index] = el }"
                    type="text"
                    v-model="otpDigits[index]"
                    @input="handleOtpInput(index, $event)"
                    @keydown="handleOtpKeydown(index, $event)"
                    @paste="handleOtpPaste($event)"
                    maxlength="1"
                    pattern="[0-9]"
                    inputmode="numeric"
                    class="otp-box"
                    :class="{ 'filled': otpDigits[index] }"
                  >
                </div>
              </div>
              
              <!-- Timer Display -->
              <div class="mfa-timer">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" class="timer-icon">
                  <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
                  <polyline points="12 6 12 12 16 14" stroke="currentColor" stroke-width="2"/>
                </svg>
                <span>Code expires in {{ formattedTimer }}</span>
              </div>
              
              <!-- Verify Button -->
              <button type="submit" class="mfa-verify-button" :disabled="isLoading || !isOtpComplete">
                <svg v-if="!isLoading" width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" class="verify-icon">
                  <path d="m9 12 2 2 4-4" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                  <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
                </svg>
                <span v-if="!isLoading">Verify Code</span>
                <span v-else class="loading-content">
                  <div class="spinner-small"></div>
                  <span>Verifying</span>
                </span>
              </button>
              
              <!-- Resend Button -->
              <button type="button" @click="resendOtp" class="mfa-resend-button" :disabled="isResendingOtp || resendCooldown > 0">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" class="resend-icon">
                  <line x1="22" y1="4" x2="22" y2="10" stroke="currentColor" stroke-width="2"/>
                  <line x1="18" y1="6" x2="22" y2="2" stroke="currentColor" stroke-width="2"/>
                  <path d="M19 11a8 8 0 0 1-8 8 8 8 0 0 1-8-8 8 8 0 0 1 8-8" stroke="currentColor" stroke-width="2"/>
                </svg>
                <span v-if="isResendingOtp">Sending...</span>
                <span v-else-if="resendCooldown > 0">Resend Code ({{ resendCooldown }}s)</span>
                <span v-else>Resend Code</span>
              </button>
              
              <!-- Back to Login Link -->
              <button type="button" @click="backToLogin" class="mfa-back-link">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" class="back-icon">
                  <polyline points="15 18 9 12 15 6" stroke="currentColor" stroke-width="2"/>
                </svg>
                <span>Back to Login</span>
              </button>
              
              <!-- Error Message -->
              <div v-if="errorMessage" class="mfa-error-alert">
                <button class="error-close" @click="errorMessage = ''" type="button">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <line x1="18" y1="6" x2="6" y2="18" stroke="currentColor" stroke-width="2"/>
                    <line x1="6" y1="6" x2="18" y2="18" stroke="currentColor" stroke-width="2"/>
                  </svg>
                </button>
                <span>{{ errorMessage }}</span>
              </div>
            </form>
          </div>
          
          <!-- Login Form -->
          <form v-else @submit.prevent="login" class="login-form">
            <!-- Login Type Selector -->
            <div class="login-type-selector">
              <!-- Username Option -->
              <div class="radio-wrapper" :class="{ checked: loginType === 'username' }" @click="loginType = 'username'">
                <input type="radio" v-model="loginType" value="username" name="loginType" style="display: none;">
                <span class="radio-mark">
                  <svg v-if="loginType === 'username'" width="8" height="8" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <circle cx="12" cy="12" r="4" fill="currentColor"/>
                  </svg>
                </span>
                <span class="radio-text">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" stroke="currentColor" stroke-width="2"/>
                    <circle cx="12" cy="7" r="4" stroke="currentColor" stroke-width="2"/>
                  </svg>
                  Username
                </span>
              </div>
              
              <!-- User ID Option -->
              <div class="radio-wrapper" :class="{ checked: loginType === 'userid' }" @click="loginType = 'userid'">
                <input type="radio" v-model="loginType" value="userid" name="loginType" style="display: none;">
                <span class="radio-mark">
                  <svg v-if="loginType === 'userid'" width="8" height="8" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <circle cx="12" cy="12" r="4" fill="currentColor"/>
                  </svg>
                </span>
                <span class="radio-text">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2" stroke="currentColor" stroke-width="2"/>
                    <rect x="8" y="2" width="8" height="4" rx="1" ry="1" stroke="currentColor" stroke-width="2"/>
                    <path d="M9 14h6M9 18h6" stroke="currentColor" stroke-width="2"/>
                  </svg>
                  User ID
                </span>
              </div>
            </div>
            
            <div class="input-group" :class="{ success: loginIdentifier && loginIdentifier.length > 0 }">
              <label for="loginIdentifier">
                {{ loginType === 'username' ? 'Username' : 'User ID' }}
              </label>
              <div class="input-wrapper" :class="{ success: loginIdentifier && loginIdentifier.length > 0 }">
                <div class="input-icon">
                  <svg v-if="loginType === 'username'" width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" stroke="currentColor" stroke-width="2"/>
                    <circle cx="12" cy="7" r="4" stroke="currentColor" stroke-width="2"/>
                  </svg>
                  <svg v-else width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2" stroke="currentColor" stroke-width="2"/>
                    <rect x="8" y="2" width="8" height="4" rx="1" ry="1" stroke="currentColor" stroke-width="2"/>
                    <path d="M9 14h6M9 18h6" stroke="currentColor" stroke-width="2"/>
                  </svg>
                </div>
                <input 
                  type="text" 
                  id="loginIdentifier" 
                  v-model="loginIdentifier" 
                  :placeholder="loginType === 'username' ? 'Enter your username' : 'Enter your user ID'"
                  required
                  :autocomplete="loginType === 'username' ? 'username' : 'off'"
                  :class="{ 'has-success': loginIdentifier && loginIdentifier.length > 0 }"
                >
                <div v-if="loginIdentifier && loginIdentifier.length > 0" class="input-success-icon">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="m9 12 2 2 4-4" stroke="currentColor" stroke-width="2"/>
                  </svg>
                </div>
              </div>
            </div>
            
            <div class="input-group" :class="{ success: password && password.length > 0 }">
              <label for="password">
                Password
              </label>
              <div class="input-wrapper" :class="{ success: password && password.length > 0 }">
                <div class="input-icon">
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <rect x="3" y="11" width="18" height="11" rx="2" ry="2" stroke="currentColor" stroke-width="2"/>
                    <circle cx="12" cy="16" r="1" stroke="currentColor" stroke-width="2"/>
                    <path d="M7 11V7a5 5 0 0 1 10 0v4" stroke="currentColor" stroke-width="2"/>
                  </svg>
                </div>
                <input 
                  :type="passwordFieldType" 
                  id="password" 
                  v-model="password" 
                  placeholder="Enter your password"
                  required
                  autocomplete="current-password"
                  :class="{ 'has-success': password && password.length > 0 }"
                >
                <div v-if="password && password.length > 0" class="input-success-icon">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="m9 12 2 2 4-4" stroke="currentColor" stroke-width="2"/>
                  </svg>
                </div>
                <button 
                  type="button"
                  @click="togglePasswordVisibility" 
                  class="password-toggle"
                  tabindex="-1"
                  :title="passwordFieldType === 'password' ? 'Show password' : 'Hide password'"
                >
                  <svg v-if="passwordFieldType === 'password'" width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" stroke="currentColor" stroke-width="2"/>
                    <circle cx="12" cy="12" r="3" stroke="currentColor" stroke-width="2"/>
                  </svg>
                  <svg v-else width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24" stroke="currentColor" stroke-width="2"/>
                    <line x1="1" y1="1" x2="23" y2="23" stroke="currentColor" stroke-width="2"/>
                  </svg>
                </button>
              </div>
            </div>
            
            <div class="form-options">
              <div class="form-options-row">
                <button type="button" @click="showForgotPasswordModal = true" class="forgot-password">
                  Forgot password ?
                </button>
              </div>
            </div>
            
            <!-- reCAPTCHA -->
            <div class="captcha-container">
              <div ref="captchaRef" id="recaptcha-container"></div>
            </div>
            
            <button type="submit" class="login-button" :disabled="isLoading || !isCaptchaVerified" :class="{ active: !isLoading && isCaptchaVerified, loading: isLoading }">
              <span v-if="!isLoading" class="button-text">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4M10 17l5-5-5-5M15 12H3" stroke="currentColor" stroke-width="2"/>
                </svg>
                Sign In to Dashboard
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="m9 18 6-6-6-6" stroke="currentColor" stroke-width="2"/>
                </svg>
              </span>
              <span v-else class="loading-content">
                <div class="spinner">
                  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2" opacity="0.25"/>
                    <path d="M12 2a10 10 0 0 1 10 10" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                  </svg>
                </div>
                <span>Signing you in</span>
                <span class="loading-dots"></span>
              </span>
            </button>
            
            <!-- Google SSO Button -->
            <div class="google-sso-section">
              <div class="divider">
                <span>or</span>
              </div>
              <button 
                type="button" 
                @click="loginWithGoogle" 
                class="google-sso-button" 
                :disabled="isLoading"
              >
                <svg width="18" height="18" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                  <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/>
                  <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
                  <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05"/>
                  <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/>
                </svg>
                <span>Sign in with Google</span>
              </button>
            </div>
            
            <div v-if="errorMessage" class="error-alert">
              <button class="error-close" @click="errorMessage = ''" type="button">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <line x1="18" y1="6" x2="6" y2="18" stroke="currentColor" stroke-width="2"/>
                  <line x1="6" y1="6" x2="18" y2="18" stroke="currentColor" stroke-width="2"/>
                </svg>
              </button>
              <span>{{ errorMessage }}</span>
            </div>
          </form>
            
          <!-- License Verification Notice -->
          <div class="license-notice">
            <div class="notice-icon">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" stroke="currentColor" stroke-width="2"/>
                <path d="m9 12 2 2 4-4" stroke="currentColor" stroke-width="2"/>
              </svg>
            </div>
            <span>License verification will be performed during login</span>
          </div>

          <!-- Contact Section -->
          <div class="contact-section">
            <div class="contact-header">
              <h4>CONTACT US</h4>
            </div>
            <div class="contact-info">
              <div class="contact-item">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z" stroke="currentColor" stroke-width="2"/>
                  <polyline points="22,6 12,13 2,6" stroke="currentColor" stroke-width="2"/>
                </svg>
                <a href="mailto:info@vardaanglobal.com">info@vardaanglobal.com</a>
              </div>
              <div class="contact-item">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71" stroke="currentColor" stroke-width="2"/>
                  <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71" stroke="currentColor" stroke-width="2"/>
                </svg>
                <a href="https://vardaanglobal.com/grc" target="_blank" rel="noopener noreferrer">vardaanglobal.com/grc</a>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- Forgot Password Modal -->
    <ForgotPassword 
      :showModal="showForgotPasswordModal" 
      :username="loginIdentifier"
      @close="showForgotPasswordModal = false" 
    />
    
    <!-- Consent Form Modal -->
    <ConsentForm 
      :showConsent="showConsentForm"
      @consent-accepted="handleConsentAccepted"
      @consent-declined="handleConsentDeclined"
    />
  </div>
</template>

<script setup>
import { ref, computed, onUnmounted, onMounted, nextTick, watch } from 'vue'
import { useRouter } from 'vue-router'
import authService from '../../services/authService.js'
import ForgotPassword from './ForgotPassword.vue'
import ConsentForm from './ConsentForm.vue'
import logo from '../../assets/RiskaVaire.png'
import { RECAPTCHA_SITE_KEY, MFA_ENABLED } from '../../config/api.js'

const password = ref('')
const rememberMe = ref(false)
const errorMessage = ref('')
const isLoading = ref(false)
const router = useRouter()
const passwordFieldType = ref('password')
const loginType = ref('username') // 'username' or 'userid'
const loginIdentifier = ref('') // username or user_id
const showForgotPasswordModal = ref(false)
const showConsentForm = ref(false)
const showMfaStep = ref(false)
const otp = ref('')
const otpDigits = ref(['', '', '', '', '', ''])
const otpInputRefs = ref([])
const emailMasked = ref('')
const isResendingOtp = ref(false)
const timer = ref(600) // 10 minutes in seconds
const timerInterval = ref(null)
const resendCooldown = ref(0) // Cooldown for resend button (30 seconds)
const resendCooldownInterval = ref(null)
const captchaRef = ref(null)
const isCaptchaVerified = ref(false)
const captchaToken = ref('')
let captchaWidgetId = null

const loginWithGoogle = async () => {
  try {
    isLoading.value = true
    errorMessage.value = ''
    
    // Initiate Google OAuth flow
    await authService.initiateGoogleOAuth()
  } catch (error) {
    isLoading.value = false
    if (error.response && error.response.data) {
      errorMessage.value = error.response.data.message || 'Google SSO login failed. Please try again.'
    } else {
      errorMessage.value = error.message || 'Unable to connect to Google. Please check your connection.'
    }
    console.error('❌ Google SSO login error:', error)
  }
}

const login = async () => {
  try {
    isLoading.value = true
    errorMessage.value = ''
    
    if (!loginIdentifier.value || !password.value) {
      errorMessage.value = 'Please fill in all required fields'
      isLoading.value = false
      return
    }
    
    // Verify CAPTCHA before proceeding
    if (!isCaptchaVerified.value || !captchaToken.value) {
      errorMessage.value = 'Please complete the CAPTCHA verification'
      isLoading.value = false
      return
    }
    
    // Clear any existing data (but preserve cookie preferences)
    const cookieSessionId = localStorage.getItem('cookie_session_id')
    const cookiePreferencesSaved = localStorage.getItem('cookie_preferences_saved')
    const cookiePreferences = localStorage.getItem('cookie_preferences')
    
    localStorage.clear()
    
    // Restore cookie preferences after clearing
    if (cookieSessionId) localStorage.setItem('cookie_session_id', cookieSessionId)
    if (cookiePreferencesSaved) localStorage.setItem('cookie_preferences_saved', cookiePreferencesSaved)
    if (cookiePreferences) localStorage.setItem('cookie_preferences', cookiePreferences)
    
    // Use JWT authentication with CAPTCHA token
    const result = await authService.login(
      loginIdentifier.value, 
      password.value, 
      loginType.value,
      captchaToken.value
    )
    
    // Handle MFA required (only if MFA is enabled)
    if (MFA_ENABLED && result.requiresMfa) {
      showMfaStep.value = true
      emailMasked.value = result.emailMasked || 'your email'
      errorMessage.value = ''
      otpDigits.value = ['', '', '', '', '', '']
      otp.value = ''
      startTimer()
      startResendCooldown() // Start cooldown for resend button
      // Focus first OTP input
      nextTick(() => {
        if (otpInputRefs.value[0]) {
          otpInputRefs.value[0].focus()
        }
      })
      return
    }
    
    if (result.success) {
      if (rememberMe.value) {
        localStorage.setItem('remember_me', 'true')
      }
      
      // Reset CAPTCHA after successful login
      resetCaptcha()
      
      console.log('🔐 JWT Login successful!', {
        user_id: result.user.UserId,
        email: result.user.Email,
        username: result.user.UserName,
        consent_required: result.user.consent_accepted !== '1'
      })
      
      // Check if consent is required (if user hasn't accepted consent yet)
      if (result.user.consent_accepted !== '1') {
        console.log('📋 Consent required - showing consent form')
        showConsentForm.value = true
      } else {
        console.log('✅ Consent already accepted - proceeding to home')
        // Call the global login success handler
        if (window.onSuccessfulLogin) {
          window.onSuccessfulLogin()
        }
        window.dispatchEvent(new Event('authChanged'))
        router.push('/home')
      }
    } else {
      errorMessage.value = 'Login failed. Please try again.'
      // Reset CAPTCHA on login failure
      resetCaptcha()
    }
  } catch (error) {
    console.error('❌ JWT Login error:', error)
    
    // Handle different error types with specific messages
    if (error.message) {
      if (error.message.includes('connect to the server') || error.message.includes('CONNECTION_REFUSED') || error.code === 'ECONNREFUSED') {
        errorMessage.value = 'Unable to connect to the server. Please ensure the backend server is running on port 8000.'
      } else if (error.message.includes('timeout') || error.message.includes('Timeout') || error.code === 'ECONNABORTED') {
        errorMessage.value = 'Request timed out. The server may be slow or unavailable. Please try again.'
      } else if (error.message.includes('CAPTCHA')) {
        errorMessage.value = error.message
      } else if (error.response && error.response.data) {
        errorMessage.value = error.response.data.message || 'Invalid credentials. Please try again.'
      } else {
        errorMessage.value = error.message || 'Unable to connect to server. Please check your connection.'
      }
    } else {
      errorMessage.value = 'An unexpected error occurred. Please try again.'
    }
    
    // Reset CAPTCHA on error
    resetCaptcha()
  } finally {
    isLoading.value = false
  }
}

const handleConsentAccepted = () => {
  console.log('✅ Consent accepted - proceeding to home')
  showConsentForm.value = false
  // Call the global login success handler
  if (window.onSuccessfulLogin) {
    window.onSuccessfulLogin()
  }
  window.dispatchEvent(new Event('authChanged'))
  router.push('/home')
}

const handleConsentDeclined = () => {
  console.log('❌ Consent declined - logging out')
  showConsentForm.value = false
  // Clear authentication data and stay on login page
  authService.clearAuthData()
  errorMessage.value = 'You must accept the terms and conditions to use the system.'
}

const verifyOtp = async () => {
  try {
    isLoading.value = true
    errorMessage.value = ''
    
    // Combine OTP digits
    otp.value = otpDigits.value.join('')
    
    if (!isOtpComplete.value) {
      errorMessage.value = 'Please enter a valid 6-digit verification code'
      isLoading.value = false
      return
    }
    
    const result = await authService.verifyMfaOtp(
      loginIdentifier.value,
      password.value,
      otp.value,
      loginType.value
    )
    
    if (result.success) {
      if (rememberMe.value) {
        localStorage.setItem('remember_me', 'true')
      }
      
      console.log('🔐 MFA Login successful!', {
        user_id: result.user.UserId,
        email: result.user.Email,
        username: result.user.UserName,
        consent_required: result.user.consent_accepted !== '1'
      })
      
      // Stop timer on successful verification
      stopTimer()
      
      // Check if consent is required
      if (result.user.consent_accepted !== '1') {
        console.log('📋 Consent required - showing consent form')
        showConsentForm.value = true
        showMfaStep.value = false
      } else {
        console.log('✅ Consent already accepted - proceeding to home')
        showMfaStep.value = false
        if (window.onSuccessfulLogin) {
          window.onSuccessfulLogin()
        }
        window.dispatchEvent(new Event('authChanged'))
        router.push('/home')
      }
    } else {
      errorMessage.value = 'Invalid verification code. Please try again.'
    }
  } catch (error) {
    console.error('❌ MFA OTP verification error:', error)
    
    // Handle different error types with specific messages
    if (error.message) {
      if (error.message.includes('connect to the server') || error.message.includes('CONNECTION_REFUSED') || error.code === 'ECONNREFUSED') {
        errorMessage.value = 'Unable to connect to the server. Please ensure the backend server is running.'
      } else if (error.message.includes('timeout') || error.message.includes('Timeout') || error.code === 'ECONNABORTED') {
        errorMessage.value = 'Request timed out. Please try again.'
      } else {
        errorMessage.value = error.message
      }
    } else {
      errorMessage.value = 'Verification failed. Please try again.'
    }
  } finally {
    isLoading.value = false
  }
}

const resendOtp = async () => {
  try {
    isResendingOtp.value = true
    errorMessage.value = ''
    
    const result = await authService.resendMfaOtp(
      loginIdentifier.value,
      password.value,
      loginType.value
    )
    
    if (result.success) {
      emailMasked.value = result.emailMasked || emailMasked.value
      // Reset OTP inputs
      otpDigits.value = ['', '', '', '', '', '']
      otp.value = ''
      // Restart timer
      startTimer()
      // Restart resend cooldown
      startResendCooldown()
      // Focus first input
      nextTick(() => {
        if (otpInputRefs.value[0]) {
          otpInputRefs.value[0].focus()
        }
      })
      errorMessage.value = ''
      // Show success message temporarily
      const successMsg = 'New verification code sent!'
      errorMessage.value = successMsg
      setTimeout(() => {
        if (errorMessage.value === successMsg) {
          errorMessage.value = ''
        }
      }, 3000)
    } else {
      errorMessage.value = result.message || 'Failed to resend code. Please try again.'
    }
  } catch (error) {
    if (error.message) {
      errorMessage.value = error.message
    } else {
      errorMessage.value = 'Failed to resend code. Please try again.'
    }
    console.error('❌ Resend OTP error:', error)
  } finally {
    isResendingOtp.value = false
  }
}

// Computed properties for MFA
const isOtpComplete = computed(() => {
  return otpDigits.value.every(digit => digit !== '') && otpDigits.value.join('').length === 6
})

const formattedTimer = computed(() => {
  const minutes = Math.floor(timer.value / 60)
  const seconds = timer.value % 60
  return `${minutes}:${seconds.toString().padStart(2, '0')}`
})

// OTP Input Handlers
const handleOtpInput = (index, event) => {
  const value = event.target.value.replace(/[^0-9]/g, '')
  if (value) {
    otpDigits.value[index] = value
    otp.value = otpDigits.value.join('')
    
    // Auto-focus next input
    if (index < 5 && value) {
      nextTick(() => {
        if (otpInputRefs.value[index + 1]) {
          otpInputRefs.value[index + 1].focus()
        }
      })
    }
  } else {
    otpDigits.value[index] = ''
    otp.value = otpDigits.value.join('')
  }
}

const handleOtpKeydown = (index, event) => {
  // Handle backspace
  if (event.key === 'Backspace' && !otpDigits.value[index] && index > 0) {
    nextTick(() => {
      if (otpInputRefs.value[index - 1]) {
        otpInputRefs.value[index - 1].focus()
      }
    })
  }
  
  // Handle arrow keys
  if (event.key === 'ArrowLeft' && index > 0) {
    event.preventDefault()
    if (otpInputRefs.value[index - 1]) {
      otpInputRefs.value[index - 1].focus()
    }
  }
  if (event.key === 'ArrowRight' && index < 5) {
    event.preventDefault()
    if (otpInputRefs.value[index + 1]) {
      otpInputRefs.value[index + 1].focus()
    }
  }
}

const handleOtpPaste = (event) => {
  event.preventDefault()
  const pastedData = event.clipboardData.getData('text').replace(/[^0-9]/g, '').slice(0, 6)
  
  if (pastedData.length > 0) {
    for (let i = 0; i < 6; i++) {
      otpDigits.value[i] = pastedData[i] || ''
    }
    otp.value = otpDigits.value.join('')
    
    // Focus the last filled input or the last input
    const lastIndex = Math.min(pastedData.length - 1, 5)
    nextTick(() => {
      if (otpInputRefs.value[lastIndex]) {
        otpInputRefs.value[lastIndex].focus()
      }
    })
  }
}

// Timer functions
const startTimer = () => {
  timer.value = 600 // 10 minutes
  if (timerInterval.value) {
    clearInterval(timerInterval.value)
  }
  timerInterval.value = setInterval(() => {
    if (timer.value > 0) {
      timer.value--
    } else {
      clearInterval(timerInterval.value)
    }
  }, 1000)
}

const stopTimer = () => {
  if (timerInterval.value) {
    clearInterval(timerInterval.value)
    timerInterval.value = null
  }
}

// Resend cooldown functions
const startResendCooldown = () => {
  resendCooldown.value = 30 // 30 seconds cooldown
  if (resendCooldownInterval.value) {
    clearInterval(resendCooldownInterval.value)
  }
  resendCooldownInterval.value = setInterval(() => {
    if (resendCooldown.value > 0) {
      resendCooldown.value--
    } else {
      clearInterval(resendCooldownInterval.value)
      resendCooldownInterval.value = null
    }
  }, 1000)
}

const stopResendCooldown = () => {
  if (resendCooldownInterval.value) {
    clearInterval(resendCooldownInterval.value)
    resendCooldownInterval.value = null
  }
  resendCooldown.value = 0
}

const backToLogin = () => {
  showMfaStep.value = false
  otp.value = ''
  otpDigits.value = ['', '', '', '', '', '']
  errorMessage.value = ''
  stopTimer()
  stopResendCooldown()
  timer.value = 600
  resendCooldown.value = 0
}

// Cleanup on unmount
onUnmounted(() => {
  stopTimer()
  stopResendCooldown()
})

const togglePasswordVisibility = () => {
  passwordFieldType.value = passwordFieldType.value === 'password' ? 'text' : 'password'
}

// CAPTCHA Functions
const loadRecaptcha = () => {
  // Don't load CAPTCHA if we're on MFA step
  if (showMfaStep.value) {
    return
  }
  
  // Check if container exists
  if (!captchaRef.value) {
    return
  }
  
  // Check if script is already loaded
  if (window.grecaptcha && window.grecaptcha.render) {
    nextTick(() => {
      renderCaptcha()
    })
    return
  }
  
  // Check if script is already being loaded
  if (document.querySelector('script[src*="recaptcha/api.js"]')) {
    // Script is loading, wait for it
    const checkInterval = setInterval(() => {
      if (window.grecaptcha && window.grecaptcha.render) {
        clearInterval(checkInterval)
        nextTick(() => {
          renderCaptcha()
        })
      }
    }, 100)
    
    // Timeout after 10 seconds
    setTimeout(() => {
      clearInterval(checkInterval)
    }, 10000)
    return
  }
  
  // Load reCAPTCHA script with error handling and timeout
  const script = document.createElement('script')
  script.src = 'https://www.google.com/recaptcha/api.js?render=explicit&onload=onRecaptchaLoad'
  script.async = true
  script.defer = true
  
  // Add timeout for script loading (30 seconds)
  const loadTimeout = setTimeout(() => {
    console.warn('⚠️ reCAPTCHA script load timeout - allowing bypass in development')
    if (process.env.NODE_ENV === 'development') {
      isCaptchaVerified.value = true // Allow bypass in development
    }
  }, 30000)
  
  // Handle script load errors
  script.onerror = () => {
    clearTimeout(loadTimeout)
    console.warn('⚠️ Failed to load reCAPTCHA script. This may be due to network issues or ad blockers.')
    // Don't block login if CAPTCHA fails to load in development
    if (process.env.NODE_ENV === 'development') {
      isCaptchaVerified.value = true // Allow bypass in development
    }
  }
  
  // Set global callback with timeout handling
  window.onRecaptchaLoad = () => {
    clearTimeout(loadTimeout)
    try {
      nextTick(() => {
        renderCaptcha()
      })
    } catch (error) {
      console.warn('⚠️ Error in reCAPTCHA onload callback:', error)
      // Suppress timeout errors from reCAPTCHA
      if (error.message && !error.message.includes('Timeout')) {
        console.error('reCAPTCHA error:', error)
      }
      if (process.env.NODE_ENV === 'development') {
        isCaptchaVerified.value = true
      }
    }
  }
  
  // Wrap script loading in try-catch to handle any errors
  try {
    document.head.appendChild(script)
  } catch (error) {
    clearTimeout(loadTimeout)
    console.warn('⚠️ Error appending reCAPTCHA script:', error)
    if (process.env.NODE_ENV === 'development') {
      isCaptchaVerified.value = true
    }
  }
}

const renderCaptcha = () => {
  // Don't render if on MFA step
  if (showMfaStep.value) {
    return
  }
  
  // Check if container exists
  if (!captchaRef.value || !document.getElementById('recaptcha-container')) {
    return
  }
  
  if (!window.grecaptcha || !window.grecaptcha.render) {
    return
  }
  
  try {
    // Clear any existing widget
    if (captchaWidgetId !== null) {
      try {
        window.grecaptcha.reset(captchaWidgetId)
      } catch (e) {
        console.warn('Error resetting CAPTCHA:', e)
      }
    }
    
    // Render new CAPTCHA widget
    captchaWidgetId = window.grecaptcha.render('recaptcha-container', {
      sitekey: RECAPTCHA_SITE_KEY,
      callback: (token) => {
        isCaptchaVerified.value = true
        captchaToken.value = token
        errorMessage.value = ''
      },
      'expired-callback': () => {
        isCaptchaVerified.value = false
        captchaToken.value = ''
      },
      'error-callback': () => {
        isCaptchaVerified.value = false
        captchaToken.value = ''
        errorMessage.value = 'CAPTCHA verification failed. Please try again.'
      }
    })
  } catch (e) {
    console.error('Error rendering CAPTCHA:', e)
    // Don't block login if CAPTCHA fails in development
    if (process.env.NODE_ENV === 'development') {
      isCaptchaVerified.value = true
    }
  }
}

// Watch for login type changes and reset CAPTCHA (only if not on MFA step)
watch(loginType, () => {
  if (!showMfaStep.value) {
    resetCaptcha()
  }
})

const resetCaptcha = () => {
  if (captchaWidgetId !== null && window.grecaptcha) {
    try {
      window.grecaptcha.reset(captchaWidgetId)
      isCaptchaVerified.value = false
      captchaToken.value = ''
    } catch (e) {
      console.warn('Error resetting CAPTCHA:', e)
    }
  }
}

// Check for reset password query parameter on mount
onMounted(() => {
  // Check if we should open forgot password modal from URL query params
  const route = router.currentRoute.value
  if (route.query.resetPassword === 'true' && route.query.email) {
    showForgotPasswordModal.value = true
    // The email will be pre-filled by the ForgotPassword component
  }
  
  nextTick(() => {
    if (!showMfaStep.value) {
      loadRecaptcha()
    }
  })
})

// Watch for MFA step changes to load/unload CAPTCHA
watch(showMfaStep, (newValue) => {
  if (!newValue) {
    // MFA step closed, load CAPTCHA for login form
    nextTick(() => {
      loadRecaptcha()
    })
  } else {
    // MFA step opened, reset CAPTCHA
    resetCaptcha()
  }
})

// Cleanup on unmount
onUnmounted(() => {
  if (captchaWidgetId !== null && window.grecaptcha) {
    try {
      window.grecaptcha.reset(captchaWidgetId)
    } catch (e) {
      // Ignore errors during cleanup
    }
  }
  stopTimer()
  stopResendCooldown()
})
</script>

<style scoped>
@import './login.css?v=2.0';
</style>