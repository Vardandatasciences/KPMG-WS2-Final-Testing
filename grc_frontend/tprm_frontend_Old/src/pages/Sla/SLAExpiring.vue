<template>
  <div class="flex-1 space-y-6 p-6">
    <div class="flex items-center justify-between">
      <div>
        <h2 class="text-3xl font-bold tracking-tight">Expired & Expiring SLAs</h2>
        <p class="text-muted-foreground">
          SLAs that have expired or are approaching expiration and require renewal or review
        </p>
      </div>
      <div class="flex items-center gap-2">
        <Badge variant="destructive">
          {{ expiringSLAs.filter(sla => sla.daysUntilExpiry <= 7).length }} Critical
        </Badge>
        <Badge variant="secondary" class="bg-yellow-100 text-yellow-800">
          {{ expiringSLAs.filter(sla => sla.daysUntilExpiry <= 30 && sla.daysUntilExpiry > 7).length }} Upcoming
        </Badge>
        <Badge v-if="expiringSLAs.filter(sla => sla.notified).length > 0" variant="secondary" class="bg-green-100 text-green-800">
          {{ expiringSLAs.filter(sla => sla.notified).length }} Notified
        </Badge>
      </div>
    </div>

    <!-- Summary Cards -->
    <div class="grid gap-4 md:grid-cols-4">
      <Card>
        <CardHeader class="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle class="text-sm font-medium">Expired SLAs</CardTitle>
          <AlertTriangle class="h-4 w-4 text-red-500" />
        </CardHeader>
        <CardContent>
          <div class="text-2xl font-bold text-red-600">
            {{ expiringSLAs.filter(sla => sla.status === 'EXPIRED' || sla.daysUntilExpiry < 0).length }}
          </div>
          <p class="text-xs text-muted-foreground">
            Immediate renewal required
          </p>
        </CardContent>
      </Card>
      
      <Card>
        <CardHeader class="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle class="text-sm font-medium">Expiring Soon (≤7 days)</CardTitle>
          <AlertTriangle class="h-4 w-4 text-orange-500" />
        </CardHeader>
        <CardContent>
          <div class="text-2xl font-bold text-orange-600">
            {{ expiringSLAs.filter(sla => sla.daysUntilExpiry <= 7 && sla.daysUntilExpiry >= 0).length }}
          </div>
          <p class="text-xs text-muted-foreground">
            Critical attention required
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader class="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle class="text-sm font-medium">Expiring This Month</CardTitle>
          <Calendar class="h-4 w-4 text-yellow-500" />
        </CardHeader>
        <CardContent>
          <div class="text-2xl font-bold text-yellow-600">
            {{ expiringSLAs.filter(sla => sla.daysUntilExpiry <= 30 && sla.daysUntilExpiry > 7).length }}
          </div>
          <p class="text-xs text-muted-foreground">
            Plan renewal actions
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader class="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle class="text-sm font-medium">Manual Renewal Required</CardTitle>
          <Clock class="h-4 w-4 text-blue-500" />
        </CardHeader>
        <CardContent>
          <div class="text-2xl font-bold text-blue-600">
            {{ expiringSLAs.filter(sla => !sla.autoRenewal).length }}
          </div>
          <p class="text-xs text-muted-foreground">
            Manual intervention needed
          </p>
        </CardContent>
      </Card>
    </div>

    <!-- Filters -->
    <Card>
      <CardHeader>
        <CardTitle class="flex items-center gap-2">
          <Filter class="h-5 w-5" />
          Filters
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div class="flex gap-4 items-center">
          <div class="flex-1">
            <div class="relative">
              <Search class="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search expiring SLAs..."
                v-model="searchTerm"
                class="pl-8"
              />
            </div>
          </div>
          <Select v-model="criticalityFilter">
            <SelectTrigger class="w-[180px]">
              <SelectValue placeholder="Criticality" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Criticality</SelectItem>
              <SelectItem value="critical">Critical</SelectItem>
              <SelectItem value="high">High</SelectItem>
              <SelectItem value="medium">Medium</SelectItem>
              <SelectItem value="low">Low</SelectItem>
            </SelectContent>
          </Select>
          <Select v-model="renewalFilter">
            <SelectTrigger class="w-[180px]">
              <SelectValue placeholder="Renewal Type" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Types</SelectItem>
              <SelectItem value="auto">Auto-Renewal</SelectItem>
              <SelectItem value="manual">Manual Renewal</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </CardContent>
    </Card>

    <!-- Loading State -->
    <div v-if="loading" class="flex items-center justify-center p-8">
      <div class="text-center">
        <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
        <p class="mt-2 text-sm text-muted-foreground">Loading expiring SLAs...</p>
      </div>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="bg-red-50 border border-red-200 rounded-md p-4">
      <div class="flex">
        <div class="ml-3">
          <h3 class="text-sm font-medium text-red-800">Error loading data</h3>
          <div class="mt-2 text-sm text-red-700">
            <p>{{ error }}</p>
          </div>
          <div class="mt-4">
            <button @click="loadData" class="bg-red-100 px-3 py-2 rounded-md text-sm font-medium text-red-800 hover:bg-red-200">
              Try again
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Expiring SLAs Table -->
    <Card v-else>
      <CardHeader>
        <CardTitle>Expired & Expiring SLAs</CardTitle>
        <CardDescription>
          SLAs that have expired or are approaching expiration and require renewal or review
        </CardDescription>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>SLA ID</TableHead>
              <TableHead>SLA Name</TableHead>
              <TableHead>Vendor</TableHead>
              <TableHead>Expiry Date</TableHead>
              <TableHead>Days Until Expiry</TableHead>
              <TableHead>Criticality</TableHead>
              <TableHead>Auto-Renewal</TableHead>
              <TableHead>Renewal Status</TableHead>
              <TableHead>Notification Status</TableHead>
              <TableHead>Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            <TableRow v-for="sla in filteredSLAs" :key="sla.id">
              <TableCell class="font-mono text-sm">{{ sla.id }}</TableCell>
              <TableCell class="font-medium">{{ sla.name }}</TableCell>
              <TableCell>{{ sla.vendor }}</TableCell>
              <TableCell>{{ sla.currentExpiry }}</TableCell>
              <TableCell>
                <div class="flex items-center gap-2">
                  <AlertTriangle v-if="sla.status === 'EXPIRED' || sla.daysUntilExpiry < 0" class="h-4 w-4 text-red-600" />
                  <AlertTriangle v-else-if="sla.daysUntilExpiry <= 7" class="h-4 w-4 text-orange-600" />
                  <Clock v-else-if="sla.daysUntilExpiry <= 30" class="h-4 w-4 text-yellow-600" />
                  <Calendar v-else class="h-4 w-4 text-green-600" />
                  <span :class="getExpiryUrgency(sla.daysUntilExpiry, sla.status)">
                    {{ sla.daysUntilExpiry < 0 ? 'Expired' : sla.daysUntilExpiry + ' days' }}
                  </span>
                </div>
              </TableCell>
              <TableCell>
                <Badge v-if="sla.criticality.toLowerCase() === 'critical'" variant="destructive">Critical</Badge>
                <Badge v-else-if="sla.criticality.toLowerCase() === 'high'" variant="secondary" class="bg-red-100 text-red-800">High</Badge>
                <Badge v-else-if="sla.criticality.toLowerCase() === 'medium'" variant="secondary" class="bg-yellow-100 text-yellow-800">Medium</Badge>
                <Badge v-else-if="sla.criticality.toLowerCase() === 'low'" variant="secondary" class="bg-blue-100 text-blue-800">Low</Badge>
                <Badge v-else variant="outline">{{ sla.criticality }}</Badge>
              </TableCell>
              <TableCell>
                <Badge v-if="sla.autoRenewal" variant="secondary" class="bg-green-100 text-green-800">Yes</Badge>
                <Badge v-else variant="outline">No</Badge>
              </TableCell>
              <TableCell>
                <Badge v-if="sla.renewalStatus.toLowerCase().includes('expired')" variant="destructive">{{ sla.renewalStatus }}</Badge>
                <Badge v-else-if="sla.renewalStatus.toLowerCase().includes('critical')" variant="destructive" class="bg-red-100 text-red-800">{{ sla.renewalStatus }}</Badge>
                <Badge v-else-if="sla.renewalStatus.toLowerCase().includes('auto-renewal')" variant="secondary" class="bg-green-100 text-green-800">{{ sla.renewalStatus }}</Badge>
                <Badge v-else-if="sla.renewalStatus.toLowerCase().includes('in progress')" variant="secondary" class="bg-blue-100 text-blue-800">{{ sla.renewalStatus }}</Badge>
                <Badge v-else-if="sla.renewalStatus.toLowerCase().includes('under review')" variant="secondary" class="bg-yellow-100 text-yellow-800">{{ sla.renewalStatus }}</Badge>
                <Badge v-else variant="outline">{{ sla.renewalStatus }}</Badge>
              </TableCell>
              <TableCell>
                <Badge v-if="sla.notified" variant="secondary" class="bg-green-100 text-green-800">
                  Notified
                </Badge>
                <Badge v-else variant="outline">
                  Pending
                </Badge>
              </TableCell>
              <TableCell>
                <div class="flex items-center gap-2">
                  <Button variant="outline" size="sm" @click="handleViewSLA(sla)">
                    <Eye class="h-4 w-4" />
                  </Button>
                  <Button 
                    :variant="sla.notified ? 'secondary' : (sla.status === 'EXPIRED' || sla.daysUntilExpiry < 0 ? 'destructive' : 'default')" 
                    size="sm" 
                    @click="handleRenewSLA(sla)"
                    :disabled="sla.notified"
                  >
                    <RefreshCw class="h-4 w-4" />
                    {{ sla.notified ? 'Notified' : (sla.status === 'EXPIRED' || sla.daysUntilExpiry < 0 ? 'Renew Now' : 'Renew') }}
                  </Button>
                  <Button 
                    v-if="sla.notified"
                    variant="outline" 
                    size="sm" 
                    @click="clearNotification(sla)"
                    class="flex items-center gap-1"
                  >
                    <X class="h-3 w-3" />
                    Clear
                  </Button>
                </div>
              </TableCell>
            </TableRow>
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  </div>

  <!-- Popup Modal -->
  <PopupModal />
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { AlertTriangle, Search, Filter, Eye, RefreshCw, Calendar, Clock, X } from 'lucide-vue-next'
import apiService from '@/services/api'
import PopupModal from '@/popup/PopupModal.vue'
import { PopupService } from '@/popup/popupService'
import { useNotifications } from '@/composables/useNotifications'
import loggingService from '@/services/loggingService'

const router = useRouter()
const { showSLASuccess, showSLAError, showSLAWarning, showInfo } = useNotifications()

const searchTerm = ref("")
const criticalityFilter = ref("all")
const renewalFilter = ref("all")
const loading = ref(false)
const error = ref(null)

// API data
const expiringSLAs = ref([])

// Load data from API
const loadData = async () => {
  loading.value = true
  error.value = null
  
  try {
    // Load SLAs from backend
    const slasData = await apiService.getSLAs()
    
    // Filter SLAs that are expiring (within 90 days) or already expired
    const today = new Date()
    const ninetyDaysFromNow = new Date(today.getTime() + (90 * 24 * 60 * 60 * 1000))
    
    // Get notified SLAs from localStorage
    const notifiedSLAs = JSON.parse(localStorage.getItem('notifiedSLAs') || '[]')
    
    expiringSLAs.value = slasData.filter(sla => {
      const expiryDate = new Date(sla.expiry_date)
      const daysUntilExpiry = getDaysUntilExpiry(sla.expiry_date)
      
      // Include SLAs that are:
      // 1. Expired (status = 'EXPIRED' or daysUntilExpiry < 0)
      // 2. Expiring within 90 days (status = 'ACTIVE' and daysUntilExpiry <= 90)
      return (sla.status === 'EXPIRED' || daysUntilExpiry < 0) || 
             (sla.status === 'ACTIVE' && daysUntilExpiry <= 90)
    }).map(sla => ({
      id: sla.sla_id,
      name: sla.sla_name,
      vendor: getVendorName(sla),
      product: sla.business_service_impacted || 'Service',
      type: sla.sla_type,
      currentExpiry: sla.expiry_date,
      daysUntilExpiry: getDaysUntilExpiry(sla.expiry_date),
      status: sla.status,
      autoRenewal: determineAutoRenewal(sla),
      renewalStatus: getRenewalStatus(sla),
      criticality: getCriticalityLevel(sla),
      lastReview: sla.effective_date,
      notified: notifiedSLAs.includes(sla.sla_id),
      notifiedAt: notifiedSLAs.includes(sla.sla_id) ? new Date().toISOString() : null
    }))
    
    console.log('Loaded expiring/expired SLAs:', expiringSLAs.value.length)
    console.log('Notified SLAs from localStorage:', notifiedSLAs)
    console.log('SLAs with notified status:', expiringSLAs.value.filter(sla => sla.notified))
    
  } catch (err) {
    error.value = err.message
    console.error('Error loading expiring SLAs:', err)
    PopupService.error('Error loading expiring SLAs. Please try again later.', 'Loading Error')
  } finally {
    loading.value = false
  }
}

// Load data on component mount
onMounted(async () => {
  await loggingService.logPageView('SLA', 'Expiring SLAs')
  await loadData()
})

// Helper functions based on vendor_slas table data
const getDaysUntilExpiry = (expiryDate) => {
  const today = new Date()
  const expiry = new Date(expiryDate)
  const diff = Math.ceil((expiry.getTime() - today.getTime()) / (1000 * 60 * 60 * 24))
  return diff
}

// Helper function to get vendor name (handles both nested objects and ID-based relationships)
const getVendorName = (sla) => {
  // Check if SLA has nested vendor object
  if (sla.vendor && typeof sla.vendor === 'object') {
    return sla.vendor.company_name || 'Unknown Vendor'
  }
  
  // Fallback to looking up by vendor_id (if vendors array is available)
  if (sla.vendor_id) {
    // This would require loading vendors separately, for now return a placeholder
    return 'Vendor ID: ' + sla.vendor_id
  }
  
  return 'Unknown Vendor'
}

const determineAutoRenewal = (sla) => {
  // Determine auto-renewal based on SLA characteristics
  // In a real implementation, this would be a field in the database
  // For now, we'll use business logic based on SLA type and contract terms
  if (sla.sla_type === 'AVAILABILITY' && sla.business_service_impacted?.toLowerCase().includes('critical')) {
    return true // Critical services often have auto-renewal
  }
  if (sla.contract?.contract_type === 'MASTER_AGREEMENT') {
    return true // Master agreements often have auto-renewal
  }
  return false // Default to manual renewal
}

const getRenewalStatus = (sla) => {
  const days = getDaysUntilExpiry(sla.expiry_date)
  const autoRenewal = determineAutoRenewal(sla)
  
  // Handle expired SLAs
  if (sla.status === 'EXPIRED' || days < 0) {
    if (autoRenewal) return 'Expired - Auto-Renewal Failed'
    return 'Expired - Manual Renewal Required'
  }
  
  // Handle expiring SLAs
  if (autoRenewal && days <= 30) return 'Auto-Renewal Scheduled'
  if (days <= 7) return 'Critical - Renewal Required'
  if (days <= 30) return 'In Progress'
  return 'Under Review'
}

const getCriticalityLevel = (sla) => {
  const days = getDaysUntilExpiry(sla.expiry_date)
  const businessService = sla.business_service_impacted?.toLowerCase() || ''
  
  // Handle expired SLAs - always critical
  if (sla.status === 'EXPIRED' || days < 0) {
    return 'Critical'
  }
  
  // Determine criticality based on business impact and time remaining
  if (days <= 7) return 'Critical'
  if (days <= 30) {
    // High criticality for critical business services
    if (businessService.includes('critical') || businessService.includes('core') || 
        businessService.includes('payment') || businessService.includes('security')) {
      return 'High'
    }
    return 'High'
  }
  if (days <= 60) return 'Medium'
  return 'Low'
}


const filteredSLAs = computed(() => {
  return expiringSLAs.value.filter(sla => {
    const matchesSearch = sla.name.toLowerCase().includes(searchTerm.value.toLowerCase()) ||
                         sla.vendor.toLowerCase().includes(searchTerm.value.toLowerCase())
    const matchesCriticality = criticalityFilter.value === "all" || sla.criticality.toLowerCase() === criticalityFilter.value
    const matchesRenewal = renewalFilter.value === "all" || 
                          (renewalFilter.value === "auto" && sla.autoRenewal) ||
                          (renewalFilter.value === "manual" && !sla.autoRenewal)
    
    return matchesSearch && matchesCriticality && matchesRenewal
  })
})

const getExpiryUrgency = (days, status) => {
  if (status === 'EXPIRED' || days < 0) return "text-red-600 font-bold"
  if (days <= 7) return "text-red-600 font-bold"
  if (days <= 30) return "text-yellow-600 font-medium"
  return "text-green-600"
}

// Handler functions
const handleViewSLA = (sla) => {
  console.log('Viewing SLA:', sla)
  // Navigate to SLA detail page
  // router.push(`/slas/${sla.id}`)
}

const handleRenewSLA = async (sla) => {
  console.log('Renewing SLA:', sla)
  
  try {
    // Show info notification about renewal process
    await showInfo('SLA Renewal Initiated', `Starting renewal process for SLA "${sla.name}"`, {
      sla_id: sla.id,
      sla_name: sla.name,
      action: 'renewal_initiated'
    })
    
    // Mark SLA as notified in localStorage for persistence
    const notifiedSLAs = JSON.parse(localStorage.getItem('notifiedSLAs') || '[]')
    if (!notifiedSLAs.includes(sla.id)) {
      notifiedSLAs.push(sla.id)
      localStorage.setItem('notifiedSLAs', JSON.stringify(notifiedSLAs))
    }
    
    // Mark SLA as notified in local state
    const slaIndex = expiringSLAs.value.findIndex(s => s.id === sla.id)
    if (slaIndex !== -1) {
      expiringSLAs.value[slaIndex].notified = true
      expiringSLAs.value[slaIndex].notifiedAt = new Date().toISOString()
    }
    
    // Navigate to SLA renewal page with SLA data
    router.push({
      path: '/slas/renew',
      query: {
        slaId: sla.id,
        slaName: sla.name,
        vendor: sla.vendor,
        currentExpiry: sla.currentExpiry,
        daysUntilExpiry: sla.daysUntilExpiry,
        status: sla.status,
        businessService: sla.product
      }
    })
  } catch (error) {
    console.error('Error initiating SLA renewal:', error)
    await showSLAError('renewal_initiation_failed', error.message, {
      sla_id: sla.id,
      sla_name: sla.name
    })
  }
}

const clearNotification = async (sla) => {
  try {
    // Show info notification about clearing notification
    await showInfo('SLA Notification Cleared', `Cleared notification for SLA "${sla.name}"`, {
      sla_id: sla.id,
      sla_name: sla.name,
      action: 'notification_cleared'
    })
    
    // Remove from localStorage
    const notifiedSLAs = JSON.parse(localStorage.getItem('notifiedSLAs') || '[]')
    const updatedNotifiedSLAs = notifiedSLAs.filter(id => id !== sla.id)
    localStorage.setItem('notifiedSLAs', JSON.stringify(updatedNotifiedSLAs))
    
    // Update local state
    const slaIndex = expiringSLAs.value.findIndex(s => s.id === sla.id)
    if (slaIndex !== -1) {
      expiringSLAs.value[slaIndex].notified = false
      expiringSLAs.value[slaIndex].notifiedAt = null
    }
  } catch (error) {
    console.error('Error clearing notification:', error)
    await showSLAError('notification_clear_failed', error.message, {
      sla_id: sla.id,
      sla_name: sla.name
    })
  }
}
</script>
