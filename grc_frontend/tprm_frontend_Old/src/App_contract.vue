<template>
  <div id="app">
    <!-- Show login page without layout -->
    <div v-if="isAuthPage" class="auth-container">
      <router-view />
    </div>
    
    <!-- Show main app with layout for all authenticated pages including dashboard -->
    <Layout v-else>
      <router-view />
    </Layout>
    
    <!-- Global Loading Overlay -->
    <div v-if="isLoading" class="loading-overlay">
      <div class="loading-spinner">
        <div class="spinner"></div>
        <p>{{ loadingMessage || 'Loading...' }}</p>
      </div>
    </div>
  </div>
</template>

<script>
import { mapActions, mapGetters } from 'vuex'
import Layout from './components/Layout.vue'

export default {
  name: 'App',
  components: {
    Layout
  },
  
  computed: {
    ...mapGetters('auth', ['isAuthenticated', 'currentUser']),
    ...mapGetters(['isLoading', 'loadingMessage']),
    
    isAuthPage() {
      return this.$route.path === '/contract-login' || this.$route.path === '/login'
    },
    
    isDashboardPage() {
      return this.$route.path === '/contractdashboard' || this.$route.path === '/dashboard'
    }
  },
  
  methods: {
    ...mapActions('auth', ['logoutUser']),
    
    async logout() {
      try {
        await this.logoutUser()
        this.$router.push('/contract-login')
      } catch (error) {
        console.error('Logout error:', error)
        // Force logout even if API call fails
        this.$store.commit('CLEAR_AUTH')
        this.$router.push('/contract-login')
      }
    }
  },
  
  async created() {
    // Check if user has a valid session on app start
    console.log('App created - checking session validation')
    
    const sessionToken = localStorage.getItem('session_token')
    if (sessionToken) {
      try {
        await this.$store.dispatch('auth/validateSession')
      } catch (error) {
        // Session invalid, clear it
        localStorage.removeItem('session_token')
        this.$store.commit('auth/CLEAR_AUTH')
      }
    } else {
      // No session token found, user needs to login
      console.log('No session token found, user needs to login')
    }
  }
}
</script>

<style>
#app {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background: white;
}

.auth-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.loading-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.loading-spinner {
  background: white;
  padding: 2rem;
  border-radius: 12px;
  text-align: center;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
}

.spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #f3f3f3;
  border-top: 4px solid #007bff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 1rem;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}
</style>