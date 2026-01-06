<template>
  <div class="space-y-4">
    <div class="border-2 border-dashed border-muted-foreground/25 rounded-lg p-6">
      <div class="text-center">
        <Upload class="mx-auto h-12 w-12 text-muted-foreground" />
        <div class="mt-4">
          <label for="file-upload" class="cursor-pointer">
            <span class="mt-2 block text-sm font-medium text-foreground">
              Upload contract document for OCR extraction
            </span>
            <span class="mt-1 block text-sm text-muted-foreground">
              PDF, JPG, PNG, or TIFF files only (Max 10MB)
            </span>
          </label>
          <input
            id="file-upload"
            ref="fileInput"
            type="file"
            accept=".pdf,.jpg,.jpeg,.png,.tiff"
            @change="handleFileUpload"
            class="sr-only"
            :disabled="uploading"
          />
        </div>
        <button
          @click="$refs.fileInput.click()"
          :disabled="uploading"
          class="mt-4 inline-flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 disabled:opacity-50"
        >
          <Upload v-if="!uploading" class="w-4 h-4" />
          <div v-else class="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
          {{ uploading ? 'Processing...' : 'Choose File' }}
        </button>
      </div>
    </div>
    
    <!-- Uploaded File Display -->
    <div v-if="uploadedFile" class="flex items-center gap-2 p-3 bg-muted rounded-md">
      <FileText class="w-4 h-4" />
      <div class="flex-1">
        <span class="text-sm font-medium">{{ uploadedFile.name }}</span>
        <div class="text-xs text-muted-foreground">
          {{ formatFileSize(uploadedFile.size) }}
        </div>
      </div>
      <button 
        @click="removeFile" 
        :disabled="uploading"
        class="text-muted-foreground hover:text-foreground disabled:opacity-50"
      >
        <X class="w-4 h-4" />
      </button>
    </div>
    
    <!-- OCR Progress -->
    <div v-if="uploading" class="space-y-2">
      <div class="flex items-center justify-between text-sm">
        <span>Processing document...</span>
        <span>{{ ocrProgress }}%</span>
      </div>
      <div class="w-full bg-muted rounded-full h-2">
        <div 
          class="bg-primary h-2 rounded-full transition-all duration-300"
          :style="{ width: `${ocrProgress}%` }"
        ></div>
      </div>
    </div>
    
    <!-- OCR Results -->
    <div v-if="ocrResults" class="space-y-4">
      <div class="border rounded-lg p-4 bg-green-50">
        <h4 class="font-medium text-green-800 mb-2">OCR Extraction Complete!</h4>
        <div class="grid grid-cols-2 gap-4 text-sm">
          <div>
            <span class="font-medium">Clauses Extracted:</span>
            <span class="ml-2 text-green-700">{{ ocrResults.extracted_clauses }}</span>
          </div>
          <div>
            <span class="font-medium">Terms Extracted:</span>
            <span class="ml-2 text-green-700">{{ ocrResults.extracted_terms }}</span>
          </div>
        </div>
      </div>
      
      <div class="flex items-center gap-2">
        <button 
          @click="applyOCRResults" 
          class="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700"
        >
          Apply Extracted Data
        </button>
        <button 
          @click="clearOCRResults" 
          class="px-4 py-2 border rounded-md hover:bg-muted"
        >
          Clear Results
        </button>
      </div>
    </div>
    
    <!-- Error Display -->
    <div v-if="error" class="border rounded-lg p-4 bg-red-50">
      <h4 class="font-medium text-red-800 mb-2">OCR Processing Error</h4>
      <p class="text-sm text-red-700">{{ error }}</p>
      <button 
        @click="clearError" 
        class="mt-2 px-3 py-1 text-xs bg-red-100 text-red-800 rounded-md hover:bg-red-200"
      >
        Dismiss
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { Upload, FileText, X } from 'lucide-vue-next'
import contractsApi from '@/services/contractsApi'

// Props
const props = defineProps({
  contractId: {
    type: Number,
    required: true
  }
})

// Emits
const emit = defineEmits(['ocr-complete', 'ocr-error'])

// Reactive state
const uploadedFile = ref(null)
const uploading = ref(false)
const ocrProgress = ref(0)
const ocrResults = ref(null)
const error = ref(null)

// Methods
const handleFileUpload = async (event) => {
  const file = event.target.files[0]
  if (!file) return
  
  // Validate file type
  const allowedTypes = ['application/pdf', 'image/jpeg', 'image/png', 'image/tiff']
  if (!allowedTypes.includes(file.type)) {
    error.value = 'Please upload a PDF or image file (JPG, PNG, TIFF)'
    return
  }
  
  // Validate file size (10MB limit)
  const maxSize = 10 * 1024 * 1024 // 10MB
  if (file.size > maxSize) {
    error.value = 'File size must be less than 10MB'
    return
  }
  
  uploadedFile.value = file
  error.value = null
  
  try {
    uploading.value = true
    ocrProgress.value = 0
    
    // Simulate progress
    const progressInterval = setInterval(() => {
      if (ocrProgress.value < 90) {
        ocrProgress.value += Math.random() * 10
      }
    }, 200)
    
    const response = await contractsApi.uploadContractOCR(props.contractId, file)
    
    clearInterval(progressInterval)
    ocrProgress.value = 100
    
    if (response.success !== false) {
      ocrResults.value = response.data
      emit('ocr-complete', response.data)
    } else {
      throw new Error(response.message || 'Failed to process OCR upload')
    }
  } catch (err) {
    console.error('Error uploading file:', err)
    error.value = err.message || 'Failed to process document'
    emit('ocr-error', err)
  } finally {
    uploading.value = false
    setTimeout(() => {
      ocrProgress.value = 0
    }, 1000)
  }
}

const removeFile = () => {
  uploadedFile.value = null
  ocrResults.value = null
  error.value = null
  ocrProgress.value = 0
}

const applyOCRResults = () => {
  emit('ocr-complete', ocrResults.value)
}

const clearOCRResults = () => {
  ocrResults.value = null
}

const clearError = () => {
  error.value = null
}

const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 Bytes'
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}
</script>