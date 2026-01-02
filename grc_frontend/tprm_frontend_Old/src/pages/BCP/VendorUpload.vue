<template>
  <div class="page">
    <div>
      <div class="page-header">
        <div class="header-content">
          <h1 class="page-title">Upload Plan (Vendor Portal)</h1>
          <p class="page-subtitle">Submit BCP/DRP plans for review and evaluation</p>
        </div>
      </div>

    <!-- Plan Type Toggle -->
    <div class="toggle-container">
      <div class="plan-type-toggle">
        <button
          type="button"
          :class="['toggle-option', planType === 'BCP' ? 'toggle-option--active' : '']"
          @click="planType = 'BCP'"
        >
          BCP (Business Continuity)
        </button>
        <button
          type="button"
          :class="['toggle-option', planType === 'DRP' ? 'toggle-option--active' : '']"
          @click="planType = 'DRP'"
        >
          DRP (Disaster Recovery)
        </button>
      </div>
    </div>

    <div class="main-layout">
      <!-- Left Column - Form -->
      <div class="form-column">
        <div class="card">
          <div class="card-content space-y-6">
            <h2 class="text-lg font-semibold">Plan Data</h2>
            <!-- Unified Form -->
            <div class="unified-form">
              <div class="form-row">
                <div>
                  <label for="strategy-name" class="label">Strategy Name *</label>
                  <input
                    id="strategy-name"
                    class="input"
                    placeholder="e.g., Payments Resilience 2025"
                    v-model="strategyName"
                  />
                </div>
              </div>

              <div class="form-row">
                <div>
                  <label for="plan-name" class="label">Plan Name *</label>
                  <input
                    id="plan-name"
                    class="input"
                    placeholder="e.g., Cloud BCP"
                    v-model="currentDoc.planName"
                  />
                </div>
                <div>
                  <label for="scope" class="label">Scope</label>
                  <select
                    id="scope"
                    class="select"
                    v-model="currentDoc.scope"
                  >
                    <option value="">Select scope</option>
                    <option v-for="scope in scopeOptions" :key="scope.id" :value="scope.value">
                      {{ scope.value }}
                    </option>
                  </select>
                </div>
                <div>
                  <label for="criticality" class="label">Criticality *</label>
                  <select
                    id="criticality"
                    class="select"
                    v-model="currentDoc.criticality"
                  >
                    <option value="">Select criticality</option>
                    <option value="LOW">LOW</option>
                    <option value="MEDIUM">MEDIUM</option>
                    <option value="HIGH">HIGH</option>
                    <option value="CRITICAL">CRITICAL</option>
                  </select>
                </div>
              </div>

              <div>
                <label for="file-upload" class="label">File *</label>
                <div class="file-upload-area" @click="triggerFileUpload">
                  <svg class="h-6 w-6 text-muted-foreground mx-auto mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"/>
                  </svg>
                  <p class="text-sm text-muted-foreground mb-2">
                    {{ selectedFile ? selectedFile.name : 'Choose File' }}
                  </p>
                  <input
                    ref="fileInput"
                    id="file-upload"
                    type="file"
                    accept=".pdf,.doc,.docx"
                    class="hidden"
                    @change="handleFileSelect"
                  />
                  <button type="button" class="btn btn--outline btn--sm">Choose File</button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Right Column - Documents -->
      <div class="documents-column">
        <div class="card">
          <div class="card-content">
            <h2 class="text-lg font-semibold mb-4">Documents</h2>
            <div v-if="documents.length > 0" class="documents-cards">
              <div v-for="(doc, index) in documents" :key="index" class="document-card">
                <div class="document-header">
                  <h3 class="document-title">{{ doc.planName }}</h3>
                  <div class="document-actions">
                    <button @click="editDocument(index)" class="btn btn--outline btn--sm" title="Edit">
                      <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"/>
                      </svg>
                    </button>
                    <button @click="removeDocument(index)" class="btn btn--outline btn--sm text-destructive" title="Remove">
                      <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/>
                      </svg>
                    </button>
                  </div>
                </div>
                <div class="document-details">
                  <div class="detail-row">
                    <span class="detail-label">Type:</span>
                    <span class="detail-value">{{ planType }}</span>
                  </div>
                  <div class="detail-row">
                    <span class="detail-label">File Name:</span>
                    <span class="detail-value">{{ doc.fileName }}</span>
                  </div>
                  <div class="detail-row">
                    <span class="detail-label">Criticality:</span>
                    <span class="detail-value">
                      {{ doc.criticality }}
                    </span>
                  </div>
                </div>
              </div>
            </div>
            <div v-else class="text-center text-muted-foreground py-8">
              No documents added yet
            </div>
          </div>
        </div>

        <div class="mt-6 flex gap-4">
          <button @click="loadMockData" class="btn btn--outline flex-1">
            <svg class="h-4 w-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12"/>
            </svg>
            Load Data
          </button>
          <button @click="addDocument" class="btn btn--primary flex-1">
            <svg class="h-4 w-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/>
            </svg>
            Add Document
          </button>
          <button @click="submitDocuments" class="btn btn--primary flex-1">
            Submit
          </button>
        </div>
      </div>
    </div>
    </div>
  </div>

  <!-- Popup Modal -->
  <PopupModal />
</template>

<script>
import { ref, reactive, onMounted, computed } from 'vue'
import api from '../../services/api_bcp.js'
import PopupModal from '@/popup/PopupModal.vue'
import { PopupService } from '@/popup/popupService'
import { useNotifications } from '@/composables/useNotifications'
import notificationService from '@/services/notificationService'
import loggingService from '@/services/loggingService'

export default {
  name: 'VendorUpload',
  components: {
    PopupModal
  },
  setup() {
    const { showSuccess, showError, showWarning, showInfo } = useNotifications()

    const planType = ref('BCP')
    const strategyName = ref('')
    const selectedFile = ref(null)
    const fileInput = ref(null)
    const scopeOptions = ref([])
    
    const currentDoc = reactive({
      planName: '',
      criticality: '',
      scope: ''
    })

    const documents = ref([])

    const fetchScopeOptions = async () => {
      try {
        console.log('Fetching scope options from: https://grc-tprm.vardaands.com/api/tprm/bcpdrp/dropdowns/?source=plan_scope')
        const response = await api.dropdowns({ source: 'plan_scope' })
        console.log('API Response:', response)
        console.log('Response data:', response.data)
        console.log('Response data type:', typeof response.data)
        console.log('Response data keys:', Object.keys(response.data || {}))
        
        // The response interceptor should have unwrapped the data
        // The dropdown options are in response.data.data
        scopeOptions.value = response.data?.data || []
        console.log('Scope options loaded:', scopeOptions.value)
        console.log('Scope options length:', scopeOptions.value.length)
      } catch (error) {
        console.error('Error fetching scope options:', error)
        console.error('Error details:', error.message)
        // No fallback - only show real data from database
        scopeOptions.value = []
      }
    }

    const triggerFileUpload = () => {
      fileInput.value.click()
    }

    const handleFileSelect = async (event) => {
      const file = event.target.files[0]
      if (file) {
        // Validate file type
        const allowedTypes = ['application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document']
        if (!allowedTypes.includes(file.type)) {
          PopupService.warning('Please select a valid file (PDF, DOC, or DOCX)', 'Invalid File Type')
          // Create notification
          await notificationService.createPlanUploadNotification('invalid_file', {})
          return
        }
        
        // Validate file size (max 10MB)
        const maxSize = 10 * 1024 * 1024 // 10MB
        if (file.size > maxSize) {
          PopupService.warning('File size must be less than 10MB', 'File Too Large')
          // Create notification
          await notificationService.createPlanUploadNotification('file_too_large', {})
          return
        }
        
        selectedFile.value = file
      }
    }


    const addDocument = () => {
      if (!currentDoc.planName || !currentDoc.criticality || !selectedFile.value) {
        PopupService.warning('Please fill in all required fields and select a file', 'Missing Information')
        return
      }

      console.log('Adding document with file:', {
        fileName: selectedFile.value.name,
        fileType: selectedFile.value.type,
        fileSize: selectedFile.value.size,
        fileObject: selectedFile.value
      })

      documents.value.push({
        ...currentDoc,
        file: selectedFile.value,
        fileName: selectedFile.value.name,
        fileSize: selectedFile.value.size
      })

      // Reset form
      currentDoc.planName = ''
      currentDoc.criticality = ''
      currentDoc.scope = ''
      selectedFile.value = null
      if (fileInput.value) {
        fileInput.value.value = ''
      }
    }

    const editDocument = (index) => {
      const doc = documents.value[index]
      currentDoc.planName = doc.planName
      currentDoc.criticality = doc.criticality
      currentDoc.scope = doc.scope
      selectedFile.value = doc.file
      
      // Remove from documents list
      documents.value.splice(index, 1)
    }

    const removeDocument = (index) => {
      PopupService.confirm(
        'Are you sure you want to remove this document?',
        'Confirm Removal',
        () => {
          documents.value.splice(index, 1)
        }
      )
    }


    const submitDocuments = async () => {
      if (documents.value.length === 0) {
        PopupService.warning('Please add at least one document', 'No Documents')
        return
      }

      if (!strategyName.value.trim()) {
        PopupService.warning('Please enter a strategy name', 'Missing Strategy Name')
        return
      }

      try {
        // Create FormData for file upload
        const formData = new FormData()
        formData.append('strategyName', strategyName.value)
        formData.append('planType', planType.value)
        
        // Add document metadata
        formData.append('documents', JSON.stringify(documents.value.map(doc => ({
          planName: doc.planName,
          scope: doc.scope,
          criticality: doc.criticality,
          fileName: doc.fileName
        }))))
        
        // Add files
        console.log('Documents to upload:', documents.value)
        documents.value.forEach((doc, index) => {
          console.log(`Processing document ${index}:`, doc)
          if (doc.file) {
            formData.append(`file_${doc.fileName}`, doc.file)
            console.log(`Adding file: file_${doc.fileName} -> ${doc.file.name}`)
          } else {
            console.warn(`Document ${index} has no file:`, doc)
          }
        })

        console.log('Submitting documents to backend...')
        console.log('FormData contents:')
        for (let [key, value] of formData.entries()) {
          console.log(`${key}:`, value)
        }
        
        // Additional debugging for file objects
        console.log('Files in FormData:')
        documents.value.forEach((doc, index) => {
          console.log(`Document ${index}:`, {
            fileName: doc.fileName,
            hasFile: !!doc.file,
            fileType: doc.file?.type,
            fileSize: doc.file?.size,
            fileKey: `file_${doc.fileName}`
          })
        })
        
        const result = await api.vendorUpload(formData)
        console.log('Upload successful:', result)
        console.log('Result type:', typeof result)
        console.log('Result keys:', Object.keys(result || {}))
        
        // Handle different response structures
        let responseData = result
        
        // If we get the full Axios response object, extract the data
        if (result && result.data && typeof result.data === 'object') {
          responseData = result.data
          console.log('Extracted response data:', responseData)
        }
        
        console.log('Response data plans:', responseData.plans)
        console.log('Response data strategy_name:', responseData.strategy_name)
        
        if (responseData && responseData.plans && Array.isArray(responseData.plans)) {
          PopupService.success(`Documents submitted successfully! Created ${responseData.plans.length} plan(s) under strategy "${responseData.strategy_name}"`, 'Submission Successful')
          // Create notification
          await notificationService.createPlanUploadNotification('plan_uploaded', {
            plan_count: responseData.plans.length,
            strategy_name: responseData.strategy_name,
            plan_type: planType.value
          })
        } else {
          console.error('Unexpected response structure:', responseData)
          PopupService.success('Documents submitted successfully!', 'Submission Successful')
          // Create generic success notification
          await notificationService.createBCPSuccessNotification('plan_upload', {
            title: 'Plans Uploaded',
            message: 'Documents submitted successfully'
          })
        }
        
        // Reset everything
        strategyName.value = ''
        documents.value = []
        currentDoc.planName = ''
        currentDoc.criticality = ''
        currentDoc.scope = ''
        selectedFile.value = null
        if (fileInput.value) {
          fileInput.value.value = ''
        }
      } catch (error) {
        console.error('Error submitting documents:', error)
        PopupService.error('Error submitting documents. Please try again.', 'Submission Failed')
        // Create error notification
        await notificationService.createPlanUploadNotification('plan_upload_failed', {
          error: error.message || 'Unknown error'
        })
      }
    }

    // Mock data functions
    const getBCPMockData = () => {
      return {
        strategyName: 'Financial Services Business Continuity Strategy',
        documents: [
          {
            planName: 'Core Banking Operations BCP',
            scope: 'Core banking systems, customer accounts, transaction processing',
            criticality: 'CRITICAL',
            fileName: 'Core_Banking_BCP_v2.1.pdf',
            file: createMockFile('Core_Banking_BCP_v2.1.pdf', 'application/pdf')
          },
          {
            planName: 'Customer Service Continuity BCP',
            scope: 'Call center operations, customer support systems, online banking',
            criticality: 'HIGH',
            fileName: 'Customer_Service_BCP_v1.8.pdf',
            file: createMockFile('Customer_Service_BCP_v1.8.pdf', 'application/pdf')
          },
          {
            planName: 'Regulatory Compliance BCP',
            scope: 'Regulatory reporting, compliance monitoring, audit trails',
            criticality: 'HIGH',
            fileName: 'Regulatory_Compliance_BCP_v3.0.pdf',
            file: createMockFile('Regulatory_Compliance_BCP_v3.0.pdf', 'application/pdf')
          }
        ]
      }
    }

    const getDRPMockData = () => {
      return {
        strategyName: 'IT Infrastructure Disaster Recovery Strategy',
        documents: [
          {
            planName: 'Primary Data Center DRP',
            scope: 'Main data center systems, servers, network infrastructure',
            criticality: 'CRITICAL',
            fileName: 'Primary_DC_DRP_v4.2.pdf',
            file: createMockFile('Primary_DC_DRP_v4.2.pdf', 'application/pdf')
          },
          {
            planName: 'Cloud Services Recovery DRP',
            scope: 'Cloud applications, SaaS services, cloud infrastructure',
            criticality: 'HIGH',
            fileName: 'Cloud_Recovery_DRP_v2.5.pdf',
            file: createMockFile('Cloud_Recovery_DRP_v2.5.pdf', 'application/pdf')
          },
          {
            planName: 'Network Infrastructure DRP',
            scope: 'Network connectivity, routers, switches, internet services',
            criticality: 'HIGH',
            fileName: 'Network_Infrastructure_DRP_v1.9.pdf',
            file: createMockFile('Network_Infrastructure_DRP_v1.9.pdf', 'application/pdf')
          }
        ]
      }
    }

    const createMockFile = (fileName, fileType) => {
      // Create a mock file object for testing
      const mockFile = new File(['Mock file content for ' + fileName], fileName, { type: fileType })
      return mockFile
    }

    const loadMockData = () => {
      if (documents.value.length > 0) {
        PopupService.confirm(
          'This will replace all existing documents. Continue?',
          'Replace Documents',
          () => {
            performLoadMockData()
          }
        )
      } else {
        performLoadMockData()
      }
    }

    const performLoadMockData = () => {
      let mockData
      if (planType.value === 'BCP') {
        mockData = getBCPMockData()
        console.log('Loading BCP mock data')
      } else if (planType.value === 'DRP') {
        mockData = getDRPMockData()
        console.log('Loading DRP mock data')
      } else {
        PopupService.warning('Please select a plan type (BCP or DRP) first', 'No Plan Type Selected')
        return
      }

      // Load the mock data
      strategyName.value = mockData.strategyName
      documents.value = [...mockData.documents]
      
      PopupService.success(`Mock data loaded for ${planType.value} strategy with ${mockData.documents.length} plans. You can now review and modify the documents before submitting.`, 'Mock Data Loaded')
    }

    // Fetch scope options on component mount
    onMounted(async () => {
      await loggingService.logPageView('BCP', 'Vendor Upload')
      await fetchScopeOptions()
    })

    return {
      planType,
      strategyName,
      currentDoc,
      documents,
      selectedFile,
      fileInput,
      scopeOptions,
      triggerFileUpload,
      handleFileSelect,
      addDocument,
      editDocument,
      removeDocument,
      submitDocuments,
      loadMockData
    }
  }
}
</script>

<style scoped>
@import './VendorUpload.css';
</style>