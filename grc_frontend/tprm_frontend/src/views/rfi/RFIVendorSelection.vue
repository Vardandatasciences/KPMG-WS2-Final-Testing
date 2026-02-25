<template>
  <div class="space-y-8">
    <!-- Back Button -->
    <div class="mb-4">
      <a @click.prevent="$router.push('/rfi-list')" class="inline-flex items-center gap-2 text-blue-600 hover:text-blue-700 cursor-pointer">
        <ArrowLeft class="h-4 w-4" />
        <span>Back to RFI List</span>
      </a>
    </div>

    <!-- Header -->
    <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
      <div class="space-y-2">
        <h1 class="text-3xl font-bold text-gray-900">Select Vendors for RFI</h1>
        <p class="text-gray-600">
          Select vendors to send this RFI to. Selected vendors will receive an invitation URL to respond.
        </p>
        <!-- RFI Context -->
        <div v-if="selectedRFI" class="mt-3 p-3 bg-blue-50 border border-blue-200 rounded-lg">
          <div class="flex items-center gap-2 mb-1">
            <span class="text-sm font-medium text-blue-900">Processing RFI:</span>
            <span class="font-mono text-sm text-blue-700">{{ selectedRFI.rfi_number }}</span>
          </div>
          <p class="text-sm text-blue-800">{{ selectedRFI.rfi_title }}</p>
          <p class="text-xs text-blue-600 mt-1" v-if="selectedRFI.estimated_value">
            Estimated Value: {{ formatCurrency(selectedRFI.estimated_value) }} • Type: {{ selectedRFI.rfi_type }}
          </p>
        </div>
      </div>
    </div>

    <!-- Vendor Selection Tabs -->
    <div class="bg-white rounded-lg border border-gray-200 shadow-sm">
      <div class="border-b border-gray-200">
        <nav class="flex space-x-8 px-6">
          <button
            v-for="tab in tabs"
            :key="tab.id"
            @click="activeTab = tab.id"
            :class="[
              'py-4 px-1 border-b-2 font-medium text-sm transition-colors',
              activeTab === tab.id
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            ]"
          >
            <component :is="tab.icon" class="h-4 w-4 inline mr-2" />
            {{ tab.name }}
            <span v-if="tab.count !== undefined" class="ml-2 bg-gray-100 text-gray-600 py-0.5 px-2 rounded-full text-xs">
              {{ tab.count }}
            </span>
          </button>
        </nav>
      </div>

      <!-- Existing Vendors Tab -->
      <div v-if="activeTab === 'existing'" class="p-6">
        <div class="mb-4">
          <input
            v-model="searchTerm"
            type="text"
            placeholder="Search vendors by name, capabilities..."
            class="w-full max-w-md p-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
        <div class="space-y-3">
          <div
            v-for="vendor in filteredVendors"
            :key="vendor.vendor_id"
            :class="[
              'flex items-center gap-4 p-4 rounded-xl border-2 transition-all',
              selectedVendorIds.includes(vendor.vendor_id)
                ? 'border-blue-500 bg-blue-50'
                : 'border-gray-200 hover:border-blue-300 bg-white'
            ]"
          >
            <input
              type="checkbox"
              :checked="selectedVendorIds.includes(vendor.vendor_id)"
              @change="toggleVendor(vendor.vendor_id)"
              class="h-4 w-4 text-blue-600 rounded"
            />
            <div class="w-12 h-12 rounded-full bg-blue-600 text-white font-bold flex items-center justify-center">
              {{ (vendor.company_name || 'V').charAt(0) }}
            </div>
            <div class="flex-1 min-w-0">
              <h3 class="font-bold text-gray-900">{{ vendor.company_name }}</h3>
              <p class="text-sm text-gray-600">{{ getPrimaryContactName(vendor) }}</p>
              <p class="text-xs text-gray-500">{{ getPrimaryContactEmail(vendor) }}</p>
            </div>
            <span class="px-2.5 py-1 bg-green-100 text-green-800 rounded-full text-xs font-semibold">
              {{ vendor.status || 'APPROVED' }}
            </span>
          </div>
        </div>
        <p v-if="filteredVendors.length === 0 && !loading" class="text-center py-8 text-gray-500">
          No vendors found. {{ searchTerm ? 'Try a different search.' : 'Load vendors from RFI List first.' }}
        </p>
        <div v-if="loading" class="text-center py-8">
          <Loader2 class="h-8 w-8 animate-spin mx-auto text-blue-600" />
          <p class="text-gray-600 mt-2">Loading vendors...</p>
        </div>
      </div>

      <!-- Manual Tab -->
      <div v-if="activeTab === 'manual'" class="p-6">
        <div class="space-y-4">
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Company Name *</label>
              <input v-model="manualVendor.company_name" type="text" class="w-full p-3 border rounded-lg" placeholder="Acme Corp" />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Contact Name *</label>
              <input v-model="manualVendor.vendor_name" type="text" class="w-full p-3 border rounded-lg" placeholder="John Doe" />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Email *</label>
              <input v-model="manualVendor.vendor_email" type="email" class="w-full p-3 border rounded-lg" placeholder="john@acme.com" />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Phone *</label>
              <input v-model="manualVendor.vendor_phone" type="tel" class="w-full p-3 border rounded-lg" placeholder="+1-555-0100" />
            </div>
          </div>
          <button
            @click="addManualVendor"
            class="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            <Plus class="h-4 w-4 mr-2" />
            Add Vendor
          </button>
          <div v-if="manualVendors.length > 0" class="mt-4 space-y-2">
            <p class="font-medium text-gray-700">Added vendors:</p>
            <div
              v-for="(v, idx) in manualVendors"
              :key="idx"
              class="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
            >
              <span>{{ v.company_name }} - {{ v.vendor_email }}</span>
              <button @click="removeManualVendor(idx)" class="text-red-600 hover:text-red-800 text-sm">Remove</button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Proceed Button -->
    <div class="flex justify-end gap-4">
      <button
        @click="handleProceedToURLGeneration"
        :disabled="totalSelected === 0 || isProceeding"
        class="inline-flex items-center px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed font-medium"
      >
        <Loader2 v-if="isProceeding" class="h-5 w-5 mr-2 animate-spin" />
        <ArrowRight v-else class="h-5 w-5 mr-2" />
        Proceed to URL Generation ({{ totalSelected }} selected)
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Users, Plus, ArrowLeft, ArrowRight, Loader2 } from 'lucide-vue-next'
import { rfpUseToast } from '@/composables/rfpUseToast.js'
import { useRfpApi } from '@/composables/useRfpApi.js'
import api from '@/utils/api_rfp.js'

const router = useRouter()
const { success, error } = rfpUseToast()
const { getAuthHeaders } = useRfpApi()

const activeTab = ref('existing')
const tabs = [
  { id: 'existing', name: 'Approved Vendors', icon: Users, count: 0 },
  { id: 'manual', name: 'Manual Creation', icon: Plus, count: 0 }
]

const selectedRFI = ref(null)
const searchTerm = ref('')
const loading = ref(false)
const isProceeding = ref(false)
const existingVendors = ref([])
const selectedVendorIds = ref([])
const manualVendors = ref([])
const manualVendor = ref({
  company_name: '',
  vendor_name: '',
  vendor_email: '',
  vendor_phone: '',
  website: '',
  industry_sector: '',
  description: ''
})

const filteredVendors = computed(() => {
  if (!existingVendors.value || !Array.isArray(existingVendors.value)) return []
  const q = searchTerm.value.toLowerCase()
  if (!q) return existingVendors.value
  return existingVendors.value.filter(v => 
    (v.company_name || '').toLowerCase().includes(q) ||
    (v.capabilities || []).some(c => c.toLowerCase().includes(q))
  )
})

const totalSelected = computed(() => {
  const existing = selectedVendorIds.value.length
  const manual = manualVendors.value.length
  return existing + manual
})

function getPrimaryContactName(v) {
  if (v.primary_contact) {
    return [v.primary_contact.first_name, v.primary_contact.last_name].filter(Boolean).join(' ') || 'No contact'
  }
  return v.contact_name || v.vendor_name || 'No contact'
}

function getPrimaryContactEmail(v) {
  return v.primary_contact?.email || v.email || v.vendor_email || 'No email'
}

function formatCurrency(val) {
  if (val == null) return 'N/A'
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(Number(val))
}

function toggleVendor(id) {
  const idx = selectedVendorIds.value.indexOf(id)
  if (idx >= 0) {
    selectedVendorIds.value = selectedVendorIds.value.filter(x => x !== id)
  } else {
    selectedVendorIds.value = [...selectedVendorIds.value, id]
  }
}

function addManualVendor() {
  const v = manualVendor.value
  if (!v.company_name?.trim() || !v.vendor_name?.trim() || !v.vendor_email?.trim() || !v.vendor_phone?.trim()) {
    error('Validation', 'Please fill Company Name, Contact Name, Email, and Phone.')
    return
  }
  manualVendors.value.push({ ...v })
  manualVendor.value = { company_name: '', vendor_name: '', vendor_email: '', vendor_phone: '', website: '', industry_sector: '', description: '' }
  success('Vendor Added', 'Vendor added to selection.')
}

function removeManualVendor(idx) {
  manualVendors.value.splice(idx, 1)
}

async function loadVendors() {
  loading.value = true
  try {
    console.log('[RFI Vendor Selection] Fetching vendors...')
    const response = await api.get('/vendor-core/vendors/', {
      params: { status: 'APPROVED' },
      headers: getAuthHeaders()
    })
    const data = response.data
    console.log('[RFI Vendor Selection] Vendors response:', data)
    
    let vendors = []
    if (data?.vendors && Array.isArray(data.vendors)) vendors = data.vendors
    else if (Array.isArray(data)) vendors = data
    else if (data?.results) vendors = data.results

    console.log(`[RFI Vendor Selection] Found ${vendors.length} vendors`)

    const withContacts = []
    for (const v of vendors) {
      try {
        console.log(`[RFI Vendor Selection] Fetching contacts for vendor ${v.vendor_id}...`)
        const cr = await api.get('/vendor-core/vendor-contacts/', {
          params: { vendor_id: v.vendor_id, contact_type: 'PRIMARY', is_active: 1 },
          headers: getAuthHeaders()
        })
        const cd = cr.data
        console.log(`[RFI Vendor Selection] Contacts response for vendor ${v.vendor_id}:`, cd)
        
        const primary = (cd?.contacts?.[0] ?? cd?.results?.[0]) || (Array.isArray(cd) ? cd[0] : null)
        
        if (primary) {
          console.log(`[RFI Vendor Selection] Found primary contact for vendor ${v.vendor_id}:`, primary)
        } else {
          console.warn(`[RFI Vendor Selection] No primary contact found for vendor ${v.vendor_id}`)
        }
        
        withContacts.push({
          ...v,
          primary_contact: primary,
          contact_name: primary ? `${primary.first_name || ''} ${primary.last_name || ''}`.trim() : '',
          email: primary?.email || '',
          vendor_name: primary ? `${primary.first_name || ''} ${primary.last_name || ''}`.trim() : '',
          vendor_phone: primary?.phone || primary?.mobile || ''
        })
      } catch (contactErr) {
        console.error(`[RFI Vendor Selection] Error fetching contacts for vendor ${v.vendor_id}:`, contactErr)
        withContacts.push({ 
          ...v, 
          primary_contact: null, 
          contact_name: '', 
          email: '', 
          vendor_name: '',
          vendor_phone: ''
        })
      }
    }
    
    console.log(`[RFI Vendor Selection] Loaded ${withContacts.length} vendors with contacts`)
    existingVendors.value = withContacts
    tabs[0].count = withContacts.length
  } catch (err) {
    console.error('[RFI Vendor Selection] Error loading vendors:', err)
    error('Failed to load vendors', err?.message || 'Please try again.')
    existingVendors.value = []
  } finally {
    loading.value = false
  }
}

function handleProceedToURLGeneration() {
  if (totalSelected.value === 0) {
    error('No vendors selected', 'Please select at least one vendor.')
    return
  }
  if (!selectedRFI.value) {
    error('No RFI', 'RFI data is missing. Please go back to RFI List and try again.')
    return
  }

  const existing = (existingVendors.value || []).filter(v => selectedVendorIds.value.includes(v.vendor_id))
  const allVendors = {
    existing: existing.map(v => ({
      vendor_id: parseInt(v.vendor_id),
      company_name: v.company_name,
      vendor_type: 'existing',
      contact_name: getPrimaryContactName(v),
      contact_email: getPrimaryContactEmail(v),
      contact_phone: v.primary_contact?.phone || v.primary_contact?.mobile || v.phone || ''
    })),
    manual: manualVendors.value.map(v => ({
      company_name: v.company_name,
      vendor_name: v.vendor_name,
      vendor_email: v.vendor_email,
      vendor_phone: v.vendor_phone,
      vendor_type: 'manual'
    })),
    total: totalSelected.value
  }

  localStorage.setItem('selectedRFIVendors', JSON.stringify(allVendors))
  localStorage.setItem('selectedRFI', JSON.stringify(selectedRFI.value))
  success('Ready', `${totalSelected.value} vendor(s) ready for URL generation.`)
  router.push('/rfi-url-generation')
}

onMounted(async () => {
  const rfiData = localStorage.getItem('selectedRFI')
  if (rfiData) {
    try {
      selectedRFI.value = JSON.parse(rfiData)
    } catch (e) {
      error('Invalid RFI data', 'Please select an RFI from the list first.')
      return
    }
  } else {
    error('No RFI selected', 'Please select an RFI from the RFI List and click "Select Vendors".')
    return
  }
  await loadVendors()
})
</script>
