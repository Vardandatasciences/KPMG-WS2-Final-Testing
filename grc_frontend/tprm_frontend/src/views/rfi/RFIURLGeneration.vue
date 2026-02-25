<template>
  <div class="space-y-8">
    <!-- Back Button -->
    <div class="mb-4">
      <a @click.prevent="$router.push('/rfi-vendor-selection')" class="inline-flex items-center gap-2 text-blue-600 hover:text-blue-700 cursor-pointer">
        <ArrowLeft class="h-4 w-4" />
        <span>Back to Vendor Selection</span>
      </a>
    </div>

    <!-- Header -->
    <div>
      <h1 class="text-3xl font-bold text-gray-900">RFI Vendor Invitations</h1>
      <p class="text-gray-600 mt-1">Generate unique invitation URLs and send them to selected vendors for RFI response.</p>
      <div v-if="selectedRFI" class="mt-3 p-3 bg-blue-50 border border-blue-200 rounded-lg">
        <p class="text-sm font-medium text-blue-900">RFI: {{ selectedRFI.rfi_number }} - {{ selectedRFI.rfi_title }}</p>
      </div>
    </div>

    <!-- Metrics -->
    <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
      <div class="bg-white border border-gray-200 rounded-lg p-4">
        <p class="text-sm text-gray-600">Selected Vendors</p>
        <p class="text-2xl font-bold text-gray-900">{{ vendorsCount }}</p>
      </div>
      <div class="bg-white border border-gray-200 rounded-lg p-4">
        <p class="text-sm text-gray-600">URLs Generated</p>
        <p class="text-2xl font-bold text-green-600">{{ generatedUrls.length }}</p>
      </div>
      <div class="bg-white border border-gray-200 rounded-lg p-4">
        <p class="text-sm text-gray-600">Pending</p>
        <p class="text-2xl font-bold text-amber-600">{{ vendorsCount - generatedUrls.length }}</p>
      </div>
    </div>

    <!-- Generate URLs -->
    <div class="bg-white border border-gray-200 rounded-lg shadow-sm p-6">
      <h3 class="text-lg font-semibold text-gray-900 mb-4">Generate & Copy Invitation URLs</h3>
      <p class="text-sm text-gray-600 mb-4">
        Each vendor will receive a unique URL to access the RFI Vendor Portal. Copy the URL and share it via email or your preferred channel.
      </p>
      <div class="flex gap-4">
        <button
          @click="generateAllUrls"
          :disabled="loading || vendorsCount === 0"
          class="inline-flex items-center px-5 py-2.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 font-medium"
        >
          <Loader2 v-if="loading" class="h-5 w-5 mr-2 animate-spin" />
          <Link2 v-else class="h-5 w-5 mr-2" />
          {{ generatedUrls.length ? 'Regenerate All URLs' : 'Generate URLs for All Vendors' }}
        </button>
        <button
          @click="sendEmailInvitations"
          :disabled="loading || generatedUrls.length === 0 || sendingEmails"
          class="inline-flex items-center px-5 py-2.5 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 font-medium"
        >
          <Loader2 v-if="sendingEmails" class="h-5 w-5 mr-2 animate-spin" />
          <Mail v-else class="h-5 w-5 mr-2" />
          Send Email Invitations
        </button>
      </div>
    </div>

    <!-- Vendor URLs Table -->
    <div class="bg-white border border-gray-200 rounded-lg shadow-sm overflow-hidden">
      <div class="px-6 py-4 border-b border-gray-200">
        <h3 class="text-lg font-semibold text-gray-900">Vendor Invitation URLs</h3>
      </div>
      <div class="overflow-x-auto">
        <table class="min-w-full divide-y divide-gray-200">
          <thead class="bg-gray-50">
            <tr>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Vendor</th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Contact</th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Unique URL</th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>
            </tr>
          </thead>
          <tbody class="bg-white divide-y divide-gray-200">
            <tr v-for="item in vendorUrlList" :key="item.key">
              <td class="px-6 py-4 text-sm font-medium text-gray-900">{{ item.company_name }}</td>
              <td class="px-6 py-4 text-sm text-gray-600">{{ item.contact_email || item.vendor_email }}</td>
              <td class="px-6 py-4">
                <code v-if="item.url" class="text-xs bg-gray-100 px-2 py-1 rounded break-all">{{ item.url }}</code>
                <span v-else class="text-gray-400 text-sm">Not generated</span>
              </td>
              <td class="px-6 py-4">
                <span v-if="item.url" class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
                  <Mail class="h-3 w-3 mr-1" />
                  Ready to send
                </span>
                <span v-else class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-600">
                  Pending
                </span>
              </td>
              <td class="px-6 py-4">
                <button
                  v-if="item.url"
                  @click="copyUrl(item.url)"
                  class="inline-flex items-center px-3 py-1.5 text-sm text-blue-600 hover:bg-blue-50 rounded-lg"
                >
                  <Copy class="h-4 w-4 mr-1" />
                  Copy
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Info Box -->
    <div class="bg-blue-50 border border-blue-200 rounded-lg p-4">
      <p class="text-sm text-blue-800 mb-2">
        <strong>📧 Email Invitations:</strong> Click "Send Email Invitations" to automatically send professional invitation emails to all selected vendors. Each email includes:
      </p>
      <ul class="text-sm text-blue-700 ml-4 list-disc space-y-1">
        <li>Unique invitation URL with pre-filled vendor information</li>
        <li>RFI details (title, number, deadline, type)</li>
        <li>Acknowledge and Decline buttons for instant response tracking</li>
        <li>Professional formatting with company branding</li>
      </ul>
      <p class="text-sm text-blue-800 mt-2">
        <strong>Note:</strong> You can also manually copy and share URLs if needed. Vendors will access the RFI Vendor Portal to submit their response with details such as Demos/Trial Version, PoC, Legal terms, Technology Stack, Integration Capabilities, and more.
      </p>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ArrowLeft, Link2, Copy, Loader2, Mail } from 'lucide-vue-next'
import { rfpUseToast } from '@/composables/rfpUseToast.js'
import { useRfpApi } from '@/composables/useRfpApi.js'
import { getTprmApiV1BaseUrl } from '@/utils/backendEnv.js'
import rfiInvitationService from '@/services/rfiInvitationService.js'

const router = useRouter()
const { success, error } = rfpUseToast()
const { getAuthHeaders } = useRfpApi()
const API_BASE = getTprmApiV1BaseUrl()

const selectedRFI = ref(null)
const selectedVendors = ref({ existing: [], manual: [], total: 0 })
const loading = ref(false)
const sendingEmails = ref(false)
const generatedUrls = ref([]) // [{ key, token, url, company_name, contact_email, invitation_id }]

const vendorsCount = computed(() => selectedVendors.value.total || 0)

const vendorUrlList = computed(() => {
  const list = []
  const existing = selectedVendors.value.existing || []
  const manual = selectedVendors.value.manual || []
  existing.forEach((v, i) => {
    const key = `e-${v.vendor_id}-${i}`
    const gen = generatedUrls.value.find(g => g.key === key)
    list.push({
      key,
      company_name: v.company_name,
      contact_email: v.contact_email,
      url: gen?.url
    })
  })
  manual.forEach((v, i) => {
    const key = `m-${i}-${v.vendor_email}`
    const gen = generatedUrls.value.find(g => g.key === key)
    list.push({
      key,
      company_name: v.company_name,
      vendor_email: v.vendor_email,
      contact_email: v.vendor_email,
      url: gen?.url
    })
  })
  return list
})

async function generateAllUrls() {
  if (!selectedRFI.value?.rfi_id) {
    error('No RFI', 'RFI data is missing. Please go back to Vendor Selection.')
    return
  }
  const existing = selectedVendors.value.existing || []
  const manual = selectedVendors.value.manual || []
  const vendors = [
    ...existing.map(v => ({
      vendor_id: v.vendor_id,
      company_name: v.company_name,
      contact_email: v.contact_email,
      contact_name: v.contact_name,
      vendor_phone: v.contact_phone
    })),
    ...manual.map(v => ({
      company_name: v.company_name,
      contact_email: v.vendor_email,
      contact_name: v.vendor_name,
      vendor_phone: v.vendor_phone
    }))
  ]
  if (vendors.length === 0) {
    error('No vendors', 'Please select vendors first.')
    return
  }

  loading.value = true
  try {
    const response = await fetch(`${API_BASE}/rfi-invitations/generate/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...getAuthHeaders()
      },
      body: JSON.stringify({
        rfiId: selectedRFI.value.rfi_id,
        vendors
      })
    })
    const data = await response.json()
    if (data.success && data.invitations) {
      const newUrls = []
      const existing = selectedVendors.value.existing || []
      const manual = selectedVendors.value.manual || []
      let idx = 0
      existing.forEach((v, i) => {
        const inv = data.invitations[idx]
        newUrls.push({
          key: `e-${v.vendor_id}-${i}`,
          token: inv?.unique_token,
          unique_token: inv?.unique_token,
          url: inv?.invitation_url,
          company_name: v.company_name,
          contact_email: v.contact_email,
          invitation_id: inv?.invitation_id,
          vendor_email: v.contact_email,
          vendor_name: v.contact_name
        })
        idx++
      })
      manual.forEach((v, i) => {
        const inv = data.invitations[idx]
        newUrls.push({
          key: `m-${i}-${v.vendor_email}`,
          token: inv?.unique_token,
          unique_token: inv?.unique_token,
          url: inv?.invitation_url,
          company_name: v.company_name,
          contact_email: v.vendor_email,
          invitation_id: inv?.invitation_id,
          vendor_email: v.vendor_email,
          vendor_name: v.vendor_name
        })
        idx++
      })
      generatedUrls.value = newUrls
      success('URLs Generated', `${newUrls.length} invitation(s) stored. Click "Send Email Invitations" to notify vendors.`)
    } else {
      console.error('[RFI URL Generation] Error response:', data)
      if (data.traceback) {
        console.error('[RFI URL Generation] Traceback:', data.traceback)
      }
      error('Failed', data.error || 'Could not generate invitations.')
    }
  } catch (e) {
    error('Error', e?.message || 'Failed to generate invitations.')
  } finally {
    loading.value = false
  }
}

function copyUrl(url) {
  navigator.clipboard.writeText(url).then(() => {
    success('Copied', 'URL copied to clipboard.')
  }).catch(() => {
    error('Copy failed', 'Could not copy to clipboard.')
  })
}

async function sendEmailInvitations() {
  if (generatedUrls.value.length === 0) {
    error('No URLs', 'Please generate URLs first.')
    return
  }
  
  if (!selectedRFI.value) {
    error('No RFI', 'RFI data is missing.')
    return
  }
  
  sendingEmails.value = true
  try {
    console.log('[RFI EMAIL] Preparing to send emails...')
    
    // Prepare invitations data for email sending
    const invitations = generatedUrls.value.map(urlData => ({
      invitation_id: urlData.invitation_id,
      invitation_url: urlData.url,
      vendor_email: urlData.vendor_email || urlData.contact_email,
      vendor_name: urlData.vendor_name || urlData.company_name,
      company_name: urlData.company_name,
      unique_token: urlData.unique_token || urlData.token
    }))
    
    // Prepare RFI data
    const rfiData = {
      rfi_title: selectedRFI.value.rfi_title,
      rfi_number: selectedRFI.value.rfi_number,
      rfi_type: selectedRFI.value.rfi_type,
      deadline: selectedRFI.value.deadline || 'TBD'
    }
    
    console.log('[RFI EMAIL] Sending emails for', invitations.length, 'invitations')
    
    // Send emails using the service
    const emailResponse = await rfiInvitationService.sendInvitationEmails(invitations, rfiData)
    
    console.log('[RFI EMAIL] Email response:', emailResponse)
    
    if (emailResponse && emailResponse.success !== false) {
      const sentCount = emailResponse.sent_emails?.length || 0
      const failedCount = emailResponse.failed_emails?.length || 0
      
      if (sentCount > 0) {
        success(
          'Emails Sent',
          `Successfully sent ${sentCount} invitation email(s)${failedCount > 0 ? `. ${failedCount} failed.` : '.'}`
        )
      } else {
        error('No emails sent', 'Failed to send any invitation emails.')
      }
      
      if (failedCount > 0) {
        console.error('[RFI EMAIL] Failed emails:', emailResponse.failed_emails)
        emailResponse.failed_emails.forEach(failed => {
          console.error(`❌ Failed to send to ${failed.vendor_email}: ${failed.error}`)
        })
      }
    } else {
      error('Email sending failed', emailResponse?.error || 'Could not send emails. Check console for details.')
    }
  } catch (e) {
    console.error('[RFI EMAIL] Error:', e)
    error('Error', e?.message || 'Failed to send invitation emails.')
  } finally {
    sendingEmails.value = false
  }
}

onMounted(() => {
  const rfiData = localStorage.getItem('selectedRFI')
  const vendorsData = localStorage.getItem('selectedRFIVendors')
  if (rfiData) {
    try {
      selectedRFI.value = JSON.parse(rfiData)
    } catch (e) {
      error('Invalid RFI data', 'Please go back to Vendor Selection.')
      return
    }
  } else {
    error('No RFI', 'Please start from RFI List and select vendors.')
    return
  }
  if (vendorsData) {
    try {
      selectedVendors.value = JSON.parse(vendorsData)
    } catch (e) {
      error('Invalid vendors data', 'Please go back to Vendor Selection.')
    }
  } else {
    error('No vendors', 'Please select vendors first.')
  }
})
</script>
