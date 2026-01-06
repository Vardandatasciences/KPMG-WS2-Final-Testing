<template>
  <div class="space-y-6">
    <!-- Page Header -->
    <div>
      <h1 class="text-3xl font-bold text-foreground">SLA Analytics Dashboard</h1>
      <p class="text-muted-foreground">Vendor Performance & SLA Management Overview</p>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="flex items-center justify-center py-12">
      <div class="text-center">
        <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
        <p class="mt-4 text-muted-foreground">Loading dashboard data...</p>
      </div>
    </div>

    <!-- Main Content -->
    <div v-else>

    <!-- SLA Summary Cards -->
    <div class="grid grid-cols-4 gap-4">
      <Card v-for="stat in slaSummaryStats" :key="stat.title">
        <CardContent class="p-6">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm font-medium text-muted-foreground">{{ stat.title }}</p>
              <p class="text-2xl font-bold">{{ stat.value }}</p>
              <p class="text-xs text-muted-foreground flex items-center gap-1 mt-1">
                <Badge 
                  :class="stat.changeType === 'positive' ? 'bg-status-active text-white' : 'bg-muted'"
                  variant="secondary"
                >
                  {{ stat.change }}
                </Badge>
                from last month
              </p>
            </div>
            <component :is="stat.icon" class="h-8 w-8 text-muted-foreground" />
          </div>
        </CardContent>
      </Card>
    </div>

    <!-- Framework Distribution - Bar Chart -->
    <Card>
      <CardHeader>
        <CardTitle class="text-lg font-semibold">SLA Framework Distribution</CardTitle>
        <p class="text-sm text-muted-foreground">Number of SLAs following each compliance framework</p>
      </CardHeader>
      <CardContent>
        <div class="h-80 flex items-end justify-between px-4 pb-4">
          <!-- Y-axis labels -->
          <div class="flex flex-col justify-between h-full text-xs text-gray-500">
            <span>100</span>
            <span>80</span>
            <span>60</span>
            <span>40</span>
            <span>20</span>
            <span>0</span>
          </div>
          
          <!-- Chart area -->
          <div class="flex-1 flex items-end justify-between px-4">
             <div 
               v-for="(framework, index) in dashboardData.frameworkDistribution" 
               :key="framework.framework"
               class="flex flex-col items-center"
             >
               <div 
                 class="w-12 rounded-t"
                 :class="getFrameworkColor(index)"
                 :style="{ height: `${Math.min((framework.count / Math.max(...dashboardData.frameworkDistribution.map(f => f.count))) * 240, 240)}px` }"
               ></div>
               <span class="text-xs mt-4 text-center">{{ framework.framework }}</span>
               <span class="text-xs mt-1 font-medium">{{ framework.count }}</span>
             </div>
          </div>
        </div>
      </CardContent>
    </Card>


    <!-- SLA Status Distribution & Types -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <!-- SLA Status Distribution - Pie Chart -->
      <Card>
        <CardHeader>
          <CardTitle class="text-lg font-semibold">SLA Status Distribution</CardTitle>
          <p class="text-sm text-muted-foreground">Distribution by SLA status</p>
        </CardHeader>
        <CardContent>
          <div class="h-80 flex items-center justify-center">
            <div class="relative w-64 h-64">
              <!-- Pie Chart SVG -->
              <svg class="w-full h-full transform -rotate-90" viewBox="0 0 100 100">
                <!-- Active SLAs -->
                <circle
                  v-if="dashboardData.slaStatusDistribution?.active_percentage"
                  cx="50"
                  cy="50"
                  r="40"
                  fill="none"
                  stroke="#10b981"
                  stroke-width="20"
                  :stroke-dasharray="`${(dashboardData.slaStatusDistribution.active_percentage / 100) * 251.2} 251.2`"
                  stroke-dashoffset="0"
                />
                <!-- At Risk SLAs -->
                <circle
                  v-if="dashboardData.slaStatusDistribution?.at_risk_percentage"
                  cx="50"
                  cy="50"
                  r="40"
                  fill="none"
                  stroke="#f59e0b"
                  stroke-width="20"
                  :stroke-dasharray="`${(dashboardData.slaStatusDistribution.at_risk_percentage / 100) * 251.2} 251.2`"
                  :stroke-dashoffset="`-${(dashboardData.slaStatusDistribution.active_percentage / 100) * 251.2}`"
                />
                <!-- Breached SLAs -->
                <circle
                  v-if="dashboardData.slaStatusDistribution?.breached_percentage"
                  cx="50"
                  cy="50"
                  r="40"
                  fill="none"
                  stroke="#ef4444"
                  stroke-width="20"
                  :stroke-dasharray="`${(dashboardData.slaStatusDistribution.breached_percentage / 100) * 251.2} 251.2`"
                  :stroke-dashoffset="`-${((dashboardData.slaStatusDistribution.active_percentage + dashboardData.slaStatusDistribution.at_risk_percentage) / 100) * 251.2}`"
                />
              </svg>
              <!-- Center text -->
              <div class="absolute inset-0 flex items-center justify-center">
                <div class="text-center">
                  <div class="text-2xl font-bold text-gray-700">{{ dashboardData.summary?.total_slas || 0 }}</div>
                  <div class="text-xs text-gray-500">Total SLAs</div>
                </div>
              </div>
            </div>
          </div>
          <!-- Legend -->
          <div class="flex justify-center gap-6 text-sm mt-4">
            <div class="flex items-center gap-2">
              <div class="w-3 h-3 rounded-full bg-green-500"></div>
              <span>Active ({{ dashboardData.slaStatusDistribution?.active_percentage || 0 }}%)</span>
            </div>
            <div class="flex items-center gap-2">
              <div class="w-3 h-3 rounded-full bg-yellow-500"></div>
              <span>At Risk ({{ dashboardData.slaStatusDistribution?.at_risk_percentage || 0 }}%)</span>
            </div>
            <div class="flex items-center gap-2">
              <div class="w-3 h-3 rounded-full bg-red-500"></div>
              <span>Breached ({{ dashboardData.slaStatusDistribution?.breached_percentage || 0 }}%)</span>
            </div>
          </div>
        </CardContent>
      </Card>

      <!-- SLA Types - Bar Chart -->
      <Card>
        <CardHeader>
          <CardTitle class="text-lg font-semibold">SLA Types</CardTitle>
          <p class="text-sm text-muted-foreground">Distribution by SLA type</p>
        </CardHeader>
        <CardContent>
          <div class="h-80 flex items-end justify-between px-4 pb-4">
            <!-- Y-axis labels -->
            <div class="flex flex-col justify-between h-full text-xs text-gray-500">
              <span>100</span>
              <span>80</span>
              <span>60</span>
              <span>40</span>
              <span>20</span>
              <span>0</span>
            </div>
            
            <!-- Chart area -->
            <div class="flex-1 flex items-end justify-between px-4">
               <div 
                 v-for="(type, index) in dashboardData.slaTypesDistribution" 
                 :key="type.type"
                 class="flex flex-col items-center"
               >
                 <div 
                   class="w-12 rounded-t"
                   :class="getFrameworkColor(index)"
                   :style="{ height: `${Math.min((type.count / Math.max(...dashboardData.slaTypesDistribution.map(t => t.count))) * 240, 240)}px` }"
                 ></div>
                 <span class="text-xs mt-4 text-center">{{ type.type }}</span>
                 <span class="text-xs mt-1 font-medium">{{ type.count }}</span>
               </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>

    <!-- Risk Level Distribution & Top Performing Vendors -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <!-- Risk Level Distribution - Bar Chart -->
      <Card>
        <CardHeader>
          <CardTitle class="text-lg font-semibold">Risk Level Distribution</CardTitle>
          <p class="text-sm text-muted-foreground">Distribution by risk level</p>
        </CardHeader>
        <CardContent>
          <div class="h-80 flex items-end justify-between px-4 pb-4">
            <!-- Y-axis labels -->
            <div class="flex flex-col justify-between h-full text-xs text-gray-500">
              <span>50</span>
              <span>40</span>
              <span>30</span>
              <span>20</span>
              <span>10</span>
              <span>0</span>
            </div>
            
            <!-- Chart area -->
            <div class="flex-1 flex items-end justify-between px-4">
               <!-- Low Risk -->
               <div class="flex flex-col items-center">
                 <div 
                   class="w-12 bg-green-500 rounded-t" 
                   :style="{ height: `${(dashboardData.riskLevelDistribution?.low_risk?.percentage || 0) * 2}px` }"
                 ></div>
                 <span class="text-xs mt-4 text-center">Low</span>
                 <span class="text-xs mt-1 font-medium">{{ dashboardData.riskLevelDistribution?.low_risk?.percentage || 0 }}%</span>
               </div>
               
               <!-- Medium Risk -->
               <div class="flex flex-col items-center">
                 <div 
                   class="w-12 bg-yellow-500 rounded-t" 
                   :style="{ height: `${(dashboardData.riskLevelDistribution?.medium_risk?.percentage || 0) * 2}px` }"
                 ></div>
                 <span class="text-xs mt-4 text-center">Medium</span>
                 <span class="text-xs mt-1 font-medium">{{ dashboardData.riskLevelDistribution?.medium_risk?.percentage || 0 }}%</span>
               </div>
               
               <!-- High Risk -->
               <div class="flex flex-col items-center">
                 <div 
                   class="w-12 bg-orange-500 rounded-t" 
                   :style="{ height: `${(dashboardData.riskLevelDistribution?.high_risk?.percentage || 0) * 2}px` }"
                 ></div>
                 <span class="text-xs mt-4 text-center">High</span>
                 <span class="text-xs mt-1 font-medium">{{ dashboardData.riskLevelDistribution?.high_risk?.percentage || 0 }}%</span>
    </div>

               <!-- Critical Risk -->
               <div class="flex flex-col items-center">
                 <div 
                   class="w-12 bg-red-500 rounded-t" 
                   :style="{ height: `${(dashboardData.riskLevelDistribution?.critical_risk?.percentage || 0) * 2}px` }"
                 ></div>
                 <span class="text-xs mt-4 text-center">Critical</span>
                 <span class="text-xs mt-1 font-medium">{{ dashboardData.riskLevelDistribution?.critical_risk?.percentage || 0 }}%</span>
               </div>
            </div>
          </div>
        </CardContent>
      </Card>

      <!-- Top Performing Vendors by Performance -->
    <Card>
      <CardHeader>
          <CardTitle class="text-lg font-semibold">Top Performing Vendors by Performance</CardTitle>
      </CardHeader>
      <CardContent>
        <div class="space-y-4">
          <div 
              v-for="vendor in dashboardData.topPerformingVendors" 
              :key="vendor.rank"
              class="flex items-center justify-between"
          >
            <div class="flex items-center gap-3">
              <div 
                  class="w-8 h-8 rounded-full flex items-center justify-center"
                  :class="getVendorRankColor(vendor.rank)"
                >
                  <span class="font-bold text-sm">{{ vendor.rank }}</span>
                </div>
              <div>
                  <p class="text-sm font-medium">{{ vendor.company_name }}</p>
                  <p class="text-xs text-muted-foreground">{{ vendor.service_type }}</p>
              </div>
            </div>
              <div class="text-right">
                <p 
                  class="text-sm font-bold"
                  :class="getPerformanceScoreColor(vendor.performance_score)"
                >{{ vendor.performance_score }}%</p>
                <p class="text-xs text-muted-foreground">Performance</p>
              </div>
          </div>
        </div>
      </CardContent>
    </Card>
    </div>
    </div>
  </div>

  <!-- Popup Modal -->
  <PopupModal />
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Shield, Users, FileText, TrendingUp, FileCheck, AlertTriangle } from 'lucide-vue-next'
import apiService from '@/services/api'
import PopupModal from '@/popup/PopupModal.vue'
import { PopupService } from '@/popup/popupService'
import loggingService from '@/services/loggingService'

// Reactive data
const loading = ref(true)
const dashboardData = ref({
  summary: null,
  frameworkDistribution: [],
  slaStatusDistribution: {},
  slaTypesDistribution: [],
  riskLevelDistribution: {},
  topPerformingVendors: [],
  complianceMetrics: null,
  slaPerformanceCategories: []
})

// Computed properties for summary stats
const slaSummaryStats = computed(() => {
  if (!dashboardData.value.summary) return []
  
  const summary = dashboardData.value.summary
  return [
    {
      title: "Total SLAs",
      value: summary.total_slas?.toString() || "0",
      change: `+${summary.sla_change || 0}`,
    changeType: "positive",
    icon: FileText
  },
  {
      title: "Active SLAs",
      value: summary.active_slas?.toString() || "0",
      change: `+${summary.sla_change || 0}`,
      changeType: "positive",
      icon: FileCheck
    },
    {
      title: "Total Vendors",
      value: summary.total_vendors?.toString() || "0",
      change: `+${summary.vendor_change || 0}`,
    changeType: "positive",
    icon: Users
  },
  {
      title: "Total Contracts",
      value: summary.total_contracts?.toString() || "0",
      change: `+${summary.contract_change || 0}`,
    changeType: "positive",
    icon: Shield
    }
  ]
})

// API calls
const loadDashboardData = async () => {
  loading.value = true
  try {
    // Load all dashboard data in parallel
    const [
      summaryResponse,
      frameworkResponse,
      statusResponse,
      typesResponse,
      riskResponse,
      vendorsResponse,
      complianceResponse,
      performanceResponse
    ] = await Promise.all([
      apiService.request('/v1/sla-dashboard/dashboard/summary/'),
      apiService.request('/v1/sla-dashboard/dashboard/framework-distribution/'),
      apiService.request('/v1/sla-dashboard/dashboard/sla-status-distribution/'),
      apiService.request('/v1/sla-dashboard/dashboard/sla-types-distribution/'),
      apiService.request('/v1/sla-dashboard/dashboard/risk-level-distribution/'),
      apiService.request('/v1/sla-dashboard/dashboard/top-performing-vendors/'),
      apiService.request('/v1/sla-dashboard/dashboard/compliance-metrics/'),
      apiService.request('/v1/sla-dashboard/dashboard/sla-performance-categories/')
    ])

    dashboardData.value = {
      summary: summaryResponse,
      frameworkDistribution: frameworkResponse,
      slaStatusDistribution: statusResponse,
      slaTypesDistribution: typesResponse,
      riskLevelDistribution: riskResponse,
      topPerformingVendors: vendorsResponse,
      complianceMetrics: complianceResponse,
      slaPerformanceCategories: performanceResponse
    }
  } catch (error) {
    console.error('Error loading dashboard data:', error)
    PopupService.error('Error loading dashboard data. Using default values.', 'Loading Error')
    
    // Log the error
    loggingService.logError('SLA', 'Failed to load dashboard data', {
      errorMessage: error.message,
      errorStack: error.stack
    })
    
    // Set default values on error
    dashboardData.value = {
      summary: {
        total_slas: 0,
        active_slas: 0,
        total_vendors: 0,
        total_contracts: 0,
        sla_change: 0,
        vendor_change: 0,
        contract_change: 0
      },
      frameworkDistribution: [],
      slaStatusDistribution: {},
      slaTypesDistribution: [],
      riskLevelDistribution: {},
      topPerformingVendors: [],
      complianceMetrics: null,
      slaPerformanceCategories: []
    }
  } finally {
    loading.value = false
  }
}

// Load data on mount
onMounted(async () => {
  // Log page view
  await loggingService.logSLAView()
  await loadDashboardData()
})

// Helper functions
const getFrameworkColor = (index) => {
  const colors = ['bg-blue-500', 'bg-green-500', 'bg-purple-500', 'bg-orange-500', 'bg-red-500', 'bg-indigo-500']
  return colors[index % colors.length]
}

const getSLAStatusColor = (status) => {
  switch (status) {
    case 'active': return 'text-green-600'
    case 'at_risk': return 'text-yellow-600'
    case 'breached': return 'text-red-600'
    default: return 'text-gray-600'
  }
}

const getRiskLevelColor = (level) => {
  switch (level) {
    case 'low_risk': return 'text-green-600'
    case 'medium_risk': return 'text-yellow-600'
    case 'high_risk': return 'text-orange-600'
    case 'critical_risk': return 'text-red-600'
    default: return 'text-gray-600'
  }
}

const getVendorRankColor = (rank) => {
  const colors = [
    'bg-green-100 text-green-600',
    'bg-blue-100 text-blue-600', 
    'bg-purple-100 text-purple-600',
    'bg-orange-100 text-orange-600',
    'bg-indigo-100 text-indigo-600'
  ]
  return colors[(rank - 1) % colors.length]
}

const getPerformanceScoreColor = (score) => {
  if (score >= 95) return 'text-green-600'
  if (score >= 90) return 'text-blue-600'
  if (score >= 85) return 'text-yellow-600'
  return 'text-red-600'
}

</script>
