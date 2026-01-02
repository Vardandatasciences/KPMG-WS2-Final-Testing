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
        <p class="text-sm lg:text-base text-muted-foreground">Contract: {{ audit?.contract_title || 'Unknown Contract' }} (Admin View)</p>
      </div>
      <div class="flex items-center gap-4">
        <!-- Admin Badge -->
        <Badge variant="default" class="bg-purple-600 text-white">
          Admin Access
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
          <div v-if="lastSaved" class="mt-2 text-xs text-muted-foreground">
            Last saved: {{ lastSaved.toLocaleTimeString() }}
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

    <!-- Debug Information (temporary) -->
    <Card v-if="questionnaires.length > 0" class="shadow-card border-blue-200 bg-blue-50">
      <CardContent class="p-4">
        <div class="text-sm text-blue-800">
          <strong>Debug Info:</strong> 
          Questionnaires loaded: {{ questionnaires.length }}, 
          Workspaces created: {{ workspaceData.length }}, 
          Active tab: {{ activeTab }}
        </div>
      </CardContent>
    </Card>

    <!-- Audit Workspace with Tabs -->
    <Card v-if="workspaceData.length > 0" class="shadow-card">
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
              @click="handleTabChange(workspace.metric_id.toString())"
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
                        Weight: {{ question.scoring_weightings }}%
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
                        <option 
                          v-for="(option, optIndex) in (question.multiple_choice || [])" 
                          :key="optIndex" 
                          :value="typeof option === 'string' ? option : option.value || option"
                        >
                          {{ typeof option === 'string' ? option : option.label || option.value || option }}
                        </option>
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
                    
                    <!-- Document Upload - Show near question if enabled -->
                    <div v-if="question.document_upload" class="mt-3 pt-3 border-t border-border">
                      <Label class="text-xs font-medium mb-2 flex items-center text-muted-foreground">
                        <Upload class="mr-1.5 h-3.5 w-3.5" />
                        Upload Supporting Documents (Multiple files allowed)
                      </Label>
                      <div class="space-y-2">
                        <div class="flex items-center gap-2">
                          <input
                            type="file"
                            :id="`document-upload-${workspace.metric_id}-${question.question_id}`"
                            multiple
                            accept=".pdf,.doc,.docx,.xls,.xlsx,.png,.jpg,.jpeg"
                            class="flex h-9 flex-1 rounded-md border border-input bg-background px-3 py-1.5 text-xs ring-offset-background file:border-0 file:bg-transparent file:text-xs file:font-medium file:text-foreground placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                            @change="(event) => handleQuestionDocumentUpload(workspaceIndex, question.question_id, event)"
                          />
                          <Button
                            type="button"
                            variant="outline"
                            size="sm"
                            @click="() => {
                              const input = document.getElementById(`document-upload-${workspace.metric_id}-${question.question_id}`)
                              if (input) {
                                input.value = ''
                                input.click()
                              }
                            }"
                            class="h-9 text-xs"
                          >
                            <Upload class="h-3 w-3 mr-1" />
                            Add More
                          </Button>
                        </div>
                        <p class="text-xs text-muted-foreground">
                          Accepted: PDF, DOC, DOCX, XLS, XLSX, PNG, JPG, JPEG (You can select multiple files)
                        </p>
                        <!-- Show uploaded files for this question -->
                        <div v-if="getQuestionDocuments(workspaceIndex, question.question_id).length > 0" class="mt-2 space-y-2">
                          <div class="flex items-center justify-between">
                            <p class="text-xs font-medium text-muted-foreground">
                              Uploaded files ({{ getQuestionDocuments(workspaceIndex, question.question_id).length }}):
                            </p>
                            <Button
                              type="button"
                              variant="ghost"
                              size="sm"
                              @click="clearQuestionDocuments(workspaceIndex, question.question_id)"
                              class="h-6 text-xs text-destructive hover:text-destructive"
                            >
                              Clear All
                            </Button>
                          </div>
                          <div class="space-y-1">
                            <div 
                              v-for="(doc, docIndex) in getQuestionDocuments(workspaceIndex, question.question_id)" 
                              :key="docIndex" 
                              class="flex items-center justify-between text-xs bg-muted p-2 rounded border border-border hover:bg-muted/80 transition-colors group"
                            >
                              <div class="flex items-center gap-2 flex-1 min-w-0">
                                <FileText class="h-3.5 w-3.5 text-muted-foreground flex-shrink-0" />
                                <span class="text-foreground truncate" :title="doc.name">{{ doc.name }}</span>
                              </div>
                              <div class="flex items-center gap-2 flex-shrink-0">
                                <span class="text-muted-foreground">{{ formatFileSize(doc.size) }}</span>
                                <Button
                                  type="button"
                                  variant="outline"
                                  size="sm"
                                  @click="viewQuestionDocument(doc)"
                                  class="h-6 px-2 text-xs flex items-center gap-1"
                                  title="View document"
                                >
                                  <Eye class="h-3 w-3" />
                                  View
                                </Button>
                                <button
                                  type="button"
                                  @click="removeQuestionDocument(workspaceIndex, question.question_id, docIndex)"
                                  class="h-6 w-6 p-0 flex items-center justify-center rounded-full text-destructive hover:text-destructive hover:bg-destructive/20 transition-colors cursor-pointer opacity-70 group-hover:opacity-100"
                                  title="Remove this document"
                                >
                                  <X class="h-4 w-4" />
                                </button>
                              </div>
                            </div>
                          </div>
                        </div>
                      </div>
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
                      :value="workspace.evidence"
                      @input="(event) => updateWorkspaceField(workspaceIndex, 'evidence', event.target.value)"
                      placeholder="Describe the evidence supporting your findings..."
                      :rows="4"
                      class="mt-2"
                    />
                  </div>
                  <div>
                    <Label :for="`verification-${workspace.metric_id}`">How to Verify</Label>
                    <Textarea
                      :id="`verification-${workspace.metric_id}`"
                      :value="workspace.verification_method"
                      @input="(event) => updateWorkspaceField(workspaceIndex, 'verification_method', event.target.value)"
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
                    :value="workspace.comments"
                    @input="(event) => updateWorkspaceField(workspaceIndex, 'comments', event.target.value)"
                    placeholder="Additional comments..."
                    :rows="3"
                    class="mt-2"
                  />
                </div>
                <div>
                  <Label :for="`recommendations-${workspace.metric_id}`">Recommendations</Label>
                  <Textarea
                    :id="`recommendations-${workspace.metric_id}`"
                    :value="workspace.recommendations"
                    @input="(event) => updateWorkspaceField(workspaceIndex, 'recommendations', event.target.value)"
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

    <!-- Actions -->
    <div class="flex flex-col sm:flex-row justify-between items-center gap-4">
      <Button variant="outline" @click="navigateToMyAudits" class="w-full sm:w-auto">
        Back to My Audits
      </Button>
      
      <div class="flex flex-col sm:flex-row gap-3 sm:gap-4 w-full sm:w-auto">
        <!-- Admin Actions - Can perform all operations -->
        <template v-if="audit.status === 'created' || audit.status === 'in_progress'">
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
            :disabled="isLoading || progress < 50"
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
            :disabled="isLoading || progress < 50"
            class="bg-gradient-to-r from-orange-600 to-orange-700 hover:shadow-hover transition-all w-full sm:w-auto"
          >
            <Send class="mr-2 h-4 w-4" />
            Resubmit for Review
          </Button>
        </template>
        
        <!-- Admin Review Actions (when status is under_review) -->
        <template v-else-if="audit.status === 'under_review'">
          <Button
            @click="handleApprove"
            :disabled="isLoading"
            class="bg-gradient-to-r from-green-600 to-green-700 hover:shadow-hover transition-all w-full sm:w-auto"
          >
            <CheckCircle class="mr-2 h-4 w-4" />
            Approve Audit
          </Button>
          <Button
            variant="destructive"
            @click="handleReject"
            :disabled="isLoading"
            class="w-full sm:w-auto"
          >
            <X class="mr-2 h-4 w-4" />
            Reject Audit
          </Button>
          <Button
            variant="outline"
            @click="() => router.push(`/contract-audit/${audit.audit_id}/review`)"
            class="w-full sm:w-auto"
          >
            <FileText class="mr-2 h-4 w-4" />
            Go to Review Page
          </Button>
        </template>
        
        <!-- Admin View Actions (when completed) -->
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

    <Card v-if="progress < 50" class="border-yellow-200 bg-yellow-50">
      <CardContent class="p-4">
        <div class="flex items-center">
          <AlertCircle class="w-5 h-5 text-yellow-600 mr-2" />
          <p class="text-sm text-yellow-800">
            Complete at least 50% of required questions to submit for review.
          </p>
        </div>
      </CardContent>
    </Card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useNotifications } from '@/composables/useNotifications'
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
  AlertTriangle
} from 'lucide-vue-next'
import contractAuditApi from '@/services/contractAuditApi.js'
import loggingService from '@/services/loggingService'
import { PopupService } from '@/popup/popupService'
import { 
  Card, CardHeader, CardTitle, CardDescription, CardContent, Button, Badge, Input, Label, Textarea, Select
} from '@/components/ui_contract'
import StatusBadge from '@/components/StatusBadge.vue'

const route = useRoute()
const router = useRouter()
const { showSuccess, showError, showWarning, showInfo } = useNotifications()

const isLoading = ref(false)
const loading = ref(true)
const activeTab = ref('')
const lastSaved = ref(null)

// Debug function to track tab changes
const handleTabChange = (newTab) => {
  console.log(`Switching from tab ${activeTab.value} to ${newTab}`)
  console.log('Current workspace data before switch:', workspaceData.value.map(w => ({
    term: w.term_name,
    evidence: w.evidence,
    comments: w.comments,
    recommendations: w.recommendations,
    verification_method: w.verification_method
  })))
  activeTab.value = newTab
  console.log('Tab switched successfully')
}
const workspaceData = ref([])
const audit = ref(null)
const contract = ref(null)
const auditor = ref(null)
const reviewer = ref(null)
const metrics = ref([])
const questionnaires = ref([])
const rejectionFeedback = ref(null)
const termQuestionnaires = ref({})
const lastFetchedTermIds = ref([])

const normalizeValue = (value) => {
  if (value === null || value === undefined) return null
  return value.toString()
}

const normalizeString = (value) => {
  if (value === null || value === undefined) return ''
  return value.toString().trim().toLowerCase()
}

const removeTermPrefix = (value) => {
  if (!value) return value
  if (value.startsWith('term_')) return value.slice(5)
  return value
}

const stripIdDecorators = (rawValue) => {
  if (!rawValue) return ''
  let value = normalizeString(rawValue)
  value = removeTermPrefix(value)
  if (value.startsWith('17') && value.length > 2) {
    value = value.slice(2)
  }
  value = value.replace(/_[0-9]+$/, '')
  return value
}

const getNormalizedTermCandidates = (rawValue) => {
  const candidates = new Set()
  const value = normalizeString(rawValue)
  if (!value) return candidates

  const stripped = stripIdDecorators(value)

  const push = (candidate) => {
    if (!candidate) return
    candidates.add(candidate)
    candidates.add(candidate.replace(/\./g, '_'))
    candidates.add(candidate.replace(/_/g, '.'))
  }

  push(value)
  push(stripIdDecorators(value))
  push(stripped)

  // If original had term_ prefix, also include numeric part
  if (value.startsWith('term_')) {
    push(value.slice(5))
  }

  return candidates
}

const getWorkspaceKey = (workspace) => {
  if (!workspace) return ''
  const key = normalizeValue(workspace.term_id)
  return key || ''
}

const findValueByCandidates = (source, candidates) => {
  if (!source) return undefined
  for (const candidate of candidates) {
    const normalizedCandidate = normalizeString(candidate)
    if (!normalizedCandidate) continue

    for (const key of Object.keys(source)) {
      const normalizedKey = normalizeString(key)
      if (!normalizedKey) continue

      const candidateSet = getNormalizedTermCandidates(normalizedCandidate)
      const keySet = getNormalizedTermCandidates(normalizedKey)

      if ([...candidateSet].some(candidateToken => keySet.has(candidateToken))) {
        return source[key]
      }
    }
  }
  return undefined
}

// Helper function to convert File to base64
const fileToBase64 = (file) => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.readAsDataURL(file)
    reader.onload = () => resolve(reader.result)
    reader.onerror = error => reject(error)
  })
}

// Helper function to convert documents to serializable format
const serializeDocuments = (questionDocuments = {}) => {
  if (!questionDocuments || Object.keys(questionDocuments).length === 0) {
    return {}
  }

  const serialized = {}
  Object.entries(questionDocuments).forEach(([questionId, documents]) => {
    if (!Array.isArray(documents) || documents.length === 0) {
      return
    }
    
    serialized[questionId] = documents.map(doc => {
        const fileData = {
          name: doc.name,
          size: doc.size,
          type: doc.type,
        uploadedAt: doc.uploadedAt || new Date().toISOString(),
        url: doc.url || doc.document_url || null,
        s3_file_id: doc.s3_file_id || doc.id || null,
        s3_key: doc.s3_key || null,
        storage: doc.storage || (doc.url ? 's3' : undefined)
        }
        
      if (!fileData.url && doc.content) {
          fileData.content = doc.content
        }
        
        return fileData
      })
  })
  
  return serialized
}

const buildExtendedInfoPayload = async () => {
  if (!workspaceData.value || workspaceData.value.length === 0) return null

  const payload = {
    responses: {},
    evidence: {},
    verification_methods: {},
    recommendations: {},
    comments: {},
    documents: {}, // Store uploaded documents
    metadata: {
      terms: {}
    }
  }

  // Process all workspaces and their documents
  for (const workspace of workspaceData.value) {
    const key = getWorkspaceKey(workspace)
    if (!key) continue

    payload.responses[key] = { ...(workspace.responses || {}) }
    payload.evidence[key] = workspace.evidence || ''
    payload.verification_methods[key] = workspace.verification_method || ''
    payload.recommendations[key] = workspace.recommendations || ''
    payload.comments[key] = workspace.comments || ''
    payload.metadata.terms[key] = {
      term_id: normalizeValue(workspace.term_id),
      term_name: workspace.metric_name,
      metric_id: normalizeValue(workspace.metric_id)
    }
    
    // Serialize documents for this workspace
    if (workspace.questionDocuments && Object.keys(workspace.questionDocuments).length > 0) {
      payload.documents[key] = serializeDocuments(workspace.questionDocuments)
    }
  }

  return payload
}

const areArraysEqual = (a = [], b = []) => {
  if (a.length !== b.length) return false
  for (let i = 0; i < a.length; i += 1) {
    if (a[i] !== b[i]) return false
  }
  return true
}

const extractQuestionnaires = (payload) => {
  if (!payload) return []
  if (Array.isArray(payload)) return payload
  if (Array.isArray(payload.questionnaires)) return payload.questionnaires
  if (payload.data) {
    if (Array.isArray(payload.data.questionnaires)) return payload.data.questionnaires
    if (Array.isArray(payload.data)) return payload.data
  }
  if (Array.isArray(payload.results)) return payload.results
  return []
}

const loadQuestionnairesForMetrics = async (metricsList = []) => {
  try {
    if (!metricsList || metricsList.length === 0) {
      termQuestionnaires.value = {}
      lastFetchedTermIds.value = []
      return
    }

    const termIds = metricsList
      .map(metric => normalizeValue(metric.term_id))
      .filter(Boolean)

    const uniqueSortedTermIds = Array.from(new Set(termIds)).sort()
    if (areArraysEqual(uniqueSortedTermIds, lastFetchedTermIds.value)) {
      return
    }

    const results = {}
    try {
      const response = await contractAuditApi.getContractAuditQuestionnairesForTermIds({
        term_ids: uniqueSortedTermIds.join(',')
      })
      const payload = response.success ? response.data : response
      const mapping = payload?.questionnaires || payload?.by_term || payload || {}

      uniqueSortedTermIds.forEach(termId => {
        const termQuestions = mapping[termId] || []
        results[termId] = Array.isArray(termQuestions) ? termQuestions : extractQuestionnaires(termQuestions)
      })
    } catch (error) {
      console.error('Error fetching questionnaires for term IDs:', error)
      uniqueSortedTermIds.forEach(termId => {
        results[termId] = []
      })
    }

    termQuestionnaires.value = results
    lastFetchedTermIds.value = uniqueSortedTermIds
    console.log('Term-specific questionnaires loaded:', termQuestionnaires.value)
  } catch (error) {
    console.error('Error loading questionnaires for metrics:', error)
    termQuestionnaires.value = {}
  }
}

// Admin mode - no user restrictions
const isAdmin = ref(true) // Always true for admin interface

// Parse extended information JSON for reviewer actions
const parsedExtendedInfo = computed(() => {
  try {
    return buildExtendedInfoPayload()
  } catch (error) {
    console.error('Error creating extended info:', error)
    return null
  }
})

// Load rejection feedback for rejected audits
const loadRejectionFeedback = async (auditId) => {
  try {
    const versionsResponse = await contractAuditApi.getContractAuditVersions({ audit_id: auditId })
    const versionsData = versionsResponse.success ? versionsResponse.data : []
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
    // Load audit details
    const auditResponse = await contractAuditApi.getContractAudit(auditId)
    const auditData = auditResponse.success ? auditResponse.data : null
    console.log('Full audit data received:', auditData)
    console.log('Audit contract_id field:', auditData.contract_id)
    console.log('Audit contract field:', auditData.contract)
    console.log('Audit contract object:', auditData.contract)
    console.log('Audit contract_id type:', typeof auditData.contract_id)
    console.log('Audit contract type:', typeof auditData.contract)
    audit.value = auditData
    
    // Note: contract_title is already included in the audit response from the API
    // No need to load contract separately
    
    // Load users (auditor/reviewer)
    const usersResponse = await contractAuditApi.getAvailableUsers()
    const usersData = usersResponse.success ? usersResponse.data : []
    auditor.value = usersData.find(u => u.user_id === auditData.auditor_id) || null
    reviewer.value = usersData.find(u => u.user_id === auditData.reviewer_id) || null
    
    // Load Contract terms
    console.log('Audit data contract_id:', auditData.contract_id)
    console.log('Audit data contract field:', auditData.contract)
    
    // Try to get contract_id from either contract_id field or contract object
    let contractIdToUse = auditData.contract_id
    if (!contractIdToUse && auditData.contract) {
      contractIdToUse = auditData.contract
      console.log('Using contract field as contract_id:', contractIdToUse)
    }
    
    if (contractIdToUse) {
      console.log('Loading contract terms for contract_id:', contractIdToUse)
      try {
        const termsResponse = await contractAuditApi.getContractTermsForAudit(contractIdToUse)
        console.log('Full terms response:', termsResponse)
        console.log('Terms response success:', termsResponse.success)
        console.log('Terms response data:', termsResponse.data)
        
        const termsData = termsResponse.success ? termsResponse.data : null
        console.log('Terms data object:', termsData)
        console.log('Terms data.terms:', termsData?.terms)
        console.log('Terms data.terms length:', termsData?.terms?.length)
        
        metrics.value = termsData?.terms || []
        console.log('Metrics value after assignment:', metrics.value)
        console.log('Metrics length:', metrics.value.length)
        
        if (metrics.value.length === 0) {
          console.warn('No contract terms found for contract_id:', contractIdToUse)
        } else {
          console.log('Contract terms loaded successfully:', metrics.value.map(m => ({ id: m.term_id, title: m.term_title })))
        }
      } catch (error) {
        console.error('Error loading contract terms:', error)
        console.error('Error details:', error.response?.data)
        console.error('Error status:', error.response?.status)
        metrics.value = []
      }
    } else {
      console.log('No contract_id found in audit data!')
      console.log('Available audit fields:', Object.keys(auditData))
      console.log('Audit data contract_id field:', auditData.contract_id)
      console.log('Audit data contract field:', auditData.contract)
      metrics.value = []
    }
    
    // Load static questionnaires for the metrics
    console.log('Loading questionnaires...')
    const questionnairesResponse = await contractAuditApi.getContractAuditQuestionnaires()
    console.log('Questionnaires API response:', questionnairesResponse)
    console.log('Questionnaires response success:', questionnairesResponse.success)
    console.log('Questionnaires response data:', questionnairesResponse.data)
    
    const questionnairesData = questionnairesResponse.success ? questionnairesResponse.data : null
    console.log('Raw questionnaires data:', questionnairesData)
    console.log('Questionnaires data type:', typeof questionnairesData)
    console.log('Is questionnaires data array?', Array.isArray(questionnairesData))
    
    // Ensure questionnaires is an array
    if (Array.isArray(questionnairesData)) {
      questionnaires.value = questionnairesData
      console.log('Using questionnaires as array, count:', questionnaires.value.length)
      console.log('First questionnaire sample:', questionnaires.value[0])
    } else if (questionnairesData && questionnairesData.results && Array.isArray(questionnairesData.results)) {
      // Handle paginated response
      questionnaires.value = questionnairesData.results
      console.log('Using questionnaires from results, count:', questionnaires.value.length)
      console.log('First questionnaire sample:', questionnaires.value[0])
    } else {
      questionnaires.value = []
      console.log('No questionnaires found, using empty array')
      console.log('Questionnaires data structure:', questionnairesData)
    }
    
    console.log('Final questionnaires loaded:', questionnaires.value)
    console.log('Questionnaires count:', questionnaires.value.length)
    
    // Load rejection feedback if audit is rejected
    if (auditData.status === 'rejected') {
      await loadRejectionFeedback(auditId)
    }
    
  } catch (error) {
    console.error('Error loading audit data:', error)
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
  await loggingService.logPageView('Contract', 'Contract Audit Execution')
  await loadAuditData()
})

// Watch for workspace data changes to ensure persistence
watch(workspaceData, (newData) => {
  console.log('Workspace data changed:', newData.map(w => ({
    term: w.term_name,
    evidence: w.evidence,
    comments: w.comments,
    recommendations: w.recommendations,
    verification_method: w.verification_method
  })))
}, { deep: true })

// Initialize workspace data when audit data is loaded
watch([audit, metrics, questionnaires], async ([newAudit, newMetrics, newQuestionnaires]) => {
  console.log('=== WORKSPACE INITIALIZATION ===')
  console.log('newAudit:', newAudit)
  console.log('newMetrics:', newMetrics)
  console.log('newQuestionnaires:', newQuestionnaires)
  
  // Initialize workspace data if we have questionnaires, regardless of metrics
  if (newAudit && Array.isArray(newQuestionnaires)) {
    console.log('Questionnaires available, creating workspaces...')
    console.log('Number of questionnaires:', newQuestionnaires.length)
    console.log('Sample questionnaire:', newQuestionnaires[0])
    
    if (newMetrics && newMetrics.length > 0) {
      await loadQuestionnairesForMetrics(newMetrics)
    } else {
      termQuestionnaires.value = {}
      lastFetchedTermIds.value = []
    }

    let workspaces = []
    const questionnairesArray = Array.isArray(newQuestionnaires) ? newQuestionnaires : []
    const generalQuestionnaires = questionnairesArray.filter(q => {
      const termId = normalizeString(q.term_id)
      return !termId || termId === 'general'
    })
    
    // If we have metrics (contract terms), create workspaces for each term
    if (newMetrics && newMetrics.length > 0) {
      console.log('Number of metrics (terms):', newMetrics.length)
      console.log('Metrics details:', newMetrics.map(m => ({ id: m.term_id, title: m.term_title })))
      
      workspaces = newMetrics.map((metric, index) => {
        console.log(`Processing metric ${index + 1}: ${metric.term_id} (${metric.term_title})`)
        
        const metricTermId = normalizeValue(metric.term_id)
        const questionsForTerm = termQuestionnaires.value[metricTermId] || []

        console.log(`Assigning ${questionsForTerm.length} questions to term: ${metric.term_title} (Term ID: ${metricTermId})`)
        
        return {
          metric_id: metric.term_id, // Keep metric_id for compatibility with existing code
          term_id: metric.term_id,
          term_name: metric.term_title,
          metric_name: metric.term_title, // Add metric_name for template compatibility
          finding_id: 0, // Would be created on first save
          questions: questionsForTerm, // Show only questions matching this term
          responses: {},
          evidence: '',
          comments: '',
          verification_method: '',
          recommendations: '',
          questionDocuments: {} // Store documents per question
        }
      })

      if (generalQuestionnaires.length > 0) {
        console.log(`Adding general workspace with ${generalQuestionnaires.length} question(s)`)
        workspaces.push({
          metric_id: 'general',
          term_id: 'general',
          term_name: 'General Audit Questions',
          metric_name: 'General Audit Questions',
          finding_id: 0,
          questions: generalQuestionnaires,
          responses: {},
          evidence: '',
          comments: '',
          verification_method: '',
          recommendations: '',
          questionDocuments: {} // Store documents per question
        })
      }
    } else {
      // If no metrics, create a single workspace with all questionnaires
      console.log('No metrics found, creating single workspace with all questionnaires')
      console.log('newMetrics value:', newMetrics)
      console.log('newMetrics length:', newMetrics?.length)
      console.log('newMetrics type:', typeof newMetrics)
      console.log('Is newMetrics array?', Array.isArray(newMetrics))
      
      workspaces = [{
        metric_id: 'general',
        term_id: 'general',
        term_name: 'General Audit Questions',
        metric_name: 'General Audit Questions',
        finding_id: 0,
        questions: questionnairesArray,
        responses: {},
        evidence: '',
        comments: '',
        verification_method: '',
        recommendations: '',
        questionDocuments: {} // Store documents per question
      }]
    }
    
    console.log('Created workspaces:', workspaces.length)
    console.log('Workspace details:', workspaces.map(w => ({
      term: w.term_name,
      questions_count: w.questions.length
    })))
    
    // Load existing audit version data if available
    try {
      const auditId = route.params.auditId
      const versionsResponse = await contractAuditApi.getContractAuditVersions({ audit_id: auditId })
      const versionsData = versionsResponse.success ? versionsResponse.data : []
      
      // Handle both array and paginated response formats
      let versions
      if (Array.isArray(versionsData)) {
        versions = versionsData
      } else if (versionsData && versionsData.results && Array.isArray(versionsData.results)) {
        versions = versionsData.results
      } else {
        versions = []
      }
      
      // Find the latest audit version (type 'A') - prioritize active versions, then drafts
      let latestVersion = versions
        .filter(v => v.version_type === 'A' && v.is_active === 1)
        .sort((a, b) => b.version_number - a.version_number)[0]
      
      // If no active version found, try to find any version with type 'A' (including drafts)
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
            const candidateKeys = [
              normalizeValue(workspace.term_id)
            ]

            // Load responses
            const savedResponses = findValueByCandidates(extendedInfo.responses, candidateKeys)
            if (savedResponses !== undefined) {
              workspace.responses = { ...(savedResponses || {}) }
            }

            // Load evidence
            const savedEvidence = findValueByCandidates(extendedInfo.evidence, candidateKeys)
            if (savedEvidence !== undefined) {
              workspace.evidence = savedEvidence || ''
            }

            // Load verification method
            const savedVerification = findValueByCandidates(extendedInfo.verification_methods, candidateKeys)
            if (savedVerification !== undefined) {
              workspace.verification_method = savedVerification || ''
            }

            // Load comments
            const savedComments = findValueByCandidates(extendedInfo.comments, candidateKeys)
            if (savedComments !== undefined) {
              workspace.comments = savedComments || ''
            }

            // Load recommendations
            const savedRecommendations = findValueByCandidates(extendedInfo.recommendations, candidateKeys)
            if (savedRecommendations !== undefined) {
              workspace.recommendations = savedRecommendations || ''
            }

        const savedDocuments = findValueByCandidates(extendedInfo.documents, candidateKeys)
        if (savedDocuments !== undefined) {
          workspace.questionDocuments = cloneQuestionDocuments(savedDocuments)
            }
          })
        }
      }
    } catch (error) {
      console.error('Error loading audit version data:', error)
    }
    
    // Try to load saved workspace data from localStorage
    const savedWorkspaceData = loadWorkspaceFromStorage()
    if (savedWorkspaceData && savedWorkspaceData.length === workspaces.length) {
      console.log('Loading saved workspace data from localStorage')
      // Merge saved data with current workspace structure
      workspaceData.value = workspaces.map((workspace, index) => {
        const savedWorkspace = savedWorkspaceData[index]
        if (savedWorkspace) {
          return {
            ...workspace,
            responses: savedWorkspace.responses || {},
            evidence: savedWorkspace.evidence || '',
            comments: savedWorkspace.comments || '',
            verification_method: savedWorkspace.verification_method || '',
            recommendations: savedWorkspace.recommendations || '',
            questionDocuments: savedWorkspace.questionDocuments || {}
          }
        }
        return workspace
      })
    } else {
      console.log('Using fresh workspace data')
      workspaceData.value = workspaces
    }
    
    // Set first tab as active
    if (workspaces.length > 0) {
      activeTab.value = workspaces[0].metric_id.toString()
    }
    
    console.log('Final workspace data set:', workspaceData.value)
  } else {
    console.log('Insufficient data for workspace initialization:')
    console.log('- newAudit:', !!newAudit)
    console.log('- newQuestionnaires:', !!newQuestionnaires, Array.isArray(newQuestionnaires) ? newQuestionnaires.length : 'not array')
  }
}, { immediate: true })

const handleResponseChange = (workspaceIndex, questionId, value) => {
  console.log(`Updating response for workspace ${workspaceIndex}, question ${questionId} with value:`, value)
  workspaceData.value[workspaceIndex].responses[questionId] = value
  console.log(`Updated responses:`, workspaceData.value[workspaceIndex].responses)
  
  // Save to localStorage as backup
  saveWorkspaceToStorage()
}

const updateWorkspaceField = (workspaceIndex, fieldName, value) => {
  console.log(`Updating workspace ${workspaceIndex} field ${fieldName} with value:`, value)
  if (workspaceData.value[workspaceIndex]) {
    workspaceData.value[workspaceIndex][fieldName] = value
    console.log(`Updated workspace data:`, workspaceData.value[workspaceIndex])
    
    // Save to localStorage as backup
    saveWorkspaceToStorage()
  }
}

const handleQuestionDocumentUpload = async (workspaceIndex, questionId, event) => {
  const files = event.target.files
  if (!files || files.length === 0) return

  if (!audit.value?.audit_id) {
    PopupService.error('Audit must be loaded before uploading documents.', 'Upload Error')
    return
  }
  
  console.log(`Uploading ${files.length} document(s) for question ${questionId} in workspace ${workspaceIndex}`)
  
  if (!workspaceData.value[workspaceIndex].questionDocuments) {
    workspaceData.value[workspaceIndex].questionDocuments = {}
  }
  
  if (!workspaceData.value[workspaceIndex].questionDocuments[questionId]) {
    workspaceData.value[workspaceIndex].questionDocuments[questionId] = []
  }
  
  for (const file of Array.from(files)) {
    try {
      const base64Content = await fileToBase64(file)
      const uploadPayload = {
        audit_id: audit.value.audit_id,
        term_id: workspaceData.value[workspaceIndex].term_id,
        question_id: questionId,
        file_name: file.name,
        file_type: file.type,
        file_size: file.size,
        file_data: base64Content
      }

      const uploadResponse = await contractAuditApi.uploadAuditDocument(uploadPayload)
      if (!uploadResponse.success) {
        console.error('Document upload failed:', uploadResponse.error)
        PopupService.error(uploadResponse.error || 'Failed to upload document', 'Upload Failed')
        continue
      }

      const uploadedFile = uploadResponse.data?.file || {}
    const docEntry = {
      name: file.name,
      size: file.size,
      type: file.type,
        uploadedAt: new Date().toISOString(),
        url: uploadedFile.url,
        s3_file_id: uploadedFile.s3_file_id,
        s3_key: uploadedFile.s3_key,
        storage: 's3'
      }

      workspaceData.value[workspaceIndex].questionDocuments[questionId].push(docEntry)
      showSuccess(`Uploaded ${file.name}`)
    } catch (error) {
      console.error('Error uploading document:', error)
      PopupService.error('Failed to upload document. Please try again.', 'Upload Error')
    }
    }
    
  if (event?.target) {
    event.target.value = ''
  }
  
  console.log(`Documents stored for question ${questionId}:`, workspaceData.value[workspaceIndex].questionDocuments[questionId])
  
  saveWorkspaceToStorage()
}

const getQuestionDocuments = (workspaceIndex, questionId) => {
  if (!workspaceData.value[workspaceIndex]?.questionDocuments?.[questionId]) {
    return []
  }
  return workspaceData.value[workspaceIndex].questionDocuments[questionId]
}

const formatFileSize = (bytes) => {
  if (!bytes) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i]
}

const removeQuestionDocument = (workspaceIndex, questionId, docIndex) => {
  if (!workspaceData.value[workspaceIndex]?.questionDocuments?.[questionId]) {
    return
  }
  
  workspaceData.value[workspaceIndex].questionDocuments[questionId].splice(docIndex, 1)
  
  // If no documents left, clean up the array
  if (workspaceData.value[workspaceIndex].questionDocuments[questionId].length === 0) {
    delete workspaceData.value[workspaceIndex].questionDocuments[questionId]
  }
  
  // Save to localStorage
  saveWorkspaceToStorage()
  
  showInfo('Document removed')
}

const clearQuestionDocuments = (workspaceIndex, questionId) => {
  if (!workspaceData.value[workspaceIndex]?.questionDocuments?.[questionId]) {
    return
  }
  
  if (confirm(`Are you sure you want to remove all ${workspaceData.value[workspaceIndex].questionDocuments[questionId].length} document(s) for this question?`)) {
    delete workspaceData.value[workspaceIndex].questionDocuments[questionId]
    
    // Save to localStorage
    saveWorkspaceToStorage()
    
    showInfo('All documents removed')
  }
}

const viewQuestionDocument = (doc) => {
  console.log('Viewing document:', doc)
  
  if (doc.url) {
    window.open(doc.url, '_blank')
    return
  }
  
  // Check if document has File object (from upload)
  if (doc.file && doc.file instanceof File) {
    try {
      const reader = new FileReader()
      reader.onload = (e) => {
        const content = e.target.result
        const fileName = doc.name || doc.file.name || 'document'
        const fileType = doc.type || doc.file.type || ''
        
        openDocumentViewer(content, fileName, fileType)
      }
      reader.onerror = (error) => {
        console.error('Error reading file:', error)
        PopupService.error('Failed to read document', 'Error')
      }
      reader.readAsDataURL(doc.file)
    } catch (error) {
      console.error('Error viewing document:', error)
      PopupService.error('Failed to view document', 'Error')
    }
  } else if (doc.content) {
    // Document already has base64 content
    const fileName = doc.name || doc.filename || 'document'
    const fileType = doc.type || ''
    openDocumentViewer(doc.content, fileName, fileType)
  } else {
    PopupService.warning('Document content not available for viewing.', 'Cannot View Document')
  }
}

const openDocumentViewer = (content, fileName, fileType) => {
  try {
    // Determine file type and handle accordingly
    // For PDFs, open directly in new tab
    if (fileType.includes('pdf') || fileName.toLowerCase().endsWith('.pdf')) {
      const newWindow = window.open('', '_blank')
      if (newWindow) {
        newWindow.document.write(`
          <html>
            <head>
              <title>${fileName}</title>
              <style>
                body { margin: 0; padding: 0; }
                iframe { width: 100vw; height: 100vh; border: none; }
              </style>
            </head>
            <body>
              <iframe src="${content}" type="application/pdf"></iframe>
            </body>
          </html>
        `)
        newWindow.document.close()
      } else {
        // Popup blocked, trigger download instead
        triggerDocumentDownload(content, fileName)
      }
    } else if (fileType.startsWith('image/')) {
      // For images, open in new tab
      const newWindow = window.open('', '_blank')
      if (newWindow) {
        newWindow.document.write(`
          <html>
            <head>
              <title>${fileName}</title>
              <style>
                body { margin: 0; padding: 20px; display: flex; justify-content: center; align-items: center; min-height: 100vh; background: #f5f5f5; }
                img { max-width: 100%; max-height: 90vh; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
              </style>
            </head>
            <body>
              <img src="${content}" alt="${fileName}" />
            </body>
          </html>
        `)
        newWindow.document.close()
      } else {
        triggerDocumentDownload(content, fileName)
      }
    } else {
      // For other file types, trigger download
      triggerDocumentDownload(content, fileName)
    }
  } catch (error) {
    console.error('Error opening document viewer:', error)
    PopupService.error('Failed to view document. Please try downloading it instead.', 'Error')
  }
}

const triggerDocumentDownload = (content, fileName) => {
  try {
    const link = document.createElement('a')
    link.href = content
    link.download = fileName
    link.target = '_blank'
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  } catch (error) {
    console.error('Error downloading document:', error)
    PopupService.error('Failed to download document', 'Error')
  }
}

const sanitizeDocumentsForStorage = (questionDocuments = {}) => {
  const sanitized = {}
  Object.entries(questionDocuments || {}).forEach(([questionId, documents]) => {
    sanitized[questionId] = documents.map(doc => ({
      name: doc.name,
      size: doc.size,
      type: doc.type,
      uploadedAt: doc.uploadedAt,
      url: doc.url || doc.document_url || null,
      s3_file_id: doc.s3_file_id || null,
      s3_key: doc.s3_key || null,
      storage: doc.storage || (doc.url ? 's3' : undefined),
      content: doc.content || null
    }))
  })
  return sanitized
}

const sanitizeWorkspaceForStorage = (workspace) => ({
  ...workspace,
  questionDocuments: sanitizeDocumentsForStorage(workspace.questionDocuments)
})

const cloneQuestionDocuments = (documents = {}) => {
  const cloned = {}
  Object.entries(documents || {}).forEach(([questionId, docs]) => {
    cloned[questionId] = Array.isArray(docs) ? docs.map(doc => ({ ...doc })) : []
  })
  return cloned
}

const saveWorkspaceToStorage = () => {
  try {
    const auditId = route.params.auditId
    const sanitizedData = workspaceData.value.map(workspace => sanitizeWorkspaceForStorage(workspace))
    localStorage.setItem(`audit_workspace_${auditId}`, JSON.stringify(sanitizedData))
    console.log('Workspace data saved to localStorage')
  } catch (error) {
    console.error('Error saving workspace to localStorage:', error)
  }
}

const loadWorkspaceFromStorage = () => {
  try {
    const auditId = route.params.auditId
    const savedData = localStorage.getItem(`audit_workspace_${auditId}`)
    if (savedData) {
      const parsedData = JSON.parse(savedData)
      console.log('Loaded workspace data from localStorage:', parsedData)
      return parsedData
    }
  } catch (error) {
    console.error('Error loading workspace from localStorage:', error)
  }
  return null
}

const clearWorkspaceStorage = () => {
  try {
    const auditId = route.params.auditId
    localStorage.removeItem(`audit_workspace_${auditId}`)
    console.log('Cleared workspace data from localStorage')
  } catch (error) {
    console.error('Error clearing workspace from localStorage:', error)
  }
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
    const auditId = route.params.auditId
    const extendedInfoPayload = await buildExtendedInfoPayload() || {
      responses: {},
      evidence: {},
      verification_methods: {},
      recommendations: {},
      comments: {},
      documents: {},
      metadata: { terms: {} }
    }
    
    // Get current version number for draft versions
    const versionsResponse = await contractAuditApi.getContractAuditVersions({ audit_id: auditId })
    const versionsData = versionsResponse.success ? versionsResponse.data : []
    let versions
    if (Array.isArray(versionsData)) {
      versions = versionsData
    } else if (versionsData && versionsData.results && Array.isArray(versionsData.results)) {
      versions = versionsData.results
    } else {
      versions = []
    }
    
    // Get the latest draft version number (type 'A' with is_active = 0)
    const draftVersions = versions.filter(v => v.version_type === 'A' && v.is_active === 0)
    const currentDraftVersion = draftVersions.length > 0 ? Math.max(...draftVersions.map(v => v.version_number)) : 0
    const nextDraftVersion = currentDraftVersion + 1
    
    console.log('Saving audit progress:', {
      auditId,
      currentDraftVersion,
      nextDraftVersion,
      workspaceCount: workspaceData.value.length
    })
    
    extendedInfoPayload.save_type = 'draft'
    extendedInfoPayload.save_timestamp = new Date().toISOString()
    extendedInfoPayload.progress_percentage = Math.round(progress.value)

    // Create a draft version of the audit
    const versionData = {
      audit_id: parseInt(auditId),
      version_type: 'A', // Audit version
      version_number: nextDraftVersion,
      extended_information: JSON.stringify(extendedInfoPayload),
      user_id: 2, // Current user ID
      approval_status: 'pending',
      date_created: new Date().toISOString().split('T')[0],
      is_active: 0 // Draft version is not active
    }
    
    console.log('Creating draft version:', versionData)
    
    // Call the API to create the draft version
    const savedVersion = await contractAuditApi.createContractAuditVersion(versionData)
    console.log('Draft version created successfully:', savedVersion)
    
    // Clear localStorage since we've saved to backend
    clearWorkspaceStorage()
    
    // Update last saved timestamp
    lastSaved.value = new Date()
    
    PopupService.success(`Your audit progress has been saved successfully as draft version ${nextDraftVersion}.`, 'Progress Saved')
  } catch (error) {
    console.error('Error saving progress:', error)
    console.error('Error details:', error.response?.data)
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
    PopupService.warning('Please complete all required questions and provide evidence before submitting.', 'Required Fields Missing')
    return
  }

  isLoading.value = true
  try {
    const auditId = route.params.auditId
    const extendedInfoPayload = await buildExtendedInfoPayload() || {
      responses: {},
      evidence: {},
      verification_methods: {},
      recommendations: {},
      comments: {},
      documents: {},
      metadata: { terms: {} }
    }
    
    // Get current version number for audit versions
    const versionsResponse = await contractAuditApi.getContractAuditVersions({ audit_id: auditId })
    const versionsData = versionsResponse.success ? versionsResponse.data : []
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
    
    extendedInfoPayload.submission_timestamp = new Date().toISOString()

    // STEP 1: Create audit version (A = Audit submission)
    const versionData = {
      audit_id: parseInt(auditId),
      version_type: 'A', // A = Audit submission from auditor
      version_number: nextVersion,
      extended_information: JSON.stringify(extendedInfoPayload),
      user_id: 2, // Current user ID (auditor)
      approval_status: 'pending', // Initially pending review
      date_created: new Date().toISOString().split('T')[0],
      is_active: 1
    }
    
    console.log('Creating audit version:', versionData)
    const auditVersion = await contractAuditApi.createContractAuditVersion(versionData)
    console.log('Audit version created:', auditVersion)
    
    // STEP 2: Update audit status to under_review
    const updateData = { status: 'under_review' }
    console.log('Updating audit with data:', updateData)
    await contractAuditApi.updateContractAudit(auditId, updateData)
    console.log('Audit status updated to under_review')
    
    // STEP 3: Note: audit_findings will be created AFTER reviewer approval
    // This happens in the review process, not during initial submission
    
    PopupService.success(`Audit version v${nextVersion} has been submitted to ${reviewer.value?.name} for review.`, 'Audit Submitted')
    
    router.push('/contract-audit/all')
  } catch (error) {
    console.error('Error submitting audit:', error)
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
    PopupService.warning('Please complete all required questions and provide evidence before resubmitting.', 'Required Fields Missing')
    return
  }

  // Confirm resubmission
  if (!confirm('Are you sure you want to resubmit this audit for review? This will create a new version.')) {
    return
  }

  isLoading.value = true
  try {
    const auditId = route.params.auditId
    const extendedInfoPayload = await buildExtendedInfoPayload() || {
      responses: {},
      evidence: {},
      verification_methods: {},
      recommendations: {},
      comments: {},
      documents: {},
      metadata: { terms: {} }
    }
    
    // Get current version number for audit versions
    const versionsResponse = await contractAuditApi.getContractAuditVersions({ audit_id: auditId })
    const versionsData = versionsResponse.success ? versionsResponse.data : []
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
    extendedInfoPayload.resubmission_notes = 'Resubmitted after addressing reviewer feedback'
    extendedInfoPayload.previous_rejection_version = currentVersion
    extendedInfoPayload.resubmission_timestamp = new Date().toISOString()

    const versionData = {
      audit_id: parseInt(auditId),
      version_type: 'A', // A = Audit submission from auditor
      version_number: nextVersion,
      extended_information: JSON.stringify(extendedInfoPayload),
      user_id: 2, // Current user ID (auditor)
      approval_status: 'pending', // Initially pending review
      date_created: new Date().toISOString().split('T')[0],
      is_active: 1
    }
    
    console.log('Creating resubmission audit version:', versionData)
    const auditVersion = await contractAuditApi.createContractAuditVersion(versionData)
    console.log('Resubmission audit version created:', auditVersion)
    
    // STEP 2: Update audit status to under_review
    const updateData = { 
      status: 'under_review',
      review_status: 'pending', // Reset to pending status for new review
      review_comments: '' // Clear previous review comments
    }
    console.log('🔄 Updating audit status after resubmission:', updateData)
    const updateResponse = await contractAuditApi.updateContractAudit(auditId, updateData)
    console.log('✅ Audit status update response:', updateResponse)
    console.log('✅ Audit status changed from "rejected" to "under_review"')
    console.log('✅ Audit is now visible in reviewer\'s queue')
    
    // Clear localStorage since we've saved to backend
    clearWorkspaceStorage()
    console.log('✅ Workspace data cleared from localStorage')
    
    PopupService.success(`Audit has been resubmitted as version v${nextVersion} to ${reviewer.value?.name} for review.\n\nThe audit is now in "Under Review" status and will appear in the reviewer's queue.`, 'Audit Resubmitted')
    
    router.push('/contract-audit/all')
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

const navigateToMyAudits = () => router.push('/contract-audit/all')

// Reviewer functions
const handleApprove = async () => {
  if (!confirm('Are you sure you want to approve this audit?')) return
  
  isLoading.value = true
  try {
    const auditId = route.params.auditId
    
    // Get current version
    const versionsResponse = await contractAuditApi.getContractAuditVersions({ audit_id: auditId })
    const versionsData = versionsResponse.success ? versionsResponse.data : []
    let versions
    if (Array.isArray(versionsData)) {
      versions = versionsData
    } else if (versionsData && versionsData.results && Array.isArray(versionsData.results)) {
      versions = versionsData.results
    } else {
      versions = []
    }
    const currentVersion = versions.find(v => v.version_type === 'A' && v.approval_status === 'pending')
    
    if (!currentVersion) {
      PopupService.warning('No pending audit version found.', 'No Pending Version')
      return
    }
    
    // Update version to approved
    console.log('Updating audit version:', currentVersion.version_id, 'with data:', { approval_status: 'approved' })
    await contractAuditApi.updateContractAuditVersion(currentVersion.version_id, {
      approval_status: 'approved'
    })
    
    // Create review version
    const reviewVersions = versions.filter(v => v.version_type === 'R')
    const nextReviewVersion = reviewVersions.length + 1
    
    await contractAuditApi.createContractAuditVersion({
      audit_id: parseInt(auditId),
      version_type: 'R',
      version_number: nextReviewVersion,
      extended_information: JSON.stringify({
        approved_version: currentVersion.version_number,
        review_comments: 'Audit approved by admin',
        approval_date: new Date().toISOString()
      }),
      user_id: 1, // Admin user ID
      approval_status: 'approved',
      date_created: new Date().toISOString().split('T')[0],
      is_active: 1
    })
    
    // STEP 4: Create audit findings for each metric (after approval)
    const extendedInfo = parsedExtendedInfo.value
    const findings = []
    
    console.log('🔍 Creating audit findings...')
    console.log('Extended info:', extendedInfo)
    console.log('Workspace data:', workspaceData.value)
    
    if (extendedInfo && extendedInfo.responses) {
      // Use the current workspace data instead of making another API call
      console.log('Creating findings for workspace data:', workspaceData.value.length, 'workspaces')
      
      // Create audit findings for each workspace (term)
      for (const workspace of workspaceData.value) {
        console.log(`Creating finding for workspace: ${workspace.term_name} (ID: ${workspace.term_id})`)
        
        const findingData = {
          audit_id: parseInt(auditId),
          term_id: workspace.term_id.toString(), // Ensure term_id is string to match CharField
          evidence: workspace.evidence || '',
          user_id: 1, // Admin user ID
          how_to_verify: workspace.verification_method || '',
          impact_recommendations: workspace.recommendations || '',
          details_of_finding: workspace.comments || '',
          comment: 'Audit approved by admin', // Admin's approval comment
          check_date: new Date().toISOString().split('T')[0],
          questionnaire_responses: JSON.stringify(workspace.responses || {})
        }
        
        console.log('Finding data to create:', findingData)
        
        try {
          const finding = await contractAuditApi.createContractAuditFinding(findingData)
          console.log('✅ Finding created successfully:', finding)
          findings.push(finding)
        } catch (error) {
          console.error('❌ Error creating finding:', error)
          console.error('Error details:', error.response?.data)
        }
      }
    } else {
      console.log('❌ No extended info or responses found')
      console.log('Extended info:', extendedInfo)
    }
    
    // Update audit status
    await contractAuditApi.updateContractAudit(auditId, {
      status: 'completed',
      review_status: 'approved',
      review_comments: 'Audit approved by admin',
      completion_date: new Date().toISOString().split('T')[0]
    })
    
    console.log(`✅ Audit approved successfully! Created ${findings.length} audit findings.`)
    PopupService.success(`Audit has been approved successfully! Created ${findings.length} audit findings.`, 'Audit Approved')
    router.push('/contract-audit/all')
    
  } catch (error) {
    console.error('Error approving audit:', error)
    PopupService.error('Failed to approve audit. Please try again.', 'Approval Failed')
  } finally {
    isLoading.value = false
  }
}

const handleReject = async () => {
  const comments = prompt('Please provide rejection comments:')
  if (!comments) return
  
  isLoading.value = true
  try {
    const auditId = route.params.auditId
    
    // Get current version
    const versionsResponse = await contractAuditApi.getContractAuditVersions({ audit_id: auditId })
    const versionsData = versionsResponse.success ? versionsResponse.data : []
    let versions
    if (Array.isArray(versionsData)) {
      versions = versionsData
    } else if (versionsData && versionsData.results && Array.isArray(versionsData.results)) {
      versions = versionsData.results
    } else {
      versions = []
    }
    const currentVersion = versions.find(v => v.version_type === 'A' && v.approval_status === 'pending')
    
    if (!currentVersion) {
      PopupService.warning('No pending audit version found.', 'No Pending Version')
      return
    }
    
    // Update version to rejected
    await contractAuditApi.updateContractAuditVersion(currentVersion.version_id, {
      approval_status: 'rejected'
    })
    
    // Create review version
    const reviewVersions = versions.filter(v => v.version_type === 'R')
    const nextReviewVersion = reviewVersions.length + 1
    
    await contractAuditApi.createContractAuditVersion({
      audit_id: parseInt(auditId),
      version_type: 'R',
      version_number: nextReviewVersion,
      extended_information: JSON.stringify({
        rejected_version: currentVersion.version_number,
        review_comments: comments,
        rejection_date: new Date().toISOString()
      }),
      user_id: 1, // Admin user ID
      approval_status: 'rejected',
      date_created: new Date().toISOString().split('T')[0],
      is_active: 1
    })
    
    // Update audit status
    await contractAuditApi.updateContractAudit(auditId, {
      status: 'rejected',
      review_status: 'rejected',
      review_comments: comments
    })
    
    PopupService.success('Audit has been rejected by admin. The auditor will be notified.', 'Audit Rejected')
    router.push('/contract-audit/all')
    
  } catch (error) {
    console.error('Error rejecting audit:', error)
    PopupService.error('Failed to reject audit. Please try again.', 'Rejection Failed')
  } finally {
    isLoading.value = false
  }
}
</script>
