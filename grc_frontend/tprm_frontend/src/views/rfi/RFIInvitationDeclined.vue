<template>
  <div class="min-h-screen bg-gradient-to-br from-red-50 to-orange-50 flex items-center justify-center p-4">
    <div class="max-w-2xl w-full bg-white rounded-2xl shadow-2xl overflow-hidden">
      <!-- Header -->
      <div class="bg-gradient-to-r from-red-500 to-orange-500 p-8 text-center">
        <div class="inline-flex items-center justify-center w-20 h-20 bg-white rounded-full mb-4">
          <XCircle class="h-12 w-12 text-red-500" />
        </div>
        <h1 class="text-3xl font-bold text-white mb-2">Invitation Declined</h1>
        <p class="text-red-100">Thank you for your response</p>
      </div>

      <!-- Content -->
      <div class="p-8">
        <div class="text-center mb-8">
          <h2 class="text-2xl font-semibold text-gray-900 mb-4">
            We've Received Your Response
          </h2>
          <p class="text-gray-600 text-lg">
            Thank you for taking the time to review our RFI invitation. We've recorded your decision to decline participation.
          </p>
        </div>

        <!-- Vendor Info -->
        <div v-if="vendorName" class="bg-gray-50 rounded-lg p-6 mb-6">
          <div class="flex items-center justify-center">
            <Building2 class="h-6 w-6 text-gray-400 mr-2" />
            <p class="text-gray-700 font-medium">{{ vendorName }}</p>
          </div>
        </div>

        <!-- What's Next -->
        <div class="bg-blue-50 border border-blue-200 rounded-lg p-6 mb-6">
          <h3 class="text-lg font-semibold text-blue-900 mb-3 flex items-center">
            <Info class="h-5 w-5 mr-2" />
            What Happens Next?
          </h3>
          <ul class="space-y-2 text-blue-800">
            <li class="flex items-start">
              <CheckCircle class="h-5 w-5 mr-2 mt-0.5 flex-shrink-0" />
              <span>Your decline has been recorded in our system</span>
            </li>
            <li class="flex items-start">
              <CheckCircle class="h-5 w-5 mr-2 mt-0.5 flex-shrink-0" />
              <span>You will not receive further communications about this RFI</span>
            </li>
            <li class="flex items-start">
              <CheckCircle class="h-5 w-5 mr-2 mt-0.5 flex-shrink-0" />
              <span>We may reach out for future opportunities that better match your capabilities</span>
            </li>
            <li class="flex items-start">
              <CheckCircle class="h-5 w-5 mr-2 mt-0.5 flex-shrink-0" />
              <span>Your vendor relationship with us remains in good standing</span>
            </li>
          </ul>
        </div>

        <!-- Feedback Section -->
        <div class="bg-gray-50 rounded-lg p-6 mb-6">
          <h3 class="text-lg font-semibold text-gray-900 mb-3 flex items-center">
            <MessageSquare class="h-5 w-5 mr-2" />
            We Value Your Feedback
          </h3>
          <p class="text-gray-600 mb-4">
            If you'd like to share why you declined or provide any feedback, please feel free to contact us:
          </p>
          <div class="space-y-2 text-sm">
            <div class="flex items-center text-gray-700">
              <Mail class="h-4 w-4 mr-2 text-gray-400" />
              <a href="mailto:rfi@company.com" class="text-blue-600 hover:underline">rfi@company.com</a>
            </div>
            <div class="flex items-center text-gray-700">
              <Phone class="h-4 w-4 mr-2 text-gray-400" />
              <span>+1 (555) 123-4567</span>
            </div>
          </div>
        </div>

        <!-- Action Button -->
        <div class="text-center">
          <button
            @click="closeWindow"
            class="inline-flex items-center px-6 py-3 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors font-medium"
          >
            <X class="h-5 w-5 mr-2" />
            Close This Window
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
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { XCircle, Building2, Info, CheckCircle, MessageSquare, Mail, Phone, X } from 'lucide-vue-next'

const route = useRoute()
const router = useRouter()
const vendorName = ref('')

onMounted(() => {
  vendorName.value = route.query.vendor || ''
})

function closeWindow() {
  window.close()
  // If window.close() doesn't work (some browsers block it), redirect to home
  setTimeout(() => {
    router.push('/')
  }, 100)
}
</script>
