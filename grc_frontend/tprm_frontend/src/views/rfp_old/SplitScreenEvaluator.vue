<template>
  <div class="h-screen flex flex-col">
    <!-- Header -->
    <div class="bg-white border-b border-gray-200 px-6 py-4">
      <h2 class="text-xl font-semibold text-gray-900">Split Screen Evaluator</h2>
    </div>

    <!-- Main Content -->
    <div class="flex-1 flex overflow-hidden">
      <!-- Left Panel - Proposal Content with Tabs -->
      <div class="flex-1 overflow-y-auto bg-white border-r border-gray-200 flex flex-col">
        <!-- Tabs -->
        <div class="border-b border-gray-200 bg-gray-50">
          <nav class="flex space-x-4 px-6 py-3" aria-label="Tabs">
            <button
              @click="activeTab = 'details'"
              :class="[
                'px-3 py-2 text-sm font-medium rounded-md transition-colors',
                activeTab === 'details'
                  ? 'bg-blue-100 text-blue-700'
                  : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
              ]"
            >
              Proposal Details
            </button>
            <button
              @click="activeTab = 'documents'"
              :class="[
                'px-3 py-2 text-sm font-medium rounded-md transition-colors',
                activeTab === 'documents'
                  ? 'bg-blue-100 text-blue-700'
                  : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
              ]"
            >
              Documents ({{ documents.length }})
            </button>
          </nav>
        </div>

        <!-- Tab Content -->
        <div class="flex-1 overflow-y-auto p-6">
          <!-- Proposal Details Tab -->
          <div v-if="activeTab === 'details'">
            <!-- Proposal Header -->
            <div class="mb-6 bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-lg p-4">
              <div class="flex items-center justify-between">
                <div>
                  <h3 class="text-lg font-semibold text-gray-900">{{ proposalData?.vendor_name || 'Loading...' }}</h3>
                  <p class="text-sm text-gray-600">{{ proposalData?.org || 'Organization' }}</p>
                  <p class="text-xs text-gray-500 mt-1">Submitted: {{ formatDate(proposalData?.submitted_at) }}</p>
                </div>
                <div class="text-right">
                  <span class="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-blue-100 text-blue-800">
                    {{ proposalData?.evaluation_status || 'PENDING' }}
                  </span>
                  <p v-if="proposalData?.proposed_value" class="text-sm text-gray-600 mt-1">
                    ${{ proposalData.proposed_value.toLocaleString() }}
                  </p>
                </div>
              </div>
            </div>

            <!-- Proposal Content -->
            <div v-if="proposalData?.proposal_data" class="prose max-w-none">
              <div v-for="(value, key) in proposalData.proposal_data" :key="key" class="mb-6">
                <h4 class="text-lg font-semibold text-gray-900 mb-2">{{ formatKey(key) }}</h4>
                <div class="text-sm text-gray-700">
                  <div v-if="typeof value === 'object' && value !== null" class="space-y-2">
                    <div v-for="(subValue, subKey) in value" :key="subKey" class="flex justify-between">
                      <span class="font-medium text-gray-600">{{ formatKey(subKey) }}:</span>
                      <span class="text-gray-900">{{ formatValue(subValue) }}</span>
                    </div>
                  </div>
                  <div v-else class="text-gray-900">{{ formatValue(value) }}</div>
                </div>
              </div>
            </div>
            <div v-else class="text-center py-8 text-gray-500">
              <span class="text-4xl mb-4 text-gray-400">📥</span>
              <p>No proposal data available</p>
            </div>
          </div>

          <!-- Documents Tab -->
          <div v-else-if="activeTab === 'documents'">
            <div v-if="documents.length > 0" class="space-y-4">
              <!-- Document Viewer -->
              <div v-if="selectedDocument" class="mb-6 bg-white border border-gray-200 rounded-lg overflow-hidden">
                <div class="flex items-center justify-between px-4 py-3 border-b border-gray-200 bg-gray-50">
                  <div class="flex items-center space-x-3">
                    <span class="text-2xl">📄</span>
                    <div>
                      <p class="text-sm font-medium text-gray-900">{{ selectedDocument.name }}</p>
                      <p class="text-xs text-gray-500">{{ formatFileType(selectedDocument.file_type) }}</p>
                    </div>
                  </div>
                  <div class="flex items-center space-x-2">
                    <button 
                      @click="downloadDocument(selectedDocument)"
                      class="inline-flex items-center px-2 py-1 text-xs font-medium text-gray-700 bg-white border border-gray-300 rounded hover:bg-gray-50"
                      title="Download"
                    >
                      ⬇ Download
                    </button>
                    <button 
                      @click="selectedDocument = null"
                      class="inline-flex items-center px-2 py-1 text-xs font-medium text-gray-700 bg-white border border-gray-300 rounded hover:bg-gray-50"
                      title="Close"
                    >
                      ✕ Close
                    </button>
                  </div>
                </div>
                
                <!-- Document Content -->
                <div class="h-96 bg-gray-100">
                  <!-- PDF Viewer -->
                  <div v-if="isPDF(selectedDocument)" class="h-full">
                    <iframe 
                      :src="selectedDocument.url" 
                      class="w-full h-full border-0"
                      @error="handleDocumentError"
                    ></iframe>
                  </div>
                  
                  <!-- Image Viewer -->
                  <div v-else-if="isImage(selectedDocument)" class="h-full flex items-center justify-center p-4">
                    <img 
                      :src="selectedDocument.url" 
                      :alt="selectedDocument.name"
                      class="max-w-full max-h-full object-contain"
                      @error="handleDocumentError"
                    />
                  </div>
                  
                  <!-- Unsupported Format -->
                  <div v-else class="flex flex-col items-center justify-center h-full text-gray-500">
                    <span class="text-4xl mb-4">📄</span>
                    <p class="text-sm mb-2">Preview not available for this file type</p>
                    <button 
                      @click="downloadDocument(selectedDocument)"
                      class="inline-flex items-center px-3 py-1 text-sm font-medium text-blue-600 bg-blue-50 rounded hover:bg-blue-100"
                    >
                      ⬇ Download to view
                    </button>
                  </div>
                </div>
              </div>

              <!-- Document List -->
              <div class="space-y-3">
                <h4 class="text-sm font-semibold text-gray-900">Available Documents</h4>
                <div 
                  v-for="doc in documents" 
                  :key="doc.id"
                  class="bg-white border border-gray-200 rounded-lg p-4 hover:border-blue-300 hover:shadow-sm transition-all"
                  :class="{ 'border-blue-500 bg-blue-50': selectedDocument?.id === doc.id }"
                >
                  <div class="flex items-start justify-between">
                    <div class="flex items-start space-x-3 flex-1">
                      <span class="text-2xl">📄</span>
                      <div class="flex-1 min-w-0">
                        <p class="text-sm font-medium text-gray-900 truncate">{{ doc.name }}</p>
                        <p class="text-xs text-gray-500">{{ formatFileType(doc.file_type) }}</p>
                        <p v-if="doc.size" class="text-xs text-gray-400">{{ formatFileSize(doc.size) }}</p>
                      </div>
                    </div>
                    <div class="flex items-center space-x-2 ml-4">
                      <button 
                        @click="selectedDocument = doc"
                        class="inline-flex items-center px-3 py-1 text-xs font-medium text-blue-600 bg-blue-50 rounded hover:bg-blue-100"
                      >
                        👁 View
                      </button>
                      <button 
                        @click="downloadDocument(doc)"
                        class="inline-flex items-center px-3 py-1 text-xs font-medium text-gray-700 bg-white border border-gray-300 rounded hover:bg-gray-50"
                      >
                        ⬇
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            
            <!-- No Documents Message -->
            <div v-else class="text-center py-8 text-gray-500">
              <span class="text-4xl mb-4 text-gray-400">📁</span>
              <p>No documents available</p>
            </div>
          </div>
        </div>
      </div>

      <!-- Right Panel - Evaluation Form -->
      <div class="w-96 overflow-y-auto bg-gray-50">
        <div class="p-6">
          <h3 class="text-lg font-medium text-gray-900 mb-6">Evaluation Form</h3>
          
          <div class="space-y-6">
            <div v-for="criterion in evaluationCriteria" :key="criterion.id">
              <label class="block text-sm font-medium text-gray-700 mb-2">
                {{ criterion.name }}
                <span v-if="criterion.is_mandatory" class="text-red-500 ml-1">*</span>
              </label>
              <div class="space-y-2">
                <div class="flex items-center justify-between text-sm">
                  <span class="text-gray-500">Score</span>
                  <span class="font-medium">{{ currentScores[criterion.id] || 0 }}/{{ criterion.max_score || 100 }}</span>
                </div>
                <input
                  v-model.number="currentScores[criterion.id]"
                  type="range"
                  :min="criterion.min_score || 0"
                  :max="criterion.max_score || 100"
                  class="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
                />
                <div class="flex justify-between text-xs text-gray-400">
                  <span>Poor</span>
                  <span>Excellent</span>
                </div>
              </div>
            </div>

            <div>
              <label class="block text-sm font-medium text-gray-700 mb-2">
                Overall Comments
              </label>
              <textarea
                v-model="localOverallComments"
                rows="4"
                class="w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                placeholder="Add your evaluation comments..."
              />
            </div>

            <div class="pt-4 border-t border-gray-200">
              <div class="flex justify-between items-center mb-4">
                <span class="text-sm font-medium text-gray-700">Total Score</span>
                <span class="text-lg font-bold text-blue-600">{{ totalScore }}/{{ evaluationCriteria.reduce((sum, c) => sum + (c.max_score || 100), 0) }}</span>
              </div>
              
              <div class="space-y-2">
                <Button @click="handleSaveEvaluation" class="w-full">Save Evaluation</Button>
                <Button @click="handleSubmitEvaluation" variant="outline" class="w-full">Submit Final</Button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- Popup Modal -->
  <PopupModal />
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import Button from '@/components_rfp/Button.vue'
import PopupModal from '@/popup/PopupModal.vue'
import { PopupService } from '@/popup/popupService'
import loggingService from '@/services/loggingService'

// Props
const props = defineProps({
  proposalData: {
    type: Object,
    default: null
  },
  evaluationCriteria: {
    type: Array,
    default: () => []
  },
  scores: {
    type: Object,
    default: () => ({})
  },
  comments: {
    type: Object,
    default: () => ({})
  },
  overallComments: {
    type: String,
    default: ''
  }
})

// Emits
const emit = defineEmits(['update-scores', 'update-comments', 'save-evaluation', 'submit-evaluation'])

// Local state
const currentScores = ref<Record<number, number>>({})
const localComments = ref('')
const localOverallComments = ref('')
const activeTab = ref('details')
const documents = ref([])
const selectedDocument = ref(null)

// Initialize from props
watch(() => props.scores, (newScores) => {
  currentScores.value = { ...newScores }
}, { immediate: true, deep: true })

watch(() => props.comments, (newComments) => {
  // Convert comments object to string for display
  localComments.value = Object.values(newComments).join('\n')
}, { immediate: true, deep: true })

watch(() => props.overallComments, (newOverallComments) => {
  localOverallComments.value = newOverallComments
}, { immediate: true })

// Watch for changes and emit updates
watch(currentScores, (newScores) => {
  emit('update-scores', newScores)
}, { deep: true })

watch(localComments, (newComments) => {
  // Convert string back to object format
  const commentsObj = {}
  props.evaluationCriteria.forEach((criterion, index) => {
    commentsObj[criterion.id] = newComments.split('\n')[index] || ''
  })
  emit('update-comments', commentsObj)
})

watch(localOverallComments, (newOverallComments) => {
  emit('update-comments', { overall: newOverallComments })
})

const totalScore = computed(() => {
  let total = 0
  let totalWeight = 0
  
  props.evaluationCriteria.forEach(criterion => {
    const score = currentScores.value[criterion.id] || 0
    total += (score * criterion.weight) / 100
    totalWeight += criterion.weight
  })
  
  return totalWeight > 0 ? Math.round(total) : 0
})

const handleSaveEvaluation = () => {
  emit('save-evaluation')
}

const handleSubmitEvaluation = () => {
  emit('submit-evaluation')
}

// Helper functions
const formatKey = (key) => {
  if (typeof key !== 'string') {
    return String(key || 'Unknown')
  }
  
  return key
    .split('_')
    .map(word => word && word.length > 0 ? word.charAt(0).toUpperCase() + word.slice(1) : '')
    .join(' ')
}

const formatValue = (value) => {
  if (value === null || value === undefined) {
    return 'Not specified'
  }
  
  if (typeof value === 'boolean') {
    return value ? 'Yes' : 'No'
  }
  
  if (typeof value === 'object') {
    return JSON.stringify(value, null, 2)
  }
  
  return String(value)
}

const formatDate = (dateString) => {
  if (!dateString) return 'N/A'
  const date = new Date(dateString)
  return date.toLocaleDateString() + ' ' + date.toLocaleTimeString()
}

// Document handling functions
const extractDocuments = () => {
  documents.value = []
  
  if (!props.proposalData) {
    console.log('No proposal data available')
    return
  }
  
  console.log('🔍 Extracting documents from proposal data:', props.proposalData)
  
  try {
    // PRIORITY 1: Extract from document_urls at root level (REAL S3 URLs)
    if (props.proposalData.document_urls) {
      console.log('✅ Found document_urls at root (REAL S3 URLs):', props.proposalData.document_urls)
      
      Object.entries(props.proposalData.document_urls).forEach(([docType, url]: [string, any]) => {
        if (url && typeof url === 'string') {
          const filename = url.split('/').pop() || docType
          documents.value.push({
            id: `s3_root_${docType}`,
            name: docType.replace(/_/g, ' ').toUpperCase(),
            file_name: filename,
            file_type: getFileTypeFromName(filename),
            url: url,
            category: 'S3 Documents',
            source: 'root.document_urls'
          })
          console.log(`✅ Added S3 document: ${docType} -> ${url}`)
        }
      })
    }
    
    // PRIORITY 2: Extract from proposal_data.document_urls (if different from root)
    if (props.proposalData.proposal_data?.document_urls) {
      console.log('Found proposal_data.document_urls:', props.proposalData.proposal_data.document_urls)
      
      Object.entries(props.proposalData.proposal_data.document_urls).forEach(([docType, url]: [string, any]) => {
        if (url && typeof url === 'string' && !documents.value.find(d => d.url === url)) {
          const filename = url.split('/').pop() || docType
          documents.value.push({
            id: `s3_${docType}`,
            name: docType.replace(/_/g, ' ').toUpperCase(),
            file_name: filename,
            file_type: getFileTypeFromName(filename),
            url: url,
            category: 'S3 Documents',
            source: 'proposal_data.document_urls'
          })
          console.log(`✅ Added S3 document from proposal_data: ${docType} -> ${url}`)
        }
      })
    }
    
    // PRIORITY 3: Extract from response_documents (backup with metadata)
    if (props.proposalData.response_documents) {
      console.log('Found response_documents:', props.proposalData.response_documents)
      
      Object.entries(props.proposalData.response_documents).forEach(([docType, docData]: [string, any]) => {
        if (docData && typeof docData === 'object' && docData.url) {
          if (!documents.value.find(d => d.type === docType)) {
            documents.value.push({
              id: docData.key || `resp_${docType}`,
              name: docData.filename || docType.replace(/_/g, ' ').toUpperCase(),
              file_name: docData.filename || docType,
              file_type: docData.content_type || getFileTypeFromName(docData.filename || ''),
              size: docData.size,
              url: docData.url,
              category: 'Response Documents',
              source: 'response_documents'
            })
            console.log(`Added document from response_documents: ${docType}`)
          }
        }
      })
    }
    
    // PRIORITY 4: Extract from proposal_data.documents (legacy)
    if (props.proposalData.proposal_data?.documents) {
      console.log('Found proposal_data.documents:', props.proposalData.proposal_data.documents)
      
      Object.entries(props.proposalData.proposal_data.documents).forEach(([docType, docData]: [string, any]) => {
        if (docData && typeof docData === 'object' && docData.url) {
          if (!documents.value.find(d => d.type === docType)) {
            documents.value.push({
              id: docData.key || `legacy_${docType}`,
              name: docData.filename || docType.replace(/_/g, ' ').toUpperCase(),
              file_name: docData.filename || docType,
              file_type: docData.content_type || getFileTypeFromName(docData.filename || ''),
              size: docData.size,
              url: docData.url,
              category: 'Legacy Documents',
              source: 'proposal_data.documents'
            })
            console.log(`Added document from proposal_data.documents: ${docType}`)
          }
        }
      })
    }
    
    console.log('✅ Total documents extracted:', documents.value.length)
    console.log('📄 Documents array:', documents.value)
    
  } catch (error) {
    console.error('Error extracting documents:', error)
  }
}

const getFileTypeFromName = (filename: string): string => {
  if (!filename) return 'application/octet-stream'
  
  const ext = filename.split('.').pop()?.toLowerCase()
  
  const typeMap: Record<string, string> = {
    'pdf': 'application/pdf',
    'doc': 'application/msword',
    'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'xls': 'application/vnd.ms-excel',
    'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'png': 'image/png',
    'jpg': 'image/jpeg',
    'jpeg': 'image/jpeg',
    'gif': 'image/gif',
    'txt': 'text/plain',
    'csv': 'text/csv'
  }
  
  return typeMap[ext || ''] || 'application/octet-stream'
}

const formatFileType = (type: string): string => {
  if (!type) return 'Unknown'
  
  if (type.includes('pdf')) return 'PDF Document'
  if (type.includes('word')) return 'Word Document'
  if (type.includes('excel') || type.includes('spreadsheet')) return 'Excel Spreadsheet'
  if (type.includes('image')) return 'Image'
  if (type.includes('text')) return 'Text File'
  
  return type.split('/').pop()?.toUpperCase() || 'Document'
}

const formatFileSize = (bytes: number): string => {
  if (!bytes) return 'Unknown size'
  
  const kb = bytes / 1024
  if (kb < 1024) return `${kb.toFixed(1)} KB`
  
  const mb = kb / 1024
  return `${mb.toFixed(1)} MB`
}

const isPDF = (doc: any): boolean => {
  return doc.file_type?.includes('pdf') || doc.name?.toLowerCase().endsWith('.pdf')
}

const isImage = (doc: any): boolean => {
  return doc.file_type?.includes('image') || 
         /\.(jpg|jpeg|png|gif|bmp|webp)$/i.test(doc.name)
}

const downloadDocument = (doc: any) => {
  try {
    console.log('Downloading document:', doc)
    
    if (!doc.url) {
      throw new Error('Document URL not available')
    }
    
    // Direct download using anchor tag
    const link = document.createElement('a')
    link.href = doc.url
    link.download = doc.file_name || doc.name || 'document'
    link.target = '_blank'
    link.rel = 'noopener noreferrer'
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    
    console.log('Document download initiated')
    
  } catch (error) {
    console.error('Error downloading document:', error)
    PopupService.error(`Failed to download document: ${error.message}`, 'Download Failed')
  }
}

const handleDocumentError = () => {
  console.error('Error loading document')
  PopupService.error('Failed to load document preview. Please try downloading the document instead.', 'Preview Error')
}

// Watch for proposal data changes and extract documents
watch(() => props.proposalData, () => {
  extractDocuments()
}, { immediate: true, deep: true })

// Initialize on mount
onMounted(async () => {
  await loggingService.logPageView('RFP', 'Split Screen Evaluator')
  await extractDocuments()
})
</script>

<style scoped>
/* Additional split-screen specific styles can be added here */
</style>
