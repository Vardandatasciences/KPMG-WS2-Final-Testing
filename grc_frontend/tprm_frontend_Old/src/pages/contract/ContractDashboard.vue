<template>
  <div class="space-y-6">
    <!-- Loading State -->
    <div v-if="isLoading" class="flex flex-col items-center justify-center py-20">
      <div class="relative">
        <div class="animate-spin rounded-full h-16 w-16 border-4 border-primary/20 border-t-primary"></div>
        <div class="absolute inset-0 flex items-center justify-center">
          <FileText class="h-6 w-6 text-primary animate-pulse" />
        </div>
      </div>
      <h3 class="mt-6 text-xl font-semibold text-foreground">Loading Dashboard</h3>
      <p class="mt-2 text-muted-foreground text-center max-w-md">
        Please wait while we fetch your contract data and performance metrics.
      </p>
      <div class="mt-4 flex space-x-1">
        <div class="w-2 h-2 bg-primary rounded-full animate-bounce"></div>
        <div class="w-2 h-2 bg-primary rounded-full animate-bounce" style="animation-delay: 0.1s"></div>
        <div class="w-2 h-2 bg-primary rounded-full animate-bounce" style="animation-delay: 0.2s"></div>
      </div>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="flex flex-col items-center justify-center py-20">
      <div class="w-20 h-20 bg-red-50 rounded-full flex items-center justify-center mb-6">
        <AlertTriangle class="h-10 w-10 text-red-500" />
      </div>
      <h3 class="text-xl font-semibold text-foreground mb-2">Unable to Load Dashboard</h3>
      <p class="text-muted-foreground text-center max-w-md mb-6">
        {{ error }}
      </p>
      <div class="flex gap-3">
        <Button variant="outline" @click="window.location.reload()" class="gap-2">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path>
          </svg>
          Try Again
        </Button>
        <Button @click="go('/contracts')" class="gap-2">
          <FileText class="w-4 h-4" />
          Go to Contracts
        </Button>
      </div>
    </div>

    <!-- Main Dashboard Content -->
    <div v-else class="space-y-8">
      <!-- Header -->
      <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div class="space-y-1">
          <h1 class="text-4xl font-bold text-foreground">Contract Dashboard</h1>
          <p class="text-lg text-muted-foreground">Comprehensive overview of your contract portfolio and performance metrics</p>
        </div>
        <div class="flex gap-3">
          <Button @click="go('/contracts/new')" class="gap-2">
            <Plus class="w-4 h-4" />
            New Contract
          </Button>
        </div>
      </div>

      <!-- KPI Cards -->
      <div class="grid grid-cols-4 gap-3">
        <Card class="relative overflow-hidden">
          <CardHeader class="space-y-0 pb-1 px-3 pt-3">
            <CardTitle class="text-xs font-medium text-muted-foreground uppercase tracking-wide flex items-center gap-1.5">
              <div class="w-3 h-3 bg-blue-100 rounded-sm flex items-center justify-center">
                <FileText class="h-2 w-2 text-blue-600" />
              </div>
              Total Contracts
            </CardTitle>
          </CardHeader>
          <CardContent class="px-3 pb-3 text-center">
            <div class="text-lg font-bold text-foreground leading-none">{{ totalContracts }}</div>
            <p class="text-xs text-muted-foreground mt-1">
              <span class="text-green-600 font-medium">+2</span> from last month
            </p>
          </CardContent>
        </Card>

        <Card class="relative overflow-hidden">
          <CardHeader class="space-y-0 pb-1 px-3 pt-3">
            <CardTitle class="text-xs font-medium text-muted-foreground uppercase tracking-wide flex items-center gap-1.5">
              <div class="w-3 h-3 bg-green-100 rounded-sm flex items-center justify-center">
                <CheckCircle class="h-2 w-2 text-green-600" />
              </div>
              Active Contracts
            </CardTitle>
        </CardHeader>
          <CardContent class="px-3 pb-3 text-center">
            <div class="text-lg font-bold text-foreground leading-none">{{ activeContracts }}</div>
            <p class="text-xs text-muted-foreground mt-1">
              <span class="text-green-600 font-medium">{{ Math.round((activeContracts / totalContracts) * 100) }}%</span> of total
          </p>
        </CardContent>
      </Card>

        <Card class="relative overflow-hidden">
          <CardHeader class="space-y-0 pb-1 px-3 pt-3">
            <CardTitle class="text-xs font-medium text-muted-foreground uppercase tracking-wide flex items-center gap-1.5">
              <div class="w-3 h-3 bg-orange-100 rounded-sm flex items-center justify-center">
                <AlertTriangle class="h-2 w-2 text-orange-600" />
              </div>
              Expiring Soon
            </CardTitle>
        </CardHeader>
          <CardContent class="px-3 pb-3 text-center">
            <div class="text-lg font-bold text-foreground leading-none">{{ expiringContracts }}</div>
            <p class="text-xs text-muted-foreground mt-1">
              Within <span class="font-medium">90 days</span>
          </p>
        </CardContent>
      </Card>

        <Card class="relative overflow-hidden">
          <CardHeader class="space-y-0 pb-1 px-3 pt-3">
            <CardTitle class="text-xs font-medium text-muted-foreground uppercase tracking-wide flex items-center gap-1.5">
              <div class="w-3 h-3 bg-purple-100 rounded-sm flex items-center justify-center">
                <TrendingUp class="h-2 w-2 text-purple-600" />
              </div>
              Total Value
            </CardTitle>
        </CardHeader>
          <CardContent class="px-3 pb-3 text-center">
            <div class="text-lg font-bold text-foreground leading-none">
            ${{ (totalValue / 1000000).toFixed(1) }}M
          </div>
            <p class="text-xs text-muted-foreground mt-1">
            Active contracts only
          </p>
        </CardContent>
      </Card>
    </div>

    <!-- Recent Contracts -->
      <Card class="shadow-sm">
        <CardHeader class="border-b">
        <div class="flex justify-between items-center">
          <div>
              <CardTitle class="text-xl font-semibold">Recent Contracts</CardTitle>
              <CardDescription class="text-base">Latest contract activities and updates</CardDescription>
          </div>
        </div>
      </CardHeader>
        <CardContent class="p-0">
          <div class="divide-y">
            <div v-for="contract in recentContracts" :key="contract.contract_id" class="flex items-center justify-between p-6 transition-colors group">
            <div class="flex items-center space-x-4">
                <div class="w-12 h-12 bg-gradient-to-br from-primary/10 to-primary/5 rounded-xl flex items-center justify-center group-hover:scale-105 transition-transform">
                  <FileText class="w-6 h-6 text-primary" />
              </div>
                <div class="space-y-1">
                  <div class="font-semibold text-foreground text-lg">{{ contract.contract_title || 'Untitled Contract' }}</div>
                <div class="text-sm text-muted-foreground">
                    {{ contract.vendor?.company_name || 'Unknown Vendor' }} • {{ contract.contract_number }}
                  </div>
                </div>
              </div>
              
              <div class="flex items-center space-x-4">
                <div class="text-right space-y-1">
                  <div class="font-semibold text-foreground text-lg">
                    {{ contract.currency }} {{ contract.contract_value?.toLocaleString() || '0' }}
            </div>
                <div class="text-sm text-muted-foreground">
                    Expires {{ contract.end_date ? new Date(contract.end_date).toLocaleDateString() : 'No end date' }}
                  </div>
                </div>
                <div class="flex flex-col gap-2">
                  <Badge :class="getStatusBadgeClass(contract.status)" class="text-xs px-2 py-1 rounded-full">
                    {{ contract.status?.replace('_', ' ') || 'Unknown' }}
                  </Badge>
                  <Badge :class="getRiskBadgeClass(contract.priority)" class="text-xs px-2 py-1 rounded-full">
                    {{ (contract.priority || 'Unknown').charAt(0).toUpperCase() + (contract.priority || 'Unknown').slice(1) }} Priority
                  </Badge>
              </div>
              <Button
                variant="ghost"
                size="icon"
                  @click="go(`/contracts/${contract.contract_id}`)"
                  class="opacity-0 group-hover:opacity-100 transition-opacity"
              >
                <Eye class="w-4 h-4" />
              </Button>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>

    <!-- Quick Actions -->
    <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card class="cursor-pointer hover:shadow-lg hover:scale-[1.02] transition-all duration-200 border-2 hover:border-primary/20 group" @click="go('/contracts')">
          <CardHeader class="pb-4">
            <div class="flex items-center gap-3 mb-2">
              <div class="w-10 h-10 bg-gradient-to-br from-green-500 to-green-600 rounded-lg flex items-center justify-center group-hover:scale-110 transition-transform">
                <FileText class="w-5 h-5 text-white" />
              </div>
              <CardTitle class="text-lg font-semibold group-hover:text-primary transition-colors">View All Contracts</CardTitle>
            </div>
            <CardDescription class="text-sm">Browse and manage all your contracts</CardDescription>
        </CardHeader>
      </Card>

        <Card class="cursor-pointer hover:shadow-lg hover:scale-[1.02] transition-all duration-200 border-2 hover:border-primary/20 group" @click="go('/contracts/new')">
          <CardHeader class="pb-4">
            <div class="flex items-center gap-3 mb-2">
              <div class="w-10 h-10 bg-gradient-to-br from-blue-500 to-blue-600 rounded-lg flex items-center justify-center group-hover:scale-110 transition-transform">
                <Plus class="w-5 h-5 text-white" />
              </div>
              <CardTitle class="text-lg font-semibold group-hover:text-primary transition-colors">Create New Contract</CardTitle>
            </div>
            <CardDescription class="text-sm">Start a new contract from scratch or template</CardDescription>
        </CardHeader>
      </Card>

        <Card class="cursor-pointer hover:shadow-lg hover:scale-[1.02] transition-all duration-200 border-2 hover:border-primary/20 group" @click="go('/analytics')">
          <CardHeader class="pb-4">
            <div class="flex items-center gap-3 mb-2">
              <div class="w-10 h-10 bg-gradient-to-br from-purple-500 to-purple-600 rounded-lg flex items-center justify-center group-hover:scale-110 transition-transform">
                <TrendingUp class="w-5 h-5 text-white" />
              </div>
              <CardTitle class="text-lg font-semibold group-hover:text-primary transition-colors">View Analytics</CardTitle>
            </div>
            <CardDescription class="text-sm">Contract performance and insights</CardDescription>
        </CardHeader>
      </Card>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useNotifications } from '@/composables/useNotifications'
import { 
  CheckCircle, 
  AlertTriangle, 
  TrendingUp, 
  FileText, 
  Plus, 
  Eye 
} from 'lucide-vue-next'
import { 
  Card, CardHeader, CardTitle, CardContent, CardDescription,
  Button, Badge
} from '@/components/ui_contract'
import contractsApi from '../../services/contractsApi'
import loggingService from '@/services/loggingService'

const router = useRouter()
const go = (path) => router.push(path)
const { showSuccess, showError, showWarning, showInfo } = useNotifications()

// State
const stats = ref({
  total_contracts: 0,
  active_contracts: 0,
  expiring_soon: 0,
  total_value: 0
})
const recentContracts = ref([])
const isLoading = ref(true)
const error = ref(null)

// Computed properties
const totalContracts = computed(() => stats.value.total_contracts)
const activeContracts = computed(() => stats.value.active_contracts)
const expiringContracts = computed(() => stats.value.expiring_soon)
const totalValue = computed(() => stats.value.total_value)

// Helper functions for badge styling
const getStatusBadgeClass = (status) => {
  const classes = {
    'ACTIVE': 'bg-emerald-50 text-emerald-700 border border-emerald-200 font-medium',
    'DRAFT': 'bg-slate-50 text-slate-700 border border-slate-200 font-medium',
    'UNDER_REVIEW': 'bg-amber-50 text-amber-800 border border-amber-200 font-medium',
    'EXPIRED': 'bg-red-50 text-red-700 border border-red-200 font-medium',
    'TERMINATED': 'bg-red-50 text-red-700 border border-red-200 font-medium',
    'PENDING': 'bg-blue-50 text-blue-700 border border-blue-200 font-medium',
    'PENDING ASSIGNMENT': 'bg-transparent text-blue-700 border border-blue-200 font-medium'
  }
  return classes[status] || 'bg-slate-50 text-slate-700 border border-slate-200 font-medium'
}

const getRiskBadgeClass = (risk) => {
  const classes = {
    'low': 'bg-emerald-50 text-emerald-700 border border-emerald-200 font-medium',
    'medium': 'bg-amber-50 text-amber-700 border border-amber-200 font-medium',
    'high': 'bg-red-50 text-red-700 border border-red-200 font-medium',
    'urgent': 'bg-red-50 text-red-700 border border-red-200 font-medium'
  }
  return classes[risk] || 'bg-slate-50 text-slate-700 border border-slate-200 font-medium'
}

// Load dashboard data
onMounted(async () => {
  await loggingService.logContractView()
  try {
    isLoading.value = true
    error.value = null
    
    // Load stats and recent contracts in parallel
    const [statsResponse, recentResponse] = await Promise.all([
      contractsApi.getContractStats(),
      contractsApi.getContracts({ limit: 5, ordering: '-created_at' })
    ])
    
    // Handle stats response
    if (statsResponse.success) {
      stats.value = statsResponse.data
      console.log('Dashboard stats loaded:', stats.value)
      console.log('Expiring soon count:', stats.value.expiring_soon)
      console.log('All stats data:', JSON.stringify(stats.value, null, 2))
    } else {
      error.value = statsResponse.message || 'Failed to load dashboard statistics'
      return
    }
    
    // Handle recent contracts response
    if (recentResponse.success) {
      recentContracts.value = recentResponse.data || []
      console.log('Recent contracts loaded:', recentContracts.value)
    }
    
  } catch (err) {
    console.error('Error loading dashboard data:', err)
    error.value = err.message || 'Failed to load dashboard data'
  } finally {
    isLoading.value = false
  }
})
</script>

