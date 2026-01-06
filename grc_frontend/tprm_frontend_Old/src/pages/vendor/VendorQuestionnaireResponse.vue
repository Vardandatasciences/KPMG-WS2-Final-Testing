<template>
  <div class="questionnaire-response">
    <!-- Header -->
    <div class="response-header">
      <div class="header-content">
        <div class="header-info">
          <h1 class="page-title">Vendor Questionnaire</h1>
        </div>
      </div>
    </div>
   
    <!-- Main Content -->
    <div class="response-content">
      <!-- Assigned Questionnaires Section -->
      <div v-if="vendorAssignments.length > 0" class="questionnaires-section">
        <div class="questionnaires-info">
          <svg class="questionnaires-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"/>
          </svg>
          <h3 class="questionnaires-title">Assigned Questionnaires</h3>
        </div>
        
        <div class="questionnaires-grid">
          <div 
            v-for="assignment in vendorAssignments" 
            :key="assignment.assignment_id" 
            class="questionnaire-card"
            @click="selectQuestionnaire(assignment)"
            :class="{ 'selected': selectedAssignmentId === assignment.assignment_id }"
          >
            <div class="questionnaire-card-header">
              <div class="questionnaire-title">{{ assignment.questionnaire_name }}</div>
              <span :class="['questionnaire-status', assignment.status.toLowerCase()]">
                {{ formatAssignmentStatus(assignment.status) }}
              </span>
            </div>
            <div class="questionnaire-meta">
              <div class="meta-item">
                <svg class="meta-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"/>
                </svg>
                <span>Assigned: {{ formatDate(assignment.assigned_date) }}</span>
              </div>
              <div v-if="assignment.due_date" class="meta-item">
                <svg class="meta-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3"/>
                </svg>
                <span>Due: {{ formatDate(assignment.due_date) }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Progress Section -->
      <div v-if="assignmentData" class="progress-card">
        <div class="progress-header">
          <div class="progress-info">
            <svg class="progress-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 17v-2a4 4 0 014-4h6"/>
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7H7a2 2 0 00-2 2v9m14 0V9a2 2 0 00-2-2h-2"/>
            </svg>
            <h3 class="progress-title">Completion Progress</h3>
          </div>
          <span class="progress-badge">{{ completedQuestions }} of {{ totalQuestions }} completed</span>
        </div>
        
        <div class="progress-bar">
          <div class="progress-fill" :style="{ width: `${completionPercentage}%` }"></div>
        </div>
        
        <div class="progress-meta">
          <div class="meta-item">
            <svg class="meta-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3M12 6a9 9 0 110 12 9 9 0 010-12z"/>
            </svg>
            <span>Last submitted: {{ lastSavedTime || 'Not submitted yet' }}</span>
          </div>
          <div class="meta-item">
            <svg class="meta-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m2-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
            </svg>
            <span>{{ requiredRemaining }} required questions remaining</span>
          </div>
        </div>
      </div>

      <!-- Questions Section -->
      <div v-if="responses.length > 0" class="questions-container">
        <div v-for="(q, idx) in responses" :key="q.id" class="question-card">
          <!-- Question Header -->
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

          <!-- Question Content -->
          <div class="question-content">
            <!-- Response Section -->
            <div class="response-section">
              <label class="section-label">Your Response</label>

              <!-- TEXT Response -->
            <textarea
              v-if="q.question_type === 'TEXT'"
              v-model="q.vendor_response"
                class="response-textarea"
              placeholder="Enter your response..."
                rows="4"
                :disabled="isLocked"
            ></textarea>

              <!-- MULTIPLE_CHOICE Response -->
              <div v-else-if="q.question_type === 'MULTIPLE_CHOICE'" class="radio-group">
                <label v-for="option in getQuestionOptions(q)" :key="option" class="radio-option">
                  <input 
                    type="radio" 
                    :value="option" 
                    v-model="q.vendor_response" 
                    @change="updateResponse(q.id, 'vendor_response', option)"
                    :disabled="isLocked" 
                  />
                  <span class="radio-label">{{ option }}</span>
                </label>
              </div>

              <!-- CHECKBOX Response -->
              <div v-else-if="q.question_type === 'CHECKBOX'" class="checkbox-group">
                <label v-for="option in getQuestionOptions(q)" :key="option" class="checkbox-option">
                  <input 
                    type="checkbox" 
                    :value="option"
                    v-model="q.selectedOptions"
                    @change="updateCheckboxResponse(q.id, option, $event.target.checked)"
                    :disabled="isLocked"
                  />
                  <span class="checkbox-label">{{ option }}</span>
                </label>
              </div>

              <!-- RATING Response -->
              <div v-else-if="q.question_type === 'RATING'" class="rating-group">
                <div class="rating-controls">
                  <input 
                    type="range" 
                    :min="getRatingConfig(q).min || 1" 
                    :max="getRatingConfig(q).max || 5" 
                    :step="getRatingConfig(q).step || 1"
                    v-model="q.vendor_response"
                    @input="updateResponse(q.id, 'vendor_response', $event.target.value)"
                    class="rating-slider"
                    :disabled="isLocked"
                  />
                  <div class="rating-value">{{ q.vendor_response || (getRatingConfig(q).min || 1) }}</div>
                </div>
                <div v-if="getRatingConfig(q).labels" class="rating-labels">
                  {{ getRatingConfig(q).labels }}
                </div>
                <div class="rating-range">
                  {{ getRatingConfig(q).min || 1 }} to {{ getRatingConfig(q).max || 5 }}
                </div>
              </div>

              <!-- DATE Response -->
              <input
                v-else-if="q.question_type === 'DATE'"
                type="date"
                v-model="q.vendor_response"
                class="date-input"
                :disabled="isLocked"
              />

              <!-- NUMBER Response -->
              <div v-else-if="q.question_type === 'NUMBER'" class="number-group">
                <input
                  type="number"
                  v-model="q.vendor_response"
                  @input="updateResponse(q.id, 'vendor_response', $event.target.value)"
                  class="number-input"
                  :placeholder="getNumberPlaceholder(q)"
                  :min="getNumberConfig(q).min || undefined"
                  :max="getNumberConfig(q).max || undefined"
                  :step="getNumberConfig(q).step || 'any'"
                  :disabled="isLocked"
                />
                <div v-if="getNumberConfig(q).unit" class="number-unit">{{ getNumberConfig(q).unit }}</div>
                <div v-if="getNumberConfig(q).min || getNumberConfig(q).max" class="number-range">
                  Range: {{ getNumberConfig(q).min || 'No minimum' }} to {{ getNumberConfig(q).max || 'No maximum' }}
                </div>
              </div>

              <!-- FILE_UPLOAD Response -->
              <div v-else-if="q.question_type === 'FILE_UPLOAD'" class="upload-area" :class="{ 'disabled': isLocked }">
                <input 
                  type="file" 
                  :id="`file-input-${q.id}`"
                  class="file-input-hidden"
                  @change="handleFileUpload(q.id, $event)"
                  :multiple="(getFileConfig(q).maxFiles || 1) > 1"
                  :accept="getFileConfig(q).allowedTypes"
                  :disabled="isLocked"
                />
                <svg class="upload-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"/>
                </svg>
                <p class="upload-text">{{ isLocked ? 'Files uploaded' : 'Click to upload or drag and drop' }}</p>
                <p class="upload-info">
                  Max {{ getFileConfig(q).maxFiles || 1 }} file(s), {{ getFileConfig(q).maxSize || 10 }}MB each
                </p>
                <p class="upload-types">Allowed: {{ getFileConfig(q).allowedTypes || 'All files' }}</p>
                <button type="button" class="btn-upload" @click="triggerFileUpload(q.id)" :disabled="isLocked">{{ isLocked ? 'View Files' : 'Choose File' }}</button>
                <div v-if="q.uploaded_files && q.uploaded_files.length" class="uploaded-files">
                  <div v-for="file in q.uploaded_files" :key="file.s3_file_id || file.name" class="uploaded-file">
                    <svg class="file-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
                    </svg>
                    <span class="file-name">{{ file.original_name || file.name }}</span>
                    <span class="file-size">{{ formatFileSize(file.file_size || file.size) }}</span>
                    <a v-if="file.s3_url" :href="file.s3_url" target="_blank" class="file-download" title="Download file">
                      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
                      </svg>
                    </a>
                    <button type="button" class="file-remove" @click="removeFile(q.id, file.original_name || file.name)" v-if="!isLocked">
                      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
                      </svg>
                    </button>
                  </div>
                </div>
              </div>
          </div>

          <!-- Additional Comments -->
            <div class="comments-section">
              <label class="section-label">Additional Comments (Optional)</label>
              <textarea 
                v-model="q.vendor_comment" 
                class="comments-textarea"
                placeholder="Add any additional context or clarification..."
                rows="3"
                :disabled="isLocked"
              ></textarea>
          </div>

            <!-- Reviewer Feedback -->
            <div v-if="q.reviewer_comment" class="feedback-section">
              <label class="section-label feedback-label">Reviewer Feedback</label>
              <div class="feedback-content">{{ q.reviewer_comment }}</div>
          </div>
        </div>
      </div>
    </div>

      <!-- Submit Section -->
      <div v-if="responses.length > 0" class="submit-section">
        <div class="submit-content">
          <h3 class="submit-title">Ready to Submit?</h3>
          <p class="submit-description">
          Please review all your responses before submitting. You can save your progress and return later if needed.
        </p>
          <div class="submit-actions">
            <button @click="submitResponses" class="btn-primary" :disabled="saving || isLocked" v-if="!isLocked">
              <svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
              </svg>
              {{ saving ? 'Submitting...' : 'Submit Response' }}
            </button>
            <div v-if="isLocked" class="submitted-message">
              <svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
              </svg>
              <span>Questionnaire responded successfully</span>
              <div v-if="assignmentData && assignmentData.submission_date" class="submission-time">
                Responded on {{ formatDate(assignmentData.submission_date) }}
              </div>
            </div>
        </div>
        </div>
      </div>
      
      <!-- Debug Section (remove in production) -->
      <div v-if="responses.length > 0" class="debug-section" style="background: #f0f9ff; border: 1px solid #0ea5e9; border-radius: 0.5rem; padding: 1rem; margin: 1rem 0; font-size: 0.875rem;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
          <h4 style="margin: 0; color: #0c4a6e;">Debug Info:</h4>
          <button @click="recalculateAllCompletion" style="background: #0ea5e9; color: white; border: none; padding: 0.25rem 0.5rem; border-radius: 0.25rem; font-size: 0.75rem; cursor: pointer;">
            Recalculate
          </button>
        </div>
        <p style="margin: 0.25rem 0;"><strong>Total Questions:</strong> {{ debugInfo.total }}</p>
        <p style="margin: 0.25rem 0;"><strong>Required Questions:</strong> {{ debugInfo.required }}</p>
        <p style="margin: 0.25rem 0;"><strong>Completed Required:</strong> {{ debugInfo.completed }}</p>
        <p style="margin: 0.25rem 0;"><strong>Required Remaining:</strong> {{ debugInfo.requiredRemaining }}</p>
        
        <!-- File Upload Debug Info -->
        <div v-if="responses.some(r => r.question_type === 'FILE_UPLOAD')" style="margin-top: 1rem; padding-top: 1rem; border-top: 1px solid #0ea5e9;">
          <p style="margin: 0.25rem 0;"><strong>File Upload Questions:</strong></p>
          <div v-for="q in responses.filter(r => r.question_type === 'FILE_UPLOAD')" :key="q.id" style="margin: 0.5rem 0; padding: 0.5rem; background: white; border-radius: 0.25rem;">
            <p style="margin: 0.25rem 0;"><strong>Question:</strong> {{ q.question_text.substring(0, 50) }}...</p>
            <p style="margin: 0.25rem 0;"><strong>Uploaded Files Count:</strong> {{ q.uploaded_files ? q.uploaded_files.length : 0 }}</p>
            <p style="margin: 0.25rem 0;"><strong>Vendor Response:</strong> "{{ q.vendor_response }}"</p>
            <p style="margin: 0.25rem 0;"><strong>Is Completed:</strong> {{ q.is_completed }}</p>
            <div v-if="q.uploaded_files && q.uploaded_files.length > 0">
              <p style="margin: 0.25rem 0;"><strong>Files:</strong></p>
              <ul style="margin: 0; padding-left: 1rem; font-size: 0.75rem;">
                <li v-for="file in q.uploaded_files" :key="file.s3_file_id || file.name" style="margin: 0.25rem 0;">
                  {{ file.original_name || file.name }} ({{ file.file_size || file.size }} bytes) - S3 ID: {{ file.s3_file_id }}
                </li>
              </ul>
            </div>
          </div>
        </div>
        
        <div v-if="debugInfo.incompleteDetails.length > 0">
          <p style="margin: 0.5rem 0 0.25rem 0;"><strong>Incomplete Questions:</strong></p>
          <ul style="margin: 0; padding-left: 1rem;">
            <li v-for="item in debugInfo.incompleteDetails" :key="item.id" style="margin: 0.25rem 0;">
              <strong>{{ item.question_type }}:</strong> {{ item.question_text }}<br>
              <span style="color: #6b7280;">Response: "{{ item.vendor_response }}" | Completed: {{ item.is_completed }}</span>
            </li>
          </ul>
        </div>
      </div>


      
      <!-- No Assignments State -->
      <div v-if="vendorAssignments.length === 0" class="empty-state">
        <svg class="empty-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"/>
        </svg>
        <h3 v-if="!currentVendorId">Vendor Account Not Available</h3>
        <h3 v-else>No Questionnaires Assigned</h3>
        <p v-if="!currentVendorId">
          Your user account is not associated with a vendor record. 
          <br />
          Please complete your vendor registration first to access questionnaires.
        </p>
        <p v-else>
          You don't have any questionnaires assigned to you at this time. 
          <br />
          Questionnaires will appear here once they are assigned to your vendor account.
        </p>
        <div v-if="!currentVendorId" class="empty-state-actions">
          <router-link to="/vendor-registration" class="btn-primary">
            <svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
            </svg>
            Go to Vendor Registration
          </router-link>
        </div>
      </div>
    </div>
  </div>

  <!-- Popup Modal -->
  <PopupModal />
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useStore } from 'vuex'
import { apiCall } from '@/utils/api'
import PopupModal from '@/popup/PopupModal.vue'
import { PopupService } from '@/popup/popupService'
import { useNotifications } from '@/composables/useNotifications'
import notificationService from '@/services/notificationService'
import loggingService from '@/services/loggingService'
import permissionsService from '@/services/permissionsService'
import { getTprmApiUrl } from '@/utils/backendEnv'

const { showSuccess, showError, showWarning, showInfo } = useNotifications()

// API base URL for vendor-questionnaire endpoints
const VENDOR_QUESTIONNAIRE_API_BASE_URL = getTprmApiUrl('vendor-questionnaire')

// Reactive data
const vendorAssignments = ref([])
const responses = ref([])
const assignmentData = ref(null)
const selectedAssignmentId = ref('')
const saving = ref(false)
const lastSavedTime = ref('')
const isLocked = ref(false)
const currentVendorId = ref(null)

// Computed properties
const completedQuestions = computed(() => responses.value.filter(r => r.is_completed).length)
const totalQuestions = computed(() => responses.value.length)
const completionPercentage = computed(() => {
  if (totalQuestions.value === 0) return 0
  return Math.round((completedQuestions.value / totalQuestions.value) * 100)
})
const requiredRemaining = computed(() => responses.value.filter(r => r.is_required && !r.is_completed).length)

// Debug computed property to help troubleshoot completion issues
const debugInfo = computed(() => {
  const requiredQuestions = responses.value.filter(r => r.is_required)
  const completedRequired = requiredQuestions.filter(r => r.is_completed)
  const incompleteRequired = requiredQuestions.filter(r => !r.is_completed)
  
  return {
    total: responses.value.length,
    required: requiredQuestions.length,
    completed: completedRequired.length,
    incomplete: incompleteRequired.length,
    requiredRemaining: requiredRemaining.value,
    incompleteDetails: incompleteRequired.map(r => ({
      id: r.id,
      question_text: r.question_text.substring(0, 50) + '...',
      question_type: r.question_type,
      vendor_response: r.vendor_response,
      is_completed: r.is_completed
    }))
  }
})

// Helper function to get vendor ID for a specific user
const getVendorIdForUser = async (userId) => {
  try {
    console.log('🔍 Getting vendor ID for user:', userId)
    
    // Try the get_user_data endpoint first
    try {
      const response = await apiCall(`${getTprmApiUrl('vendor-core')}/temp-vendors/get_user_data/?user_id=${userId}`)
      console.log('Temp vendor API response:', response)
      console.log('Response data structure:', {
        hasData: !!response.data,
        dataKeys: response.data ? Object.keys(response.data) : [],
        hasNestedData: response.data && response.data.data,
        nestedDataKeys: response.data && response.data.data ? Object.keys(response.data.data) : []
      })
      
      // Try multiple response format patterns
      let tempVendorData = null
      
      // Pattern 1: response.data.data.temp_vendor (most common DRF format)
      if (response.data && response.data.data && response.data.data.temp_vendor) {
        tempVendorData = response.data.data.temp_vendor
        console.log('✅ Found vendor via pattern 1 (response.data.data.temp_vendor)')
      }
      // Pattern 2: response.data.temp_vendor
      else if (response.data && response.data.temp_vendor) {
        tempVendorData = response.data.temp_vendor
        console.log('✅ Found vendor via pattern 2 (response.data.temp_vendor)')
      }
      // Pattern 3: response.temp_vendor
      else if (response.temp_vendor) {
        tempVendorData = response.temp_vendor
        console.log('✅ Found vendor via pattern 3 (response.temp_vendor)')
      }
      // Pattern 4: response.data is the temp_vendor object itself
      else if (response.data && response.data.id && (response.data.userid == userId || response.data.user_id == userId)) {
        tempVendorData = response.data
        console.log('✅ Found vendor via pattern 4 (response.data is vendor object)')
      }
      // Pattern 5: Check if response.data.data exists and has id (nested structure)
      else if (response.data && response.data.data && response.data.data.id) {
        tempVendorData = response.data.data
        console.log('✅ Found vendor via pattern 5 (response.data.data)')
      }
      
      if (tempVendorData) {
        console.log('✅ Found vendor ID:', tempVendorData.id)
        console.log('Temp vendor data:', tempVendorData)
        
        // Validate that the vendor actually exists and has the correct userid
        // Check both userid and user_id fields
        const vendorUserId = tempVendorData.userid || tempVendorData.user_id
        if (vendorUserId && (vendorUserId == userId || vendorUserId == parseInt(userId))) {
          currentVendorId.value = tempVendorData.id
          console.log('✅ Vendor validation passed - userid matches:', vendorUserId)
          return currentVendorId.value
        } else {
          console.log('⚠️ Vendor found but userid mismatch:', {
            expected: userId,
            actual: vendorUserId,
            vendorId: tempVendorData.id
          })
          // Still use it if it's the only vendor for this user (might be a data issue)
          if (tempVendorData.id) {
            console.log('⚠️ Using vendor ID anyway (assuming data consistency issue):', tempVendorData.id)
            currentVendorId.value = tempVendorData.id
            return currentVendorId.value
          }
        }
      }
    } catch (apiError) {
      console.log('get_user_data endpoint failed:', apiError.message)
      console.log('Error details:', apiError.response?.data || apiError.message)
      
      // If it's a 404, that's okay - just means no vendor record yet
      if (apiError.response?.status === 404) {
        console.log('⚠️ 404 response - no vendor record found for this user')
      }
    }
    
    // Try alternative: search temp_vendors by userid
    try {
      console.log('🔍 Trying alternative lookup: search temp_vendors by userid...')
      const searchResponse = await apiCall(`${getTprmApiUrl('vendor-core')}/temp-vendors/?userid=${userId}`)
      console.log('Search response:', searchResponse)
      
      if (searchResponse.data && Array.isArray(searchResponse.data) && searchResponse.data.length > 0) {
        const vendor = searchResponse.data[0]
        if (vendor.id) {
          currentVendorId.value = vendor.id
          console.log('✅ Found vendor ID via search:', vendor.id)
          return currentVendorId.value
        }
      } else if (searchResponse.data && searchResponse.data.results && searchResponse.data.results.length > 0) {
        const vendor = searchResponse.data.results[0]
        if (vendor.id) {
          currentVendorId.value = vendor.id
          console.log('✅ Found vendor ID via search (paginated):', vendor.id)
          return currentVendorId.value
        }
      }
    } catch (searchError) {
      console.log('Alternative search failed:', searchError.message)
    }
    
    // No vendor found or validation failed
    console.log('❌ No valid vendor found for user:', userId)
    console.log('This user does not have a corresponding vendor record in the temp_vendor table.')
    console.log('💡 Suggestion: Complete vendor registration first to create a vendor record.')
    return null
  } catch (error) {
    console.error('Error getting vendor ID:', error)
    console.error('Error details:', {
      message: error.message,
      response: error.response,
      data: error.response?.data
    })
    return null
  }
}

// Methods
const getCurrentVendorId = async () => {
  try {
    // Get current user from auth store or session
    const currentUserFromStorage = localStorage.getItem('current_user')
    
    console.log('=== USER ID RESOLUTION DEBUG ===')
    
    // First, try to get user from Vuex store (same as HomePage.vue)
    try {
      const store = useStore()
      const vuexUser = store.getters['auth/currentUser']
      console.log('Vuex store user:', vuexUser)
      console.log('Vuex store user ID:', vuexUser?.id)
      
      // If Vuex store has user data, use that (this is the most reliable source)
      if (vuexUser && vuexUser.id) {
        console.log('✅ Using Vuex store user ID:', vuexUser.id)
        console.log('Vuex user details:', {
          id: vuexUser.id,
          username: vuexUser.username,
          email: vuexUser.email,
          first_name: vuexUser.first_name,
          last_name: vuexUser.last_name
        })
        return await getVendorIdForUser(vuexUser.id)
      }
    } catch (vuexError) {
      console.log('Could not access Vuex store:', vuexError.message)
    }
    
    // Fallback to localStorage if Vuex store is not available
    console.log('Vuex store not available, trying localStorage...')
    console.log('localStorage.getItem("current_user"):', currentUserFromStorage)
    
    const currentUser = JSON.parse(currentUserFromStorage || '{}')
    const userId = currentUser.id || currentUser.userid
    
    console.log('Parsed currentUser object:', currentUser)
    console.log('Available userId from localStorage:', userId)
    
    if (!userId) {
      console.log('❌ No user ID found in localStorage or Vuex store')
      console.log('This user is not properly logged in or user data is missing.')
      return null
    }
    
    console.log('Using localStorage userId:', userId)
    return await getVendorIdForUser(userId)
  } catch (error) {
    console.error('Error getting vendor ID:', error)
    console.error('Error details:', {
      message: error.message,
      response: error.response,
      data: error.response?.data
    })
    return null
  }
}

const loadVendorAssignments = async () => {
  if (!currentVendorId.value) {
    console.log('❌ No currentVendorId available - user does not have a vendor record')
    vendorAssignments.value = []
    return
  }
  
  try {
    console.log('=== VENDOR ASSIGNMENTS DEBUG ===')
    console.log('Loading vendor assignments for vendor ID:', currentVendorId.value)
    console.log('API URL:', `${VENDOR_QUESTIONNAIRE_API_BASE_URL}/responses/get_vendor_assignments/?vendor_id=${currentVendorId.value}`)
    
    const response = await apiCall(`${VENDOR_QUESTIONNAIRE_API_BASE_URL}/responses/get_vendor_assignments/?vendor_id=${currentVendorId.value}`)
    console.log('Vendor assignments API response:', response)
    console.log('Response data:', response.data)
    console.log('Response status:', response.status)
    
    // Handle different response formats
    if (Array.isArray(response.data)) {
      vendorAssignments.value = response.data
    } else if (Array.isArray(response)) {
      vendorAssignments.value = response
    } else if (response.data && Array.isArray(response.data)) {
      vendorAssignments.value = response.data
    } else {
      console.warn('Unexpected response format:', response)
      vendorAssignments.value = []
    }
    
    console.log('Set vendorAssignments.value to:', vendorAssignments.value)
    console.log('Number of assignments found:', vendorAssignments.value ? vendorAssignments.value.length : 0)
    
    // If no assignments found, try to get all assignments to debug
    if (!vendorAssignments.value || vendorAssignments.value.length === 0) {
      console.log('=== NO ASSIGNMENTS FOUND - DEBUGGING ===')
      console.log('No assignments found, trying to get all assignments for debugging...')
      try {
        const allAssignmentsResponse = await apiCall(`${VENDOR_QUESTIONNAIRE_API_BASE_URL}/assignments/`)
        console.log('All assignments in database:', allAssignmentsResponse)
        console.log('All assignments data:', allAssignmentsResponse.data)
        
        if (allAssignmentsResponse.data && Array.isArray(allAssignmentsResponse.data)) {
          console.log('Total assignments in database:', allAssignmentsResponse.data.length)
          console.log('Assignment details:', allAssignmentsResponse.data.map(a => ({
            assignment_id: a.assignment_id,
            temp_vendor_id: a.temp_vendor_id,
            questionnaire_name: a.questionnaire?.questionnaire_name,
            status: a.status
          })))
          
          // Check if any assignments match our vendor ID
          const matchingAssignments = allAssignmentsResponse.data.filter(a => 
            a.temp_vendor_id == currentVendorId.value || a.temp_vendor == currentVendorId.value
          )
          console.log('Assignments matching our vendor ID:', matchingAssignments.length)
          console.log('Matching assignments:', matchingAssignments)
        }
      } catch (debugError) {
        console.log('❌ Could not fetch all assignments:', debugError)
      }
      console.log('=== END NO ASSIGNMENTS DEBUG ===')
    }
    
    // Clear selected assignment when vendor changes
    selectedAssignmentId.value = ''
    responses.value = []
    assignmentData.value = null
    isLocked.value = false
    console.log('=== END VENDOR ASSIGNMENTS DEBUG ===')
  } catch (error) {
    console.error('❌ Error loading vendor assignments:', error)
    console.error('Error details:', {
      message: error.message,
      response: error.response,
      data: error.response?.data,
      status: error.response?.status
    })
    
    // Show user-friendly error message
    if (error.response?.status === 404) {
      console.log('⚠️ No assignments found for this vendor (404)')
      vendorAssignments.value = []
    } else if (error.response?.status === 400) {
      console.error('⚠️ Bad request - vendor_id might be invalid')
      showError('Invalid Request', error.response?.data?.error || 'Invalid vendor ID provided')
    } else {
      showError('Error Loading Assignments', error.response?.data?.error || error.message || 'Failed to load vendor assignments. Please try again.')
    }
    
    vendorAssignments.value = []
  }
}

const selectQuestionnaire = (assignment) => {
  selectedAssignmentId.value = assignment.assignment_id
  loadAssignmentQuestions()
}

const formatDate = (dateString) => {
  if (!dateString) return ''
  return new Date(dateString).toLocaleDateString()
}

const loadAssignmentQuestions = async () => {
  if (!selectedAssignmentId.value) {
    responses.value = []
    assignmentData.value = null
    return
  }
  
  try {
    const response = await apiCall(`${VENDOR_QUESTIONNAIRE_API_BASE_URL}/responses/get_assignment_responses/?assignment_id=${selectedAssignmentId.value}`)
    assignmentData.value = response.data.assignment
    responses.value = response.data.responses
    isLocked.value = response.data.assignment.is_locked || false
    
    // Debug logging for uploaded files
    console.log('Loaded assignment responses:', response.data.responses)
    const fileUploadQuestions = response.data.responses.filter(r => r.question_type === 'FILE_UPLOAD')
    console.log('File upload questions:', fileUploadQuestions)
    fileUploadQuestions.forEach(q => {
      console.log(`Question ${q.id}: uploaded_files =`, q.uploaded_files)
    })
    
    // Recalculate completion status for all questions
    recalculateCompletionStatus()
  } catch (error) {
    console.error('Error loading assignment questions:', error)
  }
}

const formatAssignmentStatus = (status) => {
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

const recalculateCompletionStatus = () => {
  responses.value = responses.value.map(r => {
    const updated = { ...r }
    
    // Initialize selectedOptions for checkbox questions if not exists
    if (r.question_type === 'CHECKBOX' && !updated.selectedOptions) {
      // Try to parse from vendor_response
      if (updated.vendor_response) {
        updated.selectedOptions = updated.vendor_response.split(',').map(opt => opt.trim()).filter(opt => opt)
      } else {
        updated.selectedOptions = []
      }
    }
    
    // Update completion status based on question type and current values
    switch (r.question_type) {
      case 'TEXT':
      case 'NUMBER':
      case 'DATE':
        updated.is_completed = String(r.vendor_response || '').trim() !== ''
        break
      case 'MULTIPLE_CHOICE':
        updated.is_completed = String(r.vendor_response || '').trim() !== ''
        break
      case 'CHECKBOX':
        updated.is_completed = updated.selectedOptions && updated.selectedOptions.length > 0
        break
      case 'RATING':
        updated.is_completed = parseInt(r.vendor_response || 0) > 0
        break
      case 'FILE_UPLOAD':
        updated.is_completed = r.uploaded_files && r.uploaded_files.length > 0
        break
      default:
        updated.is_completed = String(r.vendor_response || '').trim() !== ''
    }
    
    return updated
  })
}

const updateResponse = (id, field, value) => {
  const i = responses.value.findIndex(r => r.id === id)
  if (i !== -1) {
    const r = { ...responses.value[i], [field]: value }
    
    // Update completion status based on question type and current values
    switch (r.question_type) {
      case 'TEXT':
      case 'NUMBER':
      case 'DATE':
        r.is_completed = String(r.vendor_response || '').trim() !== ''
        break
      case 'MULTIPLE_CHOICE':
        r.is_completed = String(r.vendor_response || '').trim() !== ''
        break
      case 'CHECKBOX':
        // For checkbox, check if any options are selected
        r.is_completed = r.selectedOptions && r.selectedOptions.length > 0
        r.vendor_response = r.selectedOptions ? r.selectedOptions.join(', ') : ''
        break
      case 'RATING':
        r.is_completed = parseInt(r.vendor_response || 0) > 0
        break
      case 'FILE_UPLOAD':
        r.is_completed = r.uploaded_files && r.uploaded_files.length > 0
        break
      default:
        r.is_completed = String(r.vendor_response || '').trim() !== ''
    }
    
    responses.value[i] = r
  }
}

// Handle checkbox responses
const updateCheckboxResponse = (id, option, checked) => {
  const i = responses.value.findIndex(r => r.id === id)
  if (i !== -1) {
    const r = { ...responses.value[i] }
    
    // Initialize selectedOptions if it doesn't exist
    if (!r.selectedOptions) {
      r.selectedOptions = []
    }
    
    if (checked) {
      // Add option if not already selected
      if (!r.selectedOptions.includes(option)) {
        r.selectedOptions.push(option)
      }
    } else {
      // Remove option if selected
      r.selectedOptions = r.selectedOptions.filter(opt => opt !== option)
    }
    
    // Update vendor_response with comma-separated list
    r.vendor_response = r.selectedOptions.join(', ')
    r.is_completed = r.selectedOptions.length > 0
    
    responses.value[i] = r
  }
}

const getQuestionOptions = (question) => {
  if (!question.options) return []
  
  // Handle different option formats
  if (Array.isArray(question.options)) {
    return question.options
  }
  
  // If options is a JSON string, parse it
  if (typeof question.options === 'string') {
    try {
      const parsed = JSON.parse(question.options)
      if (parsed.choices && Array.isArray(parsed.choices)) {
        return parsed.choices
      }
      return Array.isArray(parsed) ? parsed : []
    } catch (e) {
      // If parsing fails, split by newlines or commas
      return question.options.split(/[,\n]/).map(opt => opt.trim()).filter(opt => opt)
    }
  }
  
  // If options is an object with choices property
  if (question.options.choices && Array.isArray(question.options.choices)) {
    return question.options.choices
  }
  
  return []
}

// Get rating configuration
const getRatingConfig = (question) => {
  if (!question.options) return { min: 1, max: 5, step: 1, labels: '' }
  
  if (typeof question.options === 'string') {
    try {
      const parsed = JSON.parse(question.options)
      return parsed.rating || { min: 1, max: 5, step: 1, labels: '' }
    } catch (e) {
      return { min: 1, max: 5, step: 1, labels: '' }
    }
  }
  
  return question.options.rating || { min: 1, max: 5, step: 1, labels: '' }
}

// Get file upload configuration
const getFileConfig = (question) => {
  if (!question.options) return { maxFiles: 1, maxSize: 10, allowedTypes: '' }
  
  if (typeof question.options === 'string') {
    try {
      const parsed = JSON.parse(question.options)
      return parsed.file || { maxFiles: 1, maxSize: 10, allowedTypes: '' }
    } catch (e) {
      return { maxFiles: 1, maxSize: 10, allowedTypes: '' }
    }
  }
  
  return question.options.file || { maxFiles: 1, maxSize: 10, allowedTypes: '' }
}

// Get number input configuration
const getNumberConfig = (question) => {
  if (!question.options) return { min: null, max: null, step: null, unit: '' }
  
  if (typeof question.options === 'string') {
    try {
      const parsed = JSON.parse(question.options)
      return parsed.number || { min: null, max: null, step: null, unit: '' }
    } catch (e) {
      return { min: null, max: null, step: null, unit: '' }
    }
  }
  
  return question.options.number || { min: null, max: null, step: null, unit: '' }
}

// Get number input placeholder
const getNumberPlaceholder = (question) => {
  const config = getNumberConfig(question)
  let placeholder = 'Enter a number'
  
  if (config.min !== null && config.max !== null) {
    placeholder += ` (${config.min} - ${config.max})`
  } else if (config.min !== null) {
    placeholder += ` (min: ${config.min})`
  } else if (config.max !== null) {
    placeholder += ` (max: ${config.max})`
  }
  
  if (config.unit) {
    placeholder += ` in ${config.unit}`
  }
  
  return placeholder + '...'
}

// Format file size
const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 Bytes'
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

const triggerFileUpload = (questionId) => {
  const fileInput = document.getElementById(`file-input-${questionId}`)
  if (fileInput) {
    fileInput.click()
  }
}

const handleFileUpload = async (questionId, event) => {
  const files = event.target.files
  if (!files || files.length === 0) return
  
  const i = responses.value.findIndex(r => r.id === questionId)
  if (i === -1) return
  
  const question = responses.value[i]
  const fileConfig = getFileConfig(question)
  
  // Validate file count
  const existingFileCount = question.uploaded_files ? question.uploaded_files.length : 0
  if (existingFileCount + files.length > (fileConfig.maxFiles || 1)) {
    PopupService.warning(`Maximum ${fileConfig.maxFiles || 1} file(s) allowed. Currently have ${existingFileCount}, trying to add ${files.length}`, 'Too Many Files')
    event.target.value = ''
    return
  }
  
  // Validate file sizes and types
  const maxSizeMB = fileConfig.maxSize || 10
  const allowedTypes = fileConfig.allowedTypes || ''
  
  for (let file of files) {
    // Check file size
    const maxSizeBytes = maxSizeMB * 1024 * 1024
    if (file.size > maxSizeBytes) {
      PopupService.warning(`File ${file.name} exceeds maximum size of ${maxSizeMB}MB`, 'File Too Large')
      event.target.value = ''
      return
    }
    
    // Check file type
    if (allowedTypes) {
      const fileExtension = file.name.split('.').pop().toLowerCase()
      const allowedExtensions = allowedTypes.split(',').map(ext => ext.trim().toLowerCase())
      if (!allowedExtensions.includes(fileExtension)) {
        PopupService.warning(`File type .${fileExtension} not allowed. Allowed types: ${allowedTypes}`, 'Invalid File Type')
        event.target.value = ''
        return
      }
    }
  }
  
  try {
    console.log('Starting S3 file upload process...')
    console.log('Assignment ID:', selectedAssignmentId.value)
    console.log('Question ID:', questionId)
    console.log('Files to upload:', files.length)
    
    // Create FormData for file upload
    const formData = new FormData()
    formData.append('assignment_id', selectedAssignmentId.value)
    formData.append('question_id', questionId)
    formData.append('user_id', 'vendor-user') // You might want to get this from auth
    
    // Add files to FormData
    for (let file of files) {
      console.log('Adding file to FormData:', file.name, file.size, file.type)
      formData.append('files', file)
    }
    
    console.log('Sending request to S3 backend...')
    
    // Upload files to S3 via backend
    const response = await apiCall(`${VENDOR_QUESTIONNAIRE_API_BASE_URL}/responses/upload_files/`, {
      method: 'POST',
      data: formData
      // Note: Don't set Content-Type header for FormData - browser sets it automatically with boundary
    })
    
    console.log('S3 backend response:', response)
    
    if (response && response.success !== false) {
      // Update the response with uploaded file information
      const r = { ...responses.value[i] }
      
      // Safely handle uploaded_files from S3 response
      const uploadedFiles = response.uploaded_files || []
      
      // Merge with existing files
      const existingFiles = r.uploaded_files || []
      r.uploaded_files = [...existingFiles, ...uploadedFiles]
      
      // Update vendor_response with file names
      r.vendor_response = r.uploaded_files.map(f => f.original_name || f.name || '').join(', ')
      r.is_completed = r.uploaded_files.length > 0
      
      responses.value[i] = r
      
      console.log('Files uploaded successfully to S3:', uploadedFiles)
      console.log('Storage method used:', response.storage_method || 'S3')
      
      // Show success message
      PopupService.success(`Files uploaded successfully using ${response.storage_method || 'S3'}!`, 'Upload Successful')
    } else {
      console.error('S3 file upload failed:', response.error)
      PopupService.error(`File upload failed: ${response.error}`, 'Upload Failed')
    }
  } catch (error) {
    console.error('Error uploading files to S3:', error)
    console.error('Error details:', {
      message: error.message,
      stack: error.stack,
      response: error.response,
      status: error.response?.status,
      data: error.response?.data
    })
    
    let errorMessage = 'Error uploading files to S3. Please try again.'
    if (error.response?.data?.error) {
      errorMessage = `S3 Upload error: ${error.response.data.error}`
    } else if (error.message) {
      errorMessage = `S3 Upload error: ${error.message}`
    }
    
    PopupService.error(errorMessage, 'Upload Error')
  }
  
  // Clear the input so the same file can be selected again if needed
  event.target.value = ''
}

const removeFile = async (questionId, fileName) => {
  const i = responses.value.findIndex(r => r.id === questionId)
  if (i !== -1) {
    const r = { ...responses.value[i] }
    
    if (r.uploaded_files) {
      // Find the file to remove and get its S3 file ID
      const fileToRemove = r.uploaded_files.find(f => f.original_name === fileName || f.name === fileName)
      
      if (fileToRemove && fileToRemove.s3_file_id) {
        try {
          // Call backend to remove file from S3
          const response = await apiCall(`${VENDOR_QUESTIONNAIRE_API_BASE_URL}/responses/remove_file/`, {
            method: 'DELETE',
            data: {
              assignment_id: selectedAssignmentId.value,
              question_id: questionId,
              s3_file_id: fileToRemove.s3_file_id,
              user_id: 'vendor-user'
            }
          })
          
          if (response.success !== false) {
            // Update local state
            r.uploaded_files = (r.uploaded_files || []).filter(f => f.original_name !== fileName && f.name !== fileName)
            r.vendor_response = (r.uploaded_files || []).map(f => f.original_name || f.name).join(', ')
            r.is_completed = (r.uploaded_files || []).length > 0
            
            responses.value[i] = r
            
            console.log('File removed successfully from S3')
          } else {
            console.error('S3 file removal failed:', response.error)
            PopupService.error(`Failed to remove file: ${response.error}`, 'Removal Failed')
          }
        } catch (error) {
          console.error('Error removing file from S3:', error)
          PopupService.error('Error removing file from S3. Please try again.', 'Removal Error')
        }
      } else {
        // Fallback: remove from local state only (for files without S3 file ID)
        r.uploaded_files = (r.uploaded_files || []).filter(f => f.name !== fileName && f.original_name !== fileName)
        r.vendor_response = (r.uploaded_files || []).map(f => f.original_name || f.name).join(', ')
        r.is_completed = (r.uploaded_files || []).length > 0
        
        responses.value[i] = r
      }
    }
  }
}

const saveResponses = async (showMessage = true) => {
  if (!selectedAssignmentId.value || responses.value.length === 0) return
  
  try {
    saving.value = true
    
    const responseData = responses.value.map(r => ({
      question_id: r.id,
      vendor_response: r.vendor_response,
      vendor_comment: r.vendor_comment
    }))
    
    await apiCall(`${VENDOR_QUESTIONNAIRE_API_BASE_URL}/responses/save_responses/`, {
      method: 'POST',
      data: {
        assignment_id: selectedAssignmentId.value,
        responses: responseData
      }
    })
    
    lastSavedTime.value = new Date().toLocaleTimeString()
    
    if (showMessage) {
      PopupService.success('Response submitted successfully!', 'Submitted')
      // Create notification
      await notificationService.createVendorQuestionnaireNotification('questionnaire_submitted', {
        questionnaire_id: assignmentData.value?.questionnaire_id,
        questionnaire_title: assignmentData.value?.questionnaire_title || 'Questionnaire',
        vendor_id: currentVendorId.value
      })
    }
  } catch (error) {
    console.error('Error saving responses:', error)
    
    // Check for connection errors
    const isConnectionError = error.code === 'ERR_NETWORK' || 
                              error.message?.includes('ERR_CONNECTION_REFUSED') ||
                              error.message?.includes('Network Error') ||
                              !error.response
    
    let errorMessage = 'Error submitting response. Please try again.'
    if (isConnectionError) {
      errorMessage = 'Cannot connect to the server. Please check if the backend server is running and try again.'
      console.error('Connection error - backend server may not be running')
    } else if (error.response?.data?.error) {
      errorMessage = error.response.data.error
    } else if (error.response?.data?.message) {
      errorMessage = error.response.data.message
    } else if (error.message) {
      errorMessage = error.message
    }
    
    if (showMessage) {
      PopupService.error(errorMessage, 'Submission Failed')
      // Create error notification
      await notificationService.createVendorErrorNotification('save_questionnaire_responses', errorMessage, {
        title: 'Failed to Submit Response',
        questionnaire_id: assignmentData.value?.questionnaire_id
      })
    }
  } finally {
    saving.value = false
  }
}

const submitResponses = async () => {
  if (requiredRemaining.value > 0) {
    PopupService.warning('Please complete all required questions before submitting.', 'Missing Required Fields')
    // Create warning notification
    await notificationService.createVendorWarningNotification('incomplete_questionnaire', {
      title: 'Missing Required Fields',
      message: 'Please complete all required questions before submitting.',
      required_remaining: requiredRemaining.value
    })
    return
  }
  
  PopupService.confirm(
    'Are you sure you want to submit your responses? This action cannot be undone and you will not be able to edit your responses after submission.',
    'Submit Responses',
    async () => {
      await performSubmit()
    }
  )
}

const performSubmit = async () => {
  
  try {
    saving.value = true
    
    // First save all responses
    await saveResponses(false)
    
    // Then submit final responses to lock the assignment
    const response = await apiCall(`${VENDOR_QUESTIONNAIRE_API_BASE_URL}/responses/submit_final_responses/`, {
      method: 'POST',
      data: {
        assignment_id: selectedAssignmentId.value
      }
    })
    
    console.log('Submit response:', response)
    
    // Check if the response is successful
    if (response.status === 200 || response.data) {
      PopupService.success('Questionnaire responded successfully! Your responses have been locked.', 'Submitted Successfully')
      
      // Create notification
      await notificationService.createVendorQuestionnaireNotification('questionnaire_submitted', {
        questionnaire_id: assignmentData.value?.questionnaire_id,
        questionnaire_title: assignmentData.value?.questionnaire_title || 'Questionnaire',
        vendor_id: currentVendorId.value
      })
      
      // Reload the assignment to reflect new status
      await loadAssignmentQuestions()
    } else {
      console.error('Unexpected response format:', response)
      PopupService.error('Error responding to questionnaire. Please try again.', 'Submission Failed')
    }
  } catch (error) {
    console.error('Error submitting responses:', error)
    console.error('Error details:', {
      message: error.message,
      code: error.code,
      response: error.response,
      data: error.response?.data
    })
    
    // Check for connection errors
    const isConnectionError = error.code === 'ERR_NETWORK' || 
                              error.code === 'ERR_CONNECTION_REFUSED' ||
                              error.message?.includes('ERR_CONNECTION_REFUSED') ||
                              error.message?.includes('Network Error') ||
                              (!error.response && error.message)
    
    // Check if it's actually a success but axios is treating it as an error
    if (error.response && (error.response.status === 200 || error.response.status === 201)) {
      PopupService.success('Questionnaire responded successfully! Your responses have been locked.', 'Submitted Successfully')
      
      // Create notification
      await notificationService.createVendorQuestionnaireNotification('questionnaire_submitted', {
        questionnaire_id: assignmentData.value?.questionnaire_id,
        questionnaire_title: assignmentData.value?.questionnaire_title || 'Questionnaire',
        vendor_id: currentVendorId.value
      })
      
      await loadAssignmentQuestions()
    } else if (isConnectionError) {
      const errorMsg = 'Cannot connect to the server. Please check your network connection and try again.'
      console.error('Connection error - backend server may not be running')
      PopupService.error(errorMsg, 'Connection Error')
      
      // Create error notification
      await notificationService.createVendorErrorNotification('submit_questionnaire_connection_error', errorMsg, {
        title: 'Connection Error',
        questionnaire_id: assignmentData.value?.questionnaire_id
      })
    } else {
      const errorMsg = error.response?.data?.error || 
                      error.response?.data?.message || 
                      error.message || 
                      'Error responding to questionnaire. Please try again.'
      PopupService.error(errorMsg, 'Submission Error')
      
      // Create error notification
      await notificationService.createVendorErrorNotification('submit_questionnaire_responses', errorMsg, {
        title: 'Submission Error',
        questionnaire_id: assignmentData.value?.questionnaire_id
      })
    }
  } finally {
    saving.value = false
  }
}

// Manual completion recalculation (for debugging)
const recalculateAllCompletion = () => {
  recalculateCompletionStatus()
  console.log('Completion status recalculated:', debugInfo.value)
}

// Lifecycle
onMounted(async () => {
  await loggingService.logPageView('Vendor', 'Vendor Questionnaire Response')
  
  // RBAC: require submit_questionnaire_responses permission
  try {
    const hasSubmitPermission = await permissionsService.checkVendorPermission('submit_questionnaire_responses')
    if (!hasSubmitPermission) {
      sessionStorage.setItem('access_denied_error', JSON.stringify({
        message: 'You do not have permission to submit questionnaire responses.',
        code: '403',
        path: window.location.pathname,
        permission: 'submit_questionnaire_responses',
        permissionRequired: 'submit_questionnaire_responses'
      }))
      window.location.href = '/access-denied'
      return
    }
  } catch (e) {
    sessionStorage.setItem('access_denied_error', JSON.stringify({
      message: 'You do not have permission to submit questionnaire responses.',
      code: '403',
      path: window.location.pathname,
      permission: 'submit_questionnaire_responses',
      permissionRequired: 'submit_questionnaire_responses'
    }))
    window.location.href = '/access-denied'
    return
  }
  
  // Get current vendor ID and load assignments
  const vendorId = await getCurrentVendorId()
  if (vendorId) {
    await loadVendorAssignments()
  }
})
</script>

<style scoped>
/* VendorQuestionnaireResponse.css - Clean, Professional Design */

/* Main Container */
.questionnaire-response {
  min-height: 100vh;
  background: #f8fafc;
  display: flex;
  flex-direction: column;
}

/* Header Section */
.response-header {
  background: white;
  border-bottom: 1px solid #e2e8f0;
  padding: 2rem 0;
}


.header-content {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 2rem;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 0.5rem;
}

.header-info h1.page-title {
  font-size: 2rem;
  font-weight: 700;
  color: #1e293b;
  margin: 0 0 0.5rem 0;
}

.page-subtitle {
  color: #64748b;
  font-size: 1rem;
  margin: 0;
}

/* Buttons */
.btn-primary {
  background: #3b82f6;
  color: white;
  border: none;
  padding: 0.75rem 1.5rem;
  border-radius: 0.5rem;
  font-size: 0.875rem;
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  transition: all 0.2s ease;
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
}

.btn-secondary {
  background: white;
  color: #374151;
  border: 1px solid #d1d5db;
  padding: 0.75rem 1.5rem;
  border-radius: 0.5rem;
  font-size: 0.875rem;
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  transition: all 0.2s ease;
}

.btn-secondary:hover {
  background: #f9fafb;
  border-color: #9ca3af;
}

.btn-upload {
  background: #3b82f6;
  color: white;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 0.375rem;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  margin-top: 0.5rem;
}

/* Icons */
.icon {
  width: 1rem;
  height: 1rem;
}

.progress-icon,
.meta-icon {
  width: 1.25rem;
  height: 1.25rem;
}

.upload-icon {
  width: 2rem;
  height: 2rem;
  margin: 0 auto 0.5rem;
  color: #9ca3af;
}

/* Content Layout */
.response-content {
  flex: 1;
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem;
  display: flex;
  flex-direction: column;
  gap: 2rem;
}


/* Questionnaires Section */
.questionnaires-section {
  background: white;
  border-radius: 0.75rem;
  padding: 1.5rem;
  box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06);
}

.questionnaires-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
}

.questionnaires-info {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.questionnaires-icon {
  width: 1.25rem;
  height: 1.25rem;
  color: #3b82f6;
}

.questionnaires-title {
  font-size: 1.125rem;
  font-weight: 600;
  color: #1e293b;
  margin: 0;
}

.questionnaires-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 1rem;
}

.questionnaire-card {
  border: 2px solid #e2e8f0;
  border-radius: 0.75rem;
  padding: 1.25rem;
  cursor: pointer;
  transition: all 0.2s ease;
  background: white;
}

.questionnaire-card:hover {
  border-color: #3b82f6;
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.15);
  transform: translateY(-1px);
}

.questionnaire-card.selected {
  border-color: #3b82f6;
  background: #eff6ff;
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.25);
}

.questionnaire-card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 1rem;
}

.questionnaire-title {
  font-size: 1rem;
  font-weight: 600;
  color: #1e293b;
  line-height: 1.4;
}

.questionnaire-status {
  display: inline-flex;
  align-items: center;
  padding: 0.25rem 0.75rem;
  border-radius: 1rem;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  white-space: nowrap;
}

.questionnaire-status.assigned {
  background: #fef3c7;
  color: #92400e;
}

.questionnaire-status.in_progress {
  background: #e0e7ff;
  color: #3730a3;
}

.questionnaire-status.submitted {
  background: #d1fae5;
  color: #065f46;
}

.questionnaire-status.responded {
  background: #dbeafe;
  color: #1e40af;
}

.questionnaire-status.completed {
  background: #d1fae5;
  color: #065f46;
}

.questionnaire-status.overdue {
  background: #fee2e2;
  color: #991b1b;
}

.questionnaire-meta {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: #6b7280;
  font-size: 0.875rem;
}

.meta-icon {
  width: 1rem;
  height: 1rem;
  color: #9ca3af;
}

/* Empty State */
.empty-state {
  text-align: center;
  padding: 3rem;
  color: #6b7280;
  background: white;
  border-radius: 0.75rem;
  box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06);
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

.empty-state-actions {
  margin-top: 1.5rem;
  display: flex;
  justify-content: center;
  gap: 1rem;
}

.empty-state-actions .btn-primary {
  text-decoration: none;
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
}

/* Progress Card */
.progress-card {
  background: white;
  border-radius: 0.75rem;
  padding: 1.5rem;
  box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06);
}

.progress-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.progress-info {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.progress-icon {
  color: #3b82f6;
}

.progress-title {
  font-size: 1.125rem;
  font-weight: 600;
  color: #1e293b;
  margin: 0;
}

.progress-badge {
  background: #eff6ff;
  color: #1d4ed8;
  padding: 0.5rem 1rem;
  border-radius: 1rem;
  font-size: 0.875rem;
  font-weight: 600;
}

.progress-bar {
  width: 100%;
  height: 0.75rem;
  background: #e2e8f0;
  border-radius: 9999px;
  overflow: hidden;
  margin-bottom: 1rem;
}

.progress-fill {
  height: 100%;
  background: #3b82f6;
  transition: width 0.3s ease;
  border-radius: 9999px;
}

.progress-meta {
  display: flex;
  gap: 2rem;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: #64748b;
  font-size: 0.875rem;
}

.meta-icon {
  color: #9ca3af;
}

/* Questions Container */
.questions-container {
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

.question-card {
  background: white;
  border-radius: 0.75rem;
  overflow: hidden;
  box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06);
}

/* Question Header */
.question-header {
  padding: 1.5rem 1.5rem 1rem 1.5rem;
  border-bottom: 1px solid #f1f5f9;
}

.question-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.question-number {
  font-size: 0.875rem;
  font-weight: 600;
  color: #3b82f6;
  background: #eff6ff;
  padding: 0.25rem 0.75rem;
  border-radius: 1rem;
}

.question-badges {
  display: flex;
  gap: 0.5rem;
}

.badge {
  padding: 0.25rem 0.75rem;
  border-radius: 1rem;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
}

.badge-required {
  background: #fef3c7;
  color: #92400e;
}

.badge-completed {
  background: #d1fae5;
  color: #065f46;
}

.question-title {
  font-size: 1.125rem;
  font-weight: 600;
  color: #1e293b;
  margin: 0;
  line-height: 1.5;
}

/* Question Content */
.question-content {
  padding: 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.section-label {
  display: block;
  font-size: 0.875rem;
  font-weight: 600;
  color: #374151;
  margin-bottom: 0.75rem;
}

.feedback-label {
  color: #f59e0b;
}

/* Response Elements */
.response-textarea,
.comments-textarea {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid #d1d5db;
  border-radius: 0.5rem;
  font-size: 0.875rem;
  color: #374151;
  background: white;
  resize: vertical;
  font-family: inherit;
  transition: border-color 0.15s ease;
}

.response-textarea:focus,
.comments-textarea:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

/* Radio Group */
.radio-group {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.radio-option {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  cursor: pointer;
}

.radio-option input[type="radio"] {
  width: 1rem;
  height: 1rem;
  cursor: pointer;
}

.radio-label {
  font-size: 0.875rem;
  color: #374151;
  cursor: pointer;
}

/* Checkbox Group */
.checkbox-group {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

/* Checkbox Option */
.checkbox-option {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  cursor: pointer;
}

.checkbox-option input[type="checkbox"] {
  width: 1rem;
  height: 1rem;
  cursor: pointer;
}

.checkbox-label {
  font-size: 0.875rem;
  color: #374151;
  cursor: pointer;
}

/* Rating Group */
.rating-group {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.rating-controls {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.rating-slider {
  flex: 1;
  height: 0.5rem;
  background: #e2e8f0;
  border-radius: 9999px;
  outline: none;
  -webkit-appearance: none;
  appearance: none;
}

.rating-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 1.5rem;
  height: 1.5rem;
  background: #3b82f6;
  border-radius: 50%;
  cursor: pointer;
}

.rating-slider::-moz-range-thumb {
  width: 1.5rem;
  height: 1.5rem;
  background: #3b82f6;
  border-radius: 50%;
  cursor: pointer;
  border: none;
}

.rating-value {
  font-size: 1.125rem;
  font-weight: 600;
  color: #3b82f6;
  min-width: 2rem;
  text-align: center;
}

.rating-labels {
  font-size: 0.875rem;
  color: #6b7280;
  font-style: italic;
  text-align: center;
}

.rating-range {
  font-size: 0.75rem;
  color: #9ca3af;
  text-align: center;
}

.rating-stars {
  display: flex;
  gap: 0.25rem;
}

.rating-star {
  background: none;
  border: none;
  cursor: pointer;
  padding: 0.25rem;
  border-radius: 0.25rem;
  transition: all 0.2s ease;
  color: #d1d5db;
}

.rating-star:hover {
  color: #fbbf24;
  transform: scale(1.1);
}

.rating-star.filled {
  color: #fbbf24;
}

.rating-star svg {
  width: 1.5rem;
  height: 1.5rem;
}

.rating-label {
  font-size: 0.875rem;
  color: #6b7280;
  font-style: italic;
}

/* Date Input */
.date-input {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid #d1d5db;
  border-radius: 0.5rem;
  font-size: 0.875rem;
  color: #374151;
  background: white;
  transition: border-color 0.15s ease;
}

.date-input:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

/* Number Group */
.number-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.number-group .number-input {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid #d1d5db;
  border-radius: 0.5rem;
  font-size: 0.875rem;
  color: #374151;
  background: white;
  transition: border-color 0.15s ease;
}

.number-group .number-input:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.number-unit {
  font-size: 0.875rem;
  color: #6b7280;
  font-weight: 500;
  margin-left: 0.5rem;
}

.number-range {
  font-size: 0.75rem;
  color: #9ca3af;
  margin-top: 0.25rem;
}

/* Number Input (standalone) */
.number-input {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid #d1d5db;
  border-radius: 0.5rem;
  font-size: 0.875rem;
  color: #374151;
  background: white;
  transition: border-color 0.15s ease;
}

.number-input:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

/* Upload Area */
.upload-area {
  border: 2px dashed #d1d5db;
  border-radius: 0.75rem;
  padding: 2rem;
  text-align: center;
  background: #fafbfc;
  transition: border-color 0.2s ease;
  position: relative;
}

.upload-area:hover:not(.disabled) {
  border-color: #3b82f6;
}

.upload-area.disabled {
  opacity: 0.6;
  cursor: not-allowed;
  background: #f5f5f5;
}

.upload-text {
  color: #6b7280;
  font-size: 0.875rem;
  margin: 0;
}

.upload-info {
  color: #9ca3af;
  font-size: 0.75rem;
  margin: 0.25rem 0;
}

.upload-types {
  color: #9ca3af;
  font-size: 0.75rem;
  margin: 0 0 0.5rem 0;
  font-style: italic;
}

.file-input-hidden {
  position: absolute;
  opacity: 0;
  pointer-events: none;
}

.uploaded-files {
  margin-top: 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  text-align: left;
}

.uploaded-file {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem;
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 0.5rem;
}

.file-icon {
  width: 1.25rem;
  height: 1.25rem;
  color: #6b7280;
  flex-shrink: 0;
}

.file-name {
  flex: 1;
  font-size: 0.875rem;
  color: #374151;
  word-break: break-all;
}

.file-size {
  font-size: 0.75rem;
  color: #9ca3af;
  margin-left: 0.5rem;
  flex-shrink: 0;
}

.file-download {
  background: none;
  border: none;
  cursor: pointer;
  padding: 0.25rem;
  border-radius: 0.25rem;
  color: #3b82f6;
  transition: all 0.2s ease;
  flex-shrink: 0;
  text-decoration: none;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.file-download:hover {
  background: #eff6ff;
  color: #1d4ed8;
}

.file-download svg {
  width: 1rem;
  height: 1rem;
}

.file-remove {
  background: none;
  border: none;
  cursor: pointer;
  padding: 0.25rem;
  border-radius: 0.25rem;
  color: #ef4444;
  transition: all 0.2s ease;
  flex-shrink: 0;
}

.file-remove:hover {
  background: #fee2e2;
  color: #dc2626;
}

.file-remove svg {
  width: 1rem;
  height: 1rem;
}

/* Feedback Section */
.feedback-section {
  background: #fffbeb;
  border: 1px solid #fbbf24;
  border-radius: 0.5rem;
  padding: 1rem;
}

.feedback-content {
  color: #92400e;
  font-size: 0.875rem;
  line-height: 1.5;
  margin: 0;
}

/* Submit Section */
.submit-section {
  background: white;
  border-radius: 0.75rem;
  padding: 2rem;
  text-align: center;
  box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06);
}

.submit-title {
  font-size: 1.25rem;
  font-weight: 600;
  color: #1e293b;
  margin: 0 0 0.75rem 0;
}

.submit-description {
  color: #64748b;
  font-size: 0.875rem;
  margin: 0 0 1.5rem 0;
  line-height: 1.5;
}

.submit-actions {
  display: flex;
  justify-content: center;
  gap: 1rem;
  margin-bottom: 1rem;
}

.submit-warning {
  color: #dc2626;
  font-size: 0.875rem;
  margin: 0;
}

/* Submitted Message */
.submitted-message {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.75rem;
  padding: 1.5rem;
  background: #d1fae5;
  border: 1px solid #10b981;
  border-radius: 0.75rem;
  color: #065f46;
}

.submitted-message svg {
  width: 2rem;
  height: 2rem;
  color: #10b981;
}

.submitted-message span {
  font-size: 1.125rem;
  font-weight: 600;
}

.submission-time {
  font-size: 0.875rem;
  color: #047857;
  font-style: italic;
}

/* Disabled Input States */
.response-textarea:disabled,
.comments-textarea:disabled,
.date-input:disabled,
.number-input:disabled {
  background: #f9fafb;
  color: #6b7280;
  cursor: not-allowed;
  opacity: 0.7;
}

.rating-star:disabled {
  cursor: not-allowed;
  opacity: 0.7;
}

.rating-star:disabled:hover {
  transform: none;
  color: currentColor;
}

input[type="radio"]:disabled,
input[type="checkbox"]:disabled {
  cursor: not-allowed;
  opacity: 0.7;
}

.radio-option:has(input:disabled),
.checkbox-option:has(input:disabled) {
  opacity: 0.7;
  cursor: not-allowed;
}

/* Responsive Design */
@media (max-width: 1024px) {
  .header-content {
    padding: 0 1rem;
  }
  
  .response-content {
    padding: 1.5rem 1rem;
  }
  
  .progress-meta {
    flex-direction: column;
    gap: 0.75rem;
  }
}

@media (max-width: 768px) {
  .header-content {
    flex-direction: column;
    gap: 1rem;
    align-items: stretch;
  }
  
  .header-actions {
    justify-content: center;
  }
  
  .question-header {
    padding: 1rem;
  }
  
  .question-content {
    padding: 1rem;
  }
  
  .submit-actions {
    flex-direction: column;
    align-items: center;
  }
}

@media (max-width: 640px) {
  .header-actions {
    flex-direction: column;
  }
  
  .btn-primary,
  .btn-secondary {
    justify-content: center;
  }
  
  .progress-card {
    padding: 1rem;
  }
  
  .submit-section {
    padding: 1.5rem;
  }
  
  .rating-stars {
    justify-content: center;
  }
  
  .rating-star svg {
    width: 1.25rem;
    height: 1.25rem;
  }
  
  .uploaded-file {
    padding: 0.5rem;
    gap: 0.5rem;
  }
  
  .file-name {
    font-size: 0.8rem;
  }
}
</style>
