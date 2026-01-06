<template>
  <div class="vendor_min-h-screen vendor_bg-background">
    <!-- Header -->
    <header class="vendor_border-b vendor_bg-card">
      <div class="vendor_px-6 vendor_py-4">
        <div class="vendor_flex vendor_items-center vendor_justify-between">
          <div class="vendor_flex vendor_items-center vendor_gap-4">
            <div class="vendor_flex vendor_items-center vendor_gap-2">
              <svg class="vendor_h-8 vendor_w-8 vendor_text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
              </svg>
              <h1 class="vendor_text-2xl vendor_font-bold vendor_text-foreground">VendorSecure</h1>
            </div>
          </div>
          <div class="vendor_flex vendor_items-center vendor_gap-4">
            <span class="vendor_text-sm vendor_text-muted-foreground">
              Welcome, {{ userInfo?.username || 'User' }}
            </span>
            <button 
              @click="handleLogout" 
              class="vendor_btn vendor_btn-outline vendor_btn-sm"
              :disabled="logoutLoading"
            >
              <svg class="vendor_h-4 vendor_w-4 vendor_mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
              </svg>
              {{ logoutLoading ? 'Logging out...' : 'Logout' }}
            </button>
          </div>
        </div>
      </div>
    </header>

    <div class="vendor_flex">
      <!-- Sidebar -->
      <aside class="vendor_w-64 vendor_border-r vendor_bg-card" style="height: calc(100vh - 73px);">
        <nav class="vendor_p-4 vendor_space-y-2">
          <div 
            v-for="vendor_item in vendor_navigationItems" 
            :key="vendor_item.id"
          >
            <template v-if="vendor_item.children && vendor_item.children.length">
              <!-- Main dropdown header -->
              <div 
                class="vendor_sidebar-link vendor_sidebar-parent vendor_cursor-pointer"
                @click="toggleDropdown(vendor_item.id)"
              >
                <span class="vendor_sidebar-icon" v-html="vendor_item.icon"></span>
                <span class="vendor_sidebar-text">{{ vendor_item.label }}</span>
                <svg 
                  class="vendor_h-4 vendor_w-4 vendor_ml-auto vendor_transition-transform"
                  :class="{ 'vendor_rotate-180': isDropdownExpanded(vendor_item.id) }"
                  fill="none" 
                  viewBox="0 0 24 24" 
                  stroke="currentColor"
                >
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
                </svg>
              </div>
              
              <!-- Dropdown content -->
              <div 
                v-show="isDropdownExpanded(vendor_item.id)"
                class="vendor_ml-4 vendor_space-y-1"
              >
                <template v-for="child in vendor_item.children" :key="child.id">
                  <!-- If child has its own children (nested dropdown) -->
                  <template v-if="child.children && child.children.length">
                    <div 
                      class="vendor_sidebar-link vendor_sidebar-parent vendor_cursor-pointer vendor_sidebar-sub-link"
                      @click="toggleDropdown(child.id)"
                    >
                      <span class="vendor_sidebar-icon" v-html="child.icon"></span>
                      <span class="vendor_sidebar-text">{{ child.label }}</span>
                      <svg 
                        class="vendor_h-4 vendor_w-4 vendor_ml-auto vendor_transition-transform"
                        :class="{ 'vendor_rotate-180': isDropdownExpanded(child.id) }"
                        fill="none" 
                        viewBox="0 0 24 24" 
                        stroke="currentColor"
                      >
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
                      </svg>
                    </div>
                    <div 
                      v-show="isDropdownExpanded(child.id)"
                      class="vendor_ml-4 vendor_space-y-1"
                    >
                      <router-link 
                        v-for="grandchild in child.children"
                        :key="grandchild.id"
                        :to="grandchild.path"
                        class="vendor_sidebar-link vendor_sidebar-sub-link"
                        :class="{ 'vendor_sidebar-link-active': $route.path === grandchild.path }"
                      >
                        <span class="vendor_sidebar-icon" v-html="grandchild.icon"></span>
                        <span class="vendor_sidebar-text">{{ grandchild.label }}</span>
                      </router-link>
                    </div>
                  </template>
                  <!-- If child is a direct link -->
                  <template v-else>
                    <router-link 
                      :to="child.path"
                      class="vendor_sidebar-link vendor_sidebar-sub-link"
                      :class="{ 'vendor_sidebar-link-active': $route.path === child.path }"
                    >
                      <span class="vendor_sidebar-icon" v-html="child.icon"></span>
                      <span class="vendor_sidebar-text">{{ child.label }}</span>
                    </router-link>
                  </template>
                </template>
              </div>
            </template>
            <template v-else>
              <router-link 
                :to="vendor_item.path"
                class="vendor_sidebar-link"
                :class="{ 'vendor_sidebar-link-active': $route.path === vendor_item.path }"
              >
                <span class="vendor_sidebar-icon" v-html="vendor_item.icon"></span>
                <span class="vendor_sidebar-text">{{ vendor_item.label }}</span>
              </router-link>
            </template>
          </div>
        </nav>
      </aside>

      <!-- Main Content -->
      <main class="vendor_flex-1 vendor_p-6">
        <slot />
      </main>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth_vendor'

const router = useRouter()
const authStore = useAuthStore()
const logoutLoading = ref(false)

// Make userInfo reactive
const userInfo = computed(() => authStore.userInfo)

// Dropdown state management
const expandedDropdowns = ref(new Set())

const toggleDropdown = (itemId) => {
  if (expandedDropdowns.value.has(itemId)) {
    expandedDropdowns.value.delete(itemId)
  } else {
    expandedDropdowns.value.add(itemId)
  }
}

const isDropdownExpanded = (itemId) => {
  return expandedDropdowns.value.has(itemId)
}

const handleLogout = async () => {
  logoutLoading.value = true
  try {
    await authStore.logout()
    // No redirect needed - user stays logged in with hardcoded user
  } catch (error) {
    console.error('Logout error:', error)
  } finally {
    logoutLoading.value = false
  }
}

const vendor_navigationItems = [
  { 
    id: "vendor_management_integration", 
    label: "Vendor Management and Integration", 
    icon: `<svg class="vendor_h-4 vendor_w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
    </svg>`,
    children: [
      { 
        id: "vendor_dashboard", 
        label: "Dashboard", 
        path: "/dashboard",
        icon: `<svg class="vendor_h-4 vendor_w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2H5a2 2 0 00-2-2z" />
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 5a2 2 0 012-2h4a2 2 0 012 2v14l-5-3-5 3V5z" />
        </svg>`
      },
      { 
        id: "vendor_kpi-dashboard", 
        label: "KPI Dashboard", 
        path: "/kpi-dashboard",
        icon: `<svg class="vendor_h-4 vendor_w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
        </svg>`
      },
      { 
        id: "vendor_vendor-registration", 
        label: "Vendor Registration", 
        path: "/vendor-registration",
        icon: `<svg class="vendor_h-4 vendor_w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M18 9v3m0 0v3m0-3h3m-3 0h-3m-2-5a4 4 0 11-8 0 4 4 0 018 0zM3 20a6 6 0 0112 0v1H3v-1z" />
        </svg>`
      },
      { 
        id: "vendor_verification", 
        label: "External Screening", 
        path: "/verification",
        icon: `<svg class="vendor_h-4 vendor_w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
        </svg>`
      },
      { 
        id: "vendor_questionnaire-management", 
        label: "Questionnaire Management", 
        icon: `<svg class="vendor_h-4 vendor_w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
        </svg>`,
        children: [
          {
            id: "vendor_questionnaire_builder",
            label: "Builder",
            path: "/questionnaire",
            icon: `<svg class="vendor_h-4 vendor_w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
            </svg>`
          },
          {
            id: "vendor_questionnaire_assignment",
            label: "Assignment",
            path: "/questionnaire-assignment",
            icon: `<svg class="vendor_h-4 vendor_w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
            </svg>`
          },
          {
            id: "vendor_questionnaire_response",
            label: "Response",
            path: "/questionnaire-response",
            icon: `<svg class="vendor_h-4 vendor_w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
            </svg>`
          }
        ]
      },
      { 
        id: "vendor_risk-scoring", 
        label: "Risk Scoring", 
        path: "/risk-scoring",
        icon: `<svg class="vendor_h-4 vendor_w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
        </svg>`
      },
      { 
        id: "vendor_lifecycle", 
        label: "Lifecycle Tracker", 
        path: "/lifecycle",
        icon: `<svg class="vendor_h-4 vendor_w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
        </svg>`
      },
      { 
        id: "vendor_approval", 
        label: "Vendor Approval", 
        icon: `<svg class="vendor_h-4 vendor_w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>`,
        children: [
          {
            id: "vendor_approval_dashboard",
            label: "Approval Dashboard",
            path: "/approval-dashboard",
            icon: `<svg class="vendor_h-4 vendor_w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4" />
            </svg>`
          },
          {
            id: "vendor_approval_workflow_creator",
            label: "Create Workflow",
            path: "/vendor-approval-workflow-creator",
            icon: `<svg class="vendor_h-4 vendor_w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
            </svg>`
          },
          {
            id: "vendor_my_approvals",
            label: "My approvals",
            path: "/my-approvals",
            icon: `<svg class="vendor_h-4 vendor_w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
            </svg>`
          },
          {
            id: "vendor_all_approvals",
            label: "All Approvals",
            path: "/all-approvals",
            icon: `<svg class="vendor_h-4 vendor_w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
            </svg>`
          },
        ]
      }
    ]
  }
]
</script>

<style scoped>
.vendor_sidebar-link {
  width: 100%;
  justify-content: flex-start;
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.5rem 0.75rem;
  font-size: 0.875rem;
  font-weight: 500;
  border-radius: 0.375rem;
  transition: all 0.15s;
  color: hsl(var(--vendor_muted-foreground));
  text-decoration: none;
}

.vendor_sidebar-link:hover {
  color: hsl(var(--vendor_foreground));
  background-color: hsl(var(--vendor_accent));
}

.vendor_sidebar-link-active {
  background-color: hsl(var(--vendor_primary));
  color: hsl(var(--vendor_primary-foreground));
}

.vendor_sidebar-link-active:hover {
  background-color: hsl(var(--vendor_primary));
  color: hsl(var(--vendor_primary-foreground));
}

.vendor_sidebar-icon {
  display: flex;
  align-items: center;
  justify-content: center;
}

.vendor_sidebar-text {
  flex: 1;
}

/* Parent (non-clickable) group label */
.vendor_sidebar-parent {
  cursor: default;
}

/* Sub-link styling */
.vendor_sidebar-sub-link {
  padding-left: 2rem;
}

/* Dropdown arrow rotation */
.vendor_rotate-180 {
  transform: rotate(180deg);
}

/* Cursor pointer for clickable dropdown headers */
.vendor_cursor-pointer {
  cursor: pointer;
}

/* Transition for smooth dropdown animations */
.vendor_transition-transform {
  transition: transform 0.2s ease-in-out;
}
</style>
