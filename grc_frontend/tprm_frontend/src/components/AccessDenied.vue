<template>
  <div class="access-denied-viewport">
    <div class="glass-card-modern">
      <!-- Skeleton State -->
      <div v-if="isLoading" class="flex flex-col items-center">
        <div class="w-24 h-24 rounded-3xl bg-slate-100 animate-pulse mb-8 rotate-[-3deg]"></div>
        <div class="w-64 h-8 bg-slate-100 rounded-lg animate-pulse mb-4"></div>
        <div class="w-80 h-4 bg-slate-100 rounded-md animate-pulse mb-2"></div>
        <div class="w-60 h-4 bg-slate-100 rounded-md animate-pulse mb-10"></div>
        
        <div class="grid grid-cols-2 gap-4 w-full">
          <div class="h-12 bg-slate-100 rounded-xl animate-pulse"></div>
          <div class="h-12 bg-slate-100 rounded-xl animate-pulse"></div>
        </div>
      </div>

      <!-- Main Content -->
      <div v-else class="fade-in">
        <!-- Icon Section -->
        <div class="icon-header-premium">

        <div class="shield-container-animated">
          <div class="glow-layer"></div>
          <Shield class="h-12 w-12 text-white relative z-10" />
          <div class="lock-overlay-badge">
            <Lock class="w-3.5 h-3.5 text-indigo-600" />
          </div>
        </div>
      </div>
      
      <!-- Content Section -->
      <div class="content-body">
        <h1 class="text-3xl font-bold text-slate-900 mb-3 tracking-tight">Secure Workspace</h1>
        <p class="text-slate-600 mb-2 text-lg leading-relaxed">
          You've reached a secure area of the platform.
        </p>
        <p class="text-slate-500 mb-8 text-sm leading-relaxed max-w-sm mx-auto">
          To access this module, please ensure you have the appropriate permissions or submit a request below.
        </p>
        
        <!-- Primary Actions -->
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-6">
          <Button @click="goBack" variant="outline" class="h-12 rounded-xl border-slate-200 text-slate-700 hover:bg-slate-50 font-semibold flex items-center justify-center gap-2">
            <ArrowLeft class="w-4 h-4" />
            Go Back
          </Button>
          
          <Button 
            @click="requestAccess"
            :disabled="isRequesting || requestSubmitted"
            class="h-12 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white shadow-lg shadow-indigo-100 font-semibold flex items-center justify-center gap-2"
          >
            <div v-if="isRequesting" class="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent"></div>
            <span v-if="isRequesting">Processing...</span>
            <span v-else-if="requestSubmitted" class="flex items-center gap-2"><CheckCircle2 class="w-4 h-4" /> Sent</span>
            <span v-else>Request Approval</span>
          </Button>
        </div>

        <!-- Technical Details Toggle -->
        <button @click="showDetails = !showDetails" class="text-indigo-600 hover:text-indigo-700 font-semibold text-sm py-2 px-4 rounded-lg hover:bg-indigo-50 transition-colors flex items-center gap-2 mx-auto mb-4">
          {{ showDetails ? 'Hide' : 'View' }} Technical Details
          <ChevronDown :class="['w-4 h-4 transition-transform duration-300', showDetails ? 'rotate-180' : '']" />
        </button>

        <!-- Status Feedback -->
        <transition name="fade">
          <div v-if="message" :class="['p-3 rounded-xl border text-sm flex items-center gap-3 mb-4', messageType === 'success' ? 'bg-emerald-50 text-emerald-800 border-emerald-100' : 'bg-red-50 text-red-800 border-red-100']">
            <component :is="messageType === 'success' ? 'CheckCircle2' : 'AlertCircle'" class="w-4 h-4 flex-shrink-0" />
            {{ message }}
          </div>
        </transition>

        <!-- Collapsible Details Box -->
        <transition name="expand">
          <div v-if="showDetails" class="mt-4 bg-white border border-slate-100 rounded-2xl p-5 text-left shadow-inner">
            <div class="space-y-3">
              <div class="flex justify-between items-center py-1 border-b border-slate-50 last:border-0">
                <span class="text-xs font-medium text-slate-500 uppercase tracking-wider">Module</span>
                <span class="text-sm font-semibold text-slate-800">{{ errorInfo.message || 'Restricted Module' }}</span>
              </div>
              <div class="flex justify-between items-center py-1 border-b border-slate-50 last:border-0">
                <span class="text-xs font-medium text-slate-500 uppercase tracking-wider">Resource</span>
                <span class="text-sm font-semibold text-slate-800 truncate max-w-[200px]">{{ requestedUrl }}</span>
              </div>
              <div class="flex justify-between items-center py-1 border-b border-slate-50 last:border-0">
                <span class="text-xs font-medium text-slate-500 uppercase tracking-wider">Security ID</span>
                <span class="text-sm font-semibold text-slate-800">{{ userInfo.userId || 'Guest Session' }}</span>
              </div>
            </div>

            <div class="flex gap-4 mt-6 pt-4 border-t border-slate-50">
              <button @click="goHome" class="flex-1 flex items-center justify-center gap-2 text-xs font-bold text-slate-600 hover:text-indigo-600 transition-colors">
                <LayoutDashboard class="w-3.5 h-3.5" />
                DASHBOARD
              </button>
              <button @click="contactSupport" class="flex-1 flex items-center justify-center gap-2 text-xs font-bold text-slate-600 hover:text-indigo-600 transition-colors">
                <HelpCircle class="w-3.5 h-3.5" />
                SUPPORT
              </button>
            </div>
          </div>
        </transition>
      </div>
    </div>
  </div>
</template>

<script>
import { API_ENDPOINTS, getAuthToken } from '../config/api.js'
import { getCurrentUserId } from '../utils/session.js'
import axios from 'axios'
import { 
  Shield, 
  Lock, 
  ArrowLeft, 
  LayoutDashboard, 
  HelpCircle, 
  ShieldAlert, 
  CheckCircle2, 
  AlertCircle,
  ChevronDown
} from 'lucide-vue-next'
import Button from '@/components/ui/button.vue'

export default {
  components: {
    Shield,
    Lock,
    ArrowLeft,
    LayoutDashboard,
    HelpCircle,
    ShieldAlert,
    CheckCircle2,
    AlertCircle,
    ChevronDown,
    Button
  },
  data() {
    return {
      isLoading: true,
      isRequesting: false,
      requestSubmitted: false,
      message: '',
      messageType: 'success',
      showDetails: false,
      userInfo: {
        userId: null,
        role: null
      },
      requestedUrl: ''
    }
  },
  computed: {
    errorInfo() {
      try {
        const accessDeniedInfo = sessionStorage.getItem('access_denied_error')
        if (accessDeniedInfo) {
          return JSON.parse(accessDeniedInfo)
        }
      } catch (e) {
        console.error('Error parsing access denied info:', e)
      }
      return {
        message: 'Security clearance required.',
        code: null,
        permission: null,
        permissionRequired: null,
        path: null
      }
    }
  },
  mounted() {
    document.body.style.overflow = 'hidden'
    
    // Parse requested URL and load user info
    try {
      const accessDeniedInfo = sessionStorage.getItem('access_den_error') || sessionStorage.getItem('access_denied_error')
      if (accessDeniedInfo) {
        const info = JSON.parse(accessDeniedInfo)
        if (info.path) {
          this.requestedUrl = info.path
        }
      }
    } catch (e) {}

    if (!this.requestedUrl) {
      this.requestedUrl = window.location.pathname
    }

    const userId = localStorage.getItem('user_id')
    const userRole = localStorage.getItem('user_role') || localStorage.getItem('role')
    this.userInfo = {
      userId: userId,
      role: userRole
    }

    // Delay for skeleton visualization
    setTimeout(() => {
      this.isLoading = false
    }, 800)
  },
  beforeUnmount() {
    document.body.style.overflow = ''
  },
  methods: {
    async requestAccess() {
      try {
        this.isRequesting = true
        this.message = ''
        
        const accessDeniedInfo = sessionStorage.getItem('access_denied_error')
        let requestedUrl = ''
        let requestedFeature = ''
        let requiredPermission = ''
        
        if (accessDeniedInfo) {
          try {
            const info = JSON.parse(accessDeniedInfo)
            if (info.path) {
              try {
                const urlObj = new URL(info.path, window.location.origin)
                requestedUrl = urlObj.pathname
              } catch (e) {
                const pathMatch = info.path.match(/^([^?#]+)/)
                requestedUrl = pathMatch ? pathMatch[1] : info.path
              }
            }
            requiredPermission = info.permission || ''
            requestedFeature = info.message || requestedUrl || ''
          } catch (e) {
            requestedUrl = window.location.pathname
          }
        } else {
          requestedUrl = window.location.pathname
        }
        
        if (!requestedUrl || requestedUrl === '/access-denied') {
          this.message = 'Unable to determine the requested module.'
          this.messageType = 'error'
          this.isRequesting = false
          return
        }
        
        let userId = null
        try {
          userId = getCurrentUserId()
        } catch (e) {}
        
        if (!userId) {
          userId = localStorage.getItem('user_id')
        }
        
        if (!userId) {
          this.message = 'Please sign in to request clearance.'
          this.messageType = 'error'
          this.isRequesting = false
          return
        }
        
        const accessToken = getAuthToken()
        const requestData = {
          user_id: parseInt(userId),
          requested_url: requestedUrl,
          requested_feature: requestedFeature,
          required_permission: requiredPermission,
          requested_role: '',
          message: `Clearance request for: ${requestedFeature || requestedUrl}`
        }
        
        const response = await axios.post(
          API_ENDPOINTS.CREATE_ACCESS_REQUEST,
          requestData,
          {
            headers: {
              'Authorization': `Bearer ${accessToken}`,
              'Content-Type': 'application/json'
            }
          }
        )
        
        if (response.data && response.data.status === 'success') {
          this.requestSubmitted = true
          this.message = 'Clearance request submitted. You will be notified once reviewed.'
          this.messageType = 'success'
        } else {
          throw new Error(response.data?.message || 'Submission failed')
        }
        
      } catch (error) {
        this.message = error.response?.data?.message || 'Access request could not be sent at this time.'
        this.messageType = 'error'
      } finally {
        this.isRequesting = false
      }
    },
    goBack() {
      if (window.history.length > 1) {
        this.$router.go(-1)
      } else {
        this.$router.push('/dashboard')
      }
    },
    goHome() {
      this.$router.push('/dashboard')
    },
    contactSupport() {
      alert('Security center documentation is available in the help section.')
    }
  }
}
</script>

<style scoped>
.access-denied-viewport {
  min-height: 100vh;
  width: 100%;
  background: radial-gradient(circle at top right, #fdfbff, #f0f4f9, #e6ecf5);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
}

.glass-card-modern {
  width: 100%;
  max-width: 540px;
  background: rgba(255, 255, 255, 0.7);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.5);
  border-radius: 24px;
  padding: 48px 40px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.04), 
              0 2px 10px rgba(0, 0, 0, 0.02);
  text-align: center;
  position: relative;
}

.icon-header-premium {
  margin-bottom: 32px;
  display: flex;
  justify-content: center;
}

.shield-container-animated {
  position: relative;
  width: 96px;
  height: 96px;
  background: linear-gradient(135deg, #4f46e5, #6366f1);
  border-radius: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 12px 24px rgba(79, 70, 229, 0.15);
  transform: rotate(-3deg);
}

.glow-layer {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 120%;
  height: 120%;
  background: radial-gradient(circle, rgba(99, 102, 241, 0.15) 0%, transparent 70%);
  animation: pulse-ring 2.5s infinite ease-in-out;
}

.lock-overlay-badge {
  position: absolute;
  bottom: -6px;
  right: -6px;
  background: white;
  padding: 6px;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  z-index: 20;
}

@keyframes pulse-ring {
  0% { transform: translate(-50%, -50%) scale(0.9); opacity: 0.4; }
  50% { transform: translate(-50%, -50%) scale(1.1); opacity: 0.7; }
  100% { transform: translate(-50%, -50%) scale(0.9); opacity: 0.4; }
}

.fade-enter-active, .fade-leave-active {
  transition: opacity 0.3s ease;
}
.fade-enter-from, .fade-leave-to {
  opacity: 0;
}

.expand-enter-active, .expand-leave-active {
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  max-height: 400px;
  overflow: hidden;
}
.expand-enter-from, .expand-leave-to {
  max-height: 0;
  opacity: 0;
  transform: translateY(-10px);
}

.fade-in {
  animation: fadeIn 0.4s ease-out;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>
