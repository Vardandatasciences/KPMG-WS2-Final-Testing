<template>
  <Card class="search-result-card cursor-pointer hover:shadow-lg transition-all duration-200" @click="handleClick">
    <CardContent class="p-6">
      <div class="flex items-start gap-4">
        <!-- Module Icon -->
        <div class="flex-shrink-0">
          <div 
            :class="`w-10 h-10 rounded-lg flex items-center justify-center text-white font-semibold`"
            :style="{ backgroundColor: getModuleColor(result.module) }"
          >
            <component :is="getModuleIcon(result.module)" class="h-5 w-5" />
          </div>
        </div>

        <!-- Content -->
        <div class="flex-1 min-w-0">
          <!-- Title -->
          <div class="flex justify-between items-start mb-2">
            <h3 class="text-lg font-semibold text-foreground mb-1" v-html="highlightText(result.title)"></h3>
            <Badge 
              :variant="getStatusVariant(result.detailed_info?.status || result.payload_json?.status)"
              class="ml-2"
            >
              {{ result.detailed_info?.status || result.payload_json?.status || 'Unknown' }}
            </Badge>
          </div>

          <!-- Module Type -->
          <div class="flex items-center mb-2 gap-2">
            <Badge 
              :variant="getModuleVariant(result.module)"
              class="text-xs"
            >
              {{ getModuleLabel(result.module) }}
            </Badge>
            <span class="text-xs text-muted-foreground">
              Updated {{ formatDate(result.updated_at) }}
            </span>
          </div>

          <!-- Summary -->
          <div v-if="result.summary" class="text-sm text-muted-foreground mb-3" v-html="highlightText(result.summary)"></div>

          <!-- Snippet with highlighting -->
          <div class="text-sm text-muted-foreground mb-3" v-html="result.snippet"></div>

          <!-- Keywords -->
          <div v-if="result.keywords" class="mb-3">
            <div class="text-xs text-muted-foreground mb-1">Keywords:</div>
            <div class="flex flex-wrap gap-1">
              <Badge 
                v-for="keyword in result.keywords.slice(0, 5)" 
                :key="keyword"
                variant="outline"
                class="text-xs"
              >
                {{ keyword }}
              </Badge>
              <span v-if="result.keywords.length > 5" class="text-xs text-muted-foreground">
                +{{ result.keywords.length - 5 }} more
              </span>
            </div>
          </div>

          <!-- Risk Level -->
          <div v-if="result.detailed_info?.risk_level || result.payload_json?.risk_level" class="mb-3">
            <div class="text-xs text-muted-foreground mb-1">Risk Level:</div>
            <Badge 
              :variant="getRiskVariant(result.detailed_info?.risk_level || result.payload_json?.risk_level)"
              class="text-xs"
            >
              {{ (result.detailed_info?.risk_level || result.payload_json?.risk_level).toUpperCase() }}
            </Badge>
          </div>

          <!-- Additional Details -->
          <div v-if="showDetails && result.detailed_info" class="mt-4 pt-4 border-t border-border">
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
              <!-- Contract Details -->
              <div v-if="result.module === 'contract'">
                <div v-if="result.detailed_info.contract_value" class="mb-2">
                  <span class="font-medium text-muted-foreground">Value:</span>
                  <span class="ml-2 font-semibold">{{ result.detailed_info.currency }} {{ result.detailed_info.contract_value?.toLocaleString() }}</span>
                </div>
                <div v-if="result.detailed_info.deadline" class="mb-2">
                  <span class="font-medium text-muted-foreground">Deadline:</span>
                  <span class="ml-2">{{ formatDate(result.detailed_info.deadline) }}</span>
                </div>
                <div v-if="result.detailed_info.start_date" class="mb-2">
                  <span class="font-medium text-muted-foreground">Start Date:</span>
                  <span class="ml-2">{{ formatDate(result.detailed_info.start_date) }}</span>
                </div>
                <div v-if="result.detailed_info.end_date" class="mb-2">
                  <span class="font-medium text-muted-foreground">End Date:</span>
                  <span class="ml-2">{{ formatDate(result.detailed_info.end_date) }}</span>
                </div>
              </div>

              <!-- Vendor Details -->
              <div v-if="result.module === 'vendor'">
                <div v-if="result.detailed_info.company_name" class="mb-2">
                  <span class="font-medium text-muted-foreground">Company:</span>
                  <span class="ml-2">{{ result.detailed_info.company_name }}</span>
                </div>
                <div v-if="result.detailed_info.contact_email" class="mb-2">
                  <span class="font-medium text-muted-foreground">Email:</span>
                  <span class="ml-2">{{ result.detailed_info.contact_email }}</span>
                </div>
                <div v-if="result.detailed_info.effective_date" class="mb-2">
                  <span class="font-medium text-muted-foreground">Effective Date:</span>
                  <span class="ml-2">{{ formatDate(result.detailed_info.effective_date) }}</span>
                </div>
              </div>

              <!-- RFP Details -->
              <div v-if="result.module === 'rfp'">
                <div v-if="result.detailed_info.budget" class="mb-2">
                  <span class="font-medium text-muted-foreground">Budget:</span>
                  <span class="ml-2 font-semibold">{{ result.detailed_info.currency }} {{ result.detailed_info.budget?.toLocaleString() }}</span>
                </div>
                <div v-if="result.detailed_info.submission_deadline" class="mb-2">
                  <span class="font-medium text-muted-foreground">Submission Deadline:</span>
                  <span class="ml-2">{{ formatDate(result.detailed_info.submission_deadline) }}</span>
                </div>
              </div>

              <!-- SLA Details -->
              <div v-if="result.module === 'sla'">
                <div v-if="result.detailed_info.service_level" class="mb-2">
                  <span class="font-medium text-muted-foreground">Service Level:</span>
                  <span class="ml-2">{{ result.detailed_info.service_level }}%</span>
                </div>
                <div v-if="result.detailed_info.response_time" class="mb-2">
                  <span class="font-medium text-muted-foreground">Response Time:</span>
                  <span class="ml-2">{{ result.detailed_info.response_time }}</span>
                </div>
              </div>
            </div>
          </div>

          <!-- Actions -->
          <div class="flex justify-between items-center mt-4">
            <div class="flex items-center gap-2">
              <Button 
                variant="outline" 
                size="sm"
                @click.stop="handleViewDetails"
              >
                <Eye class="h-4 w-4 mr-1" />
                View Details
              </Button>
              <Button 
                v-if="result.module === 'contract' || result.module === 'bcp_drp'"
                variant="outline" 
                size="sm"
                @click.stop="handleEdit"
              >
                <Edit class="h-4 w-4 mr-1" />
                Edit
              </Button>
            </div>
            <div class="text-xs text-muted-foreground">
              Score: {{ result.score?.toFixed(2) || 'N/A' }}
            </div>
          </div>
        </div>
      </div>
    </CardContent>
  </Card>
</template>

<script setup>
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import dayjs from 'dayjs'

// TPRM UI Components
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'

// Icons
import { 
  FileText, 
  Building2, 
  Users, 
  Shield, 
  FileCheck, 
  Eye, 
  Edit,
  Target,
  ClipboardCheck,
  AlertTriangle
} from 'lucide-vue-next'

const props = defineProps({
  result: {
    type: Object,
    required: true
  },
  searchTerms: {
    type: Array,
    default: () => []
  },
  showDetails: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['click', 'view-details', 'edit'])

const router = useRouter()

const handleClick = () => {
  emit('click', props.result)
  // Navigate to the appropriate detail page based on module
  let route = null
  
  console.log('SearchResultCard handleClick:', {
    module: props.result.module,
    entity_id: props.result.entity_id,
    title: props.result.title,
    detailed_info: props.result.detailed_info,
    payload_json: props.result.payload_json
  })
  
  switch (props.result.module) {
    case 'contract':
      route = `/contracts/${props.result.entity_id}`
      break
    case 'vendor':
      route = `/vendors/${props.result.entity_id}`
      break
    case 'rfp':
      route = `/rfp-dashboard`
      break
    case 'sla':
      route = `/slas/${props.result.entity_id}`
      break
    case 'bcp_drp':
      route = getBcpRoute(props.result)
      break
    default:
      console.warn(`Unknown module: ${props.result.module}`)
      return
  }
  
  if (route) {
    router.push(route)
  }
}

const handleViewDetails = () => {
  emit('view-details', props.result)
  handleClick()
}

const handleEdit = () => {
  emit('edit', props.result)
  // Navigate to edit page
  let route = null
  
  switch (props.result.module) {
    case 'contract':
      route = `/contracts/${props.result.entity_id}/edit`
      break
    case 'vendor':
      route = `/vendor-registration`
      break
    case 'rfp':
      route = `/rfp-dashboard`
      break
    case 'sla':
      route = `/slas/${props.result.entity_id}/edit`
      break
    case 'bcp_drp':
      route = getBcpEditRoute(props.result)
      break
    default:
      console.warn(`Unknown module for edit: ${props.result.module}`)
      return
  }
  
  if (route) {
    router.push(route)
  }
}

const formatDate = (dateString) => {
  try {
    return dayjs(dateString).format('MMM DD, YYYY')
  } catch {
    return 'Unknown date'
  }
}

const highlightText = (text) => {
  if (!text || !props.searchTerms.length) return text
  
  let highlightedText = text
  props.searchTerms.forEach(term => {
    if (term.trim()) {
      const regex = new RegExp(`(${term.trim()})`, 'gi')
      highlightedText = highlightedText.replace(regex, '<mark class="bg-yellow-200 px-1 rounded">$1</mark>')
    }
  })
  return highlightedText
}

const getModuleColor = (module) => {
  const colors = {
    contract: '#3b82f6',
    vendor: '#10b981',
    rfp: '#f59e0b',
    sla: '#8b5cf6',
    bcp_drp: '#ef4444'
  }
  return colors[module] || '#6b7280'
}

const getModuleIcon = (module) => {
  const icons = {
    contract: FileText,
    vendor: Building2,
    rfp: Users,
    sla: Shield,
    bcp_drp: FileCheck
  }
  return icons[module] || FileText
}

const getModuleLabel = (module) => {
  const labels = {
    contract: 'Contract',
    vendor: 'Vendor',
    rfp: 'RFP',
    sla: 'SLA',
    bcp_drp: 'BCP/DRP'
  }
  return labels[module] || module
}

const getModuleVariant = (module) => {
  const variants = {
    contract: 'default',
    vendor: 'secondary',
    rfp: 'outline',
    sla: 'destructive',
    bcp_drp: 'secondary'
  }
  return variants[module] || 'outline'
}

const getStatusColor = (status) => {
  const colors = {
    active: 'success',
    draft: 'warning',
    pending: 'info',
    completed: 'success',
    expired: 'error'
  }
  return colors[status?.toLowerCase()] || 'grey'
}

const getStatusVariant = (status) => {
  const variants = {
    active: 'default',
    draft: 'secondary',
    pending: 'outline',
    completed: 'default',
    expired: 'destructive'
  }
  return variants[status?.toLowerCase()] || 'outline'
}

const getRiskVariant = (riskLevel) => {
  const variants = {
    low: 'default',
    medium: 'secondary',
    high: 'destructive',
    critical: 'destructive'
  }
  return variants[riskLevel?.toLowerCase()] || 'outline'
}

// BCP Route determination logic
const getBcpRoute = (result) => {
  // Extract relevant information from the result
  const entityType = result.detailed_info?.entity_type || result.payload_json?.entity_type || 'plan'
  const entityId = result.entity_id
  const resultType = result.detailed_info?.type || result.payload_json?.type
  const vendorId = result.detailed_info?.vendor_id || result.payload_json?.vendor_id
  
  console.log('BCP Route determination:', { entityType, entityId, resultType, vendorId, result })
  
  // Route based on entity type or content type
  switch (entityType.toLowerCase()) {
    case 'vendor':
      if (vendorId || entityId) {
        return `/bcp/vendor-overview/${vendorId || entityId}`
      }
      return `/bcp/vendor-hub`
    
    case 'plan':
    case 'bcp_plan':
    case 'drp_plan':
      if (resultType === 'evaluation' || result.title?.toLowerCase().includes('evaluation')) {
        return `/bcp/evaluation`
      }
      return `/bcp/library`
    
    case 'questionnaire':
      if (result.title?.toLowerCase().includes('assignment')) {
        return `/bcp/questionnaire-assignment`
      }
      return `/bcp/questionnaire-library`
    
    case 'testing':
    case 'test':
      return `/bcp/testing-library`
    
    case 'approval':
      return `/bcp/my-approvals`
    
    case 'kpi':
    case 'dashboard':
      return `/bcp/kpi-dashboard`
    
    case 'risk':
    case 'analytics':
      return `/bcp/risk-analytics`
    
    default:
      // Check title/content for keywords if entity type is unclear
      const title = (result.title || '').toLowerCase()
      const summary = (result.summary || '').toLowerCase()
      const content = title + ' ' + summary
      
      if (content.includes('vendor')) {
        return vendorId ? `/bcp/vendor-overview/${vendorId}` : `/bcp/vendor-hub`
      } else if (content.includes('questionnaire')) {
        return `/bcp/questionnaire-library`
      } else if (content.includes('evaluation')) {
        return `/bcp/evaluation`
      } else if (content.includes('testing')) {
        return `/bcp/testing-library`
      } else if (content.includes('approval')) {
        return `/bcp/my-approvals`
      } else if (content.includes('kpi') || content.includes('dashboard')) {
        return `/bcp/kpi-dashboard`
      } else if (content.includes('risk') || content.includes('analytics')) {
        return `/bcp/risk-analytics`
      } else if (content.includes('plan') || content.includes('library')) {
        return `/bcp/library`
      }
      
      // Default fallback
      return `/bcp/dashboard`
  }
}

const getBcpEditRoute = (result) => {
  // For edit operations, route to appropriate management/builder pages
  const entityType = result.detailed_info?.entity_type || result.payload_json?.entity_type || 'plan'
  const entityId = result.entity_id
  
  switch (entityType.toLowerCase()) {
    case 'questionnaire':
      return `/bcp/questionnaire-builder`
    
    case 'vendor':
      return `/bcp/vendor-upload`
    
    case 'plan':
    case 'bcp_plan':
    case 'drp_plan':
      return `/bcp/plan-submission-ocr`
    
    case 'approval':
      return `/bcp/approval-assignment`
    
    default:
      // Check content for edit context
      const title = (result.title || '').toLowerCase()
      const summary = (result.summary || '').toLowerCase()
      const content = title + ' ' + summary
      
      if (content.includes('questionnaire')) {
        return `/bcp/questionnaire-builder`
      } else if (content.includes('vendor')) {
        return `/bcp/vendor-upload`
      } else if (content.includes('approval')) {
        return `/bcp/approval-assignment`
      } else if (content.includes('plan')) {
        return `/bcp/plan-submission-ocr`
      }
      
      // Default to main dashboard for editing
      return `/bcp/dashboard`
  }
}

const formatFieldName = (fieldName) => {
  return fieldName
    .split('_')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ')
}
</script>

<style scoped>
.search-result-card {
  transition: all 0.2s ease-in-out;
}

.search-result-card:hover {
  transform: translateY(-1px);
}

/* Highlight styles */
:deep(mark) {
  background-color: rgb(254 240 138);
  padding: 0.125rem 0.25rem;
  border-radius: 0.25rem;
  font-weight: 500;
}
</style>
