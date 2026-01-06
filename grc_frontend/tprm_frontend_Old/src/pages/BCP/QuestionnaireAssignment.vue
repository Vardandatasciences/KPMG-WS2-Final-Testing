<template>
  <div class="p-6 max-w-7xl mx-auto space-y-6">
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-3xl font-bold text-foreground">Answer Questionnaire</h1>
        <p class="text-muted-foreground">Complete assigned questionnaires</p>
      </div>
      <span class="badge badge--outline text-sm">Testing Phase</span>
    </div>


    <!-- Assignments Dropdown Section -->
    <div class="assignments-dropdown-section">
      <div class="assignments-dropdown">
        <label class="modern-label">
          <div class="label-content">
            <div class="label-icon">
              <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
              </svg>
            </div>
            <span class="label-text">Select Assignment</span>
          </div>
        </label>
        <div class="modern-dropdown" :class="{ 'is-open': isAssignmentsDropdownOpen }">
          <button 
            class="modern-trigger"
            @click="toggleAssignmentsDropdown"
            @blur="closeAssignmentsDropdown"
          >
            <div class="trigger-content">
              <div v-if="selectedAssignmentId" class="selected-assignment">
                <div class="selected-assignment-info">
                  <span class="selected-assignment-name">{{ getSelectedAssignmentDisplay() }}</span>
                  <div class="selected-assignment-badges">
                    <span :class="['mini-badge', getSelectedAssignmentStatus() === 'SUBMITTED' ? 'badge--success' : 'badge--warning']">
                      {{ getSelectedAssignmentStatus() }}
                    </span>
                  </div>
                </div>
              </div>
              <div v-else class="placeholder-content">
                <span class="placeholder-text">Choose an assignment...</span>
                <span class="placeholder-subtitle">Select from available questionnaire assignments</span>
              </div>
            </div>
            <div class="trigger-icon">
              <svg class="dropdown-arrow" :class="{ 'rotated': isAssignmentsDropdownOpen }" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"/>
              </svg>
            </div>
          </button>
          <Transition name="dropdown">
            <div v-if="isAssignmentsDropdownOpen" class="table-dropdown-menu">
              <div class="table-header">
                <span class="table-title">Available Assignments</span>
                <span class="table-count">{{ availableAssignments.length }} assignments</span>
              </div>
              <div class="table-container">
                <div v-if="isLoadingAssignments" class="loading-state">
                  <div class="loading-spinner"></div>
                  <p>Loading assignments...</p>
                </div>
                <div v-else-if="availableAssignments.length === 0" class="empty-state">
                  <div class="empty-icon">📋</div>
                  <p>No assignments available</p>
                  <p class="empty-subtitle">No questionnaire assignments found in the system</p>
                </div>
                <table v-else class="assignments-table">
                  <thead>
                    <tr>
                      <th class="checkbox-column">
                        <input 
                          type="checkbox" 
                          class="select-all-checkbox"
                          :checked="isAllAssignmentsSelected"
                          @change="toggleSelectAllAssignments"
                        />
                      </th>
                      <th>Assignment ID</th>
                      <th>Plan ID</th>
                      <th>Questionnaire ID</th>
                      <th>Questions</th>
                      <th>Due Date</th>
                      <th>Status</th>
                      <th>Assigned Date</th>
                      <th>Action</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr 
                      v-for="assignment in availableAssignments" 
                      :key="assignment.assignment_response_id"
                      class="assignment-row"
                      :class="{ 'selected': selectedAssignmentId === assignment.assignment_response_id.toString() }"
                    >
                      <td class="checkbox-column">
                        <input 
                          type="checkbox" 
                          class="assignment-checkbox"
                          :checked="selectedAssignmentId === assignment.assignment_response_id.toString()"
                          @change="selectAssignment(assignment)"
                        />
                      </td>
                      <td class="assignment-id-cell">{{ assignment.assignment_response_id }}</td>
                      <td class="plan-id-cell">{{ assignment.plan_id }}</td>
                      <td class="questionnaire-id-cell">{{ assignment.questionnaire_id }}</td>
                      <td class="questions-cell">{{ assignment.total_questions || 0 }}</td>
                      <td class="due-date-cell">{{ formatDate(assignment.due_date) }}</td>
                      <td>
                        <span :class="['badge', getAssignmentStatusBadgeClass(assignment.status)]">
                          {{ assignment.status }}
                        </span>
                      </td>
                      <td class="assigned-date-cell">{{ formatDate(assignment.assigned_at) }}</td>
                      <td class="action-cell">
                        <button 
                          class="select-assignment-btn"
                          @click="selectAssignment(assignment)"
                        >
                          Select
                        </button>
                        <button 
                          class="btn btn--ghost btn--sm ml-2"
                          @click="openAssignmentForAnswer(assignment)"
                        >
                          Answer ▶
                        </button>
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </Transition>
        </div>
      </div>
    </div>

    <!-- Answer Questionnaire Section -->
    <div v-if="selectedAssignment" class="card">
      <div class="card-header">
        <h3 class="card-title flex items-center gap-2">
          📝 Answer Questionnaire
        </h3>
      </div>
      <div class="card-content space-y-6">
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4 p-4 bg-muted/30 rounded-lg">
          <div>
            <label class="text-sm font-medium text-muted-foreground">Plan</label>
            <p class="font-medium">Plan ID: {{ selectedAssignment?.plan_id || 'N/A' }}</p>
          </div>
          <div>
            <label class="text-sm font-medium text-muted-foreground">Due Date</label>
            <p class="font-medium">{{ formatDate(selectedAssignment?.due_date) || 'N/A' }}</p>
          </div>
          <div>
            <label class="text-sm font-medium text-muted-foreground">Questionnaire</label>
            <p class="font-medium">Questionnaire ID: {{ selectedAssignment?.questionnaire_id || 'N/A' }}</p>
          </div>
        </div>

        <div class="space-y-6">
          <div v-for="(question, index) in assignmentQuestions" :key="question.id" class="p-4 border border-border rounded-lg space-y-4">
            <div class="flex gap-4">
              <div class="min-w-[2rem]">
                <span class="badge badge--outline">Q{{ index + 1 }}</span>
              </div>
              <div class="flex-1">
                <h4 class="font-medium mb-2">{{ question.question_text }}</h4>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div class="space-y-2">
                    <label>Answer</label>
                    <div v-if="question.answer_type === 'YES_NO'" class="space-y-2">
                      <div class="flex items-center space-x-2">
                        <input 
                          type="radio" 
                          :name="`question-${question.id}`" 
                          :id="`yes-${question.id}`" 
                          value="YES"
                          :checked="answers[question.id]?.answer === 'YES'"
                          @change="updateAnswer(question.id, 'YES')"
                        />
                        <label :for="`yes-${question.id}`">YES</label>
                      </div>
                      <div class="flex items-center space-x-2">
                        <input 
                          type="radio" 
                          :name="`question-${question.id}`" 
                          :id="`no-${question.id}`" 
                          value="NO"
                          :checked="answers[question.id]?.answer === 'NO'"
                          @change="updateAnswer(question.id, 'NO')"
                        />
                        <label :for="`no-${question.id}`">NO</label>
                      </div>
                    </div>
                    <div v-else-if="question.answer_type === 'MULTIPLE_CHOICE'" class="space-y-2">
                      <div v-for="(option, index) in question.choice_options" :key="index" class="flex items-center space-x-2">
                        <input 
                          type="checkbox" 
                          :id="`option-${question.id}-${index}`"
                          :value="option"
                          :checked="answers[question.id]?.answer?.includes(option) || false"
                          @change="updateMultipleChoiceAnswer(question.id, option, ($event.target as HTMLInputElement).checked)"
                        />
                        <label :for="`option-${question.id}-${index}`">{{ option }}</label>
                      </div>
                    </div>
                    <input 
                      v-else 
                      class="input" 
                      :value="answers[question.id]?.answer || ''"
                      @input="updateAnswer(question.id, ($event.target as HTMLInputElement).value)"
                      :placeholder="question.answer_type === 'TEXT' ? 'Enter your answer...' : ''"
                    />
                  </div>
                  <div class="space-y-2">
                    <label>Reason/Validation <span class="text-destructive">*</span></label>
                    <textarea 
                      class="input"
                      :value="answers[question.id]?.reason || ''"
                      @input="updateReason(question.id, ($event.target as HTMLTextAreaElement).value)"
                      rows="3"
                      placeholder="Provide reasoning for your answer..."
                    ></textarea>
                  </div>
                </div>
                <!-- Document Upload Section -->
                <div v-if="question.allow_document_upload" class="mt-4 p-4 bg-muted/20 rounded-lg border border-dashed border-border">
                  <div class="space-y-3">
                    <div class="flex items-center gap-2">
                      <svg class="h-4 w-4 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
                      </svg>
                      <span class="text-sm font-medium text-muted-foreground">Evidence Documents (Optional)</span>
                    </div>
                    <div class="space-y-2">
                      <input 
                        type="file" 
                        :id="`file-${question.id}`"
                        class="file-input"
                        multiple
                        accept=".pdf,.doc,.docx,.jpg,.jpeg,.png,.txt"
                        @change="handleFileUpload(question.id, $event)"
                      />
                      <label :for="`file-${question.id}`" class="file-input-label">
                        <svg class="h-4 w-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"/>
                        </svg>
                        Choose files or drag and drop
                      </label>
                      <p class="text-xs text-muted-foreground">PDF, DOC, DOCX, JPG, PNG, TXT files up to 10MB each</p>
                    </div>
                    <!-- Display uploaded files -->
                    <div v-if="answers[question.id]?.evidence_documents?.length > 0" class="space-y-2">
                      <div class="text-sm font-medium text-muted-foreground">Uploaded Files:</div>
                      <div v-for="(file, fileIndex) in answers[question.id]?.evidence_documents" :key="fileIndex" class="flex items-center justify-between p-2 bg-background rounded border">
                        <div class="flex items-center gap-2">
                          <svg class="h-4 w-4 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
                          </svg>
                          <span class="text-sm">{{ file.name }}</span>
                          <span class="text-xs text-muted-foreground">({{ formatFileSize(file.size) }})</span>
                        </div>
                        <button 
                          type="button"
                          class="btn btn--ghost btn--sm text-destructive"
                          @click="removeFile(question.id, fileIndex)"
                        >
                          <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
                          </svg>
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Reviewer Comment Section -->
        <div class="space-y-4">
          <h4 class="text-lg font-semibold text-foreground">Reviewer Comment</h4>
          <div class="space-y-2">
            <label for="reviewerComment" class="block text-sm font-medium">
              Reviewer Comment
              
            </label>
            <textarea 
              id="reviewerComment"
              class="input"
              v-model="reviewerComment"
              rows="4"
              placeholder="Enter any reviewer comments or notes about this assignment..."
            ></textarea>
          </div>
        </div>

        <div class="flex gap-4">
          <button 
            class="btn btn--outline" 
            @click="loadMockAnswers"
            :disabled="isSubmitting"
          >
            <svg class="h-4 w-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12"/>
            </svg>
            Load Data
          </button>
          <button 
            class="btn btn--outline" 
            @click="saveDraft"
            :disabled="isSubmitting"
          >
            <svg v-if="!isSubmitting" class="h-4 w-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7H5a2 2 0 00-2 2v9a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-3m-1 4l-3-3m0 0l-3 3m3-3v12"/>
            </svg>
            <svg v-else class="h-4 w-4 mr-2 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/>
            </svg>
            {{ isSubmitting ? 'Saving...' : 'Save Draft' }}
          </button>
          <button 
            class="btn btn--primary"
            @click="submitAnswers"
            :disabled="isSubmitting"
          >
            <svg v-if="!isSubmitting" class="h-4 w-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"/>
            </svg>
            <svg v-else class="h-4 w-4 mr-2 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/>
            </svg>
            {{ isSubmitting ? 'Submitting...' : 'Submit Answers' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import './QuestionnaireAssignment.css'
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import api from '../../services/api_bcp.js'
import { useNotifications } from '@/composables/useNotifications'
import { PopupService } from '@/popup/popupService'
import notificationService from '@/services/notificationService'
import loggingService from '@/services/loggingService'

// Router
const route = useRoute()
const { showSuccess, showError, showWarning, showInfo } = useNotifications()

// Assignments dropdown state
const availableAssignments = ref<any[]>([])
const selectedAssignmentId = ref<string>("")
const isAssignmentsDropdownOpen = ref(false)
const isLoadingAssignments = ref(false)
const selectedAssignment = ref<any>(null)

// Questions and answers state
const assignmentQuestions = ref<any[]>([])
const answers = ref<Record<string, { answer: string | string[], reason: string, evidence_documents: any[] }>>({})
const isSubmitting = ref(false)
const reviewerComment = ref<string>("")

// Computed properties
const isAllAssignmentsSelected = computed(() => {
  return availableAssignments.value.length > 0 && availableAssignments.value.every(assignment => 
    selectedAssignmentId.value === assignment.assignment_response_id.toString()
  )
})

// Utility functions
const formatDate = (dateString: string) => {
  if (!dateString) return 'N/A'
  const date = new Date(dateString)
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  })
}

const getAssignmentStatusBadgeClass = (status: string) => {
  if (!status) return "badge--secondary"
  switch (status) {
    case "SUBMITTED": return "badge--success"
    case "APPROVED": return "badge--success"
    case "IN_PROGRESS": return "badge--warning"
    case "ASSIGNED": return "badge--secondary"
    case "REJECTED": return "badge--destructive"
    case "REVIEWED": return "badge--default"
    default: return "badge--secondary"
  }
}

// Dropdown functions
const toggleAssignmentsDropdown = () => {
  isAssignmentsDropdownOpen.value = !isAssignmentsDropdownOpen.value
}

const closeAssignmentsDropdown = () => {
  setTimeout(() => {
    isAssignmentsDropdownOpen.value = false
  }, 150)
}

const selectAssignment = (assignment: any) => {
  selectedAssignmentId.value = assignment.assignment_response_id.toString()
  selectedAssignment.value = assignment
  isAssignmentsDropdownOpen.value = false
}

const toggleSelectAllAssignments = () => {
  if (isAllAssignmentsSelected.value) {
    selectedAssignmentId.value = ""
    selectedAssignment.value = null
  } else {
    if (availableAssignments.value.length > 0) {
      selectAssignment(availableAssignments.value[0])
    }
  }
}

const getSelectedAssignmentDisplay = () => {
  const assignment = availableAssignments.value.find(a => a.assignment_response_id.toString() === selectedAssignmentId.value)
  if (assignment) {
    return `[${assignment.assignment_response_id}] Plan ${assignment.plan_id} - Questionnaire ${assignment.questionnaire_id}`
  }
  return ""
}

const getSelectedAssignmentStatus = () => {
  const assignment = availableAssignments.value.find(a => a.assignment_response_id.toString() === selectedAssignmentId.value)
  return assignment ? assignment.status : ""
}

const openAssignmentForAnswer = async (assignment: any) => {
  console.log('Opening assignment for answer:', assignment)
  selectedAssignmentId.value = assignment.assignment_response_id.toString()
  selectedAssignment.value = assignment
  await loadAssignmentQuestions(assignment)
}

// API functions
const fetchAssignments = async () => {
  isLoadingAssignments.value = true
  try {
    console.log('Fetching assignments from API endpoint: /api/bcpdrp/questionnaires/assignments/')
    const response = await api.questionnaires.assignments()
    
    console.log('API response data:', response)
    
    // Check if assignments are in response.data.assignments or response.assignments
    const assignments = (response as any).assignments || (response as any).data?.assignments
    console.log('Assignments found:', assignments)
    
    if (assignments && Array.isArray(assignments)) {
      availableAssignments.value = assignments
      console.log('Successfully fetched assignments:', assignments.length, 'assignments')
    } else {
      console.error('API returned no assignments data or assignments is not an array')
      availableAssignments.value = []
    }
  } catch (error) {
    console.error('Error fetching assignments from API:', error)
    availableAssignments.value = []
    PopupService.error(`Failed to load assignments: ${error.message}. Please check your connection and try again.`, 'Loading Failed')
  } finally {
    isLoadingAssignments.value = false
  }
}

const loadAssignmentQuestions = async (assignment: any) => {
  try {
    console.log('Loading questions for assignment:', assignment)
    
    // Parse the questions data from the assignment's answer_text
    let questionsData = []
    if (assignment.questions_data && Array.isArray(assignment.questions_data)) {
      questionsData = assignment.questions_data
    } else if (assignment.answer_text) {
      try {
        const parsedData = JSON.parse(assignment.answer_text)
        const rawQuestionsData = parsedData.questions_data || []
        
        // Handle both array and object formats
        if (Array.isArray(rawQuestionsData)) {
          questionsData = rawQuestionsData
        } else if (typeof rawQuestionsData === 'object' && rawQuestionsData !== null) {
          // Convert object to array
          questionsData = Object.values(rawQuestionsData)
        } else {
          questionsData = []
        }
      } catch (e) {
        console.error('Error parsing assignment answer_text:', e)
        questionsData = []
      }
    }
    
    // Convert questions data to array format for display
    assignmentQuestions.value = questionsData.map(question => ({
      id: question.question_id,
      question_text: question.question_text || `Question ${question.question_id}`,
      answer_type: question.answer_type || 'TEXT',
      choice_options: question.choice_options || [],
      allow_document_upload: question.allow_document_upload || false,
      answer: question.answer || '',
      reason: question.reason || ''
    }))
    
    // Initialize answers object with existing data
    answers.value = {}
    assignmentQuestions.value.forEach(question => {
      answers.value[question.id] = {
        answer: question.answer,
        reason: question.reason,
        evidence_documents: question.evidence_documents || []
      }
    })
    
    // Load existing reviewer comment if available
    reviewerComment.value = assignment.owner_comment || ""
    
    console.log('Loaded questions:', assignmentQuestions.value.length)
    console.log('Initialized answers:', answers.value)
    console.log('Loaded reviewer comment:', reviewerComment.value)
  } catch (error) {
    console.error('Error loading assignment questions:', error)
    PopupService.error(`Failed to load questions: ${error.message}`, 'Loading Failed')
  }
}

// Form handling functions
const updateAnswer = (questionId: number, answer: string) => {
  if (!answers.value[questionId]) {
    answers.value[questionId] = { answer: '', reason: '', evidence_documents: [] }
  }
  answers.value[questionId].answer = answer
}

const updateMultipleChoiceAnswer = (questionId: number, option: string, isChecked: boolean) => {
  if (!answers.value[questionId]) {
    answers.value[questionId] = { answer: [], reason: '', evidence_documents: [] }
  }
  
  if (!Array.isArray(answers.value[questionId].answer)) {
    answers.value[questionId].answer = []
  }
  
  if (isChecked) {
    if (!answers.value[questionId].answer.includes(option)) {
      answers.value[questionId].answer.push(option)
    }
  } else {
    answers.value[questionId].answer = answers.value[questionId].answer.filter((item: string) => item !== option)
  }
}

const updateReason = (questionId: number, reason: string) => {
  if (!answers.value[questionId]) {
    answers.value[questionId] = { answer: '', reason: '', evidence_documents: [] }
  }
  answers.value[questionId].reason = reason
}

const handleFileUpload = (questionId: number, event: Event) => {
  const target = event.target as HTMLInputElement
  const files = target.files
  
  if (!files || files.length === 0) return
  
  if (!answers.value[questionId]) {
    answers.value[questionId] = { answer: '', reason: '', evidence_documents: [] }
  }
  
  // Add new files to existing documents
  const newFiles = Array.from(files).map(file => ({
    name: file.name,
    size: file.size,
    type: file.type,
    file: file, // Store the actual file object for upload
    id: Date.now() + Math.random() // Generate unique ID
  }))
  
  answers.value[questionId].evidence_documents = [
    ...answers.value[questionId].evidence_documents,
    ...newFiles
  ]
  
  // Clear the input
  target.value = ''
}

const removeFile = (questionId: number, fileIndex: number) => {
  if (answers.value[questionId]?.evidence_documents) {
    answers.value[questionId].evidence_documents.splice(fileIndex, 1)
  }
}

const formatFileSize = (bytes: number) => {
  if (bytes === 0) return '0 Bytes'
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

const saveDraft = async () => {
  if (!selectedAssignment.value) {
    PopupService.warning('Please select an assignment first', 'No Assignment Selected')
    return
  }
  
  isSubmitting.value = true
  try {
    const response = await api.questionnaires.saveAnswers(selectedAssignment.value.assignment_response_id, {
      answers: answers.value,
      reviewer_comment: reviewerComment.value,
      is_final_submission: false
    })
    
    if (response) {
      PopupService.success('Draft saved successfully!', 'Draft Saved')
      // Create notification
      await notificationService.createQuestionnaireNotification('draft_saved', {
        assignment_id: selectedAssignment.value.assignment_response_id,
        questions_answered: Object.keys(answers.value).length
      })
      // Refresh the assignment data to show updated status
      await fetchAssignments()
    }
  } catch (error) {
    console.error('Error saving draft:', error)
    PopupService.error(`Failed to save draft: ${error.message}`, 'Save Failed')
    // Create error notification
    await notificationService.createQuestionnaireNotification('submission_failed', {
      assignment_id: selectedAssignment.value.assignment_response_id,
      error: error.message
    })
  } finally {
    isSubmitting.value = false
  }
}

const submitAnswers = async () => {
  if (!selectedAssignment.value) {
    await showWarning('No Assignment Selected', 'Please select an assignment first.', {
      action: 'no_assignment_selected'
    })
    PopupService.warning('Please select an assignment first.', 'No Assignment Selected')
    return
  }
  
  // Validate that all questions have answers and reasons
  const unansweredQuestions = []
  const questionsWithoutReasons = []
  
  assignmentQuestions.value.forEach(question => {
    const answer = answers.value[question.id]
    
    // Check if answer is provided
    let hasAnswer = false
    if (answer?.answer) {
      if (Array.isArray(answer.answer)) {
        hasAnswer = answer.answer.length > 0
      } else {
        hasAnswer = answer.answer.trim().length > 0
      }
    }
    
    if (!answer || !hasAnswer) {
      unansweredQuestions.push(question.id)
    }
    if (!answer || !answer.reason.trim()) {
      questionsWithoutReasons.push(question.id)
    }
  })
  
  if (unansweredQuestions.length > 0) {
    await showWarning('Incomplete Answers', `Please answer all questions. Missing answers for questions: ${unansweredQuestions.join(', ')}`, {
      action: 'incomplete_answers',
      unanswered_questions: unansweredQuestions,
      assignment_id: selectedAssignment.value.id
    })
    PopupService.warning(`Please answer all questions. Missing answers for questions: ${unansweredQuestions.join(', ')}`, 'Incomplete Answers')
    // Create notification
    await notificationService.createQuestionnaireNotification('incomplete_answers', {
      unanswered_questions: unansweredQuestions
    })
    return
  }
  
  if (questionsWithoutReasons.length > 0) {
    await showWarning('Missing Reasons', `Please provide reasons for all answers. Missing reasons for questions: ${questionsWithoutReasons.join(', ')}`, {
      action: 'missing_reasons',
      questions_without_reasons: questionsWithoutReasons,
      assignment_id: selectedAssignment.value.id
    })
    PopupService.warning(`Please provide reasons for all answers. Missing reasons for questions: ${questionsWithoutReasons.join(', ')}`, 'Missing Reasons')
    // Create notification
    await notificationService.createQuestionnaireNotification('missing_reasons', {
      questions_without_reasons: questionsWithoutReasons
    })
    return
  }
  
  isSubmitting.value = true
  try {
    const response = await api.questionnaires.saveAnswers(selectedAssignment.value.assignment_response_id, {
      answers: answers.value,
      reviewer_comment: reviewerComment.value,
      is_final_submission: true
    })
    
    if (response) {
      // Show success notification
      await showSuccess('Answers Submitted', 'Answers submitted successfully!', {
        action: 'answers_submitted',
        assignment_id: selectedAssignment.value.id,
        questions_answered: Object.keys(answers.value).length
      })
      
      // Show success popup
      PopupService.success('Answers submitted successfully!', 'Answers Submitted')
      
      // Create additional notification service notification
      await notificationService.createQuestionnaireNotification('answers_submitted', {
        assignment_id: selectedAssignment.value.assignment_response_id,
        questions_answered: Object.keys(answers.value).length
      })
      
      // Refresh the assignment data to show updated status
      await fetchAssignments()
      // Clear the form
      answers.value = {}
      assignmentQuestions.value = []
      reviewerComment.value = ""
      selectedAssignment.value = null
      selectedAssignmentId.value = ""
    }
  } catch (error) {
    console.error('Error submitting answers:', error)
    
    // Show error notification
    await showError('Submission Failed', 'Failed to submit answers. Please try again.', {
      action: 'answers_submission_failed',
      assignment_id: selectedAssignment.value?.id,
      error_message: error.message
    })
    
    // Show error popup
    PopupService.error('Failed to submit answers. Please try again.', 'Submission Failed')
    
    // Create additional notification service notification
    await notificationService.createQuestionnaireNotification('submission_failed', {
      assignment_id: selectedAssignment.value?.assignment_response_id,
      error: error.message
    })
  } finally {
    isSubmitting.value = false
  }
}

// Handle assignment preselection from URL
const handleAssignmentPreselection = async () => {
  const assignmentIdFromUrl = route.query.assignmentId as string
  console.log('Assignment ID from URL:', assignmentIdFromUrl)
  
  if (assignmentIdFromUrl && availableAssignments.value.length > 0) {
    const targetAssignment = availableAssignments.value.find(
      assignment => assignment.assignment_response_id.toString() === assignmentIdFromUrl
    )
    
    if (targetAssignment) {
      console.log('Found target assignment:', targetAssignment)
      selectedAssignmentId.value = assignmentIdFromUrl
      selectedAssignment.value = targetAssignment
      await loadAssignmentQuestions(targetAssignment)
    } else {
      console.warn('Assignment with ID', assignmentIdFromUrl, 'not found in available assignments')
    }
  }
}

// Mock data functions
const getBCPMockAnswers = () => {
  return {
    answers: {
      1: {
        answer: 'YES',
        reason: 'All critical business functions including core banking operations, customer service, and regulatory compliance are clearly identified and documented in the BCP with detailed procedures for each function.',
        evidence_documents: []
      },
      2: {
        answer: ['1-4 hours'],
        reason: 'The maximum acceptable downtime for core banking operations is set at 4 hours based on regulatory requirements and customer expectations. This aligns with industry best practices for financial institutions.',
        evidence_documents: []
      },
      3: {
        answer: 'The communication plan includes a multi-channel approach: 1) Automated SMS and email notifications to all customers within 30 minutes, 2) Website banner and social media updates, 3) Direct calls to key stakeholders and regulators, 4) Press releases for major incidents. The plan includes escalation procedures and backup communication methods.',
        reason: 'This comprehensive communication strategy ensures all stakeholders are informed promptly and consistently during any business disruption, maintaining trust and regulatory compliance.',
        evidence_documents: []
      },
      4: {
        answer: 'YES',
        reason: 'Backup procedures are fully documented for all critical systems including core banking, payment processing, customer databases, and regulatory reporting systems. Each procedure includes step-by-step instructions, contact information, and recovery timelines.',
        evidence_documents: []
      },
      5: {
        answer: ['Quarterly'],
        reason: 'BCP testing is conducted quarterly with comprehensive annual reviews. This frequency ensures procedures remain current and effective while meeting regulatory requirements for financial institutions.',
        evidence_documents: []
      },
      6: {
        answer: 'Alternative work arrangements include: 1) Remote work capabilities for 80% of staff with secure VPN access, 2) Rotating shift schedules to maintain operations, 3) Cross-training programs ensuring multiple staff can perform critical functions, 4) Temporary office space arrangements with key vendors.',
        reason: 'These arrangements ensure business continuity even during personnel disruptions, maintaining service levels and operational efficiency.',
        evidence_documents: []
      },
      7: {
        answer: 'YES',
        reason: 'The BCP addresses all relevant regulatory requirements including SOX, Basel III, PCI DSS, and FFIEC guidelines. Regular compliance reviews ensure alignment with current regulations and industry standards.',
        evidence_documents: []
      },
      8: {
        answer: 'The escalation procedure follows a three-tier approach: 1) Level 1: Department heads assess and respond to incidents within 15 minutes, 2) Level 2: Business continuity team activation within 30 minutes for significant disruptions, 3) Level 3: Executive crisis management team activation within 1 hour for major events. Each level has defined decision-making authority and communication protocols.',
        reason: 'This structured escalation ensures rapid response to business continuity events while maintaining clear accountability and decision-making authority at each level.',
        evidence_documents: []
      }
    },
    reviewerComment: 'BCP assessment completed with comprehensive responses. All critical business functions are well-documented with realistic recovery objectives. Communication plans are thorough and regulatory compliance is excellent. Recommend approval with minor updates to testing frequency.'
  }
}

const getDRPMockAnswers = () => {
  return {
    answers: {
      1: {
        answer: 'YES',
        reason: 'All critical IT systems including core banking applications, payment processing systems, customer databases, and network infrastructure are comprehensively identified and documented in the DRP with detailed recovery procedures.',
        evidence_documents: []
      },
      2: {
        answer: ['1-4 hours'],
        reason: 'The RTO for primary data center systems is set at 4 hours based on business requirements and technical capabilities. This includes automated failover mechanisms and manual recovery procedures for critical applications.',
        evidence_documents: []
      },
      3: {
        answer: 'Data backup and replication strategy includes: 1) Real-time replication to secondary data center for critical databases, 2) Daily incremental backups with weekly full backups, 3) Off-site storage of backup media with 30-day retention, 4) Cloud-based backup for non-critical systems, 5) Regular backup testing and validation procedures.',
        reason: 'This multi-layered approach ensures data protection and rapid recovery capabilities while meeting regulatory requirements for data integrity and availability.',
        evidence_documents: []
      },
      4: {
        answer: 'YES',
        reason: 'Automated failover procedures are implemented for critical systems including database clusters, load balancers, and network infrastructure. Manual failover procedures are documented for systems that cannot be automated.',
        evidence_documents: []
      },
      5: {
        answer: ['Quarterly'],
        reason: 'Disaster recovery testing is conducted quarterly with comprehensive annual exercises. This includes tabletop exercises, partial failover tests, and full DR drills to validate procedures and identify improvement areas.',
        evidence_documents: []
      },
      6: {
        answer: 'Network connectivity requirements include: 1) Primary connection: 1Gbps dedicated fiber with 99.9% SLA, 2) Backup connection: 500Mbps redundant link, 3) Internet connectivity: 100Mbps with multiple ISP providers, 4) VPN capacity for 200 concurrent users, 5) Load balancing and traffic management capabilities.',
        reason: 'These connectivity specifications ensure adequate bandwidth and redundancy for recovery operations while maintaining performance standards for critical applications.',
        evidence_documents: []
      },
      7: {
        answer: 'YES',
        reason: 'Security controls are maintained at the same level during recovery operations through: 1) Replicated security policies and configurations, 2) Same authentication and authorization systems, 3) Network security controls including firewalls and intrusion detection, 4) Regular security assessments of recovery environment.',
        evidence_documents: []
      },
      8: {
        answer: 'Data integrity validation procedure includes: 1) Automated checksums verification for all replicated data, 2) Database consistency checks using built-in tools, 3) Application-level data validation tests, 4) User acceptance testing with sample transactions, 5) Performance monitoring and capacity validation, 6) Rollback procedures if integrity issues are detected.',
        reason: 'This comprehensive validation process ensures data accuracy and system reliability after recovery, maintaining business continuity and regulatory compliance.',
        evidence_documents: []
      },
      9: {
        answer: 'YES',
        reason: 'Cloud-based recovery options are considered and documented including: 1) AWS/Azure disaster recovery services for non-critical applications, 2) Cloud backup solutions for data archiving, 3) Hybrid cloud architecture for scalable recovery, 4) Cost-benefit analysis and implementation timeline.',
        evidence_documents: []
      },
      10: {
        answer: 'Incident response coordination includes: 1) Joint IT-Business crisis management team with defined roles, 2) 24/7 incident response hotline and escalation procedures, 3) Regular communication protocols between teams, 4) Shared incident tracking and documentation systems, 5) Post-incident review and lessons learned processes.',
        reason: 'This coordinated approach ensures effective communication and decision-making during IT incidents, minimizing business impact and maintaining stakeholder confidence.',
        evidence_documents: []
      }
    },
    reviewerComment: 'DRP assessment completed with excellent technical depth. All critical systems are properly identified with realistic RTO targets. Backup and recovery procedures are comprehensive and security controls are well-maintained. Cloud recovery options show forward-thinking approach. Recommend approval.'
  }
}

const loadMockAnswers = () => {
  if (!selectedAssignment.value) {
    PopupService.warning('Please select an assignment first before loading mock data.', 'No Assignment Selected')
    return
  }

  if (Object.keys(answers.value).length > 0) {
    PopupService.confirm('This will replace all existing answers. Continue?', 'Confirm Replace', 
      () => {
        // Continue with loading mock data
        loadMockAnswersConfirmed()
      },
      () => {
        // User cancelled
        return
      }
    )
    return
  }
  
  loadMockAnswersConfirmed()
}

const loadMockAnswersConfirmed = () => {

  // Determine if this is BCP or DRP based on assignment data or questions
  let mockData
  const isBCP = assignmentQuestions.value.some(q => 
    q.question_text.toLowerCase().includes('business continuity') || 
    q.question_text.toLowerCase().includes('bcp')
  )
  
  if (isBCP) {
    mockData = getBCPMockAnswers()
    console.log('Loading BCP mock answers')
  } else {
    mockData = getDRPMockAnswers()
    console.log('Loading DRP mock answers')
  }

  // Map mock data to actual question IDs
  const newAnswers = {}
  assignmentQuestions.value.forEach((question, index) => {
    const mockAnswerKey = (index + 1).toString()
    if (mockData.answers[mockAnswerKey]) {
      newAnswers[question.id] = mockData.answers[mockAnswerKey]
    }
  })

  // Load the mock data with correct question IDs
  answers.value = newAnswers
  reviewerComment.value = mockData.reviewerComment
  
  console.log('Loaded answers:', answers.value)
  console.log('Assignment questions:', assignmentQuestions.value)
  
  PopupService.success(`Mock answers loaded for ${isBCP ? 'BCP' : 'DRP'} questionnaire. You can now review and modify the answers before submitting.`, 'Mock Data Loaded')
}

// Load assignments on component mount
onMounted(async () => {
  await loggingService.logPageView('BCP', 'Questionnaire Assignment')
  await fetchAssignments()
  // After assignments are loaded, check for URL parameter
  await handleAssignmentPreselection()
})
</script>
