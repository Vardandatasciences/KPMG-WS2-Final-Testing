import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import apiClient from '@/config/axios'

export const useVendorStore = defineStore('vendor', () => {
  // State from vendors.js
  const vendor_currentVendor = ref({
    vendorCode: 'VEND001',
    companyName: 'Acme Corporation',
    legalName: 'Acme Corporation Inc.',
    businessType: '',
    taxId: '12-3456789',
    dunsNumber: '123456789',
    incorporationDate: '',
    industrySector: '',
    website: 'https://acme.com',
    annualRevenue: '$10,000,000',
    employeeCount: '500',
    headquarters: '',
    vendorCategory: '',
    riskLevel: '',
    status: '',
    isCritical: false,
    hasDataAccess: false,
    hasSystemAccess: false,
    description: ''
  })

  const vendor_contacts = ref([
    {
      id: "1",
      name: "John Smith",
      email: "john@acme.com",
      phone: "+1-555-0123",
      role: "Primary",
      isPrimary: true
    },
    {
      id: "2",
      name: "Sarah Johnson",
      email: "sarah@acme.com",
      phone: "+1-555-0124",
      role: "Finance",
      isPrimary: false
    }
  ])

  const vendor_documents = ref([
    {
      id: "1",
      name: "Business_License.pdf",
      type: "License",
      version: "1.0",
      status: "Approved",
      expiryDate: "2026-01-01"
    },
    {
      id: "2",
      name: "GST_Certificate.pdf",
      type: "Certificate",
      version: "1.2",
      status: "Pending",
      expiryDate: "2025-12-31"
    }
  ])

  // State from dashboard.js
  const vendor_kpiData = ref([
    {
      title: "Total Vendors",
      value: "247",
      variant: "default",
      trend: { value: "12%", isPositive: true }
    },
    {
      title: "High-Risk Vendors",
      value: "8",
      variant: "destructive",
      trend: { value: "2%", isPositive: false }
    },
    {
      title: "SLA Compliance",
      value: "94.2%",
      variant: "success",
      trend: { value: "3.1%", isPositive: true }
    },
    {
      title: "Avg Risk Score",
      value: "2.4",
      variant: "default",
      trend: { value: "0.3", isPositive: false }
    }
  ])

  const vendor_recentVendors = ref([
    { name: "TechCorp Solutions", status: "pending", riskLevel: "medium", daysActive: 5 },
    { name: "Global Industries", status: "approved", riskLevel: "low", daysActive: 12 },
    { name: "DataStream Inc", status: "review", riskLevel: "high", daysActive: 3 },
    { name: "SecureNet Systems", status: "approved", riskLevel: "low", daysActive: 8 }
  ])

  const vendor_vendorStatusOverview = ref([
    { label: "Active", count: 180, percentage: 73, color: "vendor_bg-success" },
    { label: "Pending Review", count: 45, percentage: 18, color: "vendor_bg-warning" },
    { label: "Suspended", count: 15, percentage: 6, color: "vendor_bg-destructive" },
    { label: "Archived", count: 7, percentage: 3, color: "vendor_bg-muted" }
  ])

  // State from questionnaires.js
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

  // API Base URL
  const API_BASE = '/api/v1/vendor'

  // Computed properties
  const vendor_getCurrentVendor = computed(() => vendor_currentVendor.value)
  const vendor_getContacts = computed(() => vendor_contacts.value)
  const vendor_getDocuments = computed(() => vendor_documents.value)
  const vendor_getPrimaryContact = computed(() => vendor_contacts.value.find(c => c.isPrimary))
  const vendor_getKPIData = computed(() => vendor_kpiData.value)
  const vendor_getRecentVendors = computed(() => vendor_recentVendors.value)
  const vendor_getVendorStatusOverview = computed(() => vendor_vendorStatusOverview.value)
  const getQuestionnaires = computed(() => questionnaires.value)
  const getCurrentQuestionnaire = computed(() => currentQuestionnaire.value)
  const getQuestions = computed(() => questions.value)
  const getVendors = computed(() => vendors.value)
  const getRFPData = computed(() => rfpData.value)
  const getScreeningData = computed(() => screeningData.value)
  const isLoading = computed(() => loading.value)
  const getError = computed(() => error.value)

  // Helper function for API calls
  const apiCall = async (url, options = {}) => {
    try {
      const config = {
        url,
        method: options.method || 'GET',
        headers: {
          'Content-Type': 'application/json',
          ...options.headers
        },
        ...options
      }

      if (options.data) {
        config.data = options.data
      }

      const response = await apiClient(config)
      return response.data
    } catch (err) {
      error.value = err.message
      console.error('API call failed:', err)
      throw err
    }
  }

  // Vendor management actions
  const vendor_updateVendorField = (field, value) => {
    vendor_currentVendor.value[field] = value
  }

  const vendor_addContact = (contact) => {
    vendor_contacts.value.push(contact)
  }

  const vendor_removeContact = (id) => {
    vendor_contacts.value = vendor_contacts.value.filter(c => c.id !== id)
  }

  const vendor_updateContact = (id, updates) => {
    const index = vendor_contacts.value.findIndex(c => c.id === id)
    if (index !== -1) {
      vendor_contacts.value[index] = { ...vendor_contacts.value[index], ...updates }
    }
  }

  const vendor_addDocument = (document) => {
    vendor_documents.value.push(document)
  }

  const vendor_removeDocument = (id) => {
    vendor_documents.value = vendor_documents.value.filter(d => d.id !== id)
  }

  const vendor_updateDocumentStatus = (id, status) => {
    const document = vendor_documents.value.find(d => d.id === id)
    if (document) {
      document.status = status
    }
  }

  // Dashboard actions
  const vendor_updateKPI = (title, value) => {
    const kpi = vendor_kpiData.value.find(k => k.title === title)
    if (kpi) {
      kpi.value = value
    }
  }

  const vendor_addVendor = (vendor) => {
    vendor_recentVendors.value.unshift(vendor)
    if (vendor_recentVendors.value.length > 10) {
      vendor_recentVendors.value.pop()
    }
  }

  // Questionnaire actions
  const fetchQuestionnaires = async () => {
    loading.value = true
    error.value = null
    try {
      const data = await apiCall(`${API_BASE}-questionnaire/questionnaires/`)
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
      const data = await apiCall(`${API_BASE}-questionnaire/questionnaires/${id}/`)
      currentQuestionnaire.value = data
      questions.value = data.questions || []
      return data
    } catch (err) {
      console.error('Failed to fetch questionnaire:', err)
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
      const data = await apiCall(`${API_BASE}-questionnaire/questionnaires/`, {
        method: 'POST',
        data: questionnaireData
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
      const data = await apiCall(`${API_BASE}-questionnaire/questionnaires/${id}/`, {
        method: 'PUT',
        data: questionnaireData
      })
      currentQuestionnaire.value = data
      
      const index = questionnaires.value.findIndex(q => q.questionnaire_id === id)
      if (index !== -1) {
        questionnaires.value[index] = data
      }
      
      return data
    } catch (err) {
      console.error('Failed to update questionnaire:', err)
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
      await apiCall(`${API_BASE}-questionnaire/questionnaires/${id}/`, {
        method: 'DELETE'
      })
      
      questionnaires.value = questionnaires.value.filter(q => q.questionnaire_id !== id)
      
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
      help_text: '',
      ...question
    }
    questions.value.push(newQuestion)
    return newQuestion
  }

  const removeQuestion = (id) => {
    questions.value = questions.value.filter(q => q.id !== id)
    questions.value.forEach((q, index) => {
      q.display_order = index + 1
    })
  }

  const updateQuestion = (id, updates) => {
    const index = questions.value.findIndex(q => q.id === id)
    if (index !== -1) {
      questions.value[index] = { ...questions.value[index], ...updates }
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

  const fetchVendors = async () => {
    loading.value = true
    error.value = null
    try {
      const data = await apiCall(`${API_BASE}-core/vendors/`)
      vendors.value = data.results || data
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
      rfpData.value = []
      return []
    }
    
    loading.value = true
    error.value = null
    try {
      const data = await apiCall(`${API_BASE}-questionnaire/questionnaires/get_vendor_rfp_data/?vendor_id=${vendorId}`)
      rfpData.value = data
      return data
    } catch (err) {
      console.error('Failed to fetch RFP data:', err)
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
      const data = await apiCall(`${API_BASE}-questionnaire/questionnaires/get_vendor_screening_data/?vendor_id=${vendorId}`)
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

  return {
    // State
    vendor_currentVendor,
    vendor_contacts,
    vendor_documents,
    vendor_kpiData,
    vendor_recentVendors,
    vendor_vendorStatusOverview,
    questionnaires,
    currentQuestionnaire,
    questions,
    vendors,
    rfpData,
    screeningData,
    loading,
    error,
    
    // Computed
    vendor_getCurrentVendor,
    vendor_getContacts,
    vendor_getDocuments,
    vendor_getPrimaryContact,
    vendor_getKPIData,
    vendor_getRecentVendors,
    vendor_getVendorStatusOverview,
    getQuestionnaires,
    getCurrentQuestionnaire,
    getQuestions,
    getVendors,
    getRFPData,
    getScreeningData,
    isLoading,
    getError,
    
    // Actions
    vendor_updateVendorField,
    vendor_addContact,
    vendor_removeContact,
    vendor_updateContact,
    vendor_addDocument,
    vendor_removeDocument,
    vendor_updateDocumentStatus,
    vendor_updateKPI,
    vendor_addVendor,
    fetchQuestionnaires,
    fetchQuestionnaire,
    createQuestionnaire,
    updateQuestionnaire,
    deleteQuestionnaire,
    addQuestion,
    removeQuestion,
    updateQuestion,
    resetCurrentQuestionnaire,
    updateQuestionnaireField,
    clearError,
    fetchVendors,
    fetchVendorRFPData,
    fetchVendorScreeningData
  }
})
