<template>
  <div class="vendor_space-y-6">
    <div class="vendor_flex vendor_items-center vendor_justify-between">
      <div>
        <h1 class="vendor_text-3xl vendor_font-bold vendor_text-foreground">Vendor Management Dashboard</h1>
        <p class="vendor_text-muted-foreground">Monitor and manage your vendor ecosystem</p>
      </div>
      <Button :disabled="loading || generatingReport" @click="generateReport">
        <FileCheck class="vendor_h-4 vendor_w-4 vendor_mr-2" />
        {{ generatingReport ? 'Generating...' : 'Generate Report' }}
      </Button>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="vendor_flex vendor_items-center vendor_justify-center vendor_py-8">
      <div class="vendor_text-center">
        <div class="vendor_animate-spin vendor_rounded-full vendor_h-8 vendor_w-8 vendor_border-b-2 vendor_border-primary vendor_mx-auto"></div>
        <p class="vendor_text-muted-foreground vendor_mt-2">Loading dashboard data...</p>
      </div>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="vendor_bg-destructive/10 vendor_border vendor_border-destructive/20 vendor_rounded-lg vendor_p-4">
      <div class="vendor_flex vendor_items-center vendor_gap-2">
        <AlertTriangle class="vendor_h-5 vendor_w-5 vendor_text-destructive" />
        <p class="vendor_text-destructive vendor_font-medium">{{ error }}</p>
        <button @click="fetchDashboardData" class="vendor_btn vendor_btn-outline vendor_btn-sm vendor_ml-auto">
          Retry
        </button>
      </div>
    </div>

    <!-- Dashboard Content -->
    <div v-else>

    <!-- KPI Cards -->
    <div class="vendor_kpi-grid">
      <Card v-for="(vendor_kpi, vendor_index) in vendor_kpiData" :key="vendor_index" class="vendor_kpi-card">
        <CardContent class="vendor_kpi-content">
          <div class="vendor_kpi-header">
            <div class="vendor_kpi-icon-wrapper" :class="vendor_getKpiIconClass(vendor_kpi.variant)">
              <component :is="vendor_kpi.icon" class="vendor_kpi-icon" />
            </div>
            <div class="vendor_kpi-title-wrapper">
              <h3 class="vendor_kpi-title">{{ vendor_kpi.title }}</h3>
              <div class="vendor_kpi-trend" :class="vendor_getTrendClass(vendor_kpi.trend.isPositive)">
                <span class="vendor_trend-text">
                  {{ vendor_kpi.trend.isPositive ? '↗' : '↘' }} {{ vendor_kpi.trend.value }}
                </span>
              </div>
            </div>
          </div>
          <div class="vendor_kpi-value">
            <div class="vendor_value-number">{{ vendor_kpi.value }}</div>
          </div>
        </CardContent>
      </Card>
    </div>

    <div class="vendor_main-content-grid">
      <!-- Recent Vendor Activity -->
      <Card class="vendor_activity-card">
        <CardHeader class="vendor_card-header">
          <CardTitle class="vendor_card-title">Recent Vendor Activity</CardTitle>
        </CardHeader>
        <CardContent class="vendor_activity-content">
          <div v-for="(vendor_vendor, vendor_index) in vendor_recentVendors" :key="vendor_index" class="vendor_vendor-activity-item">
            <div class="vendor_vendor-info">
              <div class="vendor_vendor-name">{{ vendor_vendor.name }}</div>
              <div class="vendor_vendor-meta">
                Active for {{ vendor_vendor.daysActive }} days
              </div>
            </div>
            <div class="vendor_vendor-actions">
              <Badge :variant="vendor_getStatusVariant(vendor_vendor.status)" class="vendor_status-badge">
                {{ vendor_vendor.status }}
              </Badge>
              <span :class="`vendor_risk-indicator ${vendor_getRiskColor(vendor_vendor.riskLevel)}`">
                {{ vendor_vendor.riskLevel.toUpperCase() }}
              </span>
            </div>
          </div>
        </CardContent>
      </Card>

      <!-- Compliance Overview -->
      <Card class="vendor_compliance-card">
        <CardHeader class="vendor_card-header">
          <CardTitle class="vendor_card-title">Compliance Overview</CardTitle>
        </CardHeader>
        <CardContent class="vendor_compliance-content">
          <div class="vendor_compliance-progress">
            <div class="vendor_progress-header">
              <span class="vendor_progress-label">Security Assessments</span>
              <span class="vendor_progress-value">{{ vendor_complianceData.security_assessments }}%</span>
            </div>
            <Progress :value="Number(vendor_complianceData.security_assessments || 0)" class="vendor_progress-bar" />
          </div>
          
          <div class="vendor_compliance-progress">
            <div class="vendor_progress-header">
              <span class="vendor_progress-label">Documentation Complete</span>
              <span class="vendor_progress-value">{{ vendor_complianceData.documentation_complete }}%</span>
            </div>
            <Progress :value="Number(vendor_complianceData.documentation_complete || 0)" class="vendor_progress-bar" />
          </div>
          
          <div class="vendor_compliance-progress">
            <div class="vendor_progress-header">
              <span class="vendor_progress-label">Risk Assessments</span>
              <span class="vendor_progress-value">{{ vendor_complianceData.risk_assessments }}%</span>
            </div>
            <Progress :value="Number(vendor_complianceData.risk_assessments || 0)" class="vendor_progress-bar" />
          </div>

          <div class="vendor_compliance-summary">
            <div class="vendor_compliance-item">
              <CheckCircle class="vendor_compliance-icon vendor_text-success" />
              <span class="vendor_compliance-text">{{ vendor_complianceData.fully_compliant }} vendors fully compliant</span>
            </div>
            <div class="vendor_compliance-item">
              <Clock class="vendor_compliance-icon vendor_text-warning" />
              <span class="vendor_compliance-text">{{ vendor_complianceData.pending_reviews }} pending reviews</span>
            </div>
            <div class="vendor_compliance-item">
              <AlertTriangle class="vendor_compliance-icon vendor_text-destructive" />
              <span class="vendor_compliance-text">{{ vendor_complianceData.require_attention }} require immediate attention</span>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useNotifications } from '@/composables/useNotifications'
import { 
  Users, 
  Shield, 
  TrendingUp, 
  FileCheck,
  AlertTriangle,
  CheckCircle,
  Clock
} from 'lucide-vue-next'
import { useVendorDashboardStore } from '@/stores/dashboard.js'
import apiClient from '@/config/axios.js'
import loggingService from '@/services/loggingService'
import { 
  Card, CardHeader, CardTitle, CardContent,
  Button, Badge, Progress
} from '@/components/ui/index.js'

const vendor_dashboardStore = useVendorDashboardStore()

// Reactive data
const { showSuccess, showError, showWarning, showInfo } = useNotifications()

const vendor_kpiData = ref([])
const vendor_recentVendors = ref([])
const vendor_complianceData = ref({})
const loading = ref(true)
const error = ref(null)
const generatingReport = ref(false)

// Fetch dashboard data from API
const fetchDashboardData = async () => {
  try {
    loading.value = true
    error.value = null
    
    const response = await apiClient.get('/api/v1/vendor-dashboard/dashboard/')
    const rawData = response.data

    const payload = rawData?.data && typeof rawData.data === 'object'
      ? rawData.data
      : rawData

    const metrics = {
      total_vendors: payload?.metrics?.total_vendors ?? 0,
      high_risk_vendors: payload?.metrics?.high_risk_vendors ?? 0,
      questionnaire_completion: payload?.metrics?.questionnaire_completion ?? 0,
      avg_risk_score: payload?.metrics?.avg_risk_score ?? 0
    }

    const recentActivity = Array.isArray(payload?.recent_activity)
      ? payload.recent_activity
      : []

    const compliance = {
      security_assessments: payload?.compliance_overview?.security_assessments ?? 0,
      documentation_complete: payload?.compliance_overview?.documentation_complete ?? 0,
      risk_assessments: payload?.compliance_overview?.risk_assessments ?? 0,
      fully_compliant: payload?.compliance_overview?.fully_compliant ?? 0,
      pending_reviews: payload?.compliance_overview?.pending_reviews ?? 0,
      require_attention: payload?.compliance_overview?.require_attention ?? 0
    }
    
    // Update KPI data with real data
    vendor_kpiData.value = [
      {
        title: "Total Vendors",
        value: metrics.total_vendors.toString(),
        icon: Users,
        trend: { value: "12%", isPositive: true }
      },
      {
        title: "High-Risk Vendors",
        value: metrics.high_risk_vendors.toString(),
        icon: AlertTriangle,
        variant: "destructive",
        trend: { value: "2%", isPositive: false }
      },
      {
        title: "Questionnaire Completion",
        value: `${metrics.questionnaire_completion}%`,
        icon: Shield,
        variant: "success",
        trend: { value: "3.1%", isPositive: true }
      },
      {
        title: "Avg Risk Score",
        value: metrics.avg_risk_score.toString(),
        icon: TrendingUp,
        trend: { value: "0.3", isPositive: false }
      }
    ]
    
    // Update recent vendors with real data
    vendor_recentVendors.value = recentActivity.map(vendor => ({
      name: vendor.company_name,
      status: (vendor.status || '').toLowerCase(),
      riskLevel: (vendor.risk_level || '').toLowerCase(),
      daysActive: vendor.days_active ?? 0,
      isCritical: vendor.is_critical ?? false,
      hasDataAccess: vendor.has_data_access ?? false,
      hasSystemAccess: vendor.has_system_access ?? false
    }))
    
    // Update compliance data
    vendor_complianceData.value = compliance
    
  } catch (err) {
    console.error('Error fetching dashboard data:', err)
    error.value = 'Failed to load dashboard data. Please try again.'
    
    // Fallback to default data
    vendor_kpiData.value = [
      {
        title: "Total Vendors",
        value: "0",
        icon: Users,
        trend: { value: "0%", isPositive: true }
      },
      {
        title: "High-Risk Vendors",
        value: "0",
        icon: AlertTriangle,
        variant: "destructive",
        trend: { value: "0%", isPositive: false }
      },
      {
        title: "Questionnaire Completion",
        value: "0%",
        icon: Shield,
        variant: "success",
        trend: { value: "0%", isPositive: true }
      },
      {
        title: "Avg Risk Score",
        value: "0",
        icon: TrendingUp,
        trend: { value: "0", isPositive: false }
      }
    ]
    
    vendor_recentVendors.value = []
    vendor_complianceData.value = {
      security_assessments: 0,
      documentation_complete: 0,
      risk_assessments: 0,
      fully_compliant: 0,
      pending_reviews: 0,
      require_attention: 0
    }
  } finally {
    loading.value = false
  }
}

// Generate report function
const generateReport = async () => {
  try {
    generatingReport.value = true
    
    // Prepare report data from current dashboard state
    const reportData = {
      timestamp: new Date().toISOString(),
      kpis: vendor_kpiData.value.map(kpi => ({
        title: kpi.title,
        value: kpi.value,
        target: getKpiTarget(kpi.title),
        category: getKpiCategory(kpi.title),
        status: getKpiStatus(kpi),
        trend: kpi.trend
      })),
      recent_activity: vendor_recentVendors.value,
      compliance_overview: vendor_complianceData.value
    }

    console.log('Generating PDF report with data:', reportData)

    // Call the PDF export endpoint
    const response = await apiClient.post('/api/v1/vendor-dashboard/export/pdf/', reportData, {
      responseType: 'blob'
    })

    // Handle response - check content type to determine if PDF or text fallback
    const contentType = response.headers['content-type'] || ''
    const isPDF = contentType.includes('application/pdf')
    const fileExtension = isPDF ? 'pdf' : 'txt'
    const mimeType = isPDF ? 'application/pdf' : 'text/plain'
    
    // Create download link
    const blob = new Blob([response.data], { type: mimeType })
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `vendor-dashboard-report-${new Date().toISOString().split('T')[0]}.${fileExtension}`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)

    showSuccess('Report Generated', 'Vendor dashboard report downloaded successfully!')
  } catch (err) {
    console.error('Error generating report:', err)
    showError('Report Generation Failed', 'Failed to generate report. Please try again.')
  } finally {
    generatingReport.value = false
  }
}

// Helper function to categorize KPIs
const getKpiCategory = (title) => {
  const titleLower = title.toLowerCase()
  if (titleLower.includes('vendor') && titleLower.includes('total')) return 'Vendor Management'
  if (titleLower.includes('risk')) return 'Risk Management'
  if (titleLower.includes('questionnaire') || titleLower.includes('completion')) return 'Compliance'
  if (titleLower.includes('score')) return 'Performance'
  return 'General'
}

// Helper function to get KPI target
const getKpiTarget = (title) => {
  const titleLower = title.toLowerCase()
  if (titleLower.includes('high-risk')) return '<= 5%'
  if (titleLower.includes('questionnaire') || titleLower.includes('completion')) return '>= 95%'
  if (titleLower.includes('risk score')) return '< 2.0'
  return 'Monitor'
}

// Helper function to get KPI status
const getKpiStatus = (kpi) => {
  // Determine status based on trend and value
  if (kpi.trend?.isPositive) {
    return 'On Target'
  }
  return 'Review Needed'
}

// Load data on component mount
onMounted(async () => {
  await loggingService.logVendorView()
  await fetchDashboardData()
})

const vendor_getKpiIconClass = (variant) => {
  switch (variant) {
    case 'destructive': return 'vendor_text-destructive'
    case 'success': return 'vendor_text-success'
    default: return 'vendor_text-primary'
  }
}

const vendor_getTrendClass = (isPositive) => {
  return isPositive ? 'vendor_text-success' : 'vendor_text-destructive'
}


const vendor_getRiskColor = (risk) => {
  switch (risk.toLowerCase()) {
    case 'low': return 'vendor_text-success'
    case 'medium': return 'vendor_text-warning'
    case 'high': return 'vendor_text-destructive'
    default: return 'vendor_text-muted-foreground'
  }
}

// Map status to Badge variants available in UI lib
const vendor_getStatusVariant = (status) => {
  switch (status.toLowerCase()) {
    case 'approved': return 'secondary'
    case 'pending': return 'default'
    case 'review': return 'destructive'
    default: return 'outline'
  }
}
</script>

<style>
@import './VendorDashboard.css';

/* Additional vendor-specific styles */
.vendor_space-y-6 > * + * {
  margin-top: 1.5rem !important;
}

.vendor_flex {
  display: flex !important;
}

.vendor_items-center {
  align-items: center !important;
}

.vendor_justify-between {
  justify-content: space-between !important;
}

.vendor_text-3xl {
  font-size: 1.875rem !important;
  line-height: 2.25rem !important;
}

.vendor_font-bold {
  font-weight: 700 !important;
}

.vendor_text-foreground {
  color: #1e293b !important;
}

.vendor_text-muted-foreground {
  color: #64748b !important;
}

.vendor_h-4 {
  height: 1rem !important;
}

.vendor_w-4 {
  width: 1rem !important;
}

.vendor_mr-2 {
  margin-right: 0.5rem !important;
}

.vendor_flex-1 {
  flex: 1 1 0% !important;
}

.vendor_gap-2 {
  gap: 0.5rem !important;
}

.vendor_space-x-2 > * + * {
  margin-left: 0.5rem !important;
}

.vendor_text-sm {
  font-size: 0.875rem !important;
  line-height: 1.25rem !important;
}

.vendor_text-xs {
  font-size: 0.75rem !important;
  line-height: 1rem !important;
}

.vendor_font-medium {
  font-weight: 500 !important;
}

.vendor_text-2xl {
  font-size: 1.5rem !important;
  line-height: 2rem !important;
}

.vendor_text-success {
  color: #059669 !important;
}

.vendor_text-warning {
  color: #d97706 !important;
}

.vendor_text-destructive {
  color: #dc2626 !important;
}

.vendor_text-primary {
  color: #1d4ed8 !important;
}

.vendor_py-8 {
  padding-top: 2rem !important;
  padding-bottom: 2rem !important;
}

.vendor_text-center {
  text-align: center !important;
}

.vendor_animate-spin {
  animation: spin 1s linear infinite !important;
}

.vendor_rounded-full {
  border-radius: 9999px !important;
}

.vendor_border-b-2 {
  border-bottom-width: 2px !important;
}

.vendor_border-primary {
  border-color: #1d4ed8 !important;
}

.vendor_mx-auto {
  margin-left: auto !important;
  margin-right: auto !important;
}

.vendor_mt-2 {
  margin-top: 0.5rem !important;
}

.vendor_bg-destructive\/10 {
  background-color: rgba(220, 38, 38, 0.1) !important;
}

.vendor_border {
  border-width: 1px !important;
}

.vendor_border-destructive\/20 {
  border-color: rgba(220, 38, 38, 0.2) !important;
}

.vendor_rounded-lg {
  border-radius: 0.5rem !important;
}

.vendor_p-4 {
  padding: 1rem !important;
}

.vendor_h-5 {
  height: 1.25rem !important;
}

.vendor_w-5 {
  width: 1.25rem !important;
}

.vendor_text-destructive {
  color: #dc2626 !important;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}
</style>
