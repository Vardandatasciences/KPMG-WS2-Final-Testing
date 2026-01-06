<template>
  <div class="questionnaire-assignment">
    <!-- Header -->
    <div class="assignment-header">
      <div class="header-content">
        <div class="header-info">
          <h1 class="page-title">Questionnaire Assignment</h1>
          <p class="page-subtitle">Assign questionnaires to vendors for completion</p>
        </div>
        <div class="header-actions">
          <button @click="openAssignmentModal" class="btn-primary">
            <svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6"/>
            </svg>
            New Assignment
          </button>
        </div>
      </div>
    </div>

    <!-- Main Content -->
    <div class="assignment-content">
      <!-- Stats Cards -->
      <div class="stats-grid">
        <div class="stat-card">
          <div class="stat-header">
            <svg class="stat-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"/>
            </svg>
            <span class="stat-label">Total Assignments</span>
          </div>
          <div class="stat-value">{{ Array.isArray(assignments) ? assignments.length : 0 }}</div>
        </div>
        
        <div class="stat-card">
          <div class="stat-header">
            <svg class="stat-icon pending" viewBox="0 0 24 24" fill="none" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3"/>
              <circle cx="12" cy="12" r="10"/>
            </svg>
            <span class="stat-label">Pending</span>
          </div>
          <div class="stat-value">{{ getStatusCount('ASSIGNED') }}</div>
        </div>
        
        <div class="stat-card">
          <div class="stat-header">
            <svg class="stat-icon progress" viewBox="0 0 24 24" fill="none" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"/>
            </svg>
            <span class="stat-label">In Progress</span>
          </div>
          <div class="stat-value">{{ getStatusCount('IN_PROGRESS') }}</div>
        </div>
        
        <div class="stat-card">
          <div class="stat-header">
            <svg class="stat-icon completed" viewBox="0 0 24 24" fill="none" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4"/>
              <circle cx="12" cy="12" r="10"/>
            </svg>
            <span class="stat-label">Completed</span>
          </div>
          <div class="stat-value">{{ getStatusCount('SUBMITTED') + getStatusCount('RESPONDED') + getStatusCount('COMPLETED') }}</div>
        </div>
      </div>

      <!-- Filters -->
      <div class="filters-row">
        <div class="filter-group">
          <label class="filter-label">Status</label>
          <select v-model="filters.status" class="filter-select">
            <option value="">All Statuses</option>
            <option value="ASSIGNED">Assigned</option>
            <option value="IN_PROGRESS">In Progress</option>
            <option value="SUBMITTED">Responded</option>
            <option value="RESPONDED">Responded</option>
            <option value="COMPLETED">Completed</option>
            <option value="OVERDUE">Overdue</option>
          </select>
        </div>
        
        <div class="filter-group">
          <label class="filter-label">Questionnaire</label>
          <select v-model="filters.questionnaire" class="filter-select">
            <option value="">All Questionnaires</option>
            <option v-for="q in questionnaires" :key="q.questionnaire_id" :value="q.questionnaire_id">
              {{ q.questionnaire_name }}
            </option>
          </select>
        </div>
        
        <div class="filter-group">
          <label class="filter-label">Search</label>
          <input 
            v-model="filters.search" 
            type="text" 
            placeholder="Search vendors..." 
            class="filter-input"
          />
        </div>
      </div>

      <!-- Assignments Table -->
      <div class="assignments-table-section">
        <div class="table-container">
          <table class="assignments-table">
            <thead>
              <tr>
                <th>Vendor</th>
                <th>Questionnaire</th>
                <th>Status</th>
                <th>Assigned Date</th>
                <th>Due Date</th>
                <th>Progress</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="assignment in filteredAssignments" :key="assignment.assignment_id" class="assignment-row">
                <td>
                  <div class="vendor-info">
                    <div class="vendor-name">{{ assignment.vendor_name }}</div>
                  </div>
                </td>
                <td>
                  <div class="questionnaire-info">
                    <div class="questionnaire-name">{{ assignment.questionnaire_name }}</div>
                  </div>
                </td>
                <td>
                  <span :class="['status-badge', assignment.status.toLowerCase()]">
                    {{ formatStatus(assignment.status) }}
                  </span>
                </td>
                <td>{{ formatDate(assignment.assigned_date) }}</td>
                <td>{{ formatDate(assignment.due_date) || 'No due date' }}</td>
                <td>
                  <div class="progress-cell">
                    <div class="progress-bar">
                      <div class="progress-fill" :style="{ width: `${getProgressPercentage(assignment)}%` }"></div>
                    </div>
                    
                  </div>
                </td>
                <td>
                  <div class="action-buttons">
                    <button @click="viewAssignment(assignment)" class="btn-action btn-view" title="View Details">
                      <svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/>
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"/>
                      </svg>
                    </button>
                    <button @click="updateStatus(assignment)" class="btn-action btn-edit" title="Update Status">
                      <svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"/>
                      </svg>
                    </button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
          
          <div v-if="filteredAssignments.length === 0" class="empty-state">
            <svg class="empty-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"/>
            </svg>
            <h3>No assignments found</h3>
            <p>No questionnaire assignments match your current filters.</p>
          </div>
        </div>
      </div>
    </div>

    <!-- Assignment Modal -->
    <div v-if="showAssignmentModal" class="modal-overlay" @click="closeModal">
      <div class="modal-content" @click.stop>
        <!-- Close Button in Corner -->
        <button @click="closeModal" class="btn-close-corner">
          <svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
          </svg>
        </button>
        
        <div class="modal-header">
          <h2>Create New Assignment</h2>
        </div>
        
        <div class="modal-body">
          <form @submit.prevent="createAssignment" class="form-grid">
            <div class="form-group">
              <label class="form-label">Select Questionnaire</label>
              <select v-model="newAssignment.questionnaire_id" class="form-select" required>
                <option value="">Choose a questionnaire...</option>
                <option v-for="q in questionnaires" :key="q.questionnaire_id" :value="q.questionnaire_id">
                  {{ q.questionnaire_name }} ({{ q.question_count }} questions)
                </option>
              </select>
            </div>
            
            <div class="form-group">
              <label class="form-label">Select Vendor</label>
              <select v-model="newAssignment.vendor_id" class="form-select" required>
                <option value="">Choose a vendor...</option>
                <option v-for="vendor in vendors" :key="vendor.id" :value="vendor.id">
                  {{ vendor.company_name }} ({{ vendor.vendor_category || 'No category' }})
                </option>
              </select>
            </div>
            
            <div class="form-group compact">
              <label class="form-label">Due Date (Optional)</label>
              <div class="date-input">
                <input 
                  v-model="newAssignment.due_date" 
                  type="date" 
                  class="form-input date-input-field"
                />
                <CalendarIcon class="date-input-icon" />
              </div>
            </div>
            
            <div class="form-group span-2">
              <label class="form-label">Notes (Optional)</label>
              <textarea 
                v-model="newAssignment.notes" 
                class="form-textarea" 
                rows="3"
                placeholder="Add any additional notes for this assignment..."
              ></textarea>
            </div>
          </form>
        </div>
        
        <div class="modal-footer">
          <button @click="closeModal" class="btn-secondary">Cancel</button>
          <button @click="createAssignment" class="btn-primary" :disabled="!canCreateAssignment">
            Create Assignment
          </button>
        </div>
      </div>
    </div>
  </div>

  <!-- Popup Modal -->
  <PopupModal />
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { Calendar as CalendarIcon } from 'lucide-vue-next'
import { apiCall } from '@/utils/api'
import PopupModal from '@/popup/PopupModal.vue'
import { PopupService } from '@/popup/popupService'
import loggingService from '@/services/loggingService'

// Reactive data
const assignments = ref([])
const vendors = ref([])
const questionnaires = ref([])
const showAssignmentModal = ref(false)
const loading = ref(false)

// Filters
const filters = ref({
  status: '',
  questionnaire: '',
  search: ''
})

// New assignment form
const newAssignment = ref({
  questionnaire_id: '',
  vendor_id: '',
  due_date: '',
  notes: ''
})

// Computed properties
const filteredAssignments = computed(() => {
  if (!Array.isArray(assignments.value)) {
    return []
  }

  let filtered = assignments.value

  if (filters.value.status) {
    filtered = filtered.filter(a => a.status === filters.value.status)
  }

  if (filters.value.questionnaire) {
    filtered = filtered.filter(a => a.questionnaire.toString() === filters.value.questionnaire.toString())
  }

  if (filters.value.search) {
    const search = filters.value.search.toLowerCase()
    filtered = filtered.filter(a => 
      a.vendor_name.toLowerCase().includes(search) ||
      a.questionnaire_name.toLowerCase().includes(search)
    )
  }

  return filtered
})

const canCreateAssignment = computed(() => {
  return newAssignment.value.questionnaire_id && newAssignment.value.vendor_id
})

// Methods
const getStatusCount = (status) => {
  return Array.isArray(assignments.value) ? assignments.value.filter(a => a.status === status).length : 0
}

const formatStatus = (status) => {
  const statusMap = {
    'ASSIGNED': 'Assigned',
    'IN_PROGRESS': 'In Progress', 
    'SUBMITTED': 'Responded',
    'RESPONDED': 'Responded',
    'COMPLETED': 'Completed',
    'OVERDUE': 'Overdue'
  }
  return statusMap[status] || status
}

const formatDate = (dateString) => {
  if (!dateString) return ''
  return new Date(dateString).toLocaleDateString()
}

const getProgressPercentage = (assignment) => {
  // This would need to be calculated based on actual responses
  // For now, return a simple calculation based on status
  switch (assignment.status) {
    case 'ASSIGNED': return 0
    case 'IN_PROGRESS': return 50
    case 'SUBMITTED': return 100
    case 'RESPONDED': return 100
    case 'COMPLETED': return 100
    default: return 0
  }
}

const loadAssignments = async () => {
  try {
    loading.value = true
    const response = await apiCall('/api/v1/vendor-questionnaire/assignments/')
    // Ensure we always set an array, handle both paginated and direct array responses
    assignments.value = Array.isArray(response.data) ? response.data : (response.data.results || [])
  } catch (error) {
    console.error('Error loading assignments:', error)
    assignments.value = [] // Set empty array on error
  } finally {
    loading.value = false
  }
}

const loadVendors = async () => {
  try {
    const response = await apiCall('/api/v1/vendor-questionnaire/assignments/get_vendors/')
    vendors.value = Array.isArray(response.data) ? response.data : []
  } catch (error) {
    console.error('Error loading vendors:', error)
    vendors.value = []
  }
}

const loadQuestionnaires = async () => {
  try {
    const response = await apiCall('/api/v1/vendor-questionnaire/assignments/get_active_questionnaires/')
    questionnaires.value = Array.isArray(response.data) ? response.data : []
  } catch (error) {
    console.error('Error loading questionnaires:', error)
    // Fallback to load all questionnaires if no active ones
    try {
      const fallbackResponse = await apiCall('/api/v1/vendor-questionnaire/questionnaires/')
      const results = fallbackResponse.data.results || []
      questionnaires.value = results.map(q => ({
        questionnaire_id: q.questionnaire_id,
        questionnaire_name: q.questionnaire_name,
        questionnaire_type: q.questionnaire_type,
        description: q.description,
        question_count: q.question_count || 0
      }))
    } catch (fallbackError) {
      console.error('Error loading fallback questionnaires:', fallbackError)
      questionnaires.value = []
    }
  }
}

const refreshData = async () => {
  await Promise.all([
    loadAssignments(),
    loadVendors(),
    loadQuestionnaires()
  ])
}

const createAssignment = async () => {
  try {
    loading.value = true
    // Convert single vendor_id to array for backend compatibility
    const assignmentData = {
      ...newAssignment.value,
      vendor_ids: [newAssignment.value.vendor_id]
    }
    delete assignmentData.vendor_id
    
    const response = await apiCall('/api/v1/vendor-questionnaire/assignments/assign_questionnaire/', {
      method: 'POST',
      data: assignmentData
    })
    
    if (response.data.errors && response.data.errors.length > 0) {
      PopupService.warning('Some assignments could not be created:\n' + response.data.errors.join('\n'), 'Partial Success')
    } else {
      PopupService.success(`Successfully created ${response.data.created_count} assignment(s)`, 'Success')
    }
    
    closeModal()
    await loadAssignments()
  } catch (error) {
    console.error('Error creating assignment:', error)
    PopupService.error('Error creating assignment. Please try again.', 'Assignment Failed')
  } finally {
    loading.value = false
  }
}

const openAssignmentModal = () => {
  console.log('Opening assignment modal...')
  console.log('Questionnaires available:', questionnaires.value)
  console.log('Vendors available:', vendors.value)
  showAssignmentModal.value = true
}

const closeModal = () => {
  showAssignmentModal.value = false
  newAssignment.value = {
    questionnaire_id: '',
    vendor_id: '',
    due_date: '',
    notes: ''
  }
}

const viewAssignment = (assignment) => {
  // Navigate to assignment details or show details modal
  console.log('View assignment:', assignment)
}

const updateStatus = (assignment) => {
  // Show status update modal or inline edit
  console.log('Update status for:', assignment)
}

// Lifecycle
onMounted(async () => {
  await loggingService.logPageView('Vendor', 'Questionnaire Assignment')
  await refreshData()
})
</script>

<style scoped>
/* Main Container */
.questionnaire-assignment {
  min-height: 100vh;
  background: #f8fafc;
  display: flex;
  flex-direction: column;
}

/* Header Section */
.assignment-header {
  background: white;
  border-bottom: 1px solid #e2e8f0;
  padding: 1rem 0;
}

.header-content {
  width: 100% !important;
  padding: 0 1rem;
  display: flex !important;
  justify-content: space-between !important;
  align-items: flex-start;
  position: relative;
}

.header-info {
  flex: 0 0 auto;
  text-align: left;
}

.header-info h1.page-title {
  font-size: 2.5rem;
  font-weight: 700;
  color: #1e293b;
  margin: 0 0 0.5rem 0;
  text-align: left;
}

.page-subtitle {
  color: #64748b;
  font-size: 1rem;
  margin: 0;
  text-align: left;
}

.header-actions {
  display: flex !important;
  justify-content: flex-end !important;
  align-items: center;
  margin-left: auto;
  align-self: flex-start;
  padding-top: 0;
}

/* Buttons */
.btn-primary {
  background: #3b82f6;
  color: white;
  border: none;
  padding: 0.625rem 1.25rem;
  border-radius: 0.5rem;
  font-size: 0.875rem;
  font-weight: 600;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  transition: all 0.2s ease;
  height: 2.5rem;
  min-width: 140px;
}

.btn-primary:hover {
  background: #2563eb;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4);
}

.btn-primary:disabled {
  background: #9ca3af;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
  opacity: 0.6;
}

.btn-secondary {
  background: white;
  color: #374151;
  border: 1px solid #d1d5db;
  padding: 0.625rem 1.25rem;
  border-radius: 0.5rem;
  font-size: 0.875rem;
  font-weight: 600;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  transition: all 0.2s ease;
  height: 2.5rem;
  min-width: 100px;
}

.btn-secondary:hover {
  background: #f9fafb;
  border-color: #9ca3af;
  transform: translateY(-1px);
}

.btn-action {
  background: none;
  border: none;
  padding: 0.5rem;
  border-radius: 0.375rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
}

.btn-view {
  color: #3b82f6;
}

.btn-view:hover {
  background: #eff6ff;
}

.btn-edit {
  color: #059669;
}

.btn-edit:hover {
  background: #ecfdf5;
}

/* Icons */
.icon {
  width: 1rem;
  height: 1rem;
}

/* Content Layout */
.assignment-content {
  flex: 1;
  max-width: 1400px;
  margin: 0 auto;
  padding: 2rem;
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

/* Stats Grid */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1.5rem;
}

.stat-card {
  background: white;
  border-radius: 0.75rem;
  padding: 1.5rem;
  box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06);
}

.stat-header {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 1rem;
}

.stat-icon {
  width: 1.5rem;
  height: 1.5rem;
  color: #3b82f6;
}

.stat-icon.pending {
  color: #f59e0b;
}

.stat-icon.progress {
  color: #8b5cf6;
}

.stat-icon.completed {
  color: #10b981;
}

.stat-label {
  font-size: 0.875rem;
  font-weight: 600;
  color: #374151;
}

.stat-value {
  font-size: 2rem;
  font-weight: 700;
  color: #1e293b;
}

/* Filters */
.filters-row {
  display: flex;
  gap: 1rem;
  margin-bottom: 1.5rem;
  flex-wrap: wrap;
}

.filter-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  flex: 1;
  min-width: 200px;
}

.filter-label {
  font-size: 0.875rem;
  font-weight: 600;
  color: #374151;
}

.filter-select,
.filter-input {
  padding: 0.75rem;
  border: 1px solid #d1d5db;
  border-radius: 0.5rem;
  font-size: 0.875rem;
  background: white;
  transition: border-color 0.15s ease;
}

.filter-select:focus,
.filter-input:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

/* Table */
.assignments-table-section {
  background: white;
  border-radius: 0.75rem;
  box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06);
  overflow: hidden;
}

.table-container {
  overflow-x: auto;
}

.assignments-table {
  width: 100%;
  border-collapse: collapse;
}

.assignments-table th {
  background: #f8fafc;
  padding: 1rem;
  text-align: left;
  font-size: 0.875rem;
  font-weight: 600;
  color: #374151;
  border-bottom: 1px solid #e2e8f0;
}

.assignments-table td {
  padding: 1rem;
  border-bottom: 1px solid #f1f5f9;
  font-size: 0.875rem;
}

.assignment-row:hover {
  background: #f8fafc;
}

.vendor-info,
.questionnaire-info {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.vendor-name {
  font-weight: 600;
  color: #1e293b;
  font-size: 0.8rem;
}

.questionnaire-name {
  font-weight: 600;
  color: #1e293b;
}

/* Status Badge */
.status-badge {
  display: inline-flex;
  align-items: center;
  padding: 0.25rem 0.75rem;
  border-radius: 1rem;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
}

.status-badge.assigned {
  background: #fef3c7;
  color: #92400e;
}

.status-badge.in_progress {
  background: #e0e7ff;
  color: #3730a3;
}

.status-badge.submitted {
  background: #d1fae5;
  color: #065f46;
}

.status-badge.responded {
  background: #d1fae5;
  color: #065f46;
}

.status-badge.completed {
  background: #d1fae5;
  color: #065f46;
}

.status-badge.overdue {
  background: #fee2e2;
  color: #991b1b;
}

/* Progress */
.progress-cell {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.progress-bar {
  flex: 1;
  height: 0.5rem;
  background: #e2e8f0;
  border-radius: 9999px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: #3b82f6;
  transition: width 0.3s ease;
  border-radius: 9999px;
}

.progress-text {
  font-size: 0.75rem;
  font-weight: 600;
  color: #6b7280;
  white-space: nowrap;
}

/* Action Buttons */
.action-buttons {
  display: flex;
  gap: 0.5rem;
}

/* Empty State */
.empty-state {
  text-align: center;
  padding: 3rem;
  color: #6b7280;
}

.empty-icon {
  width: 3rem;
  height: 3rem;
  margin: 0 auto 1rem;
  color: #d1d5db;
}

.empty-state h3 {
  font-size: 1.125rem;
  font-weight: 600;
  color: #374151;
  margin: 0 0 0.5rem 0;
}

.empty-state p {
  margin: 0;
}

/* Modal */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.6);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  animation: fadeIn 0.2s ease;
}

@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

.modal-content {
  background: white;
  border-radius: 1rem;
  width: 90%;
  max-width: 480px;
  max-height: 85vh;
  overflow-y: auto;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
  position: relative;
  animation: slideUp 0.3s ease;
}

@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* Close Button in Top-Right Corner */
.btn-close-corner {
  position: absolute;
  top: 0.875rem;
  right: 0.875rem;
  background: #f3f4f6;
  border: none;
  padding: 0.4rem;
  border-radius: 0.5rem;
  cursor: pointer;
  color: #6b7280;
  transition: all 0.2s ease;
  z-index: 10;
  display: flex;
  align-items: center;
  justify-content: center;
}

.btn-close-corner:hover {
  background: #e5e7eb;
  color: #374151;
  transform: rotate(90deg);
}

.btn-close-corner .icon {
  width: 1.125rem;
  height: 1.125rem;
}

.modal-header {
  padding: 1.25rem 1.25rem 0.75rem 1.25rem;
  border-bottom: none;
}

.modal-header h2 {
  font-size: 1.375rem;
  font-weight: 700;
  color: #1e293b;
  margin: 0;
  padding-right: 2.5rem;
}

.modal-body {
  padding: 0.75rem 1.25rem 1.25rem 1.25rem;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
  padding: 1rem 1.25rem 1.25rem 1.25rem;
  border-top: 1px solid #f1f5f9;
  background: #fafbfc;
  border-radius: 0 0 1rem 1rem;
}

/* Form Elements */
.form-grid {
  display: grid;
  grid-template-columns: minmax(260px, 1.35fr) minmax(220px, 1fr);
  gap: 1.25rem 1.5rem;
  align-items: start;
}

.form-group {
  margin-bottom: 0.875rem;
}

.form-group:last-child {
  margin-bottom: 0;
}

.form-group.span-2 {
  grid-column: span 2;
}

.form-group.compact {
  max-width: 240px;
}

.form-label {
  display: block;
  font-size: 0.8rem;
  font-weight: 600;
  color: #374151;
  margin-bottom: 0.35rem;
  letter-spacing: 0.01em;
}

.form-select,
.form-input,
.form-textarea {
  width: 100%;
  padding: 0.5rem 0.65rem;
  border: 1px solid #d1d5db;
  border-radius: 0.375rem;
  font-size: 0.8125rem;
  background: white;
  transition: all 0.2s ease;
  color: #1e293b;
}

.form-select {
  cursor: pointer;
  background-image: url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 20 20'%3e%3cpath stroke='%236b7280' stroke-linecap='round' stroke-linejoin='round' stroke-width='1.5' d='M6 8l4 4 4-4'/%3e%3c/svg%3e");
  background-position: right 0.5rem center;
  background-repeat: no-repeat;
  background-size: 1.125em 1.125em;
  padding-right: 2rem;
  appearance: none;
  height: 2.25rem;
}

.form-select:hover {
  border-color: #9ca3af;
}

.form-input {
  height: 2.25rem;
}

.form-select:focus,
.form-input:focus,
.form-textarea:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
  background: #fafbfc;
}

.form-textarea {
  resize: vertical;
  min-height: 3.5rem;
  font-family: inherit;
  line-height: 1.5;
}

.form-select option {
  padding: 0.5rem;
  color: #1e293b;
}

.date-input {
  position: relative;
  display: flex;
  align-items: center;
}

.date-input-field {
  padding-right: 2.5rem;
}

.date-input-icon {
  position: absolute;
  right: 0.65rem;
  color: #6b7280;
  width: 1rem;
  height: 1rem;
  pointer-events: none;
}

.date-input-field::-webkit-calendar-picker-indicator {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  cursor: pointer;
  color: transparent;
  background: none;
  opacity: 0;
}

/* Vendor selection is now handled by standard form-select styles */

/* Responsive Design */
@media (max-width: 1024px) {
  .header-content {
    padding: 0 1rem;
  }
  
  .assignment-content {
    padding: 1.5rem 1rem;
  }
  
  .stats-grid {
    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  }

  .form-grid {
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 1rem 1rem;
  }
}

@media (max-width: 768px) {
  .header-content {
    flex-direction: row;
    gap: 1rem;
    align-items: center;
  }
  
  .header-actions {
    justify-content: flex-end;
  }
  
  .filters-row {
    flex-direction: column;
  }
  
  .filter-group {
    min-width: 100%;
  }
  
  .assignments-table th,
  .assignments-table td {
    padding: 0.75rem 0.5rem;
  }
  
  .modal-content {
    width: 95%;
    max-width: 95%;
    margin: 1rem;
  }
  
  .form-grid {
    grid-template-columns: 1fr;
  }

  .form-group.span-2,
  .form-group.compact {
    grid-column: span 1;
    max-width: 100%;
  }
  
  .modal-header h2 {
    font-size: 1.25rem;
  }
  
  .btn-close-corner {
    top: 0.75rem;
    right: 0.75rem;
    padding: 0.4rem;
  }
  
  .btn-close-corner .icon {
    width: 1rem;
    height: 1rem;
  }
  
  .modal-body {
    padding: 0.75rem 1rem 1rem 1rem;
  }
  
  .modal-footer {
    padding: 1rem;
    flex-wrap: wrap;
  }
  
  .btn-primary,
  .btn-secondary {
    min-width: auto;
    flex: 1;
  }
  
  .form-label {
    font-size: 0.8rem;
  }
  
  .form-select,
  .form-input,
  .form-textarea {
    font-size: 0.8125rem;
    padding: 0.5rem 0.75rem;
  }
}
</style>
