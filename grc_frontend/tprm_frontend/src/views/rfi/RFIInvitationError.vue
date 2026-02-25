<template>
  <div class="min-h-screen bg-gradient-to-br from-red-50 to-pink-50 flex items-center justify-center p-4">
    <div class="max-w-2xl w-full bg-white rounded-2xl shadow-2xl overflow-hidden">
      <!-- Header -->
      <div class="bg-gradient-to-r from-red-600 to-pink-600 p-8 text-center">
        <div class="inline-flex items-center justify-center w-20 h-20 bg-white rounded-full mb-4">
          <AlertTriangle class="h-12 w-12 text-red-600" />
        </div>
        <h1 class="text-3xl font-bold text-white mb-2">Invitation Error</h1>
        <p class="text-red-100">We encountered an issue with your invitation</p>
      </div>

      <!-- Content -->
      <div class="p-8">
        <div class="text-center mb-8">
          <h2 class="text-2xl font-semibold text-gray-900 mb-4">
            {{ errorTitle }}
          </h2>
          <p class="text-gray-600 text-lg">
            {{ errorMessage }}
          </p>
        </div>

        <!-- Error Details -->
        <div class="bg-red-50 border border-red-200 rounded-lg p-6 mb-6">
          <h3 class="text-lg font-semibold text-red-900 mb-3 flex items-center">
            <Info class="h-5 w-5 mr-2" />
            What Could Have Happened?
          </h3>
          <ul class="space-y-2 text-red-800">
            <li class="flex items-start">
              <XCircle class="h-5 w-5 mr-2 mt-0.5 flex-shrink-0" />
              <span>The invitation link may have expired</span>
            </li>
            <li class="flex items-start">
              <XCircle class="h-5 w-5 mr-2 mt-0.5 flex-shrink-0" />
              <span>The invitation may have already been used or declined</span>
            </li>
            <li class="flex items-start">
              <XCircle class="h-5 w-5 mr-2 mt-0.5 flex-shrink-0" />
              <span>The link may have been copied incorrectly</span>
            </li>
            <li class="flex items-start">
              <XCircle class="h-5 w-5 mr-2 mt-0.5 flex-shrink-0" />
              <span>There may be a temporary system issue</span>
            </li>
          </ul>
        </div>

        <!-- Next Steps -->
        <div class="bg-blue-50 border border-blue-200 rounded-lg p-6 mb-6">
          <h3 class="text-lg font-semibold text-blue-900 mb-3 flex items-center">
            <HelpCircle class="h-5 w-5 mr-2" />
            What Should You Do?
          </h3>
          <ul class="space-y-2 text-blue-800">
            <li class="flex items-start">
              <CheckCircle class="h-5 w-5 mr-2 mt-0.5 flex-shrink-0" />
              <span>Check your email for the original invitation and try the link again</span>
            </li>
            <li class="flex items-start">
              <CheckCircle class="h-5 w-5 mr-2 mt-0.5 flex-shrink-0" />
              <span>Make sure you're using the complete URL from the email</span>
            </li>
            <li class="flex items-start">
              <CheckCircle class="h-5 w-5 mr-2 mt-0.5 flex-shrink-0" />
              <span>Contact our support team if the issue persists</span>
            </li>
          </ul>
        </div>

        <!-- Contact Support -->
        <div class="bg-gray-50 rounded-lg p-6 mb-6">
          <h3 class="text-lg font-semibold text-gray-900 mb-3 flex items-center">
            <MessageSquare class="h-5 w-5 mr-2" />
            Need Help?
          </h3>
          <p class="text-gray-600 mb-4">
            Our support team is here to assist you. Please contact us with your invitation details:
          </p>
          <div class="space-y-2 text-sm">
            <div class="flex items-center text-gray-700">
              <Mail class="h-4 w-4 mr-2 text-gray-400" />
              <a href="mailto:support@company.com" class="text-blue-600 hover:underline">support@company.com</a>
            </div>
            <div class="flex items-center text-gray-700">
              <Phone class="h-4 w-4 mr-2 text-gray-400" />
              <span>+1 (555) 123-4567</span>
            </div>
            <div class="flex items-center text-gray-700">
              <Clock class="h-4 w-4 mr-2 text-gray-400" />
              <span>24/7 Support Available</span>
            </div>
          </div>
        </div>

        <!-- Action Buttons -->
        <div class="flex gap-4 justify-center">
          <button
            @click="goBack"
            class="inline-flex items-center px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium"
          >
            <ArrowLeft class="h-5 w-5 mr-2" />
            Go Back
          </button>
          <button
            @click="closeWindow"
            class="inline-flex items-center px-6 py-3 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors font-medium"
          >
            <X class="h-5 w-5 mr-2" />
            Close Window
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
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { AlertTriangle, Info, XCircle, HelpCircle, CheckCircle, MessageSquare, Mail, Phone, Clock, ArrowLeft, X } from 'lucide-vue-next'

const route = useRoute()
const router = useRouter()
const errorType = ref('')

const errorTitle = computed(() => {
  switch (errorType.value) {
    case 'invalid_token':
      return 'Invalid Invitation Link'
    case 'server_error':
      return 'System Error'
    case 'expired':
      return 'Invitation Expired'
    default:
      return 'Unable to Process Invitation'
  }
})

const errorMessage = computed(() => {
  switch (errorType.value) {
    case 'invalid_token':
      return 'The invitation link you used is not valid. This could happen if the link was copied incorrectly or has already been used.'
    case 'server_error':
      return 'We encountered a temporary system error while processing your invitation. Please try again in a few moments.'
    case 'expired':
      return 'This invitation has expired. Please contact the sender for a new invitation if you still wish to participate.'
    default:
      return 'We were unable to process your invitation. Please check the link and try again, or contact support for assistance.'
  }
})

onMounted(() => {
  errorType.value = route.query.error || 'unknown'
})

function goBack() {
  router.go(-1)
}

function closeWindow() {
  window.close()
  // If window.close() doesn't work (some browsers block it), redirect to home
  setTimeout(() => {
    window.location.href = '/'
  }, 100)
}
</script>
