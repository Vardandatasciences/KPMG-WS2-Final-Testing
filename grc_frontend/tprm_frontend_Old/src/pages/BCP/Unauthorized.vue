<template>
  <div class="unauthorized-page">
    <div class="container">
      <div class="error-content">
        <div class="error-icon">
          <svg width="64" height="64" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z" fill="#ef4444"/>
          </svg>
        </div>
        <h1 class="error-title">Access Denied</h1>
        <p class="error-message">
          You don't have permission to access this page. Please contact your administrator if you believe this is an error.
        </p>
        <div class="error-actions">
          <button @click="goBack" class="btn btn-secondary">
            Go Back
          </button>
          <button @click="goHome" class="btn btn-primary">
            Go to Dashboard
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import loggingService from '@/services/loggingService'

export default {
  name: 'Unauthorized',
  async mounted() {
    // Log unauthorized access attempt
    await loggingService.log({
      module: 'BCP',
      actionType: 'ACCESS_DENIED',
      description: 'User accessed unauthorized page',
      entityType: 'Page',
      logLevel: 'WARNING',
      additionalInfo: {
        attemptedPath: this.$route.fullPath
      }
    })
  },
  methods: {
    goBack() {
      this.$router.go(-1)
    },
    goHome() {
      this.$router.push('/dashboard')
    }
  }
}
</script>

<style scoped>
.unauthorized-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20px;
}

.container {
  max-width: 600px;
  width: 100%;
}

.error-content {
  background: white;
  border-radius: 12px;
  padding: 48px 32px;
  text-align: center;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
}

.error-icon {
  margin-bottom: 24px;
}

.error-title {
  font-size: 2.5rem;
  font-weight: 700;
  color: #1f2937;
  margin-bottom: 16px;
}

.error-message {
  font-size: 1.125rem;
  color: #6b7280;
  margin-bottom: 32px;
  line-height: 1.6;
}

.error-actions {
  display: flex;
  gap: 16px;
  justify-content: center;
  flex-wrap: wrap;
}

.btn {
  padding: 12px 24px;
  border-radius: 8px;
  font-weight: 600;
  text-decoration: none;
  border: none;
  cursor: pointer;
  transition: all 0.2s ease;
  font-size: 1rem;
}

.btn-primary {
  background: #3b82f6;
  color: white;
}

.btn-primary:hover {
  background: #2563eb;
  transform: translateY(-1px);
}

.btn-secondary {
  background: #f3f4f6;
  color: #374151;
  border: 1px solid #d1d5db;
}

.btn-secondary:hover {
  background: #e5e7eb;
  transform: translateY(-1px);
}

</style>
