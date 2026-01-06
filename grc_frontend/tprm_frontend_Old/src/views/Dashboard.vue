<template>
  <div class="dashboard-content">
    <!-- Contract Navigation Section -->
    <div class="contract-nav-section">
      <h2>📋 Contract Management Navigation</h2>
      <div class="nav-grid">
        <div class="nav-item" :class="{ active: activeSection === 'dashboard' }" @click="setActiveSection('dashboard')">
          <span class="nav-icon">📊</span>
          <span class="nav-text">Dashboard</span>
        </div>
        <div class="nav-item contract-item" :class="{ active: activeSection === 'contract' }">
          <div class="nav-item-header" @click="setActiveSection('contract'); toggleContractDropdown()">
            <span class="nav-icon">📋</span>
            <span class="nav-text">Contract</span>
            <span class="dropdown-arrow" :class="{ rotated: contractDropdownOpen }">▼</span>
          </div>
          <div class="dropdown-menu" v-if="contractDropdownOpen">
            <div class="dropdown-item" @click="navigateToPage('/contracts')">
              <span class="dropdown-icon">📄</span>
              <span class="dropdown-text">All Contracts</span>
            </div>
            <div class="dropdown-item" @click="navigateToPage('/contracts/new')">
              <span class="dropdown-icon">✏️</span>
              <span class="dropdown-text">Create Contract</span>
            </div>
            <div class="dropdown-item" @click="navigateToPage('/vendors')">
              <span class="dropdown-icon">🏢</span>
              <span class="dropdown-text">Vendor Contracts</span>
            </div>
            <div class="dropdown-item" @click="navigateToPage('/my-contract-approvals')">
              <span class="dropdown-icon">✅</span>
              <span class="dropdown-text">My Approvals</span>
            </div>
            <div class="dropdown-item" @click="navigateToPage('/audit/dashboard')">
              <span class="dropdown-icon">🔍</span>
              <span class="dropdown-text">Audit Dashboard</span>
            </div>
            <div class="dropdown-item" @click="navigateToPage('/archive')">
              <span class="dropdown-icon">📦</span>
              <span class="dropdown-text">Archive</span>
            </div>
            <div class="dropdown-item" @click="navigateToPage('/search')">
              <span class="dropdown-icon">🔎</span>
              <span class="dropdown-text">Search</span>
            </div>
            <div class="dropdown-item" @click="navigateToPage('/analytics')">
              <span class="dropdown-icon">📊</span>
              <span class="dropdown-text">Analytics</span>
            </div>
            <div class="dropdown-item" @click="navigateToPage('/contract-kpi-dashboard')">
              <span class="dropdown-icon">📈</span>
              <span class="dropdown-text">KPI Dashboard</span>
            </div>
          </div>
        </div>
        <div class="nav-item" :class="{ active: activeSection === 'vendor' }" @click="setActiveSection('vendor')">
          <span class="nav-icon">🏢</span>
          <span class="nav-text">Vendor</span>
        </div>
        <div class="nav-item" :class="{ active: activeSection === 'audit' }" @click="setActiveSection('audit')">
          <span class="nav-icon">🔍</span>
          <span class="nav-text">Audit</span>
        </div>
      </div>
    </div>

    <!-- Welcome Section -->
    <div class="welcome-section">
      <h1>🎉 Welcome to Contract Management System</h1>
      <p>Your Enterprise Contract Lifecycle Management Platform</p>
      <div class="welcome-stats">
        <div class="stat-card">
          <h3>Total Contracts</h3>
          <p class="stat-number">{{ contractStats.total || 0 }}</p>
        </div>
        <div class="stat-card">
          <h3>Active Contracts</h3>
          <p class="stat-number">{{ contractStats.active || 0 }}</p>
        </div>
        <div class="stat-card">
          <h3>Pending Approvals</h3>
          <p class="stat-number">{{ contractStats.pending || 0 }}</p>
        </div>
        <div class="stat-card">
          <h3>Expiring Soon</h3>
          <p class="stat-number">{{ contractStats.expiring || 0 }}</p>
        </div>
      </div>
    </div>

    <!-- Quick Actions -->
    <div class="quick-actions-section">
      <h2>🚀 Quick Actions</h2>
      <div class="actions-grid">
        <button class="action-button" @click="navigateToPage('/contracts/new')">
          <span class="action-icon">✏️</span>
          <span class="action-text">Create New Contract</span>
        </button>
        <button class="action-button" @click="navigateToPage('/vendors')">
          <span class="action-icon">🏢</span>
          <span class="action-text">Manage Vendors</span>
        </button>
        <button class="action-button" @click="navigateToPage('/audit/create')">
          <span class="action-icon">🔍</span>
          <span class="action-text">Start Audit</span>
        </button>
        <button class="action-button" @click="navigateToPage('/analytics')">
          <span class="action-icon">📊</span>
          <span class="action-text">View Analytics</span>
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import { mapGetters } from 'vuex'

export default {
  name: 'DashboardView',
  
  data() {
    return {
      activeSection: 'dashboard',
      contractDropdownOpen: false,
      contractStats: {
        total: 124,
        active: 89,
        pending: 15,
        expiring: 8
      }
    }
  },
  
  computed: {
    ...mapGetters('auth', ['currentUser', 'isAuthenticated'])
  },
  
  methods: {
    setActiveSection(section) {
      this.activeSection = section
      console.log(`Active section changed to: ${section}`)
    },
    
    toggleContractDropdown() {
      this.contractDropdownOpen = !this.contractDropdownOpen
    },
    
    closeContractDropdown() {
      this.contractDropdownOpen = false
    },
    
    navigateToPage(route) {
      console.log(`🎯 Dashboard: Attempting to navigate to ${route}`)
      this.closeContractDropdown()
      
      this.$router.push(route).then(() => {
        console.log(`✅ Dashboard: Successfully navigated to ${route}`)
      }).catch(error => {
        console.error(`❌ Dashboard: Navigation failed to ${route}:`, error)
      })
    }
  },
  
  async mounted() {
    // Fetch contract stats when component mounts
    try {
      // You can fetch real stats here once the API is fully integrated
      console.log('Dashboard mounted, current user:', this.currentUser)
    } catch (error) {
      console.error('Error loading dashboard:', error)
    }
  }
}
</script>

<style scoped>
.dashboard-content {
  padding: 2rem;
  background: white;
  min-height: 100vh;
}

.contract-nav-section {
  margin-bottom: 2rem;
  padding: 1.5rem;
  background: #f8f9fa;
  border-radius: 12px;
  border: 1px solid #e0e0e0;
}

.contract-nav-section h2 {
  margin: 0 0 1rem 0;
  color: #333;
  font-size: 1.3rem;
  font-weight: 600;
}

.nav-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
}

.nav-item {
  display: flex;
  align-items: center;
  padding: 1rem 1.5rem;
  cursor: pointer;
  transition: all 0.3s ease;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  background: white;
  position: relative;
}

.nav-item.contract-item {
  flex-direction: column;
  align-items: stretch;
  padding: 0;
}

.nav-item-header {
  display: flex;
  align-items: center;
  padding: 1rem 1.5rem;
  cursor: pointer;
  transition: all 0.3s ease;
  position: relative;
  border-radius: 8px;
}

.contract-item:hover .nav-item-header {
  background: rgba(0, 123, 255, 0.1);
}

.contract-item.active .nav-item-header {
  background: rgba(0, 123, 255, 0.15);
}

.nav-item:hover {
  background: rgba(0, 123, 255, 0.1);
  border-color: rgba(0, 123, 255, 0.3);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 123, 255, 0.15);
}

.nav-item.active {
  background: rgba(0, 123, 255, 0.15);
  border-color: #007bff;
}

.nav-icon {
  font-size: 1.2rem;
  margin-right: 0.75rem;
  width: 24px;
  text-align: center;
}

.nav-text {
  font-weight: 500;
  color: #333;
  font-size: 1rem;
}

.dropdown-arrow {
  margin-left: auto;
  font-size: 0.8rem;
  transition: transform 0.3s ease;
  color: #666;
}

.dropdown-arrow.rotated {
  transform: rotate(180deg);
}

.dropdown-menu {
  background: white;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  margin-top: 0.5rem;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  animation: slideDown 0.2s ease-out;
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  z-index: 1000;
}

.dropdown-item {
  display: flex;
  align-items: center;
  padding: 0.75rem 1.5rem;
  cursor: pointer;
  transition: all 0.2s ease;
  border-bottom: 1px solid #f0f0f0;
}

.dropdown-item:last-child {
  border-bottom: none;
}

.dropdown-item:hover {
  background: rgba(0, 123, 255, 0.1);
}

.dropdown-icon {
  font-size: 1rem;
  margin-right: 0.75rem;
  width: 20px;
  text-align: center;
}

.dropdown-text {
  font-weight: 400;
  color: #555;
  font-size: 0.9rem;
}

@keyframes slideDown {
  from {
    opacity: 0;
    max-height: 0;
    overflow: hidden;
  }
  to {
    opacity: 1;
    max-height: 400px;
    overflow: visible;
  }
}

.welcome-section {
  text-align: center;
  padding: 3rem 2rem;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 12px;
  color: white;
  margin-bottom: 2rem;
}

.welcome-section h1 {
  color: white;
  font-size: 2.5rem;
  margin-bottom: 0.5rem;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
}

.welcome-section p {
  font-size: 1.2rem;
  opacity: 0.9;
  margin: 0 0 2rem 0;
}

.welcome-stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
  margin-top: 2rem;
}

.stat-card {
  background: rgba(255, 255, 255, 0.1);
  padding: 1.5rem;
  border-radius: 8px;
  backdrop-filter: blur(10px);
}

.stat-card h3 {
  font-size: 0.9rem;
  margin: 0 0 0.5rem 0;
  opacity: 0.8;
}

.stat-number {
  font-size: 2rem;
  font-weight: bold;
  margin: 0;
}

.quick-actions-section {
  padding: 2rem;
  background: #f8f9fa;
  border-radius: 12px;
  border: 1px solid #e0e0e0;
}

.quick-actions-section h2 {
  margin: 0 0 1.5rem 0;
  color: #333;
  font-size: 1.3rem;
  font-weight: 600;
}

.actions-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1rem;
}

.action-button {
  display: flex;
  align-items: center;
  padding: 1.5rem;
  background: white;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
  text-align: left;
}

.action-button:hover {
  background: rgba(0, 123, 255, 0.1);
  border-color: rgba(0, 123, 255, 0.3);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 123, 255, 0.15);
}

.action-icon {
  font-size: 1.5rem;
  margin-right: 1rem;
  width: 32px;
  text-align: center;
}

.action-text {
  font-weight: 500;
  color: #333;
  font-size: 1rem;
}

@media (max-width: 768px) {
  .dashboard-content {
    padding: 1rem;
  }
  
  .nav-grid {
    grid-template-columns: 1fr;
  }
  
  .contract-nav-section {
    padding: 1rem;
  }
  
  .welcome-section {
    padding: 2rem 1rem;
  }
  
  .welcome-section h1 {
    font-size: 2rem;
  }
  
  .welcome-stats {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .actions-grid {
    grid-template-columns: 1fr;
  }
}
</style>