<template>
  <div class="login-container">
    <div class="login-card">
      <div class="login-header">
        <h1 class="login-title">Vendor Management System</h1>
        <p class="login-subtitle">Please sign in to your account</p>
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
          />
          <span v-if="errors.password" class="error-message">{{ errors.password }}</span>
        </div>
        
        <button 
          type="submit" 
          class="login-button"
          :disabled="loading"
        >
          <span v-if="loading" class="loading-spinner"></span>
          {{ loading ? 'Signing in...' : 'Sign In' }}
        </button>
        
        <div v-if="errorMessage" class="error-alert">
          {{ errorMessage }}
        </div>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import apiClient from '@/config/axios'
import loggingService from '@/services/loggingService'

const router = useRouter()
const authStore = useAuthStore()

// Form data
const form = reactive({
  username: '',
  password: ''
})

// Form state
const loading = ref(false)
const errors = reactive({})
const errorMessage = ref('')

// Validation
const validateForm = () => {
  errors.username = ''
  errors.password = ''
  
  if (!form.username.trim()) {
    errors.username = 'Username is required'
    return false
  }
  
  if (!form.password) {
    errors.password = 'Password is required'
    return false
  }
  
  return true
}

// Login handler
const handleLogin = async () => {
  if (!validateForm()) return
  
  loading.value = true
  errorMessage.value = ''
  
  try {
    const response = await apiClient.post('/api/v1/vendor-auth/login/', {
      username: form.username,
      password: form.password
    })
    
    if (response.data.success) {
      // Log successful login
      await loggingService.log({
        module: 'Vendor',
        actionType: 'LOGIN',
        description: `User logged in successfully`,
        entityType: 'User',
        entityId: form.username,
        logLevel: 'INFO',
        additionalInfo: {
          username: form.username
        }
      })
      
      // Use auth store to set user data (this will update isAuthenticated)
      authStore.setUser(response.data.user)
      
      // Redirect to dashboard
      router.push('/dashboard')
    } else {
      errorMessage.value = response.data.message || 'Login failed'
      // Log failed login
      await loggingService.log({
        module: 'Vendor',
        actionType: 'LOGIN_FAILED',
        description: `Login failed for user`,
        entityType: 'User',
        entityId: form.username,
        logLevel: 'WARNING',
        additionalInfo: {
          username: form.username,
          error: response.data.message
        }
      })
    }
  } catch (error) {
    console.error('Login error:', error)
    if (error.response?.data?.message) {
      errorMessage.value = error.response.data.message
    } else {
      errorMessage.value = 'An error occurred during login. Please try again.'
    }
    // Log login error
    await loggingService.log({
      module: 'Vendor',
      actionType: 'LOGIN_ERROR',
      description: `Login error occurred`,
      entityType: 'User',
      entityId: form.username,
      logLevel: 'ERROR',
      additionalInfo: {
        username: form.username,
        error: error.message
      }
    })
  } finally {
    loading.value = false
  }
}

// Log page view on mount
onMounted(async () => {
  await loggingService.logPageView('Vendor', 'Login')
})
</script>

<style scoped>
.login-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20px;
}

.login-card {
  background: white;
  border-radius: 12px;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
  padding: 40px;
  width: 100%;
  max-width: 400px;
}

.login-header {
  text-align: center;
  margin-bottom: 32px;
}

.login-title {
  font-size: 28px;
  font-weight: 700;
  color: #1f2937;
  margin: 0 0 8px 0;
}

.login-subtitle {
  color: #6b7280;
  font-size: 16px;
  margin: 0;
}

.login-form {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-label {
  font-weight: 600;
  color: #374151;
  font-size: 14px;
}

.form-input {
  padding: 12px 16px;
  border: 2px solid #e5e7eb;
  border-radius: 8px;
  font-size: 16px;
  transition: all 0.2s ease;
  background: #f9fafb;
}

.form-input:focus {
  outline: none;
  border-color: #667eea;
  background: white;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.form-input.error {
  border-color: #ef4444;
  background: #fef2f2;
}

.error-message {
  color: #ef4444;
  font-size: 14px;
  font-weight: 500;
}

.login-button {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  padding: 14px 24px;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  min-height: 48px;
}

.login-button:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 8px 20px rgba(102, 126, 234, 0.3);
}

.login-button:disabled {
  opacity: 0.7;
  cursor: not-allowed;
  transform: none;
}

.loading-spinner {
  width: 20px;
  height: 20px;
  border: 2px solid transparent;
  border-top: 2px solid white;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.error-alert {
  background: #fef2f2;
  border: 1px solid #fecaca;
  color: #dc2626;
  padding: 12px 16px;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  text-align: center;
}

/* Responsive design */
@media (max-width: 480px) {
  .login-card {
    padding: 24px;
    margin: 16px;
  }
  
  .login-title {
    font-size: 24px;
  }
}
</style>
