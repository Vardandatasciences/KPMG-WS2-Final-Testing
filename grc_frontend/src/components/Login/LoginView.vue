<template>
  <main class="login-page">
    <!-- Left branding panel -->
    <aside class="login-brand-panel">
      <div class="brand">
        <div class="brand-logo-wrap">
          <img :src="logo" alt="RiskaVaire Logo" class="brand-logo-img" />
        </div>
      </div>

      <div class="brand-copy">
        <h1>Advanced Governance, Risk &amp; Compliance.</h1>
        <p>
          Empower your organization with governance, risk management, and compliance tools
          designed for the modern enterprise. Stay ahead of regulatory change with real-time
          visibility.
        </p>
      </div>

      <ul class="feature-list">
        <li v-for="item in features" :key="item.label" class="feature-item">
          <div class="feature-icon">
            <component :is="item.icon" :size="14" />
          </div>
          <span>{{ item.label }}</span>
        </li>
      </ul>

      <div class="badges">
        <span class="badge"><Lock :size="14" />&nbsp;AES-256 Encryption</span>
        <span class="badge"><Clock3 :size="14" />&nbsp;24/7 Monitoring</span>
      </div>

      <div class="brand-footer">
        <p class="contact-title">Contact us</p>
        <div class="contact-links">
          <a href="mailto:info@vardaanglobal.com"><Mail :size="14" />&nbsp;info@vardaanglobal.com</a>
          <a href="https://vardaanglobal.com/grc" target="_blank" rel="noopener noreferrer">
            <LinkIcon :size="14" />&nbsp;vardaanglobal.com/grc
          </a>
        </div>
        <p class="copyright">&copy; {{ currentYear }} Vardaan Global. All rights reserved.</p>
      </div>
    </aside>

    <!-- Right form panel -->
    <section class="login-form-panel">
      <div class="login-card">
        <!-- Mobile brand (shown only on small screens) -->
        <div class="mobile-brand">
          <div class="brand-logo-wrap">
            <img :src="logo" alt="RiskaVaire Logo" class="brand-logo-img" />
          </div>
        </div>

        <!-- MFA Step -->
        <div v-if="showMfaPanel" class="mfa-step">
          <div class="card-header">
            <h2>Verify Identity</h2>
            <p>Enter the 6-digit code sent to your email</p>
          </div>

          <div class="mfa-email-box">
            <Mail :size="16" />
            <span>{{ emailMasked }}</span>
          </div>

          <form @submit.prevent="verifyOtp" class="login-form">
            <div class="field-group">
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
                  :class="{ filled: otpDigits[index] }"
                />
              </div>
            </div>

            <div class="mfa-timer">
              <Clock3 :size="14" />
              <span>Code expires in {{ formattedTimer }}</span>
            </div>

            <button type="submit" class="submit-btn" :disabled="isLoading || !isOtpComplete">
              <template v-if="!isLoading">
                <CheckCircle :size="16" />
                Verify Code
              </template>
              <span v-else class="login-loading-content">
                <span class="spinner-small"></span>
                Verifying...
              </span>
            </button>

            <button
              type="button"
              class="google-btn"
              @click="resendOtp"
              :disabled="isResendingOtp || resendCooldown > 0"
            >
              <RotateCcw :size="16" />
              <span v-if="isResendingOtp">Sending...</span>
              <span v-else-if="resendCooldown > 0">Resend Code ({{ resendCooldown }}s)</span>
              <span v-else>Resend Code</span>
            </button>

            <button type="button" @click="backToLogin" class="mfa-back-link">
              <ChevronLeft :size="16" />
              Back to Login
            </button>

            <div v-if="errorMessage" class="error-alert">
              <button class="error-close" @click="errorMessage = ''" type="button">
                <X :size="14" />
              </button>
              <span>{{ errorMessage }}</span>
            </div>
          </form>
        </div>

        <!-- Login Form -->
        <template v-else>
          <div class="card-header">
            <h2>Welcome back</h2>
            <p>Sign in to your GRC dashboard</p>
          </div>

          <div class="mode-tabs" role="tablist" aria-label="Sign-in identifier">
            <button
              v-for="item in identifierModes"
              :key="item.id"
              type="button"
              role="tab"
              :aria-selected="loginType === item.id"
              :class="['mode-tab', { active: loginType === item.id }]"
              @click="loginType = item.id"
            >
              <component :is="item.icon" :size="16" />
              {{ item.label }}
            </button>
          </div>

          <form class="login-form" novalidate @submit.prevent="login">
            <!-- Identifier field -->
            <div class="field-group">
              <label for="loginIdentifier">
                {{ loginType === 'username' ? 'Username' : 'User ID' }} <span>*</span>
              </label>
              <div class="input-wrap">
                <span class="input-icon">
                  <User v-if="loginType === 'username'" :size="16" />
                  <IdCard v-else :size="16" />
                </span>
                <input
                  id="loginIdentifier"
                  v-model="loginIdentifier"
                  type="text"
                  :autocomplete="loginType === 'username' ? 'username' : 'off'"
                  :placeholder="loginType === 'username' ? 'Enter your username' : 'Enter your User ID'"
                  required
                />
              </div>
            </div>

            <!-- Password field -->
            <div class="field-group">
              <label for="password">Password <span>*</span></label>
              <div class="input-wrap">
                <span class="input-icon"><Lock :size="16" /></span>
                <input
                  id="password"
                  v-model="password"
                  :type="passwordFieldType"
                  autocomplete="current-password"
                  placeholder="Enter your password"
                  required
                />
                <button
                  type="button"
                  class="password-toggle-btn"
                  tabindex="-1"
                  @click="togglePasswordVisibility"
                >
                  <Eye v-if="passwordFieldType === 'password'" :size="16" />
                  <EyeOff v-else :size="16" />
                </button>
              </div>
              <div class="forgot-password">
                <button type="button" class="forgot-link" @click="showForgotPasswordModal = true">
                  Forgot password?
                </button>
              </div>
            </div>

            <!-- reCAPTCHA -->
            <div class="captcha-container">
              <div ref="captchaRef" id="recaptcha-container"></div>
            </div>

            <!-- Submit -->
            <button
              class="submit-btn"
              type="submit"
              :disabled="isLoading || !isCaptchaVerified"
            >
              <template v-if="!isLoading">
                <LogIn :size="16" />
                Sign in to Dashboard
              </template>
              <span v-else class="login-loading-content">
                <span class="spinner-small"></span>
                Signing in...
              </span>
            </button>

            <div class="divider"><span>or</span></div>

            <!-- Google SSO -->
            <button type="button" class="google-btn" @click="loginWithGoogle" :disabled="isLoading">
              <svg class="google-icon" viewBox="0 0 24 24" aria-hidden="true">
                <path fill="#4285F4" d="M23.49 12.27c0-.79-.07-1.54-.19-2.27H12v4.51h6.44c-.28 1.48-1.12 2.73-2.39 3.58v2.97h3.86c2.26-2.08 3.58-5.15 3.58-8.79z"/>
                <path fill="#34A853" d="M12 24c3.24 0 5.95-1.08 7.93-2.91l-3.86-2.97c-1.07.72-2.44 1.16-4.07 1.16-3.13 0-5.78-2.11-6.73-4.96H1.29v3.09C3.26 21.3 7.31 24 12 24z"/>
                <path fill="#FBBC05" d="M5.27 14.32c-.25-.72-.38-1.49-.38-2.32s.14-1.6.38-2.32V6.59H1.29C.47 8.24 0 10.06 0 12s.47 3.76 1.29 5.41l3.98-3.09z"/>
                <path fill="#EA4335" d="M12 4.75c1.77 0 3.35.61 4.6 1.8l3.42-3.42C17.95 1.19 15.24 0 12 0 7.31 0 3.26 2.7 1.29 6.59l3.98 3.09C6.22 6.86 8.87 4.75 12 4.75z"/>
              </svg>
              Sign in with Google
            </button>

            <!-- Error message -->
            <div v-if="errorMessage" class="error-alert">
              <button class="error-close" @click="errorMessage = ''" type="button">
                <X :size="14" />
              </button>
              <span>{{ errorMessage }}</span>
            </div>

            <p class="license-note">
              <BadgeCheck :size="14" />
              License verification will be performed during login
            </p>
          </form>
        </template>
      </div>
    </section>

    <!-- Forgot Password Modal -->
    <ForgotPassword
      :showModal="showForgotPasswordModal"
      :username="loginIdentifier"
      @close="showForgotPasswordModal = false"
    />

    <!-- Consent Form Modal -->
    <ConsentForm
      :showConsent="showConsentForm"
      :isVendor="isVendorUser"
      @consent-accepted="handleConsentAccepted"
      @consent-declined="handleConsentDeclined"
    />
  </main>
</template>

<script setup>
import { ref, computed, onUnmounted, onMounted, nextTick, watch } from 'vue'
import { useRouter } from 'vue-router'
import authService from '../../services/authService.js'
import ForgotPassword from './ForgotPassword.vue'
import ConsentForm from './ConsentForm.vue'
import logo from '../../assets/RiskaVaire.png'
import { RECAPTCHA_SITE_KEY, MFA_ENABLED } from '../../config/api.js'
import {
  BadgeCheck,
  CheckCircle,
  ChevronLeft,
  Clock3,
  Eye,
  EyeOff,
  FileCheck2,
  IdCard,
  LineChart,
  Link as LinkIcon,
  Lock,
  LogIn,
  Mail,
  RotateCcw,
  ShieldHalf,
  User,
  X,
} from 'lucide-vue-next'
import './login.css'

/** Lazy-load TPRM role helper so a bundling/alias issue cannot blank the entire login screen */
async function loadRoleRoutingService() {
  const mod = await import('../../../tprm_frontend/src/services/roleRoutingService.js')
  return mod
}

// ─── Static data ────────────────────────────────────────────────────────────
const currentYear = computed(() => new Date().getFullYear())

const identifierModes = [
  { id: 'username', label: 'Username', icon: User },
  { id: 'userid', label: 'User ID', icon: IdCard },
]

const features = [
  { icon: ShieldHalf, label: 'Enterprise-grade security with multi-layer protection' },
  { icon: FileCheck2, label: 'Automated compliance reporting and real-time monitoring' },
  { icon: LineChart, label: 'Advanced risk analytics with predictive insights' },
]

// ─── Reactive state ──────────────────────────────────────────────────────────
const password = ref('')
const errorMessage = ref('')
const isLoading = ref(false)
const router = useRouter()
const passwordFieldType = ref('password')
const loginType = ref('username')
const loginIdentifier = ref('')
const showForgotPasswordModal = ref(false)
const showConsentForm = ref(false)
const isVendorUser = ref(false)
const showMfaStep = ref(false)

/** Avoid v-else adjacency bugs: show exactly one of MFA panel or login form */
const showMfaPanel = computed(() => Boolean(MFA_ENABLED && showMfaStep.value))

const otp = ref('')
const otpDigits = ref(['', '', '', '', '', ''])
const otpInputRefs = ref([])
const emailMasked = ref('')
const isResendingOtp = ref(false)
const timer = ref(600)
const timerInterval = ref(null)
const resendCooldown = ref(0)
const resendCooldownInterval = ref(null)
const captchaRef = ref(null)
const isCaptchaVerified = ref(false)
const captchaToken = ref('')
let captchaWidgetId = null

// ─── Google SSO ──────────────────────────────────────────────────────────────
const loginWithGoogle = async () => {
  try {
    isLoading.value = true
    errorMessage.value = ''
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

// ─── Login ───────────────────────────────────────────────────────────────────
const login = async () => {
  try {
    isLoading.value = true
    errorMessage.value = ''

    if (!loginIdentifier.value || !password.value) {
      errorMessage.value = 'Please fill in all required fields'
      isLoading.value = false
      return
    }

    if (!isCaptchaVerified.value || !captchaToken.value) {
      errorMessage.value = 'Please complete the CAPTCHA verification'
      isLoading.value = false
      return
    }

    const cookieSessionId = localStorage.getItem('cookie_session_id')
    const cookiePreferencesSaved = localStorage.getItem('cookie_preferences_saved')
    const cookiePreferences = localStorage.getItem('cookie_preferences')

    localStorage.clear()

    if (cookieSessionId) localStorage.setItem('cookie_session_id', cookieSessionId)
    if (cookiePreferencesSaved) localStorage.setItem('cookie_preferences_saved', cookiePreferencesSaved)
    if (cookiePreferences) localStorage.setItem('cookie_preferences', cookiePreferences)

    const result = await authService.login(
      loginIdentifier.value,
      password.value,
      loginType.value,
      captchaToken.value
    )

    if (MFA_ENABLED && result.requiresMfa) {
      showMfaStep.value = true
      emailMasked.value = result.emailMasked || 'your email'
      errorMessage.value = ''
      otpDigits.value = ['', '', '', '', '', '']
      otp.value = ''
      startTimer()
      startResendCooldown()
      nextTick(() => {
        if (otpInputRefs.value[0]) otpInputRefs.value[0].focus()
      })
      return
    }

    if (result.success) {
      resetCaptcha()
      console.log('🔐 JWT Login successful!', {
        user_id: result.user.UserId,
        email: result.user.Email,
        username: result.user.UserName,
        consent_required: result.user.consent_accepted !== '1',
      })
      await determineVendorFlag()
      if (result.user.consent_accepted !== '1') {
        console.log('📋 Consent required - showing consent form')
        showConsentForm.value = true
      } else {
        console.log('✅ Consent already accepted - proceeding to post-login route')
        await navigateAfterLogin()
        if (window.onSuccessfulLogin) window.onSuccessfulLogin()
      }
    } else {
      let errorMsg = 'Invalid username or password. Please try again.'
      if (result.error) errorMsg = result.error
      else if (result.message) errorMsg = result.message
      else if (result.details && result.details.message) errorMsg = result.details.message
      errorMessage.value = errorMsg
      resetCaptcha()
    }
  } catch (error) {
    console.error('❌ JWT Login error:', error)
    let errorMsg = 'Invalid username or password. Please try again.'
    if (error.response && error.response.data) {
      if (error.response.data.message) errorMsg = error.response.data.message
      else if (error.response.data.error) errorMsg = error.response.data.error
      else if (error.response.data.detail) errorMsg = error.response.data.detail
      else if (error.response.status === 401) errorMsg = 'Invalid username or password. Please check your credentials and try again.'
      else if (error.response.status === 403) errorMsg = error.response.data.message || 'Access denied. Your account may be locked. Please contact your administrator.'
      else if (error.response.status === 429) errorMsg = error.response.data.message || 'Too many login attempts. Please wait a moment and try again.'
      else if (error.response.status === 400) errorMsg = error.response.data.message || 'Invalid request. Please check your input and try again.'
    } else if (error.message) {
      if (error.message.includes('connect to the server') || error.message.includes('CONNECTION_REFUSED') || error.code === 'ECONNREFUSED') {
        errorMsg = 'Unable to connect to the server. Please ensure the backend server is running on port 8000.'
      } else if (error.message.includes('timeout') || error.message.includes('Timeout') || error.code === 'ECONNABORTED') {
        errorMsg = 'Request timed out. The server may be slow or unavailable. Please try again.'
      } else if (error.message.includes('CAPTCHA')) {
        errorMsg = error.message
      } else {
        errorMsg = error.message
      }
    }
    errorMessage.value = errorMsg
    resetCaptcha()
  } finally {
    isLoading.value = false
  }
}

// ─── Post-login routing ───────────────────────────────────────────────────────
const resolvePostLoginRoute = async () => {
  try {
    const token =
      sessionStorage.getItem('session_token') ||
      sessionStorage.getItem('access_token') ||
      localStorage.getItem('session_token') ||
      localStorage.getItem('access_token')
    if (!token) return '/home'

    let userId = null
    try {
      const currentUser = JSON.parse(
        sessionStorage.getItem('current_user') ||
        localStorage.getItem('current_user') ||
        localStorage.getItem('user') ||
        '{}'
      )
      userId = currentUser.userid || currentUser.id || currentUser.user_id || currentUser.UserId
    } catch (e) {
      console.error('Error getting user ID for post-login route:', e)
    }

    const roleRoutingService = await loadRoleRoutingService()
    return await roleRoutingService.getPostLoginRoute(token, userId)
  } catch (error) {
    console.error('Failed to resolve post-login route, defaulting to /home', error)
    return '/home'
  }
}

const navigateAfterLogin = async () => {
  let path = '/home'
  try {
    const raw = await resolvePostLoginRoute()
    path = (!raw || raw === '/' || raw === '/login') ? '/home' : raw
  } catch (e) {
    console.error('navigateAfterLogin:', e)
    path = '/home'
  }
  try {
    await router.replace(path)
  } catch (err) {
    console.error('router.replace failed:', err)
    await router.replace('/home')
  }
}

const determineVendorFlag = async () => {
  try {
    const token =
      sessionStorage.getItem('session_token') ||
      sessionStorage.getItem('access_token') ||
      localStorage.getItem('session_token') ||
      localStorage.getItem('access_token')
    if (!token) { isVendorUser.value = false; return }
    const roleRoutingService = await loadRoleRoutingService()
    const roleResult = await roleRoutingService.getUserRole(token)
    isVendorUser.value = roleResult.success && roleResult.role
      ? roleResult.role.toLowerCase() === 'vendor'
      : false
  } catch (error) {
    console.error('Error determining vendor role:', error)
    isVendorUser.value = false
  }
}

// ─── Consent handlers ─────────────────────────────────────────────────────────
const handleConsentAccepted = async () => {
  console.log('✅ Consent accepted - proceeding after login')
  showConsentForm.value = false
  await navigateAfterLogin()
  if (window.onSuccessfulLogin) window.onSuccessfulLogin()
}

const handleConsentDeclined = () => {
  console.log('❌ Consent declined - logging out')
  showConsentForm.value = false
  authService.clearAuthData()
  errorMessage.value = 'You must accept the terms and conditions to use the system.'
}

// ─── MFA / OTP ───────────────────────────────────────────────────────────────
const verifyOtp = async () => {
  try {
    isLoading.value = true
    errorMessage.value = ''
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
      console.log('🔐 MFA Login successful!', {
        user_id: result.user.UserId,
        email: result.user.Email,
        username: result.user.UserName,
        consent_required: result.user.consent_accepted !== '1',
      })
      stopTimer()
      await determineVendorFlag()
      if (result.user.consent_accepted !== '1') {
        console.log('📋 Consent required - showing consent form')
        showConsentForm.value = true
        showMfaStep.value = false
      } else {
        console.log('✅ Consent already accepted - proceeding to post-login route')
        showMfaStep.value = false
        await navigateAfterLogin()
        if (window.onSuccessfulLogin) window.onSuccessfulLogin()
      }
    } else {
      errorMessage.value = 'Invalid verification code. Please try again.'
    }
  } catch (error) {
    console.error('❌ MFA OTP verification error:', error)
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
      otpDigits.value = ['', '', '', '', '', '']
      otp.value = ''
      startTimer()
      startResendCooldown()
      nextTick(() => { if (otpInputRefs.value[0]) otpInputRefs.value[0].focus() })
      const successMsg = 'New verification code sent!'
      errorMessage.value = successMsg
      setTimeout(() => { if (errorMessage.value === successMsg) errorMessage.value = '' }, 3000)
    } else {
      errorMessage.value = result.message || 'Failed to resend code. Please try again.'
    }
  } catch (error) {
    errorMessage.value = error.message || 'Failed to resend code. Please try again.'
    console.error('❌ Resend OTP error:', error)
  } finally {
    isResendingOtp.value = false
  }
}

const isOtpComplete = computed(() =>
  otpDigits.value.every(d => d !== '') && otpDigits.value.join('').length === 6
)

const formattedTimer = computed(() => {
  const m = Math.floor(timer.value / 60)
  const s = timer.value % 60
  return `${m}:${s.toString().padStart(2, '0')}`
})

const handleOtpInput = (index, event) => {
  const value = event.target.value.replace(/[^0-9]/g, '')
  if (value) {
    otpDigits.value[index] = value
    otp.value = otpDigits.value.join('')
    if (index < 5) nextTick(() => { if (otpInputRefs.value[index + 1]) otpInputRefs.value[index + 1].focus() })
  } else {
    otpDigits.value[index] = ''
    otp.value = otpDigits.value.join('')
  }
}

const handleOtpKeydown = (index, event) => {
  if (event.key === 'Backspace' && !otpDigits.value[index] && index > 0) {
    nextTick(() => { if (otpInputRefs.value[index - 1]) otpInputRefs.value[index - 1].focus() })
  }
  if (event.key === 'ArrowLeft' && index > 0) {
    event.preventDefault()
    if (otpInputRefs.value[index - 1]) otpInputRefs.value[index - 1].focus()
  }
  if (event.key === 'ArrowRight' && index < 5) {
    event.preventDefault()
    if (otpInputRefs.value[index + 1]) otpInputRefs.value[index + 1].focus()
  }
}

const handleOtpPaste = (event) => {
  event.preventDefault()
  const pastedData = event.clipboardData.getData('text').replace(/[^0-9]/g, '').slice(0, 6)
  if (pastedData.length > 0) {
    for (let i = 0; i < 6; i++) otpDigits.value[i] = pastedData[i] || ''
    otp.value = otpDigits.value.join('')
    const lastIndex = Math.min(pastedData.length - 1, 5)
    nextTick(() => { if (otpInputRefs.value[lastIndex]) otpInputRefs.value[lastIndex].focus() })
  }
}

// ─── Timer ───────────────────────────────────────────────────────────────────
const startTimer = () => {
  timer.value = 600
  if (timerInterval.value) clearInterval(timerInterval.value)
  timerInterval.value = setInterval(() => {
    if (timer.value > 0) timer.value--
    else clearInterval(timerInterval.value)
  }, 1000)
}

const stopTimer = () => {
  if (timerInterval.value) { clearInterval(timerInterval.value); timerInterval.value = null }
}

const startResendCooldown = () => {
  resendCooldown.value = 30
  if (resendCooldownInterval.value) clearInterval(resendCooldownInterval.value)
  resendCooldownInterval.value = setInterval(() => {
    if (resendCooldown.value > 0) resendCooldown.value--
    else { clearInterval(resendCooldownInterval.value); resendCooldownInterval.value = null }
  }, 1000)
}

const stopResendCooldown = () => {
  if (resendCooldownInterval.value) { clearInterval(resendCooldownInterval.value); resendCooldownInterval.value = null }
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

// ─── Misc ────────────────────────────────────────────────────────────────────
const togglePasswordVisibility = () => {
  passwordFieldType.value = passwordFieldType.value === 'password' ? 'text' : 'password'
}

// ─── reCAPTCHA ───────────────────────────────────────────────────────────────
const loadRecaptcha = () => {
  if (showMfaStep.value || !captchaRef.value) return

  if (window.grecaptcha && window.grecaptcha.render) {
    nextTick(() => renderCaptcha())
    return
  }

  if (document.querySelector('script[src*="recaptcha/api.js"]')) {
    const checkInterval = setInterval(() => {
      if (window.grecaptcha && window.grecaptcha.render) {
        clearInterval(checkInterval)
        nextTick(() => renderCaptcha())
      }
    }, 100)
    setTimeout(() => clearInterval(checkInterval), 10000)
    return
  }

  const script = document.createElement('script')
  script.src = 'https://www.google.com/recaptcha/api.js?render=explicit&onload=onRecaptchaLoad'
  script.async = true
  script.defer = true

  const loadTimeout = setTimeout(() => {
    console.warn('⚠️ reCAPTCHA script load timeout')
    if (process.env.NODE_ENV === 'development') isCaptchaVerified.value = true
  }, 30000)

  script.onerror = () => {
    clearTimeout(loadTimeout)
    console.warn('⚠️ Failed to load reCAPTCHA script.')
    if (process.env.NODE_ENV === 'development') isCaptchaVerified.value = true
  }

  window.onRecaptchaLoad = () => {
    clearTimeout(loadTimeout)
    try {
      nextTick(() => renderCaptcha())
    } catch (error) {
      if (error.message && !error.message.includes('Timeout')) console.error('reCAPTCHA error:', error)
      if (process.env.NODE_ENV === 'development') isCaptchaVerified.value = true
    }
  }

  try {
    document.head.appendChild(script)
  } catch (error) {
    clearTimeout(loadTimeout)
    console.warn('⚠️ Error appending reCAPTCHA script:', error)
    if (process.env.NODE_ENV === 'development') isCaptchaVerified.value = true
  }
}

const renderCaptcha = () => {
  if (showMfaStep.value) return
  if (!captchaRef.value || !document.getElementById('recaptcha-container')) return
  if (!window.grecaptcha || !window.grecaptcha.render) return

  try {
    if (captchaWidgetId !== null) {
      try { window.grecaptcha.reset(captchaWidgetId) } catch (e) { console.warn('Error resetting CAPTCHA:', e) }
    }
    captchaWidgetId = window.grecaptcha.render('recaptcha-container', {
      sitekey: RECAPTCHA_SITE_KEY,
      callback: (token) => { isCaptchaVerified.value = true; captchaToken.value = token; errorMessage.value = '' },
      'expired-callback': () => { isCaptchaVerified.value = false; captchaToken.value = '' },
      'error-callback': () => { isCaptchaVerified.value = false; captchaToken.value = ''; errorMessage.value = 'CAPTCHA verification failed. Please try again.' },
    })
  } catch (e) {
    console.error('Error rendering CAPTCHA:', e)
    if (process.env.NODE_ENV === 'development') isCaptchaVerified.value = true
  }
}

watch(loginType, () => { if (!showMfaStep.value) resetCaptcha() })

const resetCaptcha = () => {
  if (captchaWidgetId !== null && window.grecaptcha) {
    try { window.grecaptcha.reset(captchaWidgetId); isCaptchaVerified.value = false; captchaToken.value = '' }
    catch (e) { console.warn('Error resetting CAPTCHA:', e) }
  }
}

watch(showMfaStep, (newValue) => {
  if (!newValue) nextTick(() => loadRecaptcha())
  else resetCaptcha()
})

// ─── Lifecycle ────────────────────────────────────────────────────────────────
onMounted(() => {
  document.documentElement.classList.add('login-no-scroll')
  document.body.classList.add('login-no-scroll')

  const route = router.currentRoute.value
  if (route.query.resetPassword === 'true' && route.query.email) {
    showForgotPasswordModal.value = true
  }
  nextTick(() => { if (!showMfaStep.value) loadRecaptcha() })
})

onUnmounted(() => {
  document.documentElement.classList.remove('login-no-scroll')
  document.body.classList.remove('login-no-scroll')

  if (captchaWidgetId !== null && window.grecaptcha) {
    try { window.grecaptcha.reset(captchaWidgetId) } catch (e) { /* ignore */ }
  }
  stopTimer()
  stopResendCooldown()
})
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  min-height: 100dvh;
  height: 100dvh;
  width: 100%;
  overflow: hidden;
}
</style>
