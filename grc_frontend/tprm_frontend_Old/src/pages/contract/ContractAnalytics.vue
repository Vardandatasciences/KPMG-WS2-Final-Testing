<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex justify-between items-start">
      <div>
        <h1 class="text-3xl font-bold text-foreground">Contract Analytics</h1>
        <p class="text-muted-foreground">Insights and trends from your contract portfolio</p>
      </div>
      <button 
        @click="loadAnalyticsData" 
        :disabled="loading"
        class="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 disabled:opacity-50 flex items-center gap-2"
      >
        <BarChart3 class="w-4 h-4" />
        {{ loading ? 'Refreshing...' : 'Refresh Data' }}
      </button>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="text-center py-12">
      <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto"></div>
      <p class="mt-4 text-muted-foreground">Loading analytics data...</p>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="text-center py-12">
      <div class="text-destructive mb-4">
        <AlertTriangle class="mx-auto h-12 w-12" />
      </div>
      <h3 class="text-lg font-semibold text-foreground mb-2">Error Loading Analytics</h3>
      <p class="text-muted-foreground mb-4">{{ error }}</p>
      <button @click="loadAnalyticsData" class="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90">
        Try Again
      </button>
    </div>

    <!-- Analytics Content -->
    <div v-else-if="analyticsData">

    <!-- No Data State -->
    <div v-if="!analyticsData.key_metrics" class="text-center py-12">
      <FileText class="mx-auto h-12 w-12 text-muted-foreground" />
      <h3 class="mt-2 text-sm font-semibold text-foreground">No Analytics Data</h3>
      <p class="mt-1 text-sm text-muted-foreground">
        No contract data available for analytics. Create some contracts to see insights.
      </p>
    </div>

    <!-- Analytics Content -->
    <div v-else>

    <!-- Key Metrics -->
    <div class="grid grid-cols-5 gap-4">
      <Card>
        <CardHeader class="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle class="text-xs font-medium">Total Portfolio Value</CardTitle>
          <DollarSign class="h-3 w-3 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div class="text-lg font-bold">
            ${{ (totalValue / 1000000).toFixed(1) }}M
          </div>
          <p class="text-xs text-muted-foreground">
            Active contracts only
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader class="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle class="text-xs font-medium">Total Contracts</CardTitle>
          <FileText class="h-3 w-3 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div class="text-lg font-bold">{{ totalContracts }}</div>
          <p class="text-xs text-muted-foreground">
            Across all statuses
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader class="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle class="text-xs font-medium">Active Contracts</CardTitle>
          <CheckCircle class="h-3 w-3 text-success" />
        </CardHeader>
        <CardContent>
          <div class="text-lg font-bold">{{ activeContracts }}</div>
          <p class="text-xs text-muted-foreground">
            Currently active
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader class="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle class="text-xs font-medium">Expiring Soon</CardTitle>
          <AlertTriangle class="h-3 w-3 text-warning" />
        </CardHeader>
        <CardContent>
          <div class="text-lg font-bold">{{ expiringContracts }}</div>
          <p class="text-xs text-muted-foreground">
            Within 90 days
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader class="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle class="text-xs font-medium">Avg Contract Value</CardTitle>
          <TrendingUp class="h-3 w-3 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div class="text-lg font-bold">
            ${{ contractsWithValue > 0 ? Math.round(totalValue / contractsWithValue / 1000) : 0 }}K
          </div>
          <p class="text-xs text-muted-foreground">
            Per contract with value
          </p>
        </CardContent>
      </Card>
    </div>

    <!-- Charts Grid -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <!-- Contract Status Distribution -->
      <Card>
        <CardHeader>
          <CardTitle>Contract Status Distribution</CardTitle>
          <CardDescription>Current status of all contracts</CardDescription>
        </CardHeader>
        <CardContent>
          <PieChart :data="statusChartData" :colors="COLORS" />
        </CardContent>
      </Card>

      <!-- Contract Types -->
      <Card>
        <CardHeader>
          <CardTitle>Contract Types</CardTitle>
          <CardDescription>Distribution by contract type</CardDescription>
        </CardHeader>
        <CardContent>
          <BarChartComponent :data="typeChartData" data-key="count" :colors="typeChartData.map(item => item.color)" />
        </CardContent>
      </Card>

      <!-- Risk Distribution -->
      <Card>
        <CardHeader>
          <CardTitle>Risk Level Distribution</CardTitle>
          <CardDescription>Contract risk assessment overview</CardDescription>
        </CardHeader>
        <CardContent>
          <PieChart :data="riskChartData" :colors="COLORS" />
        </CardContent>
      </Card>

      <!-- Value by Vendor -->
      <Card>
        <CardHeader>
          <CardTitle>Contract Value by Vendor</CardTitle>
          <CardDescription>Active contract values by vendor (in thousands)</CardDescription>
        </CardHeader>
        <CardContent>
          <BarChartComponent 
            :data="vendorValueData" 
            data-key="value" 
            layout="horizontal" 
            :colors="['#3b82f6', '#1d4ed8', '#1e40af']"
          />
        </CardContent>
      </Card>
    </div>

    <!-- Trend Analysis -->
    <Card>
      <CardHeader>
        <CardTitle>Monthly Contract Trends</CardTitle>
        <CardDescription>Contract value and count trends over time</CardDescription>
      </CardHeader>
      <CardContent>
        <div class="space-y-4">
          <div class="grid grid-cols-2 gap-4">
            <div class="text-center p-4 bg-muted/50 rounded-lg">
              <div class="text-2xl font-bold text-success">+12%</div>
              <div class="text-sm text-muted-foreground">Value Growth</div>
            </div>
            <div class="text-center p-4 bg-muted/50 rounded-lg">
              <div class="text-2xl font-bold text-primary">+5</div>
              <div class="text-sm text-muted-foreground">New Contracts</div>
            </div>
          </div>
          <div class="text-sm text-muted-foreground">
            Portfolio showing strong growth with increased contract values and new vendor partnerships.
          </div>
        </div>
      </CardContent>
    </Card>

    <!-- Detailed Insights -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <Card>
        <CardHeader>
          <CardTitle>Key Insights</CardTitle>
          <CardDescription>Notable patterns and recommendations</CardDescription>
        </CardHeader>
        <CardContent class="space-y-4">
          <div class="flex items-start gap-3">
            <AlertTriangle class="w-5 h-5 text-warning mt-0.5" />
            <div>
              <p class="font-medium">Renewal Attention Required</p>
              <p class="text-sm text-muted-foreground">
                {{ expiringContracts }} contracts expire within 90 days. Review renewal requirements.
              </p>
            </div>
          </div>

          <div class="flex items-start gap-3">
            <TrendingUp class="w-5 h-5 text-success mt-0.5" />
            <div>
              <p class="font-medium">Portfolio Growth</p>
              <p class="text-sm text-muted-foreground">
                Active contract portfolio worth ${{ (totalValue / 1000000).toFixed(1) }}M across {{ activeContracts }} active contracts.
              </p>
            </div>
          </div>

          <div class="flex items-start gap-3">
            <Building class="w-5 h-5 text-primary mt-0.5" />
            <div>
              <p class="font-medium">Vendor Concentration</p>
              <p class="text-sm text-muted-foreground">
                Top vendor represents ${{ Math.max(...vendorValueData.map(v => v.value)) }}K in contract value.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Compliance Status</CardTitle>
          <CardDescription>Compliance framework coverage</CardDescription>
        </CardHeader>
        <CardContent class="space-y-4">
          <div v-for="framework in complianceFrameworks" :key="framework.name" class="space-y-2">
            <div class="flex justify-between text-sm">
              <span>{{ framework.name }}</span>
              <span>{{ framework.count }} contracts ({{ framework.percentage }}%)</span>
            </div>
            <div class="w-full bg-muted rounded-full h-2">
              <div 
                class="bg-primary h-2 rounded-full" 
                :style="{ width: `${framework.percentage}%` }"
              ></div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>

    <!-- Vendor Performance Summary -->
    <Card>
      <CardHeader>
        <CardTitle>Top Performing Vendors</CardTitle>
        <CardDescription>Vendors with highest contract values and performance</CardDescription>
      </CardHeader>
      <CardContent>
        <div class="space-y-4">
          <div v-for="(vendor, index) in topVendors" :key="vendor.vendor" class="flex items-center justify-between p-3 border rounded-lg">
            <div class="flex items-center gap-3">
              <div class="w-8 h-8 bg-primary/10 rounded-full flex items-center justify-center text-sm font-bold text-primary">
                {{ index + 1 }}
              </div>
              <div>
                <div class="font-medium">{{ vendor.vendor }}</div>
                <div class="text-sm text-muted-foreground">{{ vendor.contractCount }} contracts</div>
              </div>
            </div>
            <div class="text-right">
              <div class="font-bold">${{ vendor.value.toLocaleString() }}K</div>
              <div class="text-sm text-muted-foreground">Total Value</div>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
    </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import contractsApi from '../../services/contractsApi'
import loggingService from '@/services/loggingService'
import { 
  TrendingUp, 
  DollarSign, 
  FileText, 
  AlertTriangle,
  Calendar,
  Building,
  BarChart3,
  CheckCircle
} from 'lucide-vue-next'
import { 
  Card, CardHeader, CardTitle, CardContent, CardDescription
} from '@/components/ui_contract'
import PieChart from '@/components/charts/PieChart.vue'
import BarChartComponent from '@/components/charts/BarChartComponent.vue'

// State
const loading = ref(true)
const error = ref(null)
const analyticsData = ref(null)

// Load analytics data from backend
const loadAnalyticsData = async () => {
  try {
    loading.value = true
    error.value = null
    
    const response = await contractsApi.getContractAnalytics()
    
    if (response.success) {
      analyticsData.value = response.data
    } else {
      throw new Error(response.message || 'Failed to load analytics data')
    }
  } catch (err) {
    console.error('Error loading analytics data:', err)
    error.value = err.message || 'Failed to load analytics data'
  } finally {
    loading.value = false
  }
}

// Lifecycle
onMounted(async () => {
  await loggingService.logPageView('Contract', 'Contract Analytics')
  await loadAnalyticsData()
})

// Chart data computed properties
const statusChartData = computed(() => {
  if (!analyticsData.value?.status_distribution) return []
  
  return Object.entries(analyticsData.value.status_distribution).map(([status, count]) => ({
    name: status,
    value: count
  }))
})

const typeChartData = computed(() => {
  if (!analyticsData.value?.type_distribution) return []
  
  const statusColors = [
    '#22c55e', // Green (Active)
    '#94a3b8', // Grey (Draft)
    '#f59e0b', // Orange (Review)
    '#ef4444', // Red (Expired/Terminated)
    '#3b82f6', // Blue (Other types)
    '#8b5cf6', // Purple (Other types)
    '#06b6d4'  // Cyan (Other types)
  ]
  
  return Object.entries(analyticsData.value.type_distribution).map(([type, count], index) => ({
    name: type,
    count,
    color: statusColors[index % statusColors.length]
  }))
})

const riskChartData = computed(() => {
  if (!analyticsData.value?.risk_distribution) return []
  
  return analyticsData.value.risk_distribution.map(item => ({
    name: item.risk_category,
    value: item.count
  }))
})

const vendorValueData = computed(() => {
  if (!analyticsData.value?.vendor_value_data) return []
  
  return analyticsData.value.vendor_value_data.map(vendor => ({
    name: vendor.vendor__company_name || 'Unknown Vendor',
    vendor: vendor.vendor__company_name || 'Unknown Vendor', // Keep for other uses
    value: (vendor.total_value || 0) / 1000 // Convert to thousands
  }))
})

// Key metrics
const totalContracts = computed(() => analyticsData.value?.key_metrics?.total_contracts || 0)
const activeContracts = computed(() => analyticsData.value?.key_metrics?.active_contracts || 0)
const expiringContracts = computed(() => analyticsData.value?.key_metrics?.expiring_contracts || 0)
const totalValue = computed(() => analyticsData.value?.key_metrics?.total_value || 0)
const contractsWithValue = computed(() => analyticsData.value?.vendor_value_data?.reduce((sum, vendor) => sum + vendor.contract_count, 0) || 0)

// Compliance frameworks data
const complianceFrameworks = computed(() => {
  if (!analyticsData.value?.compliance_frameworks) return []
  
  return analyticsData.value.compliance_frameworks
})

// Top performing vendors
const topVendors = computed(() => {
  return vendorValueData.value
    .slice(0, 5)
    .map(vendor => {
      const vendorData = analyticsData.value?.vendor_value_data?.find(v => 
        v.vendor__company_name === vendor.vendor
      )
      
      return {
        vendor: vendor.vendor,
        value: vendor.value,
        contractCount: vendorData?.contract_count || 0
      }
    })
})

// Chart colors
const COLORS = {
  // Contract Status Colors
  'ACTIVE': '#22c55e',           // Green
  'DRAFT': '#8b5cf6',            // Purple
  'UNDER_REVIEW': '#f59e0b',     // Orange
  'PENDING_ASSIGNMENT': '#06b6d4', // Cyan
  'APPROVED': '#10b981',         // Emerald green
  'EXPIRED': '#ef4444',          // Red
  'TERMINATED': '#dc2626',       // Dark red
  
  // Risk Level Colors
  'Low': '#22c55e',              // Green
  'Medium': '#f59e0b',           // Orange
  'High': '#ef4444',             // Red
  'Critical': '#7c2d12',         // Dark red/brown
  'Unknown': '#6b7280'           // Gray
}
</script>
