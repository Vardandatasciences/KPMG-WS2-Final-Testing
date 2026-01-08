<template>
  <div v-if="!audit" class="flex items-center justify-center min-h-[400px] p-4">
    <Card class="w-full max-w-md text-center">
      <CardContent class="p-6">
        <AlertCircle class="w-12 h-12 mx-auto mb-4 text-muted-foreground" />
        <h3 class="text-lg font-medium mb-2">Audit Not Found</h3>
        <p class="text-muted-foreground mb-4">The requested audit could not be found.</p>
        <Button @click="navigateToMyAudits">
          Back to My Audits
        </Button>
      </CardContent>
    </Card>
  </div>

  <div v-else class="max-w-7xl mx-auto space-y-4 lg:space-y-6 p-4 lg:p-6">
    <!-- Header -->
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
      <div>
        <h1 class="text-2xl lg:text-3xl font-bold tracking-tight text-foreground">{{ audit.title }}</h1>
        <p class="text-sm lg:text-base text-muted-foreground">SLA: {{ sla?.sla_name || 'Unknown SLA' }} 
          <span v-if="isAssignedAuditor">(Auditor Access)</span>
          <span v-else>(View Only)</span>
        </p>
      </div>
      <div class="flex items-center gap-4">
        <!-- Access Badge -->
        <Badge v-if="isAssignedAuditor" variant="default" class="bg-blue-600 text-white">
          Auditor Access
        </Badge>
        <Badge v-else variant="outline" class="bg-yellow-100 text-yellow-800">
          View Only
        </Badge>
      <StatusBadge :status="audit.status" />
    </div>
    </div>


    <!-- Audit Info -->
    <Card class="shadow-card">
      <CardHeader>
        <CardTitle class="flex items-center">
          <FileText class="mr-2 h-5 w-5 text-primary" />
          Audit Information
        </CardTitle>
      </CardHeader>
      <CardContent class="p-4 lg:p-6">
        <div class="grid grid-cols-1 lg:grid-cols-3 gap-4 text-sm">
          <div>
            <span class="text-muted-foreground">Auditor:</span>
            <span class="ml-2 font-medium">{{ auditor?.name }}</span>
          </div>
          <div>
            <span class="text-muted-foreground">Reviewer:</span>
            <span class="ml-2 font-medium">{{ reviewer?.name }}</span>
          </div>
          <div>
            <span class="text-muted-foreground">Due Date:</span>
            <span class="ml-2 font-medium">{{ formatDate(audit.due_date) }}</span>
          </div>
        </div>
        
        <!-- Progress -->
        <div class="mt-4">
          <div class="flex items-center justify-between mb-2">
            <span class="text-sm font-medium">Completion Progress</span>
            <span class="text-sm text-muted-foreground">{{ Math.round(progress) }}%</span>
          </div>
          <div class="w-full bg-muted rounded-full h-2">
            <div 
              class="bg-primary h-2 rounded-full transition-all duration-300" 
              :style="{ width: `${progress}%` }"
            ></div>
          </div>
        </div>
      </CardContent>
    </Card>

    <!-- Rejection Feedback (Only show when audit is rejected) -->
    <Card v-if="audit.status === 'rejected' && rejectionFeedback" class="shadow-card border-red-200 bg-red-50">
      <CardHeader>
        <CardTitle class="flex items-center text-red-800">
          <X class="mr-2 h-5 w-5 text-red-600" />
          Reviewer Feedback - Audit Rejected
        </CardTitle>
        <CardDescription class="text-red-700">Please address the following feedback and resubmit your audit</CardDescription>
      </CardHeader>
      <CardContent class="p-4 lg:p-6">
        <div class="space-y-4">
          <!-- Rejection Comments -->
          <div v-if="rejectionFeedback.review_comments">
            <h4 class="font-medium text-red-800 mb-2 flex items-center">
              <MessageSquare class="mr-2 h-4 w-4" />
              Reviewer Comments
            </h4>
            <div class="bg-white p-4 rounded-lg border border-red-200">
              <p class="text-sm text-gray-800">{{ rejectionFeedback.review_comments }}</p>
            </div>
          </div>
          
          <!-- Required Changes -->
          <div v-if="rejectionFeedback.required_changes">
            <h4 class="font-medium text-red-800 mb-2 flex items-center">
              <AlertTriangle class="mr-2 h-4 w-4" />
              Required Changes
            </h4>
            <div class="bg-white p-4 rounded-lg border border-red-200">
              <p class="text-sm text-gray-800">{{ rejectionFeedback.required_changes }}</p>
            </div>
          </div>
          
          <!-- Rejection Date -->
          <div v-if="rejectionFeedback.rejection_date">
            <h4 class="font-medium text-red-800 mb-2 flex items-center">
              <Clock class="mr-2 h-4 w-4" />
              Rejected On
            </h4>
            <div class="bg-white p-4 rounded-lg border border-red-200">
              <p class="text-sm text-gray-800">{{ formatDate(rejectionFeedback.rejection_date) }}</p>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>

    

    <!-- Audit Workspace with Tabs -->
    <Card v-if="workspaceData.length > 0 && isAssignedAuditor" class="shadow-card">
      <CardHeader>
        <CardTitle class="flex items-center">
          <Target class="mr-2 h-5 w-5 text-primary" />
          Audit Questionnaires
        </CardTitle>
        <CardDescription>
          Complete questionnaires for each metric. Use tabs to navigate between different metrics.
        </CardDescription>
      </CardHeader>
      <CardContent class="p-4 lg:p-6">
        <div class="space-y-4 lg:space-y-6">
          <!-- Tab Navigation -->
          <div class="grid w-full grid-cols-1 lg:grid-cols-3 gap-2 bg-muted rounded-lg p-1">
            <button
              v-for="workspace in workspaceData"
              :key="workspace.metric_id"
              :class="[
                'px-3 py-2 text-sm font-medium rounded-md transition-colors flex items-center justify-between',
                activeTab === workspace.metric_id.toString()
                  ? 'bg-background text-foreground shadow-sm'
                  : 'text-muted-foreground hover:text-foreground'
              ]"
              @click="activeTab = workspace.metric_id.toString()"
            >
              <span>{{ workspace.metric_name }}</span>
              <Badge variant="outline" class="ml-2 text-xs">
                {{ getAnsweredCount(workspace) }}/{{ getRequiredCount(workspace) }}
              </Badge>
            </button>
          </div>

          <!-- Tab Content -->
          <div v-for="(workspace, workspaceIndex) in workspaceData" :key="workspace.metric_id">
            <div v-if="activeTab === workspace.metric_id.toString()" class="space-y-6">
              <!-- Questions -->
              <div>
                <h4 class="font-medium text-foreground mb-4 flex items-center">
                  <MessageSquare class="mr-2 h-4 w-4" />
                  Questionnaire for {{ workspace.metric_name }}
                </h4>
                <div class="space-y-4">
                  <div v-if="workspace.questions.length === 0" class="p-4 border border-border rounded-lg bg-muted/20 text-center text-muted-foreground">
                    No questions found for this metric. Please check the questionnaire configuration.
                  </div>
                  <div 
                    v-for="question in workspace.questions" 
                    :key="question.question_id" 
                    class="p-4 border border-border rounded-lg bg-muted/20"
                  >
                    <div class="flex items-start justify-between mb-3">
                      <Label class="text-sm font-medium leading-relaxed">
                        {{ question.question_text }}
                        <span v-if="question.is_required" class="text-destructive ml-1">*</span>
                      </Label>
                      <Badge variant="outline" class="text-xs">
                        Weight: {{ question.scoring_weightings || 0 }}%
                      </Badge>
                    </div>
                    <!-- Boolean Questions -->
                    <div v-if="question.question_type === 'boolean'">
                      <select 
                        :value="workspace.responses[question.question_id]"
                        @change="(event) => handleResponseChange(workspaceIndex, question.question_id, event.target.value)"
                        class="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                      >
                        <option value="">Select answer</option>
                        <option value="true">Yes</option>
                        <option value="false">No</option>
                      </select>
                    </div>
                    
                    <!-- Number Questions -->
                    <div v-else-if="question.question_type === 'number'">
                      <Input
                        type="number"
                        :value="workspace.responses[question.question_id]"
                        @input="(event) => handleResponseChange(workspaceIndex, question.question_id, event.target.value)"
                        placeholder="Enter a number..."
                        class="w-full"
                      />
                    </div>
                    
                    <!-- Multiple Choice Questions -->
                    <div v-else-if="question.question_type === 'multiple_choice'">
                      <select 
                        :value="workspace.responses[question.question_id]"
                        @change="(event) => handleResponseChange(workspaceIndex, question.question_id, event.target.value)"
                        class="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                      >
                        <option value="">Select an option</option>
                        <option value="yes">Yes</option>
                        <option value="no">No</option>
                        <option value="not_applicable">Not Applicable</option>
                      </select>
                    </div>
                    
                    <!-- Text Questions -->
                    <div v-else-if="question.question_type === 'text'">
                      <Textarea
                        :value="workspace.responses[question.question_id]"
                        @input="(event) => handleResponseChange(workspaceIndex, question.question_id, event.target.value)"
                        placeholder="Enter your answer..."
                        :rows="3"
                        class="w-full"
                      />
                    </div>
                    
                    <!-- Default Input for other types -->
                    <div v-else>
                      <Input
                      :value="workspace.responses[question.question_id]"
                        @input="(event) => handleResponseChange(workspaceIndex, question.question_id, event.target.value)"
                        placeholder="Enter your answer..."
                        class="w-full"
                    />
                    </div>
                  </div>
                </div>
              </div>

              <hr class="border-border" />

              <!-- Evidence -->
              <div>
                <h4 class="font-medium text-foreground mb-4 flex items-center">
                  <Upload class="mr-2 h-4 w-4" />
                  Evidence Collection
                </h4>
                <div class="space-y-4">
                  <div>
                    <Label :for="`evidence-${workspace.metric_id}`">Evidence Description *</Label>
                    <Textarea
                      :id="`evidence-${workspace.metric_id}`"
                      v-model="workspace.evidence"
                      placeholder="Describe the evidence supporting your findings..."
                      :rows="4"
                      class="mt-2"
                    />
                <div class="mt-3">
                  <div class="flex flex-col gap-1">
                    <div class="flex items-center justify-between">
                      <Label class="text-sm font-medium text-muted-foreground flex items-center gap-2">
                        <Paperclip class="w-4 h-4" />
                        Evidence Documents
                      </Label>
                      <span class="text-xs text-muted-foreground">
                        PDF, DOC, XLS, Images up to 15MB
                      </span>
                    </div>
                  </div>
                  <input
                    type="file"
                    class="hidden"
                    :id="`evidence-files-${workspace.metric_id}`"
                    multiple
                    accept=".pdf,.doc,.docx,.xls,.xlsx,.jpg,.jpeg,.png,.txt"
                    @change="(event) => handleEvidenceFileUpload(workspaceIndex, event)"
                  />
                  <label
                    :for="`evidence-files-${workspace.metric_id}`"
                    class="mt-2 inline-flex items-center gap-2 px-3 py-2 border border-dashed border-border rounded-md text-sm text-foreground hover:bg-muted/50 cursor-pointer transition-colors"
                  >
                    <Paperclip class="w-4 h-4" />
                    Upload Evidence
                  </label>
                  <div v-if="workspace.evidence_files?.length" class="mt-3 space-y-2">
                    <div
                      v-for="(file, fileIndex) in workspace.evidence_files"
                      :key="`evidence-file-${workspace.metric_id}-${file.documentId || file.name}-${fileIndex}`"
                      class="flex items-center justify-between p-3 bg-muted/30 border border-border rounded-lg"
                    >
                      <div>
                        <p class="text-sm font-medium text-foreground flex items-center gap-2">
                          <Paperclip class="w-4 h-4 text-primary" />
                          {{ file.name }}
                          <span v-if="file.uploading" class="text-xs text-muted-foreground flex items-center gap-1">
                            <Loader2 class="w-3 h-3 animate-spin" />
                            Uploading...
                          </span>
                        </p>
                        <p class="text-xs text-muted-foreground">
                          {{ formatFileSize(file.size) }}
                          <span v-if="file.uploadedAt">
                            • {{ formatDate(file.uploadedAt) }}
                          </span>
                        </p>
                      </div>
                      <div class="flex items-center gap-2">
                        <Button
                          variant="ghost"
                          size="icon"
                          class="text-primary"
                          :disabled="file.uploading"
                          @click.stop="openEvidenceDocument(file)"
                        >
                          <Download class="w-4 h-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon"
                          class="text-destructive"
                          :disabled="file.uploading"
                          @click.stop="removeEvidenceFile(workspaceIndex, fileIndex)"
                        >
                          <Trash2 class="w-4 h-4" />
                        </Button>
                      </div>
                    </div>
                  </div>
                </div>
                  </div>
                  <div>
                    <Label :for="`verification-${workspace.metric_id}`">How to Verify</Label>
                    <Textarea
                      :id="`verification-${workspace.metric_id}`"
                      v-model="workspace.verification_method"
                      placeholder="Explain how this evidence can be verified..."
                      :rows="3"
                      class="mt-2"
                    />
                  </div>
                </div>
              </div>

              <hr class="border-border" />

              <!-- Comments & Recommendations -->
              <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <Label :for="`comments-${workspace.metric_id}`">Comments</Label>
                  <Textarea
                    :id="`comments-${workspace.metric_id}`"
                    v-model="workspace.comments"
                    placeholder="Additional comments..."
                    :rows="3"
                    class="mt-2"
                  />
                </div>
                <div>
                  <Label :for="`recommendations-${workspace.metric_id}`">Recommendations</Label>
                  <Textarea
                    :id="`recommendations-${workspace.metric_id}`"
                    v-model="workspace.recommendations"
                    placeholder="Impact recommendations..."
                    :rows="3"
                    class="mt-2"
                  />
                </div>
              </div>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>

    <!-- Access Denied Message -->
    <Card v-if="!isAssignedAuditor" class="shadow-card border-red-200 bg-red-50">
      <CardContent class="p-6">
        <div class="text-center">
          <AlertCircle class="w-12 h-12 mx-auto mb-4 text-red-500" />
          <h3 class="text-lg font-medium mb-2 text-red-800">Access Denied</h3>
          <p class="text-muted-foreground mb-4">
            You are not the assigned auditor for this audit. Only the assigned auditor can perform audit actions.
          </p>
          <Button @click="navigateToMyAudits" variant="outline">
            Back to My Audits
          </Button>
        </div>
      </CardContent>
    </Card>

    <!-- Actions -->
    <div v-else class="flex flex-col sm:flex-row justify-between items-center gap-4">
      <Button variant="outline" @click="navigateToMyAudits" class="w-full sm:w-auto">
        Back to My Audits
      </Button>
      
      <div class="flex flex-col sm:flex-row gap-3 sm:gap-4 w-full sm:w-auto">
        <!-- Start Audit Action (when status is created) -->
        <template v-if="audit.status === 'created'">
          <Button
            @click="handleStartAudit"
            :disabled="isLoading"
            class="bg-gradient-to-r from-green-600 to-green-700 hover:shadow-hover transition-all w-full sm:w-auto"
          >
            <Play class="mr-2 h-4 w-4" />
            Start Audit
          </Button>
        </template>
        
        <!-- Auditor Actions - Can perform all operations -->
        <template v-else-if="audit.status === 'in_progress'">
          <Button
            variant="outline"
            @click="handleSaveProgress"
            :disabled="isLoading"
            class="w-full sm:w-auto"
          >
            <Save class="mr-2 h-4 w-4" />
            Save Progress
          </Button>
          <Button
            @click="handleSubmitForReview"
            :disabled="isLoading || progress < 80"
            class="bg-gradient-to-r from-primary to-primary-glow hover:shadow-hover transition-all w-full sm:w-auto"
          >
            <Send class="mr-2 h-4 w-4" />
            Submit for Review
          </Button>
        </template>
        
        <!-- Rejected Audit Actions -->
        <template v-else-if="audit.status === 'rejected'">
          <Button
            variant="outline"
            @click="handleSaveProgress"
            :disabled="isLoading"
            class="w-full sm:w-auto"
          >
            <Save class="mr-2 h-4 w-4" />
            Save Progress
          </Button>
          <Button
            @click="handleResubmitForReview"
            :disabled="isLoading || progress < 80"
            class="bg-gradient-to-r from-orange-600 to-orange-700 hover:shadow-hover transition-all w-full sm:w-auto"
          >
            <Send class="mr-2 h-4 w-4" />
            Resubmit for Review
          </Button>
        </template>
        
        <!-- Reviewer Actions (when status is under_review and user is reviewer) -->
        <template v-else-if="canReview">
          <div class="flex flex-col gap-3 w-full">
            <div class="w-full">
              <Label for="review-comments">Review Comments *</Label>
              <Textarea
                id="review-comments"
                v-model="reviewComments"
                placeholder="Provide your review comments and feedback..."
                :rows="4"
                class="mt-2 w-full"
              />
            </div>
            <div class="flex flex-col sm:flex-row gap-3">
              <Button 
                @click="handleApprove"
                :disabled="isLoading || !reviewComments.trim()"
                class="bg-gradient-to-r from-green-600 to-green-700 hover:shadow-hover transition-all w-full sm:w-auto"
              >
                <CheckCircle class="mr-2 h-4 w-4" />
                Approve Audit
              </Button>
              <Button 
                variant="destructive"
                @click="handleReject"
                :disabled="isLoading || !reviewComments.trim()"
                class="w-full sm:w-auto"
              >
                <X class="mr-2 h-4 w-4" />
                Reject & Request Changes
              </Button>
            </div>
          </div>
        </template>
        
        <!-- View Only Actions (when status is completed or other statuses) -->
        <template v-else>
          <Button
            variant="outline"
            @click="navigateToMyAudits"
            class="w-full sm:w-auto"
          >
            <Eye class="mr-2 h-4 w-4" />
            View Audit Details
          </Button>
        </template>
      </div>
    </div>

    <Card v-if="progress < 80" class="border-yellow-200 bg-yellow-50">
      <CardContent class="p-4">
        <div class="flex items-center">
          <AlertCircle class="w-5 h-5 text-yellow-600 mr-2" />
          <p class="text-sm text-yellow-800">
            Complete at least 80% of required questions to submit for review.
          </p>
        </div>
      </CardContent>
    </Card>
  </div>

  <!-- Popup Modal -->
  <PopupModal />
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useStore } from 'vuex'
import { 
  FileText, 
  Save, 
  Send, 
  Upload, 
  Target,
  MessageSquare,
  AlertCircle,
  CheckCircle,
  X,
  Eye,
  Clock,
  AlertTriangle,
  Play,
  Paperclip,
  Download,
  Loader2,
  Trash2
} from 'lucide-vue-next'
import apiService from '@/services/api.js'
import Card from '@/components/ui/card.vue'
import CardHeader from '@/components/ui/card-header.vue'
import CardTitle from '@/components/ui/card-title.vue'
import CardDescription from '@/components/ui/card-description.vue'
import CardContent from '@/components/ui/card-content.vue'
import Button from '@/components/ui/button.vue'
import Badge from '@/components/ui/badge.vue'
import Input from '@/components/ui/input.vue'
import Label from '@/components/ui/label.vue'
import Textarea from '@/components/ui/textarea.vue'
import Select from '@/components/ui/select.vue'
import StatusBadge from '@/components/StatusBadge.vue'
import PopupModal from '@/popup/PopupModal.vue'
import { PopupService } from '@/popup/popupService'
import { useNotifications } from '@/composables/useNotifications'
import loggingService from '@/services/loggingService'

const route = useRoute()
const router = useRouter()
const store = useStore()
const { showSuccess, showError, showWarning, showInfo } = useNotifications()

// Get current user from store
const currentUser = computed(() => store.state.auth.currentUser)

// Check if current user can perform audit actions
// User can perform actions if they are:
// 1. The assigned auditor (auditor_id)
// 2. The assignee (assignee_id)
// 3. The reviewer (reviewer_id)
// 4. OR have PerformContractAudit permission (in availableUsers list)
const isAssignedAuditor = computed(() => {
  if (!currentUser.value || !audit.value) {
    console.log('[Access Check] No currentUser or audit:', { hasUser: !!currentUser.value, hasAudit: !!audit.value })
    return false
  }
  
  // Check multiple possible user ID field names (handle different formats)
  const userId = currentUser.value.id || 
                 currentUser.value.user_id || 
                 currentUser.value.userid || 
                 currentUser.value.UserId ||  // Capital U, capital I
                 currentUser.value.userId ||  // camelCase
                 currentUser.value.USER_ID
  
  if (!userId) {
    console.log('[Access Check] No userId found in currentUser:', currentUser.value)
    console.log('[Access Check] Available keys:', Object.keys(currentUser.value || {}))
    return false
  }
  
  // Convert to numbers for comparison to handle string/int mismatches
  const currentUserId = Number(userId)
  const auditAuditorId = audit.value.auditor_id ? Number(audit.value.auditor_id) : null
  const auditAssigneeId = audit.value.assignee_id ? Number(audit.value.assignee_id) : null
  const auditReviewerId = audit.value.reviewer_id ? Number(audit.value.reviewer_id) : null
  
  // Check if user is assigned as auditor, assignee, or reviewer
  const isAuditor = auditAuditorId !== null && currentUserId === auditAuditorId
  const isAssignee = auditAssigneeId !== null && currentUserId === auditAssigneeId
  const isReviewer = auditReviewerId !== null && currentUserId === auditReviewerId
  
  // Check if user has PerformContractAudit permission (is in availableUsers list)
  const hasPermission = availableUsers.value.some(u => {
    const uId = u.user_id || u.userid || u.id
    return uId && (Number(uId) === currentUserId)
  })
  
  console.log('[Access Check]', {
    currentUserId,
    auditAuditorId,
    auditAssigneeId,
    auditReviewerId,
    isAuditor,
    isAssignee,
    isReviewer,
    hasPermission,
    availableUsersCount: availableUsers.value.length,
    result: isAuditor || isAssignee || isReviewer || hasPermission
  })
  
  // Allow access if user is any of these roles OR has PerformContractAudit permission
  return isAuditor || isAssignee || isReviewer || hasPermission
})

// Check if current user is the assigned reviewer
const isAssignedReviewer = computed(() => {
  if (!currentUser.value || !audit.value) {
    return false
  }
  
  // Check multiple possible user ID field names (handle different formats)
  const userId = currentUser.value.id || 
                 currentUser.value.user_id || 
                 currentUser.value.userid || 
                 currentUser.value.UserId ||  // Capital U, capital I
                 currentUser.value.userId ||  // camelCase
                 currentUser.value.USER_ID
  
  if (!userId) {
    return false
  }
  
  // Convert to numbers for comparison to handle string/int mismatches
  const currentUserId = Number(userId)
  const auditReviewerId = audit.value.reviewer_id ? Number(audit.value.reviewer_id) : null
  
  // Check if user is assigned as reviewer
  const isReviewer = auditReviewerId !== null && currentUserId === auditReviewerId
  
  console.log('[Reviewer Check]', {
    currentUserId,
    auditReviewerId,
    isReviewer
  })
  
  return isReviewer
})

// Check if user can review (is reviewer AND audit is under review)
const canReview = computed(() => {
  const canReviewResult = isAssignedReviewer.value && audit.value?.status === 'under_review'
  console.log('[Can Review Check]', {
    isAssignedReviewer: isAssignedReviewer.value,
    auditStatus: audit.value?.status,
    canReview: canReviewResult
  })
  return canReviewResult
})

const evidenceStorageKey = 'auditEvidenceDocuments'
const evidenceBroadcastEvent = 'audit-evidence-updated'
const allowedEvidenceMimeTypes = [
  'application/pdf',
  'application/msword',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
  'application/vnd.ms-excel',
  'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
  'image/png',
  'image/jpeg',
  'text/plain'
]
const maxEvidenceFileSize = 15 * 1024 * 1024 // 15 MB

const isLoading = ref(false)
const loading = ref(true)
const availableUsers = ref([]) // Users with PerformContractAudit permission
const activeTab = ref('')
const workspaceData = ref([])
const audit = ref(null)
const sla = ref(null)
const auditor = ref(null)
const reviewer = ref(null)
const metrics = ref([])
const questionnaires = ref([])
const rejectionFeedback = ref(null)
const reviewComments = ref('') // Review comments for approve/reject actions

const createEmptyExtendedInfo = () => ({
  responses: {},
  evidence: {},
  verification_methods: {},
  recommendations: {},
  comments: {},
  evidence_documents: {}
})

const normalizeEvidenceFileForStorage = (file = {}) => ({
  document_id: file.document_id ?? file.documentId ?? file.id ?? null,
  name: file.name,
  url: file.url || file.s3_url || file.document_url || null,
  size: file.size ?? file.file_size ?? null,
  type: file.type ?? file.mimeType ?? file.file_type ?? 'application/octet-stream',
  s3_key: file.s3_key ?? file.s3Key ?? file.stored_name ?? null,
  uploaded_at: file.uploaded_at ?? file.uploadedAt ?? file.created_at ?? new Date().toISOString()
})

const buildExtendedInformationPayload = () => {
  if (!workspaceData.value || workspaceData.value.length === 0) {
    return createEmptyExtendedInfo()
  }

  const payload = createEmptyExtendedInfo()

  payload.responses = workspaceData.value.reduce((acc, workspace) => {
    const responsesWithQuestions = {}
    workspace.questions.forEach(question => {
      if (workspace.responses[question.question_id] !== undefined) {
        responsesWithQuestions[question.question_text] = workspace.responses[question.question_id]
      }
    })
    acc[workspace.metric_name] = responsesWithQuestions
    return acc
  }, {})

  payload.evidence = workspaceData.value.reduce((acc, workspace) => {
    acc[workspace.metric_name] = workspace.evidence
    return acc
  }, {})

  payload.verification_methods = workspaceData.value.reduce((acc, workspace) => {
    acc[workspace.metric_name] = workspace.verification_method
    return acc
  }, {})

  payload.recommendations = workspaceData.value.reduce((acc, workspace) => {
    acc[workspace.metric_name] = workspace.recommendations
    return acc
  }, {})

  payload.comments = workspaceData.value.reduce((acc, workspace) => {
    acc[workspace.metric_name] = workspace.comments
    return acc
  }, {})

  payload.evidence_documents = workspaceData.value.reduce((acc, workspace) => {
    acc[workspace.metric_name] = (workspace.evidence_files || []).map(normalizeEvidenceFileForStorage)
    return acc
  }, {})

  return payload
}

const persistEvidenceState = () => {
  if (typeof window === 'undefined' || !audit.value?.audit_id) return

  const evidenceByMetric = workspaceData.value.reduce((acc, workspace) => {
    acc[workspace.metric_id] = (workspace.evidence_files || []).map(normalizeEvidenceFileForStorage)
    return acc
  }, {})

  const totalDocuments = Object.values(evidenceByMetric).reduce((sum, docs) => sum + docs.length, 0)
  const payload = {
    auditId: audit.value.audit_id,
    auditTitle: audit.value.title,
    metrics: evidenceByMetric,
    count: totalDocuments,
    updatedAt: new Date().toISOString()
  }

  let existing = {}
  try {
    existing = JSON.parse(localStorage.getItem(evidenceStorageKey)) || {}
  } catch {
    existing = {}
  }

  existing[audit.value.audit_id] = payload
  localStorage.setItem(evidenceStorageKey, JSON.stringify(existing))
  window.dispatchEvent(new CustomEvent(evidenceBroadcastEvent, { detail: { auditId: audit.value.audit_id } }))
}

// Check if user has access to perform audit actions
const canPerformAudit = computed(() => {
  return isAssignedAuditor.value && audit.value?.status !== 'completed'
})

// Parse extended information JSON for reviewer actions
const parsedExtendedInfo = computed(() => {
  try {
    return buildExtendedInformationPayload()
  } catch (error) {
    console.error('Error creating extended info:', error)
    return createEmptyExtendedInfo()
  }
})

// Load rejection feedback for rejected audits
const loadRejectionFeedback = async (auditId) => {
  try {
    const versionsData = await apiService.getAuditVersions(auditId)
    let versions
    if (Array.isArray(versionsData)) {
      versions = versionsData
    } else if (versionsData && versionsData.results && Array.isArray(versionsData.results)) {
      versions = versionsData.results
    } else {
      versions = []
    }
    
    // Find the latest rejection version (type 'R' with rejected status)
    const rejectionVersion = versions
      .filter(v => v.version_type === 'R' && v.approval_status === 'rejected')
      .sort((a, b) => b.version_number - a.version_number)[0]
    
    if (rejectionVersion && rejectionVersion.extended_information) {
      try {
        const feedback = typeof rejectionVersion.extended_information === 'string' 
          ? JSON.parse(rejectionVersion.extended_information)
          : rejectionVersion.extended_information
        
        rejectionFeedback.value = feedback
      } catch (error) {
        console.error('Error parsing rejection feedback:', error)
        rejectionFeedback.value = null
      }
    } else {
      rejectionFeedback.value = null
    }
  } catch (error) {
    console.error('Error loading rejection feedback:', error)
    rejectionFeedback.value = null
  }
}

// Load audit data from API
const loadAuditData = async () => {
  try {
    loading.value = true
    const auditId = route.params.auditId
    console.log('Loading audit data for ID:', auditId)
    
    // Load audit details
    const auditData = await apiService.getAudit(auditId)
    console.log('Audit data loaded:', auditData)
    audit.value = auditData
    
    // Load SLA details
    if (auditData.sla_id) {
      try {
        const slaData = await apiService.getAvailableSLAs()
        console.log('Available SLAs:', slaData)
        
        // Handle different response formats
        let slas = []
        if (Array.isArray(slaData)) {
          slas = slaData
        } else if (slaData && slaData.results && Array.isArray(slaData.results)) {
          slas = slaData.results
        }
        
        sla.value = slas.find(s => s.sla_id === auditData.sla_id) || null
        console.log('SLA loaded for audit:', sla.value)
      } catch (error) {
        console.error('Error loading SLA details:', error)
        sla.value = null
      }
    }
    
    // Load users (auditor/reviewer) - these are users with PerformContractAudit permission
    const usersResponse = await apiService.getAvailableUsers()
    
    // Handle different response formats
    let usersData = []
    if (usersResponse && usersResponse.success && Array.isArray(usersResponse.data)) {
      usersData = usersResponse.data
    } else if (usersResponse && Array.isArray(usersResponse)) {
      usersData = usersResponse
    } else if (usersResponse && usersResponse.data && Array.isArray(usersResponse.data)) {
      usersData = usersResponse.data
    } else {
      console.error('Error loading users:', usersResponse?.error || usersResponse?.message || 'Unknown error')
      usersData = []
    }
    
    // Store available users for permission checking (these users have PerformContractAudit permission)
    availableUsers.value = usersData
    
    // Find auditor and reviewer by matching user IDs
    auditor.value = usersData.find(u => {
      const userId = u.user_id || u.userid || u.id
      return userId == auditData.auditor_id || userId === auditData.auditor_id
    }) || null
    reviewer.value = usersData.find(u => {
      const userId = u.user_id || u.userid || u.id
      return userId == auditData.reviewer_id || userId === auditData.reviewer_id
    }) || null
    console.log('Users loaded:', { auditor: auditor.value, reviewer: reviewer.value })
    
    // Load SLA metrics
    if (auditData.sla_id && auditData.sla_id !== null) {
      console.log('Loading metrics for SLA ID:', auditData.sla_id)
      try {
        const metricsData = await apiService.getSLAMetrics(auditData.sla_id)
        console.log('Raw metrics data:', metricsData)
        
        // Handle different response formats
        if (metricsData && metricsData.metrics && Array.isArray(metricsData.metrics)) {
          metrics.value = metricsData.metrics
        } else if (Array.isArray(metricsData)) {
          metrics.value = metricsData
        } else if (metricsData && metricsData.results && Array.isArray(metricsData.results)) {
          metrics.value = metricsData.results
        } else {
          metrics.value = []
          console.warn('No metrics found in response:', metricsData)
        }
        
        console.log('Metrics loaded:', metrics.value.length, 'metrics')
        console.log('Metrics details:', metrics.value)
      } catch (error) {
        console.error('Error loading SLA metrics:', error)
        metrics.value = []
      }
    } else {
      console.warn('No valid SLA ID found in audit data:', auditData)
      metrics.value = []
    }
    
    // Load static questionnaires for the metrics - FETCH ALL PAGES
    const questionnairesData = await apiService.getStaticQuestionnaires()
    console.log('Questionnaires raw data:', questionnairesData)
    
    // Ensure questionnaires is an array and handle pagination
    let allQuestionnaires = []
    if (Array.isArray(questionnairesData)) {
      allQuestionnaires = questionnairesData
    } else if (questionnairesData && questionnairesData.results && Array.isArray(questionnairesData.results)) {
      // Handle paginated response - fetch all pages
      allQuestionnaires = [...questionnairesData.results]
      
      // Check if there are more pages
      let nextPage = questionnairesData.next
      let pageCount = 1
      
      while (nextPage) {
        console.log(`Fetching questionnaires page ${pageCount + 1}...`)
        try {
          // Extract page number from next URL
          const response = await fetch(nextPage, {
            headers: {
              'Authorization': `Bearer ${localStorage.getItem('access_token')}`
            }
          })
          const nextPageData = await response.json()
          
          if (nextPageData.results && Array.isArray(nextPageData.results)) {
            allQuestionnaires = [...allQuestionnaires, ...nextPageData.results]
            console.log(`Loaded ${nextPageData.results.length} more questionnaires (total: ${allQuestionnaires.length})`)
          }
          
          nextPage = nextPageData.next
          pageCount++
        } catch (error) {
          console.error('Error fetching next page of questionnaires:', error)
          break
        }
      }
      
      console.log(`Total questionnaires loaded: ${allQuestionnaires.length} across ${pageCount} pages`)
    } else {
      allQuestionnaires = []
    }
    
    // Filter questionnaires to only include those for SLA metrics
    if (metrics.value && metrics.value.length > 0) {
      const slaMetricNames = metrics.value.map(m => m.metric_name)
      console.log('SLA metric names:', slaMetricNames)
      
      questionnaires.value = allQuestionnaires.filter(q => 
        slaMetricNames.includes(q.metric_name)
      )
      console.log('Filtered questionnaires for SLA metrics:', questionnaires.value.length, 'questions')
    } else {
      // If no SLA metrics found, use all questionnaires as fallback
      questionnaires.value = allQuestionnaires
      console.log('No SLA metrics found, using all questionnaires:', questionnaires.value.length, 'questions')
    }
    
    // Load rejection feedback if audit is rejected
    if (auditData.status === 'rejected') {
      await loadRejectionFeedback(auditId)
    }
    
  } catch (error) {
    console.error('Error loading audit data:', error)
    
    // Show error notification
    await showError('Audit Loading Failed', 'Failed to load audit data. Please try refreshing the page.', {
      audit_id: route.params.auditId,
      action: 'audit_loading_failed',
      error_message: error.message
    })
    
    audit.value = null
  } finally {
    loading.value = false
  }
}

// Calculate progress
const progress = computed(() => {
  const totalQuestions = workspaceData.value.reduce((total, workspace) => 
    total + workspace.questions.filter(q => q.is_required).length, 0)
  const answeredQuestions = workspaceData.value.reduce((total, workspace) => 
    total + workspace.questions.filter(q => 
      q.is_required && workspace.responses[q.question_id] !== undefined
    ).length, 0)
  return totalQuestions > 0 ? (answeredQuestions / totalQuestions) * 100 : 0
})

onMounted(async () => {
  await loggingService.logPageView('Audit', 'Audit Execution')
  await loadAuditData()
})

// Initialize workspace data when audit data is loaded
watch([audit, metrics, questionnaires], async ([newAudit, newMetrics, newQuestionnaires]) => {
  console.log('Watch triggered:', { 
    hasAudit: !!newAudit, 
    metricsCount: newMetrics?.length || 0, 
    questionnairesCount: newQuestionnaires?.length || 0 
  })
  
  if (newAudit && newQuestionnaires && Array.isArray(newQuestionnaires) && newQuestionnaires.length > 0) {
    console.log('Initializing workspace data...')
    
    let workspaces = []
    
    // If we have metrics, use them
    if (newMetrics && newMetrics.length > 0) {
      console.log('Using metrics to create workspaces')
      console.log('Available metric names from SLA:', newMetrics.map(m => m.metric_name))
      console.log('Available metric names from questionnaires:', [...new Set(newQuestionnaires.map(q => q.metric_name))])
      
      workspaces = newMetrics.map((metric) => {
        // Find questions for this metric from static_questionnaires
        const questions = newQuestionnaires.filter(q => q.metric_name === metric.metric_name)
        console.log(`Metric "${metric.metric_name}" has ${questions.length} questions`)
        console.log('Matching questions:', questions.map(q => ({ id: q.question_id, text: q.question_text, metric: q.metric_name })))
        
        return {
          metric_id: metric.metric_id,
          metric_name: metric.metric_name,
          finding_id: 0, // Would be created on first save
          questions,
          responses: {},
          evidence: '',
          comments: '',
          verification_method: '',
          recommendations: '',
          evidence_files: []
        }
      })
    } else {
      // Fallback: Create workspaces from questionnaire data, but only for SLA metrics if available
      console.log('No metrics found, creating workspaces from questionnaire data')
      let uniqueMetrics = [...new Set(newQuestionnaires.map(q => q.metric_name))]
      
      // If we have SLA metrics, filter to only include those
      if (newMetrics && newMetrics.length > 0) {
        const slaMetricNames = newMetrics.map(m => m.metric_name)
        uniqueMetrics = uniqueMetrics.filter(metricName => slaMetricNames.includes(metricName))
        console.log('Filtered unique metrics to SLA metrics only:', uniqueMetrics)
      }
      
      console.log('Unique metrics from questions:', uniqueMetrics)
      
      workspaces = uniqueMetrics.map((metricName, index) => {
        const questions = newQuestionnaires.filter(q => q.metric_name === metricName)
        console.log(`Creating workspace for metric ${metricName} with ${questions.length} questions`)
        
        return {
          metric_id: index + 1, // Generate a temporary ID
          metric_name: metricName,
          finding_id: 0,
          questions,
          responses: {},
          evidence: '',
          comments: '',
          verification_method: '',
          recommendations: '',
          evidence_files: []
        }
      })
    }
    
    console.log('Created workspaces:', workspaces.length)
    
    // Load existing audit version data if available
    try {
      const auditId = route.params.auditId
      const versionsData = await apiService.getAuditVersions(auditId)
      
      // Handle both array and paginated response formats
      let versions
      if (Array.isArray(versionsData)) {
        versions = versionsData
      } else if (versionsData && versionsData.results && Array.isArray(versionsData.results)) {
        versions = versionsData.results
      } else {
        versions = []
      }
      
      console.log('Found versions:', versions.length)
      
      // Find the latest audit version (type 'A') - try different approaches
      let latestVersion = versions
        .filter(v => v.version_type === 'A' && v.is_active === 1)
        .sort((a, b) => b.version_number - a.version_number)[0]
      
      // If no active version found, try to find any version with type 'A'
      if (!latestVersion) {
        latestVersion = versions
          .filter(v => v.version_type === 'A')
          .sort((a, b) => b.version_number - a.version_number)[0]
      }
      
      // If still no version found, try to find any version
      if (!latestVersion && versions.length > 0) {
        latestVersion = versions
          .sort((a, b) => b.version_number - a.version_number)[0]
      }
      
      if (latestVersion && latestVersion.extended_information) {
        console.log('Loading existing version data...')
        let extendedInfo
        try {
          extendedInfo = typeof latestVersion.extended_information === 'string' 
            ? JSON.parse(latestVersion.extended_information)
            : latestVersion.extended_information
        } catch (error) {
          console.error('Error parsing extended_information:', error)
          extendedInfo = null
        }
        
        if (extendedInfo) {
          // Populate workspace data with existing responses
          workspaces.forEach(workspace => {
            const metricName = workspace.metric_name
            
            // Load responses - handle both question ID and question text formats
            if (extendedInfo.responses && extendedInfo.responses[metricName]) {
              const metricResponses = extendedInfo.responses[metricName]
              
              // Check if responses use question text (new format) or question IDs (old format)
              const firstKey = Object.keys(metricResponses)[0]
              const usesQuestionText = workspace.questions.some(q => q.question_text === firstKey)
              
              if (usesQuestionText) {
                // New format: question text as keys
                workspace.responses = {}
                workspace.questions.forEach(question => {
                  if (metricResponses[question.question_text] !== undefined) {
                    workspace.responses[question.question_id] = metricResponses[question.question_text]
                  }
                })
              } else {
                // Old format: question IDs as keys (backward compatibility)
                workspace.responses = metricResponses
              }
            }
            
            // Load evidence
            if (extendedInfo.evidence && extendedInfo.evidence[metricName]) {
              workspace.evidence = extendedInfo.evidence[metricName]
            }
            
            // Load verification method
            if (extendedInfo.verification_methods && extendedInfo.verification_methods[metricName]) {
              workspace.verification_method = extendedInfo.verification_methods[metricName]
            }
            
            // Load comments
            if (extendedInfo.comments && extendedInfo.comments[metricName]) {
              workspace.comments = extendedInfo.comments[metricName]
            }
            
            // Load recommendations
            if (extendedInfo.recommendations && extendedInfo.recommendations[metricName]) {
              workspace.recommendations = extendedInfo.recommendations[metricName]
            }

            if (extendedInfo.evidence_documents && extendedInfo.evidence_documents[metricName]) {
              workspace.evidence_files = extendedInfo.evidence_documents[metricName].map(doc => ({
                name: doc.name || doc.file_name || 'Evidence Document',
                size: doc.size || doc.file_size || null,
                type: doc.type || doc.file_type || 'application/octet-stream',
                documentId: doc.document_id || doc.id || doc.s3_file_id || null,
                url: doc.url || doc.s3_url || null,
                s3_key: doc.s3_key || doc.stored_name || null,
                uploadedAt: doc.uploaded_at || doc.created_at || null,
                uploading: false
              }))
            } else if (!workspace.evidence_files) {
              workspace.evidence_files = []
            }
          })
        }
      } else {
        console.log('No existing version data found, starting fresh')
      }
    } catch (error) {
      console.error('Error loading audit version data:', error)
    }
    
    workspaceData.value = workspaces
    console.log('Workspace data set:', workspaceData.value.length, 'workspaces')
    
    // Set first tab as active
    if (workspaces.length > 0) {
      activeTab.value = workspaces[0].metric_id.toString()
      console.log('Active tab set to:', activeTab.value)
    }

    persistEvidenceState()
  } else {
    console.log('Missing required data for workspace initialization:', {
      hasAudit: !!newAudit,
      hasMetrics: !!newMetrics,
      metricsLength: newMetrics?.length || 0,
      hasQuestionnaires: !!newQuestionnaires,
      questionnairesLength: newQuestionnaires?.length || 0
    })
  }
}, { immediate: true })

const handleResponseChange = (workspaceIndex, questionId, value) => {
  workspaceData.value[workspaceIndex].responses[questionId] = value
}

const getAnsweredCount = (workspace) => {
  return workspace.questions.filter(q => workspace.responses[q.question_id]).length
}

const getRequiredCount = (workspace) => {
  return workspace.questions.filter(q => q.is_required).length
}

// Question component handling is now done directly in the template

const handleSaveProgress = async () => {
  isLoading.value = true
  try {
    // Save audit progress locally (could be enhanced to save to backend)
    const auditId = route.params.auditId
    
    // Create a draft version of the audit
    const versionData = {
      audit_id: parseInt(auditId),
      version_type: 'A', // Audit version
      version_number: 0, // Draft version
      extended_information: JSON.stringify(buildExtendedInformationPayload()),
      user_id: 2, // Current user ID
      approval_status: 'pending',
      date_created: new Date().toISOString().split('T')[0],
      is_active: 0 // Draft version is not active
    }
    
    // For now, just save locally (could be enhanced to save to backend)
    console.log('Saving draft version:', versionData)
    
    // Show success notification
    await showSuccess('Progress Saved', 'Your audit progress has been saved successfully.', {
      audit_id: route.params.auditId,
      audit_title: audit.value?.title,
      action: 'progress_saved'
    })
    
    PopupService.success('Your audit progress has been saved successfully.', 'Progress Saved')
  } catch (error) {
    console.error('Error saving progress:', error)
    
    // Show error notification
    await showError('Save Failed', 'Failed to save progress. Please try again.', {
      audit_id: route.params.auditId,
      audit_title: audit.value?.title,
      action: 'progress_save_failed',
      error_message: error.message
    })
    
    PopupService.error('Failed to save progress. Please try again.', 'Save Failed')
  } finally {
    isLoading.value = false
  }
}

const handleSubmitForReview = async () => {
  // Validate completion
  const missingRequired = workspaceData.value.some(workspace => 
    workspace.questions.some(q => 
      q.is_required && !workspace.responses[q.question_id]
    ) || !workspace.evidence.trim()
  )

  if (missingRequired) {
    await showWarning('Missing Required Fields', 'Please complete all required questions and provide evidence before submitting.', {
      audit_id: route.params.auditId,
      audit_title: audit.value?.title,
      action: 'validation_failed',
      missing_fields: 'required questions and evidence'
    })
    PopupService.warning('Please complete all required questions and provide evidence before submitting.', 'Missing Required Fields')
    return
  }

  isLoading.value = true
  try {
    const auditId = route.params.auditId
    
    // Get current version number for audit versions
    const versionsData = await apiService.getAuditVersions(auditId)
    let versions
    if (Array.isArray(versionsData)) {
      versions = versionsData
    } else if (versionsData && versionsData.results && Array.isArray(versionsData.results)) {
      versions = versionsData.results
    } else {
      versions = []
    }
    const currentVersion = versions.length > 0 ? Math.max(...versions.map(v => v.version_number)) : 0
    const nextVersion = currentVersion + 1
    
    console.log('Submitting audit for review:', {
      auditId,
      currentVersion,
      nextVersion,
      workspaceCount: workspaceData.value.length
    })
    
    // STEP 1: Create audit version (A = Audit submission)
    const versionData = {
      audit_id: parseInt(auditId),
      version_type: 'A', // A = Audit submission from auditor
      version_number: nextVersion,
      extended_information: JSON.stringify(buildExtendedInformationPayload()),
      user_id: 2, // Current user ID (auditor)
      approval_status: 'pending', // Initially pending review
      date_created: new Date().toISOString().split('T')[0],
      is_active: 1
    }
    
    console.log('Creating audit version:', versionData)
    const auditVersion = await apiService.createAuditVersion(versionData)
    console.log('Audit version created:', auditVersion)
    
    // STEP 2: Update audit status to under_review
    await apiService.updateAudit(auditId, { status: 'under_review' })
    console.log('Audit status updated to under_review')
    
    // STEP 3: Note: audit_findings will be created AFTER reviewer approval
    // This happens in the review process, not during initial submission
    
    // Show success notification
    await showSuccess('Audit Submitted', `Audit version v${nextVersion} has been submitted to ${reviewer.value?.name} for review.`, {
      audit_id: route.params.auditId,
      audit_title: audit.value?.title,
      version_number: nextVersion,
      reviewer_name: reviewer.value?.name,
      action: 'audit_submitted'
    })
    
    PopupService.success(`Audit version v${nextVersion} has been submitted to ${reviewer.value?.name} for review.`, 'Submitted for Review')
    PopupService.onAction('ok', () => {
      router.push('/audit/my-audits')
    })
  } catch (error) {
    console.error('Error submitting audit:', error)
    
    // Show error notification
    await showError('Submission Failed', 'Failed to submit audit. Please try again.', {
      audit_id: route.params.auditId,
      audit_title: audit.value?.title,
      action: 'audit_submission_failed',
      error_message: error.message
    })
    
    PopupService.error('Failed to submit audit. Please try again.', 'Submission Failed')
  } finally {
    isLoading.value = false
  }
}

const handleResubmitForReview = async () => {
  // Validate completion
  const missingRequired = workspaceData.value.some(workspace => 
    workspace.questions.some(q => 
      q.is_required && !workspace.responses[q.question_id]
    ) || !workspace.evidence.trim()
  )

  if (missingRequired) {
    PopupService.warning('Please complete all required questions and provide evidence before resubmitting.', 'Missing Required Fields')
    return
  }

  // Confirm resubmission
  PopupService.confirm(
    'Are you sure you want to resubmit this audit for review? This will create a new version.',
    'Confirm Resubmission',
    async () => {
      await performResubmission()
    }
  )
}

const performResubmission = async () => {

  isLoading.value = true
  try {
    const auditId = route.params.auditId
    
    // Get current version number for audit versions
    const versionsData = await apiService.getAuditVersions(auditId)
    let versions
    if (Array.isArray(versionsData)) {
      versions = versionsData
    } else if (versionsData && versionsData.results && Array.isArray(versionsData.results)) {
      versions = versionsData.results
    } else {
      versions = []
    }
    
    // Get the latest audit version number (type 'A')
    const auditVersions = versions.filter(v => v.version_type === 'A')
    const currentVersion = auditVersions.length > 0 ? Math.max(...auditVersions.map(v => v.version_number)) : 0
    const nextVersion = currentVersion + 1
    
    console.log('Resubmitting audit for review:', {
      auditId,
      currentVersion,
      nextVersion,
      workspaceCount: workspaceData.value.length
    })
    
    // STEP 1: Create new audit version (A = Audit submission)
    const versionData = {
      audit_id: parseInt(auditId),
      version_type: 'A', // A = Audit submission from auditor
      version_number: nextVersion,
      extended_information: JSON.stringify({
        ...buildExtendedInformationPayload(),
        resubmission_notes: 'Resubmitted after addressing reviewer feedback',
        previous_rejection_version: currentVersion
      }),
      user_id: 2, // Current user ID (auditor)
      approval_status: 'pending', // Initially pending review
      date_created: new Date().toISOString().split('T')[0],
      is_active: 1
    }
    
    console.log('Creating resubmission audit version:', versionData)
    const auditVersion = await apiService.createAuditVersion(versionData)
    console.log('Resubmission audit version created:', auditVersion)
    
    // STEP 2: Update audit status to under_review
    await apiService.updateAudit(auditId, { 
      status: 'under_review',
      review_status: 'pending', // Reset to pending instead of null to satisfy validation
      review_comments: '' // Clear previous comments with empty string
    })
    console.log('Audit status updated to under_review for resubmission')
    
    PopupService.success(`Audit has been resubmitted as version v${nextVersion} to ${reviewer.value?.name} for review.`, 'Resubmitted Successfully')
    PopupService.onAction('ok', () => {
      router.push('/audit/my-audits')
    })
  } catch (error) {
    console.error('Error resubmitting audit:', error)
    PopupService.error('Failed to resubmit audit. Please try again.', 'Resubmission Failed')
  } finally {
    isLoading.value = false
  }
}

const formatDate = (dateString) => {
  return new Date(dateString).toLocaleDateString()
}

const navigateToMyAudits = () => router.push('/audit/my-audits')

// Manual workspace initialization
const manualInitializeWorkspace = () => {
  console.log('Manually initializing workspace...')
  
  if (!questionnaires.value || questionnaires.value.length === 0) {
    PopupService.error('No questionnaires available. Please check the data loading.', 'No Data Available')
    return
  }
  
  // Create workspaces from questionnaire data, but only for SLA metrics
  let uniqueMetrics = [...new Set(questionnaires.value.map(q => q.metric_name))]
  
  // If we have SLA metrics, filter to only include those
  if (metrics.value && metrics.value.length > 0) {
    const slaMetricNames = metrics.value.map(m => m.metric_name)
    uniqueMetrics = uniqueMetrics.filter(metricName => slaMetricNames.includes(metricName))
    console.log('Filtered unique metrics to SLA metrics only:', uniqueMetrics)
  }
  
  console.log('Unique metrics from questions:', uniqueMetrics)
  
  const workspaces = uniqueMetrics.map((metricName, index) => {
    const questions = questionnaires.value.filter(q => q.metric_name === metricName)
    console.log(`Creating workspace for metric ${metricName} with ${questions.length} questions`)
    
    return {
      metric_id: index + 1, // Generate a temporary ID
      metric_name: metricName,
      finding_id: 0,
      questions,
      responses: {},
      evidence: '',
      comments: '',
      verification_method: '',
      recommendations: '',
      evidence_files: []
    }
  })
  
  workspaceData.value = workspaces
  console.log('Manually created workspaces:', workspaceData.value.length)
  
  // Set first tab as active
  if (workspaces.length > 0) {
    activeTab.value = workspaces[0].metric_id.toString()
    console.log('Active tab set to:', activeTab.value)
  }
  
  persistEvidenceState()
  PopupService.success(`Workspace initialized with ${workspaces.length} metrics!`, 'Workspace Initialized')
}

const validateEvidenceFile = (file) => {
  if (!file) return 'File not found.'
  if (file.size > maxEvidenceFileSize) {
    return `File exceeds the ${Math.round(maxEvidenceFileSize / (1024 * 1024))}MB limit.`
  }
  if (file.type && !allowedEvidenceMimeTypes.includes(file.type)) {
    return 'Unsupported file type. Please upload PDF, DOC, XLS, image, or text files.'
  }
  return null
}

const formatFileSize = (size) => {
  if (!size && size !== 0) return 'N/A'
  if (size < 1024) return `${size} B`
  if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`
  return `${(size / (1024 * 1024)).toFixed(1)} MB`
}

const handleEvidenceFileUpload = async (workspaceIndex, event) => {
  const files = Array.from(event.target?.files || [])
  if (!files.length || !workspaceData.value[workspaceIndex]) return

  for (const file of files) {
    const validationError = validateEvidenceFile(file)
    if (validationError) {
      await showWarning('Invalid File', validationError, {
        action: 'evidence_upload_validation_failed',
        file_name: file.name
      })
      continue
    }

    const placeholderEntry = {
      name: file.name,
      size: file.size,
      type: file.type,
      uploading: true,
      documentId: `temp-${Date.now()}-${Math.random()}`
    }

    if (!workspaceData.value[workspaceIndex].evidence_files) {
      workspaceData.value[workspaceIndex].evidence_files = []
    }
    workspaceData.value[workspaceIndex].evidence_files.push(placeholderEntry)

    try {
      const uploadResult = await apiService.uploadAuditEvidenceDocument(file, {
        auditId: audit.value?.audit_id,
        metricId: workspaceData.value[workspaceIndex].metric_id,
        metricName: workspaceData.value[workspaceIndex].metric_name,
        userId: audit.value?.auditor_id || 1,
        customFileName: `${audit.value?.title || 'audit'}-${workspaceData.value[workspaceIndex].metric_name}-${file.name}`
      })

      Object.assign(placeholderEntry, {
        uploading: false,
        documentId: uploadResult.document_id || uploadResult.id || placeholderEntry.documentId,
        url: uploadResult.s3_url || uploadResult.url || uploadResult.document_url || null,
        s3_key: uploadResult.s3_key || uploadResult.stored_name || null,
        uploadedAt: uploadResult.uploaded_at || new Date().toISOString()
      })
    } catch (error) {
      console.error('Error uploading evidence document:', error)
      workspaceData.value[workspaceIndex].evidence_files = workspaceData.value[workspaceIndex].evidence_files.filter(entry => entry !== placeholderEntry)
      await showError('Upload Failed', `Failed to upload ${file.name}. Please try again.`, {
        action: 'evidence_upload_failed',
        error_message: error.message,
        audit_id: audit.value?.audit_id
      })
    }
  }

  if (event.target) {
    event.target.value = ''
  }

  persistEvidenceState()
}

const removeEvidenceFile = (workspaceIndex, fileIndex) => {
  if (!workspaceData.value[workspaceIndex]?.evidence_files) return
  workspaceData.value[workspaceIndex].evidence_files.splice(fileIndex, 1)
  persistEvidenceState()
}

const openEvidenceDocument = async (file) => {
  if (typeof window === 'undefined') return
  try {
    if (file.url) {
      window.open(file.url, '_blank', 'noopener')
      return
    }

    if (file.documentId) {
      const response = await apiService.getS3File(file.documentId)
      const downloadUrl = response?.s3_file?.url || response?.file_operation?.s3_url || response?.url
      if (downloadUrl) {
        window.open(downloadUrl, '_blank', 'noopener')
        return
      }
    }

    throw new Error('No download URL available')
  } catch (error) {
    console.error('Unable to open evidence document:', error)
    await showError('Download Failed', 'Unable to download the evidence document. Please try again later.', {
      action: 'evidence_download_failed',
      error_message: error.message
    })
  }
}

// Start audit function
const handleStartAudit = async () => {
  PopupService.confirm(
    'Are you sure you want to start this audit? This will change the status to "In Progress".',
    'Start Audit',
    async () => {
      await performStartAudit()
    }
  )
}

const performStartAudit = async () => {
  
  isLoading.value = true
  try {
    const auditId = route.params.auditId
    
    // Update audit status to in_progress
    await apiService.updateAudit(auditId, { status: 'in_progress' })
    console.log('Audit status updated to in_progress')
    
    // Update local audit object
    audit.value.status = 'in_progress'
    
    // Show success notification
    await showSuccess('Audit Started', 'Audit has been started successfully! You can now begin filling out the questionnaire.', {
      audit_id: route.params.auditId,
      audit_title: audit.value?.title,
      action: 'audit_started'
    })
    
    PopupService.success('Audit has been started successfully! You can now begin filling out the questionnaire.', 'Audit Started')
    
    // Reload the page to refresh the data
    setTimeout(() => {
      window.location.reload()
    }, 1000)
    
  } catch (error) {
    console.error('Error starting audit:', error)
    
    // Show error notification
    await showError('Start Failed', 'Failed to start audit. Please try again.', {
      audit_id: route.params.auditId,
      audit_title: audit.value?.title,
      action: 'audit_start_failed',
      error_message: error.message
    })
    
    PopupService.error('Failed to start audit. Please try again.', 'Start Failed')
  } finally {
    isLoading.value = false
  }
}

// Reviewer functions
const handleApprove = async () => {
  if (!reviewComments.value.trim()) {
    await showWarning('Missing Comments', 'Please provide review comments before approving.', {
      audit_id: route.params.auditId,
      audit_title: audit.value?.title,
      action: 'missing_review_comments'
    })
    PopupService.warning('Please provide review comments before approving.', 'Missing Comments')
    return
  }
  
  PopupService.confirm(
    'Are you sure you want to approve this audit?',
    'Approve Audit',
    async () => {
      await performApprove()
    }
  )
}

const performApprove = async () => {
  isLoading.value = true
  try {
    const auditId = route.params.auditId
    
    // Get current version
    const versionsData = await apiService.getAuditVersions(auditId)
    let versions
    if (Array.isArray(versionsData)) {
      versions = versionsData
    } else if (versionsData && versionsData.results && Array.isArray(versionsData.results)) {
      versions = versionsData.results
    } else {
      versions = []
    }
    
    // Find the latest audit version (type 'A') - try different approaches
    let currentVersion = versions.find(v => v.version_type === 'A' && v.approval_status === 'pending')
    
    // If no pending version found, try to find any audit version
    if (!currentVersion) {
      currentVersion = versions
        .filter(v => v.version_type === 'A')
        .sort((a, b) => b.version_number - a.version_number)[0]
    }
    
    // If still no version found, try to find any version
    if (!currentVersion && versions.length > 0) {
      currentVersion = versions
        .sort((a, b) => b.version_number - a.version_number)[0]
    }
    
    if (!currentVersion) {
      PopupService.error('No audit version found. Please ensure the audit has been submitted for review.', 'No Version Found')
      isLoading.value = false
      return
    }
    
    // Update version to approved
    console.log('Updating audit version:', currentVersion.version_id, 'with data:', { approval_status: 'approved' })
    await apiService.updateAuditVersion(currentVersion.version_id, {
      approval_status: 'approved'
    })
    
    // Create review version
    const reviewVersions = versions.filter(v => v.version_type === 'R')
    const nextReviewVersion = reviewVersions.length + 1
    
    await apiService.createAuditVersion({
      audit_id: parseInt(auditId),
      version_type: 'R',
      version_number: nextReviewVersion,
      extended_information: JSON.stringify({
        approved_version: currentVersion.version_number,
        review_comments: reviewComments.value,
        approval_date: new Date().toISOString()
      }),
      user_id: currentUser.value?.UserId || currentUser.value?.user_id || currentUser.value?.id || 1, // Current reviewer user ID
      approval_status: 'approved',
      date_created: new Date().toISOString().split('T')[0],
      is_active: 1
    })
    
    // STEP 4: Create audit findings for each metric (after approval)
    const extendedInfo = parsedExtendedInfo.value
    const findings = []
    
    if (extendedInfo && extendedInfo.responses) {
      // Get metrics for this audit - handle null SLA ID
      if (audit.value.sla_id && audit.value.sla_id !== null) {
        try {
          const slaMetrics = await apiService.getSLAMetrics(audit.value.sla_id)
          
          // Create audit findings for each metric
          for (const metric of slaMetrics.metrics || []) {
            // Convert responses to use question text instead of IDs for audit findings
            const responsesForFinding = {}
            if (extendedInfo.responses?.[metric.metric_name]) {
              responsesForFinding[metric.metric_name] = extendedInfo.responses[metric.metric_name]
            }
            
            const findingData = {
              audit_id: parseInt(auditId),
              metrics_id: metric.metric_id,
              evidence: extendedInfo.evidence?.[metric.metric_name] || '',
              user_id: currentUser.value?.UserId || currentUser.value?.user_id || currentUser.value?.id || 1, // Current reviewer user ID
              how_to_verify: extendedInfo.verification_methods?.[metric.metric_name] || '',
              impact_recommendations: extendedInfo.recommendations?.[metric.metric_name] || '',
              details_of_finding: extendedInfo.comments?.[metric.metric_name] || '',
              comment: reviewComments.value, // Reviewer's approval comment
              check_date: new Date().toISOString().split('T')[0],
              questionnaire_responses: JSON.stringify(responsesForFinding)
            }
            
            const finding = await apiService.createAuditFinding(findingData)
            findings.push(finding)
          }
        } catch (error) {
          console.error('Error loading SLA metrics for audit findings:', error)
          // Continue without creating findings if SLA metrics can't be loaded
        }
      } else {
        console.warn('No valid SLA ID for creating audit findings')
        // Create findings using workspace data if available
        if (workspaceData.value && workspaceData.value.length > 0) {
          for (const workspace of workspaceData.value) {
            // Convert responses to use question text instead of IDs for audit findings
            const responsesForFinding = {}
            workspace.questions.forEach(question => {
              if (workspace.responses[question.question_id] !== undefined) {
                responsesForFinding[question.question_text] = workspace.responses[question.question_id]
              }
            })
            
            const findingData = {
              audit_id: parseInt(auditId),
              metrics_id: workspace.metric_id,
              evidence: workspace.evidence || '',
              user_id: currentUser.value?.UserId || currentUser.value?.user_id || currentUser.value?.id || 1, // Current reviewer user ID
              how_to_verify: workspace.verification_method || '',
              impact_recommendations: workspace.recommendations || '',
              details_of_finding: workspace.comments || '',
              comment: reviewComments.value, // Reviewer's approval comment
              check_date: new Date().toISOString().split('T')[0],
              questionnaire_responses: JSON.stringify(responsesForFinding)
            }
            
            try {
              const finding = await apiService.createAuditFinding(findingData)
              findings.push(finding)
            } catch (error) {
              console.error('Error creating audit finding:', error)
            }
          }
        }
      }
    }
    
    // Update audit status
    await apiService.updateAudit(auditId, {
      status: 'completed',
      review_status: 'approved',
      review_comments: reviewComments.value,
      completion_date: new Date().toISOString().split('T')[0]
    })
    
    // Show success notification
    await showSuccess('Audit Approved', 'Audit has been approved successfully!', {
      audit_id: route.params.auditId,
      audit_title: audit.value?.title,
      action: 'audit_approved'
    })
    
    PopupService.success('Audit has been approved successfully!', 'Audit Approved')
    PopupService.onAction('ok', () => {
      router.push('/audit/my-audits')
    })
    
  } catch (error) {
    console.error('Error approving audit:', error)
    
    // Show error notification
    await showError('Approval Failed', 'Failed to approve audit. Please try again.', {
      audit_id: route.params.auditId,
      audit_title: audit.value?.title,
      action: 'audit_approval_failed',
      error_message: error.message
    })
    
    PopupService.error('Failed to approve audit. Please try again.', 'Approval Failed')
  } finally {
    isLoading.value = false
  }
}

const handleReject = async () => {
  if (!reviewComments.value.trim()) {
    await showWarning('Missing Comments', 'Please provide review comments before rejecting.', {
      audit_id: route.params.auditId,
      audit_title: audit.value?.title,
      action: 'missing_review_comments'
    })
    PopupService.warning('Please provide review comments before rejecting.', 'Missing Comments')
    return
  }
  
  PopupService.confirm(
    'Are you sure you want to reject this audit? The auditor will be notified and can resubmit after addressing your feedback.',
    'Confirm Rejection',
    async () => {
      await performReject(reviewComments.value)
    }
  )
}

const performReject = async (comments) => {
  
  isLoading.value = true
  try {
    const auditId = route.params.auditId
    
    // Get current version
    const versionsData = await apiService.getAuditVersions(auditId)
    let versions
    if (Array.isArray(versionsData)) {
      versions = versionsData
    } else if (versionsData && versionsData.results && Array.isArray(versionsData.results)) {
      versions = versionsData.results
    } else {
      versions = []
    }
    
    // Find the latest audit version (type 'A') - try different approaches
    let currentVersion = versions.find(v => v.version_type === 'A' && v.approval_status === 'pending')
    
    // If no pending version found, try to find any audit version
    if (!currentVersion) {
      currentVersion = versions
        .filter(v => v.version_type === 'A')
        .sort((a, b) => b.version_number - a.version_number)[0]
    }
    
    // If still no version found, try to find any version
    if (!currentVersion && versions.length > 0) {
      currentVersion = versions
        .sort((a, b) => b.version_number - a.version_number)[0]
    }
    
    if (!currentVersion) {
      PopupService.error('No audit version found. Please ensure the audit has been submitted for review.', 'No Version Found')
      isLoading.value = false
      return
    }
    
    // Update version to rejected
    await apiService.updateAuditVersion(currentVersion.version_id, {
      approval_status: 'rejected'
    })
    
    // Create review version
    const reviewVersions = versions.filter(v => v.version_type === 'R')
    const nextReviewVersion = reviewVersions.length + 1
    
    await apiService.createAuditVersion({
      audit_id: parseInt(auditId),
      version_type: 'R',
      version_number: nextReviewVersion,
      extended_information: JSON.stringify({
        rejected_version: currentVersion.version_number,
        review_comments: comments,
        rejection_date: new Date().toISOString()
      }),
      user_id: currentUser.value?.UserId || currentUser.value?.user_id || currentUser.value?.id || 1, // Current reviewer user ID
      approval_status: 'rejected',
      date_created: new Date().toISOString().split('T')[0],
      is_active: 1
    })
    
    // Update audit status
    await apiService.updateAudit(auditId, {
      status: 'rejected',
      review_status: 'rejected',
      review_comments: comments
    })
    
    // Show warning notification
    await showWarning('Audit Rejected', 'Audit has been rejected by admin. The auditor will be notified.', {
      audit_id: route.params.auditId,
      audit_title: audit.value?.title,
      action: 'audit_rejected'
    })
    
    PopupService.success('Audit has been rejected by admin. The auditor will be notified.', 'Audit Rejected')
    PopupService.onAction('ok', () => {
      router.push('/audit/my-audits')
    })
    
  } catch (error) {
    console.error('Error rejecting audit:', error)
    
    // Show error notification
    await showError('Rejection Failed', 'Failed to reject audit. Please try again.', {
      audit_id: route.params.auditId,
      audit_title: audit.value?.title,
      action: 'audit_rejection_failed',
      error_message: error.message
    })
    
    PopupService.error('Failed to reject audit. Please try again.', 'Rejection Failed')
  } finally {
    isLoading.value = false
  }
}
</script>
