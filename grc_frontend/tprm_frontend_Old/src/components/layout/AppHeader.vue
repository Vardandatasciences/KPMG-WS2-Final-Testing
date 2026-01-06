<template>
  <header class="bg-white shadow-sm border-b">
    <div class="px-6 py-4">
      <div class="flex items-center justify-between">
        <!-- Left side: Title and Breadcrumb -->
        <div>
          <h1 class="text-2xl font-bold text-gray-900 mb-2">{{ pageTitle }}</h1>
          <nav class="flex items-center space-x-1 text-sm">
            <template v-for="(breadcrumb, index) in breadcrumbs" :key="breadcrumb.name">
              <router-link 
                v-if="breadcrumb.path && index < breadcrumbs.length - 1"
                :to="breadcrumb.path"
                class="text-blue-600 hover:text-blue-800 hover:underline"
              >
                {{ breadcrumb.name }}
              </router-link>
              <span v-else class="text-gray-600">{{ breadcrumb.name }}</span>
              <span v-if="index < breadcrumbs.length - 1" class="text-gray-400">></span>
            </template>
          </nav>
        </div>

        <!-- Right side: Notification and Profile Buttons -->
        <div class="flex items-center space-x-4">
          <div class="relative">
            <Button 
              variant="outline" 
              size="sm" 
              @click="navigateToNotifications"
              class="relative"
            >
              <Bell class="h-4 w-4 mr-2" />
              Notifications
              <!-- Unread Count Badge -->
              <span 
                v-if="unreadCount > 0"
                class="absolute -top-1 -right-1 flex items-center justify-center min-w-[18px] h-[18px] bg-red-500 text-white text-[10px] font-bold rounded-full px-1"
              >
                {{ unreadCount > 99 ? '99+' : unreadCount }}
              </span>
            </Button>
            
            <!-- Notification Popup -->
            <Transition name="notification-popup">
              <div
                v-if="showPopup && currentNotification"
                class="absolute top-full right-0 mt-2 w-96 bg-white rounded-lg shadow-2xl border border-gray-200 z-50 overflow-hidden"
              >
                <div 
                  :class="[
                    'p-4 cursor-pointer hover:bg-gray-50 transition-colors',
                    currentNotification.priority === 'critical' ? 'border-l-4 border-l-red-500' :
                    currentNotification.priority === 'high' ? 'border-l-4 border-l-orange-500' :
                    currentNotification.priority === 'medium' ? 'border-l-4 border-l-yellow-500' :
                    'border-l-4 border-l-green-500'
                  ]"
                  @click="handleNotificationClick"
                >
                  <div class="flex items-start justify-between">
                    <div class="flex items-start space-x-3 flex-1">
                      <div :class="[
                        'p-2 rounded-lg',
                        currentNotification.priority === 'critical' ? 'bg-red-100' :
                        currentNotification.priority === 'high' ? 'bg-orange-100' :
                        currentNotification.priority === 'medium' ? 'bg-yellow-100' :
                        'bg-green-100'
                      ]">
                        <Bell :class="[
                          'h-5 w-5',
                          currentNotification.priority === 'critical' ? 'text-red-600' :
                          currentNotification.priority === 'high' ? 'text-orange-600' :
                          currentNotification.priority === 'medium' ? 'text-yellow-600' :
                          'text-green-600'
                        ]" />
                      </div>
                      
                      <div class="flex-1 min-w-0">
                        <div class="flex items-center space-x-2 mb-1">
                          <h4 class="font-semibold text-sm text-gray-900">
                            {{ currentNotification.title }}
                          </h4>
                          <span :class="[
                            'inline-flex items-center rounded-full px-2 py-0.5 text-xs font-semibold',
                            currentNotification.priority === 'critical' ? 'bg-red-100 text-red-800' :
                            currentNotification.priority === 'high' ? 'bg-orange-100 text-orange-800' :
                            currentNotification.priority === 'medium' ? 'bg-yellow-100 text-yellow-800' :
                            'bg-green-100 text-green-800'
                          ]">
                            {{ currentNotification.priority.toUpperCase() }}
                          </span>
                        </div>
                        
                        <p class="text-sm text-gray-600 mb-2 line-clamp-2">
                          {{ currentNotification.message }}
                        </p>
                        
                        <div class="flex items-center justify-between text-xs text-gray-500">
                          <span class="capitalize">
                            {{ currentNotification.notification_type.replace('_', ' ') }}
                          </span>
                          <span>Just now</span>
                        </div>
                      </div>
                    </div>
                    
                    <button
                      @click.stop="closePopup"
                      class="ml-2 p-1 hover:bg-gray-200 rounded-full transition-colors"
                    >
                      <X class="h-4 w-4 text-gray-500" />
                    </button>
                  </div>
                </div>
                
                <div class="bg-gray-50 px-4 py-2 border-t border-gray-200">
                  <button
                    @click="navigateToNotifications"
                    class="text-xs text-blue-600 hover:text-blue-800 font-medium"
                  >
                    View all notifications →
                  </button>
                </div>
              </div>
            </Transition>
          </div>
          
          <div class="relative profile-dropdown-container">
            <Button 
              variant="outline" 
              size="sm"
              @click="toggleProfileDropdown"
              class="flex items-center gap-2"
            >
              <User class="h-4 w-4" />
              <span v-if="currentUser">{{ currentUser.first_name }} {{ currentUser.last_name }}</span>
              <span v-else>Profile</span>
              <ChevronDown class="h-4 w-4" />
            </Button>
            
            <!-- Profile Dropdown -->
            <Transition name="profile-dropdown">
              <div
                v-if="showProfileDropdown"
                class="absolute top-full right-0 mt-2 w-80 bg-white rounded-lg shadow-2xl border border-gray-200 z-50 overflow-hidden"
              >
                <div class="p-4 border-b border-gray-200">
                  <div class="flex items-center space-x-3">
                    <div class="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center">
                      <User class="h-5 w-5 text-blue-600" />
                    </div>
                    <div class="flex-1 min-w-0">
                      <h4 class="font-semibold text-sm text-gray-900 truncate">
                        {{ currentUser?.first_name }} {{ currentUser?.last_name }}
                      </h4>
                      <p class="text-xs text-gray-600 truncate">{{ currentUser?.email }}</p>
                    </div>
                  </div>
                </div>
                
                <div class="py-2">
                  <button
                    @click="handleLogout"
                    :disabled="loggingOut"
                    class="w-full flex items-center gap-3 px-4 py-3 text-sm text-red-600 hover:bg-red-50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <svg v-if="loggingOut" class="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                      <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                      <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    <LogOut class="h-4 w-4" v-else />
                    <span v-if="loggingOut">Logging out...</span>
                    <span v-else>Logout</span>
                  </button>
                </div>
              </div>
            </Transition>
          </div>
        </div>
      </div>
    </div>
  </header>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useStore } from 'vuex'
import { Button } from '@/components/ui/button'
import { Bell, User, X, ChevronDown, LogOut } from 'lucide-vue-next'
import { useNotificationCount } from '@/composables/useNotificationCount'
import notificationService from '@/services/notificationService'

const route = useRoute()
const router = useRouter()
const store = useStore()

// User state
const currentUser = computed(() => store.getters['auth/currentUser'])
const loggingOut = ref(false)

// Profile dropdown state
const showProfileDropdown = ref(false)

// Notification state
const { unreadCount, initializeNotificationCount } = useNotificationCount()
const showPopup = ref(false)
const currentNotification = ref(null)
let popupTimeout = null

// Route to title mapping
const routeTitleMap = {
  '/': 'Home',
  '/dashboard': 'Dashboard',
  '/contractdashboard': 'Contract Dashboard',
  '/sla-index': 'SLA Management',
  '/slas': 'SLA Management',
  '/slas/create': 'Create SLA',
  '/slas/active': 'Active SLAs',
  '/slas/expiring': 'Expiring SLAs',
  '/slas/renew': 'SLA Renewal',
  '/slas/approvals': 'SLA Approvals',
  '/slas/approval-assignment': 'SLA Approval Assignment',
  '/performance': 'Performance Dashboard',
  '/contracts': 'Contracts',
  '/contracts/new': 'New Contract',
  '/contracts/create': 'Create Contract',
  '/contracts/preview': 'Contract Preview',
  '/rfp': 'RFP Management',
  '/rfp-analytics': 'RFP Analytics Dashboard',
  '/bcp': 'BCP Management',
  '/vendor-upload': 'Vendor Upload',
  '/ocr-extraction': 'OCR Extraction',
  '/evaluation': 'Plan Evaluation',
  '/library': 'Plan Library',
  '/questionnaire-library': 'Questionnaire Library',
  '/testing-library': 'Testing Library',
  '/questionnaire-builder': 'Questionnaire Builder',
  '/questionnaire-assignment': 'Questionnaire Assignment',
  '/approval-assignment': 'Approval Assignment',
  '/my-approvals': 'My Approvals',
  '/vendor-hub': 'Vendor Hub',
  '/kpi-dashboard': 'KPI Dashboard',
  '/quick-access': 'Quick Access Dashboard',
  '/notifications': 'Notification Center'
}

// Route to breadcrumb mapping based on actual menu structure
const routeBreadcrumbMap = {
  '/': [{ name: 'Home' }],
  
  // RFP Management
  '/rfp-dashboard': [
    { name: 'RFP Management', path: '/rfp-dashboard' },
    { name: 'RFP Dashboard' }
  ],
  '/rfp-workflow': [
    { name: 'RFP Management', path: '/rfp-dashboard' },
    { name: 'Workflow' }
  ],
  '/approval-management': [
    { name: 'RFP Management', path: '/rfp-dashboard' },
    { name: 'Evaluation Workflow', path: '/approval-management' },
    { name: 'Workflow Creation' }
  ],
  '/my-approvals': [
    { name: 'RFP Management', path: '/rfp-dashboard' },
    { name: 'Evaluation Workflow', path: '/approval-management' },
    { name: 'My Approvals' }
  ],
  '/all-approvals': [
    { name: 'RFP Management', path: '/rfp-dashboard' },
    { name: 'Evaluation Workflow', path: '/approval-management' },
    { name: 'All Approvals' }
  ],

  '/rfp-approval/change-request-manager': [
    { name: 'RFP Management', path: '/rfp-dashboard' },
    { name: 'Evaluation Workflow', path: '/approval-management' },
    { name: 'Change Requests' }
  ],

  '/rfp-creation': [

    { name: 'RFP Management', path: '/rfp-dashboard' },

    { name: 'RFP Workflow', path: '/rfp-creation' },

    { name: '1. Creation' }

  ],

  '/rfp-approval': [

    { name: 'RFP Management', path: '/rfp-dashboard' },

    { name: 'RFP Workflow', path: '/rfp-creation' },

    { name: '2. Approval' }

  ],

  '/rfp-vendor-selection': [

    { name: 'RFP Management', path: '/rfp-dashboard' },

    { name: 'RFP Workflow', path: '/rfp-creation' },

    { name: '3. Vendor Selection' }

  ],

  '/rfp-url-generation': [

    { name: 'RFP Management', path: '/rfp-dashboard' },

    { name: 'RFP Workflow', path: '/rfp-creation' },

    { name: '4. URL Generation' }

  ],

  '/rfp-vendor-portal': [

    { name: 'RFP Management', path: '/rfp-dashboard' },

    { name: 'RFP Workflow', path: '/rfp-creation' },

    { name: '5. Vendor Portal' }

  ],

  '/rfp-evaluation': [

    { name: 'RFP Management', path: '/rfp-dashboard' },

    { name: 'RFP Workflow', path: '/rfp-creation' },

    { name: '6. Evaluation' }

  ],

  '/rfp-comparison': [

    { name: 'RFP Management', path: '/rfp-dashboard' },

    { name: 'RFP Workflow', path: '/rfp-creation' },

    { name: '7. Comparison' }

  ],

  '/rfp-consensus': [

    { name: 'RFP Management', path: '/rfp-dashboard' },

    { name: 'RFP Workflow', path: '/rfp-creation' },

    { name: '7. Consensus & Award' }

  ],

  '/rfp-award': [

    { name: 'RFP Management', path: '/rfp-dashboard' },

    { name: 'RFP Workflow', path: '/rfp-creation' },

    { name: '7. Consensus & Award' }

  ],
 
  '/rfp-analytics': [
    { name: 'RFP Management', path: '/rfp-dashboard' },
    { name: 'Analytics' }
  ],
  '/draft-manager': [
    { name: 'RFP Management', path: '/rfp-dashboard' },
    { name: 'Drafts' }
  ],

  // Vendor Management
  '/vendor-dashboard': [
    { name: 'Vendor Management', path: '/vendor-dashboard' },
    { name: 'Vendor Dashboard' }
  ],
  '/vendor-kpi-dashboard': [
    { name: 'Vendor Management', path: '/vendor-dashboard' },
    { name: 'KPI Dashboard' }
  ],
  '/vendor-registration': [
    { name: 'Vendor Management', path: '/vendor-dashboard' },
    { name: 'Vendor Registration' }
  ],
  '/vendor-verification': [
    { name: 'Vendor Management', path: '/vendor-dashboard' },
    { name: 'External Screening' }
  ],
  '/vendor-questionnaire': [
    { name: 'Vendor Management', path: '/vendor-dashboard' },
    { name: 'Questionnaire Management', path: '/vendor-questionnaire' },
    { name: 'Builder' }
  ],
  '/vendor-questionnaire-assignment': [
    { name: 'Vendor Management', path: '/vendor-dashboard' },
    { name: 'Questionnaire Management', path: '/vendor-questionnaire' },
    { name: 'Assignment' }
  ],
  '/vendor-questionnaire-response': [
    { name: 'Vendor Management', path: '/vendor-dashboard' },
    { name: 'Questionnaire Management', path: '/vendor-questionnaire' },
    { name: 'Response' }
  ],
  '/vendor-risk-scoring': [
    { name: 'Vendor Management', path: '/vendor-dashboard' },
    { name: 'Risk Scoring' }
  ],
  '/vendor-lifecycle': [
    { name: 'Vendor Management', path: '/vendor-dashboard' },
    { name: 'Lifecycle Tracker' }
  ],
  '/vendor-approval-dashboard': [
    { name: 'Vendor Management', path: '/vendor-dashboard' },
    { name: 'Vendor Approval', path: '/vendor-approval-dashboard' },
    { name: 'Approval Dashboard' }
  ],
  '/vendor-approval-workflow-creator': [
    { name: 'Vendor Management', path: '/vendor-dashboard' },
    { name: 'Vendor Approval', path: '/vendor-approval-dashboard' },
    { name: 'Create Workflow' }
  ],
  '/vendor-my-approvals': [
    { name: 'Vendor Management', path: '/vendor-dashboard' },
    { name: 'Vendor Approval', path: '/vendor-approval-dashboard' },
    { name: 'My Approvals' }
  ],
  '/vendor-all-approvals': [
    { name: 'Vendor Management', path: '/vendor-dashboard' },
    { name: 'Vendor Approval', path: '/vendor-approval-dashboard' },
    { name: 'All Approvals' }
  ],

  // Contract Management
  '/contractdashboard': [
    { name: 'Contract Management', path: '/contractdashboard' },
    { name: 'Contract Dashboard' }
  ],
  '/contracts': [
    { name: 'Contract Management', path: '/contractdashboard' },
    { name: 'All Contracts' }
  ],
  '/contracts/new': [
    { name: 'Contract Management', path: '/contractdashboard' },
    { name: 'Create Contract' }
  ],
  '/vendors': [
    { name: 'Contract Management', path: '/contractdashboard' },
    { name: 'Vendor Contracts' }
  ],
  '/contract-approval-assignment': [
    { name: 'Contract Management', path: '/contractdashboard' },
    { name: 'Approval Assignment' }
  ],
  '/my-contract-approvals': [
    { name: 'Contract Management', path: '/contractdashboard' },
    { name: 'My Approvals' }
  ],
  '/archive': [
    { name: 'Contract Management', path: '/contractdashboard' },
    { name: 'Archive' }
  ],
  '/search': [
    { name: 'Contract Management', path: '/contractdashboard' },
    { name: 'Search' }
  ],
  '/analytics': [
    { name: 'Contract Management', path: '/contractdashboard' },
    { name: 'Analytics' }
  ],
  '/contract-kpi-dashboard': [
    { name: 'Contract Management', path: '/contractdashboard' },
    { name: 'KPI Dashboard' }
  ],
  '/audit/dashboard': [
    { name: 'Contract Management', path: '/contractdashboard' },
    { name: 'Audit', path: '/audit/dashboard' },
    { name: 'Audit Dashboard' }
  ],
  '/contract-audit/all': [
    { name: 'Contract Management', path: '/contractdashboard' },
    { name: 'Audit', path: '/audit/dashboard' },
    { name: 'All Audits' }
  ],
  '/contract-audit/create': [
    { name: 'Contract Management', path: '/contractdashboard' },
    { name: 'Audit', path: '/audit/dashboard' },
    { name: 'Create Audit' }
  ],
  '/contract-audit/reports': [
    { name: 'Contract Management', path: '/contractdashboard' },
    { name: 'Audit', path: '/audit/dashboard' },
    { name: 'Audit Reports' }
  ],

  // Service Level Agreement
  '/dashboard': [
    { name: 'Service Level Agreement', path: '/dashboard' },
    { name: 'SLA Dashboard', path: '/dashboard' },
    { name: 'SLA Overview' }
  ],
  '/performance': [
    { name: 'Service Level Agreement', path: '/dashboard' },
    { name: 'SLA Dashboard', path: '/dashboard' },
    { name: 'Performance Summary' }
  ],
  '/kpi-dashboard': [
    { name: 'Service Level Agreement', path: '/dashboard' },
    { name: 'SLA Dashboard', path: '/dashboard' },
    { name: 'KPI Dashboard' }
  ],
  '/slas': [
    { name: 'Service Level Agreement', path: '/dashboard' },
    { name: 'SLA Management', path: '/slas' },
    { name: 'All SLAs' }
  ],
  '/slas/active': [
    { name: 'Service Level Agreement', path: '/dashboard' },
    { name: 'SLA Management', path: '/slas' },
    { name: 'Active SLAs' }
  ],
  '/slas/expiring': [
    { name: 'Service Level Agreement', path: '/dashboard' },
    { name: 'SLA Management', path: '/slas' },
    { name: 'Expiring SLAs' }
  ],
  '/slas/create': [
    { name: 'Service Level Agreement', path: '/dashboard' },
    { name: 'Create/Upload SLA', path: '/slas/create' },
    { name: 'Create New SLA' }
  ],
  '/audit': [
    { name: 'Service Level Agreement', path: '/dashboard' },
    { name: 'Audit Management', path: '/audit' },
    { name: 'Audit Dashboard' }
  ],
  '/audit/create': [
    { name: 'Service Level Agreement', path: '/dashboard' },
    { name: 'Audit Management', path: '/audit' },
    { name: 'Create Audit' }
  ],
  '/audit/my-audits': [
    { name: 'Service Level Agreement', path: '/dashboard' },
    { name: 'Audit Management', path: '/audit' },
    { name: 'My Audits' }
  ],
  '/audit/reports': [
    { name: 'Service Level Agreement', path: '/dashboard' },
    { name: 'Audit Management', path: '/audit' },
    { name: 'Audit Reports' }
  ],
  '/slas/approvals': [
    { name: 'Service Level Agreement', path: '/dashboard' },
    { name: 'SLA Approvals', path: '/slas/approvals' },
    { name: 'My Approvals' }
  ],
  '/slas/approval-assignment': [
    { name: 'Service Level Agreement', path: '/dashboard' },
    { name: 'SLA Approvals', path: '/slas/approvals' },
    { name: 'Assign Approvals' }
  ],
  '/slas/renew': [
    { name: 'Service Level Agreement', path: '/dashboard' },
    { name: 'SLA Renewal' }
  ],
  
  // Quick Access & Notifications
  '/quick-access': [
    { name: 'Management' },
    { name: 'Quick Access' }
  ],
  '/notifications': [
    { name: 'Management' },
    { name: 'Notifications' }
  ],

  // BCP/DRP Management
  '/bcp/vendor-upload': [
    { name: 'BCP/DRP Management', path: '/bcp/vendor-upload' },
    { name: 'Plan Phase', path: '/bcp/vendor-upload' },
    { name: 'Upload Plans' }
  ],
  '/bcp/ocr-extraction': [
    { name: 'BCP/DRP Management', path: '/bcp/vendor-upload' },
    { name: 'Plan Phase', path: '/bcp/vendor-upload' },
    { name: 'OCR Extraction' }
  ],
  '/bcp/evaluation': [
    { name: 'BCP/DRP Management', path: '/bcp/vendor-upload' },
    { name: 'Plan Phase', path: '/bcp/vendor-upload' },
    { name: 'Plan Evaluation' }
  ],
  '/bcp/library': [
    { name: 'BCP/DRP Management', path: '/bcp/vendor-upload' },
    { name: 'Plan Phase', path: '/bcp/vendor-upload' },
    { name: 'Plan Library' }
  ],
  '/bcp/dashboard': [
    { name: 'BCP/DRP Management', path: '/bcp/vendor-upload' },
    { name: 'Owner Console', path: '/bcp/dashboard' },
    { name: 'Analytics Dashboard' }
  ],
  '/bcp/kpi-dashboard': [
    { name: 'BCP/DRP Management', path: '/bcp/vendor-upload' },
    { name: 'Owner Console', path: '/bcp/dashboard' },
    { name: 'KPI Dashboard' }
  ],
  '/bcp/risk-analytics': [
    { name: 'BCP/DRP Management', path: '/bcp/vendor-upload' },
    { name: 'Owner Console', path: '/bcp/dashboard' },
    { name: 'Risk Analytics' }
  ],
  '/bcp/testing-library': [
    { name: 'BCP/DRP Management', path: '/bcp/vendor-upload' },
    { name: 'Testing Phase', path: '/bcp/testing-library' },
    { name: 'Testing Library' }
  ],
  '/bcp/questionnaire-library': [
    { name: 'BCP/DRP Management', path: '/bcp/vendor-upload' },
    { name: 'Testing Phase', path: '/bcp/testing-library' },
    { name: 'Questionnaire Library' }
  ],
  '/bcp/questionnaire-builder': [
    { name: 'BCP/DRP Management', path: '/bcp/vendor-upload' },
    { name: 'Testing Phase', path: '/bcp/testing-library' },
    { name: 'Build & Review' }
  ],
  '/bcp/questionnaire-assignment': [
    { name: 'BCP/DRP Management', path: '/bcp/vendor-upload' },
    { name: 'Testing Phase', path: '/bcp/testing-library' },
    { name: 'Assignment & Answering' }
  ],
  '/bcp/approval-assignment': [
    { name: 'BCP/DRP Management', path: '/bcp/vendor-upload' },
    { name: 'Testing Phase', path: '/bcp/testing-library' },
    { name: 'Approval Assignment' }
  ],
  '/bcp/my-approvals': [
    { name: 'BCP/DRP Management', path: '/bcp/vendor-upload' },
    { name: 'Testing Phase', path: '/bcp/testing-library' },
    { name: 'My Approvals' }
  ],
  '/bcp/vendor-hub': [
    { name: 'BCP/DRP Management', path: '/bcp/vendor-upload' },
    { name: 'Testing Phase', path: '/bcp/testing-library' },
    { name: 'Vendor Hub' }
  ],

  // Legacy routes for backward compatibility
  '/vendor-upload': [
    { name: 'BCP/DRP Management', path: '/bcp/vendor-upload' },
    { name: 'Plan Phase', path: '/bcp/vendor-upload' },
    { name: 'Upload Plans' }
  ],
  '/ocr-extraction': [
    { name: 'BCP/DRP Management', path: '/bcp/vendor-upload' },
    { name: 'Plan Phase', path: '/bcp/vendor-upload' },
    { name: 'OCR Extraction' }
  ],
  '/evaluation': [
    { name: 'BCP/DRP Management', path: '/bcp/vendor-upload' },
    { name: 'Plan Phase', path: '/bcp/vendor-upload' },
    { name: 'Plan Evaluation' }
  ],
  '/library': [
    { name: 'BCP/DRP Management', path: '/bcp/vendor-upload' },
    { name: 'Plan Phase', path: '/bcp/vendor-upload' },
    { name: 'Plan Library' }
  ],
  '/questionnaire-library': [
    { name: 'BCP/DRP Management', path: '/bcp/vendor-upload' },
    { name: 'Testing Phase', path: '/bcp/testing-library' },
    { name: 'Questionnaire Library' }
  ],
  '/testing-library': [
    { name: 'BCP/DRP Management', path: '/bcp/vendor-upload' },
    { name: 'Testing Phase', path: '/bcp/testing-library' },
    { name: 'Testing Library' }
  ],
  '/questionnaire-builder': [
    { name: 'BCP/DRP Management', path: '/bcp/vendor-upload' },
    { name: 'Testing Phase', path: '/bcp/testing-library' },
    { name: 'Build & Review' }
  ],
  '/questionnaire-assignment': [
    { name: 'BCP/DRP Management', path: '/bcp/vendor-upload' },
    { name: 'Testing Phase', path: '/bcp/testing-library' },
    { name: 'Assignment & Answering' }
  ],
  '/approval-assignment': [
    { name: 'BCP/DRP Management', path: '/bcp/vendor-upload' },
    { name: 'Testing Phase', path: '/bcp/testing-library' },
    { name: 'Approval Assignment' }
  ],
  '/vendor-hub': [
    { name: 'BCP/DRP Management', path: '/bcp/vendor-upload' },
    { name: 'Testing Phase', path: '/bcp/testing-library' },
    { name: 'Vendor Hub' }
  ]
}

// Dynamic page title
const pageTitle = computed(() => {
  const currentPath = route.path
  
  // Check for exact match first
  if (routeTitleMap[currentPath]) {
    return routeTitleMap[currentPath]
  }
  
  // Check for dynamic routes (with parameters)
  for (const [path, title] of Object.entries(routeTitleMap)) {
    if (path.includes(':')) {
      const pathPattern = path.replace(/:\w+/g, '[^/]+')
      const regex = new RegExp(`^${pathPattern}$`)
      if (regex.test(currentPath)) {
        return title
      }
    }
  }
  
  // Fallback to route name or path
  return route.name || currentPath.split('/').pop() || 'Page'
})

// Dynamic breadcrumbs
const breadcrumbs = computed(() => {
  const currentPath = route.path
  
  // Check for exact match first
  if (routeBreadcrumbMap[currentPath]) {
    return routeBreadcrumbMap[currentPath]
  }
  
  // Check for dynamic routes (with parameters)
  for (const [path, breadcrumb] of Object.entries(routeBreadcrumbMap)) {
    if (path.includes(':')) {
      const pathPattern = path.replace(/:\w+/g, '[^/]+')
      const regex = new RegExp(`^${pathPattern}$`)
      if (regex.test(currentPath)) {
        return breadcrumb
      }
    }
  }
  
  // Generate breadcrumb from path segments with proper menu structure
  const segments = currentPath.split('/').filter(segment => segment)
  const generatedBreadcrumbs = []
  
  // Try to determine the main menu based on the first segment
  let mainMenu = null
  let mainMenuPath = null
  
  if (segments.length > 0) {
    const firstSegment = segments[0]
    
    // Map first segment to main menu
    const menuMapping = {
      'rfp': { name: 'RFP Management', path: '/rfp-dashboard' },
      'vendor': { name: 'Vendor Management', path: '/vendor-dashboard' },
      'contract': { name: 'Contract Management', path: '/contractdashboard' },
      'sla': { name: 'Service Level Agreement', path: '/dashboard' },
      'slas': { name: 'Service Level Agreement', path: '/dashboard' },
      'bcp': { name: 'BCP/DRP Management', path: '/bcp/vendor-upload' },
      'audit': { name: 'Service Level Agreement', path: '/dashboard' },
      'dashboard': { name: 'Service Level Agreement', path: '/dashboard' },
      'performance': { name: 'Service Level Agreement', path: '/dashboard' },
      'kpi': { name: 'Service Level Agreement', path: '/dashboard' }
    }
    
    mainMenu = menuMapping[firstSegment] || { name: 'Home', path: '/' }
    mainMenuPath = mainMenu.path
  }
  
  // Add main menu
  if (mainMenu) {
    generatedBreadcrumbs.push(mainMenu)
  }
  
  // Add remaining segments
  let currentPathAccumulator = ''
  segments.forEach((segment, index) => {
    currentPathAccumulator += `/${segment}`
    const isLast = index === segments.length - 1
    
    // Convert segment to readable name
    const readableName = segment
      .split('-')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ')
    
    generatedBreadcrumbs.push({
      name: readableName,
      path: isLast ? null : currentPathAccumulator
    })
  })
  
  return generatedBreadcrumbs
})

// Notification methods
const navigateToNotifications = () => {
  router.push('/notifications')
}

const handleNotificationClick = () => {
  closePopup()
  navigateToNotifications()
}

const closePopup = () => {
  showPopup.value = false
  currentNotification.value = null
  if (popupTimeout) {
    clearTimeout(popupTimeout)
    popupTimeout = null
  }
}

// Profile dropdown methods
const toggleProfileDropdown = () => {
  showProfileDropdown.value = !showProfileDropdown.value
  // Close notification popup when opening profile dropdown
  if (showProfileDropdown.value) {
    closePopup()
  }
}

const handleLogout = async () => {
  if (loggingOut.value) return
  
  try {
    loggingOut.value = true
    console.log('AppHeader: Logging out user...')
    console.log('AppHeader: Current user:', currentUser.value)
    
    const result = await store.dispatch('auth/logoutUser')
    
    console.log('AppHeader: Logout result:', result)
    
    if (result.success) {
      console.log('AppHeader: ✅ Logout successful, session token cleared from database')
      // Close profile dropdown
      showProfileDropdown.value = false
      // Redirect to login page
      setTimeout(() => {
        router.push('/login')
      }, 100)
    } else {
      console.error('AppHeader: ⚠️ Logout API failed:', result.error)
      console.log('AppHeader: Local storage cleared, redirecting to login anyway')
      // Still redirect to login even if API call failed
      showProfileDropdown.value = false
      setTimeout(() => {
        router.push('/login')
      }, 100)
    }
  } catch (error) {
    console.error('AppHeader: ❌ Logout error:', error)
    // Redirect to login anyway
    showProfileDropdown.value = false
    setTimeout(() => {
      router.push('/login')
    }, 100)
  } finally {
    loggingOut.value = false
  }
}

const showNotificationPopup = (notification) => {
  currentNotification.value = notification
  showPopup.value = true
  
  // Auto-hide popup after 5 seconds
  if (popupTimeout) {
    clearTimeout(popupTimeout)
  }
  popupTimeout = setTimeout(() => {
    closePopup()
  }, 5000)
}

// Subscribe to new notifications
let unsubscribe = null

// Click outside handler for profile dropdown
const handleClickOutside = (event) => {
  const profileDropdown = event.target.closest('.profile-dropdown-container')
  if (!profileDropdown && showProfileDropdown.value) {
    showProfileDropdown.value = false
  }
}

onMounted(async () => {
  // Initialize notification count on app startup
  await initializeNotificationCount()
  
  // Subscribe to new notifications
  unsubscribe = notificationService.subscribe((notification) => {
    showNotificationPopup(notification)
  })
  
  // Add click outside listener
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  if (unsubscribe) {
    unsubscribe()
  }
  if (popupTimeout) {
    clearTimeout(popupTimeout)
  }
  // Remove click outside listener
  document.removeEventListener('click', handleClickOutside)
})

// Watch for route changes to update title
watch(() => route.path, (newPath) => {
  // Update document title
  document.title = `${pageTitle.value} - TPRM System`
}, { immediate: true })
</script>

<style scoped>
/* Notification popup animation */
.notification-popup-enter-active,
.notification-popup-leave-active {
  transition: all 0.3s ease;
}

.notification-popup-enter-from {
  opacity: 0;
  transform: translateY(-10px);
}

.notification-popup-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}

/* Line clamp utility */
.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

/* Profile dropdown animation */
.profile-dropdown-enter-active,
.profile-dropdown-leave-active {
  transition: all 0.3s ease;
}

.profile-dropdown-enter-from {
  opacity: 0;
  transform: translateY(-10px);
}

.profile-dropdown-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}
</style>
