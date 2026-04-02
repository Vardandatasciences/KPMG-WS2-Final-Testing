<template>
  <div class="min-h-screen bg-gradient-to-br from-green-50 to-emerald-50 flex items-center justify-center p-4">
    <div class="max-w-2xl w-full bg-white rounded-2xl shadow-2xl overflow-hidden">
      <!-- Header -->
      <div class="bg-gradient-to-r from-green-500 to-emerald-500 p-8 text-center">
        <div class="inline-flex items-center justify-center w-20 h-20 bg-white rounded-full mb-4 animate-bounce">
          <CheckCircle class="h-12 w-12 text-green-500" />
        </div>
        <h1 class="text-3xl font-bold text-white mb-2">Invitation Acknowledged!</h1>
        <p class="text-green-100">Thank you for accepting our invitation</p>
      </div>

      <!-- Content -->
      <div class="p-8">
        <div class="text-center mb-8">
          <h2 class="text-2xl font-semibold text-gray-900 mb-4">
            Welcome to the RFI Process
          </h2>
          <p class="text-gray-600 text-lg">
            We're excited to have you participate! You'll be redirected to the vendor portal in a moment.
          </p>
        </div>

        <!-- Loading Indicator -->
        <div class="flex justify-center mb-8">
          <div class="relative">
            <div class="w-16 h-16 border-4 border-green-200 border-t-green-500 rounded-full animate-spin"></div>
            <div class="absolute inset-0 flex items-center justify-center">
              <Loader2 class="h-8 w-8 text-green-500 animate-pulse" />
            </div>
          </div>
        </div>

        <!-- What's Next -->
        <div class="bg-green-50 border border-green-200 rounded-lg p-6 mb-6">
          <h3 class="text-lg font-semibold text-green-900 mb-3 flex items-center">
            <Info class="h-5 w-5 mr-2" />
            What Happens Next?
          </h3>
          <ul class="space-y-2 text-green-800">
            <li class="flex items-start">
              <CheckCircle class="h-5 w-5 mr-2 mt-0.5 flex-shrink-0" />
              <span>Your acknowledgment has been recorded in our system</span>
            </li>
            <li class="flex items-start">
              <CheckCircle class="h-5 w-5 mr-2 mt-0.5 flex-shrink-0" />
              <span>You'll be redirected to the RFI Vendor Portal</span>
            </li>
            <li class="flex items-start">
              <CheckCircle class="h-5 w-5 mr-2 mt-0.5 flex-shrink-0" />
              <span>Complete the RFI questionnaire with your company information</span>
            </li>
            <li class="flex items-start">
              <CheckCircle class="h-5 w-5 mr-2 mt-0.5 flex-shrink-0" />
              <span>Submit your response before the deadline</span>
            </li>
          </ul>
        </div>

        <!-- RFI Information -->
        <div class="bg-blue-50 border border-blue-200 rounded-lg p-6 mb-6">
          <h3 class="text-lg font-semibold text-blue-900 mb-3 flex items-center">
            <FileText class="h-5 w-5 mr-2" />
            What You'll Need to Provide
          </h3>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm text-blue-800">
            <div class="flex items-start">
              <Building2 class="h-4 w-4 mr-2 mt-0.5 flex-shrink-0" />
              <span>Company Information</span>
            </div>
            <div class="flex items-start">
              <Package class="h-4 w-4 mr-2 mt-0.5 flex-shrink-0" />
              <span>Product & Services Details</span>
            </div>
            <div class="flex items-start">
              <Code class="h-4 w-4 mr-2 mt-0.5 flex-shrink-0" />
              <span>Technology Stack</span>
            </div>
            <div class="flex items-start">
              <Shield class="h-4 w-4 mr-2 mt-0.5 flex-shrink-0" />
              <span>Risk & Compliance Info</span>
            </div>
            <div class="flex items-start">
              <FileText class="h-4 w-4 mr-2 mt-0.5 flex-shrink-0" />
              <span>Legal Terms</span>
            </div>
            <div class="flex items-start">
              <Upload class="h-4 w-4 mr-2 mt-0.5 flex-shrink-0" />
              <span>Supporting Documents</span>
            </div>
          </div>
        </div>

        <!-- Manual Redirect Button -->
        <div class="text-center">
          <p class="text-sm text-gray-600 mb-4">
            If you're not redirected automatically, click the button below:
          </p>
          <button
            @click="redirectToPortal"
            class="inline-flex items-center px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors font-medium shadow-lg hover:shadow-xl"
          >
            <ArrowRight class="h-5 w-5 mr-2" />
            Go to Vendor Portal
          </button>
        </div>
      </div>

      <!-- Footer -->
      <div class="bg-gray-50 px-8 py-6 border-t border-gray-200">
        <p class="text-center text-sm text-gray-600">
          <strong>TPRM Management System</strong><br>
          Third-Party Risk Management | Enterprise Solutions Division<br>
          © {{ new Date().getFullYear() }} All rights reserved
        </p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { CheckCircle, Info, FileText, Building2, Package, Code, Shield, Upload, ArrowRight, Loader2 } from 'lucide-vue-next'

const route = useRoute()
const router = useRouter()

const getTokenFromRoute = () => {
  const paramToken = route.params?.token
  if (paramToken) {
    return String(paramToken)
  }
  return null
}

const redirectToPortal = () => {
  const token = getTokenFromRoute()
  if (token) {
    router.push(`/rfi-vendor-portal/${token}`)
  } else {
    // Fallback: try to get token from URL path
    const pathParts = window.location.pathname.split('/')
    const tokenIndex = pathParts.indexOf('acknowledge') + 1
    if (tokenIndex > 0 && pathParts[tokenIndex]) {
      router.push(`/rfi-vendor-portal/${pathParts[tokenIndex]}`)
    }
  }
}

onMounted(() => {
  // Auto-redirect after 3 seconds
  setTimeout(() => {
    redirectToPortal()
  }, 3000)
})
</script>
