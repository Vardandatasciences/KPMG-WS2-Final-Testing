<template>
  <div class="login-container">
    <div class="login-card">
      <div class="login-header">
        <div class="logo">
          <svg
            class="h-8 w-8 text-primary"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"
            />
          </svg>
        </div>
        <h1 class="login-title">BCP/DRP Manager</h1>
        <p class="login-subtitle">Business Continuity Portal</p>
      </div>

      <form @submit.prevent="handleLogin" class="login-form">
        <div class="form-group">
          <label for="username" class="form-label">Username</label>
          <input
            id="username"
            v-model="form.username"
            type="text"
            class="form-input"
            :class="{ 'error': errors.username }"
            placeholder="Enter your username"
            required
            autocomplete="username"
          />
          <span v-if="errors.username" class="error-message">{{ errors.username }}</span>
        </div>

        <div class="form-group">
          <label for="password" class="form-label">Password</label>
          <input
            id="password"
            v-model="form.password"
            type="password"
            class="form-input"
            :class="{ 'error': errors.password }"
            placeholder="Enter your password"
            required
            autocomplete="current-password"
          />
          <span v-if="errors.password" class="error-message">{{ errors.password }}</span>
        </div>

        <div v-if="loginError" class="error-banner">
          <svg class="error-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          {{ loginError }}
        </div>

        <button
          type="submit"
          class="login-button"
          :disabled="isLoading"
        >
          <svg v-if="isLoading" class="animate-spin h-4 w-4 mr-2" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
          {{ isLoading ? 'Signing in...' : 'Sign In' }}
        </button>
      </form>

      <div class="login-footer">
        <p class="footer-text">
          Secure access to Business Continuity and Disaster Recovery Management System
        </p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useStore } from 'vuex'
import loggingService from '@/services/loggingService'

const router = useRouter()
const store = useStore()

// Form data
const form = ref({
  username: '',
  password: '',
  rememberMe: false
})

// Form validation
const errors = ref({
  username: '',
  password: ''
})

// Loading and error states
const isLoading = ref(false)
const loginError = ref('')

// Computed properties
const isFormValid = computed(() => {
  return form.value.username.trim() && form.value.password.trim()
})

// Methods
const validateForm = () => {
  errors.value = { username: '', password: '' }
  let isValid = true

  if (!form.value.username.trim()) {
    errors.value.username = 'Username is required'
    isValid = false
  }

  if (!form.value.password.trim()) {
    errors.value.password = 'Password is required'
    isValid = false
  }

  return isValid
}

const handleLogin = async () => {
  if (!validateForm()) {
    return
  }

  isLoading.value = true
  loginError.value = ''

  try {
    const result = await store.dispatch('auth/login', {
      username: form.value.username,
      password: form.value.password
    })

    if (result.success) {
      // Log successful login
      await loggingService.log({
        module: 'BCP',
        actionType: 'LOGIN',
        description: `User logged in successfully`,
        entityType: 'User',
        entityId: form.value.username,
        logLevel: 'INFO',
        additionalInfo: {
          username: form.value.username,
          rememberMe: form.value.rememberMe
        }
      })
      
      // Redirect to the vendor upload page (original home page)
      router.push('/vendor-upload')
    } else {
      loginError.value = result.error || 'Login failed. Please try again.'
      // Log failed login attempt
      await loggingService.log({
        module: 'BCP',
        actionType: 'LOGIN_FAILED',
        description: `Login failed for user`,
        entityType: 'User',
        entityId: form.value.username,
        logLevel: 'WARNING',
        additionalInfo: {
          username: form.value.username,
          error: result.error
        }
      })
    }
  } catch (error) {
    console.error('Login error:', error)
    loginError.value = 'An unexpected error occurred. Please try again.'
    // Log login error
    await loggingService.log({
      module: 'BCP',
      actionType: 'LOGIN_ERROR',
      description: `Login error occurred`,
      entityType: 'User',
      entityId: form.value.username,
      logLevel: 'ERROR',
      additionalInfo: {
        username: form.value.username,
        error: error.message
      }
    })
  } finally {
    isLoading.value = false
  }
}
</script>

<style scoped>
.login-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 1rem;
}

.login-card {
  background: white;
  border-radius: 12px;
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
  padding: 2rem;
  width: 100%;
  max-width: 400px;
}

.login-header {
  text-align: center;
  margin-bottom: 2rem;
}

.logo {
  display: flex;
  justify-content: center;
  margin-bottom: 1rem;
}

.login-title {
  font-size: 1.875rem;
  font-weight: 700;
  color: #1f2937;
  margin-bottom: 0.5rem;
}

.login-subtitle {
  color: #6b7280;
  font-size: 0.875rem;
}

.login-form {
  space-y: 1.5rem;
}

.form-group {
  margin-bottom: 1.5rem;
}

.form-label {
  display: block;
  font-size: 0.875rem;
  font-weight: 500;
  color: #374151;
  margin-bottom: 0.5rem;
}

.form-input {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 1rem;
  transition: border-color 0.15s ease-in-out, box-shadow 0.15s ease-in-out;
}

.form-input:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.form-input.error {
  border-color: #ef4444;
}

.error-message {
  display: block;
  color: #ef4444;
  font-size: 0.75rem;
  margin-top: 0.25rem;
}

.error-banner {
  display: flex;
  align-items: center;
  background-color: #fef2f2;
  border: 1px solid #fecaca;
  color: #dc2626;
  padding: 0.75rem;
  border-radius: 6px;
  margin-bottom: 1rem;
  font-size: 0.875rem;
}

.error-icon {
  width: 1rem;
  height: 1rem;
  margin-right: 0.5rem;
  flex-shrink: 0;
}

.login-button {
  width: 100%;
  background-color: #3b82f6;
  color: white;
  padding: 0.75rem 1rem;
  border: none;
  border-radius: 6px;
  font-size: 1rem;
  font-weight: 500;
  cursor: pointer;
  transition: background-color 0.15s ease-in-out;
  display: flex;
  align-items: center;
  justify-content: center;
}

.login-button:hover:not(:disabled) {
  background-color: #2563eb;
}

.login-button:disabled {
  background-color: #9ca3af;
  cursor: not-allowed;
}

.login-footer {
  margin-top: 2rem;
  text-align: center;
}

.footer-text {
  color: #6b7280;
  font-size: 0.75rem;
  line-height: 1.4;
}

.animate-spin {
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
</style>
