<template>
  <div class="questionnaire-review">
    <!-- Header -->
    <div class="review-header">
      <div class="header-content">
        <div class="header-info">
          <h1 class="page-title">Questionnaire Responses</h1>
          <p class="page-subtitle">
            View the answers submitted by the vendor for this assignment.
          </p>
        </div>
        <div class="header-actions">
          <button
            v-if="assignmentId"
            class="btn-primary"
            type="button"
            @click="sendForApproval"
          >
            Send for Approval
          </button>
          <button class="btn-secondary" type="button" @click="goBack">
            Back to Assignments
          </button>
        </div>
      </div>
      <div v-if="assignment" class="assignment-summary">
        <div class="summary-item">
          <span class="summary-label">Vendor</span>
          <span class="summary-value">{{ assignment.vendor_name || 'N/A' }}</span>
        </div>
        <div class="summary-item">
          <span class="summary-label">Questionnaire</span>
          <span class="summary-value">{{ assignment.questionnaire_name || 'N/A' }}</span>
        </div>
        <div class="summary-item">
          <span class="summary-label">Status</span>
          <span class="summary-value">
            {{ formatStatus(assignment.status) }}
          </span>
        </div>
        <div class="summary-item">
          <span class="summary-label">Assigned</span>
          <span class="summary-value">{{ formatDate(assignment.assigned_date) }}</span>
        </div>
        <div class="summary-item">
          <span class="summary-label">Due Date</span>
          <span class="summary-value">
            {{ formatDate(assignment.due_date) || 'No due date' }}
          </span>
        </div>
      </div>
    </div>

    <!-- Loading / Error -->
    <div class="review-content">
      <div v-if="loading" class="state-card">
        Loading questionnaire responses...
      </div>

      <div v-else-if="error" class="state-card state-error">
        {{ error }}
      </div>

      <div v-else-if="!assignmentId">
        <div class="state-card state-error">
          No assignment selected. Please open this page from Questionnaire Assignment.
        </div>
      </div>

      <!-- Questions and responses -->
      <div v-else-if="responses.length" class="questions-container">
        <div
          v-for="(q, idx) in responses"
          :key="q.id || q.question_id || idx"
          class="question-card"
        >
          <div class="question-header">
            <div class="question-meta">
              <span class="question-number">Question {{ idx + 1 }}</span>
              <div class="question-badges">
                <span v-if="q.is_required" class="badge badge-required">Required</span>
                <span v-if="q.is_completed" class="badge badge-completed">Completed</span>
              </div>
            </div>
            <h3 class="question-title">{{ q.question_text }}</h3>
          </div>

          <div class="question-body">
            <div class="field-block">
              <label class="field-label">Vendor Response</label>
              <div class="field-value">
                <template v-if="q.question_type === 'FILE_UPLOAD'">
                  <div v-if="q.uploaded_files && q.uploaded_files.length" class="files-list">
                    <div
                      v-for="file in q.uploaded_files"
                      :key="file.s3_file_id || file.name"
                      class="file-item"
                    >
                      <span class="file-name">{{ file.original_name || file.name }}</span>
                      <span class="file-size">
                        {{ formatFileSize(file.file_size || file.size) }}
                      </span>
                      <a
                        v-if="file.s3_url"
                        :href="file.s3_url"
                        target="_blank"
                        class="file-link"
                      >
                        Download
                      </a>
                    </div>
                  </div>
                  <div v-else class="field-empty">No files uploaded.</div>
                </template>

                <template v-else>
                  <div v-if="displayResponse(q) !== ''">
                    {{ displayResponse(q) }}
                  </div>
                  <div v-else class="field-empty">No response provided.</div>
                </template>
              </div>
            </div>

            <div class="field-block">
              <label class="field-label">Vendor Comment</label>
              <div class="field-value">
                <div v-if="q.vendor_comment && q.vendor_comment.trim() !== ''">
                  {{ q.vendor_comment }}
                </div>
                <div v-else class="field-empty">No additional comments.</div>
              </div>
            </div>

            <div class="field-block" v-if="q.reviewer_comment">
              <label class="field-label">Reviewer Feedback</label>
              <div class="field-value reviewer-feedback">
                {{ q.reviewer_comment }}
              </div>
            </div>
          </div>
        </div>
      </div>

      <div v-else class="state-card">
        No responses found for this assignment.
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { apiCall } from '@/utils/api'

const route = useRoute()
const router = useRouter()

const assignmentId = ref(route.query.assignment_id || route.query.assignmentId || '')
const assignment = ref(null)
const responses = ref([])
const loading = ref(false)
const error = ref('')

const loadAssignmentResponses = async () => {
  if (!assignmentId.value) {
    error.value = 'No assignment selected.'
    return
  }

  try {
    loading.value = true
    error.value = ''

    const res = await apiCall(
      `/api/v1/vendor-questionnaire/responses/get_assignment_responses/?assignment_id=${assignmentId.value}`
    )

    assignment.value = res.data.assignment
    responses.value = res.data.responses || []
  } catch (e) {
    console.error('Error loading assignment responses (review page):', e)
    const msg =
      e.response?.data?.message ||
      e.response?.data?.error ||
      e.message ||
      'Failed to load responses.'
    error.value = msg
  } finally {
    loading.value = false
  }
}

const goBack = () => {
  router
    .push({ path: '/vendor-questionnaire-assignment' })
    .catch(() => {})
}

const sendForApproval = () => {
  if (!assignmentId.value) return

  const query = {
    workflow_type: 'MULTI_PERSON',
    approval_type: 'response_approval',
    assignment_id: assignmentId.value,
    auto_populate: 'true'
  }

  if (assignment.value?.vendor_id) {
    query.vendor_id = assignment.value.vendor_id
  }
  if (assignment.value?.questionnaire_id) {
    query.questionnaire_id = assignment.value.questionnaire_id
  }

  router.push({
    name: 'Vendor Approval Workflow Creator',
    query
  }).catch((err) => {
    if (err && err.name !== 'NavigationDuplicated') {
      console.error('Error navigating to workflow creator:', err)
    }
  })
}

const formatStatus = (status) => {
  const map = {
    ASSIGNED: 'Assigned',
    IN_PROGRESS: 'In Progress',
    SUBMITTED: 'Responded',
    RESPONDED: 'Responded',
    COMPLETED: 'Completed',
    OVERDUE: 'Overdue'
  }
  return map[status] || status || 'N/A'
}

const formatDate = (value) => {
  if (!value) return ''
  const d = new Date(value)
  if (isNaN(d.getTime())) return ''
  return d.toLocaleDateString()
}

const displayResponse = (q) => {
  if (!q) return ''

  // Checkbox responses may be stored as CSV or selectedOptions
  if (q.question_type === 'CHECKBOX') {
    if (Array.isArray(q.selectedOptions) && q.selectedOptions.length) {
      return q.selectedOptions.join(', ')
    }
    if (q.vendor_response) {
      return String(q.vendor_response)
    }
    return ''
  }

  return q.vendor_response != null ? String(q.vendor_response) : ''
}

const formatFileSize = (bytes) => {
  if (!bytes || isNaN(bytes)) return ''
  const sizes = ['B', 'KB', 'MB', 'GB']
  let i = 0
  let value = bytes
  while (value >= 1024 && i < sizes.length - 1) {
    value /= 1024
    i++
  }
  return `${value.toFixed(1)} ${sizes[i]}`
}

onMounted(() => {
  loadAssignmentResponses()
})
</script>

<style scoped>
.questionnaire-review {
  min-height: 100vh;
  background: #f8fafc;
  display: flex;
  flex-direction: column;
}

.review-header {
  background: #ffffff;
  border-bottom: 1px solid #e2e8f0;
  padding: 1rem 0;
}

.header-content {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 1.5rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.header-info {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.page-title {
  font-size: 1.75rem;
  font-weight: 700;
  color: #1e293b;
  margin: 0;
}

.page-subtitle {
  margin: 0;
  color: #64748b;
  font-size: 0.95rem;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.btn-secondary {
  border-radius: 0.5rem;
  border: 1px solid #cbd5f5;
  background: #ffffff;
  color: #1d4ed8;
  font-size: 0.875rem;
  font-weight: 500;
  padding: 0.5rem 1rem;
  cursor: pointer;
}

.btn-secondary:hover {
  background: #eff6ff;
}

.btn-primary {
  border-radius: 0.5rem;
  border: 1px solid #2563eb;
  background: #2563eb;
  color: #ffffff;
  font-size: 0.875rem;
  font-weight: 600;
  padding: 0.5rem 1rem;
  cursor: pointer;
}

.btn-primary:hover {
  background: #1d4ed8;
  border-color: #1d4ed8;
}

.assignment-summary {
  max-width: 1200px;
  margin: 0.5rem auto 0;
  padding: 0 1.5rem 1rem;
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 0.75rem;
}

.summary-item {
  display: flex;
  flex-direction: column;
  gap: 0.15rem;
}

.summary-label {
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: #94a3b8;
}

.summary-value {
  font-size: 0.95rem;
  font-weight: 500;
  color: #0f172a;
}

.review-content {
  flex: 1;
  max-width: 1200px;
  margin: 0 auto;
  padding: 1.5rem;
}

.state-card {
  background: #ffffff;
  border-radius: 0.75rem;
  padding: 1.5rem;
  text-align: center;
  color: #4b5563;
  box-shadow: 0 1px 3px rgba(15, 23, 42, 0.08);
}

.state-card.state-error {
  border: 1px solid #fecaca;
  color: #991b1b;
  background: #fef2f2;
}

.questions-container {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.question-card {
  background: #ffffff;
  border-radius: 0.75rem;
  box-shadow: 0 1px 3px rgba(15, 23, 42, 0.08);
  padding: 1.25rem 1.5rem;
}

.question-header {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
  margin-bottom: 0.75rem;
}

.question-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.question-number {
  font-size: 0.8rem;
  font-weight: 600;
  color: #6b7280;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.question-badges {
  display: flex;
  gap: 0.4rem;
}

.badge {
  padding: 0.1rem 0.5rem;
  border-radius: 999px;
  font-size: 0.7rem;
  font-weight: 600;
}

.badge-required {
  background: #fee2e2;
  color: #b91c1c;
}

.badge-completed {
  background: #dcfce7;
  color: #166534;
}

.question-title {
  font-size: 1rem;
  font-weight: 600;
  color: #111827;
  margin: 0;
}

.question-body {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.field-block {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.field-label {
  font-size: 0.8rem;
  font-weight: 600;
  color: #6b7280;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.field-value {
  font-size: 0.9rem;
  color: #111827;
  line-height: 1.5;
  white-space: pre-wrap;
}

.field-empty {
  font-size: 0.85rem;
  color: #9ca3af;
  font-style: italic;
}

.reviewer-feedback {
  background: #f0f9ff;
  border-radius: 0.5rem;
  padding: 0.6rem 0.75rem;
  border: 1px solid #bae6fd;
}

.files-list {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
}

.file-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.85rem;
}

.file-name {
  font-weight: 500;
  color: #1f2933;
}

.file-size {
  color: #9ca3af;
}

.file-link {
  color: #2563eb;
  text-decoration: underline;
  font-weight: 500;
}
</style>

