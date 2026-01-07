<template>
  <div class="min-h-screen flex items-center justify-center bg-gray-50">
    <div class="max-w-md w-full bg-white rounded-lg shadow-lg p-8 text-center">
      <!-- Icon -->
      <div class="mx-auto flex items-center justify-center h-20 w-20 rounded-full bg-red-100 mb-6">
        <ShieldX class="h-10 w-10 text-red-600" />
      </div>
      
      <!-- Title -->
      <h1 class="text-2xl font-bold text-gray-900 mb-2">Access Denied</h1>
      
      <!-- Description -->
      <p class="text-gray-600 mb-6">
        {{ errorInfo.message }}
      </p>
      
      <!-- Error Code and Permission Info -->
      <div class="mb-6 space-y-2">
        <div v-if="errorInfo.code">
          <span class="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-red-100 text-red-800">
            Error Code: {{ errorInfo.code }}
          </span>
        </div>
        <div v-if="errorInfo.permission || errorInfo.permissionRequired">
          <span class="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-blue-100 text-blue-800">
            Required Permission: {{ errorInfo.permission || errorInfo.permissionRequired }}
          </span>
        </div>
      </div>
      
      <!-- Actions -->
      <div class="space-y-3">
        <Button @click="goBack" class="w-full">
          <ArrowLeft class="w-4 h-4 mr-2" />
          Go Back
        </Button>
        
        <Button variant="outline" @click="goHome" class="w-full">
          <Home class="w-4 h-4 mr-2" />
          Go to Dashboard
        </Button>
        
        <Button variant="ghost" @click="contactSupport" class="w-full">
          <Mail class="w-4 h-4 mr-2" />
          Contact Support
        </Button>
      </div>
      
      <!-- Additional Info -->
      <div class="mt-8 pt-6 border-t border-gray-200">
        <p class="text-sm text-gray-500">
          If you need access to this page, please contact your system administrator.
        </p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Button } from '@/components/ui'
import { ShieldX, ArrowLeft, Home, Mail } from 'lucide-vue-next'

const router = useRouter()

// Props
const props = defineProps({
  message: {
    type: String,
    default: ''
  },
  errorCode: {
    type: String,
    default: ''
  },
  permission: {
    type: String,
    default: ''
  }
})

// Reactive state for error info
const errorInfo = ref({
  message: props.message || 'You do not have permission to access this page. Please contact your administrator if you believe this is an error.',
  code: props.errorCode || '403',
  path: '',
  permission: props.permission || '',
  permissionRequired: ''
})

// Load error info from sessionStorage on mount
onMounted(() => {
  try {
    const storedError = sessionStorage.getItem('access_denied_error')
    if (storedError) {
      const parsedError = JSON.parse(storedError)
      errorInfo.value = {
        message: parsedError.message || errorInfo.value.message,
        code: parsedError.code || errorInfo.value.code,
        path: parsedError.path || '',
        permission: parsedError.permission || '',
        permissionRequired: parsedError.permissionRequired || ''
      }
      // Clear the error from sessionStorage after reading
      sessionStorage.removeItem('access_denied_error')
    }
  } catch (e) {
    console.error('Error reading access denied info:', e)
  }
})

// Methods
const goBack = () => {
  if (window.history.length > 1) {
    router.go(-1)
  } else {
    // Go to appropriate module's home page
    const storedPath = errorInfo.value.path || ''
    
    if (storedPath.includes('/bcp') || storedPath.includes('/vendor-upload') || storedPath.includes('/library')) {
      router.push('/vendor-upload')
    } else if (storedPath.includes('/contract')) {
      router.push('/contracts')
    } else if (storedPath.includes('/rfp')) {
      router.push('/rfp/dashboard')
    } else {
      router.push('/dashboard')
    }
  }
}

const goHome = () => {
  // Detect which module we're in based on the stored path
  const storedPath = errorInfo.value.path || ''
  
  if (storedPath.includes('/bcp') || storedPath.includes('/vendor-upload') || storedPath.includes('/library')) {
    // BCP module
    router.push('/dashboard')
  } else if (storedPath.includes('/contract')) {
    // Contract module
    router.push('/contractdashboard')
  } else if (storedPath.includes('/rfp')) {
    // RFP module
    router.push('/rfp/dashboard')
  } else {
    // Default dashboard
    router.push('/dashboard')
  }
}

const contactSupport = () => {
  // You can implement contact support functionality here
  // For now, we'll just show an alert
  alert('Please contact your system administrator for access to this page.')
}
</script>
