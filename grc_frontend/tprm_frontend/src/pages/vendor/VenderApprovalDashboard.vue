<template>
  <div class="dashboard">
    <div class="row">
      <div class="col-24">
        <h1 class="dashboard-title">Approval System Dashboard</h1>
        <p class="dashboard-subtitle">Manage workflows, requests, and approvals</p>
      </div>
    </div>

    <!-- Statistics Cards Grid -->
    <div class="stats-grid">
      <!-- Total Requests Card -->
      <div class="stat-card" :class="{ 'loading': loading }">
        <div class="stat-content">
          <div class="stat-icon-label">
            <div class="stat-icon total">
              <svg class="icon" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M14 2H6C4.9 2 4 2.9 4 4V20C4 21.1 4.89 22 5.99 22H18C19.1 22 20 21.1 20 20V8L14 2Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <polyline points="14,2 14,8 20,8" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <line x1="16" y1="13" x2="8" y2="13" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <line x1="16" y1="17" x2="8" y2="17" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <polyline points="10,9 9,9 8,9" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
            </div>
            <div class="stat-label">Total Requests</div>
          </div>
          <div class="stat-info">
            <div class="stat-number">
              <span v-if="!loading">{{ stats.total_requests || 0 }}</span>
              <div v-else class="loading-skeleton"></div>
            </div>
          </div>
        </div>
      </div>

      <!-- Pending Requests Card -->
      <div class="stat-card" :class="{ 'loading': loading }">
        <div class="stat-content">
          <div class="stat-icon-label">
            <div class="stat-icon pending">
              <svg class="icon" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
                <polyline points="12,6 12,12 16,14" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
            </div>
            <div class="stat-label">Pending Requests</div>
          </div>
          <div class="stat-info">
            <div class="stat-number">
              <span v-if="!loading">{{ stats.pending_requests || 0 }}</span>
              <div v-else class="loading-skeleton"></div>
            </div>
          </div>
        </div>
      </div>

      <!-- In Progress Card -->
      <div class="stat-card" :class="{ 'loading': loading }">
        <div class="stat-content">
          <div class="stat-icon-label">
            <div class="stat-icon in-progress">
              <svg class="icon" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M21 12A9 9 0 0 0 6 5.69L6 9H2L6 2L10 9H6L6 6.31A7 7 0 1 1 5.93 17.07" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
            </div>
            <div class="stat-label">In Progress</div>
          </div>
          <div class="stat-info">
            <div class="stat-number">
              <span v-if="!loading">{{ stats.in_progress_requests || 0 }}</span>
              <div v-else class="loading-skeleton"></div>
            </div>
          </div>
        </div>
      </div>

      <!-- Approved Card -->
      <div class="stat-card" :class="{ 'loading': loading }">
        <div class="stat-content">
          <div class="stat-icon-label">
            <div class="stat-icon approved">
              <svg class="icon" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M9 12L11 14L15 10" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
              </svg>
            </div>
            <div class="stat-label">Approved</div>
          </div>
          <div class="stat-info">
            <div class="stat-number">
              <span v-if="!loading">{{ stats.approved_requests || 0 }}</span>
              <div v-else class="loading-skeleton"></div>
            </div>
          </div>
        </div>
      </div>

      <!-- Rejected Card -->
      <div class="stat-card" :class="{ 'loading': loading }">
        <div class="stat-content">
          <div class="stat-icon-label">
            <div class="stat-icon rejected">
              <svg class="icon" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
                <line x1="15" y1="9" x2="9" y2="15" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <line x1="9" y1="9" x2="15" y2="15" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
            </div>
            <div class="stat-label">Rejected</div>
          </div>
          <div class="stat-info">
            <div class="stat-number">
              <span v-if="!loading">{{ stats.rejected_requests || 0 }}</span>
              <div v-else class="loading-skeleton"></div>
            </div>
          </div>
        </div>
      </div>

      <!-- My Tasks Card -->
      <div class="stat-card" :class="{ 'loading': loading }">
        <div class="stat-content">
          <div class="stat-icon-label">
            <div class="stat-icon tasks">
              <svg class="icon" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M14 2H6C4.9 2 4 2.9 4 4V20C4 21.1 4.89 22 5.99 22H18C19.1 22 20 21.1 20 20V8L14 2Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <polyline points="14,2 14,8 20,8" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <line x1="16" y1="13" x2="8" y2="13" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <line x1="16" y1="17" x2="8" y2="17" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <polyline points="10,9 9,9 8,9" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <circle cx="18" cy="6" r="3" stroke="currentColor" stroke-width="2"/>
              </svg>
            </div>
            <div class="stat-label">My Tasks</div>
          </div>
          <div class="stat-info">
            <div class="stat-number">
              <span v-if="!loading">{{ myTasksCount }}</span>
              <div v-else class="loading-skeleton"></div>
            </div>
          </div>
        </div>
      </div>

      <!-- Recent Requests Card -->
      <div class="stat-card" :class="{ 'loading': loading }">
        <div class="stat-content">
          <div class="stat-icon-label">
            <div class="stat-icon recent">
              <svg class="icon" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
                <polyline points="12,6 12,12 16,14" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <path d="M21 12C21 16.9706 16.9706 21 12 21C7.02944 21 3 16.9706 3 12C3 7.02944 7.02944 3 12 3C16.9706 3 21 7.02944 21 12Z" stroke="currentColor" stroke-width="1.5" fill="none"/>
              </svg>
            </div>
            <div class="stat-label">Recent Requests</div>
          </div>
          <div class="stat-info">
            <div class="stat-number">
              <span v-if="!loading">{{ recentRequestsCount }}</span>
              <div v-else class="loading-skeleton"></div>
            </div>
          </div>
        </div>
      </div>

      <!-- Refresh Button Card -->
      <div class="stat-card stat-card-refresh">
        <div class="stat-content">
          <div class="stat-icon-label">
            <div class="stat-icon refresh">
              <svg class="icon" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M1 4V10H7" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <path d="M23 20V14H17" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <path d="M20.49 9C19.9828 7.56678 19.1209 6.2854 17.9845 5.27542C16.848 4.26545 15.4745 3.55976 13.9917 3.22426C12.5089 2.88876 10.9652 2.93434 9.50481 3.35677C8.04439 3.77921 6.71475 4.56471 5.64 5.64L1 10M23 14L18.36 18.36C17.2853 19.4353 15.9556 20.2208 14.4952 20.6432C13.0348 21.0657 11.4911 21.1112 10.0083 20.7757C8.52547 20.4402 7.15202 19.7345 6.01547 18.7246C4.87892 17.7146 4.01702 16.4332 3.50983 15" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
            </div>
          </div>
          <div class="stat-info">
            <button 
              class="btn btn-primary btn-small"
              @click="loadDashboardData"
              :disabled="loading"
            >
              {{ loading ? 'Loading...' : 'Refresh Data' }}
            </button>
            <div class="refresh-info">
              <small>Last updated: {{ lastUpdated || 'Never' }}</small>
            </div>
          </div>
        </div>
      </div>
    </div>


    <!-- Recent Activity -->
    <div class="row activity-row">
      <div class="col-12">
        <div class="activity-card">
          <div class="card-header">
            <div class="card-header-with-dropdown">
              <h3>Recent Requests</h3>
              <select 
                v-model="selectedRequestUser" 
                @change="loadUserRequests"
                class="user-select"
              >
                <option value="">Select User</option>
                <option
                  v-for="user in users"
                  :key="user.UserId"
                  :value="user.UserId"
                >
                  {{ user.UserName }}
                </option>
              </select>
            </div>
          </div>
          
          <div class="content-container">
            <div v-if="!hasRecentRequests" class="no-data">
              <div class="empty-state">No recent requests</div>
            </div>
            
            <div v-if="hasRecentRequests" class="request-list">
              <div 
                v-for="request in recentRequests" 
                :key="request.approval_id"
                class="request-item"
                @click="viewRequest(request.approval_id)"
              >
                <div class="request-header">
                  <span class="request-title">{{ request.request_title }}</span>
                  <div class="request-tags">
                    <span class="tag" :class="getStatusColor(request.overall_status)">
                      {{ request.overall_status }}
                    </span>
                    <span class="tag" :class="getWorkflowTypeColor(request.workflow_type)">
                      {{ formatWorkflowType(request.workflow_type) }}
                    </span>
                  </div>
                </div>
                <div class="request-meta">
                  <span class="workflow-name">{{ request.workflow_name }}</span>
                  <span class="request-date">{{ formatDate(request.created_at) }}</span>
                </div>
                <div class="request-details">
                  <span class="requester">By: {{ request.requester_id }}</span>
                  <span class="priority" :class="getPriorityClass(request.priority)">
                    {{ request.priority || 'MEDIUM' }}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="col-12">
        <div class="activity-card">
          <div class="card-header">
            <div class="card-header-with-dropdown">
              <h3>My Tasks</h3>
              <select 
                v-model="selectedTaskUser" 
                @change="loadUserTasks"
                class="user-select"
              >
                <option value="">Select User</option>
                <option
                  v-for="user in users"
                  :key="user.UserId"
                  :value="user.UserId"
                >
                  {{ user.UserName }}
                </option>
              </select>
            </div>
          </div>
          
          <div class="content-container">
            <div v-if="!hasMyTasks" class="no-data">
              <div class="empty-state">No pending tasks</div>
            </div>
            
            <div v-if="hasMyTasks" class="task-list">
              <div 
                v-for="task in myTasks" 
                :key="task.stage_id"
                class="task-item"
                @click="viewRequest(task.approval_id)"
              >
                <div class="task-header">
                  <span class="task-name">{{ task.stage_name }}</span>
                  <div class="task-tags">
                    <span class="tag" :class="getStageColor(task.stage_status)">
                      {{ task.stage_status }}
                    </span>
                    <span class="tag" :class="getWorkflowTypeColor(task.workflow_type)">
                      {{ formatWorkflowType(task.workflow_type) }}
                    </span>
                  </div>
                </div>
                <div class="task-meta">
                  <span class="request-title">{{ task.request_title }}</span>
                  <span class="deadline">{{ formatDate(task.deadline_date) }}</span>
                </div>
                <div class="task-details">
                  <span class="workflow-name">{{ task.workflow_name }}</span>
                  <span v-show="isDeadlineNear(task.deadline_date)" class="deadline-warning">
                    ⚠️ Due Soon
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import api from '@/utils/api'
import dayjs from 'dayjs'
import loggingService from '@/services/loggingService'

export default {
  name: 'VendorApprovalDashboard',
  setup() {
    const router = useRouter()
    const stats = ref({})
    const recentRequests = ref([])
    const myTasks = ref([])
    const loading = ref(false)
    const lastUpdated = ref(null)
    const users = ref([])
    const selectedRequestUser = ref('')
    const selectedTaskUser = ref('')

    // Computed properties to avoid template complexity
    const myTasksCount = computed(() => {
      return myTasks.value ? myTasks.value.length : 0
    })

    const recentRequestsCount = computed(() => {
      return recentRequests.value ? recentRequests.value.length : 0
    })

    const hasRecentRequests = computed(() => {
      return recentRequests.value && recentRequests.value.length > 0
    })

    const hasMyTasks = computed(() => {
      return myTasks.value && myTasks.value.length > 0
    })

    const loadUsers = async () => {
      try {
        console.log('Loading users...')
        const usersResponse = await api.get('/api/v1/vendor-approval/users/')
        console.log('Users response:', usersResponse.data)
        users.value = usersResponse.data
        
        // Set default selected users
        if (users.value.length > 0) {
          selectedRequestUser.value = users.value[0].UserId
          selectedTaskUser.value = users.value[0].UserId
        }
      } catch (error) {
        console.error('Error loading users:', error)
        users.value = []
      }
    }

    const loadUserRequests = async () => {
      if (!selectedRequestUser.value) return
      
      try {
        console.log('Loading requests for user:', selectedRequestUser.value)
        const response = await api.get(`/api/v1/vendor-approval/dashboard/user-requests/${selectedRequestUser.value}/`)
        console.log('User requests response:', response.data)
        recentRequests.value = response.data
      } catch (error) {
        console.error('Error loading user requests:', error)
        recentRequests.value = []
      }
    }

    const loadUserTasks = async () => {
      if (!selectedTaskUser.value) return
      
      try {
        console.log('Loading tasks for user:', selectedTaskUser.value)
        const response = await api.get(`/api/v1/vendor-approval/dashboard/user-tasks/${selectedTaskUser.value}/`)
        console.log('User tasks response:', response.data)
        myTasks.value = response.data
      } catch (error) {
        console.error('Error loading user tasks:', error)
        myTasks.value = []
      }
    }

    const loadDashboardData = async () => {
      try {
        loading.value = true
        console.log('Loading dashboard data...')
        
        // Load statistics
        console.log('Fetching stats...')
        const statsResponse = await api.get('/api/v1/vendor-approval/dashboard/stats/')
        console.log('Stats response:', statsResponse.data)
        stats.value = statsResponse.data

        // Load recent requests from database
        console.log('Fetching recent requests...')
        const recentResponse = await api.get('/api/v1/vendor-approval/dashboard/recent-requests/')
        console.log('Recent requests response:', recentResponse.data)
        recentRequests.value = recentResponse.data

        // Load my tasks from database (using current user ID)
        const currentUserId = localStorage.getItem('currentUserId') || 'admin'
        console.log('Fetching tasks for user:', currentUserId)
        const tasksResponse = await api.get(`/api/v1/vendor-approval/dashboard/user-tasks/${currentUserId}/`)
        console.log('Tasks response:', tasksResponse.data)
        myTasks.value = tasksResponse.data

        console.log('Dashboard data loaded successfully!')
        
        // Update last updated timestamp
        lastUpdated.value = new Date().toLocaleTimeString()

      } catch (error) {
        console.error('Error loading dashboard data:', error)
        console.error('Error details:', error.response?.data || error.message)
        // Set empty arrays on error
        recentRequests.value = []
        myTasks.value = []
      } finally {
        loading.value = false
      }
    }

    const viewRequest = (approvalId) => {
      router.push(`/review/${approvalId}`)
    }


    const getStatusColor = (status) => {
      const colors = {
        'DRAFT': 'info',
        'PENDING': 'warning',
        'IN_PROGRESS': 'primary',
        'APPROVED': 'success',
        'REJECTED': 'danger'
      }
      return colors[status] || 'info'
    }

    const getStageColor = (status) => {
      const colors = {
        'PENDING': 'info',
        'IN_PROGRESS': 'warning',
        'APPROVED': 'success',
        'REJECTED': 'danger'
      }
      return colors[status] || 'info'
    }

    const getWorkflowTypeColor = (type) => {
      const colors = {
        'MULTI_LEVEL': 'primary',
        'MULTI_PERSON': 'success'
      }
      return colors[type] || 'info'
    }

    const formatWorkflowType = (type) => {
      if (!type) return 'Unknown'
      const typeStr = String(type).toUpperCase()
      if (typeStr === 'MULTI_LEVEL') return 'Tiered Approval'
      if (typeStr === 'MULTI_PERSON') return 'Team Approval'
      return type
    }

    const getPriorityClass = (priority) => {
      if (!priority) return 'priority-medium'
      return `priority-${priority.toLowerCase()}`
    }

    const formatDate = (date) => {
      if (!date) return 'Not set'
      return dayjs(date).format('MMM DD, YYYY')
    }

    const isDeadlineNear = (deadlineDate) => {
      if (!deadlineDate) return false
      const deadline = dayjs(deadlineDate)
      const now = dayjs()
      const daysUntilDeadline = deadline.diff(now, 'day')
      return daysUntilDeadline <= 3 && daysUntilDeadline >= 0
    }

    onMounted(async () => {
      await loggingService.logPageView('Vendor', 'Vendor Approval Dashboard (Alt)')
      await loadUsers()
      await loadDashboardData()
    })

    return {
      stats,
      recentRequests,
      myTasks,
      loading,
      lastUpdated,
      users,
      selectedRequestUser,
      selectedTaskUser,
      myTasksCount,
      recentRequestsCount,
      hasRecentRequests,
      hasMyTasks,
      loadDashboardData,
      loadUsers,
      loadUserRequests,
      loadUserTasks,
      viewRequest,
      getStatusColor,
      getStageColor,
      getWorkflowTypeColor,
      formatWorkflowType,
      getPriorityClass,
      formatDate,
      isDeadlineNear
    }
  }
}
</script>

<style scoped>
/* Dashboard Container */
.dashboard {
  max-width: 1400px;
  margin: 0 auto;
  padding: 32px 24px;
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
  min-height: 100vh;
}

.dashboard-title {
  margin: 0 0 12px 0;
  color: #1e293b;
  font-size: 32px;
  font-weight: 700;
  letter-spacing: -0.025em;
  line-height: 1.2;
}

.dashboard-subtitle {
  margin: 0 0 40px 0;
  color: #64748b;
  font-size: 18px;
  font-weight: 400;
  line-height: 1.5;
}

/* Grid System */
.row {
  display: flex;
  flex-wrap: wrap;
  margin: 0 -12px;
  gap: 0;
}

.col-24 {
  flex: 0 0 100%;
  max-width: 100%;
  padding: 0 12px;
}

.col-12 {
  flex: 0 0 50%;
  max-width: 50%;
  padding: 0 12px;
}

.col-6 {
  flex: 0 0 25%;
  max-width: 25%;
  padding: 0 12px;
}

/* Statistics Grid */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
  margin-bottom: 40px;
}

/* Statistics Cards */
.stat-card {
  border-radius: 16px;
  background: #ffffff;
  border: 1px solid rgba(226, 232, 240, 0.8);
  box-shadow: 0 4px 12px rgba(15, 23, 42, 0.08);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  padding: 24px;
  position: relative;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.stat-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 24px rgba(15, 23, 42, 0.12);
  border-color: rgba(148, 163, 184, 0.5);
}

.stat-card.stat-card-refresh {
  justify-content: center;
}

.stat-content {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 12px;
}

.stat-icon-label {
  display: flex;
  align-items: center;
  gap: 12px;
  width: 100%;
}

.stat-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  position: relative;
  overflow: hidden;
}

.stat-icon::after {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  opacity: 0;
  transition: opacity 0.3s ease;
}

.stat-icon:hover::after {
  opacity: 1;
}

.stat-icon .icon {
  width: 24px;
  height: 24px;
  stroke: currentColor;
  fill: none;
  stroke-width: 2;
  position: relative;
  z-index: 1;
}

.stat-icon.total {
  background: linear-gradient(135deg, #3b82f6 0%, #1e40af 100%);
  color: #ffffff;
}

.stat-icon.pending {
  background: linear-gradient(135deg, #ef4444 0%, #b91c1c 100%);
  color: #ffffff;
}

.stat-icon.in-progress {
  background: linear-gradient(135deg, #10b981 0%, #047857 100%);
  color: #ffffff;
}

.stat-icon.approved {
  background: linear-gradient(135deg, #8b5cf6 0%, #6d28d9 100%);
  color: #ffffff;
}

.stat-icon.rejected {
  background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
  color: #ffffff;
}

.stat-icon.tasks {
  background: linear-gradient(135deg, #06b6d4 0%, #0891b2 100%);
  color: #ffffff;
}

.stat-icon.recent {
  background: linear-gradient(135deg, #ec4899 0%, #be185d 100%);
  color: #ffffff;
}

.stat-icon.refresh {
  background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%);
  color: #ffffff;
}

.stat-info {
  width: 100%;
}

.stat-number {
  font-size: 36px;
  font-weight: 800;
  color: #0f172a;
  line-height: 1;
  letter-spacing: -0.025em;
}

.stat-label {
  font-size: 13px;
  color: #64748b;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  white-space: nowrap;
}

/* Buttons */
.btn {
  padding: 10px 20px;
  border: none;
  border-radius: 12px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 600;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  text-decoration: none;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  text-align: center;
  position: relative;
  overflow: hidden;
}

.btn::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
  transition: left 0.5s;
}

.btn:hover::before {
  left: 100%;
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none !important;
}

.btn-primary {
  background: linear-gradient(135deg, #bfdbfe 0%, #a5b4fc 100%);
  color: #1e3a8a;
  box-shadow: 0 4px 14px 0 rgba(148, 163, 184, 0.3);
}

.btn-primary:hover:not(:disabled) {
  background: linear-gradient(135deg, #cbd5f5 0%, #c7d2fe 100%);
  transform: translateY(-2px);
  box-shadow: 0 8px 25px 0 rgba(148, 163, 184, 0.35);
}

.btn-success {
  background-color: #bbf7d0;
  color: #166534;
}

.btn-success:hover:not(:disabled) {
  background-color: #a7f3ce;
}

.btn-warning {
  background-color: #fde68a;
  color: #b45309;
}

.btn-warning:hover:not(:disabled) {
  background-color: #fcd34d;
}

.btn-info {
  background-color: #e2e8f0;
  color: #475569;
}

.btn-info:hover:not(:disabled) {
  background-color: #cbd5f5;
}

.btn-small {
  padding: 6px 12px;
  font-size: 12px;
}

.btn-large {
  padding: 12px 24px;
  font-size: 16px;
}


/* Activity Cards */
.activity-row {
  margin-bottom: 40px;
}


.activity-card {
  border-radius: 20px;
  background: #ffffff;
  border: 1px solid rgba(226, 232, 240, 0.8);
  box-shadow: 0 14px 32px -16px rgba(148, 163, 184, 0.5);
  height: 520px;
  display: flex;
  flex-direction: column;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;
}

.activity-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 28px 46px -24px rgba(148, 163, 184, 0.6);
}

.card-header-with-dropdown {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 24px 24px 0 24px;
  margin-top: 4px;
}

.card-header-with-dropdown h3 {
  margin: 0;
  color: #1e293b;
  font-size: 20px;
  font-weight: 700;
  letter-spacing: -0.025em;
}

.user-select {
  padding: 10px 16px;
  border: 2px solid #e2e8f0;
  border-radius: 12px;
  font-size: 14px;
  font-weight: 500;
  background-color: #fff;
  min-width: 200px;
  transition: all 0.3s ease;
  color: #475569;
}

.user-select:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.content-container {
  flex: 1;
  padding: 24px;
  overflow: hidden;
}

.no-data {
  padding: 40px 20px;
  text-align: center;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.empty-state {
  color: #909399;
  font-size: 14px;
}

.request-list,
.task-list {
  height: 100%;
  overflow-y: auto;
}

.request-item,
.task-item {
  padding: 20px;
  border: 1px solid #f1f5f9;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  border-radius: 12px;
  margin-bottom: 12px;
  background: #ffffff;
  position: relative;
  overflow: hidden;
}

.request-item:hover,
.task-item:hover {
  background-color: #f1f5f9;
  border-color: #cbd5e1;
  transform: translateX(4px);
  box-shadow: 0 4px 12px rgba(148, 163, 184, 0.25);
}

.request-item:last-child,
.task-item:last-child {
  border-bottom: none;
  margin-bottom: 0;
}

.request-header,
.task-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 8px;
}

.request-title,
.task-name {
  font-weight: 700;
  color: #1e293b;
  flex: 1;
  margin-right: 10px;
  font-size: 15px;
  line-height: 1.4;
}

.request-tags,
.task-tags {
  display: flex;
  gap: 5px;
  flex-shrink: 0;
}

.tag {
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.tag.info {
  background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
  color: #475569;
  border: 1px solid #cbd5e1;
}

.tag.warning {
  background: linear-gradient(135deg, #fdf4ff 0%, #fde68a 100%);
  color: #b45309;
  border: 1px solid #fcd34d;
}

.tag.primary {
  background: linear-gradient(135deg, #eef2ff 0%, #dbeafe 100%);
  color: #4338ca;
  border: 1px solid #c7d2fe;
}

.tag.success {
  background: linear-gradient(135deg, #ecfdf5 0%, #d1fae5 100%);
  color: #15803d;
  border: 1px solid #86efac;
}

.tag.danger {
  background: linear-gradient(135deg, #fee2e2 0%, #fbcfe8 100%);
  color: #b91c1c;
  border: 1px solid #fda4af;
}

.request-meta,
.task-meta {
  display: flex;
  justify-content: space-between;
  margin-bottom: 5px;
  font-size: 14px;
  color: #666;
}

.request-details,
.task-details {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 12px;
  color: #999;
}

.priority-high {
  color: #f87171;
  font-weight: 600;
}

.priority-medium {
  color: #fbbf24;
  font-weight: 600;
}

.priority-low {
  color: #34d399;
  font-weight: 600;
}

.deadline-warning {
  color: #f59e0b;
  font-weight: 600;
}

.refresh-info {
  margin-top: 8px;
  text-align: center;
}

.refresh-info small {
  color: #909399;
  font-size: 11px;
}

/* Responsive Design */
@media (max-width: 1400px) {
  .dashboard {
    padding: 28px 20px;
  }
  
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 1024px) {
  .dashboard {
    padding: 24px 16px;
  }
  
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 16px;
  }
  
  .col-6 {
    flex: 0 0 50%;
    max-width: 50%;
  }
}

@media (max-width: 768px) {
  .dashboard {
    padding: 20px 12px;
  }
  
  .dashboard-title {
    font-size: 28px;
  }
  
  .dashboard-subtitle {
    font-size: 16px;
  }
  
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 12px;
    margin-bottom: 32px;
  }
  
  .col-6 {
    flex: 0 0 100%;
    max-width: 100%;
    margin-bottom: 16px;
  }
  
  .col-12 {
    flex: 0 0 100%;
    max-width: 100%;
    margin-bottom: 24px;
  }
  
  .stat-card {
    padding: 18px;
  }
  
  .stat-icon-label {
    gap: 10px;
  }
  
  .stat-icon {
    width: 44px;
    height: 44px;
    border-radius: 10px;
  }
  
  .stat-icon .icon {
    width: 22px;
    height: 22px;
  }
  
  .stat-number {
    font-size: 32px;
  }
  
  .stat-label {
    font-size: 12px;
  }
  
  .card-header-with-dropdown {
    flex-direction: column;
    gap: 12px;
    align-items: flex-start;
  }
  
  .user-select {
    width: 100% !important;
    min-width: auto;
  }
  
  .activity-card {
    height: 480px;
  }
  
  .request-item,
  .task-item {
    padding: 16px;
  }
}

@media (max-width: 480px) {
  .dashboard {
    padding: 16px 8px;
  }
  
  .dashboard-title {
    font-size: 24px;
  }
  
  .dashboard-subtitle {
    font-size: 14px;
    margin-bottom: 24px;
  }
  
  .stats-grid {
    grid-template-columns: 1fr;
    gap: 12px;
  }
  
  .stat-card {
    padding: 16px;
  }
  
  .stat-icon-label {
    gap: 10px;
  }
  
  .stat-icon {
    width: 40px;
    height: 40px;
  }
  
  .stat-icon .icon {
    width: 20px;
    height: 20px;
  }
  
  .stat-number {
    font-size: 28px;
  }
  
  .stat-label {
    font-size: 11px;
  }
}

/* Loading States and Animations */
.loading-skeleton {
  width: 60px;
  height: 36px;
  background: linear-gradient(90deg, #f1f5f9 25%, #e2e8f0 50%, #f1f5f9 75%);
  background-size: 200% 100%;
  animation: loading 1.5s infinite;
  border-radius: 8px;
}

.stat-card.loading {
  pointer-events: none;
}

.stat-card.loading .stat-icon {
  opacity: 0.7;
}

@keyframes loading {
  0% {
    background-position: 200% 0;
  }
  100% {
    background-position: -200% 0;
  }
}

/* Fade in animation for content */
.stat-card {
  animation: fadeInUp 0.6s ease-out;
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* Staggered animation for stat cards */
.stat-card:nth-child(1) { animation-delay: 0.1s; }
.stat-card:nth-child(2) { animation-delay: 0.2s; }
.stat-card:nth-child(3) { animation-delay: 0.3s; }
.stat-card:nth-child(4) { animation-delay: 0.4s; }

.activity-card {
  animation: fadeInUp 0.8s ease-out;
}

.activity-card:nth-child(1) { animation-delay: 0.2s; }
.activity-card:nth-child(2) { animation-delay: 0.4s; }
</style>