<template>
  <div class="qt-container">
    <h1 class="qt-title">Create Questionnaire Template</h1>
    
    <!-- Info banner when coming from SLA creation -->
    <div v-if="returnTo === 'sla-create' && prefilledMetricName" class="qt-info-banner">
      <div class="qt-info-content">
        <svg xmlns="http://www.w3.org/2000/svg" class="qt-info-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/>
        </svg>
        <div>
          <div class="qt-info-title">Creating questionnaires for SLA metric: <strong>{{ prefilledMetricName }}</strong></div>
          <div class="qt-info-subtitle">After saving, you will be redirected back to complete your SLA creation.</div>
        </div>
      </div>
    </div>
    
    <!-- Info banner when coming from Contract creation -->
    <div v-if="returnTo === 'contract-create' && prefilledTermId" class="qt-info-banner">
      <div class="qt-info-content">
        <svg xmlns="http://www.w3.org/2000/svg" class="qt-info-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/>
        </svg>
        <div>
          <div class="qt-info-title">Creating questionnaires for contract term: <strong>{{ route.query.term_title || 'Term' }}</strong></div>
          <div class="qt-info-subtitle" v-if="prefilledTermCategory">Term Category: <strong>{{ prefilledTermCategory }}</strong> | Term ID: <strong>{{ prefilledTermId }}</strong></div>
          <div class="qt-info-subtitle">After saving, you will be redirected back to complete your contract creation.</div>
        </div>
      </div>
    </div>
    
    <form class="qt-form" @submit.prevent="handleSubmit">
      <div class="qt-grid">
        <div class="qt-field">
          <label for="template_name">Template Name<span class="qt-required">*</span></label>
          <input id="template_name" v-model.trim="form.template_name" type="text" required placeholder="e.g., Vendor Security Assessment" />
        </div>
        <div class="qt-field">
          <label for="template_version">Version</label>
          <input id="template_version" v-model.trim="form.template_version" type="text" placeholder="1.0" />
        </div>
        <div class="qt-field">
          <label for="template_type">Template Type</label>
          <select id="template_type" v-model="form.template_type">
            <option v-for="opt in TEMPLATE_TYPE_CHOICES" :key="opt" :value="opt">{{ opt }}</option>
          </select>
        </div>

        <div class="qt-field">
          <label for="module_type">Module Type</label>
          <select id="module_type" v-model="form.module_type">
            <option v-for="opt in MODULE_TYPE_CHOICES" :key="opt" :value="opt">{{ opt }}</option>
          </select>
        </div>

        <div class="qt-field">
          <label for="module_subtype">Module Subtype</label>
          <input id="module_subtype" v-model.trim="form.module_subtype" type="text" placeholder="Optional subtype" />
        </div>

        <div class="qt-field">
          <label for="status">Status</label>
          <select id="status" v-model="form.status">
            <option v-for="opt in STATUS_CHOICES" :key="opt" :value="opt">{{ opt }}</option>
          </select>
        </div>

        
        <div class="qt-checkboxes">
          <label class="qt-checkbox">
            <input type="checkbox" v-model="form.approval_required" />
            <span>Approval Required</span>
          </label>
          <label class="qt-checkbox">
            <input type="checkbox" v-model="form.is_active" />
            <span>Active</span>
          </label>
        </div>
      </div>

      <div class="qt-field">
        <label for="template_description">Description</label>
        <textarea id="template_description" v-model.trim="form.template_description" rows="4" placeholder="Describe the purpose of this template"></textarea>
      </div>

      <div class="qt-field">
        <div class="qt-label-row">
          <label>Questions</label>
          <div class="qt-question-controls">
            <button type="button" class="qt-mini qt-add" @click="addQuestion">Add question</button>
            <button
              v-if="form.module_type === 'SLA'"
              type="button"
              class="qt-mini qt-import"
              @click="openMetricSelector"
              :disabled="staticMetricsLoading"
            >
              {{ staticMetricsLoading ? 'Loading metrics...' : 'Import from metrics' }}
            </button>
          </div>
        </div>
        <p v-if="importNotice" class="qt-import-notice">{{ importNotice }}</p>
        <div v-if="questions.length === 0" class="qt-hint">No questions yet. Click "Add question" to start.</div>
        <div v-for="(q, idx) in questions" :key="q._key" class="qt-question">
          <div class="qt-question-header">
            <div class="qt-question-title">Question {{ idx + 1 }}</div>
            <div class="qt-question-actions">
              <button type="button" class="qt-mini qt-remove" @click="removeQuestion(idx)">Remove</button>
            </div>
          </div>

          <!-- Place main text fields first -->
          <div class="qt-field">
            <label>question_text<span class="qt-required">*</span></label>
            <textarea v-model.trim="q.question_text" rows="2" placeholder="Enter the question text"></textarea>
          </div>

          <div class="qt-field">
            <label>help_text</label>
            <textarea v-model.trim="q.help_text" rows="2" placeholder="Optional help for respondent"></textarea>
          </div>

          <!-- Then the attribute grid -->
          <div class="qt-grid">
            <div class="qt-field" v-if="form.module_type === 'VENDOR'">
              <label>question_category</label>
              <input type="text" v-model.trim="q.question_category" placeholder="e.g., Security" />
            </div>
            <div class="qt-field">
              <label>answer_type</label>
              <select v-model="q.answer_type">
                <option v-for="opt in ANSWER_TYPE_CHOICES" :key="opt" :value="opt">{{ opt }}</option>
              </select>
            </div>
            <div class="qt-field">
              <label>is_required</label>
              <select v-model="q.is_required">
                <option :value="true">true</option>
                <option :value="false">false</option>
              </select>
            </div>
            <div class="qt-field">
              <label>weightage</label>
              <input type="number" step="0.01" v-model.number="q.weightage" placeholder="e.g., 10.0" />
            </div>
            <div class="qt-field" v-if="form.module_type === 'SLA'">
              <label>metric_name</label>
              <input type="text" v-model.trim="q.metric_name" placeholder="e.g., Security Score" />
            </div>
            <div class="qt-field" v-if="form.module_type === 'CONTRACT'">
              <label>term_id</label>
              <input type="text" v-model.trim="q.term_id" placeholder="e.g., TERM-001 or 42 (optional)" />
            </div>
            <div class="qt-field">
              <label>allow_document_upload</label>
              <select v-model="q.allow_document_upload">
                <option :value="true">true</option>
                <option :value="false">false</option>
              </select>
            </div>
            <div class="qt-field" v-if="q.answer_type === 'MULTIPLE_CHOICE' || q.answer_type === 'CHECKBOX'">
              <label>options (comma separated)</label>
              <input type="text" v-model.trim="q._optionsString" placeholder="Option 1, Option 2" />
            </div>
          </div>

          <!-- Options positioned next to allow_document_upload in the attribute grid -->
        </div>
      </div>

      <div class="qt-actions">
        <button type="submit" class="qt-primary" :disabled="submitting">{{ submitting ? 'Saving...' : 'Save Template' }}</button>
        <button type="button" class="qt-secondary" @click="resetForm" :disabled="submitting">Reset</button>
      </div>

      <p v-if="successMessage" class="qt-success">{{ successMessage }}</p>
      <p v-if="submitError" class="qt-error">{{ submitError }}</p>
    </form>

    <!-- Static metric question selector -->
    <div
      v-if="showMetricSelector"
      class="qt-modal-backdrop"
      @click.self="closeMetricSelector"
    >
      <div class="qt-modal">
        <div class="qt-modal-header">
          <h2>Select Questions from Existing Metrics</h2>
          <button type="button" class="qt-modal-close" @click="closeMetricSelector">&times;</button>
        </div>
        <div class="qt-modal-body">
          <div v-if="staticMetricsLoading" class="qt-modal-loading">Loading metrics...</div>
          <div v-else-if="staticMetricsError" class="qt-error">
            {{ staticMetricsError }}
            <button type="button" class="qt-mini qt-retry" @click="loadStaticMetricQuestions(true)">Retry</button>
          </div>
          <div v-else-if="groupedMetricQuestions.length === 0" class="qt-hint">
            No static questionnaires found. You can still create new questions manually.
          </div>
          <div v-else class="qt-metric-list">
            <div
              v-for="metric in groupedMetricQuestions"
              :key="metric.metricName"
              class="qt-metric-item"
              :class="{ 'qt-metric-partial': isMetricPartiallySelected(metric.metricName) }"
            >
              <div class="qt-metric-header">
                <label class="qt-metric-checkbox">
                  <input
                    type="checkbox"
                    :checked="isMetricFullySelected(metric.metricName)"
                    :data-partial="isMetricPartiallySelected(metric.metricName)"
                    @change="toggleMetricSelection(metric.metricName, $event.target.checked)"
                  />
                  <span>{{ metric.metricName }}</span>
                </label>
                <button
                  type="button"
                  class="qt-mini qt-toggle"
                  @click="toggleMetricExpansion(metric.metricName)"
                >
                  {{ expandedMetrics.includes(metric.metricName) ? 'Hide' : 'Show' }} ({{ metric.questions.length }})
                </button>
              </div>
              <div
                v-show="expandedMetrics.includes(metric.metricName)"
                class="qt-metric-questions"
              >
                <label
                  v-for="question in metric.questions"
                  :key="question.question_id"
                  class="qt-question-checkbox"
                >
                  <input
                    type="checkbox"
                    :value="String(question.question_id)"
                    v-model="selectedStaticQuestionIds"
                  />
                  <span class="qt-question-text">{{ question.question_text }}</span>
                </label>
              </div>
            </div>
          </div>
        </div>
        <div class="qt-modal-footer">
          <button type="button" class="qt-secondary" @click="closeMetricSelector">Cancel</button>
          <button type="button" class="qt-primary" @click="applySelectedStaticQuestions" :disabled="selectedStaticQuestionIds.length === 0">
            Apply ({{ selectedStaticQuestionIds.length }})
          </button>
        </div>
      </div>
    </div>
  </div>
  
</template>

<script setup>
import { reactive, ref, onMounted, computed, watch, onBeforeUnmount } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import apiClient from '@/config/axios'
import apiService from '@/services/api'
import { PopupService } from '@/popup/popupService'

const route = useRoute()
const router = useRouter()

const TEMPLATE_TYPE_CHOICES = ['STATIC', 'DYNAMIC', 'ASSESSMENT', 'EVALUATION', 'TEST']
const MODULE_TYPE_CHOICES = ['VENDOR', 'CONTRACT', 'PLANS', 'SLA', 'AUDIT', 'GENERAL']
const STATUS_CHOICES = ['DRAFT', 'ACTIVE', 'IN_REVIEW', 'APPROVED', 'ARCHIVED', 'DEPRECATED']
const ANSWER_TYPE_CHOICES = ['TEXT', 'TEXTAREA', 'NUMBER', 'BOOLEAN', 'MULTIPLE_CHOICE', 'CHECKBOX', 'RATING', 'SCALE', 'DATE', 'YES_NO']

const form = reactive({
  template_name: '',
  template_description: '',
  template_version: '1.0',
  template_type: 'STATIC',
  module_type: 'GENERAL',
  module_subtype: '',
  approval_required: false,
  is_active: true,
  status: 'DRAFT',
})

const questions = ref([])
const submitting = ref(false)
const successMessage = ref('')
const submitError = ref('')
const importNotice = ref('')
let importNoticeTimer = null

// Store query params for auto-filling
const prefilledMetricName = ref('')
const prefilledTermId = ref('')
const prefilledTermCategory = ref('')
const prefilledContractId = ref('')
const returnTo = ref('')

// Static questionnaires for SLA metrics
const staticQuestionnaires = ref([])
const staticMetricsLoading = ref(false)
const staticMetricsError = ref('')
const showMetricSelector = ref(false)
const selectedStaticQuestionIds = ref([])
const expandedMetrics = ref([])

const groupedMetricQuestions = computed(() => {
  if (!staticQuestionnaires.value.length) return []
  const map = new Map()
  staticQuestionnaires.value.forEach((q) => {
    if (!q.metric_name) return
    const key = q.metric_name.trim()
    if (!key) return
    if (!map.has(key)) {
      map.set(key, [])
    }
    map.get(key).push(q)
  })

  return Array.from(map.entries())
    .map(([metricName, questions]) => ({
      metricName,
      questions: questions
        .slice()
        .sort((a, b) => Number(a.question_id) - Number(b.question_id)),
    }))
    .sort((a, b) => a.metricName.localeCompare(b.metricName))
})

// Initialize form with query parameters
onMounted(() => {
  // Check for module_type in query params
  if (route.query.module_type) {
    form.module_type = route.query.module_type
  }
  
  // Check for metric_name in query params (for SLA)
  if (route.query.metric_name) {
    prefilledMetricName.value = route.query.metric_name
    form.template_name = `${route.query.metric_name} Questionnaire`
    
    // Add first question with metric name pre-filled
    const firstQuestion = newQuestion()
    firstQuestion.metric_name = route.query.metric_name
    questions.value.push(firstQuestion)
  }
  
  // Check for term_id and term_category in query params (for CONTRACT)
  if (route.query.term_id) {
    prefilledTermId.value = route.query.term_id
  }
  if (route.query.term_category) {
    prefilledTermCategory.value = route.query.term_category
  }
  if (route.query.contract_id) {
    prefilledContractId.value = route.query.contract_id
  }
  
  // Check for return_to parameter
  if (route.query.return_to) {
    returnTo.value = route.query.return_to
  }
  
  // Check if we're in edit mode and have existing questions to load
  // This should be checked BEFORE adding a new empty question
  const isEditMode = route.query.edit_mode === 'true' && form.module_type === 'CONTRACT'
  let hasLoadedEditQuestions = false
  
  if (isEditMode) {
    const editData = sessionStorage.getItem('questionnaire_edit_data')
    if (editData) {
      try {
        const parsedData = JSON.parse(editData)
        console.log('📋 Loading existing questions for editing:', parsedData)
        
        // Update template name if we have term_title
        if (parsedData.term_title) {
          form.template_name = `${parsedData.term_title} Questionnaire`
        }
        
        // Pre-populate questions from edit data
        if (parsedData.questions && Array.isArray(parsedData.questions) && parsedData.questions.length > 0) {
          questions.value = parsedData.questions.map(q => ({
            _key: `${Date.now()}-${Math.random()}-${Math.random()}`,
            question_text: q.question_text || '',
            help_text: q.help_text || '',
            question_category: q.question_category || '',
            answer_type: q.answer_type || 'TEXT',
            is_required: q.is_required !== undefined ? q.is_required : true,
            weightage: q.weightage !== undefined ? q.weightage : undefined,
            term_id: q.term_id || parsedData.term_id || null,
            allow_document_upload: q.allow_document_upload !== undefined ? q.allow_document_upload : false,
            _optionsString: q._optionsString || (q.options ? q.options.join(', ') : ''),
            options: q.options || [],
            metric_name: q.metric_name || null
          }))
          console.log(`✅ Pre-populated ${questions.value.length} questions for editing`)
        }
        
        // Clear the edit data from sessionStorage after loading
        sessionStorage.removeItem('questionnaire_edit_data')
        hasLoadedEditQuestions = true
      } catch (error) {
        console.error('Error loading questionnaire edit data:', error)
      }
    }
  }
  
  // Only add a new empty question if we're NOT in edit mode or if no questions were loaded
  if (route.query.term_title && form.module_type === 'CONTRACT' && !hasLoadedEditQuestions) {
    form.template_name = `${route.query.term_title} Questionnaire`
    
    // Add first question with term_id pre-filled
    const firstQuestion = newQuestion()
    if (prefilledTermId.value) {
      firstQuestion.term_id = prefilledTermId.value
    }
    questions.value.push(firstQuestion)
  }

  if (form.module_type === 'SLA') {
    loadStaticMetricQuestions()
  }
})

onBeforeUnmount(() => {
  if (importNoticeTimer) {
    clearTimeout(importNoticeTimer)
    importNoticeTimer = null
  }
})

watch(
  () => form.module_type,
  (newValue, oldValue) => {
    if (newValue === 'SLA' && oldValue !== 'SLA') {
      loadStaticMetricQuestions()
    }
    if (newValue !== 'SLA') {
      closeMetricSelector()
    }
  }
)

function getNextQuestionnaireId() {
  const key = 'qt_next_qid'
  const raw = localStorage.getItem(key)
  let next = parseInt(raw || '0', 10)
  if (!next || next < 100) {
    next = 100
  }
  localStorage.setItem(key, String(next + 1))
  return next
}

function resetForm() {
  form.template_name = ''
  form.template_description = ''
  form.template_version = '1.0'
  form.template_type = 'STATIC'
  form.module_type = 'GENERAL'
  form.module_subtype = ''
  form.approval_required = false
  form.is_active = true
  form.status = 'DRAFT'
  questions.value = []
  successMessage.value = ''
  submitError.value = ''
}

function newQuestion() {
  return {
    _key: `${Date.now()}-${Math.random()}`,
    question_text: '',
    question_category: '',
    answer_type: 'TEXT',
    is_required: true,
    weightage: undefined,
    metric_name: '',
    term_id: null,
    allow_document_upload: false,
    _optionsString: '',
    options: [],
    help_text: '',
  }
}

function addQuestion() {
  const q = newQuestion()
  // Pre-fill metric_name if we have one from query params (for SLA)
  if (prefilledMetricName.value && form.module_type === 'SLA') {
    q.metric_name = prefilledMetricName.value
  }
  // Pre-fill term_id if we have one from query params (for CONTRACT)
  if (prefilledTermId.value && form.module_type === 'CONTRACT') {
    q.term_id = prefilledTermId.value
  }
  questions.value.push(q)
}

function duplicateQuestion(index) {
  const base = questions.value[index]
  const copy = JSON.parse(JSON.stringify(base))
  copy._key = `${Date.now()}-${Math.random()}`
  questions.value.splice(index + 1, 0, copy)
}

function removeQuestion(index) {
  questions.value.splice(index, 1)
}

function setImportNotice(message, duration = 4000) {
  importNotice.value = message
  if (importNoticeTimer) {
    clearTimeout(importNoticeTimer)
  }
  if (duration > 0) {
    importNoticeTimer = setTimeout(() => {
      importNotice.value = ''
      importNoticeTimer = null
    }, duration)
  } else {
    importNoticeTimer = null
  }
}

async function loadStaticMetricQuestions(force = false) {
  if (staticMetricsLoading.value) return
  if (!force && staticQuestionnaires.value.length) return

  staticMetricsLoading.value = true
  staticMetricsError.value = ''

  try {
    const response = await apiService.getAllStaticQuestionnaires()
    const questionnaires = response?.results || response || []
    staticQuestionnaires.value = Array.isArray(questionnaires) ? questionnaires : []
    if (!expandedMetrics.value.length) {
      expandedMetrics.value = groupedMetricQuestions.value.map((metric) => metric.metricName)
    }
  } catch (error) {
    console.error('Error loading static questionnaires:', error)
    staticMetricsError.value = error?.response?.data?.message || error?.message || 'Failed to load static questionnaires.'
    staticQuestionnaires.value = []
  } finally {
    staticMetricsLoading.value = false
  }
}

function openMetricSelector() {
  if (form.module_type !== 'SLA') return
  if (!staticQuestionnaires.value.length && !staticMetricsLoading.value) {
    loadStaticMetricQuestions()
  } else if (!expandedMetrics.value.length) {
    expandedMetrics.value = groupedMetricQuestions.value.map((metric) => metric.metricName)
  }
  showMetricSelector.value = true
}

function closeMetricSelector() {
  showMetricSelector.value = false
  selectedStaticQuestionIds.value = []
  expandedMetrics.value = []
}

function toggleMetricExpansion(metricName) {
  if (expandedMetrics.value.includes(metricName)) {
    expandedMetrics.value = expandedMetrics.value.filter((name) => name !== metricName)
  } else {
    expandedMetrics.value = [...expandedMetrics.value, metricName]
  }
}

function isMetricFullySelected(metricName) {
  const metric = groupedMetricQuestions.value.find((m) => m.metricName === metricName)
  if (!metric || metric.questions.length === 0) return false
  const ids = metric.questions.map((question) => String(question.question_id))
  return ids.every((id) => selectedStaticQuestionIds.value.includes(id))
}

function isMetricPartiallySelected(metricName) {
  const metric = groupedMetricQuestions.value.find((m) => m.metricName === metricName)
  if (!metric || metric.questions.length === 0) return false
  const ids = metric.questions.map((question) => String(question.question_id))
  const selectedCount = ids.filter((id) => selectedStaticQuestionIds.value.includes(id)).length
  return selectedCount > 0 && selectedCount < ids.length
}

function toggleMetricSelection(metricName, isChecked) {
  const metric = groupedMetricQuestions.value.find((m) => m.metricName === metricName)
  if (!metric) return
  const ids = metric.questions.map((question) => String(question.question_id))

  if (isChecked) {
    const merged = new Set([...selectedStaticQuestionIds.value, ...ids])
    selectedStaticQuestionIds.value = Array.from(merged)
  } else {
    selectedStaticQuestionIds.value = selectedStaticQuestionIds.value.filter((id) => !ids.includes(id))
  }
}

function applySelectedStaticQuestions() {
  if (!selectedStaticQuestionIds.value.length) {
    setImportNotice('Select at least one question to import.', 3000)
    return
  }

  const selectedIdSet = new Set(selectedStaticQuestionIds.value)
  const selectedQuestions = staticQuestionnaires.value.filter((question) =>
    selectedIdSet.has(String(question.question_id))
  )

  const existingSignatures = new Set(
    questions.value.map((question) => `${(question.metric_name || '').trim().toLowerCase()}::${(question.question_text || '').trim().toLowerCase()}`)
  )

  let addedCount = 0
  selectedQuestions.forEach((staticQuestion) => {
    const signature = `${(staticQuestion.metric_name || '').trim().toLowerCase()}::${(staticQuestion.question_text || '').trim().toLowerCase()}`
    if (!staticQuestion.question_text || existingSignatures.has(signature)) {
      return
    }
    const builtQuestion = buildQuestionFromStatic(staticQuestion)
    questions.value.push(builtQuestion)
    existingSignatures.add(signature)
    addedCount += 1
  })

  if (addedCount > 0) {
    setImportNotice(`${addedCount} question${addedCount === 1 ? '' : 's'} imported from static questionnaires.`)
  } else {
    setImportNotice('No new questions were imported (duplicates were skipped).')
  }

  closeMetricSelector()
}

function buildQuestionFromStatic(staticQuestion) {
  return {
    _key: `${Date.now()}-${Math.random()}`,
    question_text: staticQuestion.question_text || '',
    question_category: '',
    answer_type: mapAnswerType(staticQuestion.question_type),
    is_required: Boolean(staticQuestion.is_required),
    weightage:
      staticQuestion.scoring_weightings !== undefined && staticQuestion.scoring_weightings !== null
        ? Number(staticQuestion.scoring_weightings)
        : undefined,
    metric_name: staticQuestion.metric_name || '',
    term_id: null,
    allow_document_upload: false,
    _optionsString: '',
    options: [],
    help_text: '',
  }
}

function mapAnswerType(rawType) {
  if (!rawType) return 'TEXT'
  const normalized = rawType.toString().trim().toLowerCase()
  switch (normalized) {
    case 'text':
      return 'TEXT'
    case 'number':
      return 'NUMBER'
    case 'boolean':
      return 'BOOLEAN'
    case 'multiple_choice':
      return 'MULTIPLE_CHOICE'
    default:
      return 'TEXT'
  }
}

async function handleSubmit() {
  submitError.value = ''
  successMessage.value = ''
  if (!form.template_name.trim()) {
    submitError.value = 'Template name is required'
    return
  }

  // Build questions JSON from form fields
  // Generate a unique numeric questionnaire_id starting from 100 (one per submission)
  const questionnaireId = getNextQuestionnaireId()
  const builtQuestions = questions.value.map((q, i) => {
    const opts = (q._optionsString || '').trim()
      ? (q._optionsString || '')
          .split(',')
          .map(s => s.trim())
          .filter(Boolean)
      : []
    return {
      question_id: i + 1,
      questionnaire_id: questionnaireId,
      display_order: i + 1,
      question_text: q.question_text,
      question_category: form.module_type === 'VENDOR' ? (q.question_category || undefined) : undefined,
      answer_type: q.answer_type,
      is_required: Boolean(q.is_required),
      weightage: q.weightage != null && q.weightage !== '' ? Number(q.weightage) : undefined,
      metric_name: form.module_type === 'SLA' ? (q.metric_name || undefined) : undefined,
      term_id: form.module_type === 'CONTRACT'
        ? ((q.term_id !== undefined && q.term_id !== null && String(q.term_id).trim() !== '') ? String(q.term_id).trim() : null)
        : null,
      allow_document_upload: Boolean(q.allow_document_upload),
      options: opts,
      help_text: q.help_text || undefined,
      created_at: new Date().toISOString(),
    }
  })

  // Set status to ACTIVE if is_active is checked
  const finalStatus = form.is_active ? 'ACTIVE' : form.status
  
  const payload = {
    ...form,
    status: finalStatus, // Use ACTIVE if is_active is checked, otherwise use form.status
    module_subtype: form.module_subtype || null,
    template_questions_json: builtQuestions,
  }

  try {
    submitting.value = true
    const { data } = await apiClient.post('/api/tprm/bcpdrp/questionnaire-templates/save/', payload)
    
    const responseData = data?.data || data
    const questionsCreated = responseData?.questions_created || 0
    const contractQuestionsCreated = responseData?.contract_questions_created || 0
    
     // Prepare success message
     let successMsg = ''
    if (form.module_type === 'SLA' && questionsCreated > 0) {
      successMsg = `Saved successfully! Template ID: ${responseData?.template_id ?? 'N/A'} | ${questionsCreated} question(s) added to SLA metrics.`
    } else if (form.module_type === 'CONTRACT' && contractQuestionsCreated > 0) {
      successMsg = `Saved successfully! Template ID: ${responseData?.template_id ?? 'N/A'} | ${contractQuestionsCreated} question(s) added to contract static questionnaires.`
    } else {
      successMsg = `Saved successfully. Template ID: ${responseData?.template_id ?? 'N/A'}`
    }
    
    // If we came from SLA creation, redirect back after a short delay
    if (returnTo.value === 'sla-create') {
      const redirectMsg = successMsg + ' Redirecting back to SLA creation...'
      successMessage.value = redirectMsg
      // Show success popup with redirect message
      PopupService.success(redirectMsg, 'Template Saved')
      setTimeout(() => {
        router.push('/slas/create')
      }, 2000)
    } else if (returnTo.value === 'contract-create') {
      // If we came from contract creation, redirect back after a short delay
      // Include ?tab=terms to ensure the Terms tab is active
      const redirectMsg = successMsg + ' Redirecting back to contract creation...'
      successMessage.value = redirectMsg
      // Show success popup with redirect message
      PopupService.success(redirectMsg, 'Template Saved')
      setTimeout(() => {
        router.push('/contracts/create?tab=terms')
      }, 2000)
    } else if (returnTo.value === 'contract-amendment') {
      const redirectMsg = successMsg + ' Redirecting back to contract amendment...'
      successMessage.value = redirectMsg
      // Show success popup with redirect message
      PopupService.success(redirectMsg, 'Template Saved')
      const contractId = prefilledContractId.value || route.query.contract_id
      setTimeout(() => {
        if (contractId) {
          router.push(`/contracts/${contractId}/create-amendment?tab=terms&from=questionnaire-templates`)
        } else {
          router.back()
        }
      }, 2000)
    } else if (returnTo.value === 'contract-subcontract-advanced') {
      const redirectMsg = successMsg + ' Redirecting back to subcontract creation...'
      successMessage.value = redirectMsg
      // Show success popup with redirect message
      PopupService.success(redirectMsg, 'Template Saved')
      const contractId = prefilledContractId.value || route.query.contract_id
      setTimeout(() => {
        if (contractId) {
          router.push(`/contracts/${contractId}/create-subcontract-advanced?tab=terms&from=questionnaire-templates`)
        } else {
          router.back()
        }
      }, 2000)
    } else if (returnTo.value === 'subcontract-create') {
      const redirectMsg = successMsg + ' Redirecting back to subcontract creation...'
      successMessage.value = redirectMsg
      // Show success popup with redirect message
      PopupService.success(redirectMsg, 'Template Saved')
      const parentContractId = route.query.parent_contract_id
      setTimeout(() => {
        if (parentContractId) {
          router.push(`/contracts/${parentContractId}/subcontract?tab=terms&from=questionnaire-templates`)
        } else {
          router.push('/contracts/create-subcontract?tab=terms&from=questionnaire-templates')
        }
      }, 2000)
    } else {
      // Show success popup when not redirecting
      PopupService.success(successMsg, 'Template Saved')
      successMessage.value = successMsg
      resetForm()
    }
  } catch (err) {
    const errorMsg = err?.response?.data?.message || err?.message || 'Failed to save template'
    submitError.value = errorMsg
    
    // Show error popup
    PopupService.error(errorMsg, 'Save Failed')
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.qt-container {
  max-width: 100%;
  width: 100%;
  margin: 0;
  padding: 24px 32px;
}

.qt-title {
  font-size: 28px;
  font-weight: 700;
  color: #0f172a; /* slate-900 */
  margin-bottom: 12px;
}

.qt-info-banner {
  background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%); /* blue-100 to blue-200 */
  border: 1px solid #93c5fd; /* blue-300 */
  border-radius: 10px;
  padding: 16px;
  margin-bottom: 20px;
  box-shadow: 0 2px 8px rgba(59, 130, 246, 0.1);
}

.qt-info-content {
  display: flex;
  align-items: flex-start;
  gap: 12px;
}

.qt-info-icon {
  width: 24px;
  height: 24px;
  color: #1e40af; /* blue-800 */
  flex-shrink: 0;
}

.qt-info-title {
  font-size: 14px;
  font-weight: 600;
  color: #1e3a8a; /* blue-900 */
  margin-bottom: 4px;
}

.qt-info-subtitle {
  font-size: 13px;
  color: #1e40af; /* blue-800 */
}

.qt-form {
  background: #ffffff;
  border: 1px solid #e5e7eb; /* gray-200 */
  border-radius: 10px;
  padding: 18px;
  box-shadow: 0 3px 12px rgba(2, 6, 23, 0.05);
  width: 100%;
}

.qt-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.qt-field {
  display: flex;
  flex-direction: column;
}

.qt-field label {
  font-weight: 600;
  color: #334155; /* slate-600 */
  margin-bottom: 4px;
  font-size: 12px;
}

.qt-required {
  color: #dc2626;
  margin-left: 2px;
}

input[type="text"], input[type="number"], select, textarea {
  border: 1px solid #d1d5db; /* gray-300 */
  background: #ffffff;
  border-radius: 8px;
  padding: 8px 10px;
  font-size: 13px;
  outline: none;
  transition: border-color 0.15s ease, box-shadow 0.15s ease;
}

input[type="text"]:focus, input[type="number"]:focus, select:focus, textarea:focus {
  border-color: #3b82f6; /* blue-500 */
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.2);
}

.qt-checkboxes {
  display: flex;
  align-items: center;
  gap: 12px;
}

.qt-checkbox {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  color: #334155;
}

.qt-label-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 10px; /* prevent overlap with previous textarea */
  gap: 8px;
}

.qt-question-controls {
  display: flex;
  align-items: center;
  gap: 8px;
}

.qt-import-notice {
  margin-top: 6px;
  font-size: 12px;
  color: #0369a1; /* sky-700 */
}

.qt-code {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
}

.qt-hint {
  font-size: 13px;
  color: #64748b; /* slate-500 */
  margin-bottom: 6px;
}

.qt-question {
  border: 1px solid #e2e8f0; /* slate-200 */
  border-radius: 10px;
  padding: 12px;
  margin-top: 10px;
  background: #f8fafc; /* slate-50 */
}

.qt-question-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}

.qt-question-title {
  font-weight: 600;
  color: #0f172a;
  font-size: 13px;
}

.qt-question-actions {
  display: flex;
  gap: 6px;
}

.qt-danger {
  border-color: #fecaca;
  color: #991b1b;
}

.qt-actions {
  display: flex;
  gap: 10px;
  margin-top: 10px;
}

.qt-primary {
  background-color: #2563eb; /* blue-600 */
  color: #ffffff;
  border: 1px solid #1d4ed8; /* blue-700 */
  padding: 10px 16px;
  border-radius: 10px;
  font-weight: 600;
  font-size: 14px;
  cursor: pointer;
  transition: background-color 0.15s ease, box-shadow 0.15s ease;
}

.qt-primary:hover {
  background-color: #1d4ed8; /* blue-700 */
  box-shadow: 0 6px 16px rgba(29, 78, 216, 0.15);
}

.qt-primary:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.qt-secondary {
  background-color: #f8fafc; /* slate-50 */
  color: #0f172a;
  border: 1px solid #e2e8f0; /* slate-200 */
  padding: 10px 16px;
  border-radius: 10px;
  font-weight: 600;
  font-size: 14px;
  cursor: pointer;
  transition: background-color 0.15s ease, border-color 0.15s ease;
}

.qt-secondary:hover {
  background-color: #f1f5f9; /* slate-100 */
  border-color: #cbd5e1; /* slate-300 */
}

.qt-mini {
  background: #ffffff;
  border: 1px solid #e2e8f0; /* slate-200 */
  color: #334155;
  font-size: 13px;
  padding: 8px 10px;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  transition: background-color 0.15s ease, border-color 0.15s ease;
}

.qt-mini:hover {
  background-color: #f8fafc;
  border-color: #cbd5e1; /* slate-300 */
}

.qt-import {
  background: #eff6ff; /* blue-50 */
  border-color: #bfdbfe; /* blue-200 */
  color: #1d4ed8; /* blue-700 */
}

.qt-import:disabled {
  opacity: 0.7;
  cursor: wait;
}

.qt-toggle {
  background: #f1f5f9; /* slate-100 */
  border-color: #cbd5e1; /* slate-300 */
  color: #1e293b; /* slate-800 */
}

.qt-retry {
  margin-left: 8px;
  background: #fff7ed; /* orange-50 */
  border-color: #fdba74; /* orange-300 */
  color: #9a3412; /* orange-800 */
}

/* Emphasize add/remove buttons */
.qt-add {
  background: #ecfdf5; /* green-50 */
  border-color: #86efac; /* green-300 */
  color: #065f46; /* green-800 */
}

.qt-add:hover {
  background: #d1fae5; /* green-100 */
  border-color: #34d399; /* green-400 */
}

.qt-remove {
  background: #fef2f2; /* red-50 */
  border-color: #fecaca; /* red-200 */
  color: #991b1b; /* red-800 */
}

.qt-remove:hover {
  background: #fee2e2; /* red-100 */
  border-color: #fca5a5; /* red-300 */
}

.qt-success {
  color: #065f46;
  background: #ecfdf5;
  border: 1px solid #a7f3d0;
  padding: 10px 12px;
  border-radius: 10px;
  margin-top: 12px;
}

.qt-error {
  color: #991b1b;
  background: #fef2f2;
  border: 1px solid #fecaca;
  padding: 10px 12px;
  border-radius: 10px;
  margin-top: 8px;
}

.qt-modal-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.5); /* slate-900/50 */
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 60;
  padding: 16px;
}

.qt-modal {
  background: #ffffff;
  border-radius: 12px;
  max-width: 720px;
  width: 100%;
  box-shadow: 0 20px 40px rgba(15, 23, 42, 0.2);
  display: flex;
  flex-direction: column;
  max-height: 90vh;
}

.qt-modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  border-bottom: 1px solid #e2e8f0;
}

.qt-modal-header h2 {
  font-size: 18px;
  font-weight: 600;
  color: #0f172a;
  margin: 0;
}

.qt-modal-close {
  background: none;
  border: none;
  font-size: 24px;
  line-height: 1;
  cursor: pointer;
  color: #475569;
  padding: 0 4px;
}

.qt-modal-body {
  padding: 16px 20px;
  overflow-y: auto;
  flex: 1;
}

.qt-modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  padding: 14px 20px;
  border-top: 1px solid #e2e8f0;
  background: #f8fafc;
}

.qt-modal-loading {
  text-align: center;
  padding: 20px 0;
  color: #1d4ed8;
  font-weight: 500;
}

.qt-metric-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.qt-metric-item {
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  background: #f8fafc;
}

.qt-metric-partial {
  border-color: #fbbf24; /* amber-400 */
  box-shadow: inset 0 0 0 1px rgba(251, 191, 36, 0.2);
}

.qt-metric-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 12px;
  gap: 12px;
}

.qt-metric-checkbox {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  color: #0f172a;
  font-size: 13px;
}

.qt-metric-checkbox input[data-partial="true"] {
  accent-color: #f59e0b; /* amber-500 */
}

.qt-metric-questions {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 10px 12px 14px;
  background: #fff;
  border-top: 1px solid #e2e8f0;
}

.qt-question-checkbox {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  color: #1e293b;
  font-size: 13px;
}

.qt-question-text {
  flex: 1;
}

@media (max-width: 768px) {
  .qt-grid {
    grid-template-columns: 1fr;
  }
}

@media (min-width: 1280px) {
  /* Use 3 columns on wide screens to better fill space */
  .qt-grid {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}
</style>


