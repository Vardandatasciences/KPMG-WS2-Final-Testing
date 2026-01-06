<template>
  <div class="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
    <!-- Standalone Page - No Navigation -->
    <div class="flex items-center justify-center min-h-screen py-12 px-4 sm:px-6 lg:px-8">
      <div class="max-w-2xl w-full space-y-8">
        <!-- Header -->
        <div class="text-center mb-8">
          <div class="mx-auto h-20 w-20 rounded-full bg-gradient-to-br from-green-400 to-green-600 flex items-center justify-center mb-4 shadow-lg">
            <Trophy class="h-10 w-10 text-white" />
          </div>
          <h1 class="text-3xl font-bold text-gray-900 mb-2">Contract Award Notification</h1>
          <p class="text-gray-600 text-lg">You have received an important contract award notification</p>
        </div>

        <!-- Main Card -->
        <div class="bg-white rounded-xl shadow-2xl border border-gray-100 overflow-hidden">
          <!-- Decorative Header -->
          <div class="bg-gradient-to-r from-green-500 to-green-600 px-8 py-6">
            <div class="flex items-center justify-center gap-3">
              <div class="h-12 w-12 bg-white/20 backdrop-blur-sm rounded-full flex items-center justify-center">
                <Trophy class="h-6 w-6 text-white" />
              </div>
              <div class="text-white">
                <h2 class="text-xl font-bold">Congratulations!</h2>
                <p class="text-green-50 text-sm">Contract Award Notification</p>
              </div>
            </div>
          </div>

          <!-- Content -->
          <div class="p-8">

            <!-- Loading State -->
            <div v-if="loading" class="text-center py-12">
              <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-green-600 mx-auto mb-4"></div>
              <p class="text-gray-600 text-lg">Loading notification...</p>
            </div>

            <!-- Error State -->
            <div v-else-if="error" class="text-center py-12">
              <div class="mx-auto h-20 w-20 rounded-full bg-red-100 flex items-center justify-center mb-6">
                <XCircle class="h-10 w-10 text-red-600" />
              </div>
              <h3 class="text-2xl font-bold text-gray-900 mb-3">Invalid or Expired Link</h3>
              <p class="text-gray-600 text-lg">{{ error }}</p>
              <p class="text-gray-500 mt-4">Please contact the RFP team if you believe this is an error.</p>
            </div>

            <!-- Notification Content -->
            <div v-else-if="notification" class="space-y-6">
              <!-- Award Message -->
              <div class="bg-gradient-to-r from-green-50 to-blue-50 border-l-4 border-green-500 rounded-lg p-6">
                <div class="flex items-start gap-3">
                  <div class="flex-shrink-0">
                    <div class="h-10 w-10 rounded-full bg-green-500 flex items-center justify-center">
                      <Trophy class="h-5 w-5 text-white" />
                    </div>
                  </div>
                  <div class="flex-1">
                    <h3 class="text-lg font-semibold text-gray-900 mb-2">Award Notification</h3>
                    <p class="text-gray-700 leading-relaxed">{{ notification.award_message }}</p>
                  </div>
                </div>
              </div>

              <!-- Vendor Information -->
              <div class="bg-gray-50 rounded-lg p-6">
                <h4 class="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-3">Vendor Information</h4>
                <div class="flex items-center gap-3">
                  <div class="h-12 w-12 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-white font-bold text-lg">
                    {{ notification.vendor_name?.charAt(0) || 'V' }}
                  </div>
                  <div>
                    <p class="font-semibold text-gray-900">{{ notification.vendor_name }}</p>
                    <p class="text-sm text-gray-500">Award Recipient</p>
                  </div>
                </div>
              </div>

              <!-- Next Steps -->
              <div class="bg-blue-50 border border-blue-200 rounded-lg p-6">
                <h4 class="text-sm font-semibold text-blue-900 uppercase tracking-wider mb-3">Next Steps</h4>
                <p class="text-blue-800 leading-relaxed">{{ notification.next_steps }}</p>
              </div>

              <!-- Already Responded States -->
              <div v-if="notification.notification_status === 'accepted'" class="bg-green-50 border-2 border-green-500 rounded-lg p-6">
                <div class="flex items-start gap-4">
                  <div class="flex-shrink-0">
                    <div class="h-12 w-12 rounded-full bg-green-500 flex items-center justify-center">
                      <CheckCircle2 class="h-6 w-6 text-white" />
                    </div>
                  </div>
                  <div class="flex-1">
                    <h4 class="text-lg font-bold text-green-900 mb-2">Award Accepted</h4>
                    <p class="text-green-800">You have already accepted this award. The procurement team will contact you shortly with further instructions.</p>
                  </div>
                </div>
              </div>

              <div v-else-if="notification.notification_status === 'rejected'" class="bg-red-50 border-2 border-red-500 rounded-lg p-6">
                <div class="flex items-start gap-4">
                  <div class="flex-shrink-0">
                    <div class="h-12 w-12 rounded-full bg-red-500 flex items-center justify-center">
                      <XCircle class="h-6 w-6 text-white" />
                    </div>
                  </div>
                  <div class="flex-1">
                    <h4 class="text-lg font-bold text-red-900 mb-2">Award Declined</h4>
                    <p class="text-red-800">You have declined this award. Thank you for your participation in our RFP process.</p>
                  </div>
                </div>
              </div>

              <!-- Action Buttons -->
              <div v-else class="space-y-4">
                <div>
                  <label class="block text-sm font-semibold text-gray-700 mb-2">
                    Additional Comments <span class="text-gray-400 font-normal">(Optional)</span>
                  </label>
                  <textarea
                    v-model="comments"
                    rows="4"
                    class="w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent transition-all"
                    placeholder="Add any comments or questions about this award..."
                  ></textarea>
                </div>

                <!-- Warning for Decline -->
                <div v-if="showDeclineWarning" class="bg-yellow-50 border-2 border-yellow-300 rounded-lg p-4">
                  <div class="flex items-start gap-3">
                    <AlertTriangle class="h-5 w-5 text-yellow-600 flex-shrink-0 mt-0.5" />
                    <div>
                      <h4 class="text-sm font-semibold text-yellow-900 mb-1">Are you sure you want to decline?</h4>
                      <p class="text-sm text-yellow-700 mb-3">
                        Declining this award will notify the RFP team, and they may select an alternate vendor. Please provide a reason in the comments above if possible.
                      </p>
                      <div class="flex gap-2">
                        <button
                          @click="confirmDecline"
                          :disabled="responding"
                          class="inline-flex items-center px-4 py-2 text-sm font-medium text-white bg-red-600 rounded-md hover:bg-red-700 transition-colors disabled:opacity-50"
                        >
                          <XCircle class="h-4 w-4 mr-1" />
                          {{ responding ? 'Processing...' : 'Yes, Decline Award' }}
                        </button>
                        <button
                          @click="showDeclineWarning = false"
                          class="inline-flex items-center px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200 transition-colors"
                        >
                          Cancel
                        </button>
                      </div>
                    </div>
                  </div>
                </div>

                <div class="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-4">
                  <button
                    @click="respondToAward('accept')"
                    :disabled="responding"
                    class="group relative flex items-center justify-center px-6 py-4 text-base font-semibold text-white bg-gradient-to-r from-green-600 to-green-700 rounded-lg hover:from-green-700 hover:to-green-800 transition-all duration-200 shadow-lg hover:shadow-xl disabled:opacity-50 disabled:cursor-not-allowed transform hover:scale-105"
                  >
                    <CheckCircle2 class="h-5 w-5 mr-2" />
                    {{ responding ? 'Processing...' : 'Accept Award' }}
                  </button>
                  <button
                    @click="showDeclineWarning = true"
                    :disabled="responding || showDeclineWarning"
                    class="group relative flex items-center justify-center px-6 py-4 text-base font-semibold text-white bg-gradient-to-r from-red-600 to-red-700 rounded-lg hover:from-red-700 hover:to-red-800 transition-all duration-200 shadow-lg hover:shadow-xl disabled:opacity-50 disabled:cursor-not-allowed transform hover:scale-105"
                  >
                    <XCircle class="h-5 w-5 mr-2" />
                    Decline Award
                  </button>
                </div>

                <p class="text-xs text-gray-500 text-center pt-2">
                  By responding, you acknowledge receipt of this award notification
                </p>
              </div>
            </div>
          </div>

          <!-- Footer -->
          <div class="bg-gray-50 border-t border-gray-200 px-8 py-6">
            <div class="text-center">
              <p class="text-sm text-gray-600 mb-2">
                This is a secure, confidential notification from the RFP Management System
              </p>
              <p class="text-xs text-gray-500">
                If you have any questions, please contact the procurement team directly
              </p>
            </div>
          </div>
        </div>

        <!-- Security Notice -->
        <div class="text-center">
          <p class="text-xs text-gray-500">
            🔒 This link is secure and will expire in 30 days
          </p>
        </div>
      </div>
    </div>
  </div>

  <!-- Popup Modal -->
  <PopupModal />
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import { Trophy, XCircle, CheckCircle2, AlertTriangle } from 'lucide-vue-next'
import PopupModal from '@/popup/PopupModal.vue'
import { PopupService } from '@/popup/popupService'
import loggingService from '@/services/loggingService'

const route = useRoute()
const API_BASE_URL = 'https://grc-tprm.vardaands.com/api/tprm/rfp'

const loading = ref(true)
const error = ref('')
const notification = ref(null)
const comments = ref('')
const responding = ref(false)
const showDeclineWarning = ref(false)

const loadNotification = async () => {
  const awardToken = route.params.token
  if (!awardToken) {
    error.value = 'No token provided'
    loading.value = false
    return
  }

  try {
    const response = await fetch(`${API_BASE_URL}/award-response/${awardToken}/`, {
      method: 'GET'
    })
    if (response.ok) {
      const data = await response.json()
      if (data.success) {
        notification.value = data.notification
      } else {
        error.value = data.error || 'Failed to load notification'
      }
    } else {
      error.value = 'Failed to load notification'
    }
  } catch (err) {
    error.value = 'Network error occurred'
    console.error('Error loading notification:', err)
  } finally {
    loading.value = false
  }
}

const respondToAward = async (action) => {
  const awardToken = route.params.token
  if (!awardToken) return

  responding.value = true
  try {
    const response = await fetch(`${API_BASE_URL}/award-response/${awardToken}/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
      },
      body: JSON.stringify({
        action: action,
        comments: comments.value
      })
    })

    if (response.ok) {
      const data = await response.json()
      if (data.success) {
        if (action === 'accept') {
          PopupService.success('Award accepted successfully! You will receive further instructions via email.', 'Award Accepted')
        } else {
          PopupService.success('Your response has been recorded. The RFP team has been notified.', 'Response Submitted')
        }
        // Reload notification to show updated status
        await loadNotification()
        showDeclineWarning.value = false
      } else {
        PopupService.error('Failed to process response: ' + data.error, 'Processing Failed')
      }
    } else {
      PopupService.error('Failed to process response', 'Response Failed')
    }
  } catch (err) {
    PopupService.error('Error processing response: ' + err.message, 'Error')
    console.error('Error responding to award:', err)
  } finally {
    responding.value = false
  }
}

const confirmDecline = async () => {
  if (!comments.value.trim()) {
    PopupService.warning('Please provide a reason for declining in the comments section above.', 'Comment Required')
    return
  }
  await respondToAward('reject')
}

onMounted(async () => {
  document.body.classList.add('standalone-route')
  document.documentElement.classList.add('standalone-route')

  await loggingService.logPageView('RFP', 'Award Response')
  await loadNotification()
})

onUnmounted(() => {
  document.body.classList.remove('standalone-route')
  document.documentElement.classList.remove('standalone-route')
})
</script>

<style scoped>
.animate-spin {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}
</style>
