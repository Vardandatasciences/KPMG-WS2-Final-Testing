<template>
  <div class="flex-1 space-y-6 p-6">
    <div class="flex items-center justify-between">
      <div>
        <h2 class="text-3xl font-bold tracking-tight">Renewal Management</h2>
        <p class="text-muted-foreground">
          <span v-if="route.query.slaId">Managing specific SLA: {{ route.query.slaName }}</span>
          <span v-else>Manage renewals, extensions, and terminations</span>
        </p>
      </div>
      <div class="flex items-center gap-2">
        <Button 
          v-if="route.query.slaId" 
          variant="outline" 
          size="sm" 
          @click="router.push('/slas/expiring')"
          class="flex items-center gap-2"
        >
          <ArrowLeft class="h-4 w-4" />
          Back to Expiring SLAs
        </Button>
        <Badge variant="destructive">
          {{ pendingRenewals.filter(r => r.urgency === 'critical').length }} Critical
        </Badge>
        <Badge variant="secondary" class="bg-yellow-100 text-yellow-800">
          {{ pendingRenewals.filter(r => r.urgency === 'high').length }} High Priority
        </Badge>
      </div>
    </div>

    <!-- Summary Cards -->
    <div class="grid gap-4 md:grid-cols-4">
      <Card>
        <CardHeader class="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle class="text-sm font-medium">Pending Renewals</CardTitle>
          <Clock class="h-4 w-4 text-blue-500" />
        </CardHeader>
        <CardContent>
          <div class="text-2xl font-bold text-blue-600">
            {{ pendingRenewals.length }}
          </div>
          <p class="text-xs text-muted-foreground">
            Awaiting action
          </p>
        </CardContent>
      </Card>
      
      <Card>
        <CardHeader class="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle class="text-sm font-medium">Extended This Month</CardTitle>
          <RefreshCw class="h-4 w-4 text-green-500" />
        </CardHeader>
        <CardContent>
          <div class="text-2xl font-bold text-green-600">
            {{ extendedThisMonth }}
          </div>
          <p class="text-xs text-muted-foreground">
            Successfully extended
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader class="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle class="text-sm font-medium">Terminated This Month</CardTitle>
          <XCircle class="h-4 w-4 text-red-500" />
        </CardHeader>
        <CardContent>
          <div class="text-2xl font-bold text-red-600">
            {{ terminatedThisMonth }}
          </div>
          <p class="text-xs text-muted-foreground">
            Marked as inactive
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader class="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle class="text-sm font-medium">Auto-Renewal</CardTitle>
          <Zap class="h-4 w-4 text-purple-500" />
        </CardHeader>
        <CardContent>
          <div class="text-2xl font-bold text-purple-600">
            {{ autoRenewalCount }}
          </div>
          <p class="text-xs text-muted-foreground">
            Scheduled for auto-renewal
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
                placeholder="Search renewals..."
                v-model="searchTerm"
                class="pl-8"
              />
            </div>
          </div>
          <Select v-model="urgencyFilter">
            <SelectTrigger class="w-[180px]">
              <SelectValue placeholder="Urgency" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Urgency</SelectItem>
              <SelectItem value="critical">Critical</SelectItem>
              <SelectItem value="high">High</SelectItem>
              <SelectItem value="medium">Medium</SelectItem>
              <SelectItem value="low">Low</SelectItem>
            </SelectContent>
          </Select>
          <Select v-model="statusFilter">
            <SelectTrigger class="w-[180px]">
              <SelectValue placeholder="Status" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Status</SelectItem>
              <SelectItem value="pending">Pending</SelectItem>
              <SelectItem value="extended">Extended</SelectItem>
              <SelectItem value="terminated">Terminated</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </CardContent>
    </Card>

    <!-- Loading State -->
    <div v-if="loading" class="flex items-center justify-center p-8">
      <div class="text-center">
        <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
        <p class="mt-2 text-sm text-muted-foreground">Loading renewal data...</p>
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

    <!-- Renewal Notifications -->
    <div v-else class="space-y-4">
      <!-- No renewals message -->
      <Card v-if="filteredRenewals.length === 0" class="border-2 border-dashed">
        <CardContent class="flex flex-col items-center justify-center py-12">
          <Calendar class="h-12 w-12 text-muted-foreground mb-4" />
          <h3 class="text-lg font-semibold mb-2">No Renewals Found</h3>
          <p class="text-sm text-muted-foreground text-center max-w-md">
            There are no SLAs requiring renewal action at this time. 
            <span v-if="route.query.slaId">The selected SLA may have been marked as inactive.</span>
            <span v-else>Check back later or adjust your filters.</span>
          </p>
          <Button variant="outline" class="mt-4" @click="router.push('/slas')">
            View All SLAs
          </Button>
        </CardContent>
      </Card>
      
      <!-- Renewals list -->
      <div v-for="renewal in filteredRenewals" :key="renewal.id" class="relative">
        <Card :class="getNotificationCardClass(renewal.urgency)">
          <CardHeader>
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-3">
                <div :class="getUrgencyIconClass(renewal.urgency)">
                  <AlertTriangle v-if="renewal.urgency === 'critical'" class="h-5 w-5" />
                  <Clock v-else-if="renewal.urgency === 'high'" class="h-5 w-5" />
                  <Calendar v-else class="h-5 w-5" />
                </div>
                <div>
                  <CardTitle class="text-lg">{{ renewal.slaName }}</CardTitle>
                  <CardDescription>
                    SLA ID: {{ renewal.slaId }} | Vendor: {{ renewal.vendor }}
                  </CardDescription>
                </div>
              </div>
              <Badge :variant="getUrgencyBadgeVariant(renewal.urgency)">
                {{ renewal.urgency.toUpperCase() }}
              </Badge>
            </div>
          </CardHeader>
          <CardContent>
            <div class="grid gap-4 md:grid-cols-2">
              <div class="space-y-2">
                <div class="flex justify-between">
                  <span class="text-sm font-medium">Current Expiry:</span>
                  <span class="text-sm">{{ renewal.currentExpiry }}</span>
                </div>
                <div class="flex justify-between">
                  <span class="text-sm font-medium">Days Until Expiry:</span>
                  <span :class="getDaysUntilExpiryClass(renewal.daysUntilExpiry)">
                    {{ renewal.daysUntilExpiry < 0 ? 'Expired' : renewal.daysUntilExpiry + ' days' }}
                  </span>
                </div>
                <div class="flex justify-between">
                  <span class="text-sm font-medium">Business Service:</span>
                  <span class="text-sm">{{ renewal.businessService }}</span>
                </div>
              </div>
              <div class="space-y-2">
                <div class="flex justify-between">
                  <span class="text-sm font-medium">Auto-Renewal:</span>
                  <Badge v-if="renewal.autoRenewal" variant="secondary" class="bg-green-100 text-green-800">Yes</Badge>
                  <Badge v-else variant="outline">No</Badge>
                </div>
                <div class="flex justify-between">
                  <span class="text-sm font-medium">Status:</span>
                  <Badge :variant="getStatusBadgeVariant(renewal.status)">
                    {{ renewal.status }}
                  </Badge>
                </div>
                <div class="flex justify-between">
                  <span class="text-sm font-medium">Last Updated:</span>
                  <span class="text-sm">{{ renewal.lastUpdated }}</span>
                </div>
              </div>
            </div>
            
            <!-- Action Buttons -->
            <div class="flex items-center gap-3 mt-6 pt-4 border-t">
              <Button 
                variant="outline" 
                size="sm" 
                @click="handleViewSLA(renewal)"
                class="flex items-center gap-2"
              >
                <Eye class="h-4 w-4" />
                View Details
              </Button>
              <Button 
                variant="default" 
                size="sm" 
                @click="handleExtendSLA(renewal)"
                class="flex items-center gap-2"
                :disabled="renewal.status === 'terminated' || renewal.status === 'inactive'"
              >
                <RefreshCw class="h-4 w-4" />
                Extend
              </Button>
              <Button 
                variant="destructive" 
                size="sm" 
                @click="handleStopSLA(renewal)"
                class="flex items-center gap-2"
                :disabled="renewal.status === 'terminated' || renewal.status === 'inactive'"
              >
                <XCircle class="h-4 w-4" />
                Stop
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>

    <!-- Extend SLA Modal -->
    <Dialog v-model:open="showExtendModal">
      <DialogContent class="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>Extend SLA</DialogTitle>
          <DialogDescription>
            Extend the expiry date for {{ selectedSLA?.slaName }}
          </DialogDescription>
        </DialogHeader>
        <div class="grid gap-4 py-4">
          <div class="grid grid-cols-4 items-center gap-4">
            <Label for="current-expiry" class="text-right">Current Expiry</Label>
            <Input 
              id="current-expiry" 
              :value="selectedSLA?.currentExpiry" 
              class="col-span-3" 
              disabled 
            />
          </div>
          <div class="grid grid-cols-4 items-center gap-4">
            <Label for="new-expiry" class="text-right">New Expiry Date</Label>
            <Input 
              id="new-expiry" 
              type="date" 
              v-model="newExpiryDate" 
              class="col-span-3"
              :min="minDate"
            />
          </div>
          <div class="grid grid-cols-4 items-center gap-4">
            <Label for="extension-reason" class="text-right">Reason</Label>
            <Textarea 
              id="extension-reason" 
              v-model="extensionReason" 
              class="col-span-3"
              placeholder="Enter reason for extension..."
              :rows="3"
            />
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" @click="showExtendModal = false">Cancel</Button>
          <Button @click="confirmExtendSLA" :disabled="!newExpiryDate || !extensionReason">
            Extend SLA
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>

    <!-- Stop SLA Modal -->
    <Dialog v-model:open="showStopModal">
      <DialogContent class="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>Stop SLA</DialogTitle>
          <DialogDescription>
            Mark {{ selectedSLA?.slaName }} as inactive. This action cannot be undone.
          </DialogDescription>
        </DialogHeader>
        <div class="grid gap-4 py-4">
          <div class="grid grid-cols-4 items-center gap-4">
            <Label for="stop-reason" class="text-right">Reason</Label>
            <Textarea 
              id="stop-reason" 
              v-model="stopReason" 
              class="col-span-3"
              placeholder="Enter reason for stopping this SLA..."
              :rows="3"
            />
          </div>
          <div class="col-span-4">
            <div class="flex items-center space-x-2">
              <Checkbox id="confirm-stop" :checked="confirmStop" @update:checked="confirmStop = $event" />
              <Label for="confirm-stop" class="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70">
                I understand this will mark the SLA as inactive
              </Label>
            </div>
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" @click="showStopModal = false">Cancel</Button>
          <Button 
            variant="destructive" 
            @click="confirmStopSLA" 
            :disabled="!stopReason || !confirmStop"
          >
            Stop SLA
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  </div>

  <!-- Popup Modal -->
  <PopupModal />
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { Label } from '@/components/ui/label'
import { Checkbox } from '@/components/ui'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { 
  AlertTriangle, 
  Search, 
  Filter, 
  Eye, 
  RefreshCw, 
  Calendar, 
  Clock, 
  XCircle, 
  Zap,
  ArrowLeft
} from 'lucide-vue-next'
import apiService from '@/services/api'
import PopupModal from '@/popup/PopupModal.vue'
import { PopupService } from '@/popup/popupService'
import { useNotifications } from '@/composables/useNotifications'
import loggingService from '@/services/loggingService'

const router = useRouter()
const route = useRoute()
const { showSLASuccess, showSLAError, showSLAWarning, showInfo } = useNotifications()

const searchTerm = ref("")
const urgencyFilter = ref("all")
const statusFilter = ref("all")
const loading = ref(false)
const error = ref(null)

// Modal states
const showExtendModal = ref(false)
const showStopModal = ref(false)
const selectedSLA = ref(null)
const newExpiryDate = ref("")
const extensionReason = ref("")
const stopReason = ref("")
const confirmStop = ref(false)

// Data
const pendingRenewals = ref([])
const extendedThisMonth = ref(0)
const terminatedThisMonth = ref(0)
const autoRenewalCount = ref(0)

// Computed properties
const filteredRenewals = computed(() => {
  return pendingRenewals.value.filter(renewal => {
    const matchesSearch = renewal.slaName.toLowerCase().includes(searchTerm.value.toLowerCase()) ||
                         renewal.vendor.toLowerCase().includes(searchTerm.value.toLowerCase())
    const matchesUrgency = urgencyFilter.value === "all" || renewal.urgency === urgencyFilter.value
    const matchesStatus = statusFilter.value === "all" || renewal.status === statusFilter.value
    
    return matchesSearch && matchesUrgency && matchesStatus
  })
})

const minDate = computed(() => {
  const today = new Date()
  return today.toISOString().split('T')[0]
})

// Load data from API
const loadData = async () => {
  loading.value = true
  error.value = null
  
  try {
    // Check if we have specific SLA data from route query
    const routeQuery = route.query
    if (routeQuery.slaId) {
      // Skip if the SLA is INACTIVE
      if (routeQuery.status === 'INACTIVE') {
        pendingRenewals.value = []
        console.log('SLA is INACTIVE, not showing in renewals')
        return
      }
      
      // Create a specific renewal entry from route data
      const specificRenewal = {
        id: routeQuery.slaId,
        slaId: routeQuery.slaId,
        slaName: routeQuery.slaName,
        vendor: routeQuery.vendor,
        businessService: routeQuery.businessService || 'Service',
        currentExpiry: routeQuery.currentExpiry,
        daysUntilExpiry: parseInt(routeQuery.daysUntilExpiry),
        status: getRenewalStatusFromRoute(routeQuery.status, routeQuery.daysUntilExpiry),
        urgency: getUrgencyLevelFromRoute(routeQuery.status, routeQuery.daysUntilExpiry),
        autoRenewal: false, // Default value, could be enhanced
        lastUpdated: new Date().toISOString(),
        fromRoute: true // Flag to indicate this came from route
      }
      
      pendingRenewals.value = [specificRenewal]
      console.log('Loaded specific SLA from route:', specificRenewal)
    } else {
      // Load all SLAs that need renewal attention
      const slasData = await apiService.getSLAs()
      
      // Filter SLAs that need renewal (expired or expiring within 90 days)
      const today = new Date()
      
      pendingRenewals.value = slasData.filter(sla => {
        const expiryDate = new Date(sla.expiry_date)
        const daysUntilExpiry = getDaysUntilExpiry(sla.expiry_date)
        
        // Exclude INACTIVE SLAs from the renewals page
        if (sla.status === 'INACTIVE') {
          return false
        }
        
        // Include SLAs that are expired or expiring within 90 days
        return (sla.status === 'EXPIRED' || daysUntilExpiry < 0) || 
               (sla.status === 'ACTIVE' && daysUntilExpiry <= 90)
      }).map(sla => ({
        id: sla.sla_id,
        slaId: sla.sla_id,
        slaName: sla.sla_name,
        vendor: getVendorName(sla),
        businessService: sla.business_service_impacted || 'Service',
        currentExpiry: sla.expiry_date,
        daysUntilExpiry: getDaysUntilExpiry(sla.expiry_date),
        status: getRenewalStatus(sla),
        urgency: getUrgencyLevel(sla),
        autoRenewal: determineAutoRenewal(sla),
        lastUpdated: sla.updated_at || sla.created_at
      }))
      
      console.log('Loaded renewal data:', pendingRenewals.value.length)
      
      // Calculate statistics from all SLAs (not just filtered ones)
      // This gives accurate counts for extended/terminated this month
      const thisMonthStart = new Date()
      thisMonthStart.setDate(1)
      thisMonthStart.setHours(0, 0, 0, 0)
      
      // Count INACTIVE SLAs updated this month (terminated)
      terminatedThisMonth.value = slasData.filter(sla => {
        if (sla.status !== 'INACTIVE') return false
        const updatedAt = sla.updated_at ? new Date(sla.updated_at) : null
        return updatedAt && updatedAt >= thisMonthStart
      }).length
      
      // Count extended SLAs this month (we'd need a separate tracking for this in future)
      // For now, just count ACTIVE SLAs with recent updates that aren't close to expiring
      extendedThisMonth.value = slasData.filter(sla => {
        if (sla.status !== 'ACTIVE') return false
        const updatedAt = sla.updated_at ? new Date(sla.updated_at) : null
        const daysUntilExpiry = getDaysUntilExpiry(sla.expiry_date)
        // Extended if updated this month and expiry is far out
        return updatedAt && updatedAt >= thisMonthStart && daysUntilExpiry > 90
      }).length
      
      autoRenewalCount.value = pendingRenewals.value.filter(r => r.autoRenewal).length
    }
    
    // For route-specific SLA, set simple stats
    if (routeQuery.slaId) {
      extendedThisMonth.value = 0
      terminatedThisMonth.value = 0
    }
    
  } catch (err) {
    error.value = err.message
    console.error('Error loading renewal data:', err)
    PopupService.error('Error loading renewal data. Please try again later.', 'Loading Error')
  } finally {
    loading.value = false
  }
}

// Helper functions
const getDaysUntilExpiry = (expiryDate) => {
  const today = new Date()
  const expiry = new Date(expiryDate)
  const diff = Math.ceil((expiry.getTime() - today.getTime()) / (1000 * 60 * 60 * 24))
  return diff
}

const getVendorName = (sla) => {
  if (sla.vendor && typeof sla.vendor === 'object') {
    return sla.vendor.company_name || 'Unknown Vendor'
  }
  if (sla.vendor_id) {
    return 'Vendor ID: ' + sla.vendor_id
  }
  return 'Unknown Vendor'
}

const determineAutoRenewal = (sla) => {
  if (sla.sla_type === 'AVAILABILITY' && sla.business_service_impacted?.toLowerCase().includes('critical')) {
    return true
  }
  if (sla.contract?.contract_type === 'MASTER_AGREEMENT') {
    return true
  }
  return false
}

const getRenewalStatus = (sla) => {
  const days = getDaysUntilExpiry(sla.expiry_date)
  
  // INACTIVE SLAs should not appear in renewals list (filtered out)
  if (sla.status === 'INACTIVE') {
    return 'terminated'
  }
  if (sla.status === 'EXPIRED') {
    return 'expired'
  }
  if (days < 0) {
    return 'expired' // Past expiry date but still ACTIVE = expired
  }
  if (sla.status === 'ACTIVE') {
    return 'pending' // ACTIVE SLA that needs renewal attention
  }
  return 'pending'
}

const getUrgencyLevel = (sla) => {
  const days = getDaysUntilExpiry(sla.expiry_date)
  
  // INACTIVE SLAs have low urgency (they're already stopped)
  if (sla.status === 'INACTIVE') {
    return 'low'
  }
  if (sla.status === 'EXPIRED' || days < 0) {
    return 'critical'
  }
  if (days <= 7) {
    return 'critical'
  }
  if (days <= 30) {
    return 'high'
  }
  if (days <= 60) {
    return 'medium'
  }
  return 'low'
}

// Helper functions for route data
const getRenewalStatusFromRoute = (status, daysUntilExpiry) => {
  const days = parseInt(daysUntilExpiry)
  
  if (status === 'INACTIVE') {
    return 'terminated' // INACTIVE = terminated (stopped)
  }
  if (status === 'EXPIRED') {
    return 'expired'
  }
  if (days < 0) {
    return 'expired' // Past expiry date but still ACTIVE = expired
  }
  if (status === 'ACTIVE') {
    return 'pending' // ACTIVE SLA that needs renewal attention
  }
  return 'pending'
}

const getUrgencyLevelFromRoute = (status, daysUntilExpiry) => {
  const days = parseInt(daysUntilExpiry)
  
  // INACTIVE SLAs have low urgency (they're already stopped)
  if (status === 'INACTIVE') {
    return 'low'
  }
  if (status === 'EXPIRED' || days < 0) {
    return 'critical'
  }
  if (days <= 7) {
    return 'critical'
  }
  if (days <= 30) {
    return 'high'
  }
  if (days <= 60) {
    return 'medium'
  }
  return 'low'
}

// UI helper functions
const getNotificationCardClass = (urgency) => {
  switch (urgency) {
    case 'critical':
      return 'border-red-200 bg-red-50'
    case 'high':
      return 'border-orange-200 bg-orange-50'
    case 'medium':
      return 'border-yellow-200 bg-yellow-50'
    default:
      return 'border-blue-200 bg-blue-50'
  }
}

const getUrgencyIconClass = (urgency) => {
  switch (urgency) {
    case 'critical':
      return 'text-red-600'
    case 'high':
      return 'text-orange-600'
    case 'medium':
      return 'text-yellow-600'
    default:
      return 'text-blue-600'
  }
}

const getUrgencyBadgeVariant = (urgency) => {
  switch (urgency) {
    case 'critical':
      return 'destructive'
    case 'high':
      return 'secondary'
    default:
      return 'outline'
  }
}

const getStatusBadgeVariant = (status) => {
  switch (status) {
    case 'expired':
      return 'destructive'
    case 'terminated':
      return 'destructive'
    case 'extended':
      return 'secondary'
    default:
      return 'outline'
  }
}

const getDaysUntilExpiryClass = (days) => {
  if (days < 0) return "text-red-600 font-bold"
  if (days <= 7) return "text-red-600 font-bold"
  if (days <= 30) return "text-yellow-600 font-medium"
  return "text-green-600"
}

// Handler functions
const handleViewSLA = (renewal) => {
  router.push(`/slas/${renewal.slaId}`)
}

const handleExtendSLA = (renewal) => {
  selectedSLA.value = renewal
  newExpiryDate.value = ""
  extensionReason.value = ""
  showExtendModal.value = true
}

const handleStopSLA = (renewal) => {
  selectedSLA.value = renewal
  stopReason.value = ""
  confirmStop.value = false
  showStopModal.value = true
}

const confirmExtendSLA = async () => {
  if (!newExpiryDate.value || !extensionReason.value) return
  
  try {
    // Call API to extend SLA
    const response = await apiService.extendSLA(selectedSLA.value.slaId, {
      newExpiryDate: newExpiryDate.value,
      reason: extensionReason.value
    })
    
    console.log('SLA extended successfully:', response)
    
    const extendedDate = newExpiryDate.value
    
    // Log the action
    await loggingService.logSLAExtend(
      selectedSLA.value.slaId,
      selectedSLA.value.slaName,
      extensionReason.value
    )
    
    showExtendModal.value = false
    newExpiryDate.value = ""
    extensionReason.value = ""
    
    // Show success notification
    await showSLASuccess('renewed', {
      sla_id: selectedSLA.value.slaId,
      sla_name: selectedSLA.value.slaName,
      new_expiry_date: extendedDate
    })
    
    // Show success message
    PopupService.success(`SLA "${selectedSLA.value.slaName}" has been successfully extended to ${extendedDate}`, 'SLA Extended')
    
    // Reload data to update the list with new expiry date
    await loadData()
    
  } catch (err) {
    console.error('Error extending SLA:', err)
    
    // Show error notification
    await showSLAError('renewal_failed', err.message, {
      sla_id: selectedSLA.value.slaId,
      sla_name: selectedSLA.value.slaName
    })
    
    PopupService.error(`Error extending SLA: ${err.message}`, 'Extension Failed')
  }
}

const confirmStopSLA = async () => {
  if (!stopReason.value || !confirmStop.value) return
  
  try {
    // Call API to stop SLA (sets status to INACTIVE)
    const response = await apiService.stopSLA(selectedSLA.value.slaId, {
      reason: stopReason.value
    })
    
    console.log('SLA stopped successfully:', response)
    
    // Log the action
    await loggingService.logSLAStop(
      selectedSLA.value.slaId,
      selectedSLA.value.slaName,
      stopReason.value
    )
    
    showStopModal.value = false
    stopReason.value = ""
    confirmStop.value = false
    
    // Show warning notification for SLA termination
    await showSLAWarning('terminated', {
      sla_id: selectedSLA.value.slaId,
      sla_name: selectedSLA.value.slaName,
      reason: stopReason.value
    })
    
    // Show success message
    PopupService.success(`SLA "${selectedSLA.value.slaName}" has been successfully marked as INACTIVE and removed from the renewals list.`, 'SLA Stopped')
    
    // Reload data to remove the INACTIVE SLA from the list
    await loadData()
    
  } catch (err) {
    console.error('Error stopping SLA:', err)
    
    // Show error notification
    await showSLAError('termination_failed', err.message, {
      sla_id: selectedSLA.value.slaId,
      sla_name: selectedSLA.value.slaName
    })
    
    PopupService.error(`Error stopping SLA: ${err.message}`, 'Stop Failed')
  }
}

// Load data on component mount
onMounted(async () => {
  await loggingService.logPageView('SLA', 'SLA Renewal')
  await loadData()
})
</script>
