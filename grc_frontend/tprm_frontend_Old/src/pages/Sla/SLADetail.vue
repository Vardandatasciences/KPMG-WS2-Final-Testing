<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <div class="flex items-center gap-4">
        <Button variant="outline" @click="goBack" class="flex items-center gap-2">
          <ArrowLeft class="h-4 w-4" />
          Back to SLAs
        </Button>
        <div>
          <h1 class="text-3xl font-bold">SLA Details</h1>
          <p class="text-muted-foreground">Comprehensive view of Service Level Agreement</p>
        </div>
      </div>
      <div class="flex gap-2">
         <Button @click="handleExport" data-export-button>
          <Download class="h-4 w-4 mr-2" />
          Export
        </Button>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="flex items-center justify-center p-8">
      <div class="text-center">
        <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
        <p class="mt-2 text-sm text-muted-foreground">Loading SLA details...</p>
      </div>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="bg-red-50 border border-red-200 rounded-md p-4">
      <div class="flex">
        <div class="ml-3">
          <h3 class="text-sm font-medium text-red-800">Error loading SLA details</h3>
          <div class="mt-2 text-sm text-red-700">
            <p>{{ error }}</p>
          </div>
          <div class="mt-4 flex gap-2">
            <button @click="loadSLADetails" class="bg-red-100 px-3 py-2 rounded-md text-sm font-medium text-red-800 hover:bg-red-200">
              Try again
            </button>
            <button @click="goBack" class="bg-gray-100 px-3 py-2 rounded-md text-sm font-medium text-gray-800 hover:bg-gray-200">
              Back to SLA List
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Main Content -->
    <div v-else class="space-y-6">
      <!-- SLA Overview Cards -->
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardContent class="p-6">
            <div class="flex items-center justify-between">
              <div>
                <p class="text-sm text-muted-foreground">SLA Name</p>
                <p class="text-lg font-semibold">{{ slaData.sla_name }}</p>
                <p class="text-xs text-muted-foreground">v{{ slaData.document_versioning || '1.0' }}</p>
              </div>
              <FileText class="h-8 w-8 text-muted-foreground" />
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent class="p-6">
            <div class="flex items-center justify-between">
              <div>
                <p class="text-sm text-muted-foreground">Vendor</p>
                <p class="text-lg font-semibold">{{ slaData.vendor?.company_name || 'Unknown Vendor' }}</p>
                <p class="text-xs text-muted-foreground">{{ slaData.contract?.contract_name || 'Unknown Contract' }}</p>
              </div>
              <Building class="h-8 w-8 text-muted-foreground" />
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent class="p-6">
            <div class="flex items-center justify-between">
              <div>
                <p class="text-sm text-muted-foreground">Status</p>
                <Badge :class="getStatusBadgeClass(slaData.status)">{{ slaData.status }}</Badge>
                <p class="text-xs text-muted-foreground">{{ slaData.priority }} Priority</p>
              </div>
              <Shield class="h-8 w-8 text-muted-foreground" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent class="p-6">
            <div class="flex items-center justify-between">
              <div>
                <p class="text-sm text-muted-foreground">Compliance Score</p>
                <p class="text-lg font-semibold">{{ slaData.compliance_score || 0 }}%</p>
                <p class="text-xs text-muted-foreground">{{ slaData.metrics?.length || 0 }} metrics</p>
              </div>
              <BarChart3 class="h-8 w-8 text-muted-foreground" />
            </div>
          </CardContent>
        </Card>
      </div>

      <!-- SLA Information Grid -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <!-- Basic Information -->
        <Card>
          <CardHeader>
            <CardTitle class="flex items-center gap-2">
              <Info class="h-5 w-5" />
              Basic Information
            </CardTitle>
          </CardHeader>
          <CardContent class="space-y-4">
            <div class="grid grid-cols-2 gap-4">
              <div>
                <p class="text-sm text-muted-foreground">SLA Type</p>
                <p class="font-medium">{{ slaData.sla_type }}</p>
              </div>
              <div>
                <p class="text-sm text-muted-foreground">Business Service</p>
                <p class="font-medium">{{ slaData.business_service_impacted || 'Not specified' }}</p>
              </div>
              <div>
                <p class="text-sm text-muted-foreground">Effective Date</p>
                <p class="font-medium">{{ formatDate(slaData.effective_date) }}</p>
              </div>
              <div>
                <p class="text-sm text-muted-foreground">Expiry Date</p>
                <p class="font-medium" :class="getExpiryStatus(getDaysUntilExpiry(slaData.expiry_date)).color">
                  {{ formatDate(slaData.expiry_date) }}
                  <span class="text-xs block">{{ getExpiryStatus(getDaysUntilExpiry(slaData.expiry_date)).status }}</span>
                </p>
              </div>
              <div>
                <p class="text-sm text-muted-foreground">Reporting Frequency</p>
                <p class="font-medium capitalize">{{ slaData.reporting_frequency }}</p>
              </div>
              <div>
                <p class="text-sm text-muted-foreground">Approval Status</p>
                <Badge :class="getApprovalBadgeClass(slaData.approval_status)">{{ slaData.approval_status }}</Badge>
              </div>
            </div>
          </CardContent>
        </Card>

        <!-- Thresholds & Penalties -->
        <Card>
          <CardHeader>
            <CardTitle class="flex items-center gap-2">
              <AlertTriangle class="h-5 w-5" />
              Thresholds & Penalties
            </CardTitle>
          </CardHeader>
          <CardContent class="space-y-4">
            <div class="grid grid-cols-2 gap-4">
              <div>
                <p class="text-sm text-muted-foreground">Penalty Threshold</p>
                <p class="font-medium">{{ slaData.penalty_threshold || 'Not set' }}%</p>
              </div>
              <div>
                <p class="text-sm text-muted-foreground">Credit Threshold</p>
                <p class="font-medium">{{ slaData.credit_threshold || 'Not set' }}%</p>
              </div>
              <div class="col-span-2">
                <p class="text-sm text-muted-foreground">Baseline Period</p>
                <p class="font-medium">{{ slaData.baseline_period || 'Not specified' }}</p>
              </div>
            </div>
            <div v-if="slaData.improvement_targets && Object.keys(slaData.improvement_targets).length > 0">
              <p class="text-sm text-muted-foreground mb-2">Improvement Targets</p>
              <div class="bg-gray-50 p-3 rounded-md">
                <pre class="text-xs">{{ JSON.stringify(slaData.improvement_targets, null, 2) }}</pre>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <!-- SLA Metrics -->
      <Card>
        <CardHeader>
          <CardTitle class="flex items-center gap-2">
            <BarChart3 class="h-5 w-5" />
            SLA Metrics ({{ slaData.metrics?.length || 0 }})
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div v-if="slaData.metrics && slaData.metrics.length > 0" class="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Metric Name</TableHead>
                  <TableHead>Threshold</TableHead>
                  <TableHead>Unit</TableHead>
                  <TableHead>Frequency</TableHead>
                  <TableHead>Penalty</TableHead>
                  <TableHead>Methodology</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                <TableRow v-for="metric in slaData.metrics" :key="metric.metric_id">
                  <TableCell class="font-medium">{{ metric.metric_name }}</TableCell>
                  <TableCell>{{ metric.threshold }}</TableCell>
                  <TableCell>{{ metric.measurement_unit }}</TableCell>
                  <TableCell>
                    <Badge variant="outline">{{ metric.frequency }}</Badge>
                  </TableCell>
                  <TableCell>{{ metric.penalty || 'Not specified' }}</TableCell>
                  <TableCell class="max-w-xs truncate" :title="metric.measurement_methodology">
                    {{ metric.measurement_methodology || 'Not specified' }}
                  </TableCell>
                </TableRow>
              </TableBody>
            </Table>
          </div>
          <div v-else class="text-center py-8">
            <BarChart3 class="h-12 w-12 text-muted-foreground mx-auto mb-4" />
            <p class="text-muted-foreground">No metrics defined for this SLA</p>
          </div>
        </CardContent>
      </Card>

      <!-- Additional Information -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <!-- Measurement Methodology -->
        <Card v-if="slaData.measurement_methodology">
          <CardHeader>
            <CardTitle class="flex items-center gap-2">
              <Clipboard class="h-5 w-5" />
              Measurement Methodology
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p class="text-sm text-gray-600 whitespace-pre-wrap">{{ slaData.measurement_methodology }}</p>
          </CardContent>
        </Card>

        <!-- Exclusions -->
        <Card v-if="slaData.exclusions">
          <CardHeader>
            <CardTitle class="flex items-center gap-2">
              <X class="h-5 w-5" />
              Exclusions
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p class="text-sm text-gray-600 whitespace-pre-wrap">{{ slaData.exclusions }}</p>
          </CardContent>
        </Card>

        <!-- Force Majeure Clauses -->
        <Card v-if="slaData.force_majeure_clauses">
          <CardHeader>
            <CardTitle class="flex items-center gap-2">
              <Shield class="h-5 w-5" />
              Force Majeure Clauses
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p class="text-sm text-gray-600 whitespace-pre-wrap">{{ slaData.force_majeure_clauses }}</p>
          </CardContent>
        </Card>

        <!-- Audit Requirements -->
        <Card v-if="slaData.audit_requirements">
          <CardHeader>
            <CardTitle class="flex items-center gap-2">
              <Search class="h-5 w-5" />
              Audit Requirements
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p class="text-sm text-gray-600 whitespace-pre-wrap">{{ slaData.audit_requirements }}</p>
          </CardContent>
        </Card>
      </div>
    </div>
  </div>

  <!-- Popup Modal -->
  <PopupModal />
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { 
  Building, Shield, ArrowLeft, Download, BarChart3, 
  Info, Clipboard, X, Search, FileText, AlertTriangle
} from 'lucide-vue-next'
import apiService from '@/services/api'
import jsPDF from 'jspdf'
import html2canvas from 'html2canvas'
import PopupModal from '@/popup/PopupModal.vue'
import { PopupService } from '@/popup/popupService'

const route = useRoute()
const router = useRouter()
const loading = ref(false)
const error = ref(null)

const slaData = ref<any>({})

// Load comprehensive SLA details from API
const loadSLADetails = async () => {
  loading.value = true
  error.value = null
  
  try {
    const slaId = route.params.id
    if (!slaId) {
      throw new Error('SLA ID not provided')
    }
    
    // Load comprehensive SLA details from backend using VendorSLADetailSerializer
    const slaResponse = await apiService.getSLADetail(slaId)
    
    console.log('SLA Data received:', slaResponse)
    console.log('SLA Metrics in response:', slaResponse.metrics)
    slaData.value = slaResponse
    
    // Always try to fetch metrics separately to ensure we get the latest data
    try {
      console.log('Fetching metrics separately for SLA:', slaId)
      const metricsResponse = await apiService.getSLAMetrics(slaId)
      console.log('Metrics received separately:', metricsResponse)
      if (metricsResponse && metricsResponse.length > 0) {
        slaData.value.metrics = metricsResponse
        console.log('Updated slaData.metrics:', slaData.value.metrics)
      }
    } catch (metricsError) {
      console.warn('Could not fetch metrics separately:', metricsError)
      // Keep the metrics from the main response if available
      if (!slaData.value.metrics) {
        slaData.value.metrics = []
      }
    }
    
  } catch (err) {
    // Check if it's a 404 error
    if (err.message.includes('404') || err.message.includes('Not Found')) {
      error.value = `SLA with ID ${route.params.id} not found. It may have been deleted or does not exist.`
    } else {
      error.value = err.message || 'An error occurred while loading SLA details'
    }
    console.error('Error loading SLA details:', err)
  } finally {
    loading.value = false
  }
}

// Load data on component mount
onMounted(() => {
  loadSLADetails()
})

// Helper functions for styling and formatting
const getStatusBadgeClass = (status: string) => {
  switch (status?.toUpperCase()) {
    case 'ACTIVE':
      return 'bg-green-100 text-green-800'
    case 'EXPIRED':
      return 'bg-red-100 text-red-800'
    case 'PENDING':
      return 'bg-blue-100 text-blue-800'
    default:
      return 'bg-gray-100 text-gray-800'
  }
}

const getApprovalBadgeClass = (status: string) => {
  switch (status?.toUpperCase()) {
    case 'APPROVED':
      return 'bg-green-100 text-green-800'
    case 'PENDING':
      return 'bg-yellow-100 text-yellow-800'
    default:
      return 'bg-gray-100 text-gray-800'
  }
}

const formatDate = (dateString: string) => {
  if (!dateString) return 'Not specified'
  try {
    const date = new Date(dateString)
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    })
  } catch (error) {
    return dateString
  }
}

const getDaysUntilExpiry = (expiryDate: string) => {
  if (!expiryDate) return 0
  const today = new Date()
  const expiry = new Date(expiryDate)
  const diff = Math.ceil((expiry.getTime() - today.getTime()) / (1000 * 60 * 60 * 24))
  return diff
}

const getExpiryStatus = (days: number) => {
  if (days < 0) return { status: 'Expired', color: 'text-red-600' }
  if (days <= 30) return { status: 'Expiring soon', color: 'text-orange-600' }
  if (days <= 90) return { status: 'Expiring', color: 'text-yellow-600' }
  return { status: 'Active', color: 'text-green-600' }
}

// Action handlers
const handleExport = async () => {
  try {
    if (!slaData.value || !slaData.value.sla_name) {
      PopupService.warning('No SLA data available to export', 'No Data')
      return
    }

    // Show loading state
    const exportButton = document.querySelector('[data-export-button]') as HTMLButtonElement
    if (exportButton) {
      exportButton.disabled = true
      exportButton.textContent = 'Generating PDF...'
    }

    // Generate PDF
    await generateSLAExportPDF(slaData.value)
    
    console.log('SLA PDF exported successfully:', slaData.value.sla_name)
    PopupService.success('SLA PDF exported successfully!', 'Export Complete')
  } catch (error) {
    console.error('Error exporting SLA PDF:', error)
    PopupService.error('Error exporting SLA PDF. Please try again.', 'Export Failed')
  } finally {
    // Reset button state
    const exportButton = document.querySelector('[data-export-button]') as HTMLButtonElement
    if (exportButton) {
      exportButton.disabled = false
      exportButton.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 mr-2" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 5 17 10"/><line x1="12" y1="5" x2="12" y2="20"/></svg>Export'
    }
  }
}

// Generate comprehensive PDF export
const generateSLAExportPDF = async (sla) => {
  const pdf = new jsPDF('p', 'mm', 'a4')
  const pageWidth = pdf.internal.pageSize.getWidth()
  const pageHeight = pdf.internal.pageSize.getHeight()
  let yPosition = 20
  const margin = 20
  const contentWidth = pageWidth - (margin * 2)
  
  // Colors
  const primaryColor = [37, 99, 235] // Blue
  const secondaryColor = [107, 114, 128] // Gray
  const successColor = [34, 197, 94] // Green
  const warningColor = [245, 158, 11] // Orange
  const dangerColor = [239, 68, 68] // Red
  
  // Helper function to add text with word wrap
  const addText = (text: string, x: number, y: number, options: any = {}) => {
    const { fontSize = 10, color = [0, 0, 0], font = 'helvetica', maxWidth = contentWidth } = options
    pdf.setFontSize(fontSize)
    pdf.setTextColor(color[0], color[1], color[2])
    pdf.setFont(font, options.fontStyle || 'normal')
    
    const lines = pdf.splitTextToSize(text, maxWidth)
    pdf.text(lines, x, y)
    return y + (lines.length * fontSize * 0.4)
  }
  
  // Helper function to add a section header
  const addSectionHeader = (title: string, y: number) => {
    pdf.setFillColor(240, 240, 240)
    pdf.rect(margin, y - 3, contentWidth, 6, 'F')
    
    pdf.setFontSize(11)
    pdf.setTextColor(0, 0, 0)
    pdf.setFont('helvetica', 'bold')
    pdf.text(title, margin + 3, y + 1)
    
    return y + 10
  }
  
  // Helper function to create a data table
  const createDataTable = (data: [string, string][], y: number, title: string) => {
    checkNewPage(30)
    
    // Only add section header if title is provided
    if (title && title.trim() !== '') {
      y = addSectionHeader(title, y)
    }
    
    // Table dimensions
    const tableWidth = contentWidth
    const rowHeight = 8
    const labelWidth = tableWidth * 0.4
    const valueWidth = tableWidth * 0.6
    
    // Draw table header
    pdf.setFillColor(249, 250, 251)
    pdf.rect(margin, y - 3, tableWidth, rowHeight, 'F')
    
    // Header text
    pdf.setFontSize(9)
    pdf.setTextColor(0, 0, 0)
    pdf.setFont('helvetica', 'bold')
    pdf.text('Field', margin + 2, y + 2)
    pdf.text('Value', margin + labelWidth + 2, y + 2)
    
    y += rowHeight
    
    // Draw table rows
    data.forEach(([label, value], index) => {
      checkNewPage(15)
      
      // Alternate row colors
      if (index % 2 === 0) {
        pdf.setFillColor(249, 250, 251)
        pdf.rect(margin, y - 3, tableWidth, rowHeight, 'F')
      }
      
      // Draw borders
      pdf.setDrawColor(200, 200, 200)
      pdf.line(margin, y - 3, margin + tableWidth, y - 3)
      pdf.line(margin, y + rowHeight - 3, margin + tableWidth, y + rowHeight - 3)
      pdf.line(margin, y - 3, margin, y + rowHeight - 3)
      pdf.line(margin + labelWidth, y - 3, margin + labelWidth, y + rowHeight - 3)
      pdf.line(margin + tableWidth, y - 3, margin + tableWidth, y + rowHeight - 3)
      
      // Add content
      pdf.setFontSize(8)
      pdf.setTextColor(0, 0, 0)
      pdf.setFont('helvetica', 'bold')
      pdf.text(label, margin + 2, y + 2)
      
      pdf.setFont('helvetica', 'normal')
      const valueText = value || 'Not specified'
      const lines = pdf.splitTextToSize(valueText, valueWidth - 4)
      pdf.text(lines, margin + labelWidth + 2, y + 2)
      
      y += Math.max(rowHeight, lines.length * 3)
    })
    
    return y + 10
  }
  
  // Helper function to check if we need a new page
  const checkNewPage = (requiredSpace = 20) => {
    if (yPosition + requiredSpace > pageHeight - margin) {
      pdf.addPage()
      yPosition = 20
      return true
    }
    return false
  }
  
  // Header
  pdf.setFillColor(primaryColor[0], primaryColor[1], primaryColor[2])
  pdf.rect(0, 0, pageWidth, 25, 'F')
  
  pdf.setFontSize(18)
  pdf.setTextColor(255, 255, 255)
  pdf.setFont('helvetica', 'bold')
  pdf.text('Service Level Agreement', margin, 12)
  
  pdf.setFontSize(14)
  pdf.text(sla.sla_name, margin, 20)
  
  yPosition = 35
  
  // Export info
  const currentDate = new Date().toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  })
  
  yPosition = addText(`Export Generated: ${currentDate} | Document Version: ${sla.document_versioning || '1.0'} | Status: ${sla.status}`, 
    margin, yPosition, { fontSize: 9, color: secondaryColor })
  
  yPosition += 15
  
  // Basic Information Table
  const basicInfo: [string, string][] = [
    ['SLA Name', sla.sla_name],
    ['SLA Type', sla.sla_type || 'Not specified'],
    ['Vendor', sla.vendor?.company_name || 'Not specified'],
    ['Contract', sla.contract?.contract_name || 'Not specified'],
    ['Business Service Impacted', sla.business_service_impacted || 'Not specified'],
    ['Reporting Frequency', sla.reporting_frequency || 'Not specified']
  ]
  
  yPosition = createDataTable(basicInfo, yPosition, 'Basic Information')
  
  // Dates & Status Table
  const datesInfo: [string, string][] = [
    ['Effective Date', formatDateForPDF(sla.effective_date)],
    ['Expiry Date', formatDateForPDF(sla.expiry_date)],
    ['Status', sla.status || 'PENDING'],
    ['Priority', sla.priority || 'MEDIUM'],
    ['Approval Status', sla.approval_status || 'PENDING'],
    ['Compliance Score', `${sla.compliance_score || 0}%`]
  ]
  
  yPosition = createDataTable(datesInfo, yPosition, 'Dates & Status')
  
  // Thresholds & Penalties Table
  const thresholdsInfo: [string, string][] = [
    ['Penalty Threshold', `${sla.penalty_threshold || 'Not set'}%`],
    ['Credit Threshold', `${sla.credit_threshold || 'Not set'}%`],
    ['Baseline Period', sla.baseline_period || 'Not specified'],
    ['Compliance Framework', sla.compliance_framework || 'Not specified']
  ]
  
  // Add Improvement Targets to the same table if available
  if (sla.improvement_targets && Object.keys(sla.improvement_targets).length > 0) {
    thresholdsInfo.push(['Improvement Targets', JSON.stringify(sla.improvement_targets, null, 2)])
  }
  
  yPosition = createDataTable(thresholdsInfo, yPosition, 'Thresholds & Penalties')
  
  // SLA Metrics Table
  yPosition = addSectionHeader(`SLA Metrics (${sla.metrics?.length || 0})`, yPosition)
  
  if (sla.metrics && sla.metrics.length > 0) {
    // Table headers
    const headers = ['Metric Name', 'Threshold', 'Unit', 'Frequency', 'Penalty', 'Methodology']
    const colWidths = [35, 20, 15, 20, 30, 40]
    let xPosition = margin
    
    // Draw table header
    pdf.setFillColor(249, 250, 251)
    pdf.rect(margin, yPosition - 5, contentWidth, 8, 'F')
    
    // Draw header borders
    pdf.setDrawColor(200, 200, 200)
    pdf.line(margin, yPosition - 5, margin + contentWidth, yPosition - 5)
    pdf.line(margin, yPosition + 3, margin + contentWidth, yPosition + 3)
    
    headers.forEach((header, index) => {
      pdf.setFontSize(9)
      pdf.setTextColor(0, 0, 0)
      pdf.setFont('helvetica', 'bold')
      pdf.text(header, xPosition, yPosition + 2)
      
      // Draw column borders
      if (index > 0) {
        pdf.line(xPosition, yPosition - 5, xPosition, yPosition + 3)
      }
      xPosition += colWidths[index]
    })
    
    yPosition += 10
    
    // Draw table rows
    sla.metrics.forEach((metric, index) => {
      checkNewPage(15)
      
      if (index % 2 === 0) {
        pdf.setFillColor(249, 250, 251)
        pdf.rect(margin, yPosition - 3, contentWidth, 8, 'F')
      }
      
      xPosition = margin
      const rowData = [
        metric.metric_name || 'N/A',
        metric.threshold || 'N/A',
        metric.measurement_unit || 'N/A',
        metric.frequency || 'N/A',
        metric.penalty || 'Not specified',
        metric.measurement_methodology || 'Not specified'
      ]
      
      rowData.forEach((data, colIndex) => {
        pdf.setFontSize(8)
        pdf.setTextColor(0, 0, 0)
        pdf.setFont('helvetica', 'normal')
        
        // Truncate long text
        const maxLength = colIndex === 0 ? 25 : colIndex === 4 ? 20 : colIndex === 5 ? 30 : 15
        const displayText = data.length > maxLength ? data.substring(0, maxLength) + '...' : data
        
        pdf.text(displayText, xPosition, yPosition + 2)
        
        // Draw column borders
        if (colIndex > 0) {
          pdf.line(xPosition, yPosition - 3, xPosition, yPosition + 5)
        }
        xPosition += colWidths[colIndex]
      })
      
      // Draw row borders
      pdf.setDrawColor(200, 200, 200)
      pdf.line(margin, yPosition - 3, margin + contentWidth, yPosition - 3)
      pdf.line(margin, yPosition + 5, margin + contentWidth, yPosition + 5)
      
      yPosition += 8
    })
  } else {
    yPosition = addText('No metrics defined for this SLA', margin, yPosition, { 
      fontSize: 10, 
      color: secondaryColor,
      fontStyle: 'italic'
    })
  }
  
  yPosition += 15
  
  // Additional Information Table
  const additionalSections: [string, string][] = [
    ['Measurement Methodology', sla.measurement_methodology],
    ['Exclusions', sla.exclusions],
    ['Force Majeure Clauses', sla.force_majeure_clauses],
    ['Audit Requirements', sla.audit_requirements]
  ].filter(([title, content]) => content) as [string, string][] // Only include sections with content
  
  if (additionalSections.length > 0) {
    yPosition = createDataTable(additionalSections, yPosition, 'Additional Information')
  }
  
  // Footer
  const footerY = pageHeight - 20
  pdf.setFontSize(8)
  pdf.setTextColor(secondaryColor[0], secondaryColor[1], secondaryColor[2])
  pdf.setFont('helvetica', 'normal')
  pdf.text('This document was automatically generated from the SLA Management System', margin, footerY)
  pdf.text('For questions or clarifications, please contact the SLA management team', margin, footerY + 5)
  
  // Generate filename and download
  const filename = `${sla.sla_name.replace(/[^a-z0-9]/gi, '_').toLowerCase()}_sla_export.pdf`
  pdf.save(filename)
}

// Helper function to format dates for PDF
const formatDateForPDF = (dateString) => {
  if (!dateString) return 'Not specified'
  try {
    const date = new Date(dateString)
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    })
  } catch (error) {
    return dateString
  }
}

// Navigate back to SLA Management page
const goBack = () => {
  router.push('/slas')
}
</script>

