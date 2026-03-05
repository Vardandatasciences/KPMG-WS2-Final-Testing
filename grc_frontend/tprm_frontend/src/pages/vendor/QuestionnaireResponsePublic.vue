<template>
  <div class="questionnaire-response-public">
    <div class="public-header">
      <h1 class="page-title">Questionnaire Response</h1>
      <p class="page-subtitle">Complete the questionnaire using the link you received by email. No login required.</p>
    </div>

    <!-- Invalid or missing token -->
    <div v-if="errorMessage" class="error-state">
      <svg class="error-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z"/>
      </svg>
      <h3>Invalid or Expired Link</h3>
      <p>{{ errorMessage }}</p>
    </div>

    <!-- Loading -->
    <div v-else-if="loading" class="loading-state">
      <div class="loading-spinner"></div>
      <p>Loading questionnaire...</p>
    </div>

    <!-- Already submitted -->
    <div v-else-if="assignmentData && assignmentData.is_locked" class="submitted-state">
      <svg class="success-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
      </svg>
      <h3>Already Submitted</h3>
      <p>This questionnaire has already been submitted. Thank you.</p>
    </div>

    <!-- Questionnaire form -->
    <div v-else-if="assignmentData && responses.length > 0" class="response-content">
      <div class="progress-card">
        <div class="progress-header">
          <h3>{{ assignmentData.questionnaire_name }}</h3>
          <span class="progress-badge">{{ completedQuestions }} of {{ totalQuestions }} completed</span>
        </div>
        <div class="progress-bar">
          <div class="progress-fill" :style="{ width: `${completionPercentage}%` }"></div>
        </div>
      </div>

      <div class="questions-container">
        <div v-for="(q, idx) in responses" :key="q.id" class="question-card">
          <div class="question-header">
            <span class="question-number">Question {{ idx + 1 }}</span>
            <span v-if="q.is_required" class="badge badge-required">Required</span>
            <span v-if="q.is_completed" class="badge badge-completed">Completed</span>
          </div>
          <h3 class="question-title">{{ q.question_text }}</h3>

          <div class="question-content">
            <label class="section-label">Your Response</label>

            <textarea
              v-if="q.question_type === 'TEXT'"
              v-model="q.vendor_response"
              class="response-textarea"
              placeholder="Enter your response..."
              rows="4"
            ></textarea>

            <div v-else-if="q.question_type === 'MULTIPLE_CHOICE'" class="radio-group">
              <label v-for="option in getQuestionOptions(q)" :key="option" class="radio-option">
                <input type="radio" :value="option" v-model="q.vendor_response" />
                <span class="radio-label">{{ option }}</span>
              </label>
            </div>

            <div v-else-if="q.question_type === 'CHECKBOX'" class="checkbox-group">
              <label v-for="option in getQuestionOptions(q)" :key="option" class="checkbox-option">
                <input type="checkbox" :value="option" v-model="q.selectedOptions" @change="syncCheckboxResponse(q)" />
                <span class="checkbox-label">{{ option }}</span>
              </label>
            </div>

            <div v-else-if="q.question_type === 'RATING'" class="rating-group">
              <div class="rating-controls">
                <input
                  type="range"
                  :min="getRatingConfig(q).min || 1"
                  :max="getRatingConfig(q).max || 5"
                  :step="getRatingConfig(q).step || 1"
                  v-model="q.vendor_response"
                  class="rating-slider"
                />
                <div class="rating-value">{{ q.vendor_response || (getRatingConfig(q).min || 1) }}</div>
              </div>
              <div class="rating-range">{{ getRatingConfig(q).min || 1 }} to {{ getRatingConfig(q).max || 5 }}</div>
            </div>

            <input
              v-else-if="q.question_type === 'DATE'"
              type="date"
              v-model="q.vendor_response"
              class="date-input"
            />

            <input
              v-else-if="q.question_type === 'NUMBER'"
              type="number"
              v-model="q.vendor_response"
              class="number-input"
              :placeholder="getNumberPlaceholder(q)"
              :min="getNumberConfig(q).min"
              :max="getNumberConfig(q).max"
            />

            <div v-else-if="q.question_type === 'FILE_UPLOAD'" class="upload-area">
              <input
                type="file"
                :id="`file-input-${q.id}`"
                class="file-input-hidden"
                @change="handleFileUpload(q.id, $event)"
                :multiple="getFileConfig(q).maxFiles > 1"
                :accept="getFileConfig(q).allowedTypes"
              />
              <label :for="`file-input-${q.id}`" class="upload-label">
                <svg class="upload-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"/>
                </svg>
                <span>Choose files or drag here</span>
                <span class="upload-hint">Max {{ getFileConfig(q).maxFiles }} file(s), {{ getFileConfig(q).maxSize }}MB each</span>
              </label>
              
              <div v-if="q.uploaded_files && q.uploaded_files.length" class="uploaded-files">
                <div v-for="file in q.uploaded_files" :key="file.s3_file_id || file.name" class="uploaded-file">
                  <svg class="file-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
                  </svg>
                  <span class="file-name">{{ file.original_name || file.name }}</span>
                  <span class="file-size">{{ formatFileSize(file.file_size || file.size) }}</span>
                  <button @click="removeFile(q.id, file.original_name || file.name)" class="remove-file-btn" type="button">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
                    </svg>
                  </button>
                </div>
              </div>
            </div>

            <div v-else>
              <input type="text" v-model="q.vendor_response" class="response-input" placeholder="Your response" />
            </div>

            <div class="comments-section">
              <label class="section-label">Additional Comments (Optional)</label>
              <textarea v-model="q.vendor_comment" class="comments-textarea" placeholder="Add any comments..." rows="2"></textarea>
            </div>
          </div>
        </div>
      </div>

      <div class="submit-section">
        <button @click="saveDraft" class="btn-secondary" :disabled="saving">{{ saving ? 'Saving...' : 'Save progress' }}</button>
        <button @click="submitResponses" class="btn-primary" :disabled="saving">{{ saving ? 'Submitting...' : 'Submit questionnaire' }}</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { apiCall } from '@/utils/api'

const route = useRoute()
const assignmentId = ref('')
const vendorId = ref('')
const questionnaireId = ref('')
const loading = ref(true)
const saving = ref(false)
const errorMessage = ref('')
const assignmentData = ref(null)
const responses = ref([])

const totalQuestions = computed(() => responses.value.length)
const completedQuestions = computed(() => responses.value.filter(r => r.is_completed).length)
const completionPercentage = computed(() =>
  totalQuestions.value ? Math.round((completedQuestions.value / totalQuestions.value) * 100) : 0
)

function getQuestionOptions(q) {
  const opts = q.options
  if (Array.isArray(opts)) return opts
  if (typeof opts === 'string') {
    try {
      const parsed = JSON.parse(opts)
      return Array.isArray(parsed) ? parsed : (parsed.options || [])
    } catch {
      return opts.split(',').map(s => s.trim()).filter(Boolean)
    }
  }
  if (opts && typeof opts === 'object' && opts.options) return opts.options
  return []
}

function getRatingConfig(q) {
  let opts = q.options
  if (typeof opts === 'string') {
    try { opts = JSON.parse(opts) } catch { opts = {} }
  }
  return opts && opts.rating ? opts.rating : { min: 1, max: 5, step: 1 }
}

function getNumberConfig(q) {
  let opts = q.options
  if (typeof opts === 'string') {
    try { opts = JSON.parse(opts) } catch { opts = {} }
  }
  return opts && opts.number ? opts.number : {}
}

function getNumberPlaceholder(q) {
  const c = getNumberConfig(q)
  if (c.min != null && c.max != null) return `Between ${c.min} and ${c.max}`
  return 'Enter a number'
}

function syncCheckboxResponse(q) {
  q.vendor_response = (q.selectedOptions && q.selectedOptions.length)
    ? q.selectedOptions.join(', ') : ''
  recalculateCompletion()
}

function recalculateCompletion() {
  responses.value = responses.value.map(r => {
    const updated = { ...r }
    if (r.question_type === 'CHECKBOX' && !updated.selectedOptions && updated.vendor_response) {
      updated.selectedOptions = updated.vendor_response.split(',').map(s => s.trim()).filter(Boolean)
    }
    switch (r.question_type) {
      case 'TEXT':
      case 'DATE':
      case 'MULTIPLE_CHOICE':
        updated.is_completed = String(r.vendor_response || '').trim() !== ''
        break
      case 'CHECKBOX':
        updated.is_completed = updated.selectedOptions && updated.selectedOptions.length > 0
        break
      case 'RATING':
      case 'NUMBER':
        const v = r.vendor_response
        updated.is_completed = v !== null && v !== undefined && v !== ''
        break
      case 'FILE_UPLOAD':
        updated.is_completed = r.uploaded_files && Array.isArray(r.uploaded_files) && r.uploaded_files.length > 0
        break
      default:
        updated.is_completed = String(r.vendor_response || '').trim() !== ''
    }
    return updated
  })
}

// File upload helper functions
function getFileConfig(question) {
  if (!question.options) return { maxFiles: 1, maxSize: 10, allowedTypes: '' }
  
  if (typeof question.options === 'string') {
    try {
      const opts = JSON.parse(question.options)
      return opts.file || { maxFiles: 1, maxSize: 10, allowedTypes: '' }
    } catch {
      return { maxFiles: 1, maxSize: 10, allowedTypes: '' }
    }
  }
  
  if (question.options && question.options.file) {
    return question.options.file
  }
  
  return { maxFiles: 1, maxSize: 10, allowedTypes: '' }
}

function formatFileSize(bytes) {
  if (!bytes) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i]
}

async function handleFileUpload(questionId, event) {
  const files = Array.from(event.target.files || [])
  if (!files.length) return
  
  const i = responses.value.findIndex(r => r.id === questionId)
  if (i === -1) return
  
  const question = responses.value[i]
  const fileConfig = getFileConfig(question)
  
  // Validate file count
  const existingFileCount = question.uploaded_files ? question.uploaded_files.length : 0
  if (existingFileCount + files.length > (fileConfig.maxFiles || 1)) {
    alert(`Maximum ${fileConfig.maxFiles || 1} file(s) allowed. Currently have ${existingFileCount}, trying to add ${files.length}`)
    event.target.value = ''
    return
  }
  
  // Validate file sizes
  const maxSizeMB = fileConfig.maxSize || 10
  const maxSizeBytes = maxSizeMB * 1024 * 1024
  for (const file of files) {
    if (file.size > maxSizeBytes) {
      alert(`File "${file.name}" exceeds maximum size of ${maxSizeMB}MB`)
      event.target.value = ''
      return
    }
  }
  
  try {
    saving.value = true
    
    console.log('[FILE UPLOAD] Starting upload for question:', questionId)
    console.log('[FILE UPLOAD] Files to upload:', files.map(f => ({ name: f.name, size: f.size, type: f.type })))
    
    // Create FormData for file upload
    const formData = new FormData()
    formData.append('assignment_id', assignmentId.value)
    formData.append('question_id', questionId)
    formData.append('user_id', 'public-vendor')
    
    for (let file of files) {
      formData.append('files', file)
      console.log('[FILE UPLOAD] Appended file to FormData:', file.name)
    }
    
    console.log('[FILE UPLOAD] Sending request to backend...')
    
    // Axios will automatically set the correct Content-Type with boundary for FormData
    const response = await apiCall('/api/v1/vendor-questionnaire/responses/upload_files/', {
      method: 'POST',
      data: formData
    })
    
    console.log('[FILE UPLOAD] Backend response:', response.data)
    
    if (response && response.data && response.data.success !== false) {
      const uploadedFiles = response.data.uploaded_files || []
      console.log('[FILE UPLOAD] Uploaded files from response:', uploadedFiles)
      
      const r = responses.value[i]
      const existingFiles = r.uploaded_files || []
      r.uploaded_files = [...existingFiles, ...uploadedFiles]
      r.vendor_response = r.uploaded_files.map(f => f.original_name || f.name || '').join(', ')
      r.is_completed = r.uploaded_files && Array.isArray(r.uploaded_files) && r.uploaded_files.length > 0
      responses.value[i] = r
      recalculateCompletion()
      alert(`Successfully uploaded ${uploadedFiles.length} file(s)`)
    } else if (response && response.data && response.data.error) {
      console.error('[FILE UPLOAD] Error from backend:', response.data.error)
      alert(`File upload failed: ${response.data.error}`)
    } else {
      console.error('[FILE UPLOAD] Unknown response format:', response)
      alert('File upload failed: Unknown error')
    }
  } catch (error) {
    console.error('[FILE UPLOAD] Exception during upload:', error)
    console.error('[FILE UPLOAD] Error response:', error.response?.data)
    const errorMsg = error.response?.data?.error || error.response?.data?.message || error.message || 'Unknown error'
    alert(`Error uploading files: ${errorMsg}`)
  } finally {
    saving.value = false
    event.target.value = ''
  }
}

async function removeFile(questionId, fileName) {
  if (!confirm(`Remove file "${fileName}"?`)) return
  
  const i = responses.value.findIndex(r => r.id === questionId)
  if (i === -1) return
  
  try {
    saving.value = true
    const r = responses.value[i]
    const fileToRemove = r.uploaded_files.find(f => f.original_name === fileName || f.name === fileName)
    
    if (fileToRemove && fileToRemove.s3_file_id) {
      try {
        const response = await apiCall('/api/v1/vendor-questionnaire/responses/remove_file/', {
          method: 'POST',
          data: {
            assignment_id: assignmentId.value,
            question_id: questionId,
            s3_file_id: fileToRemove.s3_file_id
          }
        })
        
        if (response.data && response.data.success) {
          r.uploaded_files = (r.uploaded_files || []).filter(f => f.original_name !== fileName && f.name !== fileName)
          r.vendor_response = (r.uploaded_files || []).map(f => f.original_name || f.name).join(', ')
          r.is_completed = r.uploaded_files && Array.isArray(r.uploaded_files) && r.uploaded_files.length > 0
          responses.value[i] = r
          recalculateCompletion()
          alert('File removed successfully')
        } else {
          alert('Failed to remove file from storage')
        }
      } catch (error) {
        console.error('Error removing file from S3:', error)
        alert('Error removing file')
      }
    } else {
      r.uploaded_files = (r.uploaded_files || []).filter(f => f.name !== fileName && f.original_name !== fileName)
      r.vendor_response = (r.uploaded_files || []).map(f => f.original_name || f.name).join(', ')
      r.is_completed = r.uploaded_files && Array.isArray(r.uploaded_files) && r.uploaded_files.length > 0
      responses.value[i] = r
      recalculateCompletion()
      alert('File removed')
    }
  } catch (error) {
    console.error('Error in removeFile:', error)
    alert('Error removing file')
  } finally {
    saving.value = false
  }
}

// Removed the watch to prevent infinite loop

// Recalculation is now done explicitly when needed

async function loadByToken() {
  if (!assignmentId.value) {
    errorMessage.value = 'Missing link parameters. Please use the link from your email.'
    loading.value = false
    return
  }
  try {
    loading.value = true
    errorMessage.value = ''
    
    // Use the same API as the authenticated vendor questionnaire response page for better performance
    const res = await apiCall(`/api/v1/vendor-questionnaire/responses/get_assignment_responses/?assignment_id=${assignmentId.value}`)
    
    assignmentData.value = res.data.assignment
    responses.value = (res.data.responses || []).map(r => ({
      ...r,
      selectedOptions: r.question_type === 'CHECKBOX' && r.vendor_response
        ? r.vendor_response.split(',').map(s => s.trim()).filter(Boolean)
        : (r.selectedOptions || [])
    }))
    recalculateCompletion()
  } catch (err) {
    console.error('Error loading questionnaire:', err)
    errorMessage.value = err.response?.data?.error || err.message || 'Failed to load questionnaire. Please try again or contact support.'
  } finally {
    loading.value = false
  }
}

function buildPayload() {
  return responses.value.map(r => ({
    question_id: r.id,
    vendor_response: r.question_type === 'CHECKBOX' ? (r.selectedOptions && r.selectedOptions.length ? r.selectedOptions.join(', ') : '') : (r.vendor_response || ''),
    vendor_comment: r.vendor_comment || ''
  }))
}

async function saveDraft() {
  if (!assignmentId.value) return
  try {
    saving.value = true
    // Use the same API as the authenticated vendor questionnaire response page
    await apiCall('/api/v1/vendor-questionnaire/responses/save_responses/', {
      method: 'POST',
      data: { assignment_id: assignmentId.value, responses: buildPayload() }
    })
    alert('Progress saved. You can return later using the same link.')
  } catch (err) {
    alert(err.response?.data?.error || 'Failed to save. Please try again.')
  } finally {
    saving.value = false
  }
}

async function submitResponses() {
  recalculateCompletion()
  const required = responses.value.filter(r => r.is_required && !r.is_completed).length
  if (required > 0) {
    alert(`Please complete all required questions. ${required} required question(s) remaining.`)
    return
  }
  if (!confirm('Submit your responses? You will not be able to edit after submission.')) return
  try {
    saving.value = true
    // Use the same API as the authenticated vendor questionnaire response page
    await apiCall('/api/v1/vendor-questionnaire/responses/save_responses/', {
      method: 'POST',
      data: { assignment_id: assignmentId.value, responses: buildPayload() }
    })
    await apiCall('/api/v1/vendor-questionnaire/responses/submit_final_responses/', {
      method: 'POST',
      data: { assignment_id: assignmentId.value }
    })
    assignmentData.value = { ...assignmentData.value, is_locked: true }
    alert('Thank you! Your questionnaire has been submitted successfully.')
  } catch (err) {
    alert(err.response?.data?.error || 'Submission failed. Please try again.')
  } finally {
    saving.value = false
  }
}

onMounted(() => {
  assignmentId.value = route.query.assignmentId || ''
  vendorId.value = route.query.vendorId || ''
  questionnaireId.value = route.query.questionnaireId || ''
  loadByToken()
})
</script>

<style scoped>
.questionnaire-response-public {
  max-width: 800px;
  margin: 0 auto;
  padding: 2rem;
  min-height: 100vh;
  background: #f8fafc;
}
.public-header {
  margin-bottom: 2rem;
}
.page-title { font-size: 1.75rem; font-weight: 700; color: #1e293b; margin: 0 0 0.5rem 0; }
.page-subtitle { color: #64748b; margin: 0; }
.error-state, .loading-state, .submitted-state {
  text-align: center;
  padding: 3rem 2rem;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}
.error-icon { width: 64px; height: 64px; color: #dc2626; margin-bottom: 1rem; }
.success-icon { width: 64px; height: 64px; color: #10b981; margin-bottom: 1rem; }
.error-state h3, .submitted-state h3 { margin: 0 0 0.5rem 0; color: #1e293b; }
.loading-spinner {
  width: 48px; height: 48px;
  border: 4px solid #e2e8f0;
  border-top-color: #3b82f6;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin: 0 auto 1rem;
}
@keyframes spin { to { transform: rotate(360deg); } }
.progress-card {
  background: #fff;
  padding: 1.25rem;
  border-radius: 12px;
  margin-bottom: 1.5rem;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}
.progress-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.75rem; }
.progress-header h3 { margin: 0; font-size: 1.125rem; color: #1e293b; }
.progress-badge { font-size: 0.875rem; color: #64748b; font-weight: 500; }
.progress-bar { height: 8px; background: #e2e8f0; border-radius: 4px; overflow: hidden; }
.progress-fill { height: 100%; background: #3b82f6; border-radius: 4px; transition: width 0.3s ease; }
.questions-container { display: flex; flex-direction: column; gap: 1.5rem; }
.question-card {
  background: #fff;
  padding: 1.5rem;
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}
.question-header { display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.5rem; }
.question-number { font-size: 0.875rem; font-weight: 600; color: #64748b; }
.badge { font-size: 0.75rem; padding: 0.2rem 0.5rem; border-radius: 6px; font-weight: 500; }
.badge-required { background: #fef3c7; color: #92400e; }
.badge-completed { background: #d1fae5; color: #065f46; }
.question-title { margin: 0 0 1rem 0; font-size: 1rem; color: #1e293b; line-height: 1.5; }
.question-content { margin-top: 0.5rem; }
.section-label { display: block; font-size: 0.875rem; font-weight: 600; color: #374151; margin-bottom: 0.5rem; }
.response-textarea, .comments-textarea {
  width: 100%; padding: 0.75rem; border: 1px solid #e2e8f0; border-radius: 8px;
  font-size: 0.875rem; resize: vertical;
}
.radio-group, .checkbox-group { display: flex; flex-direction: column; gap: 0.5rem; }
.radio-option, .checkbox-option { display: flex; align-items: center; gap: 0.5rem; cursor: pointer; }
.rating-controls { display: flex; align-items: center; gap: 1rem; margin-bottom: 0.5rem; }
.rating-slider { flex: 1; }
.rating-value { font-weight: 600; color: #1e293b; min-width: 2rem; }
.rating-range { font-size: 0.75rem; color: #64748b; }
.date-input, .number-input, .response-input {
  width: 100%; padding: 0.75rem; border: 1px solid #e2e8f0; border-radius: 8px; font-size: 0.875rem;
}
.comments-section { margin-top: 1rem; }
.file-upload-note { padding: 0.75rem; background: #f0f9ff; border-radius: 8px; font-size: 0.875rem; color: #0369a1; }

/* File upload styles */
.upload-area {
  margin-top: 0.5rem;
}
.file-input-hidden {
  position: absolute;
  opacity: 0;
  width: 0;
  height: 0;
}
.upload-label {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 2rem 1rem;
  border: 2px dashed #cbd5e1;
  border-radius: 8px;
  background: #f8fafc;
  cursor: pointer;
  transition: all 0.2s;
}
.upload-label:hover {
  border-color: #3b82f6;
  background: #f0f9ff;
}
.upload-icon {
  width: 48px;
  height: 48px;
  color: #64748b;
  margin-bottom: 0.5rem;
}
.upload-label span {
  font-size: 0.875rem;
  color: #475569;
}
.upload-hint {
  font-size: 0.75rem !important;
  color: #94a3b8 !important;
  margin-top: 0.25rem;
}
.uploaded-files {
  margin-top: 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}
.uploaded-file {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
}
.file-icon {
  width: 24px;
  height: 24px;
  color: #3b82f6;
  flex-shrink: 0;
}
.file-name {
  flex: 1;
  font-size: 0.875rem;
  color: #1e293b;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.file-size {
  font-size: 0.75rem;
  color: #64748b;
  flex-shrink: 0;
}
.remove-file-btn {
  padding: 0.25rem;
  background: transparent;
  border: none;
  cursor: pointer;
  color: #dc2626;
  transition: color 0.2s;
  flex-shrink: 0;
}
.remove-file-btn:hover {
  color: #b91c1c;
}
.remove-file-btn svg {
  width: 18px;
  height: 18px;
}

.submit-section { margin-top: 2rem; display: flex; gap: 1rem; flex-wrap: wrap; }
.btn-primary, .btn-secondary {
  padding: 0.75rem 1.5rem; border-radius: 8px; font-weight: 600; font-size: 0.875rem; cursor: pointer;
  border: none; transition: background 0.2s;
}
.btn-primary { background: #3b82f6; color: #fff; }
.btn-primary:hover:not(:disabled) { background: #2563eb; }
.btn-secondary { background: #e2e8f0; color: #374151; }
.btn-secondary:hover:not(:disabled) { background: #cbd5e1; }
.btn-primary:disabled, .btn-secondary:disabled { opacity: 0.6; cursor: not-allowed; }
</style>
