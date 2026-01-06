<template>
  <aside :style="{
    width: isCollapsed ? '56px' : '256px',
    borderRight: '1px solid #e5e7eb',
    background: 'white',
    boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1)',
    transition: 'all 0.3s ease',
    height: '100vh',
    position: 'fixed',
    left: 0,
    top: 0,
    zIndex: 1000,
    display: 'flex',
    flexDirection: 'column',
    overflow: 'hidden'
  }">
    <div style="padding: 1rem;">
      <div style="display: flex; align-items: center; gap: 0.5rem;">
        <div style="width: 32px; height: 32px; background: #3b82f6; border-radius: 6px; display: flex; align-items: center; justify-content: center; color: white;">
          📄
        </div>
        <div v-if="!isCollapsed">
          <h1 style="font-size: 1.125rem; font-weight: 600; color: #111827; margin: 0;">ContractHub</h1>
          <p style="font-size: 0.75rem; color: #6b7280; margin: 0;">Management System</p>
        </div>
      </div>
    </div>

    <!-- Scrollable navigation container -->
    <div class="scrollable-nav" style="flex: 1; overflow-y: auto; overflow-x: hidden; padding: 0 0.5rem;">
      <nav>
        <div style="margin-bottom: 1rem;">
          <ul style="margin: 0; padding: 0; list-style: none;">
            <!-- Contract Dropdown -->
            <li style="margin-bottom: 0.25rem;">
              <div style="position: relative;">
                <div 
                  @click.stop="toggleContractDropdown"
                  :style="getLinkStyle('/contract')"
                  style="cursor: pointer; display: flex; align-items: center; justify-content: space-between; padding: 0.5rem 0.75rem; font-size: 0.875rem;"
                  @mouseenter="hoveredItem = '/contract'"
                  @mouseleave="hoveredItem = null"
                >
                  <div style="display: flex; align-items: center;">
                    <span style="width: 16px; height: 16px; display: inline-block; margin-right: 0.5rem;">{{ getIcon('Contract') }}</span>
                    <span v-if="!isCollapsed">Contract</span>
                  </div>
                  <span v-if="!isCollapsed" style="font-size: 0.75rem; transition: transform 0.2s ease;" :style="{ transform: contractDropdownOpen ? 'rotate(180deg)' : 'rotate(0deg)' }">▼</span>
                </div>
                <!-- Contract Dropdown -->
                <div v-if="contractDropdownOpen && !isCollapsed" style="margin-left: 1rem; margin-top: 0.25rem; background: #e5e7eb; border-radius: 6px; padding: 0.25rem 0;">
                  <div v-for="contractItem in contractItems" :key="contractItem.title" style="margin-bottom: 0.125rem;">
                    <!-- Audit sub-dropdown within Contract -->
                    <div v-if="contractItem.isDropdown" style="position: relative;">
                      <div 
                        @click.stop="toggleAuditDropdown"
                        :style="getLinkStyle('/audit')"
                        style="cursor: pointer; display: flex; align-items: center; justify-content: space-between; padding: 0.5rem 0.75rem; font-size: 0.875rem;"
                        @mouseenter="hoveredItem = '/audit'"
                        @mouseleave="hoveredItem = null"
                      >
                        <div style="display: flex; align-items: center;">
                          <span style="width: 14px; height: 14px; display: inline-block; margin-right: 0.5rem;">{{ getIcon('Audit') }}</span>
                          Audit
                        </div>
                        <span style="font-size: 0.75rem; transition: transform 0.2s ease;" :style="{ transform: auditDropdownOpen ? 'rotate(180deg)' : 'rotate(0deg)' }">▼</span>
                      </div>
                      <!-- Audit Sub-Dropdown -->
                      <div v-if="auditDropdownOpen" style="margin-left: 1rem; margin-top: 0.25rem; background: #f3f4f6; border-radius: 6px; padding: 0.25rem 0;">
                        <div v-for="auditItem in auditItems" :key="auditItem.title" style="margin-bottom: 0.125rem;">
                          <RouterLink 
                            :to="auditItem.url" 
                            :style="getLinkStyle(auditItem.url)"
                            @mouseenter="hoveredItem = auditItem.url"
                            @mouseleave="hoveredItem = null"
                            style="padding: 0.5rem 0.75rem; font-size: 0.875rem;"
                          >
                            <span style="width: 12px; height: 12px; display: inline-block; margin-right: 0.5rem;">{{ getIcon(auditItem.title) }}</span>
                            {{ auditItem.title }}
                          </RouterLink>
                        </div>
                      </div>
                    </div>
                    <!-- Regular contract items -->
                    <RouterLink 
                      v-else
                      :to="contractItem.url" 
                      :style="getLinkStyle(contractItem.url)"
                      @mouseenter="hoveredItem = contractItem.url"
                      @mouseleave="hoveredItem = null"
                      style="padding: 0.5rem 0.75rem; font-size: 0.875rem;"
                    >
                      <span style="width: 14px; height: 14px; display: inline-block; margin-right: 0.5rem;">{{ getIcon(contractItem.title) }}</span>
                      {{ contractItem.title }}
                    </RouterLink>
                  </div>
                </div>
              </div>
            </li>

          </ul>
        </div>

        <div style="margin-top: 1.5rem;">
          <p style="padding: 0 0.5rem; font-size: 0.75rem; text-transform: uppercase; color: #6b7280; font-weight: 500; margin: 0 0 0.5rem 0;">Administration</p>
          <ul style="margin: 0; padding: 0; list-style: none;">
            <li v-for="item in adminItems" :key="item.title" style="margin-bottom: 0.25rem;">
              <RouterLink 
                :to="item.url" 
                :style="getLinkStyle(item.url)"
                @mouseenter="hoveredItem = item.url"
                @mouseleave="hoveredItem = null"
              >
                <span style="width: 16px; height: 16px; display: inline-block; margin-right: 0.5rem;">{{ getIcon(item.title) }}</span>
                <span v-if="!isCollapsed">{{ item.title }}</span>
              </RouterLink>
            </li>
          </ul>
        </div>
      </nav>
    </div>

    <!-- Collapse Toggle Button -->
    <div style="position: absolute; bottom: 1rem; right: 1rem;">
      <button 
        @click="toggleCollapse"
        style="padding: 0.5rem; border-radius: 6px; background: transparent; border: none; color: #6b7280; cursor: pointer; transition: all 0.2s ease;"
        :title="isCollapsed ? 'Expand Sidebar' : 'Collapse Sidebar'"
        @mouseenter="$event.target.style.background = '#f3f4f6'"
        @mouseleave="$event.target.style.background = 'transparent'"
      >
        {{ isCollapsed ? '→' : '←' }}
      </button>
    </div>
  </aside>
</template>

<script setup>
import { ref } from 'vue'
import { RouterLink, useRoute } from 'vue-router'

const route = useRoute()
const isCollapsed = ref(false)
const hoveredItem = ref(null)
const contractDropdownOpen = ref(false)
const auditDropdownOpen = ref(false)


const contractItems = [
  { title: 'Contract Dashboard', url: '/contractdashboard' },
  { title: 'All Contracts', url: '/contracts' },
  { title: 'Create Contract', url: '/contracts/new' },
  { title: 'Vendor Contracts', url: '/vendors' },
  { title: 'Approval Assignment', url: '/contract-approval-assignment' },
  { title: 'My Approvals', url: '/my-contract-approvals' },
  { title: 'Archive', url: '/archive' },
  { title: 'Search', url: '/search' },
  { title: 'Analytics', url: '/analytics' },
  { title: 'KPI Dashboard', url: '/contract-kpi-dashboard' },
  { title: 'Audit', url: '/audit', isDropdown: true },
]

const auditItems = [
  { title: 'Audit Dashboard', url: '/audit/dashboard' },
  { title: 'All Audits', url: '/audit/all' },
  { title: 'Create Audit', url: '/audit/create' },
  { title: 'Audit Reports', url: '/audit/reports' },
]

const adminItems = [
  { title: 'Settings', url: '/settings' }
]

// Check if a route is active (matches the React version logic)
const isActive = (path) => {
  if (path === '/') {
    return route.path === path
  }
  return route.path.startsWith(path)
}

// Get icon emoji for navigation items
const getIcon = (title) => {
  const icons = {
    'Contract': '📋',
    'Contract Dashboard': '📊',
    'All Contracts': '📄',
    'Create Contract': '✏️',
    'Vendor Contracts': '🏢',
    'Approval Assignment': '👥',
    'My Approvals': '✅',
    'Archive': '📦',
    'Search': '🔎',
    'Analytics': '📊',
    'KPI Dashboard': '📈',
    'Audit': '🔍',
    'Audit Dashboard': '📊',
    'All Audits': '📋',
    'Create Audit': '➕',
    'Audit Reports': '📈',
    'Settings': '⚙️'
  }
  return icons[title] || '📄'
}

// Get link styles
const getLinkStyle = (url) => {
  const isActiveLink = isActive(url)
  const isHovered = hoveredItem.value === url
  
  return {
    display: 'flex',
    alignItems: 'center',
    gap: '0.5rem',
    padding: '0.5rem 0.75rem',
    borderRadius: '6px',
    transition: 'all 0.2s ease',
    textDecoration: 'none',
    color: isActiveLink ? 'white' : '#374151',
    background: isActiveLink ? '#2563eb' : (isHovered ? '#f3f4f6' : 'transparent'),
    fontWeight: isActiveLink ? '500' : '400'
  }
}

// Toggle sidebar collapse
const toggleCollapse = () => {
  isCollapsed.value = !isCollapsed.value
}


// Toggle contract dropdown
const toggleContractDropdown = () => {
  contractDropdownOpen.value = !contractDropdownOpen.value
}

// Toggle audit dropdown
const toggleAuditDropdown = () => {
  auditDropdownOpen.value = !auditDropdownOpen.value
}
</script>

<style scoped>
/* Custom scrollbar styling for the navigation */
.scrollable-nav::-webkit-scrollbar {
  width: 6px;
}

.scrollable-nav::-webkit-scrollbar-track {
  background: transparent;
}

.scrollable-nav::-webkit-scrollbar-thumb {
  background: #d1d5db;
  border-radius: 3px;
}

.scrollable-nav::-webkit-scrollbar-thumb:hover {
  background: #9ca3af;
}

/* For Firefox */
.scrollable-nav {
  scrollbar-width: thin;
  scrollbar-color: #d1d5db transparent;
}
</style>