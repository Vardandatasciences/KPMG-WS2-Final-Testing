import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { getTprmApiUrl } from '@/utils/backendEnv'

export const useQuestionnaireStore = defineStore('questionnaire', () => {
  // State
  const questionnaires = ref([])
  const currentQuestionnaire = ref({
    questionnaire_name: '',
    questionnaire_type: '',
    description: '',
    vendor_category_id: '',
    vendor_id: '',
    version: '1.0',
    status: 'DRAFT'
  })
  const questions = ref([])
  const vendors = ref([])
  const rfpData = ref([])
  const screeningData = ref([])
  const loading = ref(false)
  const error = ref(null)

  // API Base URL - use correct path: /api/tprm/vendor-questionnaire/
  const API_BASE = getTprmApiUrl('vendor-questionnaire')

  // Computed
  const getQuestionnaires = computed(() => questionnaires.value)
  const getCurrentQuestionnaire = computed(() => currentQuestionnaire.value)
  const getQuestions = computed(() => questions.value)
  const getVendors = computed(() => vendors.value)
  const getRFPData = computed(() => rfpData.value)
  const getScreeningData = computed(() => screeningData.value)
  const isLoading = computed(() => loading.value)
  const getError = computed(() => error.value)

  // Helper function for API calls with JWT authentication
  const apiCall = async (url, options = {}) => {
    try {
      // Get JWT token from localStorage
      const token = localStorage.getItem('session_token')
      
      const response = await fetch(url, {
        headers: {
          'Content-Type': 'application/json',
          // Add JWT authentication header
          ...(token && { 'Authorization': `Bearer ${token}` }),
          ...options.headers
        },
        ...options
      })

      // Handle 401 Unauthorized
      if (response.status === 401) {
        localStorage.removeItem('session_token')
        localStorage.removeItem('access_token')
        localStorage.removeItem('refresh_token')
        localStorage.removeItem('current_user')
        if (window.location.pathname !== '/login') {
          window.location.href = '/login'
        }
        throw new Error('Authentication required')
      }

      // Handle 403 Forbidden
      if (response.status === 403) {
        const errorData = await response.json().catch(() => ({}))
        const errorMessage = errorData?.error || errorData?.message || 'You do not have permission to access this resource.'
        sessionStorage.setItem('access_denied_error', JSON.stringify({
          message: errorMessage,
          code: '403',
          timestamp: new Date().toISOString(),
          path: window.location.pathname
        }))
        if (window.location.pathname !== '/access-denied') {
          window.location.href = '/access-denied'
        }
        throw new Error(errorMessage)
      }

      if (!response.ok) {
        const errorText = await response.text().catch(() => '')
        console.error(`API Error [${response.status}]: ${url}`, errorText)
        throw new Error(`HTTP error! status: ${response.status} - ${errorText.substring(0, 100)}`)
      }

      const data = await response.json()
      return data
    } catch (err) {
      error.value = err.message
      throw err
    }
  }

  // Actions
  const fetchQuestionnaires = async () => {
    loading.value = true
    error.value = null
    try {
      const data = await apiCall(`${API_BASE}/questionnaires/`)
      questionnaires.value = data.results || data
    } catch (err) {
      console.error('Failed to fetch questionnaires:', err)
    } finally {
      loading.value = false
    }
  }

  const fetchQuestionnaire = async (id) => {
    loading.value = true
    error.value = null
    try {
      const data = await apiCall(`${API_BASE}/questionnaires/${id}/`)
      currentQuestionnaire.value = data
      questions.value = data.questions || []
      return data
    } catch (err) {
      console.error('Failed to fetch questionnaire:', err)
      // If questionnaire doesn't exist, reset to new questionnaire
      if (err.message.includes('404') || err.message.includes('Not Found')) {
        console.warn(`Questionnaire with ID ${id} does not exist. Resetting to new questionnaire.`)
        resetCurrentQuestionnaire()
        return null
      }
      throw err
    } finally {
      loading.value = false
    }
  }

  const createQuestionnaire = async (questionnaireData) => {
    loading.value = true
    error.value = null
    try {
      console.log('QuestionnaireStore - createQuestionnaire called with:', questionnaireData)
      console.log('QuestionnaireStore - vendor_id in data:', questionnaireData.vendor_id, 'Type:', typeof questionnaireData.vendor_id)
      console.log('QuestionnaireStore - vendor_category_id in data:', questionnaireData.vendor_category_id, 'Type:', typeof questionnaireData.vendor_category_id)
      
      // Ensure numeric fields are properly formatted
      const processedData = { ...questionnaireData }
      
      // Process vendor_id
      if (processedData.vendor_id === '' || processedData.vendor_id === null || processedData.vendor_id === undefined) {
        processedData.vendor_id = null
      } else {
        processedData.vendor_id = parseInt(processedData.vendor_id, 10)
      }
      
      // Process vendor_category_id - must be integer or null, NOT empty string
      if (processedData.vendor_category_id === '' || processedData.vendor_category_id === null || processedData.vendor_category_id === undefined) {
        processedData.vendor_category_id = null
      } else {
        processedData.vendor_category_id = parseInt(processedData.vendor_category_id, 10)
      }
      
      console.log('QuestionnaireStore - Processed data:', processedData)
      console.log('QuestionnaireStore - Processed vendor_id:', processedData.vendor_id, 'Type:', typeof processedData.vendor_id)
      console.log('QuestionnaireStore - Processed vendor_category_id:', processedData.vendor_category_id, 'Type:', typeof processedData.vendor_category_id)
      
      const data = await apiCall(`${API_BASE}/questionnaires/`, {
        method: 'POST',
        body: JSON.stringify(processedData)
      })
      currentQuestionnaire.value = data
      questionnaires.value.push(data)
      return data
    } catch (err) {
      console.error('Failed to create questionnaire:', err)
      throw err
    } finally {
      loading.value = false
    }
  }

  const updateQuestionnaire = async (id, questionnaireData) => {
    loading.value = true
    error.value = null
    try {
      // Process numeric fields to ensure proper formatting
      const processedData = { ...questionnaireData }
      
      // Process vendor_id
      if (processedData.vendor_id === '' || processedData.vendor_id === null || processedData.vendor_id === undefined) {
        processedData.vendor_id = null
      } else if (typeof processedData.vendor_id !== 'number') {
        processedData.vendor_id = parseInt(processedData.vendor_id, 10)
      }
      
      // Process vendor_category_id
      if (processedData.vendor_category_id === '' || processedData.vendor_category_id === null || processedData.vendor_category_id === undefined) {
        processedData.vendor_category_id = null
      } else if (typeof processedData.vendor_category_id !== 'number') {
        processedData.vendor_category_id = parseInt(processedData.vendor_category_id, 10)
      }
      
      const data = await apiCall(`${API_BASE}/questionnaires/${id}/`, {
        method: 'PUT',
        body: JSON.stringify(processedData)
      })
      currentQuestionnaire.value = data
      
      // Update in list
      const index = questionnaires.value.findIndex(q => q.questionnaire_id === id)
      if (index !== -1) {
        questionnaires.value[index] = data
      }
      
      return data
    } catch (err) {
      console.error('Failed to update questionnaire:', err)
      // If questionnaire doesn't exist, suggest creating a new one
      if (err.message.includes('404') || err.message.includes('Not Found')) {
        console.warn(`Questionnaire with ID ${id} does not exist. You may need to create a new questionnaire.`)
        throw new Error(`Questionnaire with ID ${id} does not exist. Please create a new questionnaire.`)
      }
      throw err
    } finally {
      loading.value = false
    }
  }

  const saveQuestionnaireWithQuestions = async (id, questionnaireData, questionsData) => {
    loading.value = true
    error.value = null
    try {
      // Save questionnaire details first
      await updateQuestionnaire(id, questionnaireData)
      
      // Then save questions - clean up the questions data to match backend expectations
      const cleanedQuestions = questionsData.map(q => ({
        question_text: q.question_text || '',
        question_type: q.question_type || 'TEXT',
        question_category: q.question_category || '',
        is_required: q.is_required || false,
        display_order: q.display_order || 1,
        scoring_weight: q.scoring_weight || 1.0,
        options: q.options || {},
        conditional_logic: q.conditional_logic || {},
        help_text: q.help_text || ''
      }))
      
      const data = await apiCall(`${API_BASE}/questionnaires/${id}/update_questions/`, {
        method: 'PUT',
        body: JSON.stringify({ questions: cleanedQuestions })
      })
      
      questions.value = data.questions || []
      return data
    } catch (err) {
      console.error('Failed to save questionnaire with questions:', err)
      // If questionnaire doesn't exist, suggest creating a new one
      if (err.message.includes('404') || err.message.includes('Not Found')) {
        console.warn(`Questionnaire with ID ${id} does not exist. You may need to create a new questionnaire.`)
        throw new Error(`Questionnaire with ID ${id} does not exist. Please create a new questionnaire.`)
      }
      throw err
    } finally {
      loading.value = false
    }
  }

  const saveDraft = async (id, questionnaireData, questionsData) => {
    loading.value = true
    error.value = null
    try {
      // Process numeric fields properly
      const vendorId = questionnaireData.vendor_id
      const processedVendorId = (vendorId === '' || vendorId === null || vendorId === undefined) ? null : parseInt(vendorId, 10)
      
      const vendorCategoryId = questionnaireData.vendor_category_id
      const processedVendorCategoryId = (vendorCategoryId === '' || vendorCategoryId === null || vendorCategoryId === undefined) ? null : parseInt(vendorCategoryId, 10)
      
      console.log('QuestionnaireStore - saveDraft processing:', {
        vendor_id: { original: vendorId, processed: processedVendorId, type: typeof processedVendorId },
        vendor_category_id: { original: vendorCategoryId, processed: processedVendorCategoryId, type: typeof processedVendorCategoryId }
      })
      
      const data = await apiCall(`${API_BASE}/questionnaires/${id}/save_draft/`, {
        method: 'POST',
        body: JSON.stringify({
          questionnaire_name: questionnaireData.questionnaire_name,
          description: questionnaireData.description,
          questionnaire_type: questionnaireData.questionnaire_type,
          vendor_category_id: processedVendorCategoryId,
          vendor_id: processedVendorId,
          questions: questionsData
        })
      })
      
      currentQuestionnaire.value = data
      questions.value = data.questions || []
      return data
    } catch (err) {
      console.error('Failed to save draft:', err)
      throw err
    } finally {
      loading.value = false
    }
  }

  const activateQuestionnaire = async (id, questionnaireData, questionsData) => {
    loading.value = true
    error.value = null
    try {
      // Clean the questions data for submission
      const cleanedQuestions = questionsData.map(q => ({
        question_text: q.question_text || '',
        question_type: q.question_type || 'TEXT',
        question_category: q.question_category || '',
        is_required: q.is_required || false,
        display_order: q.display_order || 1,
        scoring_weight: q.scoring_weight || 1.0,
        options: q.options || {},
        conditional_logic: q.conditional_logic || {},
        help_text: q.help_text || ''
      }))
      
      // Process numeric fields properly
      const vendorId = questionnaireData.vendor_id
      const processedVendorId = (vendorId === '' || vendorId === null || vendorId === undefined) ? null : parseInt(vendorId, 10)
      
      const vendorCategoryId = questionnaireData.vendor_category_id
      const processedVendorCategoryId = (vendorCategoryId === '' || vendorCategoryId === null || vendorCategoryId === undefined) ? null : parseInt(vendorCategoryId, 10)
      
      console.log('QuestionnaireStore - activateQuestionnaire processing:', {
        vendor_id: { original: vendorId, processed: processedVendorId, type: typeof processedVendorId },
        vendor_category_id: { original: vendorCategoryId, processed: processedVendorCategoryId, type: typeof processedVendorCategoryId }
      })
      
      const data = await apiCall(`${API_BASE}/questionnaires/${id}/activate/`, {
        method: 'POST',
        body: JSON.stringify({
          questionnaire_name: questionnaireData.questionnaire_name,
          description: questionnaireData.description,
          questionnaire_type: questionnaireData.questionnaire_type,
          vendor_category_id: processedVendorCategoryId,
          vendor_id: processedVendorId,
          questions: cleanedQuestions
        })
      })
      
      currentQuestionnaire.value = data
      questions.value = data.questions || []
      
      // Update in list
      const index = questionnaires.value.findIndex(q => q.questionnaire_id === id)
      if (index !== -1) {
        questionnaires.value[index] = data
      }
      
      return data
    } catch (err) {
      console.error('Failed to activate questionnaire:', err)
      // If questionnaire doesn't exist, suggest creating a new one
      if (err.message.includes('404') || err.message.includes('Not Found')) {
        console.warn(`Questionnaire with ID ${id} does not exist. You may need to create a new questionnaire.`)
        throw new Error(`Questionnaire with ID ${id} does not exist. Please create a new questionnaire.`)
      }
      throw err
    } finally {
      loading.value = false
    }
  }

  const deleteQuestionnaire = async (id) => {
    loading.value = true
    error.value = null
    try {
      await apiCall(`${API_BASE}/questionnaires/${id}/`, {
        method: 'DELETE'
      })
      
      questionnaires.value = questionnaires.value.filter(q => q.questionnaire_id !== id)
      
      // Clear current if it was deleted
      if (currentQuestionnaire.value.questionnaire_id === id) {
        resetCurrentQuestionnaire()
      }
    } catch (err) {
      console.error('Failed to delete questionnaire:', err)
      throw err
    } finally {
      loading.value = false
    }
  }

  const addQuestion = (question) => {
    const newQuestion = {
      id: String(Date.now()),
      question_text: '',
      question_type: 'TEXT',
      question_category: '',
      is_required: false,
      display_order: questions.value.length + 1,
      scoring_weight: 1.0,
      options: {},
      conditional_logic: {},
      help_text: '',
      ...question
    }
    
    // Initialize options based on question type
    if (newQuestion.question_type === 'MULTIPLE_CHOICE' || newQuestion.question_type === 'CHECKBOX') {
      newQuestion.options.choices = ['Option 1', 'Option 2']
    } else if (newQuestion.question_type === 'RATING') {
      newQuestion.options.rating = {
        min: 1,
        max: 5,
        step: 1,
        labels: ''
      }
    } else if (newQuestion.question_type === 'FILE_UPLOAD') {
      newQuestion.options.file = {
        allowedTypes: 'pdf,doc,docx,jpg,jpeg,png',
        maxSize: 10,
        maxFiles: 1
      }
    } else if (newQuestion.question_type === 'NUMBER') {
      newQuestion.options.number = {
        min: null,
        max: null,
        step: null,
        unit: ''
      }
    }
    
    questions.value.push(newQuestion)
    return newQuestion
  }

  const removeQuestion = (id) => {
    questions.value = questions.value.filter(q => q.id !== id)
    // Reorder remaining questions
    questions.value.forEach((q, index) => {
      q.display_order = index + 1
    })
  }

  const updateQuestion = (id, updates) => {
    const index = questions.value.findIndex(q => q.id === id)
    if (index !== -1) {
      const question = questions.value[index]
      const updatedQuestion = { ...question, ...updates }
      
      // If question type is changing, initialize appropriate options
      if (updates.question_type && updates.question_type !== question.question_type) {
        if (!updatedQuestion.options) {
          updatedQuestion.options = {}
        }
        
        // Initialize options based on new question type
        if (updates.question_type === 'MULTIPLE_CHOICE' || updates.question_type === 'CHECKBOX') {
          updatedQuestion.options.choices = ['Option 1', 'Option 2']
        } else if (updates.question_type === 'RATING') {
          updatedQuestion.options.rating = {
            min: 1,
            max: 5,
            step: 1,
            labels: ''
          }
        } else if (updates.question_type === 'FILE_UPLOAD') {
          updatedQuestion.options.file = {
            allowedTypes: 'pdf,doc,docx,jpg,jpeg,png',
            maxSize: 10,
            maxFiles: 1
          }
        } else if (updates.question_type === 'NUMBER') {
          updatedQuestion.options.number = {
            min: null,
            max: null,
            step: null,
            unit: ''
          }
        }
      }
      
      questions.value[index] = updatedQuestion
    }
  }

  const resetCurrentQuestionnaire = () => {
    currentQuestionnaire.value = {
      questionnaire_name: '',
      questionnaire_type: '',
      description: '',
      vendor_category_id: '',
      vendor_id: '',
      version: '1.0',
      status: 'DRAFT'
    }
    questions.value = []
  }

  const updateQuestionnaireField = (field, value) => {
    currentQuestionnaire.value[field] = value
  }

  const clearError = () => {
    error.value = null
  }

  const getQuestionTypes = async () => {
    try {
      const data = await apiCall(`${API_BASE}/questionnaires/get_question_types/`)
      return data
    } catch (err) {
      console.error('Failed to fetch question types:', err)
      return []
    }
  }

  const getQuestionnaireTypes = async () => {
    try {
      const data = await apiCall(`${API_BASE}/questionnaires/get_questionnaire_types/`)
      return data
    } catch (err) {
      console.error('Failed to fetch questionnaire types:', err)
      return []
    }
  }

  const getVendorCategories = async () => {
    try {
      const data = await apiCall(`${API_BASE}/questionnaires/get_vendor_categories/`)
      return data
    } catch (err) {
      console.error('Failed to fetch vendor categories:', err)
      return []
    }
  }

  const fetchVendors = async () => {
    loading.value = true
    error.value = null
    try {
      const data = await apiCall(`${API_BASE}/questionnaires/get_vendors/`)
      vendors.value = data
      return data
    } catch (err) {
      console.error('Failed to fetch vendors:', err)
      return []
    } finally {
      loading.value = false
    }
  }

  const fetchVendorRFPData = async (vendorId) => {
    if (!vendorId) {
      console.log('fetchVendorRFPData - No vendor ID provided, clearing RFP data')
      rfpData.value = []
      return []
    }
    
    loading.value = true
    error.value = null
    try {
      console.log(`fetchVendorRFPData - Fetching RFP data for vendor_id: ${vendorId} (type: ${typeof vendorId})`)
      const url = `${API_BASE}/questionnaires/get_vendor_rfp_data/?vendor_id=${vendorId}`
      console.log(`fetchVendorRFPData - API URL: ${url}`)
      
      const data = await apiCall(url)
      console.log(`fetchVendorRFPData - API response received:`, data)
      console.log(`fetchVendorRFPData - Response type: ${Array.isArray(data) ? 'array' : typeof data}, Length: ${Array.isArray(data) ? data.length : 'N/A'}`)
      
      // Handle both array and object responses
      if (Array.isArray(data)) {
        rfpData.value = data
      } else if (data && Array.isArray(data.results)) {
        rfpData.value = data.results
      } else if (data && data.error) {
        console.error('fetchVendorRFPData - API returned error:', data.error)
        rfpData.value = []
        throw new Error(data.error)
      } else {
        console.warn('fetchVendorRFPData - Unexpected response format:', data)
        rfpData.value = []
      }
      
      console.log(`fetchVendorRFPData - Final rfpData.value length: ${rfpData.value.length}`)
      return rfpData.value
    } catch (err) {
      console.error('fetchVendorRFPData - Failed to fetch RFP data:', err)
      console.error('fetchVendorRFPData - Error details:', {
        message: err.message,
        stack: err.stack,
        response: err.response
      })
      rfpData.value = []
      return []
    } finally {
      loading.value = false
    }
  }

  const fetchVendorScreeningData = async (vendorId) => {
    if (!vendorId) {
      screeningData.value = []
      return []
    }
    
    loading.value = true
    error.value = null
    try {
      const data = await apiCall(`${API_BASE}/questionnaires/get_vendor_screening_data/?vendor_id=${vendorId}`)
      screeningData.value = data
      return data
    } catch (err) {
      console.error('Failed to fetch screening data:', err)
      screeningData.value = []
      return []
    } finally {
      loading.value = false
    }
  }

  const fetchTemplates = async (params = {}) => {
    loading.value = true
    error.value = null
    try {
      // Build query string
      const queryParams = new URLSearchParams(params).toString()
      const url = queryParams 
        ? `${API_BASE}/questionnaires/get_templates/?${queryParams}`
        : `${API_BASE}/questionnaires/get_templates/`
      
      console.log('Fetching templates from:', url)
      const data = await apiCall(url)
      console.log('Templates response:', data)
      return data.templates || data || []
    } catch (err) {
      console.error('Failed to fetch templates:', err)
      console.error('Error details:', {
        message: err.message,
        stack: err.stack
      })
      return []
    } finally {
      loading.value = false
    }
  }

  const fetchTemplate = async (templateId) => {
    loading.value = true
    error.value = null
    try {
      const url = `${API_BASE}/questionnaires/get_template/?template_id=${templateId}`
      console.log('Fetching template from:', url)
      const data = await apiCall(url)
      console.log('Template response:', data)
      return data
    } catch (err) {
      console.error('Failed to fetch template:', err)
      console.error('Error details:', {
        message: err.message,
        stack: err.stack
      })
      throw err
    } finally {
      loading.value = false
    }
  }

  const loadTemplateData = async (templateId) => {
    try {
      const templateData = await fetchTemplate(templateId)
      
      // Map template data to questionnaire format
      if (templateData) {
        // Update questionnaire fields
        currentQuestionnaire.value.questionnaire_name = templateData.template_name || ''
        currentQuestionnaire.value.description = templateData.template_description || ''
        // DON'T map template_type to questionnaire_type - they have different valid values!
        // Template types: STATIC, DYNAMIC, ASSESSMENT, EVALUATION, TEST
        // Questionnaire types: ONBOARDING, ANNUAL, INCIDENT, CUSTOM
        // Keep the existing questionnaire_type value (don't overwrite it)
        currentQuestionnaire.value.status = 'DRAFT' // Always start as draft
        
        // Map template questions to questionnaire questions format
        if (templateData.questions && Array.isArray(templateData.questions)) {
          questions.value = templateData.questions.map((q, index) => {
            // Map answer_type to question_type
            const questionTypeMap = {
              'TEXT': 'TEXT',
              'MULTIPLE_CHOICE': 'MULTIPLE_CHOICE',
              'CHECKBOX': 'CHECKBOX',
              'RATING': 'RATING',
              'FILE_UPLOAD': 'FILE_UPLOAD',
              'DATE': 'DATE',
              'NUMBER': 'NUMBER'
            }
            
            const mappedQuestion = {
              id: String(Date.now() + index), // Generate unique ID
              question_text: q.question_text || '',
              question_type: questionTypeMap[q.answer_type] || q.answer_type || 'TEXT',
              question_category: q.question_category || q.question_categor || '',
              is_required: q.is_required !== undefined ? q.is_required : false,
              display_order: q.display_order || index + 1,
              scoring_weight: q.weightage || q.scoring_weight || 1.0,
              help_text: q.help_text || '',
              options: q.options || {}
            }
            
            // Map options based on question type
            // If options is an array, it might be choices for MULTIPLE_CHOICE/CHECKBOX
            if (Array.isArray(mappedQuestion.options) && mappedQuestion.options.length > 0) {
              if (mappedQuestion.question_type === 'MULTIPLE_CHOICE' || mappedQuestion.question_type === 'CHECKBOX') {
                mappedQuestion.options = { choices: mappedQuestion.options }
              } else {
                mappedQuestion.options = {}
              }
            }
            
            // Initialize or validate options based on question type
            if (!mappedQuestion.options || typeof mappedQuestion.options !== 'object') {
              mappedQuestion.options = {}
            }
            
            if (mappedQuestion.question_type === 'MULTIPLE_CHOICE' || mappedQuestion.question_type === 'CHECKBOX') {
              if (!mappedQuestion.options.choices || !Array.isArray(mappedQuestion.options.choices)) {
                mappedQuestion.options.choices = ['Option 1', 'Option 2']
              }
            } else if (mappedQuestion.question_type === 'RATING') {
              if (!mappedQuestion.options.rating) {
                mappedQuestion.options.rating = {
                  min: 1,
                  max: 5,
                  step: 1,
                  labels: ''
                }
              }
            } else if (mappedQuestion.question_type === 'FILE_UPLOAD') {
              if (!mappedQuestion.options.file) {
                mappedQuestion.options.file = {
                  allowedTypes: 'pdf,doc,docx,jpg,jpeg,png',
                  maxSize: 10,
                  maxFiles: 1
                }
              }
            } else if (mappedQuestion.question_type === 'NUMBER') {
              if (!mappedQuestion.options.number) {
                mappedQuestion.options.number = {
                  min: null,
                  max: null,
                  step: null,
                  unit: ''
                }
              }
            }
            
            return mappedQuestion
          })
        } else {
          questions.value = []
        }
      }
      
      return templateData
    } catch (err) {
      console.error('Failed to load template data:', err)
      throw err
    }
  }

  return {
    // State
    questionnaires,
    currentQuestionnaire,
    questions,
    vendors,
    rfpData,
    screeningData,
    loading,
    error,
    
    // Computed
    getQuestionnaires,
    getCurrentQuestionnaire,
    getQuestions,
    getVendors,
    getRFPData,
    getScreeningData,
    isLoading,
    getError,
    
    // Actions
    fetchQuestionnaires,
    fetchQuestionnaire,
    createQuestionnaire,
    updateQuestionnaire,
    saveQuestionnaireWithQuestions,
    saveDraft,
    activateQuestionnaire,
    deleteQuestionnaire,
    addQuestion,
    removeQuestion,
    updateQuestion,
    resetCurrentQuestionnaire,
    updateQuestionnaireField,
    clearError,
    getQuestionTypes,
    getQuestionnaireTypes,
    getVendorCategories,
    fetchVendors,
    fetchVendorRFPData,
    fetchVendorScreeningData,
    fetchTemplates,
    fetchTemplate,
    loadTemplateData
  }
})
