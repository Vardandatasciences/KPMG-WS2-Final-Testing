<template>
  <div class="space-y-6">
    <!-- Page Header -->
    <div>
      <h1 class="text-3xl font-bold text-foreground">KPI Dashboard</h1>
      <p class="text-muted-foreground">Comprehensive SLA performance and compliance metrics</p>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="flex items-center justify-center py-12">
      <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="rounded-lg border border-destructive bg-destructive/10 p-4">
      <div class="flex items-center gap-2">
        <AlertTriangle class="h-5 w-5 text-destructive" />
        <p class="text-destructive font-medium">{{ error }}</p>
      </div>
    </div>

    <!-- No Data State -->
    <div v-else-if="!kpiData" class="flex items-center justify-center py-12">
      <div class="text-center">
        <AlertTriangle class="h-16 w-16 text-muted-foreground mx-auto mb-4" />
        <p class="text-lg font-medium text-muted-foreground">No KPI data available</p>
        <p class="text-sm text-muted-foreground mt-2">Please ensure SLA data exists in the database</p>
      </div>
    </div>

    <div v-else class="space-y-6">
      <!-- Tabs Navigation -->
      <div class="inline-flex h-10 items-center justify-center rounded-md bg-muted p-1 text-muted-foreground">
        <button
          v-for="tab in tabs"
          :key="tab.value"
          @click="activeTab = tab.value"
          :class="[
            'inline-flex items-center justify-center whitespace-nowrap rounded-sm px-3 py-1.5 text-sm font-medium ring-offset-background transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50',
            activeTab === tab.value ? 'bg-background text-foreground shadow-sm' : 'hover:bg-background/50'
          ]"
        >
          {{ tab.label }}
        </button>
      </div>

      <!-- KPI Overview Tab -->
      <div v-if="activeTab === 'overview'" class="space-y-6">
        <!-- Primary KPI Cards -->
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <Tooltip>
            <TooltipTrigger as-child>
              <Card class="cursor-help">
                <CardContent class="p-6">
                  <div class="flex items-center justify-between">
                    <div>
                      <p class="text-sm font-medium text-muted-foreground">Total SLAs Monitored</p>
                      <p class="text-2xl font-bold text-primary">{{ kpiData.totalSLAs }}</p>
                      <p class="text-xs text-muted-foreground">Active SLAs</p>
                    </div>
                    <FileText class="h-8 w-8 text-primary" />
                  </div>
                </CardContent>
              </Card>
            </TooltipTrigger>
            <TooltipContent>
              <p>Count of all active SLAs in the system across vendors and versions</p>
            </TooltipContent>
          </Tooltip>

          <Tooltip>
            <TooltipTrigger as-child>
              <Card class="cursor-help">
                <CardContent class="p-6">
                  <div class="flex items-center justify-between">
                    <div>
                      <p class="text-sm font-medium text-muted-foreground">SLA Compliance Rate</p>
                      <p class="text-2xl font-bold text-metric-excellent">{{ Math.round(kpiData.complianceRate) }}%</p>
                      <p class="text-xs text-muted-foreground">Metrics being met</p>
                    </div>
                    <Shield class="h-8 w-8 text-metric-excellent" />
                  </div>
                </CardContent>
              </Card>
            </TooltipTrigger>
            <TooltipContent>
              <p>Percentage of SLA metrics that are currently being met (not violated)</p>
            </TooltipContent>
          </Tooltip>

          <Tooltip>
            <TooltipTrigger as-child>
              <Card class="cursor-help">
                <CardContent class="p-6">
                  <div class="flex items-center justify-between">
                    <div>
                      <p class="text-sm font-medium text-muted-foreground">Violation Rate</p>
                      <p class="text-2xl font-bold text-status-critical">{{ Math.round(kpiData.violationRate) }}%</p>
                      <p class="text-xs text-muted-foreground">Entries violated</p>
                    </div>
                    <AlertTriangle class="h-8 w-8 text-status-critical" />
                  </div>
                </CardContent>
              </Card>
            </TooltipTrigger>
            <TooltipContent>
              <p>Percentage of SLA entries that have recorded violations</p>
            </TooltipContent>
          </Tooltip>

          <Tooltip>
            <TooltipTrigger as-child>
              <Card class="cursor-help">
                <CardContent class="p-6">
                  <div class="flex items-center justify-between">
                    <div>
                      <p class="text-sm font-medium text-muted-foreground">Acknowledgment Rate</p>
                      <p class="text-2xl font-bold text-info">{{ Math.round(kpiData.acknowledgmentRate) }}%</p>
                      <p class="text-xs text-muted-foreground">Alerts acknowledged</p>
                    </div>
                    <CheckCircle class="h-8 w-8 text-info" />
                  </div>
                </CardContent>
              </Card>
            </TooltipTrigger>
            <TooltipContent>
              <p>Measures vendor responsiveness - how many alerts were acknowledged</p>
            </TooltipContent>
          </Tooltip>
        </div>

        <!-- Coverage Metrics -->
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
          <Tooltip>
            <TooltipTrigger as-child>
              <Card class="cursor-help">
                <CardHeader>
                  <CardTitle class="flex items-center gap-2">
                    <Shield class="h-5 w-5" />
                    Vendor Compliance Coverage
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div class="text-center">
                    <div class="text-4xl font-bold text-metric-excellent mb-2">
                      {{ Math.round(kpiData.complianceCoverage) }}%
                    </div>
                    <p class="text-sm text-muted-foreground">
                      Vendors mapped to compliance frameworks
                    </p>
                  </div>
                </CardContent>
              </Card>
            </TooltipTrigger>
            <TooltipContent>
              <p>Percentage of vendors mapped to compliance frameworks like ISO 27001, PCID</p>
            </TooltipContent>
          </Tooltip>

          <Tooltip>
            <TooltipTrigger as-child>
              <Card class="cursor-help">
                <CardHeader>
                  <CardTitle class="flex items-center gap-2">
                    <BarChart3 class="h-5 w-5" />
                    Framework-Linked SLA Coverage
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div class="text-center">
                    <div class="text-4xl font-bold text-metric-good mb-2">
                      {{ Math.round(kpiData.frameworkCoverage) }}%
                    </div>
                    <p class="text-sm text-muted-foreground">
                      SLAs mapped to regulatory frameworks
                    </p>
                  </div>
                </CardContent>
              </Card>
            </TooltipTrigger>
            <TooltipContent>
              <p>Percentage of SLAs mapped to at least one compliance/regulatory framework</p>
            </TooltipContent>
          </Tooltip>
        </div>
      </div>

      <!-- Performance Analytics Tab -->
      <div v-if="activeTab === 'performance'" class="space-y-6">
        <!-- Performance Trends Chart -->
        <Card>
          <CardHeader>
            <CardTitle class="flex items-center gap-2">
              <TrendingUp class="h-5 w-5" />
              SLA Performance Trends
            </CardTitle>
            <p class="text-sm text-muted-foreground">Monthly compliance and violation rate trends</p>
          </CardHeader>
          <CardContent>
            <div v-if="performanceTrends.length === 0" class="h-64 flex items-center justify-center">
              <p class="text-muted-foreground">No performance trend data available</p>
            </div>
            <div v-else class="h-80">
              <!-- Y-axis labels -->
              <div class="flex h-full">
                <div class="flex flex-col justify-between text-xs text-gray-500 pr-2">
                  <span>100%</span>
                  <span>80%</span>
                  <span>60%</span>
                  <span>40%</span>
                  <span>20%</span>
                  <span>0%</span>
                </div>
                
                <!-- Chart area -->
                <div class="flex-1 flex items-end justify-between gap-2 px-4 pb-12">
                  <div v-for="(item, index) in performanceTrends" :key="index" class="flex flex-col items-center flex-1 h-full justify-end">
                    <!-- Bar container -->
                    <div class="flex flex-col-reverse items-center gap-1 mb-2 w-full max-w-[60px]">
                      <!-- Compliance Bar (Green) -->
                      <div class="relative w-full group">
                        <div 
                          class="w-full bg-green-500 rounded transition-all hover:bg-green-600"
                          :style="{ height: `${Math.max((item.compliance / 100) * 200, 2)}px` }"
                        >
                          <div class="absolute -top-6 left-1/2 -translate-x-1/2 text-xs font-semibold text-green-700 opacity-0 group-hover:opacity-100 transition-opacity">
                            {{ Math.round(item.compliance) }}%
                          </div>
                        </div>
                      </div>
                      
                      <!-- Violations Bar (Red) -->
                      <div class="relative w-full group">
                        <div 
                          class="w-full bg-red-500 rounded transition-all hover:bg-red-600"
                          :style="{ height: `${Math.max((item.violations / 100) * 200, 2)}px` }"
                        >
                          <div class="absolute -top-6 left-1/2 -translate-x-1/2 text-xs font-semibold text-red-700 opacity-0 group-hover:opacity-100 transition-opacity">
                            {{ Math.round(item.violations) }}%
                          </div>
                        </div>
                      </div>
                    </div>
                    
                    <!-- Month Label -->
                    <span class="text-xs text-muted-foreground font-medium mt-2 text-center">{{ item.month }}</span>
                  </div>
                </div>
              </div>
              
              <!-- Legend -->
              <div class="flex justify-center gap-6 mt-4 text-sm border-t pt-4">
                <div class="flex items-center gap-2">
                  <div class="w-3 h-3 bg-green-500 rounded"></div>
                  <span>Compliance Rate</span>
                </div>
                <div class="flex items-center gap-2">
                  <div class="w-3 h-3 bg-red-500 rounded"></div>
                  <span>Violation Rate</span>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        <!-- Top Violated Metrics -->
        <Card>
          <CardHeader>
            <CardTitle class="flex items-center gap-2">
              <AlertTriangle class="h-5 w-5" />
              Top Violated SLA Metrics
            </CardTitle>
            <p class="text-sm text-muted-foreground">Metrics with the highest violation counts</p>
          </CardHeader>
          <CardContent>
            <div v-if="topViolatedMetrics.length === 0" class="h-56 flex items-center justify-center">
              <p class="text-muted-foreground">No violation data available</p>
            </div>
            <div v-else class="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <!-- Bar Chart View -->
              <div class="h-72">
                <div class="flex h-full">
                  <!-- Y-axis -->
                  <div class="flex flex-col justify-between text-xs text-gray-500 pr-2">
                    <span>{{ maxViolations }}</span>
                    <span>{{ Math.round(maxViolations * 0.75) }}</span>
                    <span>{{ Math.round(maxViolations * 0.5) }}</span>
                    <span>{{ Math.round(maxViolations * 0.25) }}</span>
                    <span>0</span>
                  </div>
                  
                  <!-- Bars -->
                  <div class="flex-1 flex items-end justify-between gap-2 pb-16 px-2">
                    <div v-for="(item, index) in topViolatedMetrics.slice(0, 5)" :key="index" class="flex flex-col items-center flex-1 h-full justify-end group">
                      <div class="relative w-full">
                        <div 
                          class="w-full rounded-t transition-all"
                          :class="getViolationColor(index)"
                          :style="{ height: `${Math.max((item.violations / maxViolations) * 180, 4)}px` }"
                        >
                          <div class="absolute -top-6 left-1/2 -translate-x-1/2 text-xs font-bold opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap">
                            {{ item.violations }}
                          </div>
                        </div>
                      </div>
                      <span class="text-xs text-muted-foreground mt-2 text-center leading-tight max-w-[80px] line-clamp-2">{{ truncateMetricName(item.metric) }}</span>
                    </div>
                  </div>
                </div>
              </div>
              
              <!-- List View -->
              <div class="h-72 overflow-y-auto">
                <div class="space-y-3 pr-2">
                  <div v-for="(item, index) in topViolatedMetrics" :key="index" class="flex items-center justify-between p-3 rounded-lg border hover:shadow-md transition-shadow">
                    <div class="flex items-center gap-3 flex-1">
                      <div 
                        class="w-8 h-8 rounded-full flex items-center justify-center text-white font-bold text-sm"
                        :style="{ backgroundColor: COLORS[index % COLORS.length] }"
                      >
                        {{ index + 1 }}
                      </div>
                      <div class="flex-1 min-w-0">
                        <p class="text-sm font-medium truncate">{{ item.metric }}</p>
                        <p class="text-xs text-muted-foreground">Violation count</p>
                      </div>
                    </div>
                    <Badge :variant="item.violations > 10 ? 'destructive' : 'secondary'" class="ml-2">
                      {{ item.violations }}
                    </Badge>
                  </div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <!-- Vendor Scorecard Tab -->
      <div v-if="activeTab === 'vendor'" class="space-y-6">
        <!-- Vendor Scorecard -->
        <Card>
          <CardHeader>
            <CardTitle class="flex items-center gap-2">
              <Users class="h-5 w-5" />
              Vendor-wise SLA Scorecard
            </CardTitle>
            <p class="text-sm text-muted-foreground">Performance comparison across all vendors</p>
          </CardHeader>
          <CardContent>
            <div v-if="vendorScorecard.length === 0" class="py-12 text-center">
              <p class="text-muted-foreground">No vendor scorecard data available</p>
            </div>
            <div v-else class="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead class="font-semibold">Vendor Name</TableHead>
                    <TableHead class="font-semibold">Compliance %</TableHead>
                    <TableHead class="font-semibold">Acknowledgment %</TableHead>
                    <TableHead class="font-semibold">Violations</TableHead>
                    <TableHead class="font-semibold">Overall Score</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  <TableRow v-for="(vendor, index) in vendorScorecard" :key="index" class="hover:bg-muted/50 transition-colors">
                    <TableCell class="font-medium">{{ vendor.vendor }}</TableCell>
                    <TableCell>
                      <div class="flex items-center gap-2">
                        <Badge :class="getComplianceBadgeClass(vendor.compliance)">
                          {{ Math.round(vendor.compliance) }}%
                        </Badge>
                        <div class="w-24 h-2 bg-gray-200 rounded-full overflow-hidden">
                          <div 
                            class="h-full rounded-full transition-all"
                            :class="getComplianceBarClass(vendor.compliance)"
                            :style="{ width: `${Math.min(vendor.compliance, 100)}%` }"
                          ></div>
                        </div>
                      </div>
                    </TableCell>
                    <TableCell>
                      <div class="flex items-center gap-2">
                        <Badge class="bg-info text-white">
                          {{ Math.round(vendor.acknowledgment) }}%
                        </Badge>
                        <div class="w-24 h-2 bg-gray-200 rounded-full overflow-hidden">
                          <div 
                            class="h-full bg-info rounded-full transition-all"
                            :style="{ width: `${Math.min(vendor.acknowledgment, 100)}%` }"
                          ></div>
                        </div>
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge :variant="vendor.violations <= 5 ? 'default' : 'destructive'" class="font-semibold">
                        {{ vendor.violations || 0 }}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <Badge v-if="vendor.score === 'Excellent'" class="bg-metric-excellent text-white font-semibold">Excellent</Badge>
                      <Badge v-else-if="vendor.score === 'Good'" class="bg-metric-good text-white font-semibold">Good</Badge>
                      <Badge v-else-if="vendor.score === 'Fair'" class="bg-metric-fair text-white font-semibold">Fair</Badge>
                      <Badge v-else-if="vendor.score === 'Poor'" class="bg-metric-poor text-white font-semibold">Poor</Badge>
                      <Badge v-else variant="secondary" class="font-semibold">{{ vendor.score }}</Badge>
                    </TableCell>
                  </TableRow>
                </TableBody>
              </Table>
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
import { ref, computed, onMounted } from 'vue'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip'
import apiService from '@/services/api'
// Charts removed - using CSS-based charts instead
import { 
  FileText, 
  Shield, 
  AlertTriangle, 
  CheckCircle, 
  TrendingUp, 
  Users, 
  BarChart3
} from 'lucide-vue-next'
import PopupModal from '@/popup/PopupModal.vue'
import { PopupService } from '@/popup/popupService'
import loggingService from '@/services/loggingService'

const activeTab = ref('overview')
const loading = ref(true)
const error = ref(null)

const tabs = [
  { value: 'overview', label: 'KPI Overview' },
  { value: 'performance', label: 'Performance Analytics' },
  { value: 'vendor', label: 'Vendor Scorecard' }
]

// Initialize with null - no fallback data
const kpiData = ref(null)
const performanceTrends = ref([])
const topViolatedMetrics = ref([])
const vendorScorecard = ref([])

const COLORS = ['#3b82f6', '#ef4444', '#f97316', '#22c55e', '#8b5cf6']

// Fetch KPI data from backend - no fallback data
const fetchKPIData = async () => {
  try {
    loading.value = true
    error.value = null
    
    const data = await apiService.getSLAKPIData()
    
    // Only set data if it exists from backend
    if (data && data.overview) {
      kpiData.value = {
        totalSLAs: data.overview.totalSLAs,
        complianceRate: parseFloat(data.overview.complianceRate),
        violationRate: parseFloat(data.overview.violationRate),
        acknowledgmentRate: parseFloat(data.overview.acknowledgmentRate),
        complianceCoverage: parseFloat(data.overview.complianceCoverage),
        frameworkCoverage: parseFloat(data.overview.frameworkCoverage)
      }
    }
    
    // Update performance trends - only if data exists
    if (data.performanceTrends && Array.isArray(data.performanceTrends) && data.performanceTrends.length > 0) {
      performanceTrends.value = data.performanceTrends.map(trend => ({
        month: trend.month || trend.period,
        compliance: parseFloat(trend.compliance) || parseFloat(trend.compliance_rate),
        violations: parseFloat(trend.violations) || parseFloat(trend.violation_rate)
      }))
    }
    
    // Update top violated metrics - only if data exists
    if (data.topViolatedMetrics && Array.isArray(data.topViolatedMetrics) && data.topViolatedMetrics.length > 0) {
      topViolatedMetrics.value = data.topViolatedMetrics.map(metric => ({
        metric: metric.metric || metric.metric_name,
        violations: parseInt(metric.violations) || parseInt(metric.violation_count)
      }))
    }
    
    // Update vendor scorecard - only if data exists
    if (data.vendorScorecard && Array.isArray(data.vendorScorecard) && data.vendorScorecard.length > 0) {
      vendorScorecard.value = data.vendorScorecard.map(vendor => ({
        vendor: vendor.vendor || vendor.vendor_name || vendor.company_name,
        compliance: parseFloat(vendor.compliance) || parseFloat(vendor.compliance_rate) || 0,
        acknowledgment: parseFloat(vendor.acknowledgment) || parseFloat(vendor.acknowledgment_rate) || 0,
        violations: parseInt(vendor.violations) || parseInt(vendor.violation_count) || 0,
        score: vendor.score || vendor.overall_score || calculateScore(vendor)
      }))
    }
    
  } catch (err) {
    console.error('Failed to fetch KPI data:', err)
    error.value = 'Failed to load KPI data from database. Please try again later.'
    PopupService.error('Failed to load KPI data. Please check database connection.', 'Loading Error')
    
    // Log the error
    loggingService.logError('SLA', 'Failed to load KPI data', {
      errorMessage: err.message,
      errorStack: err.stack
    })
  } finally {
    loading.value = false
  }
}

// Helper function to calculate score if not provided
const calculateScore = (vendor) => {
  const compliance = parseFloat(vendor.compliance) || parseFloat(vendor.compliance_rate) || 0
  const complianceValue = isNaN(compliance) ? 0 : compliance
  
  if (complianceValue >= 95) return 'Excellent'
  if (complianceValue >= 90) return 'Good'
  if (complianceValue >= 80) return 'Fair'
  return 'Poor'
}

// Computed properties for chart calculations
const maxViolations = computed(() => {
  if (!topViolatedMetrics.value || topViolatedMetrics.value.length === 0) return 1
  return Math.max(...topViolatedMetrics.value.map(m => m.violations || 0), 1)
})

// Helper functions
const getViolationColor = (index) => {
  const colors = ['bg-red-500', 'bg-orange-500', 'bg-yellow-500', 'bg-blue-500', 'bg-purple-500']
  return colors[index % colors.length]
}

const truncateMetricName = (name) => {
  if (!name) return 'N/A'
  return name.length > 15 ? name.substring(0, 15) + '...' : name
}

const getComplianceBadgeClass = (compliance) => {
  if (compliance >= 95) return 'bg-metric-excellent text-white'
  if (compliance >= 90) return 'bg-metric-good text-white'
  if (compliance >= 80) return 'bg-metric-fair text-white'
  return 'bg-metric-poor text-white'
}

const getComplianceBarClass = (compliance) => {
  if (compliance >= 95) return 'bg-metric-excellent'
  if (compliance >= 90) return 'bg-metric-good'
  if (compliance >= 80) return 'bg-metric-fair'
  return 'bg-metric-poor'
}

// Fetch data on component mount
onMounted(async () => {
  await loggingService.logKPIView()
  await fetchKPIData()
})

</script>
