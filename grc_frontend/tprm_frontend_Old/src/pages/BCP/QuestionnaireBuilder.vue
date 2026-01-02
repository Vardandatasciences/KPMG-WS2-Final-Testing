<template>
  <div class="p-6 max-w-7xl mx-auto space-y-6">
    <div class="flex items-center justify-between">
    <div>
        <h1 class="text-3xl font-bold text-foreground">Build & Review Questionnaire</h1>
        <p class="text-muted-foreground">Create and review testing questionnaires for BCP/DRP plans</p>
      </div>
      <div class="badge badge--outline text-sm">Testing Phase</div>
    </div>

    <!-- REVIEWER VIEW -->
    <div class="space-y-6">
        <!-- Questionnaire Selection Dropdown -->
        <div class="questionnaire-dropdown-section">
          <div class="questionnaire-dropdown">
            <label class="modern-label">
              <div class="label-content">
                <div class="label-icon">
                  <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2V7a2 2 0 00-2-2H9z"/>
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 9h10m-10 4h10m-10 4h10"/>
                  </svg>
                </div>
                <span class="label-text">Select Questionnaire</span>
              </div>
            </label>
            <div class="modern-dropdown" :class="{ 'is-open': isDropdownOpen }">
              <button 
                class="modern-trigger"
                @click="toggleDropdown"
                @blur="closeDropdown"
              >
                <div class="trigger-content">
                  <div v-if="selectedQuestionnaireId" class="selected-questionnaire">
                    <div class="selected-questionnaire-info">
                      <span class="selected-questionnaire-name">{{ getSelectedQuestionnaireDisplay() }}</span>
                      <div class="selected-questionnaire-badges">
                        <span :class="['mini-badge', getSelectedQuestionnaireType() === 'BCP' ? 'badge--default' : 'badge--secondary']">
                          {{ getSelectedQuestionnaireType() }}
                        </span>
                      </div>
                    </div>
                  </div>
                  <div v-else class="placeholder-content">
                    <span class="placeholder-text">Choose a questionnaire...</span>
                    <span class="placeholder-subtitle">Select from available questionnaires</span>
                  </div>
                </div>
                <div class="trigger-icon">
                  <svg class="dropdown-arrow" :class="{ 'rotated': isDropdownOpen }" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"/>
                  </svg>
                </div>
              </button>
              <Transition name="dropdown">
                <div v-if="isDropdownOpen" class="dropdown-content">
                  <div class="table-header">
                    <span class="table-title">Available Questionnaires</span>
                    <span class="table-count">{{ availableQuestionnaires.length }} questionnaires</span>
                  </div>
                  <div class="table-container">
                    <div v-if="isLoadingQuestionnaires" class="loading-state">
                      <div class="loading-spinner"></div>
                      <p>Loading questionnaires...</p>
                    </div>
                    <div v-else-if="availableQuestionnaires.length === 0" class="empty-state">
                      <div class="empty-icon">📝</div>
                      <p>No questionnaires available</p>
                      <p class="empty-subtitle">No questionnaires found in the system</p>
                    </div>
                    <table v-else class="questionnaires-table">
                      <thead>
                        <tr>
                          <th class="checkbox-column">
                            <input type="checkbox" class="select-all-checkbox" />
                          </th>
                          <th>ID</th>
                          <th>Title</th>
                          <th>Type</th>
                          <th>Status</th>
                          <th>Owner</th>
                          <th>Questions</th>
                        </tr>
                      </thead>
                      <tbody>
                        <tr 
                          v-for="questionnaire in availableQuestionnaires" 
                          :key="questionnaire.questionnaire_id"
                          class="questionnaire-row"
                          :class="{ 'selected': selectedQuestionnaireId === questionnaire.questionnaire_id.toString() }"
                        >
                          <td class="checkbox-column">
                            <input 
                              type="checkbox" 
                              class="questionnaire-checkbox"
                              :checked="selectedQuestionnaireId === questionnaire.questionnaire_id.toString()"
                              @change="selectQuestionnaire(questionnaire)"
                            />
                          </td>
                          <td class="questionnaire-id-cell">{{ questionnaire.questionnaire_id }}</td>
                          <td class="questionnaire-name-cell">{{ questionnaire.title }}</td>
                          <td>
                            <span :class="['badge', questionnaire.planType === 'BCP' ? 'badge--default' : 'badge--secondary']">
                              {{ questionnaire.planType }}
                            </span>
                          </td>
                          <td>
                            <span class="badge badge--outline">
                              {{ questionnaire.status || 'DRAFT' }}
                            </span>
                          </td>
                          <td class="owner-cell">{{ questionnaire.owner || 'N/A' }}</td>
                          <td class="questions-cell">{{ questionnaire.questionCount || 0 }}</td>
                        </tr>
                      </tbody>
                    </table>
                  </div>
                </div>
              </Transition>
            </div>
          </div>
        </div>

        <div class="card" v-if="selectedQuestionnaireData">
          <div class="card-header">
            <h3 class="card-title flex items-center gap-2">
              👀 Review Selected Questionnaire
            </h3>
          </div>
          <div class="card-content space-y-6">
            <div class="grid grid-cols-1 gap-4 p-4 bg-muted/30 rounded-lg">
              <div>
                <label class="label text-sm font-medium text-muted-foreground">Questionnaire</label>
                <p class="font-medium">{{ selectedQuestionnaireData.title }} (v{{ selectedQuestionnaireData.version || '1.0' }})</p>
              </div>
              <div>
                <label class="label text-sm font-medium text-muted-foreground">Created by</label>
                <p class="font-medium">{{ selectedQuestionnaireData.owner || 'Owner A' }}</p>
              </div>
              <div>
                <label class="label text-sm font-medium text-muted-foreground">Status</label>
                <div class="badge badge--default">{{ selectedQuestionnaireData.status || 'IN_REVIEW' }}</div>
              </div>
            </div>

            <div>
              <h4 class="font-medium mb-4">Questions Preview (Read-only)</h4>
              <div class="overflow-x-auto">
                <div v-if="!selectedQuestionnaireData.questions || selectedQuestionnaireData.questions.length === 0" class="text-center py-8 text-muted-foreground">
                  No questions available for this questionnaire
                </div>
                <table v-else class="table">
                  <thead>
                    <tr>
                      <th>#</th>
                      <th>Question Text</th>
                      <th>Type</th>
                      <th>Required?</th>
                      <th>Weight</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="(question, index) in selectedQuestionnaireData.questions" :key="question.id">
                      <td>{{ index + 1 }}</td>
                      <td class="max-w-md">{{ question.text }}</td>
                      <td>
                        <div class="badge badge--secondary">{{ question.type }}</div>
                        <div v-if="question.type === 'MULTIPLE_CHOICE' && question.choice_options?.length > 0" class="choice-options-display mt-2">
                          <div class="text-xs text-muted-foreground mb-1">
                            {{ question.choice_options.length }} options:
                          </div>
                          <div class="choice-options-list">
                            <div 
                              v-for="(option, optionIndex) in question.choice_options" 
                              :key="optionIndex" 
                              class="choice-option-item"
                            >
                              <span class="choice-option-number">{{ optionIndex + 1 }}.</span>
                              <span class="choice-option-text">{{ option }}</span>
                            </div>
                          </div>
                        </div>
                        <div v-if="question.allow_document_upload" class="text-xs text-muted-foreground mt-1">
                          📎 Document upload allowed
                        </div>
                      </td>
                      <td>{{ question.required ? "✓" : "—" }}</td>
                      <td>{{ question.weight || 1.0 }}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>

            <div class="space-y-2">
              <label class="label" for="reviewComment">Overall Review Comment</label>
              <div v-if="selectedQuestionnaireData.reviewer_comment" class="p-3 bg-muted/20 rounded border-l-4 border-primary mb-2">
                <p class="text-sm text-muted-foreground mb-1">Existing Review Comment:</p>
                <p class="text-sm">{{ selectedQuestionnaireData.reviewer_comment }}</p>
              </div>
              <textarea 
                class="textarea" 
                id="reviewComment"
                :placeholder="selectedQuestionnaireData.reviewer_comment ? 'Update the review comment...' : 'e.g., Add question on failback test procedure.'"
                v-model="reviewComment"
                rows="4"
              ></textarea>
            </div>

            <button 
              class="btn btn--primary" 
              @click="submitReviewComment" 
              :disabled="!reviewComment.trim() || isSubmittingReview"
            >
              <svg v-if="!isSubmittingReview" class="h-4 w-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"/>
              </svg>
              <div v-else class="loading-spinner-sm mr-2"></div>
              {{ isSubmittingReview ? 'Submitting...' : (selectedQuestionnaireData?.reviewer_comment ? 'Update Review Comment' : 'Submit Review Comment') }}
            </button>
          </div>
        </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import http from '../../api/http'
import { questionnaireApi } from '../../api/questionnaire.js'
import { useNotifications } from '@/composables/useNotifications'
import { PopupService } from '@/popup/popupService'
import loggingService from '@/services/loggingService'
import './QuestionnaireBuilder.css'

const route = useRoute()
const router = useRouter()
const { showSuccess, showError, showWarning, showInfo } = useNotifications()

const reviewComment = ref('')

// Review View questionnaire dropdown data
const availableQuestionnaires = ref([])
const selectedQuestionnaireId = ref('')
const selectedQuestionnaireData = ref(null)
const isLoadingQuestionnaires = ref(false)
const isDropdownOpen = ref(false)
const isSubmittingReview = ref(false)

const submitReviewComment = async () => {
  if (!selectedQuestionnaireId.value || !reviewComment.value.trim()) {
    await showWarning('Missing Information', 'Please select a questionnaire and enter a review comment.', {
      action: 'review_validation_failed',
      questionnaire_id: selectedQuestionnaireId.value,
      has_comment: !!reviewComment.value.trim()
    })
    PopupService.warning('Please select a questionnaire and enter a review comment.', 'Missing Information')
    return
  }

  isSubmittingReview.value = true

  try {
    console.log('Submitting review comment for questionnaire:', selectedQuestionnaireId.value)
    console.log('Review comment:', reviewComment.value)
    
    // Prepare the data to send to the API
    const reviewData = {
      questionnaire_id: parseInt(selectedQuestionnaireId.value),
      reviewer_comment: reviewComment.value.trim()
    }

    // Make API call to save the review comment
    const response = await http.put(`/bcpdrp/questionnaires/${selectedQuestionnaireId.value}/review/`, reviewData)

    console.log('Review comment saved successfully:', response.data)
    
    // Show success notification
    await showSuccess('Review Submitted', 'Review comment submitted successfully!', {
      action: 'review_submitted',
      questionnaire_id: selectedQuestionnaireId.value,
      comment_length: reviewComment.value.trim().length
    })
    
    // Show success popup
    PopupService.success('Review comment submitted successfully!', 'Review Submitted')
    
    // Clear the comment after successful submission
    reviewComment.value = ''
    
    // Update the questionnaire data to show the updated comment
    if (selectedQuestionnaireData.value) {
      selectedQuestionnaireData.value.reviewer_comment = reviewData.reviewer_comment
    }
    
    // Redirect to My Approvals screen
    router.push('/bcp/my-approvals')
    
  } catch (error) {
    console.error('Error submitting review comment:', error)
    
    // Show error notification
    await showError('Submission Failed', 'Error submitting review comment. Please try again.', {
      action: 'review_submission_failed',
      questionnaire_id: selectedQuestionnaireId.value,
      error_message: error.response?.data?.message || error.message || 'Unknown error'
    })
    
    // Show error popup
    PopupService.error('Error submitting review comment. Please try again.', 'Submission Failed')
  } finally {
    isSubmittingReview.value = false
  }
}

// Review View functions
const fetchQuestionnaires = async () => {
  isLoadingQuestionnaires.value = true
  try {
    console.log('Fetching questionnaires from API endpoint: /api/bcpdrp/questionnaires/')
    const response = await questionnaireApi.getQuestionnaires()
    
    console.log('API response data:', response)
    console.log('Response type:', typeof response)
    console.log('Response keys:', Object.keys(response))
    
    // Try both possible structures
    const questionnairesData = (response as any).questionnaires || (response as any).data?.questionnaires || []
    console.log('Questionnaires found:', questionnairesData)
    console.log('Questionnaires type:', typeof questionnairesData)
    console.log('Questionnaires length:', questionnairesData ? questionnairesData.length : 'undefined')
    
    if (questionnairesData && Array.isArray(questionnairesData)) {
      availableQuestionnaires.value = questionnairesData
      console.log('Successfully fetched questionnaires:', questionnairesData.length, 'questionnaires')
    } else {
      console.error('API returned no questionnaires data or questionnaires is not an array')
      console.error('Response structure:', JSON.stringify(response, null, 2))
      availableQuestionnaires.value = []
    }
  } catch (error) {
    console.error('Error fetching questionnaires from API:', error)
    availableQuestionnaires.value = []
    PopupService.error(`Failed to load questionnaires: ${error.message}. Please check your connection and try again.`, 'Loading Failed')
  } finally {
    isLoadingQuestionnaires.value = false
  }
}

const toggleDropdown = () => {
  isDropdownOpen.value = !isDropdownOpen.value
}

const closeDropdown = () => {
  setTimeout(() => {
    isDropdownOpen.value = false
  }, 150)
}

const selectQuestionnaire = async (questionnaire: any) => {
  selectedQuestionnaireId.value = questionnaire.questionnaire_id.toString()
  isDropdownOpen.value = false
  
  try {
    // Fetch detailed questionnaire data
    const response = await questionnaireApi.getQuestionnaireDetail(questionnaire.questionnaire_id)
    console.log('Questionnaire details response:', response)
    
    selectedQuestionnaireData.value = response.data || response
    console.log('Selected questionnaire data:', selectedQuestionnaireData.value)
  } catch (error) {
    console.error('Error fetching questionnaire details:', error)
    PopupService.error('Failed to load questionnaire details', 'Loading Failed')
  }
}

const getSelectedQuestionnaireDisplay = () => {
  const questionnaire = availableQuestionnaires.value.find(q => q.questionnaire_id.toString() === selectedQuestionnaireId.value)
  if (questionnaire) {
    return `[${questionnaire.questionnaire_id}] ${questionnaire.title} (${questionnaire.planType})`
  }
  return ""
}

const getSelectedQuestionnaireType = () => {
  const questionnaire = availableQuestionnaires.value.find(q => q.questionnaire_id.toString() === selectedQuestionnaireId.value)
  return questionnaire ? questionnaire.planType : ""
}

// Initialize component
onMounted(async () => {
  await loggingService.logPageView('BCP', 'Questionnaire Builder')
  await fetchQuestionnaires()
  
  // Check for URL parameters to preselect questionnaire and set tab
  const questionnaireIdFromUrl = route.query.questionnaireId
  const tabFromUrl = route.query.tab
  
  // Preselect questionnaire if ID is provided
  if (questionnaireIdFromUrl) {
    console.log('Questionnaire ID from URL parameter:', questionnaireIdFromUrl)
    
    // Wait a bit to ensure questionnaires are loaded
    setTimeout(async () => {
      // Find the questionnaire in the available questionnaires
      const targetQuestionnaire = availableQuestionnaires.value.find(questionnaire => 
        questionnaire.questionnaire_id.toString() === questionnaireIdFromUrl.toString()
      )
      
      if (targetQuestionnaire) {
        console.log('Found target questionnaire:', targetQuestionnaire)
        // Preselect the questionnaire
        await selectQuestionnaire(targetQuestionnaire)
      } else {
        console.warn('Questionnaire with ID', questionnaireIdFromUrl, 'not found in available questionnaires')
      }
    }, 500) // Small delay to ensure questionnaires are loaded
  }
})
</script>