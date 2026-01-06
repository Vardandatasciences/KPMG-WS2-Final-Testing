<template>
  <div class="login-container">
    <div class="login-card">
      <div class="login-header">
        <h1>🚀 Contract Management System</h1>
        <p>Welcome, testuser1</p>
      </div>
      
      <div class="welcome-content">
        <div class="welcome-icon">👋</div>
        <h2>Ready to manage contracts?</h2>
        <p>You're logged in as <strong>testuser1</strong> and ready to access the contract management system.</p>
        
        <button
          @click="goToDashboard"
          class="btn btn-primary btn-full"
        >
          🏠 Go to Contract Dashboard
        </button>
      </div>
      
      <!-- Info Section -->
      <div class="login-info">
        <div class="info-item">
          <span class="icon">👤</span>
          <span>Logged in as: testuser1</span>
        </div>
        <div class="info-item">
          <span class="icon">⚡</span>
          <span>No authentication required</span>
        </div>
        <div class="info-item">
          <span class="icon">🏢</span>
          <span>Enterprise Contract Management</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import loggingService from '@/services/loggingService'

export default {
  name: 'ContractLogin',
  
  data() {
    return {
      currentUser: 'testuser1'
    }
  },
  
  async mounted() {
    await loggingService.logPageView('Contract', 'Login')
    // Set hardcoded user in localStorage
    localStorage.setItem('current_user', this.currentUser)
    localStorage.setItem('session_token', 'hardcoded_token_for_testuser1')
  },
  
  methods: {
    goToDashboard() {
      // Navigate to contract dashboard
      this.$router.push('/contractdashboard')
    }
  }
}
</script>

<style scoped>
.login-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2rem;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.login-card {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  border-radius: 20px;
  padding: 3rem;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
  width: 100%;
  max-width: 450px;
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.login-header {
  text-align: center;
  margin-bottom: 2rem;
}

.login-header h1 {
  color: #333;
  margin-bottom: 0.5rem;
  font-size: 2rem;
  font-weight: 700;
}

.login-header p {
  color: #666;
  font-size: 1rem;
}

.welcome-content {
  text-align: center;
  margin-bottom: 2rem;
}

.welcome-icon {
  font-size: 4rem;
  margin-bottom: 1rem;
}

.welcome-content h2 {
  color: #333;
  margin-bottom: 1rem;
  font-size: 1.5rem;
}

.welcome-content p {
  color: #666;
  margin-bottom: 2rem;
  line-height: 1.6;
}

.btn {
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 8px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
  text-decoration: none;
  display: inline-block;
  text-align: center;
}

.btn-primary {
  background: #007bff;
  color: white;
}

.btn-primary:hover {
  background: #0056b3;
  transform: translateY(-2px);
}

.btn-full {
  width: 100%;
  font-size: 1.1rem;
  padding: 1rem;
  margin-top: 1rem;
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
}

.login-info {
  border-top: 1px solid #e1e5e9;
  padding-top: 2rem;
}

.info-item {
  display: flex;
  align-items: center;
  margin-bottom: 1rem;
  color: #666;
  font-size: 0.9rem;
}

.info-item .icon {
  margin-right: 0.75rem;
  font-size: 1.2rem;
}

.info-item:last-child {
  margin-bottom: 0;
}

@media (max-width: 480px) {
  .login-card {
    padding: 2rem;
    margin: 1rem;
  }
  
  .login-header h1 {
    font-size: 1.5rem;
  }
}
</style>