<template>
  <header style="border-bottom: 1px solid #e5e7eb; background: white; padding: 0.75rem 1.5rem;">
    <div style="display: flex; align-items: center; justify-content: space-between;">
      <div style="display: flex; align-items: center; gap: 1rem;">
        <!-- Sidebar trigger -->
        <button style="display: flex; align-items: center; justify-content: center; border-radius: 6px; padding: 0.5rem; background: transparent; border: none; cursor: pointer;" aria-label="Toggle sidebar">
          ☰
        </button>

        <div style="position: relative; flex: 1; max-width: 20rem;">
          <span style="position: absolute; left: 0.75rem; top: 50%; transform: translateY(-50%); color: #6b7280;">🔍</span>
          <input 
            placeholder="Search contracts, vendors..." 
            style="padding-left: 2.5rem; width: 100%; height: 2.25rem; border-radius: 6px; border: 1px solid #d1d5db; background: white; padding-right: 0.75rem; font-size: 0.875rem; outline: none;"
          />
        </div>
      </div>

      <div style="display: flex; align-items: center; gap: 1rem;">
        <button style="position: relative; display: flex; height: 2.25rem; width: 2.25rem; align-items: center; justify-content: center; border-radius: 6px; background: transparent; border: none; cursor: pointer;">
          🔔
          <span style="position: absolute; top: -0.25rem; right: -0.25rem; width: 1.25rem; height: 1.25rem; border-radius: 50%; background: #dc2626; color: white; font-size: 0.75rem; display: flex; align-items: center; justify-content: center;">3</span>
        </button>
        
        <!-- User info and logout -->
        <div style="display: flex; align-items: center; gap: 0.75rem;">
          <div style="font-size: 0.875rem;">
            <div style="font-weight: 500;">{{ displayName }}</div>
            <div style="color: #6b7280;">{{ currentUser?.email || '' }}</div>
          </div>
          <button 
            @click="logout" 
            style="display: flex; height: 2.25rem; padding: 0 0.75rem; align-items: center; justify-content: center; border-radius: 6px; background: #dc2626; color: white; border: none; font-size: 0.875rem; font-weight: 500; cursor: pointer; transition: all 0.2s ease;"
            title="Logout"
            @mouseenter="$event.target.style.background = '#b91c1c'"
            @mouseleave="$event.target.style.background = '#dc2626'"
          >
            🚪 Logout
          </button>
        </div>
      </div>
    </div>
  </header>
</template>

<script>
import { mapActions, mapGetters } from 'vuex'

export default {
  name: 'Header',
  
  computed: {
    ...mapGetters('auth', ['currentUser']),
    
    displayName() {
      if (!this.currentUser) {
        console.log('Header: No currentUser found')
        return 'testuser1'
      }
      
      console.log('Header: currentUser found:', this.currentUser)
      
      // Try to use first_name and last_name if available
      if (this.currentUser.first_name && this.currentUser.last_name) {
        return `${this.currentUser.first_name} ${this.currentUser.last_name}`
      }
      
      // Fall back to username, default to testuser1
      return this.currentUser.username || 'testuser1'
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
  }
}
</script>