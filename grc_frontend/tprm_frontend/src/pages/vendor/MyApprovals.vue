<template>
  <div class="vendor_space-y-6 my-approvals-wrapper">
    <div class="filters-bar">
      <div class="filters-group">
        <label class="filters-label" for="approvals-search">Search</label>
        <input
          id="approvals-search"
          v-model="searchTerm"
          type="text"
          class="filters-input"
          placeholder="Search by title, approval ID or stage"
        />
      </div>

      <div class="filters-group">
        <label class="filters-label" for="priority-filter">Priority</label>
        <select id="priority-filter" v-model="selectedPriority" class="filters-select">
          <option v-for="option in priorityOptions" :key="option" :value="option">
            {{ option === 'ALL' ? 'All priorities' : option }}
          </option>
        </select>
      </div>

      <div class="filters-group">
        <label class="filters-label" for="status-filter">Status</label>
        <select id="status-filter" v-model="selectedStatus" class="filters-select">
          <option v-for="option in statusOptions" :key="option" :value="option">
            {{ option === 'ALL' ? 'All statuses' : option }}
          </option>
        </select>
      </div>
    </div>

    <div class="my-approvals-two-col">
      <div class="vendor_card my-approvals-col">
        <div class="vendor_card-header">
          <h2 class="vendor_card-title">Team Approval requests</h2>
          <p class="vendor_card-description">Requests assigned to multiple approvers simultaneously</p>
        </div>
        <div class="vendor_card-content vendor_space-y-3">
          <div v-if="!filteredParallel.length" class="vendor_text-sm vendor_text-muted-foreground empty-state">No team approval requests</div>
          <div 
            v-for="item in filteredParallel" 
            :key="item.stage.stage_id" 
            class="vendor_border vendor_rounded vendor_p-3 vendor_flex vendor_justify-between vendor_items-start vendor_cursor-pointer approval-item"
            @click="openStage(item)"
          >
            <div>
              <div class="vendor_font-medium">{{ item.request_title }}</div>
              <div class="vendor_text-xs vendor_text-muted-foreground">Stage: {{ item.stage.stage_name }} • Order {{ item.stage.stage_order }}</div>
              <div class="vendor_text-xs vendor_text-muted-foreground">Priority: {{ item.priority }} • Status: {{ item.stage.stage_status }}</div>
            </div>
            <div class="vendor_text-right vendor_text-xs vendor_text-muted-foreground">
              <div>Approval: {{ item.approval_id }}</div>
              <div v-if="item.stage.deadline_date">Due: {{ formatDate(item.stage.deadline_date) }}</div>
            </div>
          </div>
        </div>
      </div>

      <div class="vendor_card my-approvals-col">
        <div class="vendor_card-header">
          <h2 class="vendor_card-title">Tiered Approval requests</h2>
          <p class="vendor_card-description">Requests progressing across ordered approval stages</p>
        </div>
        <div class="vendor_card-content vendor_space-y-3">
          <div v-if="!filteredSequential.length" class="vendor_text-sm vendor_text-muted-foreground empty-state">No tiered approval requests</div>
          <div 
            v-for="item in filteredSequential" 
            :key="item.stage.stage_id" 
            class="vendor_border vendor_rounded vendor_p-3 vendor_flex vendor_justify-between vendor_items-start vendor_cursor-pointer approval-item"
            @click="openStage(item)"
          >
            <div>
              <div class="vendor_font-medium">{{ item.request_title }}</div>
              <div class="vendor_text-xs vendor_text-muted-foreground">Stage: {{ item.stage.stage_name }} • Order {{ item.stage.stage_order }}</div>
              <div class="vendor_text-xs vendor_text-muted-foreground">Priority: {{ item.priority }} • Status: {{ item.stage.stage_status }}</div>
            </div>
            <div class="vendor_text-right vendor_text-xs vendor_text-muted-foreground">
              <div>Approval: {{ item.approval_id }}</div>
              <div v-if="item.stage.deadline_date">Due: {{ formatDate(item.stage.deadline_date) }}</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useStore } from 'vuex'
import api from '@/utils/api'
import loggingService from '@/services/loggingService'

const loading = ref(false)
const parallel = ref([])
const sequential = ref([])
const selectedPriority = ref('ALL')
const selectedStatus = ref('ALL')
const searchTerm = ref('')
const router = useRouter()

// Get current user from localStorage with Vuex fallback
const getCurrentUserId = () => {
  try {
    console.log('=== USER ID RESOLUTION DEBUG ===')
    
    // First, try to get user_id directly from localStorage (set by App.vue)
    const directUserId = localStorage.getItem('user_id')
    if (directUserId) {
      console.log('✅ Found user_id directly in localStorage:', directUserId)
      return parseInt(directUserId) || directUserId
    }
    
    // Second, try to get user from Vuex store (most reliable source)
    try {
      const store = useStore()
      const vuexUser = store.getters['auth/currentUser']
      console.log('Vuex store user:', vuexUser)
      
      if (vuexUser) {
        // Try all possible user ID field names
        const userId = vuexUser.UserId || vuexUser.userId || vuexUser.user_id || vuexUser.id || vuexUser.userid
        if (userId) {
          console.log('✅ Using Vuex store user ID:', userId)
          return parseInt(userId) || userId
        }
      }
    } catch (vuexError) {
      console.log('Could not access Vuex store:', vuexError.message)
    }
    
    // Fallback to localStorage - check both 'current_user' and 'user' keys
    console.log('Vuex store not available, trying localStorage...')
    
    // Try 'current_user' first (preferred)
    let currentUserFromStorage = localStorage.getItem('current_user')
    console.log('localStorage.getItem("current_user"):', currentUserFromStorage ? 'Found' : 'Not found')
    
    // If not found, try 'user' key as fallback
    if (!currentUserFromStorage) {
      currentUserFromStorage = localStorage.getItem('user')
      console.log('localStorage.getItem("user"):', currentUserFromStorage ? 'Found' : 'Not found')
    }
    
    if (currentUserFromStorage) {
      try {
        const user = JSON.parse(currentUserFromStorage)
        console.log('Parsed user object keys:', Object.keys(user))
        
        // Try ALL possible user ID field names (including UserId with capital U and I)
        const userId = user.UserId || user.userId || user.user_id || user.id || user.userid || user.UserID
        console.log('Available userId from localStorage:', userId)
        
        if (userId) {
          console.log('✅ Using localStorage userId:', userId)
          return parseInt(userId) || userId
        } else {
          console.warn('User object found but no ID field detected. Available fields:', Object.keys(user))
        }
      } catch (parseError) {
        console.error('Error parsing user from localStorage:', parseError)
      }
    }
    
    console.log('❌ No user ID found in localStorage or Vuex store')
    return null
  } catch (error) {
    console.error('Error getting current user:', error)
    return null
  }
}

const loadApprovals = async (retryCount = 0) => {
  const maxRetries = 5
  const retryDelay = 500 // 500ms delay between retries
  
  let currentUserId = getCurrentUserId()
  
  // If user ID not found and we haven't exceeded retries, wait and retry
  // This handles race condition where auth sync hasn't completed yet
  if (!currentUserId && retryCount < maxRetries) {
    console.log(`User ID not found yet, retrying... (attempt ${retryCount + 1}/${maxRetries})`)
    await new Promise(resolve => setTimeout(resolve, retryDelay))
    return loadApprovals(retryCount + 1)
  }
  
  if (!currentUserId) {
    console.error('No current user found in localStorage or Vuex store after retries')
    console.error('User may not be properly logged in. Please refresh the page or log in again.')
    console.error('Available localStorage keys:', Object.keys(localStorage).filter(k => k.includes('user') || k.includes('token')))
    loading.value = false
    return
  }
  
  loading.value = true
  try {
    console.log('Loading approvals for user ID:', currentUserId)
    const res = await api.get('/api/v1/vendor-approval/my-approvals/', {
      params: { user_id: currentUserId }
    })
    console.log('Approvals API response:', res.data)
    parallel.value = res.data?.parallel || []
    sequential.value = res.data?.sequential || []
    console.log('Loaded parallel requests:', parallel.value.length)
    console.log('Loaded sequential requests:', sequential.value.length)
  } catch (e) {
    console.error('Error loading approvals:', e)
    parallel.value = []
    sequential.value = []
  } finally {
    loading.value = false
  }
}

const formatDate = (d) => {
  if (!d) return ''
  try { return new Date(d).toLocaleString() } catch { return d }
}

const priorityOptions = computed(() => {
  const values = new Set()
  ;[...parallel.value, ...sequential.value].forEach(item => {
    const priority = (item.priority || '').toString().toUpperCase()
    if (priority) values.add(priority)
  })
  return ['ALL', ...values]
})

const statusOptions = computed(() => {
  const values = new Set()
  ;[...parallel.value, ...sequential.value].forEach(item => {
    const status = (item.stage?.stage_status || item.status || '').toString().toUpperCase()
    if (status) values.add(status)
  })
  return ['ALL', ...values]
})

const applyFilters = (items) => {
  const term = searchTerm.value.trim().toLowerCase()
  const priorityFilter = selectedPriority.value
  const statusFilter = selectedStatus.value

  return items.filter(item => {
    const priority = (item.priority || '').toString().toUpperCase()
    const status = (item.stage?.stage_status || item.status || '').toString().toUpperCase()

    const matchesPriority = priorityFilter === 'ALL' || priority === priorityFilter
    const matchesStatus = statusFilter === 'ALL' || status === statusFilter

    const haystack = `${item.request_title || ''} ${item.approval_id || ''} ${item.stage?.stage_name || ''}`.toLowerCase()
    const matchesSearch = !term || haystack.includes(term)

    return matchesPriority && matchesStatus && matchesSearch
  })
}

const filteredParallel = computed(() => applyFilters(parallel.value))
const filteredSequential = computed(() => applyFilters(sequential.value))

// Listen for auth sync messages from parent (GRC) to reload approvals when user data becomes available
let authMessageHandler = null

onMounted(async () => {
  await loggingService.logPageView('Vendor', 'My Approvals')
  
  // Set up message listener for auth sync
  authMessageHandler = (event) => {
    if (event.data && event.data.type === 'GRC_AUTH_SYNC' && event.data.user) {
      console.log('[MyApprovals] Received auth sync, reloading approvals...')
      // Wait a bit for localStorage to be updated
      setTimeout(() => {
        loadApprovals()
      }, 100)
    }
  }
  
  window.addEventListener('message', authMessageHandler)
  
  // Initial load with retry mechanism
  await loadApprovals()
})

onUnmounted(() => {
  // Clean up message listener
  if (authMessageHandler) {
    window.removeEventListener('message', authMessageHandler)
  }
})

const openStage = (item) => {
  const currentUserId = getCurrentUserId()
  router.push({
    name: 'Vendor Stage Reviewer',
    query: { user_id: currentUserId, stage_id: item.stage.stage_id }
  })
}
</script>

<style scoped>
/* Base styles for vendor components */

.my-approvals-wrapper {
  padding: clamp(1.5rem, 3vw + 1rem, 3rem);
  background: #f5f7fb;
  min-height: 100vh;
}


.filters-bar {
  display: flex;
  flex-wrap: wrap;
  gap: 1.25rem;
  align-items: flex-end;
  background: #ffffff;
  border: 1px solid rgba(148, 163, 184, 0.2);
  border-radius: 0.75rem;
  padding: 1rem 1.25rem;
  box-shadow: 0 10px 24px -18px rgba(15, 23, 42, 0.35);
}

.filters-group {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
  min-width: clamp(180px, 25vw, 260px);
}

.filters-label {
  font-size: 0.8rem;
  font-weight: 600;
  color: #475569;
  letter-spacing: 0.02em;
}

.filters-input,
.filters-select {
  appearance: none;
  border: 1px solid rgba(148, 163, 184, 0.35);
  border-radius: 0.65rem;
  padding: 0.6rem 0.75rem;
  font-size: 0.9rem;
  background: #ffffff;
  color: #0f172a;
  transition: border-color 0.2s ease, box-shadow 0.2s ease;
}

.filters-input:focus,
.filters-select:focus {
  outline: none;
  border-color: rgba(59, 130, 246, 0.45);
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.15);
}


.vendor_card { 
  position: relative;
  border: 1px solid rgba(148, 163, 184, 0.25); 
  border-radius: 0.75rem; 
  background: #ffffff; 
  box-shadow: 0 18px 35px -25px rgba(15, 23, 42, 0.35);
  overflow: hidden;
  transition: transform 0.25s ease, box-shadow 0.25s ease, border-color 0.25s ease;
}

.vendor_card:hover {
  transform: translateY(-4px);
  box-shadow: 0 22px 40px -22px rgba(15, 23, 42, 0.45);
  border-color: rgba(59, 130, 246, 0.25);
}

.vendor_card-header { 
  padding: 1.25rem 1.5rem; 
  border-bottom: none; 
  background: transparent;
  position: relative;
}

.vendor_card-header::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 1.5rem;
  right: 1.5rem;
  height: 3px;
  border-radius: 9999px;
  background: #60a5fa;
}

.vendor_card-title { 
  font-weight: 700; 
  font-size: 1.2rem;
  color: #0f172a;
  margin: 0;
  letter-spacing: -0.015em;
}

.vendor_card-description { 
  font-size: 0.9rem; 
  color: #64748b; 
  margin: 0.35rem 0 0 0;
}

.vendor_card-content { 
  padding: 1.25rem 1.5rem 1.75rem; 
  flex: 1 1 auto;
  overflow-y: auto;
}

.vendor_card-content::-webkit-scrollbar {
  width: 8px;
}

.vendor_card-content::-webkit-scrollbar-track {
  background: rgba(226, 232, 240, 0.6);
  border-radius: 9999px;
}

.vendor_card-content::-webkit-scrollbar-thumb {
  background: rgba(148, 163, 184, 0.6);
  border-radius: 9999px;
}

/* Utility classes */
.vendor_space-y-6 > * + * { margin-top: 1.5rem; }
.vendor_space-y-3 > * + * { margin-top: 0.75rem; }
.vendor_flex { display: flex; }
.vendor_items-start { align-items: flex-start; }
.vendor_text-sm { font-size: 0.875rem; }
.vendor_text-xs { font-size: 0.75rem; }
.vendor_text-muted-foreground { color: #6b7280; }
.vendor_font-medium { font-weight: 500; }
.vendor_border { border: 1px solid #e5e7eb; }
.vendor_rounded { border-radius: 0.375rem; }
.vendor_p-3 { padding: 0.75rem; }
.vendor_justify-between { justify-content: space-between; }
.vendor_cursor-pointer { cursor: pointer; }
.vendor_text-right { text-align: right; }

.approval-item {
  position: relative;
  background: #ffffff;
  border: 1px solid rgba(148, 163, 184, 0.25);
  box-shadow: 0 12px 18px -18px rgba(15, 23, 42, 0.4);
  transition: all 0.25s ease;
  overflow: hidden;
}

.approval-item::before {
  content: none;
}

.approval-item:hover {
  transform: translateY(-2px) translateX(2px);
  border-color: rgba(59, 130, 246, 0.35);
  box-shadow: 0 16px 24px -18px rgba(59, 130, 246, 0.35);
  background: #f1f5f9;
}

.approval-item .vendor_font-medium {
  font-size: 1rem;
  font-weight: 600;
  color: #0f172a;
  margin-bottom: 0.4rem;
}

.approval-item .vendor_text-muted-foreground {
  color: #64748b;
}

.approval-item .vendor_text-right {
  color: #475569;
}

.approval-item .vendor_text-right div:first-child {
  font-weight: 600;
  color: #0f172a;
}

.approval-item:hover .vendor_font-medium {
  color: #1d4ed8;
}

.empty-state {
  padding: 1.25rem;
  border-radius: 0.65rem;
  background: #f1f5f9;
  border: 1px dashed rgba(148, 163, 184, 0.35);
  text-align: center;
  font-weight: 500;
  letter-spacing: 0.02em;
}

/* Ensure the two sections are adjacent */
.my-approvals-two-col { 
  position: relative;
  display: flex; 
  gap: 1.75rem; 
  align-items: stretch; 
  margin-top: 1.5rem;
}

.my-approvals-col { 
  flex: 1 1 0; 
  min-width: 0; 
  max-height: 70vh;
  display: flex;
  flex-direction: column;
}

/* Responsive design */
@media (max-width: 768px) {
  .my-approvals-wrapper {
    padding: 1.25rem;
  }

  .filters-bar {
    padding: 0.85rem 1rem;
  }

  .filters-group {
    min-width: 100%;
  }

  .my-approvals-two-col {
    flex-direction: column;
    gap: 1rem;
  }

  .vendor_card {
    border-radius: 0.65rem;
  }
}
</style>


