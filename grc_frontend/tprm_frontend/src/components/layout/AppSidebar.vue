<template>
  <aside :class="['bg-white shadow-lg h-screen fixed left-0 top-0 z-50 hidden sm:block transition-all duration-300', isCollapsed ? 'w-16' : 'w-64']" :style="{ width: isCollapsed ? '4.28rem' : '17.00rem' }">
    <div class="h-full flex flex-col">
      <div class="p-6 pb-4 flex items-center justify-between">
        <h2 v-if="!isCollapsed" class="text-lg font-semibold text-gray-900">TPRM</h2>
        <button 
          @click="toggleSidebar"
          class="p-2 rounded-md hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <ChevronLeft v-if="!isCollapsed" class="h-5 w-5 text-gray-600 chevron-arrow" />
          <ChevronRight v-else class="h-5 w-5 text-gray-600 chevron-arrow" />
        </button>
      </div>
      <div class="flex-1 overflow-y-auto px-6 pt-2">
        <nav class="space-y-2">
        <div v-for="item in mainItems" :key="item.title" class="space-y-1">
          <div v-if="item.subItems" class="space-y-1">
            <button
              @click="toggleExpanded(item.title)"
              class="flex items-center justify-between w-full px-3 py-2 text-sm font-medium text-gray-700 rounded-md hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <div class="flex items-center flex-1 min-w-0">
                <component :is="item.icon" class="h-5 w-5 mr-3 flex-shrink-0" />
                <div v-if="!isCollapsed" class="flex flex-col leading-tight min-w-0">
                  <span v-if="item.title === 'Continuity and Recovery plans management'" class="whitespace-nowrap">Continuity and Recovery</span>
                  <span v-else class="truncate">{{ item.title }}</span>
                  <span v-if="item.title === 'Continuity and Recovery plans management'" class="whitespace-nowrap">plans management</span>
                </div>
              </div>
              <ChevronDown 
                v-if="!isCollapsed"
                :class="['h-4 w-4 transition-transform chevron-arrow flex-shrink-0 ml-2', expandedItems.includes(item.title) ? 'rotate-180' : '']" 
              />
            </button>
            <div v-if="expandedItems.includes(item.title) && !isCollapsed" class="ml-6 space-y-1">
              <div v-for="subItem in item.subItems" :key="subItem.title" class="space-y-1">
                <div v-if="subItem.subItems" class="space-y-1">
                    <!-- Parent category with URL - clickable to navigate -->
          <RouterLink

          v-if="subItem.url"

          :to="subItem.url"

          class="flex items-center justify-between w-full px-3 py-2 text-sm font-medium text-gray-600 rounded-md hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500"

          active-class="bg-blue-50 text-blue-700"

          @click.stop="toggleExpanded(subItem.title)"
          >
          <div class="flex items-center">
          <component :is="subItem.icon" class="h-4 w-4 mr-3" />

            {{ subItem.title }}
          </div>
          <ChevronDown 

            :class="['h-3 w-3 transition-transform chevron-arrow', expandedItems.includes(subItem.title) ? 'rotate-180' : '']" 

          />
          </RouterLink>
          <!-- Parent category without URL - just expandable -->
          <button
            v-else
            @click="toggleExpanded(subItem.title)"
            class="flex items-center justify-between w-full px-3 py-2 text-sm font-medium text-gray-600 rounded-md hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <div class="flex items-center">
              <component :is="subItem.icon" class="h-4 w-4 mr-3" />
              {{ subItem.title }}
            </div>
            <ChevronDown 
              :class="['h-3 w-3 transition-transform chevron-arrow', expandedItems.includes(subItem.title) ? 'rotate-180' : '']" 
            />
          </button>
                  <div v-if="expandedItems.includes(subItem.title)" class="ml-6 space-y-1">
                    <RouterLink
                      v-for="subSubItem in subItem.subItems"
                      :key="subSubItem.title"
                      :to="subSubItem.url"
                      class="block px-3 py-2 text-sm text-gray-500 rounded-md hover:bg-gray-100 hover:text-gray-700"
                      active-class="bg-blue-50 text-blue-700"
                    >
                    <component :is="subSubItem.icon" class="h-4 w-4 mr-3" />
                    {{ subSubItem.title }}
                    </RouterLink>
                  </div>
                </div>
                <RouterLink
                  v-else
                  :to="subItem.url"
                  class="flex items-center px-3 py-2 text-sm font-medium text-gray-600 rounded-md hover:bg-gray-100 hover:text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  active-class="bg-blue-50 text-blue-700"
                >
                  <component :is="subItem.icon" class="h-4 w-4 mr-3" />
                  {{ subItem.title }}
                </RouterLink>
              </div>
            </div>
          </div>
          <RouterLink
            v-else
            :to="item.url"
            class="flex items-center px-3 py-2 text-sm font-medium text-gray-700 rounded-md hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
            active-class="bg-blue-50 text-blue-700"
            :title="isCollapsed ? item.title : ''"
          >
            <component :is="item.icon" class="h-5 w-5 mr-3 flex-shrink-0" />
            <span v-if="!isCollapsed" class="truncate">{{ item.title }}</span>
          </RouterLink>
        </div>
        </nav>
      </div>
      
      <div class="p-6 pt-4 border-t border-gray-200 bg-white">
        <!-- User Profile Section -->
        <div v-if="!isCollapsed" class="mb-4 pb-4 border-b border-gray-200">
          <div class="flex items-center px-3 py-2">
            <User class="h-5 w-5 mr-3 flex-shrink-0 text-gray-600" />
            <div class="flex-1 min-w-0">
              <p class="text-sm font-medium text-gray-900 truncate">{{ username }}</p>
              <p class="text-xs text-gray-500 truncate">{{ userEmail || 'User' }}</p>
            </div>
          </div>
        </div>
        
        <h3 v-if="!isCollapsed" class="text-sm font-medium text-gray-500 uppercase tracking-wider mb-3">Management</h3>
        <nav class="space-y-1">
          <RouterLink
            v-for="item in managementItems"
            :key="item.title"
            :to="item.url"
            class="flex items-center px-3 py-2 text-sm font-medium text-gray-700 rounded-md hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500 relative"
            active-class="bg-blue-50 text-blue-700"
            :title="isCollapsed ? item.title : ''"
          >
            <div class="relative flex items-center">
              <component :is="item.icon" class="h-5 w-5 mr-3 flex-shrink-0" />
              <!-- Notification badge -->
              <span 
                v-if="item.title === 'Notifications' && unreadCount > 0"
                class="absolute -top-1 -right-1 flex items-center justify-center min-w-[18px] h-[18px] bg-red-500 text-white text-[10px] font-bold rounded-full px-1"
              >
                {{ unreadCount > 99 ? '99+' : unreadCount }}
              </span>
            </div>
            <span v-if="!isCollapsed" class="truncate">{{ item.title }}</span>
          </RouterLink>
        </nav>
      </div>
    </div>
  </aside>
</template>

<script setup>
import { ref } from 'vue'
import { RouterLink } from 'vue-router'
import { 
  BarChart3, 
  FileText, 
  Plus, 
  Target, 
  ChevronRight,
  ChevronLeft,
  ChevronDown,
  ChevronUp,
  Bell,
  Activity,
  Zap,
  CheckSquare,
  Eye,
  User,
  ClipboardCheck,
  Upload,
  Search,
  Building2,
  Shield,
  Users,
  FileCheck,
  Layers,
  Workflow,
  RefreshCw,
  GitCompare,
  Edit3
} from 'lucide-vue-next'
import { useNotificationCount } from '@/composables/useNotificationCount'
import { computed, onMounted } from 'vue'

const expandedItems = ref([])
const isCollapsed = ref(false)

// Get unread notification count
const { unreadCount } = useNotificationCount()

// Username and email
const username = ref('User')
const userEmail = ref('')

// Fetch username from localStorage
const fetchUsername = () => {
  try {
    const userStr = localStorage.getItem('current_user') || localStorage.getItem('user')
    if (userStr) {
      const user = JSON.parse(userStr)
      username.value = user.UserName || user.username || user.full_name || user.first_name + ' ' + (user.last_name || '') || 'User'
      userEmail.value = user.email || user.Email || ''
    } else {
      // Try other sources
      const storedFullName = localStorage.getItem('fullName')
      const storedUsername = localStorage.getItem('username')
      if (storedFullName && storedFullName !== 'null') {
        username.value = storedFullName
      } else if (storedUsername && storedUsername !== 'null') {
        username.value = storedUsername
      }
    }
  } catch (e) {
    console.error('Error fetching username:', e)
    username.value = 'User'
  }
}

onMounted(() => {
  fetchUsername()
  // Listen for user data updates
  window.addEventListener('userDataUpdated', fetchUsername)
})

const toggleExpanded = (title) => {
  const index = expandedItems.value.indexOf(title)
  if (index > -1) {
    expandedItems.value.splice(index, 1)
  } else {
    expandedItems.value.push(title)
  }
}

const emit = defineEmits(['sidebar-toggle'])

const toggleSidebar = () => {
  isCollapsed.value = !isCollapsed.value
  // Close all expanded items when collapsing
  if (isCollapsed.value) {
    expandedItems.value = []
  }
  // Emit the sidebar state change
  emit('sidebar-toggle', isCollapsed.value)
}

const mainItems = [
  { 
    title: "Home", 
    url: "/", 
    icon: BarChart3
  },
  {
    title: "Global Search",
    url: "/global-search",
    icon: Search
  },
  {
    title: "Questionnaire Templates",
    url: "/questionnaire-templates",
    icon: ClipboardCheck
  },
  {
    title: "RFP Management",
    url: "/rfp-dashboard",
    icon: FileText,
    subItems: [
      {
        title: "Dashboard",
        url: "/rfp-dashboard",
        icon: BarChart3
      },
      {
        title: "Select RFP",
        url: "/rfp-list",
        icon: Search
      },
      {
        title: "Workflow",
        url: "/rfp-workflow",
        icon: Activity
      },
      {
        title: "Evaluation Workflow",
        icon: Workflow,
        subItems: [
          { title: "Workflow Creation", url: "/approval-management", icon: Plus },
          { title: "My Approvals", url: "/my-approvals", icon: User },
          { title: "All Approvals", url: "/all-approvals", icon: CheckSquare },
          { title: "Change Requests", url: "/rfp-approval/change-request-manager", icon: Edit3 },
        ]
      },
      {
        title: "RFP Workflow",
        icon: Layers,
        subItems: [
          { title: "Step 1: RFP Creation", url: "/rfp-creation", icon: FileText },
          { title: "Step 2: RFP Approval", url: "/rfp-approval", icon: CheckSquare },
          { title: "Step 3: Vendor Selection", url: "/rfp-vendor-selection", icon: Users },
          { title: "Step 4: URL Generation", url: "/rfp-url-generation", icon: Zap },
          { title: "Step 5: Evaluation", url: "/rfp-evaluation", icon: ClipboardCheck },
          { title: "Step 6: Comparison", url: "/rfp-comparison", icon: GitCompare },
          { title: "Step 7: Consensus & Award", url: "/rfp-consensus", icon: Target },
        ]
      },
 
      {
        title: "KPI Dashboard",
        url: "/rfp-analytics",
        icon: BarChart3
      },
      {
        title: "Drafts",
        url: "/draft-manager",
        icon: FileText
      },
    ]
  },
  { 
    title: "Vendor Management", 
    url: "/vendor-dashboard", 
    icon: Building2,
    subItems: [
      { 
        title: "Dashboard", 
        url: "/vendor-dashboard", 
        icon: BarChart3
      },
      { 
        title: "KPI Dashboard", 
        url: "/vendor-kpi-dashboard", 
        icon: Target
      },
      { 
        title: "Vendor Registration", 
        url: "/vendor-registration", 
        icon: Plus
      },
      { 
        title: "External Screening", 
        url: "/vendor-verification", 
        icon: Search
      },
      { 
        title: "Questionnaire Management", 
        url: "/vendor-questionnaire", 
        icon: ClipboardCheck,
        subItems: [
          { title: "Builder", url: "/vendor-questionnaire" },
          { title: "Assignment", url: "/vendor-questionnaire-assignment" },
          { title: "Response", url: "/vendor-questionnaire-response" },
        ]
      },
      { 
        title: "Risk Scoring", 
        url: "/vendor-risk-scoring", 
        icon: Shield
      },
      { 
        title: "Lifecycle Tracker", 
        url: "/vendor-lifecycle", 
        icon: Activity
      },
      { 
        title: "Vendor Approval", 
        url: "/vendor-approval-dashboard", 
        icon: CheckSquare,
        subItems: [
          { title: "Approval Dashboard", url: "/vendor-approval-dashboard" },
          { title: "Create Workflow", url: "/vendor-approval-workflow-creator" },
          { title: "My approvals", url: "/vendor-my-approvals" },
          { title: "All Approvals", url: "/vendor-all-approvals" },

        ]
      },
    ]
  },
{ 
    title: "Contract Management", 
    url: "/contractdashboard", 
    icon: FileCheck,
    subItems: [
      { 
        title: "Contract Dashboard", 
        url: "/contractdashboard", 
        icon: BarChart3
      },
      { 
        title: "All Contracts", 
        url: "/contracts", 
        icon: FileText
      },
      { 
        title: "Create Contract", 
        url: "/contracts/new", 
        icon: Plus
      },
      { 
        title: "Vendor Contracts", 
        url: "/vendors", 
        icon: Building2
      },
      { 
        title: "Approval Assignment", 
        url: "/contract-approval-assignment", 
        icon: Users
      },
      { 
        title: "My Approvals", 
        url: "/my-contract-approvals", 
        icon: CheckSquare
      },
      { 
        title: "Archive", 
        url: "/archive", 
        icon: FileText
      },
      { 
        title: "Contract Comparison", 
        url: "/contract-comparison", 
        icon: GitCompare
      },
      { 
        title: "Analytics", 
        url: "/analytics", 
        icon: BarChart3
      },
      { 
        title: "KPI Dashboard", 
        url: "/contract-kpi-dashboard", 
        icon: Target
      },
      { 
        title: "Audit", 
        url: "/audit/dashboard", 
        icon: Eye,
        subItems: [
          { title: "Audit Dashboard", url: "/audit/dashboard" },
          { title: "All Audits", url: "/contract-audit/all" },
          { title: "Create Audit", url: "/contract-audit/create" },
          { title: "Audit Reports", url: "/contract-audit/reports" },
        ]
      },
    ]
  },
  { 
    title: "Service Level Agreement", 
    url: "/dashboard", 
    icon: FileText,
    subItems: [
      { 
        title: "SLA Dashboard", 
        url: "/dashboard", 
        icon: BarChart3,
        subItems: [
          { title: "SLA Overview", url: "/dashboard" },
          { title: "Performance Summary", url: "/performance" },
          { title: "KPI Dashboard", url: "/kpi-dashboard" },
        ]
      },
      { 
        title: "SLA Management", 
        url: "/slas", 
        icon: FileText,
        subItems: [
          { title: "All SLAs", url: "/slas" },
          { title: "Active SLAs", url: "/slas/active" },
          { title: "Expiring SLAs", url: "/slas/expiring" },
        ]
      },
      { 
        title: "Create/Upload SLA", 
        url: "/slas/create", 
        icon: Plus,
        subItems: [
          { title: "Create New SLA", url: "/slas/create" },
        ]
      },
      { 
        title: "Audit Management", 
        url: "/audit", 
        icon: CheckSquare,
        subItems: [
          { title: "Audit Dashboard", url: "/audit" },
          { title: "Create Audit", url: "/audit/create" },
          { title: "My Audits", url: "/audit/my-audits" },
          { title: "Audit Reports", url: "/audit/reports" },
        ]
      },
      { 
        title: "SLA Approvals", 
        url: "/slas/approvals", 
        icon: ClipboardCheck,
        subItems: [
          { title: "My Approvals", url: "/slas/approvals" },
          { title: "Assign Approvals", url: "/slas/approval-assignment" },
        ]
      },
    ]
  },
  
  { 
    title: "Continuity and Recovery plans management", 
    url: "/bcp/vendor-upload", 
    icon: Shield,
    subItems: [
      { 
        title: "Plan Phase", 
        icon: Upload,
        subItems: [
          { title: "Upload Plans", url: "/bcp/vendor-upload" },
          { title: "Plan Submission & OCR", url: "/bcp/plan-submission-ocr" },
          { title: "Plan Evaluation", url: "/bcp/evaluation" },
          { title: "Plan Library", url: "/bcp/library" },
        ]
      },
      { 
        title: "Testing Phase", 
        icon: FileCheck,
        subItems: [
          { title: "Questionnaire Creation", url: "/bcp/questionnaire-workflow" },
          { title: "Questionnaire Review", url: "/bcp/questionnaire-builder" },
          { title: "Questionnaire Library", url: "/bcp/questionnaire-library" },
          { title: "Questionnaire Assignment", url: "/bcp/questionnaire-assignment-workflow" },
          { title: "Questionnaire Answering", url: "/bcp/questionnaire-assignment" },
          // { title: "Testing Library", url: "/bcp/testing-library" },
          { title: "Approval Assignment", url: "/bcp/approval-assignment" },
          { title: "My Approvals", url: "/bcp/my-approvals" },
          // { title: "Vendor Hub", url: "/bcp/vendor-hub" },
        ]
      },
      { 
        title: "Owner Console", 
        icon: BarChart3,
        subItems: [
          { title: "Analytics Dashboard", url: "/bcp/dashboard" },
          { title: "KPI Dashboard", url: "/bcp/kpi-dashboard" },
          { title: "Risk Analytics", url: "/bcp/risk-analytics" },
        ]
      },
    ]
  },
]

const managementItems = [
  { title: "Admin Access", url: "/admin-access", icon: Shield },
  { title: "Quick Access", url: "/quick-access", icon: Zap },
  { title: "Notifications", url: "/notifications", icon: Bell },
  { title: "Renewals", url: "/slas/renew", icon: RefreshCw },
]
</script>

<style scoped>
/* Ensure sidebar takes full height and is properly positioned */
aside {
  min-height: 100vh;
  max-height: 100vh;
}

/* Ensure proper scrolling behavior for the navigation area */
.overflow-y-auto {
  scrollbar-width: thin;
  scrollbar-color: #cbd5e0 transparent;
  -webkit-overflow-scrolling: touch;
}

.overflow-y-auto::-webkit-scrollbar {
  width: 6px;
}

.overflow-y-auto::-webkit-scrollbar-track {
  background: transparent;
}

.overflow-y-auto::-webkit-scrollbar-thumb {
  background-color: #cbd5e0;
  border-radius: 3px;
}

.overflow-y-auto::-webkit-scrollbar-thumb:hover {
  background-color: #a0aec0;
}

/* Ensure flex layout works properly */
.flex-1 {
  flex: 1 1 0%;
  min-height: 0;
}

/* Management section positioning */
.mt-auto {
  margin-top: auto;
}

/* Ensure proper spacing and layout */
nav {
  padding-bottom: 1rem;
}

/* Fix for proper content flow */
aside {
  display: flex;
  flex-direction: column;
}

/* Bold arrow styling */
.font-bold {
  font-weight: 900;
  stroke-width: 2.5;
}

/* Enhanced arrow visibility */
.chevron-arrow {
  stroke-width: 2.5;
  font-weight: 900;
}
</style>
